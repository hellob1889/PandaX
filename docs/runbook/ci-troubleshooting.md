# CI Troubleshooting Runbook

> **Audience**: on-call maintainer when a CI check fails.
> **Goal**: diagnose and fix the failure without guesswork.

## How CI works

PR triggers 5 checks via GitHub Actions:

| Check | Workflow | What it does |
|---|---|---|
| **Lint Summary** | `lint.yml` | Python lint, type hints, format check |
| **i18n Coverage Check** | `lint.yml` | Verify all CLI strings have en/zh translations |
| **i18n Hardcoded Chinese Audit** | `lint.yml` | Detect hardcoded Chinese in source code |
| **Pandaone 审计验证** (L7 audit) | `audit.yml` | Run `pandax ci` on changed code |
| **Smoke Tests** | `audit.yml` | Sanity test the package imports + CLI starts |

Push to `v*` tag additionally triggers **Publish to PyPI** (`publish.yml`):
- `Build wheel + sdist`
- `Run tests`
- `Publish` (OIDC upload to PyPI)

---

## L7 审计验证 (failed)

The `audit.yml` workflow has skip logic. Diagnose which path you hit:

```yaml
# audit.yml (simplified)
SKIP_AUDIT=$(git log -5 --pretty=format:'%s%n%n%b' | grep -q '\[skip-audit\]' && echo yes)
WORKFLOW_ONLY=$(git diff --name-only HEAD~1 HEAD | grep -v '^\.github/workflows/' | grep -v '^\.trae-html-share-packages/' | wc -l)
DOCS_ONLY=$(git diff --name-only HEAD~1 HEAD | grep -v -E '^(CHANGELOG\.md|README[^/]*\.md|docs/.*|\.github/PULL_REQUEST_TEMPLATE(\.md|/.*)|\.github/ISSUE_TEMPLATE/.*|\.github/CODEOWNERS|\.github/CODE_OF_CONDUCT\.md|\.github/CONTRIBUTING\.md|\.github/SECURITY\.md|LICENSE[^/]*|NOTICE[^/]*)$' | wc -l)

if [ -n "$SKIP_AUDIT" ]; then exit 0; fi
if [ "$WORKFLOW_ONLY" = "0" ]; then exit 0; fi
if [ "$DOCS_ONLY" = "0" ]; then exit 0; fi
# else: run pandax ci
```

### Scenario A: PR is docs-only but audit ran

**Symptom**: L7 audit ran even though you only changed `.md` files.

**Likely cause**: the path filter doesn't match your files.

**Debug**:
```bash
# Pull PR's changed files
gh api /repos/hellob1889/Pandaone-AI-Agent/pulls/<PR>/files \
  --jq '.[] | .filename'
```

**Check against regex**:
```
^(CHANGELOG\.md|README[^/]*\.md|docs/.*|\.github/PULL_REQUEST_TEMPLATE(\.md|/.*)|\.github/ISSUE_TEMPLATE/.*|\.github/CODEOWNERS|\.github/CODE_OF_CONDUCT\.md|\.github/CONTRIBUTING\.md|\.github/SECURITY\.md|LICENSE[^/]*|NOTICE[^/]*)$
```

**Common misses**:
- `README.md` in subdirectory: not matched (regex is `README[^/]*\.md`, no `/`)
- `RELEASE.md` in root: not matched
- `RELEASE_NOTES_v0.7.2.md`: not matched
- `docs/asset.png`: not matched (only `.md` extension matters, but `docs/.*` matches anything under docs)

**Fix**: either add the file type to regex (modify audit.yml), or rename/restructure.

### Scenario B: PR has `[skip-audit]` but audit ran

**Likely cause**: marker is in commit body / footer, not subject.

**Debug**:
```bash
gh api /repos/hellob1889/Pandaone-AI-Agent/pulls/<PR>/commits \
  --jq '.[] | {sha: .sha[:7], subject: .commit.message | split("\n")[0], has_marker: (.commit.message | test("\\[skip-audit\\]"))}'
```

**Fix**: amend the commit so `[skip-audit]` is the FIRST line of the commit message.

```bash
git commit --amend -m "[skip-audit] <your commit message>"
git push --force-with-lease
```

### Scenario C: PR is genuinely code change

**Likely cause**: the change is a business code change requiring audit record.

**Fix**: you need to run `pandax ci` locally, fix issues, push:

```bash
pip install pandaone-guard
pandax ci --root . --base origin/main
# ... fix issues ...
git add -A
git commit -m "fix(audit): <fix description>"
git push
```

### Scenario D: Audit passes locally, fails on CI

**Likely cause**: `.pandax/` audit record directory not committed.

**Fix**: ensure `.pandax/` is committed in the PR.

---

## Publish failures

### 403 Invalid API Token (project-scoped)

```
HTTPError: 403 Forbidden
{"message": "Invalid API Token: project-scoped token 'pypi-...' is not valid for project: 'pandaone-guard'"}
```

**Cause**: `PYPI_API_TOKEN` secret is scoped to old package name.

**Fix**:
1. Delete secret via `https://github.com/hellob1889/Pandaone-AI-Agent/settings/secrets/actions`
2. Find `PYPI_API_TOKEN` row → click trash icon → confirm
3. Re-run failed jobs via browser (see release.md § 5)

### 403 pending publisher not configured

```
Trusted publishing not configured for pandaone-guard
```

**Cause**: PyPI doesn't have pending/active trusted publisher for this project.

**Fix**: configure at `https://pypi.org/manage/account/publishing/` (see release.md § 4.2).

### 404 project does not exist

```
404 The project 'pandaone-guard' does not exist
```

**Cause 1**: typo in distribution name in `pyproject.toml`.

**Cause 2**: pending publisher configured but PyPI requires project pre-creation.

**Fix**: PyPI actually does auto-create on first OIDC upload IF pending publisher is configured. If still 404:
- Verify pending publisher at `/manage/account/publishing/`
- Verify GitHub repo name matches exactly (case-sensitive)

### Invalid distribution filename

```
HTTPError: 400 Bad Request
File name 'pandaone_guard-0.7.6.tar.gz' is invalid
```

**Cause**: PyPI rejects filenames with version mismatch.

**Fix**: ensure `pyproject.toml version` matches tag (`v0.7.6` → `0.7.6`).

---

## Smoke tests failed

**Symptom**: `audit.yml` Smoke Tests job fails.

**Debug**: download logs:
```bash
# Via browser: Actions → run → click job → "Download log archive"
# Or extract:
curl -sL -H "Authorization: Bearer <GH_TOKEN>" \
  https://api.github.com/repos/hellob1889/Pandaone-AI-Agent/actions/runs/<RUN_ID>/logs \
  -o logs.zip
unzip logs.zip
cat "Smoke Tests/1_*.txt"
```

**Common causes**:
- Missing `__init__.py` in new module
- Circular import introduced
- New required dependency not in `pyproject.toml`

---

## Lint failed

**Symptom**: `Lint Summary` check fails.

**Common causes**:
- Import order wrong (`isort` would fix)
- Trailing whitespace
- Missing docstring on public function
- Print statement left in source

**Fix locally**:
```bash
# Install dev deps
pip install -e .[dev]

# Run linters
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

---

## i18n Coverage failed

**Symptom**: A new CLI string lacks en/zh translation.

**Debug**: log shows which key is missing.

**Fix**:
```bash
# Find string in source
grep -rn '<missing_key>' src/

# Add to both:
# src/pandaone/i18n.py (en dict)
# docs/zh/commands.md or similar (zh dict)
```

---

## i18n Hardcoded Chinese failed

**Symptom**: Hardcoded Chinese string detected in `src/` (outside `i18n.py`).

**Fix**: extract to `i18n` dict, use `_('key')` lookup.

---

## Build wheel + sdist failed

**Symptom**: `publish.yml` Build job fails.

**Common causes**:
- `pyproject.toml` syntax error: validate with `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
- Missing `MANIFEST.in` for non-Python files
- Invalid version string: must be PEP 440 (`X.Y.Z` or `X.Y.Za1`, no leading `v`)

---

## How to download logs (general)

```bash
# Browser: Actions → run → top-right "..." → Download logs

# API (works for read):
curl -sL -H "Authorization: Bearer <GH_TOKEN>" \
  -o logs.zip \
  https://api.github.com/repos/hellob1889/Pandaone-AI-Agent/actions/runs/<RUN_ID>/logs
unzip logs.zip -d logs/
cat logs/<Job>/<step>.txt
```

**Note**: GitHub App integration tokens lack `actions:write` (rerun/delete) but DO have `actions:read` (logs).
