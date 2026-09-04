# MCP Integration

> **Let AI Agents (Claude / Cursor / Trae) directly call PandaX.**

## What is MCP?

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is a standard protocol for AI Agents to call external tools via stdio JSON-RPC.

PandaX implements as a **stdio JSON-RPC 2.0 server** — **no network exposure**, IDE-managed process lifecycle.

## Client Configuration

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pandax": {
      "command": "pandax-mcp",
      "env": {}
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pandax": {
      "command": "pandax-mcp"
    }
  }
}
```

## 11 Tools Exposed

| Tool | Purpose |
|---|---|
| `pandax_init` | Initialize PandaX in directory |
| `pandax_lock` | Lock all protected files |
| `pandax_unlock` | Unlock |
| `pandax_write` | Audit write (core) |
| `pandax_log` | Query audit history, 13 export formats |
| `pandax_status` | Show project status dashboard |
| `pandax_install_hook` | Install L3 pre-commit hook |
| `pandax_watch` | Start watchdog daemon |
| `pandax_install_git` | Probe/install git |
| `pandax_fingerprint_update` | Update CLI self-fingerprint |
| `pandax_ci` | L7 CI verification |

## Why stdio over HTTP?

- ✅ **Zero network exposure** (no ports, no auth)
- ✅ IDE-managed process (start/restart/sandbox)
- ✅ Standard protocol (any MCP client works)
- ✅ Low latency (no HTTP overhead)

## Test MCP Manually

```bash
pandax-mcp &
echo '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}' | pandax-mcp
```

Full demo: [examples/04_mcp_client.py](../../examples/04_mcp_client.py)

---

[← Home](index.md) | [CI Integration](ci-integration.md)