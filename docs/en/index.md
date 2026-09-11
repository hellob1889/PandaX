# Pandaone AI Agent Documentation (English)

> **AI Agent Code Audit Gateway** — Every code change leaves a compliant, traceable evidence chain.

## Quick Navigation

- [Install](install.md) — One-line install on any platform
- [Quick Start](quickstart.md) — 5 minutes to first audit write
- [7 Defense Layers](defense-layers.md) — How each layer works
- [Commands](commands.md) — Complete CLI reference
- [MCP Integration](mcp-integration.md) — AI Agent direct connect
- [CI Integration](ci-integration.md) — GitHub Actions automation
- [Examples](../../EXAMPLES.md) — 10 real workflows
- [Validation Report](../../实战验证报告.md) — 7-layer defense real-world test
- [中文文档](../zh/index.md)

## What is it?

Pandaone is a **7-layer defense system** that forces every code change through an audit gate.
Any modification to a protected file (17 text + 24 binary formats) must go through `pandaone write`,
which records reason / problem / approach as immutable audit evidence.

## Use Cases

- 🤖 **AI Agent development** — Prevent agents from bypassing review
- 🏢 **Enterprise compliance** — Meet SOC2 / ISO 27001 code change audit requirements
- 👥 **Team collaboration** — Every PR must have audit records before merging

## Core Features

- **17 text formats + 24 binary formats protected** (`.py` / `.md` / `.json` / `.yml` / `.env` / `.png` / `.pdf` / ...)
- **7 defense layers** (L1-L7, see [defense-layers.md](defense-layers.md))
- **MCP Server native support** — Direct integration with Claude / Cursor / Trae AI IDEs
- **13 audit log export formats** (Excel / Word / PDF / SQLite / ...)
- **Pure Python** — Windows / macOS / Linux, **no C extensions**

## One-line Install

```bash
pip install pandaone-guard
```

Try it now: [Quick Start](quickstart.md) → [Examples](../../EXAMPLES.md)