# Changelog

All notable changes to PandaX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2] - 2026-09-10

### Fixed (CI 工程化 / CI Engineering)
- **CI Tests job 在干净 ubuntu-latest 上 25 秒 exit 1** —— 根因：test job 没 pin setuptools 版本，build-isolation 拉到的 setuptools 与 build job 不一致，导致 `pip install -e .[dev]` 阶段 metadata 解析失败
  **CI Tests job exits 1 within 25s on clean ubuntu-latest** —— Root cause: test job didn't pin setuptools version; setuptools pulled by build-isolation was inconsistent with the build job, causing metadata parsing failure during `pip install -e .[dev]`
  - test job pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`，与 build 步骤完全对齐
    test job pins `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`, fully aligned with build step
  - v0.7.1 publish run（run 34429112009）Build ✅ / Tests ❌ / Publish ✅ — 已修复
    v0.7.1 publish run (run 34429112009) Build ✅ / Tests ❌ / Publish ✅ — fixed
  - 新验证 run（run 34430629959）Build ✅ / Tests ✅ / Publish ✅
    new verification run (run 34430629959) Build ✅ / Tests ✅ / Publish ✅

### Added (CI 诊断加固 / CI Diagnostics Hardening)
- **pytest log artifact**：测试失败时 `tee /tmp/pytest.log` + `actions/upload-artifact@v4` 上传完整日志，artifact 名 `pytest-log-{run_id}`
  **pytest log artifact**: on test failure, `tee /tmp/pytest.log` + `actions/upload-artifact@v4` uploads full log; artifact name `pytest-log-{run_id}`
- **continue-on-error + 显式 fail step**：解耦"上传日志"与"标红"，下次 CI 失败可以直接从 artifact 看到 pytest 输出，无需再重新跑
  **continue-on-error + explicit fail step**: decouples "upload logs" from "mark red"; next CI failure can be diagnosed from artifact directly without re-running

### Distribution
- **分发名 `pandax-guard`**（沿用 v0.7.1）：保留 `pandax` 作为内部 Python 包和 CLI 命令
  **Distribution name `pandax-guard`** (inherited from v0.7.1): keeps `pandax` as internal Python package and CLI command
- **wheel/sdist 文件名归一化**：`pandax_guard-0.7.2-py3-none-any.whl` + `pandax_guard-0.7.2.tar.gz`（setuptools 自动把分发名 hyphen 转为下划线）
  **wheel/sdist filename normalization**: `pandax_guard-0.7.2-py3-none-any.whl` + `pandax_guard-0.7.2.tar.gz` (setuptools auto-converts distribution name hyphen to underscore)

### Stats
- **测试**：340 passed（与 v0.7.1 持平，无回归）
  **Tests**: 340 passed (parity with v0.7.1, no regression)
- **PyPI**：[pandax-guard 0.7.2](https://pypi.org/project/pandax-guard/0.7.2/)
- **Trusted Publishing**：tag `v0.7.2` push → GitHub Actions `publish.yml` 自动通过 OIDC 上传到 PyPI
  **Trusted Publishing**: tag `v0.7.2` push → GitHub Actions `publish.yml` auto-uploads to PyPI via OIDC

## [0.7.1] - 2026-09-06

### Fixed (28 bugs)

**P0 安全 (5) / P0 Security (5)**：
- **#8 + #7** install-context 通配符阻塞（PS5.1 registry provider 改用 .NET API）
  **#8 + #7** install-context globbing blocker (PS5.1 registry provider switched to .NET API)
- **#12 v1** write 失败时 mode 恢复（try/finally + 原始 mode 恢复）
  **#12 v1** write mode restoration on failure (try/finally + restore original mode)
- **#12 v2** write 默认拒绝 ReadOnly 锁定文件（`--force-write` 显式 opt-in）
  **#12 v2** write default rejects ReadOnly-locked file (`--force-write` explicit opt-in)
- **#22** pre-commit hook CRLF→LF（bash 在 *nix 上不支持 CRLF，P0 安全）
  **#22** pre-commit hook CRLF→LF (bash on *nix doesn't support CRLF, P0 security)
- **#23** watchdog dedupe（1 次写入只产 1 条审计，2 秒去重窗口）
  **#23** watchdog dedupe (1 write produces 1 audit entry, 2-second dedupe window)

**P1 (4)**：
- **#2** status 用 `_iter_protected_files` 共享 helper（19 种扩展名全覆盖）
  **#2** status uses shared helper `_iter_protected_files` (full coverage of 19 extensions)
- **#5** `--lang` 全局参数支持任意位置（main() 预扫描 argv）
  **#5** `--lang` global flag accepts any position (main() pre-scans argv)
- **#15** PowerShell subprocess `-NoProfile -NonInteractive` + timeout=60
- **#29** `pandax init` merge-preserve（不再覆盖用户自定义 config.json）
  **#29** `pandax init` merge-preserve (no longer overwrites user's custom config.json)

**P2 (5)**：
- **#21** doctor/write git 检测一致性（共享 `_resolve_git_exe()`）
  **#21** doctor/write git detection consistency (shared `_resolve_git_exe()`)
- **#6** log 标签 i18n 完整（REJECTED/UNAUTHORIZED 走 t()）
  **#6** log tag i18n complete (REJECTED/UNAUTHORIZED go through t())
- **#20** ci 区分空仓库 vs 首次 commit（智能 baseline fallback）
  **#20** ci distinguishes empty repo vs first commit (intelligent baseline fallback)
- **#9 / #10** 智能长度阈值（`_info_length` unicode 宽度，1 中文字 = 2 宽度）
  **#9 / #10** smart length threshold (`_info_length` unicode width, 1 CJK char = 2 width)

**P3 (4)**：
- **#13** log `-n` 简写作为 `--recent` 别名
  **#13** log `-n` short form as `--recent` alias
- **#4** README summary 显示最新 Phase 而非旧 Step
  **#4** README summary shows latest Phase instead of old Step
- **#26** export html/md/text 报告标签本地化
  **#26** export html/md/text report label localization
- **#39** cmd_write 4 处硬编码中文改为 i18n
  **#39** cmd_write 4 hardcoded Chinese strings migrated to i18n

**UX + 横切 i18n (3) / UX + Cross-cutting i18n (3)**：
- **#14** log 在 lang=en 时 Reason 字段本地化
  **#14** log Reason field localized when lang=en
- **#17** status i18n 完整性
  **#17** status i18n completeness
- **#48** `--trust-default` 自动接受新指纹（pip install --upgrade 场景）
  **#48** `--trust-default` auto-accepts new fingerprint (pip install --upgrade scenario)

**UX (2)**：
- **#25** 独立 `pandax export` 子命令（语义清晰，不再借用 log）
  **#25** independent `pandax export` subcommand (cleaner semantics, no longer borrowing log)
- **#28** `pandax lock` 一键启用（未 init 时自动 init，首次使用友好）
  **#28** `pandax lock` one-click enable (auto-init if not initialized, friendly first-use)

**工程化 (4) / Engineering (4)**：
- **#TBD 版本号漂移** `src/pandax/__init__.py` 的 `__version__` 字面量与 `pyproject.toml` 漂移 → 改为 `importlib.metadata.version()` 动态读取 + pyproject.toml fallback
  **#TBD Version Drift** `src/pandax/__init__.py`'s `__version__` literal drifted from `pyproject.toml` → switched to `importlib.metadata.version()` dynamic read + pyproject.toml fallback
- **#TBD README 分组标签** `load_readme_summary` 解析 H3 分组标题，把 P0/P1/P2/P3/UX 标签附加到 step 行，CLI 启动 banner 显示完整 23 个 bug 的分组前缀
  **#TBD README Grouping Tags** `load_readme_summary` parses H3 group titles, appends P0/P1/P2/P3/UX tags to step lines; CLI startup banner displays full group prefixes for 23 bugs
- **#TBD 自指纹 CRLF 根因** `python -m build` 在 Windows 上把 cli.py LF 转 CRLF（81694 vs 79644 bytes），导致 SHA256 不匹配；wheel 后处理 normalize LF
  **#TBD Self-fingerprint CRLF Root Cause** `python -m build` on Windows converts cli.py LF to CRLF (81694 vs 79644 bytes), causing SHA256 mismatch; post-build wheel normalization to LF
- **#TBD 方案 A 文件夹图标** `pandax lock` 同步切换 Windows 文件夹图标(写入 `desktop.ini` 引用 pandaX 锁 ICO),`unlock` 清理;非 Windows 平台 silent skip;ICO 内置到 wheel(多尺寸 16/32/48/64/128/256);**不影响 TortoiseGit 9 个 overlay 名额**(替换文件夹主图标,不是叠加)
  **#TBD Plan A Folder Icon** `pandax lock` switches Windows folder icon (writes `desktop.ini` referencing PandaX lock ICO); `unlock` cleans up; non-Windows platforms silent skip; ICO embedded in wheel (multi-size 16/32/48/64/128/256); **doesn't consume TortoiseGit's 9 overlay slots** (replaces folder primary icon, not overlay)
- **#TBD Git 兼容性** `pandax init` 在 git 仓库中自动维护 `.gitignore`(追加 `.pandax/` + `desktop.ini` 条目,不覆盖用户现有规则);`pandax status` 显示 `[Git 集成]` 检查段;13 个新测试覆盖(幂等 / 保留现有规则 / 跳过非 git / 部分缺失 / 真实 git 验证)
  **#TBD Git Compatibility** `pandax init` auto-maintains `.gitignore` in git repos (appends `.pandax/` + `desktop.ini` entries, doesn't overwrite user rules); `pandax status` shows `[Git Integration]` check section; 13 new tests cover (idempotent / preserve existing rules / skip non-git / partial-missing / real-git validation)
- **#TBD Web 实时仪表盘** 新增 `pandax serve` 子命令(`localhost:8765` HTTP + SSE);`watchdog` OS 级文件监视 + SSE 推送端到端 <100ms;多客户端订阅互不干扰;**自动历史回放** + **实时增量** + Toast 通知 + 状态统计 + 客户端搜索过滤;现代明亮 Notion/Linear 风格 UI(单文件 `index.html`,无构建);20 个测试覆盖(单元 + SSE 端到端 + cmd_serve + HTML 合规)
  **#TBD Web Realtime Dashboard** new `pandax serve` subcommand (`localhost:8765` HTTP + SSE); `watchdog` OS-level file monitor + SSE push end-to-end <100ms; multi-client subscribe without interference; **auto history replay** + **real-time incremental** + Toast notifications + status stats + client-side search filter; modern bright Notion/Linear-style UI (single-file `index.html`, no build); 20 tests cover (unit + SSE e2e + cmd_serve + HTML compliance)

### Added
- **`tests/test_version_single_source.py`**（5 个测试）：版本号单一事实源回归（pyproject → METADATA → importlib.metadata → 源码 import）
  **`tests/test_version_single_source.py`** (5 tests): version single-source-of-truth regression (pyproject → METADATA → importlib.metadata → source import)
- **`--trust-default`** 在子命令后位置无关生效（#48 注册表右键场景）
  **`--trust-default`** position-independent after subcommand (registry context-menu scenario #48)
- **右键菜单端到端测试覆盖**：Init/Lock/Status/Unlock + Bug #48 + 路径含空格/中文
  **Context menu end-to-end test coverage**: Init/Lock/Status/Unlock + Bug #48 + paths with spaces/Chinese

### Changed
- README summary 自动取最新 Phase 而非旧 Step（#4）
  README summary auto-takes latest Phase instead of old Step (#4)
- 右键菜单加 #28 一键 Lock 流程（自动 init）
  Context menu adds #28 one-click Lock flow (auto-init)
- i18n 字典从 184 keys 增至 200+ keys
  i18n dictionary from 184 keys grew to 200+ keys
- README badges 同步：Tests 264 / Bugs 28 / Phase v0.7.1
  README badges synced: Tests 264 / Bugs 28 / Phase v0.7.1

### Stats
- **测试**：264 passed（+21 新测试：版本一致性 5 + #48 3 + #29/#39 8 + 其他 5）
  **Tests**: 264 passed (+21 new tests: version consistency 5 + #48 3 + #29/#39 8 + others 5)
- **零回归**：所有原有测试保持通过
  **Zero regression**: all existing tests stay passing
- **打包**：wheel 73 KB + sdist 156 KB + ZIP 235 KB
  **Packaging**: wheel 73 KB + sdist 156 KB + ZIP 235 KB
- **CLI 启动 banner**：显示 P0/P1/P2/P3/UX 分组标签的 23 个 bug 修复列表
  **CLI startup banner**: displays 23 bug fix list with P0/P1/P2/P3/UX group prefixes
- **右键菜单**：HKCU 注册表 4 项 + macOS Quick Action + Linux Nautilus/Dolphin（v0.7.0 已有）
  **Context menu**: HKCU registry 4 entries + macOS Quick Action + Linux Nautilus/Dolphin (already in v0.7.0)

## [0.7.0] - 2026-09-05

### Added (Phase 9: OS 右键菜单集成 / OS Context Menu Integration)
- **Windows 右键菜单**：HKCU 注册表级联菜单（无需管理员权限），覆盖任意文件 / 目录 / 空白处
  **Windows Context Menu**: HKCU registry cascade menu (no admin rights required), covers any file / directory / blank space
- **macOS Finder 服务**：Automator Quick Action（workflow + AppleScript 弹窗）
  **macOS Finder Service**: Automator Quick Action (workflow + AppleScript popup)
- **Linux 文件管理器**：Nautilus 脚本（GNOME / Cinnamon / MATE）+ Dolphin 服务菜单（KDE）
  **Linux File Manager**: Nautilus scripts (GNOME / Cinnamon / MATE) + Dolphin service menu (KDE)
- **`pandax install-context`**：CLI 自动检测 OS 并安装右键菜单
  **`pandax install-context`**: CLI auto-detects OS and installs context menu
- **`pandax uninstall-context`**：一键卸载右键菜单
  **`pandax uninstall-context`**: one-click context menu uninstall
- **`--silent` 旗标**：跳过 banner + README 摘要（右键场景 0 噪音）
  **`--silent` flag**: skips banner + README summary (zero-noise context menu scenario)
- **`--trust-default` 旗标**：使用默认密码 `0000` 自动处理指纹（右键场景无需手动初始化）
  **`--trust-default` flag**: uses default password `0000` to auto-handle fingerprints (no manual init needed for context menu)

### Added (Phase 10: 国际化 i18n / Internationalization)
- **`src/pandax/i18n.py`**：i18n 引擎（**184 keys** × 2 语言，100% 覆盖）
  **`src/pandax/i18n.py`**: i18n engine (**184 keys** × 2 languages, 100% coverage)
- **`--lang=zh-CN|en` 旗标**：CLI 语言切换（覆盖自动检测）
  **`--lang=zh-CN|en` flag**: CLI language switch (overrides auto-detection)
- **自动检测 OS 语言**：Windows `GetUserDefaultLocaleName` + Unix `LANG` + `locale` 模块
  **Auto-detect OS language**: Windows `GetUserDefaultLocaleName` + Unix `LANG` + `locale` module
- **持久化偏好**：`~/.pandax/config.json` 保存用户语言选择
  **Persistent preference**: `~/.pandax/config.json` saves user's language choice
- **右键菜单双语**：静态菜单项同时显示中文 + 英文（"锁定文件 (Lock)"）
  **Context menu bilingual**: static menu items show Chinese + English simultaneously ("锁定文件 (Lock)")
- **PowerShell 脚本双语**：`install_context_menu.ps1` 自动读取 `~/.pandax/config.json` 切换语言
  **PowerShell script bilingual**: `install_context_menu.ps1` auto-reads `~/.pandax/config.json` for language switching
- **macOS workflow 双语**：AppleScript 弹窗和提示文本双语
  **macOS workflow bilingual**: AppleScript popups and prompts bilingual
- **Linux 脚本双语**：zenity / kdialog / read fallback 全双语
  **Linux script bilingual**: zenity / kdialog / read fallback all bilingual

### Changed
- **`pandax` 启动**：自动检测语言 + 显示对应语言的 banner tagline
  **`pandax` startup**: auto-detects language + displays banner tagline in that language
- **`pandax status`**：状态仪表盘全部走 `t()`（锁定数 / 指纹 / 审计统计 / 二进制快照）
  **`pandax status`**: status dashboard fully goes through `t()` (lock count / fingerprint / audit stats / binary snapshot)
- **`pandax log`**：审计历史表头 + 字段标签（文件 / 操作 / 时间 / session / 原因）走 `t()`
  **`pandax log`**: audit history header + field labels (file / action / time / session / reason) through `t()`
- **`pandax write`**：14 个 REJECTED 错误信息走 `t()`（含 JSON 格式）
  **`pandax write`**: 14 REJECTED error messages through `t()` (including JSON format)
- **`pandax ci`**：基线 / 变更文件数 / 受保护扩展统计 / PASS / FAIL 输出走 `t()`
  **`pandax ci`**: baseline / changed file count / protected extension stats / PASS / FAIL output through `t()`
- **`pandax install-git`**：探测 / 下载 / 解压 / 错误提示全双语
  **`pandax install-git`**: probe / download / extract / error messages all bilingual
- **`pandax install-hook`**：watchdog 检测 / pre-commit hook 安装全双语
  **`pandax install-hook`**: watchdog detection / pre-commit hook install all bilingual
- **`pandax watch`**：daemon 启动信息（PID / 日志 / 停止命令）走 `t()`
  **`pandax watch`**: daemon startup info (PID / log / stop command) through `t()`
- **Inno Setup 脚本**：右键菜单注册表项双语（`PandaX 审计工具 / Audit Tools`）
  **Inno Setup script**: context menu registry entries bilingual (`PandaX 审计工具 / Audit Tools`)
- **Linux Dolphin .desktop**：每条 Action 增加 `Name[en]` 翻译
  **Linux Dolphin .desktop**: each Action adds `Name[en]` translation

### Documentation
- **`docs/i18n.md`**（NEW）：翻译提交流程（添加新语言 / 翻译 key / 覆盖率检查）
  **`docs/i18n.md`** (NEW): translation contribution workflow (add new language / translate key / coverage check)
- **`docs/context-menu.md`**（已有，已更新）：右键菜单使用指南
  **`docs/context-menu.md`** (existing, updated): context menu usage guide
- **`README.md`**：核心特性加「右键集成」+「i18n 国际化」两条
  **`README.md`**: core features add "Context Menu Integration" + "i18n Internationalization" two entries
- **`mkdocs.yml`**：导航加「右键菜单 (Context Menu)」栏目
  **`mkdocs.yml`**: navigation adds "Context Menu" section

### Tests
- **191 个 pytest 测试全部通过**（覆盖所有现有功能，无回归）— 含 140 个原有 + 35 个 i18n + 16 个 audit-CI 集成
  **191 pytest tests all pass** (covers all existing functionality, no regression) — including 140 original + 35 i18n + 16 audit-CI integration
- **新增 i18n 测试**（见 `tests/test_i18n.py`）：检测、自动检测、持久化、覆盖率、t() 占位符
  **New i18n tests** (see `tests/test_i18n.py`): detection, auto-detection, persistence, coverage, t() placeholders

### Added (CI / 自动化 / 环境 / Automation / Environment)
- **`scripts/audit_i18n.py`**：对抗式审查脚本（扫描 `pandax` 包内硬编码中文字符串 + 检查翻译覆盖率 100%）
  **`scripts/audit_i18n.py`**: adversarial review script (scans `pandax` package for hardcoded Chinese + checks 100% translation coverage)
- **`.github/workflows/lint.yml`**：4-job CI（i18n-audit / i18n-coverage / test matrix × 9 / summary）— PR 引入硬编码中文或翻译倒退立即 fail
  **`.github/workflows/lint.yml`**: 4-job CI (i18n-audit / i18n-coverage / test matrix × 9 / summary) — PR introducing hardcoded Chinese or translation regression immediately fails
- **`scripts/doctor.py`**：环境自检工具（Python / pip / git / pandax 安装位置 / pandax.exe PATH / 指纹 / setuptools / 5 个运行时依赖）
  **`scripts/doctor.py`**: environment self-check tool (Python / pip / git / pandax install location / pandax.exe PATH / fingerprint / setuptools / 5 runtime dependencies)
- **`scripts/doctor.py --fix`**：自动修复 13 类问题（pip 缺失 / git PATH / pandax 装在 site-packages / pandax.exe PATH / 指纹污染 / setuptools / 5 个运行时依赖缺失）
  **`scripts/doctor.py --fix`**: auto-fixes 13 categories of issues (pip missing / git PATH / pandax in site-packages / pandax.exe PATH / fingerprint pollution / setuptools / 5 runtime dependency missing)
- **`scripts/doctor.py --fix --persist-path`**：PATH 持久化（Windows `setx` → `HKCU\Environment\Path`；Unix → `~/.bashrc` / `~/.zshrc`）
  **`scripts/doctor.py --fix --persist-path`**: PATH persistence (Windows `setx` → `HKCU\Environment\Path`; Unix → `~/.bashrc` / `~/.zshrc`)
- **`scripts/install.sh`** + **`scripts/install.ps1`**：跨平台 bootstrap 安装器（检测 OS / Python / git / 卸载老版本 / `pip install -e .` / 调 `doctor.py --fix --persist-path`）
  **`scripts/install.sh`** + **`scripts/install.ps1`**: cross-platform bootstrap installer (detect OS / Python / git / uninstall old version / `pip install -e .` / call `doctor.py --fix --persist-path`)
- **README badges**：Tests 191 passed / i18n 184/184 keys / Lint & i18n CI passing
- **9 处硬编码中文字符串迁移到 `t()`**（`watchdog_guard.py` / `exporters.py` / `mcp_server.py` / `cmd_status` / `cmd_log` / `cmd_write` 剩余）
  **9 hardcoded Chinese strings migrated to `t()`** (`watchdog_guard.py` / `exporters.py` / `mcp_server.py` / `cmd_status` / `cmd_log` / `cmd_write` remaining)

### Changed (右键菜单内容 i18n / Context Menu i18n)
- **`installer/macos/PandaX Lock.workflow/Contents/document.wflow`**：模板化（11 处硬编码中文 → `{TXT_XXX}` 占位符），安装时 Python 渲染为对应语言
  **`installer/macos/PandaX Lock.workflow/Contents/document.wflow`**: templated (11 hardcoded Chinese → `{TXT_XXX}` placeholders), Python renders to corresponding language at install time
- **`installer/linux/nautilus/PandaX`**：重写为内嵌双语 dict（17 个文案 → `T[lang][key]`），优先级 PANDAX_LANG > config.json > zh-CN
  **`installer/linux/nautilus/PandaX`**: rewritten as embedded bilingual dict (17 strings → `T[lang][key]`), priority PANDAX_LANG > config.json > zh-CN
- **`installer/macos/install_context_menu.sh`** + **`installer/linux/install_context_menu.sh`**：shell 头部加 `USER_LANG` 解析块 + 全部 `$TXT_*` 变量化
  **`installer/macos/install_context_menu.sh`** + **`installer/linux/install_context_menu.sh`**: shell header adds `USER_LANG` parsing block + all `$TXT_*` variabled
- **`src/pandax/cli.py` `_run_installer`**：子进程 env 显式传 `PANDAX_LANG=get_lang()`（绕过 Git Bash `$HOME` 异常）
  **`src/pandax/cli.py` `_run_installer`**: subprocess env explicitly passes `PANDAX_LANG=get_lang()` (works around Git Bash `$HOME` anomaly)

### Documentation
- **`docs/i18n.md` §10**（NEW）：`install-context --lang` 跨平台右键菜单 i18n 全流程（优先级 / 用法 / 改动覆盖范围 / 限制）
  **`docs/i18n.md` §10** (NEW): `install-context --lang` cross-platform context menu i18n full workflow (priority / usage / change coverage / limitations)
- **`README.md`**：doctor.py `--fix` / `--fix-only` / `--persist-path` 文档化；版本表加 v0.7.0 完整描述
  **`README.md`**: doctor.py `--fix` / `--fix-only` / `--persist-path` documented; version table adds v0.7.0 full description

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

[Unreleased]: https://github.com/hellob1889/PandaX/compare/v0.7.2...HEAD
[0.7.2]: https://github.com/hellob1889/PandaX/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/hellob1889/PandaX/compare/v0.6.2...v0.7.1
[0.6.2]: https://github.com/hellob1889/PandaX/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/hellob1889/PandaX/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/hellob1889/PandaX/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/hellob1889/PandaX/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/hellob1889/PandaX/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/hellob1889/PandaX/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/hellob1889/PandaX/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hellob1889/PandaX/releases/tag/v0.1.0