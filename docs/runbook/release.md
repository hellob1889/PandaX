# Release Runbook

> **Audience**: maintainer doing a release.
> **Goal**: ship a new version to PyPI + GitHub Release with all CI green and full audit trail.

## 0. Pre-flight (10 min)

Before you start, verify:

```bash
# You have push access to hellob1889/Pandaone-AI-Agent
gh repo view hellob1889/Pandaone-AI-Agent --json permissions  # (or check via web UI)

# Local clone is in sync with origin
git fetch origin
git status
git rev-parse HEAD  # should match origin/main HEAD

# Local tests pass
pytest tests/ -q  # expect 342 passed, 1 skipped (or whatever current count is)
```

**Decision points:**

| Situation | Action |
|---|---|
| Local tests fail | Stop. Fix tests first. Do not release broken code. |
| Local HEAD != origin/main | `git pull --rebase` or merge. Then re-run tests. |
| You don't have push access | Stop. Ask repo owner to grant access or do release via their account. |

---

## 1. Choose release type (decision tree)

```
What changed?
├── Code/business logic only          → Standard release (Section 2)
├── Brand/PyPI rename cutover         → See Section 6
├── CI/audit infrastructure only     → Tag-only release (Section 7)
├── Documentation only                → Tag-only release (Section 7)
└── Mixed (code + docs + CI)          → Standard release (Section 2)
```

---

## 2. Standard release (code changes)

### 2.1 Version bump + code changes

```bash
# Create release branch
git checkout -b release/v0.7.7 main

# Edit pyproject.toml: bump version
# version = "0.7.7"  (was "0.7.6")

# Make your code changes
# ...

# Commit
git add -A
git commit -m "feat: <your feature>"
git push origin release/v0.7.7
```

### 2.2 Open PR

Open PR against `main`:
- Title: `release: v0.7.7 — <short description>`
- Body: link to issues / changelog draft

**Wait for CI 5/5 green.** If L7 audit fails, see [ci-troubleshooting.md § L7 audit](./ci-troubleshooting.md#l7-audit验证failed).

**Merge strategy: squash.** Single commit on `main`.

### 2.3 CHANGELOG PR

After PR merged, open a **second** PR (docs-only):

```bash
git checkout -b docs/changelog-v077 main
# Edit CHANGELOG.md: prepend "## [0.7.7] - <YYYY-MM-DD>" section
# (Push directly; this PR auto-skips audit via PR #19+#20 mechanism)
git push origin docs/changelog-v077
```

Wait for CI 5/5 (L7 should be auto-skipped), then squash-merge.

**Why separate PR?** Audit auto-skip only triggers when PR is docs-only.
Mixing docs with code makes audit fail, requiring manual `[skip-audit]` marker.

### 2.4 Tag + push

```bash
git checkout main
git pull --rebase

# Tag the CHANGELOG merge commit (latest on main)
git tag v0.7.7
git push origin v0.7.7
```

**Verify tag pushed:**

```bash
curl -s https://api.github.com/repos/hellob1889/Pandaone-AI-Agent/tags | grep -E '"name":' | tail -3
# Should see v0.7.7
```

### 2.5 Wait for publish workflow

```bash
# Watch run creation
curl -s -H "Authorization: Bearer <GH_TOKEN>" \
  "https://api.github.com/repos/hellob1889/Pandaone-AI-Agent/actions/runs?event=push&per_page=1" \
  | jq '.workflow_runs[0] | {id, status, conclusion, head_branch}'
```

**Expected**: 3 jobs all green (`Build wheel + sdist`, `Run tests`, `Publish`).

**If failed**, see [ci-troubleshooting.md § Publish failures](./ci-troubleshooting.md#publish-failures).

### 2.6 Verify PyPI

```bash
curl -s "https://pypi.org/pypi/pandaone-guard/0.7.7/json" | jq '.info.version'
# Expected: "0.7.7"

# Verify files exist
curl -s "https://pypi.org/pypi/pandaone-guard/0.7.7/json" | jq '.urls[].filename'
# Expected: pandaone_guard-0.7.7-py3-none-any.whl + pandaone_guard-0.7.7.tar.gz
```

### 2.7 Install verification

```bash
python -m venv /tmp/pandaone-verify-077
source /tmp/pandaone-verify-077/bin/activate  # Windows: Scripts\activate
pip install pandaone-guard==0.7.7
pandaone --version  # Expected: pandaone-guard v0.7.7
deactivate
```

### 2.8 Create GitHub Release

```bash
# Browser automation OR:
gh release create v0.7.7 \
  --title "Pandaone AI Agent v0.7.7 — <title>" \
  --notes "$(cat release_notes.md)"
```

If using browser automation (no `gh` CLI), see the v0.7.6 release flow as template:
1. Navigate to `https://github.com/hellob1889/Pandaone-AI-Agent/releases/new?tag=v0.7.7`
2. Fill title input
3. Fill release body via `document.getElementById('release_body')` + React native setter
4. Click "Publish release" button

---

## 3. Tag-only release (CI/docs changes)

For PRs that change ONLY:
- `.github/workflows/*`
- `docs/**`
- `CHANGELOG.md`
- `README*.md`
- `.github/PULL_REQUEST_TEMPLATE*`
- `.github/ISSUE_TEMPLATE/*`
- `LICENSE*`, `NOTICE*`

The PR auto-skips L7 audit (via PR #19+#20 docs-only regex).

**After merge, tag the release commit:**

```bash
git checkout main
git pull --rebase
git tag v0.7.5 <commit-sha>
git push origin v0.7.5
```

**Create pre-release GitHub Release:**

```
Release URL: https://github.com/hellob1889/Pandaone-AI-Agent/releases/new?tag=v0.7.5

☑ Set as a pre-release  ← CRITICAL: this is not a PyPI release

Body:
> This release is CI/audit infrastructure or documentation only.
> No PyPI publish. No user-facing code change.
```

**Why tag at all?** See v0.7.5 tag rationale (CHANGELOG continuity, reproducibility, audit trail).

**Skip**: sections 2.5-2.7 (no PyPI publish, no install verification).

---

## 4. PyPI Trusted Publisher setup (one-time, per new package name)

When adding a NEW PyPI distribution name (e.g., when renaming `pandax-guard` → `pandaone-guard`):

### 4.1 Verify name availability

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/<new-name>/json
# Expected: 404 (name not taken)
# If 200: name already exists, choose different name
```

### 4.2 Register pending trusted publisher

PyPI supports **pending trusted publishers** that auto-activate on first OIDC upload.
**You do NOT need to pre-create the project.**

URL: `https://pypi.org/manage/account/publishing/`

Form fields:

| Field | Value |
|---|---|
| Project name | `pandaone-guard` |
| Owner | `hellob1889` |
| Repository | `Pandaone-AI-Agent` |
| Workflow filename | `publish.yml` |
| Environment name | (leave blank) |

**Verify success**: page shows `Pending publishers → pandaone-guard → GitHub → Repository: hellob1889/Pandaone-AI-Agent → Workflow: publish.yml`.

### 4.3 Ensure no conflicting API tokens

Before the first OIDC upload, the GitHub `PYPI_API_TOKEN` secret MUST NOT exist.
If it exists and is project-scoped to the old name, the publish job will fail with:
```
403 Invalid API Token: project-scoped token is not valid for project: 'new-name'
```

**How to delete**:
1. Go to `https://github.com/hellob1889/Pandaone-AI-Agent/settings/secrets/actions`
2. Find `PYPI_API_TOKEN` row
3. Click trash icon (`aria-label="Delete PYPI_API_TOKEN"`)
4. Confirm "Yes, delete this secret"

**If you have no browser access**: API DELETE returns 403 (GitHub App lacks `secrets:write`). Get a maintainer to delete manually.

### 4.4 First upload auto-creates project

Push the tag and trigger the workflow as normal. The first OIDC upload will:
1. PyPI accepts the OIDC token (because pending publisher matches)
2. PyPI auto-creates the project (using `pyproject.toml` metadata)
3. PyPI uploads the wheel + sdist
4. Pending publisher → active publisher

---

## 5. Re-run failed publish workflow

When `Publish` job fails but `Build`/`Tests` succeeded:

```bash
# API: usually 403 (GitHub App lacks actions:write)
# Browser: required

# Steps (browser):
1. Navigate to https://github.com/hellob1889/Pandaone-AI-Agent/actions
2. Click on the failed "Publish to PyPI" run
3. Top-right: click "Re-run jobs" (dropdown)
4. Select "Re-run failed jobs"
5. Confirmation dialog appears: click the "Re-run jobs" button inside the dialog
6. Wait 60-90s for re-run to complete
```

**Why not API?** GitHub App integration tokens lack `actions:write` permission.
Browser is the only path.

---

## 6. Brand cutover (PyPI rename)

Special case: changing PyPI distribution name (e.g., `pandax-guard` → `pandaone-guard`).

### Decision matrix

| Existing package | New package | Existing users impact |
|---|---|---|
| Keep publishing to old | Stop publishing to old | **Breaks** `pip install <old>` for new versions |
| Keep publishing to old | Also publish to new | **Confusing** — two parallel versions |
| **Stop publishing to old** | **Start publishing to new** | **Recommended** — old stays at last version, new starts fresh |

### 6.1 Plan

Open PR with cutover plan document at `docs/plan/vX.Y.Z.md`. Cover:
- Timeline (when old stops, when new starts)
- Migration guide (`pip uninstall <old> && pip install <new>`)
- Internal alias map (Python import path, CLI command)
- Validation plan

### 6.2 Code changes

Single PR (or 2 PRs: code + CHANGELOG):
- `pyproject.toml`: `name = "<new>"`, `version = "<X.Y.Z>"`
- `README.md` + `docs/**/*.md`: substitute `<old>` → `<new>`
- Remove any temporary fallback comments
- `examples/*`: substitute in shell scripts

### 6.3 PyPI setup

See [Section 4](#4-pypi-trusted-publisher-setup-one-time-per-new-package-name).

### 6.4 Tag + push + verify

Same as [Section 2.4-2.7](#24-tag--push) but with new package name.

### 6.5 Backward-compat policy

| Element | Policy |
|---|---|
| Python `import` path | Keep `<old>` as alias for 1+ major version |
| CLI command | Keep `<old>` as alias for 1+ major version |
| PyPI distribution | Stop at last `<old>` version (e.g., `pandax-guard 0.7.4`) |
| Documentation | New docs reference `<new>`; old docs archived |

---

## 7. Post-release checklist (15 min)

After release is live:

- [ ] PyPI page renders correctly (`https://pypi.org/project/<pkg>/<version>/`)
- [ ] GitHub Release is public (or marked pre-release if appropriate)
- [ ] `pip install --upgrade <pkg>` works in fresh venv
- [ ] `<cli> --version` shows correct version
- [ ] No stale branches left over
- [ ] CHANGELOG link block updated with compare URL:
      `[0.7.7]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.7.6...v0.7.7`
- [ ] README badge shows new version (shields.io auto-updates)

---

## 8. Common pitfalls (from prior releases)

| Pitfall | Symptom | Fix |
|---|---|---|
| `[skip-audit]` in commit footer | L7 audit runs anyway | Put marker in commit **subject**, not body |
| PR mixed code + docs | L7 audit fails | Split into 2 PRs: code, then docs |
| `pandax-guard` token for `pandaone-guard` | 403 Invalid API Token | Delete `PYPI_API_TOKEN` secret, rely on OIDC |
| Tag points to wrong commit | Wrong code in release | Always `git pull --rebase` before `git tag` |
| Forgot to update link block | Compare links break | Add `[X.Y.Z]: https://...compare/...` at bottom |
| Skipped TestPyPI dry-run | PyPI page renders ugly | TestPyPI first, fix, then production |

---

## 9. Rollback procedure

If a release needs to be yanked:

```bash
# 1. Yank from PyPI (only if major bug)
#    PyPI does NOT support un-publishing, but supports yanking
#    PyPI admin: https://pypi.org/manage/project/<pkg>/release/<version>/
#    OR via twine: twine yank <pkg> <version>

# 2. Delete GitHub Release (preserve tag, or also delete tag if necessary)
gh release delete v0.7.7 --yes  # preserves tag
# OR
git push origin :refs/tags/v0.7.7
gh release delete v0.7.7 --yes

# 3. If issue is in code: revert the merge commit, push a patch release
git revert <merge-commit-sha>
git tag v0.7.8
# ... etc
```

**Important**: never rewrite history on `main` after a release. Always revert.
