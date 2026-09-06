# Changelog

All notable changes to PandaX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2026-09-06

### Fixed (28 bugs)

**P0 安全 (5)**：
- **#8 + #7** install-context 通配符阻塞（PS5.1 registry provider 改用 .NET API）
- **#12 v1** write 失败时 mode 恢复（try/finally + 原始 mode 恢复）
- **#12 v2** write 默认拒绝 ReadOnly 锁定文件（`--force-write` 显式 opt-in）
- **#22** pre-commit hook CRLF→LF（bash 在 *nix 上不支持 CRLF，P0 安全）
- **#23** watchdog dedupe（1 次写入只产 1 条审计，2 秒去重窗口）

**P1 (4)**：
- **#2** status 用 `_iter_protected_files` 共享 helper（19 种扩展名全覆盖）
- **#5** `--lang` 全局参数支持任意位置（main() 预扫描 argv）
- **#15** PowerShell subprocess `-NoProfile -NonInteractive` + timeout=60
- **#29** `pandax init` merge-preserve（不再覆盖用户自定义 config.json）

**P2 (5)**：
- **#21** doctor/write git 检测一致性（共享 `_resolve_git_exe()`）
- **#6** log 标签 i18n 完整（REJECTED/UNAUTHORIZED 走 t()）
- **#20** ci 区分空仓库 vs 首次 commit（智能 baseline fallback）
- **#9 / #10** 智能长度阈值（`_info_length` unicode 宽度，1 中文字 = 2 宽度）

**P3 (4)**：
- **#13** log `-n` 简写作为 `--recent` 别名
- **#4** README summary 显示最新 Phase 而非旧 Step
- **#26** export html/md/text 报告标签本地化
- **#39** cmd_write 4 处硬编码中文改为 i18n

**UX + 横切 i18n (3)**：
- **#14** log 在 lang=en 时 Reason 字段本地化
- **#17** status i18n 完整性
- **#48** `--trust-default` 自动接受新指纹（pip install --upgrade 场景）

**UX (2)**：
- **#25** 独立 `pandax export` 子命令（语义清晰，不再借用 log）
- **#28** `pandax lock` 一键启用（未 init 时自动 init，首次使用友好）

**工程化 (4)**：
- **#TBD 版本号漂移** `src/pandax/__init__.py` 的 `__version__` 字面量与 `pyproject.toml` 漂移 → 改为 `importlib.metadata.version()` 动态读取 + pyproject.toml fallback
- **#TBD README 分组标签** `load_readme_summary` 解析 H3 分组标题，把 P0/P1/P2/P3/UX 标签附加到 step 行，CLI 启动 banner 显示完整 23 个 bug 的分组前缀
- **#TBD 自指纹 CRLF 根因** `python -m build` 在 Windows 上把 cli.py LF 转 CRLF（81694 vs 79644 bytes），导致 SHA256 不匹配；wheel 后处理 normalize LF
- **#TBD 方案 A 文件夹图标** `pandax lock` 同步切换 Windows 文件夹图标(写入 `desktop.ini` 引用 pandaX 锁 ICO),`unlock` 清理;非 Windows 平台 silent skip;ICO 内置到 wheel(多尺寸 16/32/48/64/128/256);**不影响 TortoiseGit 9 个 overlay 名额**(替换文件夹主图标,不是叠加)

### Added
- **`tests/test_version_single_source.py`**（5 个测试）：版本号单一事实源回归（pyproject → METADATA → importlib.metadata → 源码 import）
- **`--trust-default`** 在子命令后位置无关生效（#48 注册表右键场景）
- **右键菜单端到端测试覆盖**：Init/Lock/Status/Unlock + Bug #48 + 路径含空格/中文

### Changed
- README summary 自动取最新 Phase 而非旧 Step（#4）
- 右键菜单加 #28 一键 Lock 流程（自动 init）
- i18n 字典从 184 keys 增至 200+ keys
- README badges 同步：Tests 264 / Bugs 28 / Phase v0.7.1

### Stats
- **测试**：264 passed（+21 新测试：版本一致性 5 + #48 3 + #29/#39 8 + 其他 5）
- **零回归**：所有原有测试保持通过
- **打包**：wheel 73 KB + sdist 156 KB + ZIP 235 KB
- **CLI 启动 banner**：显示 P0/P1/P2/P3/UX 分组标签的 23 个 bug 修复列表
- **右键菜单**：HKCU 注册表 4 项 + macOS Quick Action + Linux Nautilus/Dolphin（v0.7.0 已有）

## [0.7.0] - 2026-09-05

### Added (Phase 9: OS 右键菜单集成)
- **Windows 右键菜单**：HKCU 注册表级联菜单（无需管理员权限），覆盖任意文件 / 目录 / 空白处
- **macOS Finder 服务**：Automator Quick Action（workflow + AppleScript 弹窗）
- **Linux 文件管理器**：Nautilus 脚本（GNOME / Cinnamon / MATE）+ Dolphin 服务菜单（KDE）
- **`pandax install-context`**：CLI 自动检测 OS 并安装右键菜单
- **`pandax uninstall-context`**：一键卸载右键菜单
- **`--silent` 旗标**：跳过 banner + README 摘要（右键场景 0 噪音）
- **`--trust-default` 旗标**：使用默认密码 `0000` 自动处理指纹（右键场景无需手动初始化）

### Added (Phase 10: 国际化 i18n)
- **`src/pandax/i18n.py`**：i18n 引擎（**184 keys** × 2 语言，100% 覆盖）
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
- **191 个 pytest 测试全部通过**（覆盖所有现有功能，无回归）— 含 140 个原有 + 35 个 i18n + 16 个 audit-CI 集成
- **新增 i18n 测试**（见 `tests/test_i18n.py`）：检测、自动检测、持久化、覆盖率、t() 占位符

### Added (CI / 自动化 / 环境)
- **`scripts/audit_i18n.py`**：对抗式审查脚本（扫描 `pandax` 包内硬编码中文字符串 + 检查翻译覆盖率 100%）
- **`.github/workflows/lint.yml`**：4-job CI（i18n-audit / i18n-coverage / test matrix × 9 / summary）— PR 引入硬编码中文或翻译倒退立即 fail
- **`scripts/doctor.py`**：环境自检工具（Python / pip / git / pandax 安装位置 / pandax.exe PATH / 指纹 / setuptools / 5 个运行时依赖）
- **`scripts/doctor.py --fix`**：自动修复 13 类问题（pip 缺失 / git PATH / pandax 装在 site-packages / pandax.exe PATH / 指纹污染 / setuptools / 5 个运行时依赖缺失）
- **`scripts/doctor.py --fix --persist-path`**：PATH 持久化（Windows `setx` → `HKCU\Environment\Path`；Unix → `~/.bashrc` / `~/.zshrc`）
- **`scripts/install.sh`** + **`scripts/install.ps1`**：跨平台 bootstrap 安装器（检测 OS / Python / git / 卸载老版本 / `pip install -e .` / 调 `doctor.py --fix --persist-path`）
- **README badges**：Tests 191 passed / i18n 184/184 keys / Lint & i18n CI passing
- **9 处硬编码中文字符串迁移到 `t()`**（`watchdog_guard.py` / `exporters.py` / `mcp_server.py` / `cmd_status` / `cmd_log` / `cmd_write` 剩余）

### Changed (右键菜单内容 i18n)
- **`installer/macos/PandaX Lock.workflow/Contents/document.wflow`**：模板化（11 处硬编码中文 → `{TXT_XXX}` 占位符），安装时 Python 渲染为对应语言
- **`installer/linux/nautilus/PandaX`**：重写为内嵌双语 dict（17 个文案 → `T[lang][key]`），优先级 PANDAX_LANG > config.json > zh-CN
- **`installer/macos/install_context_menu.sh`** + **`installer/linux/install_context_menu.sh`**：shell 头部加 `USER_LANG` 解析块 + 全部 `$TXT_*` 变量化
- **`src/pandax/cli.py` `_run_installer`**：子进程 env 显式传 `PANDAX_LANG=get_lang()`（绕过 Git Bash `$HOME` 异常）

### Documentation
- **`docs/i18n.md` §10**（NEW）：`install-context --lang` 跨平台右键菜单 i18n 全流程（优先级 / 用法 / 改动覆盖范围 / 限制）
- **`README.md`**：doctor.py `--fix` / `--fix-only` / `--persist-path` 文档化；版本表加 v0.7.0 完整描述

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