# Changelog

All notable changes to Pandaone AI Agent will be documented in this file.

## [0.7.11] - 2026-09-15

### Added: 一键硬隔离安装 (PR #41)

**问题**：用户机器上多个 Python 版本（3.10 + 3.11）共存时，`pip install --user pandaone-guard==0.7.10` 只更新其中一个 Python 的 site-packages，另一个 Python 的 entry point（`pandaone.EXE`）会继续跑旧版本（0.7.8），导致 `pandaone doctor` 报告错误的版本号。这是 Python 多版本隔离的通用坑，不是 pandaone 独有。

**解决方案**：GitHub Release v0.7.11 新增两个**硬隔离**安装脚本，自动把所有内容装到专用 venv（不碰任何 site-packages）：

| 平台 | 脚本 | venv 路径 |
|---|---|---|
| Windows | `install.ps1` | `%LOCALAPPDATA%\pandaone\venv\` |
| macOS / Linux | `install.sh` | `~/.local/share/pandaone/venv` |

**特性**：
- ✅ 硬隔离：永远 venv 装，**不** fallback 到 `--user` / system site-packages
- ✅ 从 GitHub Release API 拉**最新** wheel（不是 PyPI，永远跟随最新 release）
- ✅ SHA256 校验 GitHub attestation（防止中间人）
- ✅ 自动把 venv/Scripts（Windows）或 venv/bin（*nix）加到 PATH
- ✅ 自动验证 `pandaone --version` 和 `importlib.metadata.version`
- ✅ 复用已下载 wheel + 已存在 venv（升级而非重建）

**用法**：

```powershell
# Windows 一行 (PowerShell)
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex
```

```bash
# macOS / Linux 一行
curl -sSL https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.sh | bash
```

或从 [GitHub Release v0.7.11](https://github.com/hellob1889/Pandaone-AI-Agent/releases/tag/v0.7.11) Assets 下载 `install.ps1` / `install.sh` 本地跑。

**publish.yml 修改**：
- L270 `files:` 改为 multi-line glob：`dist/*.whl` + `dist/*.tar.gz` + `install.ps1` + `install.sh`，让 GitHub Release 自动 attach 这两个脚本
- release body 加 "Hard-isolated install" 段落，链接到 GitHub raw URL

**对比传统 pip install**：

```bash
# 传统方式 (用户机器 Python 3.10/3.11 共存时会冲突):
pip install --user pandaone-guard==0.7.10
# → 装到 Python 3.10 user site-packages
# → 但 pandaone.EXE 来自 Python 3.11 scripts，仍然跑 Python 3.11 site-packages 里的旧版本
# → pandaone --version 显示旧版本号

# 硬隔离方式 (推荐):
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex
# → 装到独立 venv: C:\Users\X\AppData\Local\pandaone\venv\
# → pandaone.EXE 来自该 venv Scripts 目录
# → pandaone --version 永远显示真实装的版本
```

### 升级方式

- **已用 install.ps1/install.sh 装的**：`irm ... | iex` 再次跑一次（自动检测并升级）
- **传统 pip install 装的**：`pip install --upgrade pandaone-guard`（不变）

## [0.7.10] - 2026-09-15

### Fixed (PR #40 — Bug #40: 移除 `D:\软件\Git\cmd` 等作者机器硬编码路径)

**问题**：v0.7.9 及之前版本，`pandaone doctor` / `pandaone install-git` / git auto-detection 在 4 处硬编码了作者自用机器的路径 `D:\软件\Git\cmd`。99.9% 的 Windows 用户都没有这条路径，导致：
- `_find_git_executable` 永远多跑一次 `os.path.isfile('D:\软件\Git\cmd\git.exe')` 返回 False
- `for prefix in ["D:\\", "C:\\"]: for sub in ["软件", "Program Files", ...]` 这种"作者目录白名单"模式跨语言失效（中文 Windows 是"软件"，英文 Windows 是"Software"）
- 4 处候选列表各自维护，重复硬编码 → 永远同步不齐

**修复**：
- 在 `src/pandaone/git_installer.py` 新增 `_windows_candidate_dirs()` 单一来源函数
- 来源基于**环境变量 + 注册表**：
  1. `%ProgramFiles%` / `%ProgramFiles(x86)` / `%ProgramW6432%\Git\cmd|bin`
  2. `%LOCALAPPDATA%\Programs\Git\cmd|bin` (Portable Git / 微软商店版)
  3. `%USERPROFILE%\scoop\apps\git\current|2.47.1|2.43.0\cmd|bin` (Scoop 安装)
  4. 注册表 `HKLM\SOFTWARE\GitForWindows\InstallPath\cmd|bin` (Git for Windows 安装器自写)
  5. `C:\Git\cmd|bin` (便携位置)
  6. `%USERPROFILE%\Git\cmd` 等常见解压位置
- 4 处调用点全部改为调用 `_windows_candidate_dirs()`：
  - `git_installer.py` `_find_git_executable`
  - `cli_chunks/part_003.py` `_resolve_git_exe`
  - `cli_chunks/part_005.py` `cmd_install_git`
  - `pandaone_guard/__main__.py` `_ensure_git_in_path`
  - `tests/conftest.py` `GIT_CANDIDATES`

**对抗式审查**：
- 不假设用户在哪个盘（C/D/E/...）
- 不假设语言环境（中文"软件" vs 英文"Software"）
- 不假设安装方式（标准 / Scoop / 微软商店 / 解压）
- 注册表项是 Git for Windows 安装器**自己写的**，作为权威来源
- 所有调用点共用一个函数，杜绝未来再漂移

### 用户面行为变化

- `pandaone doctor` 在 Windows 上能正确检测到**用户实际安装**的 git（不再受作者机器路径污染）
- Git 在 PATH 时仍优先返回（保持 fast path 行为）
- 在 Windows 上 Git 装在非默认位置（`D:\dev\Git` 等）也能检测（注册表 InstallPath + 多种常见子目录模式）

### 升级方式

```bash
pip install --upgrade pandaone-guard==0.7.10
```

无需 `--update-fingerprint`（本次未改 cli loader，纯 git 检测逻辑）。

## [0.7.9] - 2026-09-14

### Fixed (PR #35 — `pandaone install-context` Windows broken since v0.7.0)

**问题**：Windows 用户从 v0.7.0 起右键菜单永远不可用。修 PS1 6 个 bug 仍不能完整工作。

**Root cause**：PowerShell 脚本 5 个累积 bug 导致 parser 失败：

1. **5 个 UTF-8 BOM**：文件头 `EF BB BF` 重复 5 次，PowerShell 5.1 parser 把后续 `[CmdletBinding()]` 误认为普通 attribute
2. **`#Requires -Version 5.1` line**：v0.7.4+ 添加，PowerShell 5.1 parser 把它当成 `#Requires` 后立即接 `[CmdletBinding()]` 失败
3. **`[CmdletBinding()]` 后函数体内 `$ErrorActionPreference = 'Stop'`**：PowerShell 5.1 parser bug，把 param list 延伸到 `$ErrorActionPreference`
4. **注释里的 `(任意文件) (pandaone init) (pandaone lock)`**：PowerShell 5.1 parser 把注释里的括号也算 param list 括号
5. **PowerShell 7+ 表达式 `if`**：`$VAR = if (...) { ... } else { ... }` 是 PS7+ 语法，用户机器 PS5.1 不支持

**修复策略**：不再折腾 PowerShell — Windows 直接用 Python `winreg` 模块写注册表，完全 bypass PowerShell。注册表结构与原 PS1 等价（HKCU\\Software\\Classes\\\*\\shell\\Pandaone + 4 subcommands）。

### Fixed (PR #35 — cli.py loader `__file__` bug)

`cli.py` loader 用 `_exec_ns["__file__"] = str(Path(__file__).resolve())` 把 `__file__` 钉死成 cli.py 自己路径，所有 part_* 脚本里 `ROOT = Path(__file__).parent.parent` 解析到 site-packages/ 而非 site-packages/pandaone/。导致 L4 防线 README.md 找不到 + portable git 下载错位 + sys.path.insert 错。

**修复**：loader 在每个 chunk exec 前 `_exec_ns["__file__"] = str(chunk.resolve())` 让每个 chunk 用自己路径。

### Fixed (PR #35 — README.md not in wheel)

`MANIFEST.in` 没 `include src/pandaone/README.md`，导致 wheel 安装后 L4 防线 README summary 永远报错 "[ERROR] README.md 未找到"。

**修复**：`include src/pandaone/README.md`。

### Added (PR #35 — install-context 暴露 stderr)

`cmd_install_context` 之前用 `subprocess.run(..., capture_output=True)` 把 PowerShell stderr 完全吞掉，用户只能看到 exit 1 不知道原因。

**修复**：去掉 `capture_output=True`，stderr 直接输出 + 加 `TimeoutExpired/FileNotFoundError` 友好错误消息。

### 升级方式

```bash
pip install --upgrade pandaone-guard

# 升级后首次跑会触发 L5 指纹更新（v0.7.9 改了 cli loader, SHA256 变了）:
pandaone --update-fingerprint 0000

# 然后右键菜单安装:
pandaone install-context
```

### 用户面行为变化

- `pandaone install-context` 在 Windows **真的能用**了（之前 v0.7.0~v0.7.8 一直不可用）
- 注册表写入通过 Python `winreg`，不依赖 PowerShell（无 PS5.1/PS7 兼容问题）
- 4 个子命令：Init / Lock / Status / Unlock
- macOS / Linux 仍用 .sh 脚本（未受影响）

## [0.7.8] - 2026-09-14

### Fixed (PR #28 follow-up: git auto-installer + doctor 子命令真正可用)

PR #28 在 fix/auto-install-git 分支写了 git_installer.py / cmd_doctor.py / i18n_extras.py,
通过 PR #31 merge 到 main。但 PR #28 设计了两个**隐藏 bug**,让 doctor 子命令
对 `pandaone` entry point 实际**不可用**,`ci --base` 参数**被忽略**。v0.7.8 修复
这两个 bug + 加 doctor 的 cmd_doctor 等价 PR #28 的内容。

- **PR #32 (P0 / 阻断): `pandaone doctor` 不可用**
  - 现象:`pandaone --help` 列 14 个子命令,没有 doctor。`pandaone doctor` 报
    `invalid choice: 'doctor'`。
  - 根因(双 bug):
    1. `pyproject.toml` entry point `pandaone = "pandaone:main"` 走
       `pandaone/__init__.py:main`,**完全跳过 `__main__.py`** — monkey-patch
       注册的 doctor 子命令从未生效。
    2. v0.7.7 把 84KB cli.py 拆 cli_chunks/part_*.py 用 `exec()` 加载,loader 用独立
       `_exec_ns` dict 作 exec namespace,exec 后 `for k,v: globals()[k]=v` 浅复制。
       Python 函数 `__globals__` 在 def 时绑定,part_006 的 `def main():` 的
       `__globals__` 指向原 `_exec_ns` (不是 cli 模块 globals)。monkey-patch
       `cli.build_parser = patched` 只改 cli 模块 globals,`cli.main()` 内部查找
       `build_parser` 走自己的 `__globals__` — 看不到 patched version。
  - 修复:
    1. `src/pandaone/__main__.py`:把 `if __name__ == "__main__":` 保护块改成
       顶层 `def main():`,让 entry point 能调到。
    2. `pyproject.toml`:entry point 改 `"pandaone.__main__:main"` — import 时
       触发 `_ensure_doctor_registered()` 注册副作用。
    3. `src/pandaone/cli.py` loader:`_exec_ns = globals()` 直接共享 dict 引用,
       让 part_006 main 函数的 `__globals__` 自然指向 cli 模块 globals。

- **PR #33 (P1): `pandaone ci --base` 被 HEAD~1 fallback 顶替**
  - 现象:`pandaone ci --base main --head HEAD` 即使 base 解析成功,实际 diff
    仍是 `HEAD~1..HEAD`,`--base main` 参数被静默忽略。
  - 根因:`cmd_ci` 里 `candidates = ["HEAD~1", base, f"origin/{base}", ...]`
    `HEAD~1` 永远存在且排第一,`for ref in candidates: ... base = ref` 把
    用户的 base 顶替掉。
  - 修复:把顺序改成 `[base, f"origin/{base}", "HEAD~1", "main", "master", ...]` —
    用户传的 base 优先,HEAD~1 降级为真正的 fallback。
  - 测试:新增 `test_ci_explicit_base_overrides_head_minus_1` 回归测试,用
    detached HEAD 让 main 不跟随 forward,断言 `--base HEAD~1` 和 `--base main`
    表现不同 (证明 base 真的在用),`--base <evil_sha>` 看 0 变更 PASS。

### Added (PR #28 / #31)
- **`git_installer.py`**:跨平台 git 自动安装 (Windows: winget / choco / scoop /
  manual download;macOS: brew;Linux: apt / dnf / yum)。多路径探测 (PATH +
  WindowsApps shim + `D:\软件\Git` 等用户目录 + USERPROFILE `\cmd\git.exe`)。
  缺失 git 时 `pandaone` 启动自动触发安装,避免 L2 (watchdog 回滚) 和 L3
  (pre-commit hook) 静默降级。
- **`cmd_doctor.py`**:`pandaone doctor` 子命令。报告 7 层防护 + git + Python
  状态,支持 `--silent --json` 输出给 CI / 监控系统用。退出码:0=全部 OK,
  1=git 缺失,2=Python 太老。
- **`i18n_extras.py`**:18 个新 key × 2 语言 (zh-CN + en) 翻译,doctor + git gate
  文案。
- **32 个新单测**:`tests/test_git_installer.py` (19 个) + `tests/test_cmd_doctor.py`
  (13 个),覆盖跨平台 git 检测、安装、doctor 输出格式、JSON 结构、退出码。

### Notes
- 升级方式:`pip install --upgrade pandaone-guard`
- 用户面行为变化:
  - `pandaone --help` 多一个 `doctor` 子命令
  - `pandaone ci --base <ref>` 现在尊重用户传的 `<ref>`,不被 HEAD~1 顶替
  - `pandaone` 启动自动检测 git,缺失时尝试自动安装 (可用
    `PANDAONE_SKIP_GIT_CHECK=1` 环境变量跳过,适合 CI 环境)
- API 兼容性:不破坏现有 API;`pandaone write` / `pandaone init` / `pandaone ci`
  等所有子命令行为不变

## [0.7.7] - 2026-09-13

### Fixed (验证报告驱动的批量 bugfix)

本 release 修复了 pandaone-运行可行性验证报告.html 中识别的 6 个问题，让 L7 防线 (GitHub Actions CI 审计) 真正生效。

- BUG-04a (P0 / 阻断): .github/workflows/audit.yml 切到 pip install -e . + pandaone ci
  - 之前 audit.yml 装的是 PyPI 上的 pandax-guard 固定版本 + 调用旧 CLI pandax ci。
  - 后果：CI 一直跑"绿色假阳性"，验证的是被废弃的旧实现。
  - 修复：装当前分支 (pip install -e .)，调用命令切到 pandaone ci。
- BUG-01 (P1): src/pandaone_mcp/__init__.py 补 from .__main__ import main re-export
  - console_scripts 入口 pandaone_mcp:main 要求 main 从 package 顶层可导入。
  - 修复：参考 pandaone_guard/__init__.py 的同模式，显式 re-export。
- BUG-04b (P2): README 解析器兼容中英对照标题 ## 当前阶段 / Current Phase
  - 旧解析器严格相等匹配，双语标题会让 phase_lines 永远为空。
  - 修复：增加 OR 分支接受双语标题。
- BUG-05 (P3): pandaone write 用 git add -f 强制暂存审计日志
  - .pandaone/pandaone.jsonl 被 .gitignore 排除，普通 git add 会被 git 拒绝。
  - 修复：加 -f 强制暂存，让审计 jsonl 跟 commit 原子绑定。
- BUG-02 + BUG-06 (P4): 仓库卫生清理
  - 清理磁盘残留：src/pandax_guard.egg-info/ / test_project/ / __pycache__/ x 6 / .pytest_cache/
  - 验证 .gitignore 已覆盖所有模式。

### Notes
- 本 release 是纯 bugfix，不引入新功能、不破坏 API
- 升级方式：pip install --upgrade pandaone-guard
- 用户面行为变化：MCP server 现在能正常启动（之前是 import 报错）

## [0.7.6] - 2026-09-13

### Changed (品牌切回 / Rebrand Cutover)

- PyPI 分发名从 pandax-guard 切回 pandaone-guard (PR #23)
- pyproject.toml name = "pandaone-guard", version = "0.7.6"
- 13 个用户面文件:pandax-guard → pandaone-guard (还原 PR #12 临时回退)
- 发布到 PyPI 后用户可执行 pip install pandaone-guard