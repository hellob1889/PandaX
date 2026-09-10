# CI/CD Integration

> **Auto-audit every PR** — L7 defense.

## GitHub Actions (Recommended)

`.github/workflows/audit.yml`:

```yaml
name: PandaX CI
on:
  pull_request:
    branches: [main, master, develop]
  push:
    branches: [main, master]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install pandax-guard
      - run: pandax ci --root . --base origin/main
```

## GitLab CI

`.gitlab-ci.yml`:

```yaml
audit:
  stage: test
  image: python:3.10
  before_script:
    - pip install pandax-guard
  script:
    - pandax ci --root . --base origin/main
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

## Output Example

```
================================================================
[FAIL] Detected 2 unaudited changes:

  [text  ] src/auth.py      Reason: No APPROVED audit record found
  [binary] assets/icon.ico  Reason: SHA256 mismatch (snapshot=abc, actual=def)

{"status":"FAIL","violations":2,"changed":5}
```

## Fix Workflow

```bash
pandax write --file src/auth.py \
    --reason "..." --problem "..." --approach "..." \
    --old "..." --new "..."

pandax write --file assets/icon.ico \
    --reason "..." --problem "..." --approach "..." \
    --from-file /tmp/new_icon.ico

git add -A
git commit -m "fix: address CI audit feedback"
git push
```

---

[← Home](index.md) | [Commands](commands.md) | [GitHub](https://github.com/hellob1889/PandaX)