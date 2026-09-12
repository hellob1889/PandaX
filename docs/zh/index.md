# Pandaone AI Agent 文档（中文）

> **AI Agent 代码审计门禁** — 让每一次代码改动都留下合规、可追溯的证据链。

## 🧑‍💼 Pandaone 是你代码库的专属经理 / Pandaone is your codebase's personal manager

每个 AI agent 都是你公司的员工 —— 你的代码库就是那家公司。没有专属经理，员工想干什么就干什么 —— 改文件、推提交、搞崩生产 —— 你完全不知道是谁干的、什么时候干的、为什么。

**Pandaone 是你雇来保护代码的专属经理。** 每一个 AI agent —— Claude、Cursor、Trae，或者你明天会采用的任何工具 —— 都必须先向 Pandaone 报备。任何代码改动、任何 git commit、任何部署动作，都要 Pandaone 签字盖章才会放行，并留下可审计的凭证：

```
┌─────────────────────────────────────────────┐
│ [APPROVED]                  2026-09-11 03:47 │
│ File:      src/payment.py                    │
│ Agent:     Claude Code（员工 #3）              │
│ Reason:    "修复四舍五入错误"                  │
│ Problem:   "5 万元账单算成 50,001 元"            │
│ Approach:  "转账前先取整，不要转账后取整"         │
│ Commit:    a3f7b2c                           │
└─────────────────────────────────────────────┘
```

没有专属经理，你的 AI 在转钱 —— 呃，是转代码 —— 但没有凭证：

```
没有 Pandaone          有了 Pandaone
──────────────          ──────────────
$50,000 ???            $50,000  src/payment.py
                        Reason:  "修复四舍五入"
                        By:      Claude Code
                        When:    2026-09-11 03:47
                        Commit:  a3f7b2c
```

**左边这一列，是今天大多数被 AI agent 改过的代码库的样子。**
**右边这一列，是你的代码库用一行命令就能变成的样子：**

```bash
pip install pandax-guard
```

你的专属经理 24/7 值班 —— **每一次代码改动的前、中、后都在场**。每一个 AI agent —— Claude、Cursor、Trae —— 都在同一条可审计的协议下工作。**无例外。不许绕行。**

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

Pandaone 是一个 **7 层防御体系**，强制 AI Agent（或任何开发者）写代码前必须经过审计。
任何受保护文件的修改都必须通过 `pandaone write` 命令，留下 reason / problem / approach 三段式审计记录。

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