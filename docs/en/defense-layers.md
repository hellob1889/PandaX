# 7 Defense Layers

Pandaone AI Agent's core is **redundant defense** — any modification must bypass at least 5 of L1-L7 to succeed.
Each layer **operates independently** and **backs up the others**.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Protected Files                          │
│  main.py  README.md  config.json  .env  logo.png  report.pdf │
└─────────────────────────────────────────────────────────────┘
         ↓ ↑           ↓ ↑           ↓ ↑            ↓ ↑
    L1 file lock    L2 watchdog    L3 hook       L6 binary
    (chmod -w)     (realtime)    (git commit)    (SHA256)
                                          ↓
                                    L7 CI verification
                                    (PR merge gate)

Metadata above all layers:
  L4 README startup          L5 self-fingerprint
```

## Layer Details

### L1: file chmod lock

**Purpose**: OS-level read-only enforcement.

**Implementation**:
- Windows: `attrib +R file.py`
- macOS/Linux: `chmod 444 file.py`

**Bypass difficulty**: Low (root can chmod +w)

**Backup layer**: L2 watchdog via file modification events.

### L2: watchdog real-time monitoring

**Purpose**: Background daemon monitors all protected files.

**Implementation**: watchdog library + audit token mechanism.

**Detection**:
- Any file modification → check if it's during pandaone write (has audit_token)
- If no audit_token → git checkout HEAD to revert + log UNAUTHORIZED

**Bypass difficulty**: Medium (must kill watchdog process first)

**Backup layer**: L3 hook (validate at git commit time).

### L3: pre-commit hook

**Purpose**: Prevent unaudited code from entering git history.

**Implementation**: `pre-commit-check.py` (Python validation logic)

**Validation**:
```python
for staged_file in git_diff_cached:
    if staged_file not in audit_log.approved_files:
        exit(1)  # reject commit
```

**Bypass difficulty**: Medium (attacker can use `--no-verify`)

**Backup layer**: L7 CI (re-validate at PR merge).

### L4: README startup load

**Purpose**: CLI loads project metadata (current phase, completed steps) on startup.

**Implementation**: Auto-load project root `.pandaone/README` on every run.

**Value**: Makes audit gate visible in project's **daily workflow** (transparent).

### L5: self-fingerprint

**Purpose**: Prevent CLI itself from being tampered.

**Implementation**: SHA256 of CLI code, stored in `~/.pandaone_fp.txt`.

**Validation**: Every CLI startup.

**Bypass difficulty**: Very high (must modify fingerprint storage + recompute all hashes).

### L6: binary SHA256 snapshot

**Purpose**: Protect images, PDFs, Word files, etc.

**Implementation**: SHA256 dictionary built on init, updated on write.

**Validation**: Watchdog detects binary modification, compares SHA256.

**Bypass difficulty**: Low (write auto-updates snapshot) — but **audit log records the change**.

### L7: GitHub Actions CI

**Purpose**: Final validation before PR merge.

**Implementation**: `pandaone ci --root . --base origin/main`

**Validation**:
```bash
# PR-modified files vs audit log APPROVED records
git diff --name-only origin/main..HEAD
for each file:
    if file not in audit_log.approved_files:
        FAIL  # PR rejected
```

**Bypass difficulty**: Very high (must modify main branch + bypass GitHub permissions).

---

## Adversarial Analysis

| Attack | Attack Path | Defense |
|---|---|---|
| Attacker chmod +w modifies file | L1 → L2 backup | L2 |
| Attacker kills watchdog | L2 → L3 backup | L3 |
| Attacker uses `--no-verify` | L3 → L7 backup | L7 |
| Attacker modifies pandaone CLI | L5 detects mismatch → L4 startup fails | L5 |
| Attacker modifies .gitignore | L1 lock + L2 monitor | L1+L2 |
| Attacker overwrites .png | L1 lock + L6 SHA256 mismatch | L1+L6 |
| Attacker pushes directly to main | GitHub branch protection | (GitHub settings) |

**Conclusion**: 7 layers is **defense in depth** — bypassing one is not fatal.

---

## First Principles

> **Audit is "every change has evidence"** — evidence = audit log entry = reason/problem/approach.
> 7-layer defense makes **"changes without evidence" impossible**, not "changes impossible".
> The distinction: blocking only delays attacks; **leaving traces is the essence of audit**.

---

[← Home](index.md) | [Commands](commands.md) | [Validation Report](../../实战验证报告.md)