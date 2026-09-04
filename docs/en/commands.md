# Commands

Complete CLI command reference. All commands support `--root <path>` (default: cwd).

## init — Initialize project

```bash
pandax init [--root PATH]
```

Creates `.pandax/` with:
- `config.json` — 17 text + 24 binary extensions
- `pandax.jsonl` — audit log (JSON Lines)
- `binary_snapshots.json` — binary SHA256 dictionary

## lock / unlock

```bash
pandax lock [--root PATH]
pandax unlock [--root PATH]
```

Windows: `attrib +R` / `-R`
macOS/Linux: `chmod 444` / `chmod 644`

## write — Audit write (core)

```bash
pandax write \
    --file <RELATIVE_PATH> \
    --reason "change reason" \
    --problem "problem solved" \
    --approach "approach used" \
    [--old "old"] [--new "new"] \
    [--content "full new content"] \
    [--from-file <PATH>] \
    [--content-base64 "BASE64"]
```

**Text**: use `--old/--new` or `--content`
**Binary**: use `--from-file` or `--content-base64`

`--reason` / `--problem` / `--approach` are **mandatory**.

## log — Audit history

```bash
pandax log [--root PATH] [--last N] [--status STATUS]
pandax log --format <fmt> --output <file>
```

13 export formats: text/txt, csv/tsv, json, yaml/yml, md/markdown, html, xlsx/excel, docx/word, pdf, sqlite/db, rst, asciidoc/adoc

## status — Project status dashboard

```bash
pandax status [--root PATH]
```

Shows: L1 lock, L2 watchdog, L5 fingerprint, audit stats, recent audits, Phase 5 binary snapshots.

## install-hook — Install L3 pre-commit hook

```bash
pandax install-hook [--root PATH]
```

Requires: `.git/` directory.

Installs:
- `.git/hooks/pre-commit` — shell launcher
- `.pandax/pre-commit-check.py` — Python validation

## watch — Start L2 watchdog

```bash
pandax watch [--root PATH] [--daemon]
```

`--daemon`: background mode, writes PID to `.pandax/.watchdog_pid`.

## install-git — Auto-install git

```bash
pandax install-git
```

## ci — L7 CI verification

```bash
pandax ci [--root PATH] [--base REF]
```

**base**: baseline ref (default `HEAD~1`)

Exit codes: 0 = all audited, 1 = unaudited changes found.

## update-fingerprint — Update CLI self-fingerprint

```bash
pandax --update-fingerprint <CODE>
```

## MCP

`pandax-mcp` — Start MCP server (stdio JSON-RPC).

Exposes 11 tools for AI Agents (Claude / Cursor / Trae).

See [MCP Integration](mcp-integration.md).

---

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Rejected (CI failure / bypass blocked / validation failed) |
| 2 | Git working directory dirty |
| 3 | Tests failed |
| 4 | Build failed |
| 5 | Metadata invalid |
| 6 | Upload failed |

---

[← Home](index.md) | [Defense Layers](defense-layers.md) | [MCP](mcp-integration.md)