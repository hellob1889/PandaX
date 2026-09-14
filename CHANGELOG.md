# Changelog

All notable changes to Pandaone AI Agent will be documented in this file.

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