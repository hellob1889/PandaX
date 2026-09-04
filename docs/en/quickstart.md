# Quick Start

> **5 minutes to first audit write.**

## Step 1: Install (30s)

```bash
pip install pandax
pandax --version
# pandax v0.6.2
```

## Step 2: Init Project (10s)

```bash
cd /path/to/your-project
pandax init --root .
```

Creates:
- `.pandax/config.json` — 17 text + 24 binary extensions
- `.pandax/pandax.jsonl` — audit log
- `.pandax/binary_snapshots.json` — binary SHA256

## Step 3: Lock Files (5s)

```bash
pandax lock --root .
```

**All protected files become read-only**:
```
[OK] Locked 12 files (protected extensions: .py, .pyx, .json, ...)
```

## Step 4: Audit Write (30s)

Don't edit directly — use `pandax write`:

```bash
pandax write \
    --file src/main.py \
    --reason "Fix user ID type annotation" \
    --problem "Original used int, could be None" \
    --approach "Change to Optional[int]" \
    --old 'def get_user(user_id: int):' \
    --new 'def get_user(user_id: Optional[int]):'
```

Output:
```
[APPROVED] {"status":"APPROVED","commit":"3d52141","audit_id":"audit_xxx","file":"src/main.py"}
```

## Step 5: View Audit History (10s)

```bash
# CLI
pandax log --last 10

# Export to Excel
pandax log --format xlsx --output audit.xlsx

# Export to PDF (with Chinese support)
pandax log --format pdf --output audit.pdf
```

## Step 6: Status (5s)

```bash
pandax status --root .
```

Shows L1 lock, L2 watchdog, L5 fingerprint, recent audits.

---

## Next

- **Protect Git commits**: `pandax install-hook --root .`
- **Background monitoring**: `pandax watch --root . --daemon`
- **AI Agent integration**: [MCP Server](mcp-integration.md)
- **CI integration**: [CI/CD](ci-integration.md)

## Full Examples

[EXAMPLES.md](../../EXAMPLES.md) | [Validation Report](../../实战验证报告.md)