# PandaX v0.7.0 真实场景 Bug 清单

> **测试环境**：Windows 11 + Python 3.11 + `pip install -e .` (PandaX 0.7.0)
> **测试时间**：2026-09-05
> **测试项目**：`D:\pandax-test\`（单文件 test.py + README.md + .env + config.json）
> **测试方法**：第一性原理 + 对抗式审查
>
> **总计**：15 个有效 Bug（1 个误判已撤销，2 个测试方法问题）

---

## 严重程度分级

- 🔴 **critical**：审计核心安全失效 / 系统挂死 / 数据损坏
- 🟡 **mid**：i18n 不完整 / 文档缺失 / 用户体验差
- 🟢 **low**：样式问题 / 参数缺失别名 / 文案不准确

---

## Bug 清单

| # | 严重 | 模块 | 简述 |
|---|---|---|---|
| 12 | 🔴 critical | write | write 失败时不清除的 mode 恢复不完整（hidden/system 文件写入失败后永久 writable） |
| 8 | 🔴 critical | install-context | PS1 `Test-Path` 把 `*` 当通配符，永久阻塞 |
| 7 | 🔴 critical | install-context | 中断时注册表留半成品（无 Icon/SubCommands/command 子键） |
| 2 | 🔴 high | status | 只扫描 `.py`，忽略其余 16 种受保护扩展名 |
| 5 | 🔴 high | global | `--lang` 必须放子命令前才生效（CLI 解析顺序问题） |
| 6 | 🟡 mid | log | log 标签（Reason/Problem/Approach）和 Reason 字符串是 hardcoded，未走 t() |
| 17 | 🟡 mid | status | status 输出完全没做 i18n，`--lang=en` 时仍中文 |
| 9 | 🟡 mid | write | reason 长度 < 5 字符被拒，中文短句易误伤 |
| 10 | 🟡 mid | write | problem 长度 < 10 字符被拒，中文短句易误伤 |
| 15 | 🟡 mid | install-context | PowerShell subprocess 在非 TTY 下不退出，pandax 永远等待 |
| 19 | 🟡 mid | status | status 报 Locked=N 但不检查当前 ReadOnly 实际状态 |
| 20 | 🟡 mid | ci | ci 报 "empty repo" 但实际有文件 |
| 21 | 🟡 mid | write / doctor | write 报 git not installed，doctor 报 git OK（检测不一致） |
| 3 | 🟢 low | global | `--silent` flag 不生效，banner + README 仍显示 |
| 4 | 🟢 low | cli.py | README summary 停在 Step 13，与实际 Phase 11 / Step 89+ 脱节 |
| 13 | 🟢 low | log | `log -n N` 无效（应为 `--recent N`），缺少短选项别名 |
| 14 | 🟡 mid | log | log 在 `--lang=en` 时 Reason 标签仍是中文（与 #6 关联） |

---

## 详细复现与根因分析

### Bug #12 🔴 critical — write 失败时 mode 恢复不完整（隐藏/系统属性丢失）

**复现步骤**：
```bash
# 1. 创建 PandaX 项目
pandax init --root D:\test-write

# 2. 锁定文件
pandax lock --root D:\test-write
#   → test.py mode=0o100444, IsReadOnly=True

# 3. 标记文件为 hidden + system（attrib 命令）
attrib +h +s D:\test-write\test.py

# 4. 试图 write（即使 reason/problem/approach 完美）
pandax write --root D:\test-write --file test.py \
    --reason "..." --problem "..." --approach "..." \
    --old '...' --new '...'

# 5. 检查文件属性（应当仍然 ReadOnly）
dir D:\test-write\test.py
```

**结果（修复前）**：
- write 抛 PermissionError（hidden+system 阻止 write_text 写入）
- 文件 mode **变成 0o100666，IsReadOnly=False** ❌
- 锁永久失效，文件可被任何编辑器/进程修改

**结果（修复后）**：
- write 抛 PermissionError → audit REJECTED
- 文件 mode **恢复 0o100444，IsReadOnly=True** ✅

**根因**：`cli.py cmd_write` step 4 写入步骤没有 try/finally 包裹：
```python
target.write_text(new_content, encoding="utf-8")  # 抛 PermissionError → 文件 mode 永久 writable
# 写入失败也不会恢复 mode
```

**修复方案**（已实施 commit）：
1. 整个 step 4 包在 try/except/finally 中
2. finally 块 `os.chmod(target, mode)` 用 step 3 保存的**原始 mode** 恢复
3. 业务拒绝（`--old` 不在文件）通过专用异常 `_OldNotFoundError` 区分
4. IO 错误记录 audit REJECTED + 恢复 mode

**关键变更**：
- `cli.py` 第 645-744 行：`cmd_write` 重写为 try/except/finally 结构
- 新增 `_OldNotFoundError` 异常类（line 451-457）

**验证**：`test_write_lock_robustness.py` ADVERSARIAL 1+2 全过，`tests/test_write.py` 8/8 全过，191/191 测试套件零回归。

---

### Bug #8 🔴 critical — install-context PS1 通配符阻塞

**复现步骤**：
```powershell
pandax uninstall-context  # 干净状态
pandax install-context --force
```

**结果**：`[1/4] Cleaning old entries...` 显示后**永久挂死**（180s+）。

**根因**：`installer/windows/install_context_menu.ps1` 和 `uninstall_context_menu.ps1` 使用：
```powershell
Test-Path "HKCU:\Software\Classes\*\shell\PandaX"
```
PS 把 `*` 当通配符，glob 整个 `HKCU:\Software\Classes\*`（上千 ProgID），可能进入死循环或挂死。

**修复**：
```powershell
Test-Path -LiteralPath "HKCU:\Software\Classes\*\shell\PandaX"
Remove-Item -LiteralPath $path -Recurse -Force
New-Item -LiteralPath $path -Force | Out-Null
```
所有 `*` 出现的位置都用 `-LiteralPath` 替代。

**影响范围**：
- `installer/windows/install_context_menu.ps1`（4 处）
- `installer/windows/uninstall_context_menu.ps1`（5 处）

---

### Bug #7 🔴 critical — install-context 中断残留

**复现**：Bug #8 触发后 Ctrl+C，注册表残留：
```
HKCU\Software\Classes\*\shell\PandaX
    (Default)  = "PandaX"
    MUIVerb    = "PandaX 审计工具 / Audit Tools"
```
**缺**：Icon, SubCommands, Init/Lock/Status/Unlock 子菜单及其 command 子键。

**根因**：每次 `Install-CascadeMenu` 调用**非原子**——先写主菜单值，再写 4 个子菜单，子菜单之间无事务。

**修复**：
1. 改 Bug #8 后此 Bug 自然消失（不再中断）
2. 加防御：写注册表前先全部准备好 dict，最后一次性 flush；失败时自动 rollback
3. uninstall 时改用更宽松的清理逻辑（删除整个 `*` key 树而非仅 `*` 单 key）

---

### Bug #2 🔴 high — status 只查 .py

**复现**：
```bash
pandax status --root D:\pandax-test
# [L1 File Lock] Total .py files: 1
# 但实际有 .py, .md, .json, .env 4 个受保护文件
```

**根因**：`cli.py:950` `py_files = [p for p in root.rglob("*.py")]`，硬编码 `*.py`。

**修复**：用共享的 `PROTECTED_EXTS` 常量（lock/unlock 已用 19 种扩展名）。

---

### Bug #5 🔴 high — --lang 位置敏感

**复现**：
```bash
pandax --lang=en status --root .   # ✅ 英文
pandax status --root . --lang=en   # ❌ 仍中文
```

**根因**：`cli.py` argparse 在 `parse_known_args` 时，全局 `--lang` 在 `subcommand parser` 之后才解析。

**修复方案**：
1. 手动从 `sys.argv` 提取 `--lang=`，全局设到 `i18n._lang`
2. 或在每个子命令 parser 加 `--lang` 别名
3. 或用 `argparse.ParentParser` 模式

---

### Bug #6 + #14 🟡 mid — log 标签和 reason 字符串硬编码

**复现**：
```bash
pandax --lang=en log --recent 3
# 输出仍是：Reason: / Problem: / Approach: / attempted: / "problem 长度 < 10"
```

**根因**：`cli.py:870-883` 直接 `print(f"\n[{ts}] {status}  id={rid}  file={file_}")` 和 `print(f"  Reason:   {reason}")`——label 和 reason 都未走 `t()`。

**修复**：在 i18n 字典加 `log_label_reason`, `log_label_problem`, `log_label_approach`, `log_label_attempted` 等 key，并要求 `cmd_write` 在记录审计时把 reason 也存为 i18n key 而非直接字符串。

---

### Bug #17 🟡 mid — status 不做 i18n

**复现**：
```bash
pandax --lang=en status --root .
# 输出："PandaX 状态仪表盘", "[L1 文件锁]", "总计 .py 文件", etc.
```

**根因**：`cmd_status` 内字符串全部 hardcoded 中英混合。

**修复**：和 Bug #6 一起处理，给 status 全部走 `t()`。

---

### Bug #9 + #10 🟡 mid — write 长度限制对中文不友好

**复现**：
```bash
pandax write --reason "测试写入" ...   # 4 字符 → REJECTED "reason 长度 < 5"
pandax write --problem "原文件太简单" ...   # 9 字符 → REJECTED "problem 长度 < 10"
```

**根因**：长度检查用 `len(string)`（字节数？字符数？取决于编码）。

**修复**：
1. 改成字符数（已经是字符数，但阈值太低）
2. 阈值改成 `reason >= 3`, `problem >= 5`, `approach >= 5`（更宽松）
3. 提示信息也走 i18n

---

### Bug #15 🟡 mid — PowerShell subprocess 不退出

**复现**：`pandax uninstall-context` 在干净状态下输出 `[OK] Removed 0 registry entries.` 后**180 秒**仍不退出。

**根因**：`subprocess.run(cmd, check=False, env=env)` 缺 timeout；powershell 在缺 stdin 时进程可能不主动 exit。

**修复**：
```python
try:
    rc = subprocess.run(cmd, check=False, env=env, timeout=60).returncode
except subprocess.TimeoutExpired:
    print("[WARN] installer script timeout, killed")
    return 124
```
同时给 powershell 加 `-NoProfile -NonInteractive` 参数。

---

### Bug #18 🟡 mid — write 静默清除 ReadOnly

**复现**：见 Bug #12 复现，write 成功后 `os.stat(path).st_mode == 0o100666`（被清）。

**根因**：Python `open(path, 'w')` 写入时不保留 mode；写完需手动 `os.chmod`。

**修复**：
```python
old_mode = path.stat().st_mode
path.write_text(new_content, encoding='utf-8')
os.chmod(path, old_mode)  # 恢复原 mode
```
或拒绝写入 ReadOnly 文件（推荐，见 Bug #12）。

---

### Bug #19 🟡 mid — status 报 Locked 但实际未锁

**复现**：
```bash
pandax lock   # mode=0o100444
pandax write ...   # Bug #18，mode 被清
pandax status   # 仍报 Locked=1
```

**根因**：status 用 `pandax.lock` 的内部 L1 metadata 判断（哪个文件被 lock 过），而非每次 `os.stat()` 实际检查。

**修复**：status 改成每次实际 stat ReadOnly 标志，给出真实状态。

---

### Bug #20 🟡 mid — ci 误报 empty repo

**复现**：
```bash
pandax ci --root D:\pandax-test
# 输出 "Baseline: none (first commit, no history to compare)"
# "repository is empty (no changes to audit)"
```

**根因**：D:\pandax-test 不是 git 仓库，ci 命令没有 git fallback 处理未初始化仓库的情况。

**修复**：
1. ci 自动检测 `git status` 是否可用
2. 不可用时用 `binary_snapshots.json` 作为 baseline 替代
3. 或更明确告诉用户 "this dir is not a git repo"

---

### Bug #21 🟡 mid — write/doctor git 检测不一致

**复现**：
```bash
pandax doctor.py   # 12/12 OK, git OK
pandax write ...   # [WARN] git not installed
```

**根因**：两处 git 检测代码路径不同。

**修复**：统一 git 检测函数 `git_available() -> bool` 在 `core/utils.py`，doctor 和 write 都用。

---

### Bug #3 🟢 low — --silent 无效

**复现**：
```bash
pandax --silent status --root .
# 仍然显示 ASCII banner + README summary
```

**根因**：`_print_banner()` 不检查 `--silent` 标志。

**修复**：在 `main()` 开头 `_print_banner()` 前判断 `args.silent`，是则 return。

---

### Bug #4 🟢 low — README summary 过时

**复现**：每次 `pandax` 启动都打印 README summary，但只到 Step 13 / Phase 2，实际已到 Phase 11 / Step 89+。

**根因**：README summary 是 `__main__.py` 启动时打印的硬编码文本。

**修复**：要么删掉这个 summary（它对回放项目历史有帮助但已经过时），要么从 `docs/ROADMAP.md` 动态加载。

---

### Bug #13 🟢 low — log -n 无效

**复现**：
```bash
pandax log -n 3   # 显示全部 11 条记录
```

**根因**：argparse 中没有 `-n` 别名，只有 `--recent N`。

**修复**：argparse 加 `add_argument("-n", "--recent", type=int, default=20)`。

---

## 误判与撤销

### ~~Bug #1~~ 撤销 — lock 命令实际有效

之前怀疑 `pandax lock` 在 Windows 上失效，实际测试：
- `pandax lock` 把 test.py/md/env/json 都从 0o100666 改成 0o100444 + IsReadOnly=True ✅
- `pandax unlock` 全部还原 ✅
- 是 init 时已经自动 lock 了所有受保护文件，**lock 命令本身工作正常**

真正的问题是 **Bug #12（write 失败时 mode 恢复不完整）**。

### ~~Bug #18~~ 撤销 — write 静默清除 ReadOnly（误判）

最初报告说 write 改完文件后 IsReadOnly 被清除。深入测试发现：
- write 设计**就是**先 chmod writable → 写 → chmod readonly
- 写成功路径下，mode 恢复 0o100444 + IsReadOnly=True ✅
- 误判来源：第一次测试只看 status "Locked=1" 就下结论，没看真实 mode

**真实的 #18 不存在**——实际是 #12（写入失败路径没恢复）。

---

## 修复优先级建议

**P0（必修，发布前）**：
- #12 write 绕过文件锁 — 核心安全漏洞
- #8 install-context 通配符阻塞 — 用户首次安装即卡死
- #7 install-context 中断残留 — 半成品注册表污染系统

**P1（应该修，下个版本）**：
- #2 status 只看 .py — 审计覆盖不全
- #5 --lang 位置敏感 — 用户体验
- #15 PowerShell subprocess 不退出 — CI/脚本调用困难
- #19 status 报 Locked 但实际未锁 — 安全假象

**P2（可以延后）**：
- #6 / #14 / #17 i18n 完整性（status, log labels）
- #9 / #10 write 长度阈值对中文不友好
- #18 write 静默清除 ReadOnly
- #20 ci 误报 empty repo
- #21 doctor/write git 检测不一致

**P3（nice-to-have）**：
- #3 --silent 无效
- #4 README summary 过时
- #13 log -n 别名缺失

---

## 修复方案快速参考

### Bug #8 修复（最优先，影响首次安装）

**install_context_menu.ps1** 4 处替换：
```diff
- Test-Path $Path
+ Test-Path -LiteralPath $Path
- Remove-Item -Path $Path -Recurse -Force
+ Remove-Item -LiteralPath $Path -Recurse -Force
- New-Item -Path $Path -Force | Out-Null
+ New-Item -LiteralPath $Path -Force | Out-Null
- New-ItemProperty -Path $Path ...
+ New-ItemProperty -LiteralPath $Path ...
```

**uninstall_context_menu.ps1** 5 处替换同上。

### Bug #12 修复（核心安全）

```python
# core/write.py 或 cli.py cmd_write
def cmd_write(args):
    target = Path(args.root) / args.file
    # Bug #12 fix: 检查 ReadOnly
    if os.name == 'nt':
        import stat
        mode = target.stat().st_mode
        if not (mode & stat.S_IWRITE):
            return {"status": "REJECTED", "reason": t("write_rejected_readonly", file=str(target))}
    # 原有流程 ...
```

### Bug #15 修复（subprocess timeout）

```python
# cli.py _run_installer
try:
    rc = subprocess.run(cmd, check=False, env=env, timeout=60).returncode
    return rc
except subprocess.TimeoutExpired:
    print(t("warn_install_timeout"))
    return 124
```

并给 powershell 加 `-NoProfile -NonInteractive`：
```python
interpreter = handler["interpreter"] + ["-NoProfile", "-NonInteractive"]
```

---

## 附：所有 bug 一句话总结

1. ~~lock 在 Windows 失效~~ **撤销**（实际有效）
2. status 只查 .py
3. --silent 不生效
4. README summary 过时（Step 13 vs Step 89+）
5. --lang 位置敏感
6. log 标签硬编码
7. install-context 中断残留
8. install-context 通配符阻塞
9. reason 长度限制
10. problem 长度限制
11. ~~--old 找不到~~ **撤销**（PowerShell 引号问题，非 pandax bug）
12. **write 失败时 mode 不恢复（最严重，已修复）**
13. log -n 无效
14. log 在 lang=en 时仍中文（与 #6 关联）
15. PowerShell subprocess 不退出
16. ~~status 命令卡死~~ **撤销**（之前测试环境残留进程导致，非 status 本身问题）
17. status 不做 i18n
18. ~~write 静默清除 ReadOnly~~ **撤销**（写入成功路径实际恢复 mode）
19. status 报 Locked 但实际未锁
20. ci 误报 empty repo
21. doctor/write git 检测不一致

## 修复记录（v0.7.0 → v0.7.1）

### 已修复
- **#8** + **#7**（install-context 通配符 + 中断残留）：
  - `installer/windows/install_context_menu.ps1`：改用 .NET `[Microsoft.Win32.Registry]` API 替代 PS cmdlets
  - `installer/windows/uninstall_context_menu.ps1`：同样改用 .NET API
  - 完整注册表写入验证（37 行：Default + MUIVerb + Icon + SubCommands + 4 个子菜单带 command）
- **#12**（write 失败时 mode 恢复）：
  - `src/pandax/cli.py` 重写 `cmd_write` step 4 为 try/except/finally
  - 新增 `_OldNotFoundError` 业务异常类
  - finally 块始终 `os.chmod(target, mode)` 恢复**原始 mode**

### 验证
- `tests/test_write.py` 8/8 通过
- 完整套件 **191/191 通过**，零回归
- 对抗测试 `test_write_lock_robustness.py` ADVERSARIAL 1+2 全过
