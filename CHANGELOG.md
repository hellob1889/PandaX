# Changelog

All notable changes to Pandaone AI Agent will be documented in this file.

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