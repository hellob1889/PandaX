# Changelog

All notable changes to Pandaone AI Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.6] - 2026-09-13

### Changed (品牌切回 / Rebrand Cutover)

- **PyPI 分发名从 `pandax-guard` 切回 `pandaone-guard`** (PR #23)：
  - `pyproject.toml` `name = "pandaone-guard"`,`version = "0.7.6"`
  - 13 个用户面文件:`pandax-guard` → `pandaone-guard` (还原 PR #12 临时回退)
  - 发布到 PyPI 后用户可执行 `pip install pandaone-guard`
- **PyPI `pandaone-guard` 项目自动创建**：M1+M2 阶段在 PyPI `/manage/account/publishing/` 配 pending trusted publisher（GitHub Actions from `hellob1889/Pandaone-AI-Agent`, workflow `publish.yml`）。第一次 OIDC upload 时 PyPI 自动建项目
- **PyPI `pandax-guard` 项目保留**(不动)——不破坏现有 `pip install pandax-guard` 用户,v0.7.4 仍是其最新版

### Distribution 命名约定(永久)

| 包名 | 含义 | 引用 |
|---|---|---|
| `pandax-guard` | PyPI 旧分发名(2026-09-13 之前的发布) | 仅向后兼容,v0.7.4 是其最后一个 release |
| `pandaone-guard` | PyPI 新分发名(品牌 Pandaone AI Agent) | 主分发,本 release 起 |
| `pandaone` | Python `import` 包名(PR #4 改名,自 v0.7.4 起) | `from pandaone.cli import main` |
| `pandax` | Python `import` 旧别名(向后兼容) | `import pandax` 仍可用 |
| `pandaone` | CLI 主命令(PR #4 改名) | `pandaone --version` |
| `pandax` | CLI 旧命令别名(向后兼容) | `pandax --version` 仍可用 |

### Migration Guide (从 pandax-guard 升级到 pandaone-guard)

```bash
# 1. 卸载旧包
pip uninstall pandax-guard

# 2. 安装新包
pip install pandaone-guard

# 3. 验证
pandaone --version  # 应输出: pandaone-guard v0.7.6
```

### Stats

- **测试**：342 passed, 1 skipped（无回归）
- **PyPI**：[pandaone-guard 0.7.6](https://pypi.org/project/pandaone-guard/0.7.6/)（首次发布到新包名）
- **GitHub Release**：[v0.7.6](https://github.com/hellob1889/Pandaone-AI-Agent/releases/tag/v0.7.6)
- **PRs in this release**：#23 + #22 (#22 是 v0.7.6 plan 文档,docs-only)
- **Trusted Publisher**：在 PyPI 配的 pending trusted publisher 自动激活(从 pending 转为 active)

### Notes

- 本 release 是**纯品牌切回**,不影响业务代码
- 内部 Python 包 `import` 路径(自 v0.7.4 已切到 `pandaone`)保持不变
- CLI 命令(自 v0.7.4 已切到 `pandaone`)保持不变
- 向后兼容别名(`import pandax` / `pandax` CLI)保持不变

## [0.7.5] - 2026-09-13

### Fixed (CI 审计机制加固 / CI Audit Mechanism Hardening)

- **PR #18** — audit.yml `[skip-audit]` 检测范围从 commit subject-only (`%s`) 扩展到 subject+body (`%s%n%n%b`)。修复 PR #17 (CHANGELOG.md v0.7.4 补段) 把 `[skip-audit]` 写在 footer 却被旧逻辑漏检、L7 审计误判失败的问题。footer 标记写法现在和 `Signed-off-by:` / `[skip ci]` / `[skip actions]` 等 Git 社区惯例对齐
- **PR #19** — audit.yml 新增"docs-only / meta-only" 自动跳过机制。push 仅触及下列文件时自动跳过 pandax ci 验证，贡献者**无需**手动写 `[skip-audit]`：
  - `CHANGELOG.md` / `README*.md`（含 `README.md` / `README-zh.md` 等）
  - `docs/**`
  - `.github/PULL_REQUEST_TEMPLATE/**` / `.github/PULL_REQUEST_TEMPLATE.md` / `.github/ISSUE_TEMPLATE/**`
  - `.github/CODEOWNERS` / `CODE_OF_CONDUCT.md` / `CONTRIBUTING.md` / `SECURITY.md`
  - `LICENSE` / `LICENSE-*` / `LICENSE.md` / `LICENSE.txt` / `NOTICE*`
- **PR #20** — docs-only regex bug 修复。PR #19 引入的 regex 用了 literal `docs/$` 形式（缺少 `.*` 后缀），导致 `docs/foo.md`、`docs/sub/nested/file.md`、`.github/PULL_REQUEST_TEMPLATE/foo.md` 等不匹配 → 仍触发 audit。PR #20 改成 `docs/.*` + `.github/PULL_REQUEST_TEMPLATE(\.md|/.*)`，本地用 bash `grep -E` 验证 23 个 docs 路径全部 SKIP ✅、4 个代码路径正确 AUDIT ✅

### Added (PR Template / 贡献者引导)

- `.github/PULL_REQUEST_TEMPLATE.md`（v0.7.4 之前已存在，本 release 进一步强化）— "Audit 状态" 区块明确列出 4 种情况：
  1. 已通过 `pandaone write` 记录所有改动
  2. 仅 workflow 文件改动 → `[skip-audit]`
  3. 仅文档 / 示例 / assets 改动 → `[skip-audit]`（**v0.7.5 起也可省略，docs-only 自动跳过**）
  4. 其他情况说明

### Repository Cleanup / 仓库清理

- **远端分支清理**：`docs/changelog-v074`（squash merge auto-delete 自动清）、`fix/audit-yml-skip-marker-body-scan`（PR #18 squash 后手动 API 删）、`chore/cleanup-stale-deployment`（部署清理用，任务完成后强删）
- **远端 tag 清理**：`v0.7.1-test`（实验分支 tag，无对应 release）
- **Deployment `6362252475` 清理** — v0.7.1-test 实验 deployment（3 天前失败的 publish run 残留）通过一次性 cleanup workflow（`github-actions[bot]`）自动加 `inactive` status，UI 不再显示为 "Active"

### Stats

- **测试**：342 passed, 1 skipped（无回归）
- **PyPI**：无新发布（v0.7.4 仍是最新）
- **main HEAD**：`2635cfde9b2e2a7b0382aed7d6b3ae287caf2b1c`
- **PRs in this release**：#17 + #18 + #19 + #20（其中 #17 是 v0.7.4 补 CHANGELOG，#18/#19/#20 是 v0.7.5 CI 修复）

### Notes

- 本 release 是**纯 CI/仓库工程化变更**，不影响 PyPI 包内容，也不影响受审计业务代码
- 下一 release (v0.7.6) 计划：切回 `pandaone-guard` PyPI 包名（需先在 PyPI 建新项目 + 配置 Trusted Publisher），把临时回退 (PR #12) 还原

## [0.7.4] - 2026-09-13

### Changed (Rebrand: PandaX → Pandaone AI Agent)
- **PyPI 包名保留 `pandax-guard`**（不切 `pandaone-guard`，避免破坏现有用户 + PyPI Trusted Publisher 历史配置）
- **Python 包 import 路径从 `pandax` 改为 `pandaone`**（PR #4）：`from pandaone.cli import main`，旧 `import pandax` 仍可用（向后兼容别名）
- **CLI 主命令从 `pandax` 改为 `pandaone`** + 别名 `pandaone-guard` / `pandaone-mcp`（PR #4）：`pandaone --version` 输出 `pandaone-guard v0.7.4`，`pandax --version` 仍可用
- **7 层防御架构名从 "PandaX" 改为 "Pandaone AI Agent"**：L7 CI workflow `.github/workflows/audit.yml` job 名 + 错误消息
- **CI/CD 工程化**（publish.yml + audit.yml）：
  - publish.yml 加 API token fallback（PR #16）：当 `PYPI_API_TOKEN` secret 存在时优先使用 token 模式上传 PyPI，绕过 OIDC Trusted Publisher 配置不匹配的限制
  - audit.yml 加自动跳过分支（PR #11）：当 PR diff 只改 `.github/workflows/` 或 `.trae-html-share-packages/`（无业务代码变更），自动跳过审计验证
- **本地临时回退**（PR #12）：用户面安装指令从 `pip install pandaone-guard` 临时回退到 `pip install pandax-guard`（v0.7.4 实际发布的包），等 PyPI 上新建 `pandaone-guard` 项目 + Trusted Publisher 配置完成后再统一切回品牌名
- **Repository 元数据清理**：URL / Topics / About description 全部更新为 Pandaone AI Agent

### Stats
- **测试**：342 passed, 1 skipped（与 v0.7.3 持平）
- **PyPI**：[pandax-guard 0.7.4](https://pypi.org/project/pandax-guard/0.7.4/)（含 `pandaone` CLI 命令 + `pandax` 向后兼容别名）
- **GitHub Release**：[v0.7.4](https://github.com/hellob1889/Pandaone-AI-Agent/releases/tag/v0.7.4)
- **PRs in this release**: #4 + #5 + #6 + #7 + #8 + #9 (closed) + #10 + #11 + #12 + #13 + #14 + #15 + #16 (see [Release notes](https://github.com/hellob1889/Pandaone-AI-Agent/releases/tag/v0.7.4) for detail)

## [0.7.3] - 2026-09-11

### Added (审计可追溯性增强 / Audit Traceability)

- **`pandaone write --agent` 参数**：所有 audit 记录现在带 agent 身份字段
- **`pandaone write` 捕获 diff 上下文**（文本文件）：在 audit log 里存 `old_content` / `new_content`（截断 500 字符）
- **`pandaone log` 重写为彩色面板格式**（ANSI box drawing chars）：APPROVED=绿，REJECTED=红，agent=青，diff 行加号=绿 / 减号=红
- **HTML 导出升级为卡片式布局**：每条审计记录独立卡片 + 可折叠 diff 详情（`<details>` 标签）

### Added (国际化 / i18n)
- **16 个新双语 key**：`panel_file` / `panel_commit` / `panel_lines` / `panel_reason` / `panel_problem` / `panel_approach` / `panel_attempted` / `panel_detection` / `panel_action` / `panel_diff` / `panel_force_write` / `panel_verbose_hint` / `panel_agent_by` / `panel_no_commit` / `status_by_agent` / `status_writes`（zh-CN + en 双语）

### Stats
- **测试**：342 passed, 1 skipped
- **PyPI**：[pandaone-guard 0.7.3](https://pypi.org/project/pandaone-guard/0.7.3/)
- **Trusted Publishing**：tag `v0.7.3` push → GitHub Actions `publish.yml` 通过 OIDC 自动上传 PyPI

## [0.7.2] - 2026-09-10

### Fixed (CI 工程化 / CI Engineering)
- **CI Tests job 在干净 ubuntu-latest 上 25 秒 exit 1** —— 根因：test job 没 pin setuptools 版本，build-isolation 拉到的 setuptools 与 build job 不一致，导致 `pip install -e .[dev]` 阶段 metadata 解析失败
  - test job pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`，与 build 步骤完全对齐
  - v0.7.1 publish run（run 34429112009）Build ✅ / Tests ❌ / Publish ✅ — 已修复
  - 新验证 run（run 34430629959）Build ✅ / Tests ✅ / Publish ✅

### Added (CI 诊断加固 / CI Diagnostics Hardening)
- **pytest log artifact**：测试失败时 `tee /tmp/pytest.log` + `actions/upload-artifact@v4` 上传完整日志，artifact 名 `pytest-log-{run_id}`
- **continue-on-error + 显式 fail step**：解耦"上传日志"与"标红"，下次 CI 失败可以直接从 artifact 看到 pytest 输出，无需再重新跑

### Distribution
- **分发名 `pandax-guard`**（沿用 v0.7.1）：保留 `pandax` 作为内部 Python 包和 CLI 命令
- **wheel/sdist 文件名归一化**：`pandax_guard-0.7.2-py3-none-any.whl` + `pandax_guard-0.7.2.tar.gz`

### Stats
- **测试**：340 passed（与 v0.7.1 持平，无回归）
- **PyPI**：[pandax-guard 0.7.2](https://pypi.org/project/pandax-guard/0.7.2/)

## [0.7.1] - 2026-09-06

### Fixed (28 bugs)

**P0 安全 (5) / P0 Security (5)**：
- **#8 + #7** install-context 通配符阻塞（PS5.1 registry provider 改用 .NET API）
- **#12 v1** write 失败时 mode 恢复（try/finally + 原始 mode 恢复）
- **#12 v2** write 默认拒绝 ReadOnly 锁定文件（`--force-write` 显式 opt-in）
- **#22** pre-commit hook CRLF→LF
- **#23** watchdog dedupe（1 次写入只产 1 条审计，2 秒去重窗口）

**P1 (4) / P1 (4)**：
- **#2** status 用 `_iter_protected_files` 共享 helper（19 种扩展名全覆盖）
- **#5** `--lang` 全局参数支持任意位置（main() 预扫描 argv）
- **#15** PowerShell subprocess `-NoProfile -NonInteractive` + timeout=60
- **#29** `pandax init` merge-preserve（不再覆盖用户自定义 config.json）

**P2 (5) / P2 (5)**：
- **#21** doctor/write git 检测一致性（共享 `_resolve_git_exe()`）
- **#6** log 标签 i18n 完整（REJECTED/UNAUTHORIZED 走 t()）
- **#20** ci 区分空仓库 vs 首次 commit（智能 baseline fallback）
- **#9 / #10** 智能长度阈值（`_info_length` unicode 宽度，1 中文字 = 2 宽度）

**P3 (4) / P3 (4)**：
- **#13** log `-n` 简写作为 `--recent` 别名
- **#4** README summary 显示最新 Phase 而非旧 Step
- **#26** export html/md/text 报告标签本地化
- **#39** cmd_write 4 处硬编码中文改为 i18n

**UX + 横切 i18n (3) / UX + Cross-cutting i18n (3)**：
- **#14** log 在 lang=en 时 Reason 字段本地化
- **#17** status i18n 完整性
- **#48** `--trust-default` 自动接受新指纹

**UX (2) / UX (2)**：
- **#25** 独立 `pandax export` 子命令（语义清晰，不再借用 log）
- **#28** `pandax lock` 一键启用（未 init 时自动 init，首次使用友好）

**工程化 (4) / Engineering (4)**：
- **版本号漂移** `src/pandax/__init__.py` 的 `__version__` 字面量与 `pyproject.toml` 漂移 → 改为 `importlib.metadata.version()` 动态读取 + pyproject.toml fallback
- **README 分组标签** `load_readme_summary` 解析 H3 分组标题，把 P0/P1/P2/P3/UX 标签附加到 step 行
- **自指纹 CRLF 根因** `python -m build` 在 Windows 上把 cli.py LF 转 CRLF，wheel 后处理 normalize LF
- **方案 A 文件夹图标** `pandax lock` 同步切换 Windows 文件夹图标
- **Git 兼容性** `pandax init` 在 git 仓库中自动维护 `.gitignore`
- **Web 实时仪表盘** 新增 `pandax serve` 子命令（`localhost:8765` HTTP + SSE）

### Added
- **`tests/test_version_single_source.py`**（5 个测试）：版本号单一事实源回归
- **`--trust-default`** 在子命令后位置无关生效
- **右键菜单端到端测试覆盖**：Init/Lock/Status/Unlock + Bug #48 + 路径含空格/中文

### Changed
- README summary 自动取最新 Phase 而非旧 Step（#4）
- 右键菜单加 #28 一键 Lock 流程（自动 init）
- i18n 字典从 184 keys 增至 200+ keys

### Stats
- **测试**：264 passed（+21 新测试）
- **零回归**：所有原有测试保持通过
- **打包**：wheel 73 KB + sdist 156 KB + ZIP 235 KB
- **右键菜单**：HKCU 注册表 4 项 + macOS Quick Action + Linux Nautilus/Dolphin

## [0.7.0] - 2026-09-05

### Added (Phase 9: OS 右键菜单集成 / OS Context Menu Integration)
- **Windows 右键菜单**：HKCU 注册表级联菜单（无需管理员权限）
- **macOS Finder 服务**：Automator Quick Action
- **Linux 文件管理器**：Nautilus 脚本 + Dolphin 服务菜单
- **`pandax install-context`**：CLI 自动检测 OS 并安装右键菜单
- **`pandax uninstall-context`**：一键卸载右键菜单

### Added (Phase 10: 国际化 i18n / Internationalization)
- **`src/pandax/i18n.py`**：i18n 引擎（**184 keys** × 2 语言，100% 覆盖）
- **`--lang=zh-CN|en` 旗标**：CLI 语言切换
- **自动检测 OS 语言**：Windows `GetUserDefaultLocaleName` + Unix `LANG` + `locale` 模块
- **持久化偏好**：`~/.pandax/config.json` 保存用户语言偏好

### Added (CI / 自动化 / Automation)
- **`scripts/audit_i18n.py`**：对抗式审查脚本
- **`.github/workflows/lint.yml`**：4-job CI
- **`scripts/doctor.py`**：环境自检工具
- **`scripts/install.sh`** + **`scripts/install.ps1`**：跨平台 bootstrap 安装器

### Tests
- **191 个 pytest 测试全部通过**
- **新增 i18n 测试**（35 个）
- **新增 audit-CI 集成测试**（16 个）

## [0.6.2] - 2026-09-04

### Fixed
- **Hidden file protection bug**: `.env`, `.gitignore`, `.env.local` not locked (Python `Path.suffix` returns `""` for dotfiles)
- `--version` output shows outdated `v0.0.1` instead of real version
- `taskkill` hint on non-Windows platforms

### Changed
- Bumped version to 0.6.2 (was incorrectly showing 0.0.1 / 0.1.0)
- Locked wheel/sdist metadata

### Tests
- 140 passed

## [0.6.1] - 2026-09-04

### Fixed
- **CRITICAL: pre-commit hook bypass bug**: `git add -A` would automatically stage audit log, causing hook to falsely approve any commit.

### Added
- `tests/test_pre_commit_hook.py`: 5 tests covering bypass scenarios
- `实战验证报告.md`: full e2e validation report

### Tests
- 134 passed

## [0.6.0] - 2026-09-04

### Added - Phase 7: GitHub Actions CI (L7 defense)
- `pandax ci --root . --base main` subcommand
- `.github/workflows/audit.yml`: auto-run on pull_request + push
- Auto-comment on failed PR via `actions/github-script`

### Tests
- 129 passed

## [0.5.0] - 2026-09-04

### Added - Phase 6: MCP Server for AI Agents
- `pandax_mcp` package: stdio JSON-RPC 2.0 server
- 10 tools exposed
- Registered as `pandax-mcp` console script

### Tests
- 115 passed

## [0.4.0] - 2026-09-04

### Added - Phase 5: Binary File SHA256 Protection (L6 defense)
- `binary_protected_extensions`: 24 formats
- `binary_snapshots.json`: SHA256 dictionary
- `--from-file` and `--content-base64` options for `write`
- Watchdog now detects binary tampering

### Tests
- 105 passed

## [0.3.0] - 2026-09-04

### Added - Phase 4.6: 17 Text Formats Protected (L1 defense upgrade)
- `protected_extensions` defaults expanded from `["py"]` to 17 formats
- Watchdog filters by `protected_extensions`

### Tests
- 96 passed

## [0.2.0] - 2026-09-04

### Added - Phase 4: Multi-Format Audit Log Export
- `pandax log --format <fmt> --output <file>` exports audit history
- Supported: text / csv / tsv / json / yaml / md / html / xlsx / docx / pdf

### Tests
- 69 passed

## [0.1.0] - 2026-09-03

### Added - Phase 1-3: MVP
- 5-layer defense: L1 file lock / L2 watchdog / L3 pre-commit hook / L4 README startup / L5 fingerprint
- `pandax` CLI with `init`/`lock`/`unlock`/`write`/`log`/`status`/`install-hook`/`watch`
- Pure Python, cross-platform
- Self-fingerprinting via SHA256
- Append-only `.pandax/pandax.jsonl` audit log

### Tests
- 59 passed

[Unreleased]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.7.4...HEAD
[0.7.4]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.6.2...v0.7.1
[0.6.2]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.6.1...v0.6.0
[0.6.1]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.6.0...v0.6.0
[0.6.0]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.5.0...v0.5.0
[0.5.0]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.4.0...v0.4.0
[0.4.0]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.3.0...v0.3.0
[0.3.0]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.2.0...v0.2.0
[0.2.0]: https://github.com/hellob1889/Pandaone-AI-Agent/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hellob1889/Pandaone-AI-Agent/releases/tag/v0.1.0