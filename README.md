<p align="center">
  <img src="assets/banner-readme.svg" alt="PandaX — AI Agent 代码审计门禁" width="800"/>
</p>

# PandaX

<p align="center">
  <img src="assets/icon-github.svg" alt="PandaX Logo" width="96" height="96"/>
</p>

> **AI Agent 代码审计门禁** — 让每一次代码改动都留下合规、可追溯的证据链。

[![PyPI version](https://img.shields.io/pypi/v/pandax?color=blue)](https://pypi.org/project/pandax/)
[![Python](https://img.shields.io/pypi/pyversions/pandax)](https://pypi.org/project/pandax/)
[![License](https://img.shields.io/pypi/l/pandax)](https://github.com/pandax/pandax/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-191%20passed-brightgreen)](https://github.com/pandax/pandax)
[![i18n](https://img.shields.io/badge/i18n-184%2F184%20keys%20100%25-blueviolet)](https://github.com/pandax/pandax/blob/main/docs/i18n.md)
[![Lint & i18n CI](https://img.shields.io/badge/Lint%20%26%20i18n-passing-success)](https://github.com/pandax/pandax/blob/main/.github/workflows/lint.yml)
[![OS](https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://pypi.org/project/pandax/)
[![Phase](https://img.shields.io/badge/status-v0.7.0%20production--ready-success)](https://github.com/pandax/pandax/releases)

[English](#english) | [中文](#中文)

---

## 中文

### 是什么？

PandaX 是一个 **7 层防御体系**，强制 AI Agent（或任何开发者）写代码前必须经过审计：
任何受保护文件的修改都必须通过 `pandax write` 命令，留下 reason / problem / approach 三段式审计记录。

**适用场景**：
- 🤖 AI Agent 开发：防止 Agent 绕过审查直接改代码
- 🏢 企业合规：满足 SOC2 / ISO 27001 等代码变更审计要求
- 👥 团队协作：所有 PR 必须有审计记录才能合入

### 核心特性

- **17 种文本格式 + 24 种二进制格式保护**（`.py` / `.md` / `.json` / `.yml` / `.env` / `.png` / `.pdf` / ...）
- **7 层防御体系**（详见 [防御体系](#防御体系)）
- **MCP Server 原生支持** — Claude / Cursor / Trae 等 AI IDE 直连
- **13 种审计日志导出格式**（Excel / Word / PDF / SQLite / ...）
- **纯 Python** — Windows / macOS / Linux 通吃，**无 C 扩展**
- **右键菜单集成** — 一行命令在 3 大平台安装原生右键菜单（HKCU / Quick Action / Nautilus + Dolphin）
- **i18n 国际化** — `zh-CN` / `en` 双语 CLI 自动检测 + `--lang` 强制 + 持久化偏好

### 快速开始

#### 安装

```bash
pip install pandax

# 一键装上右键菜单（Windows / macOS / Linux 自动检测）
pandax install-context
```

#### 初始化项目

```bash
cd /path/to/your-project
pandax init --root .
# 自动：
#   - 创建 .pandax/ 目录
#   - 生成 config.json（17 文本 + 24 二进制扩展名）
#   - 创建 binary_snapshots.json（SHA256 字典）
#   - 初始化 .gitignore 排除
```

#### 写代码（合规路径）

```bash
# 修改 Python 文件
pandax write \
    --file src/main.py \
    --reason "修复 user_id 类型注解" \
    --problem "原代码用 int，实际可能是 None" \
    --approach "改为 Optional[int]" \
    --old 'def get_user(user_id: int):' \
    --new 'def get_user(user_id: Optional[int]):'

# 替换二进制文件（图片/文档/PDF 等）
pandax write \
    --file assets/logo.png \
    --reason "更新品牌 logo" \
    --problem "旧 logo 与新品牌色不匹配" \
    --approach "用新版 logo 替换" \
    --from-file /tmp/new_logo.png
```

#### 查看审计日志

```bash
# 命令行查看
pandax log --last 10

# 导出为 Excel
pandax log --format xlsx --output audit_report.xlsx

# 导出为 PDF（含中文支持）
pandax log --format pdf --output audit_report.pdf

# 全部 13 种格式：text / csv / tsv / json / yaml / md / html / xlsx / docx / pdf / sqlite / rst / asciidoc
```

#### 项目状态仪表盘

```bash
pandax status --root .
```

显示：项目路径、配置摘要、L1 锁定状态、二进制快照、最近审计、版本指纹等。

### 防御体系（7 层）

| 层 | 组件 | 作用 | 被绕过后的兜底 |
|---|---|---|---|
| **L1** | file chmod | 文件级只读锁（attrib +r / chmod -w）| L2 watchdog |
| **L2** | watchdog | 实时文件监控 + git checkout 回滚 | L3 hook |
| **L3** | pre-commit hook | 严格校验每个 staged 文件的 APPROVED 记录 | L4 / L5 |
| **L4** | 启动读 README | CLI 启动时加载项目元数据 | L5 |
| **L5** | 自指纹 | CLI 自身 SHA256 检测篡改 | L6 |
| **L6** | 二进制 SHA256 snapshot | 检测 .png/.pdf 等二进制篡改 | L7 |
| **L7** | GitHub Actions CI | PR 合入前审计验证（最终兜底）| 人工 review |

### MCP Server（AI Agent 直连）

```json
// claude_desktop_config.json 或 Cursor MCP 配置
{
  "mcpServers": {
    "pandax": {
      "command": "pandax-mcp",
      "env": {}
    }
  }
}
```

暴露 **11 个工具**：`pandax_init` / `pandax_lock` / `pandax_unlock` / `pandax_write` / `pandax_log` / `pandax_status` / `pandax_install_hook` / `pandax_watch` / `pandax_install_git` / `pandax_fingerprint_update` / `pandax_ci`

### 真实场景测试

完整实战验证报告：[实战验证报告.md](实战验证报告.md)

包含：
- 7 层防御每层实战证据
- L3 hook 严重 bug 的发现 + 修复
- 隐藏文件锁定 bug 的发现 + 修复
- 13 种导出格式实测
- MCP 协议完整工作流

### 详细示例集

- [EXAMPLES.md](EXAMPLES.md) — 10 个真实工作流 + 终端输出
- [examples/](examples/) — 5 个可运行的 Python demo 脚本
- [docs/](docs/) — 中英双语文档站（mkdocs）
- [docs/index.html](docs/index.html) — 交互式 HTML 文档首页（带终端动画）

### 命令清单

| 命令 | 用途 |
|---|---|
| `pandax init` | 初始化项目 |
| `pandax lock` / `unlock` | 锁定 / 解锁所有受保护文件 |
| `pandax write` | **核心**：审计写入（支持文本/二进制） |
| `pandax log` | 查询审计历史（13 种导出格式） |
| `pandax status` | 项目状态仪表盘 |
| `pandax install-hook` | 安装 L3 pre-commit hook |
| `pandax watch` | 启动 L2 watchdog 守护进程 |
| `pandax install-git` | 自动安装 git |
| `pandax ci` | L7 CI 验证（git diff vs audit log）|
| `pandax-mcp` | 启动 MCP server（stdio JSON-RPC） |

### 开发与测试

```bash
git clone https://github.com/pandax/pandax
cd pandax
pip install -e .[dev]
pytest tests/ -v
```

当前测试数：**140 passed**

### 路线图

| 版本 | 状态 | 关键能力 |
|---|---|---|
| v0.1.0 | ✅ | Phase 1-3 MVP（5 层防御） |
| v0.2.0 | ✅ | 多格式导出（7 种） |
| v0.3.0 | ✅ | 17 种文本保护 |
| v0.4.0 | ✅ | 24 种二进制 SHA256 |
| v0.5.0 | ✅ | MCP Server |
| v0.6.0 | ✅ | GitHub Actions CI |
| v0.6.1 | ✅ | L3 hook 强化（实战验证） |
| **v0.6.2** | ✅ | 隐藏文件锁定 bug 修复 |
| **v0.7.0** | ✅ | Phase 9 OS 右键菜单（Windows HKCU / macOS Quick Action / Linux Nautilus+Dolphin） |

完整历史：[CHANGELOG.md](CHANGELOG.md)

### 许可

MIT License — 详见 [LICENSE](LICENSE)

---

## English

### What is it?

PandaX is a **7-layer defense system** that forces every code change through an audit gate.
Any modification to a protected file (17 text + 24 binary formats) must go through `pandax write`,
which records reason / problem / approach as immutable audit evidence.

### Use cases

- 🤖 AI Agent development: prevent agents from bypassing review
- 🏢 Enterprise compliance: meet SOC2 / ISO 27001 code change audit requirements
- 👥 Team collaboration: every PR must have audit records before merging

### Install

```bash
pip install pandax
```

### Quick start

```bash
cd /path/to/your-project
pandax init --root .

pandax write \
    --file src/main.py \
    --reason "Fix user_id type annotation" \
    --problem "Original used int, could be None" \
    --approach "Change to Optional[int]" \
    --old 'def get_user(user_id: int):' \
    --new 'def get_user(user_id: Optional[int]):'
```

### 7 Defense Layers

| Layer | Component | Purpose |
|---|---|---|
| L1 | file chmod | File-level read-only lock |
| L2 | watchdog | Real-time file monitoring + git checkout rollback |
| L3 | pre-commit hook | Strict per-file APPROVED validation |
| L4 | startup README | CLI loads project metadata on startup |
| L5 | self-fingerprint | CLI's own SHA256 detects tampering |
| L6 | binary SHA256 snapshot | Detect .png/.pdf binary tampering |
| L7 | GitHub Actions CI | Pre-merge audit verification (final backstop) |

### MCP Server

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

Exposes 11 tools for AI agents (Claude / Cursor / Trae).

### License

MIT — see [LICENSE](LICENSE)

### Links

- [PyPI Package](https://pypi.org/project/pandax/)
- [GitHub Repository](https://github.com/pandax/pandax)
- [Issue Tracker](https://github.com/pandax/pandax/issues)
- [Documentation](https://github.com/pandax/pandax/blob/main/README.md)
- [Changelog](https://github.com/pandax/pandax/blob/main/CHANGELOG.md)
- [实战验证报告 (Validation Report)](实战验证报告.md)