# PandaX v0.7.0 真实场景 Bug 清单 / PandaX v0.7.0 Real-World Bug List

> **测试环境 / Test Environment**：Windows 11 + Python 3.11 + `pip install -e .` (PandaX 0.7.0)
> **测试时间 / Test Time**：2026-09-05
> **测试项目 / Test Project**：`D:\pandax-test\`（单文件 test.py + README.md + .env + config.json）
> **测试方法 / Test Method**：第一性原理 + 对抗式审查 / First Principles + Adversarial Review
>
> **总计 / Total**：15 个有效 Bug（1 个误判已撤销，2 个测试方法问题 / 15 valid bugs (1 misjudgment revoked, 2 test method issues)

---

## 严重程度分级 / Severity Levels

- 🔴 **critical**：审计核心安全失效 / 系统挂死 / 数据损坏 / Audit core security failure / system hang / data corruption
- 🟡 **mid**：i18n 不完整 / 文档缺失 / 用户体验差 / i18n incomplete / docs missing / poor UX
- 🟢 **low**：样式问题 / 参数缺失别名 / 文案不准确 / Style issues / missing param aliases / inaccurate text

---

## Bug 清单 / Bug List

| # | 严重 / Severity | 模块 / Module | 简述 / Summary |
|---|---|---|---|
| 12 | 🔴 critical | write | write 失败时不清除的 mode 恢复不完整（hidden/system 文件写入失败后永久 writable）/ mode restoration incomplete on write failure (hidden/system file becomes permanently writable after write failure) |
| 8 | 🔴 critical | install-context | PS1 `Test-Path` 把 `*` 当通配符，永久阻塞 / PS1 `Test-Path` treats `*` as wildcard, permanent block |
| 7 | 🔴 critical | install-context | 中断时注册表留半成品（无 Icon/SubCommands/command 子键）/ Registry left half-done on interrupt (no Icon/SubCommands/command subkeys) |
| 2 | 🔴 high | status | 只扫描 `.py`，忽略其余 16 种受保护扩展名 / Only scans `.py`, ignoring other 16 protected extensions |
| 5 | 🔴 high | global | `--lang` 必须放子命令前才生效（CLI 解析顺序问题）/ `--lang` must be before subcommand (CLI parsing order issue) |
| 6 | 🟡 mid | log | log 标签（Reason/Problem/Approach）和 Reason 字符串是 hardcoded，未走 t() / log labels and Reason strings hardcoded, not via t() |
| 17 | 🟡 mid | status | status 输出完全没做 i18n，`--lang=en` 时仍中文 / status output not i18n'd, still Chinese when `--lang=en` |
| 9 | 🟡 mid | write | reason 长度 < 5 字符被拒，中文短句易误伤 / reason length < 5 chars rejected, Chinese short phrases easily false-positive |
| 10 | 🟡 mid | write | problem 长度 < 10 字符被拒，中文短句易误伤 / problem length < 10 chars rejected, Chinese short phrases easily false-positive |
| 15 | 🟡 mid | install-context | PowerShell subprocess 在非 TTY 下不退出，pandax 永远等待 / PowerShell subprocess doesn't exit without TTY, pandax waits forever |
| 19 | 🟡 mid | status | status 报 Locked=N 但不检查当前 ReadOnly 实际状态 / status reports Locked=N but doesn't check actual ReadOnly state |
| 20 | 🟡 mid | ci | ci 报 "empty repo" 但实际有文件 / ci reports "empty repo" but actually has files |
| 21 | 🟡 mid | write / doctor | write 报 git not installed，doctor 报 git OK（检测不一致）/ write says git not installed, doctor says git OK (detection inconsistency) |
| 3 | 🟢 low | global | `--silent` flag 不生效，banner + README 仍显示 / `--silent` flag ineffective, banner + README still shown |
| 4 | 🟢 low | cli.py | README summary 停在 Step 13，与实际 Phase 11 / Step 89+ 脱节 / README summary stuck at Step 13, far behind actual Phase 11 / Step 89+ |
| 13 | 🟢 low | log | `log -n N` 无效（应为 `--recent N`），缺少短选项别名 / `log -n N` ineffective (should be `--recent N`), missing short alias |
| 14 | 🟡 mid | log | log 在 `--lang=en` 时 Reason 标签仍是中文（与 #6 关联）/ log Reason label still Chinese in `--lang=en` (related to #6) |

---

## 详细复现与根因分析 / Detailed Reproduction & Root Cause Analysis

### Bug #12 🔴 critical — write 失败时 mode 恢复不完整（隐藏/系统属性丢失）/ Bug #12 🔴 critical — mode restoration incomplete on write failure (hidden/system attributes lost)

**复现步骤 / Reproduction Steps**：
```bash
# 1. 创建 PandaX项目
# 1. Create PandaX project
pandax init --root D:\test-write

# 2. 锁定文件
# 2. Lock file
pandax lock --root D:\test-write
#   → test.py mode=0o100444, IsReadOnly=True

# 3. 标记文件为 hidden + system（attrib 命令）
# 3. Mark file as hidden + system (attrib command)
attrib +h +s D:\test-write\test.py

# 4. 试图 write（即使 reason/problem/approach 完美）
# 4. Try to write (even with perfect reason/problem/approach)
pandax write --root D:\test-write --file test.py \
    --reason "..." --problem "..." --approach "..." \
    --old '...' --new '...'

# 5. 检查文件属性（应当仍然 ReadOnly）
# 5. Check file attributes (should still be ReadOnly)
dir D:\test-write\test.py
```

**结果（修复前）/ Result (Before Fix)**：
- write 抛 PermissionError（hidden+system 阻止 write_text 写入）/ write throws PermissionError (hidden+system prevents write_text)
- 文件 mode **变成 0o100666，IsReadOnly=False** ❌ / file mode **becomes 0o100666, IsReadOnly=False** ❌
- 锁永久失效，文件可被任何编辑器/进程修改 / lock permanently broken, file can be modified by any editor/process

**结果（修复后）/ Result (After Fix)**：
- write 抛 PermissionError → audit REJECTED
- 文件 mode **恢复 0o100444，IsReadOnly=True** ✅ / file mode **restored to 0o100444, IsReadOnly=True** ✅

**根因 / Root Cause**：`cli.py cmd_write` step 4 写入步骤没有 try/finally 包裹：
`cli.py cmd_write` step 4 write step not wrapped in try/finally:
```python
target.write_text(new_content, encoding="utf-8")  # 抛 PermissionError → 文件 mode 永久 writable
                                                   # throws PermissionError → file mode permanently writable
# 写入失败也不会恢复 mode
# Write failure doesn't restore mode
```

**修复方案 v1**（commit b520357）：try/except/finally + 恢复原始模式 / Fix Plan v1 (commit b520357): try/except/finally + restore original mode
**修复方案 v2**（commit TBD）：新增 --force-write flag + ReadOnly 前置检查 / Fix Plan v2 (commit TBD): add --force-write flag + ReadOnly pre-check

### Bug #12 v2 — write 默认严格，需 --force-write 显式覆盖锁定文件 / Bug #12 v2 — write default strict, requires explicit --force-write to overwrite locked files

**新增风险点 / New Risk Point**：v1 修复只保证"写完后 mode 恢复"，但**没有阻止 write 主动解锁**。如果某个脚本/Agent 调用 `pandax write`，会自动 unlock→write→lock，**绕过用户意图**。
v1 fix only ensures "mode restored after write", but **doesn't prevent write from actively unlocking**. If a script/Agent calls `pandax write`, it auto-unlock→write→lock, **bypassing user intent**.

**改进设计**（第一性原则 + 对抗式审查）/ Improved Design (First Principles + Adversarial Review):
1. **写命令默认严格**：检测目标文件 `os.access(W_OK)=False` → REJECTED / **write default strict**: check target file `os.access(W_OK)=False` → REJECTED
2. **显式 --force-write** 才放行，走完整 unlock-write-lock 流程 / **explicit --force-write** to allow, full unlock-write-lock flow
3. **审计记录 `force_write` 字段**，让审计可追溯 / **audit record `force_write` field**, making audit traceable

**验证 / Verification**：
- `test_write_rejects_readonly_without_force`: 锁定文件不带 --force-write → REJECTED
- `test_write_accepts_readonly_with_force`: 锁定文件带 --force-write → APPROVED + 审计 force_write=true
- `test_write_no_force_for_unlocked_file`: 未锁定文件不需要 --force-write 也能正常 write
- E2E（`D:\pandax-test`）：5/5 检查全过（exit=0, file updated, file RE-LOCKED, force_write=true, commit_hash）

**关键变更**（commit TBD）/ Key Changes (commit TBD):
- `src/pandax/cli.py` line 236-242: argparse `--force-write` flag
- `src/pandax/cli.py` line 638-644: cmd_write step 1.5 ReadOnly 前置检查 / cmd_write step 1.5 ReadOnly pre-check
- `src/pandax/cli.py` line 776: APPROVED audit 记录 `force_write` 字段 / APPROVED audit records `force_write` field
- `src/pandax/i18n.py` line 112/332: 新增 `write_reject_readonly_need_force` 双语言 key / add `write_reject_readonly_need_force` bilingual key
- `tests/test_write.py`: 现有 3 个 write 测试加 `--force-write` + 新增 3 个 v2 测试用例 / existing 3 write tests add `--force-write` + add 3 new v2 tests
- `tests/test_e2e.py` + `tests/test_phase2_e2e.py`: 加 `--force-write` 适配新语义 / add `--force-write` adapting to new semantics

**回归测试 / Regression Test**：194/194 全过（比 v1 多 3 个新用例 / all pass (3 more new cases than v1)

---

### Bug #8 🔴 critical — install-context PS1 通配符阻塞 / Bug #8 🔴 critical — install-context PS1 wildcard blocking

**复现步骤 / Reproduction Steps**：
```powershell
pandax uninstall-context  # 干净状态 / clean state
pandax install-context --force
```

**结果 / Result**：`[1/4] Cleaning old entries...` 显示后**永久挂死**（180s+）/ shown then **permanently hangs** (180s+).

**根因 / Root Cause**：`installer/windows/install_context_menu.ps1` 和 `uninstall_context_menu.ps1` 使用：
`installer/windows/install_context_menu.ps1` and `uninstall_context_menu.ps1` use:
```powershell
Test-Path "HKCU:\Software\Classes\*\shell\PandaX"
```
PS 把 `*` 当通配符，glob 整个 `HKCU:\Software\Classes\*`（上千 ProgID），可能进入死循环或挂死。
PS treats `*` as wildcard, globs entire `HKCU:\Software\Classes\*` (thousands of ProgIDs), may enter infinite loop or hang.

**修复 / Fix**：
```powershell
Test-Path -LiteralPath "HKCU:\Software\Classes\*\shell\PandaX"
Remove-Item -LiteralPath $path -Recurse -Force
New-Item -LiteralPath $path -Force | Out-Null
```
所有 `*` 出现的位置都用 `-LiteralPath` 替代。
All `*` occurrences replaced with `-LiteralPath`.

**影响范围 / Impact Scope**：
- `installer/windows/install_context_menu.ps1`（4 处 / 4 occurrences）
- `installer/windows/uninstall_context_menu.ps1`（5 处 / 5 occurrences）

---

### Bug #7 🔴 critical — install-context 中断残留 / Bug #7 🔴 critical — install-context interrupt residue

**复现 / Reproduction**：Bug #8 触发后 Ctrl+C，注册表残留 / Registry residue after Ctrl+C following Bug #8:
```
HKCU\Software\Classes\*\shell\PandaX
    (Default)  = "PandaX"
    MUIVerb    = "PandaX 审计工具 / Audit Tools"
```
**缺 / Missing**：Icon, SubCommands, Init/Lock/Status/Unlock 子菜单及其 command 子键 / submenus and command subkeys.

**根因 / Root Cause**：每次 `Install-CascadeMenu` 调用**非原子**——先写主菜单值，再写 4 个子菜单，子菜单之间无事务。
Each `Install-CascadeMenu` call is **non-atomic** — writes main menu value first, then 4 submenus, with no transaction between submenus.

**修复 / Fix**：
1. 改 Bug #8 后此 Bug 自然消失（不再中断）/ After fixing Bug #8, this Bug disappears naturally (no more interrupts)
2. 加防御：写注册表前先全部准备好 dict，最后一次性 flush；失败时自动 rollback / Add defense: prepare all dicts before writing registry, finally flush once; auto rollback on failure
3. uninstall 时改用更宽松的清理逻辑（删除整个 `*` key 树而非仅 `*` 单 key）/ uninstall uses more lenient cleanup logic (delete entire `*` key tree, not just `*` single key)

---

### Bug #2 🔴 high — status 只查 .py / Bug #2 🔴 high — status only checks .py

**复现 / Reproduction**：
```bash
pandax status --root D:\pandax-test
# [L1 File Lock] Total .py files: 1
# 但实际有 .py, .md, .json, .env 4 个受保护文件
# but actually has .py, .md, .json, .env 4 protected files
```

**根因 / Root Cause**：`cli.py:950` `py_files = [p for p in root.rglob("*.py")]`，硬编码 `*.py` / hardcoded `*.py`.

**修复 / Fix**：用共享的 `PROTECTED_EXTS` 常量（lock/unlock 已用 19 种扩展名）/ Use shared `PROTECTED_EXTS` constant (lock/unlock already use 19 extensions).

---

### Bug #5 🔴 high — --lang 位置敏感 / Bug #5 🔴 high — --lang position-sensitive

**复现 / Reproduction**：
```bash
pandax --lang=en status --root .   # ✅ 英文 / English
pandax status --root . --lang=en   # ❌ 仍中文 / still Chinese
```

**根因 / Root Cause**：`cli.py` argparse 在 `parse_known_args` 时，全局 `--lang` 在 `subcommand parser` 之后才解析。
`cli.py` argparse in `parse_known_args`, global `--lang` is parsed only after `subcommand parser`.

**修复方案 / Fix Plan**：
1. 手动从 `sys.argv` 提取 `--lang=`，全局设到 `i18n._lang` / Manually extract `--lang=` from `sys.argv`, set globally to `i18n._lang`
2. 或在每个子命令 parser 加 `--lang` 别名 / Or add `--lang` alias in each subcommand parser
3. 或用 `argparse.ParentParser` 模式 / Or use `argparse.ParentParser` mode

---

### Bug #6 + #14 🟡 mid — log 标签和 reason 字符串硬编码 / Bug #6 + #14 🟡 mid — log labels and reason strings hardcoded

**复现 / Reproduction**：
```bash
pandax --lang=en log --recent 3
# 输出仍是：Reason: / Problem: / Approach: / attempted: / "problem 长度 < 10"
# output still: Reason: / Problem: / Approach: / attempted: / "problem 长度 < 10"
```

**根因 / Root Cause**：`cli.py:870-883` 直接 `print(f"\n[{ts}] {status}  id={rid}  file={file_}")` 和 `print(f"  Reason:   {reason}")`——label 和 reason 都未走 `t()`。
`cli.py:870-883` directly prints labels and reasons without `t()`.

**修复 / Fix**：在 i18n 字典加 `log_label_reason`, `log_label_problem`, `log_label_approach`, `log_label_attempted` 等 key，并要求 `cmd_write` 在记录审计时把 reason 也存为 i18n key 而非直接字符串。
Add `log_label_reason`, `log_label_problem`, etc. keys to i18n dict, and require `cmd_write` to store reason as i18n key, not raw string, when recording audit.

---

### Bug #17 🟡 mid — status 不做 i18n / Bug #17 🟡 mid — status doesn't do i18n

**复现 / Reproduction**：
```bash
pandax --lang=en status --root .
# 输出："PandaX 状态仪表盘", "[L1 文件锁]", "总计 .py 文件", etc.
# output: "PandaX 状态仪表盘", "[L1 文件锁]", "总计 .py 文件", etc.
```

**根因 / Root Cause**：`cmd_status` 内字符串全部 hardcoded 中英混合 / All strings in `cmd_status` are hardcoded mixed Chinese-English.

**修复 / Fix**：和 Bug #6 一起处理，给 status 全部走 `t()` / Process together with Bug #6, route all status through `t()`.

---

### Bug #9 + #10 🟡 mid — write 长度限制对中文不友好 / Bug #9 + #10 🟡 mid — write length limit unfriendly to Chinese

**复现 / Reproduction**：
```bash
pandax write --reason "测试写入" ...   # 4 字符 → REJECTED "reason 长度 < 5"
pandax write --problem "原文件太简单" ...   # 9 字符 → REJECTED "problem 长度 < 10"
```

**根因 / Root Cause**：长度检查用 `len(string)`（字节数？字符数？取决于编码）/ Length check uses `len(string)` (bytes? chars? depends on encoding).

**修复 / Fix**：
1. 改成字符数（已经是字符数，但阈值太低）/ Change to char count (already char count, but threshold too low)
2. 阈值改成 `reason >= 3`, `problem >= 5`, `approach >= 5`（更宽松）/ Threshold to `reason >= 3`, `problem >= 5`, `approach >= 5` (more lenient)
3. 提示信息也走 i18n / Hint messages also through i18n

---

### Bug #15 🟡 mid — PowerShell subprocess 不退出 / Bug #15 🟡 mid — PowerShell subprocess doesn't exit

**复现 / Reproduction**：`pandax uninstall-context` 在干净状态下输出 `[OK] Removed 0 registry entries.` 后**180 秒**仍不退出。
`pandax uninstall-context` in clean state outputs `[OK] Removed 0 registry entries.` then **180 seconds** still doesn't exit.

**根因 / Root Cause**：`subprocess.run(cmd, check=False, env=env)` 缺 timeout；powershell 在缺 stdin 时进程可能不主动 exit。
`subprocess.run(cmd, check=False, env=env)` lacks timeout; powershell without stdin may not actively exit.

**修复 / Fix**：
```python
try:
    rc = subprocess.run(cmd, check=False, env=env, timeout=60).returncode
except subprocess.TimeoutExpired:
    print("[WARN] installer script timeout, killed")
    return 124
```
同时给 powershell 加 `-NoProfile -NonInteractive` 参数 / Also add `-NoProfile -NonInteractive` to powershell.

---

### Bug #18 🟡 mid — write 静默清除 ReadOnly / Bug #18 🟡 mid — write silently clears ReadOnly

**复现 / Reproduction**：见 Bug #12 复现，write 成功后 `os.stat(path).st_mode == 0o100666`（被清）/ See Bug #12 reproduction; after write success `os.stat(path).st_mode == 0o100666` (cleared).

**根因 / Root Cause**：Python `open(path, 'w')` 写入时不保留 mode；写完需手动 `os.chmod` / Python `open(path, 'w')` doesn't preserve mode on write; need manual `os.chmod` after write.

**修复 / Fix**：
```python
old_mode = path.stat().st_mode
path.write_text(new_content, encoding='utf-8')
os.chmod(path, old_mode)  # 恢复原 mode / restore original mode
```
或拒绝写入 ReadOnly 文件（推荐，见 Bug #12）/ Or refuse to write ReadOnly files (recommended, see Bug #12).

---

### Bug #19 🟡 mid — status 报 Locked 但实际未锁 / Bug #19 🟡 mid — status reports Locked but actually unlocked

**复现 / Reproduction**：
```bash
pandax lock   # mode=0o100444
pandax write ...   # Bug #18，mode 被清 / Bug #18, mode cleared
pandax status   # 仍报 Locked=1 / still reports Locked=1
```

**根因 / Root Cause**：status 用 `pandax.lock` 的内部 L1 metadata 判断（哪个文件被 lock 过），而非每次 `os.stat()` 实际检查。
status uses internal L1 metadata from `pandax.lock` (which files were locked), not actual `os.stat()` check each time.

**修复 / Fix**：status 改成每次实际 stat ReadOnly 标志，给出真实状态 / status changed to actually stat ReadOnly flag each time, giving real status.

---

### Bug #20 🟡 mid — ci 误报 empty repo / Bug #20 🟡 mid — ci false-reports empty repo

**复现 / Reproduction**：
```bash
pandax ci --root D:\pandax-test
# 输出 "Baseline: none (first commit, no history to compare)"
# "repository is empty (no changes to audit)"
```

**根因 / Root Cause**：D:\pandax-test 不是 git 仓库，ci 命令没有 git fallback 处理未初始化仓库的情况。
D:\pandax-test is not a git repo; ci command lacks git fallback for uninitialized repo.

**修复 / Fix**：
1. ci 自动检测 `git status` 是否可用 / ci auto-detects if `git status` is available
2. 不可用时用 `binary_snapshots.json` 作为 baseline 替代 / If unavailable, use `binary_snapshots.json` as baseline substitute
3. 或更明确告诉用户 "this dir is not a git repo" / Or more clearly tell user "this dir is not a git repo"

---

### Bug #21 🟡 mid — write/doctor git 检测不一致 / Bug #21 🟡 mid — write/doctor git detection inconsistent

**复现 / Reproduction**：
```bash
pandax doctor.py   # 12/12 OK, git OK
pandax write ...   # [WARN] git not installed
```

**根因 / Root Cause**：两处 git 检测代码路径不同 / Two git detection code paths differ.

**修复 / Fix**：统一 git 检测函数 `git_available() -> bool` 在 `core/utils.py`，doctor 和 write 都用 / Unify git detection function `git_available() -> bool` in `core/utils.py`, both doctor and write use it.

---

### Bug #3 🟢 low — --silent 无效 / Bug #3 🟢 low — --silent ineffective

**复现 / Reproduction**：
```bash
pandax --silent status --root .
# 仍然显示 ASCII banner + README summary
# still shows ASCII banner + README summary
```

**根因 / Root Cause**：`_print_banner()` 不检查 `--silent` 标志 / `_print_banner()` doesn't check `--silent` flag.

**修复 / Fix**：在 `main()` 开头 `_print_banner()` 前判断 `args.silent`，是则 return / At `main()` start, check `args.silent` before `_print_banner()`, return if so.

---

### Bug #4 🟢 low — README summary 过时 / Bug #4 🟢 low — README summary outdated

**复现 / Reproduction**：每次 `pandax` 启动都打印 README summary，但只到 Step 13 / Phase 2，实际已到 Phase 11 / Step 89+。
Each `pandax` startup prints README summary but only up to Step 13 / Phase 2; actually at Phase 11 / Step 89+.

**根因 / Root Cause**：README summary 是 `__main__.py` 启动时打印的硬编码文本 / README summary is hardcoded text printed at `__main__.py` startup.

**修复 / Fix**：要么删掉这个 summary（它对回放项目历史有帮助但已经过时），要么从 `docs/ROADMAP.md` 动态加载 / Either delete this summary (helpful for replay history but outdated) or dynamically load from `docs/ROADMAP.md`.

---

### Bug #13 🟢 low — log -n 无效 / Bug #13 🟢 low — log -n ineffective

**复现 / Reproduction**：
```bash
pandax log -n 3   # 显示全部 11 条记录 / shows all 11 records
```

**根因 / Root Cause**：argparse 中没有 `-n` 别名，只有 `--recent N` / argparse has no `-n` alias, only `--recent N`.

**修复 / Fix**：argparse 加 `add_argument("-n", "--recent", type=int, default=20)` / argparse add `add_argument("-n", "--recent", type=int, default=20)`.

---

## 误判与撤销 / Misjudgments & Revocations

### ~~Bug #1~~ 撤销 — lock 命令实际有效 / ~~Bug #1~~ Revoked — lock command actually works

之前怀疑 `pandax lock` 在 Windows 上失效，实际测试：
Previously suspected `pandax lock` ineffective on Windows; actual testing:
- `pandax lock` 把 test.py/md/env/json 都从 0o100666 改成 0o100444 + IsReadOnly=True ✅ / `pandax lock` changes test.py/md/env/json from 0o100666 to 0o100444 + IsReadOnly=True ✅
- `pandax unlock` 全部还原 ✅ / `pandax unlock` restores all ✅
- 是 init 时已经自动 lock 了所有受保护文件，**lock 命令本身工作正常** / init already auto-locked all protected files; **lock command itself works fine**

真正的问题是 **Bug #12（write 失败时 mode 恢复不完整）** / The real issue is **Bug #12 (mode restoration incomplete on write failure)**.

### ~~Bug #18~~ 撤销 — write 静默清除 ReadOnly（误判）/ ~~Bug #18~~ Revoked — write silently clears ReadOnly (misjudgment)

最初报告说 write 改完文件后 IsReadOnly 被清除。深入测试发现：
Initially reported write clears IsReadOnly after modifying file. Deeper testing revealed:
- write 设计**就是**先 chmod writable → 写 → chmod readonly / write **is designed** to chmod writable → write → chmod readonly
- 写成功路径下，mode 恢复 0o100444 + IsReadOnly=True ✅ / In write success path, mode restored to 0o100444 + IsReadOnly=True ✅
- 误判来源：第一次测试只看 status "Locked=1" 就下结论，没看真实 mode / Misjudgment source: first test only checked status "Locked=1" without looking at actual mode

**真实的 #18 不存在**——实际是 #12（写入失败路径没恢复）/ **Real #18 doesn't exist** — it's actually #12 (write failure path not restored).

---

## 修复优先级建议 / Fix Priority Recommendation

**P0（必修，发布前）/ P0 (Required, before release)**：
- #12 write 绕过文件锁 — 核心安全漏洞 / write bypasses file lock — core security vulnerability
- #8 install-context 通配符阻塞 — 用户首次安装即卡死 / install-context wildcard block — first install hangs
- #7 install-context 中断残留 — 半成品注册表污染系统 / install-context interrupt residue — half-done registry pollutes system

**P1（应该修，下个版本）/ P1 (Should fix, next version)**：
- #2 status 只看 .py — 审计覆盖不全 / status only checks .py — audit coverage incomplete
- #5 --lang 位置敏感 — 用户体验 / --lang position-sensitive — UX
- #15 PowerShell subprocess 不退出 — CI/脚本调用困难 / PowerShell subprocess doesn't exit — CI/scripting hard
- #19 status 报 Locked 但实际未锁 — 安全假象 / status reports Locked but actually unlocked — security illusion

**P2（可以延后）/ P2 (Can defer)**：
- #6 / #14 / #17 i18n 完整性（status, log labels）
- #9 / #10 write 长度阈值对中文不友好 / write length threshold unfriendly to Chinese
- #18 write 静默清除 ReadOnly / write silently clears ReadOnly
- #20 ci 误报 empty repo / ci false-reports empty repo
- #21 doctor/write git 检测不一致 / doctor/write git detection inconsistent

**P3（nice-to-have）/ P3 (Nice-to-have)**：
- #3 --silent 无效 / --silent ineffective
- #4 README summary 过时 / README summary outdated
- #13 log -n 别名缺失 / log -n alias missing

---

## 修复方案快速参考 / Quick Fix Reference

### Bug #8 修复（最优先，影响首次安装）/ Bug #8 Fix (Top Priority, Affects First Install)

**install_context_menu.ps1** 4 处替换 / 4 replacements:
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

**uninstall_context_menu.ps1** 5 处替换同上 / 5 same replacements.

### Bug #12 修复（核心安全）/ Bug #12 Fix (Core Security)

```python
# core/write.py 或 cli.py cmd_write
def cmd_write(args):
    target = Path(args.root) / args.file
    # Bug #12 fix: 检查 ReadOnly
    # Bug #12 fix: check ReadOnly
    if os.name == 'nt':
        import stat
        mode = target.stat().st_mode
        if not (mode & stat.S_IWRITE):
            return {"status": "REJECTED", "reason": t("write_rejected_readonly", file=str(target))}
    # 原有流程 / original flow ...
```

### Bug #15 修复（subprocess timeout）/ Bug #15 Fix (subprocess timeout)

```python
# cli.py _run_installer
try:
    rc = subprocess.run(cmd, check=False, env=env, timeout=60).returncode
    return rc
except subprocess.TimeoutExpired:
    print(t("warn_install_timeout"))
    return 124
```

并给 powershell 加 `-NoProfile -NonInteractive` / And add `-NoProfile -NonInteractive` to powershell:
```python
interpreter = handler["interpreter"] + ["-NoProfile", "-NonInteractive"]
```

---

## 附：所有 bug 一句话总结 / Appendix: All Bug One-Line Summary

1. ~~lock 在 Windows 失效~~ **撤销**（实际有效）/ ~~lock fails on Windows~~ **Revoked** (actually works)
2. status 只查 .py / status only checks .py
3. --silent 不生效 / --silent ineffective
4. README summary 过时（Step 13 vs Step 89+）/ README summary outdated
5. --lang 位置敏感 / --lang position-sensitive
6. log 标签硬编码 / log labels hardcoded
7. install-context 中断残留 / install-context interrupt residue
8. install-context 通配符阻塞 / install-context wildcard blocking
9. reason 长度限制 / reason length limit
10. problem 长度限制 / problem length limit
11. ~~--old 找不到~~ **撤销**（PowerShell 引号问题，非 pandax bug）/ ~~--old not found~~ **Revoked** (PowerShell quote issue, not pandax bug)
12. **write 失败时 mode 不恢复（最严重，已修复）** / **write mode not restored on failure (most serious, fixed)**
13. log -n 无效 / log -n ineffective
14. log 在 lang=en 时仍中文（与 #6 关联）/ log still Chinese in lang=en (related to #6)
15. PowerShell subprocess 不退出 / PowerShell subprocess doesn't exit
16. ~~status 命令卡死~~ **撤销**（之前测试环境残留进程导致，非 status 本身问题）/ ~~status command hangs~~ **Revoked** (test env residual process, not status itself)
17. status 不做 i18n / status doesn't do i18n
18. ~~write 静默清除 ReadOnly~~ **撤销**（写入成功路径实际恢复 mode）/ ~~write silently clears ReadOnly~~ **Revoked** (write success path actually restores mode)
19. status 报 Locked 但实际未锁 / status reports Locked but actually unlocked
20. ci 误报 empty repo / ci false-reports empty repo
21. doctor/write git 检测不一致 / doctor/write git detection inconsistent

## 修复记录（v0.7.0 → v0.7.1）/ Fix Log (v0.7.0 → v0.7.1)

### 已修复 / Fixed
- **#8** + **#7**（install-context 通配符 + 中断残留）/ **#8** + **#7** (install-context wildcard + interrupt residue):
  - `installer/windows/install_context_menu.ps1`：改用 .NET `[Microsoft.Win32.Registry]` API 替代 PS cmdlets / Switched to .NET `[Microsoft.Win32.Registry]` API replacing PS cmdlets
  - `installer/windows/uninstall_context_menu.ps1`：同样改用 .NET API / Same .NET API
  - 完整注册表写入验证（37 行：Default + MUIVerb + Icon + SubCommands + 4 个子菜单带 command）/ Full registry write verification (37 lines)
- **#12**（write 失败时 mode 恢复）/ **#12** (mode restoration on write failure):
  - `src/pandax/cli.py` 重写 `cmd_write` step 4 为 try/except/finally / Rewrote `cmd_write` step 4 to try/except/finally
  - 新增 `_OldNotFoundError` 业务异常类 / Added `_OldNotFoundError` business exception class
  - finally 块始终 `os.chmod(target, mode)` 恢复**原始 mode** / finally block always `os.chmod(target, mode)` restores **original mode**

### 验证 / Verification
- `tests/test_write.py` 8/8 通过 / 8/8 pass
- 完整套件 **191/191 通过**，零回归 / Full suite **191/191 pass**, zero regression
- 对抗测试 `test_write_lock_robustness.py` ADVERSARIAL 1+2 全过 / Adversarial test `test_write_lock_robustness.py` ADVERSARIAL 1+2 all pass
