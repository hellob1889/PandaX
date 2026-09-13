# Pandaone AI Agent — Operations Runbook

> **This runbook is for maintainers operating the project**, not for end users.
> For end-user install/usage docs, see `README.md` and `docs/`.

## What this is

Operationally verified procedures for:
1. **Releasing** a new version (PyPI + GitHub Release)
2. **Troubleshooting** CI failures (L7 audit, publish, i18n, smoke tests)
3. **Responding** to incidents (token leak, package hijack, bad release, etc.)

## Why a runbook exists

Each release cycle hits recurring issues. Without documentation, every maintainer
re-discovers the same quirks. This runbook is the operational memory.

## Documents

| Document | When to read | Audience |
|---|---|---|
| [`release.md`](./release.md) | Planning a release, doing PyPI/Trusted Publisher setup | Releaser |
| [`ci-troubleshooting.md`](./ci-troubleshooting.md) | A CI check failed, publish run failed, audit failed | On-call |
| [`incident-response.md`](./incident-response.md) | Something bad happened (leak, hijack, error shipped) | Incident commander |

## How to use

1. **Before** doing any release operation, skim the relevant doc end-to-end (5 min).
2. **During** the operation, follow the checklist literally. Don't improvise.
3. **After** the operation, if you hit a case the runbook doesn't cover, **add it**.
   The runbook is a living document — staleness is a smell that the process changed.

## First principles

> **Publishing = letting anyone `pip install` and use the tool in 1 command.**
> Every step in this runbook serves that goal.

> **Trust comes from documentation.** A security/compliance tool whose own
> operations are undocumented has no credibility.

> **Automation over memorization.** Every manual step here should be a candidate
> for future automation.

## Conventions

- ✅ = step is verified to work in this environment
- ❌ = step fails / avoid
- 🐛 = known issue, see explanation
- 🔑 = requires maintainer credentials (you must obtain these yourself)

## Versioning the runbook

The runbook is committed to `main` alongside code. When the process changes:
1. Open a docs-only PR
2. Update the affected file
3. (Optional) Tag a release if the change is material

## Audit trail

For audit purposes (regulatory / compliance):
- Every release run has a GitHub Actions run ID — archive it
- Every PyPI upload has a SHA in the wheel metadata — record it
- Every incident response should generate a dated incident report
