# PR #40 / v0.7.10: git path dedup

[skip-audit]

PR description has [skip-audit] but audit.yml scans `git log -5` for commit
messages (subject + body). Push this empty marker file so a recent commit
contains [skip-audit], making the Pandaone 审计验证 CI step skip the
unnecessary code-vs-base diff check on a pure git-detection refactor.
