# PandaX 文档（中文）

> **AI Agent 代码审计门禁** — 让每一次代码改动都留下合规、可追溯的证据链。

## 快速导航

- [安装](install.md) — 一行命令在任何平台安装
- [快速开始](quickstart.md) — 5 分钟上手
- [7 层防御体系](defense-layers.md) — 详细解释每层的工作原理
- [命令参考](commands.md) — 所有 CLI 命令
- [MCP 集成](mcp-integration.md) — AI Agent 直连
- [CI/CD 集成](ci-integration.md) — GitHub Actions 自动化
- [示例集](../EXAMPLES.md) — 10 个真实工作流
- [实战验证报告](../实战验证报告.md) — 7 层防御的实战测试
- [English Documentation](../en/index.md)

## 是什么？

PandaX 是一个 **7 层防御体系**，强制 AI Agent（或任何开发者）写代码前必须经过审计。
任何受保护文件的修改都必须通过 `pandax write` 命令，留下 reason / problem / approach 三段式审计记录。

## 适用场景

- 🤖 **AI Agent 开发** — 防止 Agent 绕过审查直接改代码
- 🏢 **企业合规** — 满足 SOC2 / ISO 27001 等代码变更审计要求
- 👥 **团队协作** — 所有 PR 必须有审计记录才能合入

## 核心特性

- **17 种文本格式 + 24 种二进制格式保护**（`.py` / `.md` / `.json` / `.yml` / `.env` / `.png` / `.pdf` / ...）
- **7 层防御体系**（L1-L7 详见 [defense-layers.md](defense-layers.md)）
- **MCP Server 原生支持** — Claude / Cursor / Trae 等 AI IDE 直连
- **13 种审计日志导出格式**（Excel / Word / PDF / SQLite / ...）
- **纯 Python** — Windows / macOS / Linux 通吃，**无 C 扩展**

## 一行安装

```bash
pip install pandax-guard
```

立即试用：[快速开始](quickstart.md) → [示例集](../EXAMPLES.md)