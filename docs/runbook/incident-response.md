# Incident Response Runbook

> **Audience**: incident commander when something bad happens.
> **Goal**: minimize blast radius, recover service, document for postmortem.

## Severity classification

| Severity | Definition | Response time | Examples |
|---|---|---|---|
| **SEV-1** | Production users affected, data integrity at risk | < 1 hour | Compromised publish token, malicious release shipped, package hijack |
| **SEV-2** | Release pipeline broken, no user impact yet | < 4 hours | CI broken, PyPI upload failing for all releases |
| **SEV-3** | Single release issue, workaround available | < 1 day | One CI check flaky, one release version has cosmetic issue |

---

## SEV-1: PyPI publish token compromised

**Symptom**: API token leaked to public (e.g., committed to repo, posted in public Slack).

**Immediate actions (within 15 min)**:

```bash
# 1. Disable token at PyPI
#    https://pypi.org/manage/account/token/
#    Find leaked token → click "Remove" → confirm

# 2. Remove from GitHub secrets
#    https://github.com/hellob1889/Pandaone-AI-Agent/settings/secrets/actions
#    Delete the secret

# 3. If we have secret rotation: generate new token, update secret
#    (otherwise rely on OIDC only, which doesn't need a token)
```

**Then**:
- Search GitHub for leaked token string (if in repo, GitHub auto-revokes via secret scanning, but verify)
- Audit PyPI release history for unauthorized uploads:
  ```bash
  curl -s "https://pypi.org/pypi/<pkg>/json" | jq '.releases | to_entries | .[] | .value | .[] | {filename, upload_time}'
  ```
- Notify users via GitHub Security Advisory if unauthorized release exists

**Communication**: file GitHub Security Advisory at `/hellob1889/Pandaone-AI-Agent/security/advisories/new`.

---

## SEV-1: Malicious release shipped

**Symptom**: A release with malicious code was published (e.g., compromised maintainer account).

**Immediate actions**:

```bash
# 1. Yank the release on PyPI (does NOT delete, but hides from pip install --upgrade)
#    https://pypi.org/manage/project/<pkg>/release/<version>/
#    Click "Options" → "Yank"

# 2. Pin the previous known-good version in installation instructions
#    Update README + docs: "pip install pandaone-guard==0.7.6" (not latest)

# 3. Delete GitHub Release for the bad version
gh release delete v0.7.X --yes

# 4. If code was injected: revert on main
git revert <bad-commit-sha>
git push
git tag v0.7.X+1
git push origin v0.7.X+1

# 5. Audit PyPI downloads for the bad version
#    (PyPI doesn't expose this to maintainers; check mirrors or bug reports)
```

**Postmortem**:
- How did malicious code enter?
- Was it a compromised account or compromised PR?
- What detection failed?

---

## SEV-1: Package name hijacked

**Symptom**: Your PyPI package name (`pandax-guard`, `pandaone-guard`, etc.) was registered by another user (typo squatting, brand squatting, name expiration claim).

**Actions**:

```bash
# 1. Check current owner
curl -s "https://pypi.org/pypi/<pkg>/json" | jq '.info | {name, author, home_page}'

# 2. File PyPI support ticket
#    https://pypi.org/help/
#    Include: your project history, prior ownership evidence

# 3. If you can recover: follow PyPI admin instructions
#    If you cannot recover: rename your package, update all docs, migration guide
```

**Prevention**:
- Register all foreseeable package names upfront (including common typos)
- Set up PyPI email notification for any new release of YOUR project

---

## SEV-2: CI broken for all releases

**Symptom**: Latest main passes local tests but CI fails on every PR.

**Diagnosis**:

```bash
# Check if it's a single check or multiple
gh pr checks <PR_NUMBER>

# Download logs
curl -sL -H "Authorization: Bearer <GH_TOKEN>" \
  -o logs.zip \
  https://api.github.com/repos/hellob1889/Pandaone-AI-Agent/actions/runs/<RUN_ID>/logs
unzip logs.zip -d logs/
ls logs/
```

**Common causes**:
- `audit.yml` workflow syntax error: fix the YAML, push
- `pandax ci` missing in CI environment: add `pip install pandaone-guard` step
- GitHub Actions runner deprecation: see `actions/setup-python@v5` node 20 warning

**Fix**: open a "ci: fix" PR against `main` with the diagnosis + fix.

---

## SEV-3: One release has cosmetic issue

**Symptom**: v0.7.X released, but README has typo or CHANGELOG is incomplete.

**Actions**:

```bash
# 1. Open docs-only PR to fix
git checkout -b docs/fix-v077-typo
# ... fix ...
git commit -m "docs: fix README typo in v0.7.7"
git push origin docs/fix-v077-typo

# 2. This PR auto-skips audit (docs-only)
gh pr create --base main --head docs/fix-v077-typo
# ... merge ...

# 3. Do NOT tag a new release for typo fixes
#    The CHANGELOG history shows what was actually fixed in each version
```

---

## Detection: how to know about incidents

| Source | Catches |
|---|---|
| PyPI email notifications | New package releases (configurable) |
| GitHub Security tab | Secret scanning alerts, Dependabot |
| GitHub Issues | User bug reports |
| Social media / Twitter | Public reputation issues |
| CI failure alerts (if configured) | Build failures |

**Setup checklist**:
- [ ] Configure PyPI to email you on new release of YOUR packages
- [ ] Enable GitHub secret scanning (Settings → Code security)
- [ ] Enable Dependabot (already done in this project)

---

## Postmortem template

After every SEV-1/2, write a postmortem. Template:

```markdown
# Postmortem: <incident-title>

**Date**: YYYY-MM-DD
**Severity**: SEV-X
**Duration**: <start-time> to <end-time>
**Reporter**: <name>
**Resolver**: <name>

## What happened
<2-3 sentence summary>

## Timeline (UTC)
- HH:MM — <event>
- HH:MM — <event>
- ...

## Root cause
<What actually caused it>

## Detection
<How did we find out? How long from incident to detection?>

## Impact
<Who/what was affected?>

## Recovery actions
<What did we do to fix?>

## Lessons learned
<What should we change to prevent this?>

## Action items
- [ ] <action 1> (owner: <name>, deadline: <date>)
- [ ] <action 2> ...
```

Store postmortems at `docs/postmortem/YYYY-MM-DD-<slug>.md`.

---

## Communication templates

### User-facing (when we broke something)

```markdown
> ## Notice: v0.7.X install issue
>
> **Affected versions**: v0.7.X
> **Severity**: <sev>
> **Fix**: <action user needs to take>
>
> ### What happened
> <summary>
>
> ### What to do
> ```bash
> pip uninstall pandaone-guard
> pip install pandaone-guard==0.7.X-1
> ```
>
> ### Timeline
> - YYYY-MM-DD HH:MM UTC: v0.7.X published
> - YYYY-MM-DD HH:MM UTC: issue detected
> - YYYY-MM-DD HH:MM UTC: fix released
>
> Full details: <link to issue or postmortem>
```

### Internal (when investigating)

Use a temporary incident channel (Slack/Discord/email):
```
[SEV-X] <one-line summary>
Status: investigating / identified / mitigating / resolved
IC: <name>
Next update in 15 min
```

---

## First principles

> **Speed of recovery > speed of root cause.** Get users working first, then investigate.
>
> **Document while fresh.** Postmortem written 1 hour after incident = useful. Written 1 week after = fiction.
>
> **Single IC per incident.** Multiple decision-makers cause chaos. One IC makes calls, others execute.
>
> **No blame.** Humans make mistakes. Systems fail. Ask "what allowed this?" not "who did this?"
