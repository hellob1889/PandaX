# Changelog

All notable changes to PandaX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-09-04

### Added (Phase 9: OS 右键菜单集成)
- **Windows 右键菜单**：HKCU 注册表级联菜单（无需管理员权限），覆盖任意文件 / 目录 / 空白处
- **macOS Finder 服务**：Automator Quick Action（workflow + AppleScript 弹窗）
- **Linux 文件管理器**：Nautilus 脚本（GNOME / Cinnamon / MATE）+ Dolphin 服务菜单（KDE）
- **`pandax install-context`**：CLI 自动检测 OS 并安装右键菜单
- **`pandax uninstall-context`**：一键卸载右键菜单
- **`--silent` 旗标**：跳过 banner + README 摘要（右键场景 0 噪音）
- **`--trust-default` 旗标**：使用默认密码 `0000` 自动处理指纹（右键场景无需手动初始化）

### Added (Phase 10: 国际化 i18n)
- **`src/pandax/i18n.py`**：i18n 引擎（149 keys × 2 语言，100% 覆盖）
- **`--lang=zh-CN|en` 旗标**：CLI 语言切换（覆盖自动检测）
- **自动检测 OS 语言**：Windows `GetUserDefaultLocaleName` + Unix `LANG` + `locale` 模块
- **持久化偏好**：`~/.pandax/config.json` 保存用户语言选择
- **右键菜单双语**：静态菜单项同时显示中文 + 英文（"锁定文件 (Lock)"）
- **PowerShell 脚本双语**：`install_context_menu.ps1` 自动读取 `~/.pandax/config.json` 切换语言
- **macOS workflow 双语**：AppleScript 弹窗和提示文本双语
- **Linux 脚本双语**：zenity / kdialog / read fallback 全双语

### Changed
- **`pandax` 启动**：自动检测语言 + 显示对应语言的 banner tagline
- **`pandax status`**：状态仪表盘全部走 `t()`（锁定数 / 指纹 / 审计统计 / 二进制快照）
- **`pandax log`**：审计历史表头 + 字段标签（文件 / 操作 / 时间 / session / 原因）走 `t()`
- **`pandax write`**：14 个 REJECTED 错误信息走 `t()`（含 JSON 格式）
- **`pandax ci`**：基线 / 变更文件数 / 受保护扩展统计 / PASS / FAIL 输出走 `t()`
- **`pandax install-git`**：探测 / 下载 / 解压 / 错误提示全双语
- **`pandax install-hook`**：watchdog 检测 / pre-commit hook 安装全双语
- **`pandax watch`**：daemon 启动信息（PID / 日志 / 停止命令）走 `t()`
- **Inno Setup 脚本**：右键菜单注册表项双语（`PandaX 审计工具 / Audit Tools`）
- **Linux Dolphin .desktop**：每条 Action 增加 `Name[en]` 翻译

### Documentation
- **`docs/i18n.md`**（NEW）：翻译提交流程（添加新语言 / 翻译 key / 覆盖率检查）
- **`docs/context-menu.md`**（已有，已更新）：右键菜单使用指南
- **`README.md`**：核心特性加「右键集成」+「i18n 国际化」两条
- **`mkdocs.yml`**：导航加「右键菜单 (Context Menu)」栏目

### Tests
- **140 个 pytest 测试全部通过**（覆盖所有现有功能，无回归）
- **新增 i18n 测试**（见 `tests/test_i18n.py`）：检测、自动检测、持久化、覆盖率、t() 占位符

## [0.6.2] - 2026-09-04

### Fixed
- **Hidden file protection bug**: `.env`, `.gitignore`, `.env.local` not locked (Python `Path.suffix` returns `""` for dotfiles)
  - Added `_effective_suffix()` helper in `cli.py` and `pandax_guard/__main__.py`
  - `lock`, `write`, and watchdog now correctly handle hidden files
- `--version` output shows outdated `v0.0.1` instead of real version
- `taskkill` hint on non-Windows platforms

### Changed
- Bumped version to 0.6.2 (was incorrectly showing 0.0.1 / 0.1.0)
- Locked wheel/sdist metadata (Operating System :: OS Independent confirmed)

### Tests
- 140 passed (was 134 before adding 6 hidden-file tests)

## [0.6.1] - 2026-09-04

### Fixed
- **CRITICAL: pre-commit hook bypass bug**: `git add -A` would automatically stage audit log, causing hook to falsely approve any commit. Real-world validation discovered this.
  - New `pre-commit-check.py` (Python): strictly validates every staged file has matching APPROVED record
  - Old shell-only hook replaced with shell → Python delegation

### Added
- `tests/test_pre_commit_hook.py`: 5 tests covering bypass scenarios
- `实战验证报告.md`: full e2e validation report

### Tests
- 134 passed

## [0.6.0] - 2026-09-04

### Added - Phase 7: GitHub Actions CI (L7 defense)
- `pandax ci --root . --base main` subcommand: validates PR against audit log
- `.github/workflows/audit.yml`: auto-run on pull_request + push
- Auto-comment on failed PR via `actions/github-script`
- `pandax_ci` MCP tool (11 total MCP tools)

### Tests
- 129 passed (added 14 CI tests)

## [0.5.0] - 2026-09-04

### Added - Phase 6: MCP Server for AI Agents
- `pandax_mcp` package: stdio JSON-RPC 2.0 server
- 10 tools exposed: `pandax_init`, `pandax_lock`, `pandax_write`, etc.
- Registered as `pandax-mcp` console script

### Tests
- 115 passed

## [0.4.0] - 2026-09-04

### Added - Phase 5: Binary File SHA256 Protection (L6 defense)
- `binary_protected_extensions`: 24 formats (PNG/JPG/ZIP/ICO/PDF/DOCX/XLSX/EXE/etc.)
- `binary_snapshots.json`: SHA256 dictionary, auto-created on init
- `--from-file` and `--content-base64` options for `write`
- Watchdog now detects binary tampering

### Tests
- 105 passed

## [0.3.0] - 2026-09-04

### Added - Phase 4.6: 17 Text Formats Protected (L1 defense upgrade)
- `protected_extensions` defaults expanded from `["py"]` to 17 formats:
  code (.py/.pyx) / config (.json/.yaml/.yml/.toml/.cfg/.ini/.env) /
  docs (.md/.rst/.txt) / frontend (.html/.css/.js/.ts) / scripts (.sh/.bat/.ps1)
- Watchdog filters by `protected_extensions` (not hardcoded `.py`)
- New tests cover all 17 extensions

### Tests
- 96 passed

## [0.2.0] - 2026-09-04

### Added - Phase 4: Multi-Format Audit Log Export
- `pandax log --format <fmt> --output <file>` exports audit history
- Supported: text / csv / tsv / json / yaml / md / html / xlsx / docx / pdf
- `--format` and `--output` as new standard interface

### Tests
- 69 passed

## [0.1.0] - 2026-09-03

### Added - Phase 1-3: MVP
- 5-layer defense: L1 file lock / L2 watchdog / L3 pre-commit hook / L4 README startup / L5 fingerprint
- `pandax` CLI with `init`/`lock`/`unlock`/`write`/`log`/`status`/`install-hook`/`watch`
- Pure Python, cross-platform (Windows/Linux/macOS via `pip install`)
- Self-fingerprinting via SHA256 to detect CLI tampering
- Append-only `.pandax/pandax.jsonl` audit log

### Tests
- 59 passed

[Unreleased]: https://github.com/pandax/pandax/compare/v0.6.2...HEAD
[0.6.2]: https://github.com/pandax/pandax/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/pandax/pandax/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/pandax/pandax/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/pandax/pandax/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/pandax/pandax/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pandax/pandax/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pandax/pandax/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pandax/pandax/releases/tag/v0.1.0