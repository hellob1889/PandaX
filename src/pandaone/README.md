# Pandaone AI Agent 实施日志（Living Doc）/ Pandaone Implementation Log (Living Doc)

> **核心机制**：CLI 每次运行都会读取本文件，并在启动时显示当前阶段 / 已完成步骤 / 待办。
> 所以本文件不是"写完就不管"的文档，而是 **CLI 自身依赖的运行时数据**。
> **Core mechanism**: CLI reads this file on every run and displays the current phase / completed steps / TODO at startup.
> So this file is not a "write-and-forget" document, but **runtime data that CLI itself depends on**.

***

## 项目目标 / Project Goal

实现 `Pandaone` —— 一个 OS 级物理强制的 AI Agent 代码审计门禁系统。
详见 `Pandaone_项目文档.html`（v2.0 设计文档）。
Implement `Pandaone` — an OS-level physically-enforced AI Agent code audit gateway system.
See `Pandaone_项目文档.html` (v2.0 design doc) for details.

***

## 当前阶段 / Current Phase

**v0.7.0 — 生产就绪（25 个 bug 全修，243 测试通过）**
**v0.7.0 — Production ready (25 bugs all fixed, 243 tests pass)**

### P0 安全 (5) / P0 Security (5)
- [x] **#8 + #7** — install-context 通配符阻塞（PS5.1 registry provider 改用 .NET API）
  **#8 + #7** — install-context wildcard block (PS5.1 registry provider switched to .NET API)
- [x] **#12 v1** — write 失败时 mode 恢复（try/finally + 原始 mode 恢复）
  **#12 v1** — write mode restoration on failure (try/finally + restore original mode)
- [x] **#12 v2** — write 默认拒绝 ReadOnly 锁定文件（`--force-write` 显式 opt-in）
  **#12 v2** — write default rejects ReadOnly-locked file (`--force-write` explicit opt-in)
- [x] **#22** — pre-commit hook CRLF→LF（bash 在 *nix 上不支持 CRLF，P0 安全）
  **#22** — pre-commit hook CRLF→LF (bash on *nix doesn't support CRLF, P0 security)
- [x] **#23** — watchdog dedupe（1 次写入只产 1 条审计，2 秒去重窗口）
  **#23** — watchdog dedupe (1 write produces 1 audit entry, 2-second dedupe window)

### P1 (4)
- [x] **#2** — status 用 `_iter_protected_files` 共享 helper（19 种扩展名全覆盖）
  **#2** — status uses shared helper `_iter_protected_files` (full coverage of 19 extensions)
- [x] **#5** — `--lang` 全局参数支持任意位置（main() 预扫描 argv）
  **#5** — `--lang` global flag accepts any position (main() pre-scans argv)
- [x] **#15** — PowerShell subprocess `-NoProfile -NonInteractive` + timeout=60
- [x] **#29** — pandaone init merge-preserve（不再覆盖用户自定义 config.json）
  **#29** — pandaone init merge-preserve (no longer overwrites user's custom config.json)

### P2 (5)
- [x] **#21** — doctor/write git 检测一致性（共享 `_resolve_git_exe()`）
  **#21** — doctor/write git detection consistency (shared `_resolve_git_exe()`)
- [x] **#6** — log 标签 i18n 完整（REJECTED/UNAUTHORIZED 走 t()）
  **#6** — log tag i18n complete (REJECTED/UNAUTHORIZED go through t())
- [x] **#20** — ci 区分空仓库 vs 首次 commit（智能 baseline fallback）
  **#20** — ci distinguishes empty repo vs first commit (intelligent baseline fallback)
- [x] **#9 / #10** — 智能长度阈值（`_info_length` unicode 宽度，1 中文字 = 2 宽度）
  **#9 / #10** — smart length threshold (`_info_length` unicode width, 1 CJK char = 2 width)

### P3 (4)
- [x] **#13** — log `-n` 简写作为 `--recent` 别名
  **#13** — log `-n` short form as `--recent` alias
- [x] **#4** — README summary 显示最新 Phase 而非旧 Step
  **#4** — README summary shows latest Phase instead of old Step
- [x] **#26** — export html/md/text 报告标签本地化
  **#26** — export html/md/text report label localization
- [x] **#39** — cmd_write 4 处硬编码中文改为 i18n
  **#39** — cmd_write 4 hardcoded Chinese strings migrated to i18n

### UX + 横切 i18n (3) / UX + Cross-cutting i18n (3)
- [x] **#14** — log 在 lang=en 时 Reason 字段本地化
  **#14** — log Reason field localized when lang=en
- [x] **#17** — status i18n 完整性
  **#17** — status i18n completeness
- [x] **#48** — `--trust-default` 自动接受新指纹（pip install --upgrade 场景）
  **#48** — `--trust-default` auto-accepts new fingerprint (pip install --upgrade scenario)

### UX (2)
- [x] **#25** — 独立 `pandaone export` 子命令（语义清晰，不再借用 log）
  **#25** — independent `pandaone export` subcommand (cleaner semantics, no longer borrowing log)
- [x] **#28** — `pandaone lock` 一键启用（未 init 时自动 init，首次使用友好）
  **#28** — `pandaone lock` one-click enable (auto-init if not initialized, friendly first-use)

### Phase 进度 / Phase Progress

**Phase 1：CLI MVP（P0）** ✅ 全部完成（Step 0–8）
**Phase 1: CLI MVP (P0)** ✅ All done (Steps 0–8)
**Phase 2：监控加固（P1）** ✅ 全部完成（Step 9–13）
**Phase 2: Monitoring Hardening (P1)** ✅ All done (Steps 9–13)
**Phase 3：标准 Python 包分发（P0）** ✅ 全部完成（Step 14–18）
**Phase 3: Standard Python Package Distribution (P0)** ✅ All done (Steps 14–18)
**Phase 4：跨平台右键菜单（P1）** ✅ 全部完成（Windows/macOS/Linux + i18n）
**Phase 4: Cross-Platform Context Menu (P1)** ✅ All done (Windows/macOS/Linux + i18n)
**Phase 5：环境诊断（P1）** ✅ 全部完成（doctor.py + 13 类 auto-fix + PATH 持久化）
**Phase 5: Environment Diagnostics (P1)** ✅ All done (doctor.py + 13 auto-fix + PATH persistence)

**当前测试数 / Current Test Count**：264 passed（覆盖 i18n / write / status / lock / ci / watchdog / export / init / e2e / version-source-of-truth）
264 passed (covers i18n / write / status / lock / ci / watchdog / export / init / e2e / version-source-of-truth)

**Phase 6：MCP Server / TRAE Skill（P2）**：下一步
**Phase 6: MCP Server / TRAE Skill (P2)**: Next step

***

## 实施步骤记录 / Implementation Steps Log

### Step 0 — 创建 README（本次）/ Create README (This Time)

**目标 / Goal**：建立实施日志结构，使 CLI 启动可读取。
Establish implementation log structure so CLI startup can read it.
**决策 / Decision**：

- README 顶部固定段落（`## 当前阶段`、`## 实施步骤记录`）让 CLI 可以结构化解析
  README top fixed sections (`## 当前阶段`, `## 实施步骤记录`) enable structured CLI parsing

- 每个 Step 一个三级标题，含"目标 / 决策 / TDD过程 / 产出"
  Each Step is a level-3 heading, with "Goal / Decision / TDD Process / Output"

- 完成的 Step 标记 `[x]`，进行中 `[~]`，待办 `[ ]`
  Completed Steps marked `[x]`, in-progress `[~]`, pending `[ ]`

**产出 / Output**：

- `README.md`

**下一步 / Next Step**：建立 test_project 测试项目，写第一个 RED 测试。
Set up test_project, write first RED test.

***

### Step 1 — 第一个 RED 测试（CLI 必读 README）/ Step 1 — First RED Test (CLI Must Read README)

**目标 / Goal**：用 TDD 锁定 "CLI 启动必读 README" 的机制。
Use TDD to lock in the "CLI startup must read README" mechanism.

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_readme_loaded.py` 共 4 个测试
  RED: write `tests/test_readme_loaded.py` with 4 tests

  - `test_pandaone_file_exists`：pandaone.py 必须存在
    `test_pandaone_file_exists`: pandaone.py must exist

  - `test_readme_file_exists`：README.md 必须存在
    `test_readme_file_exists`: README.md must exist

  - `test_cli_loads_readme_on_startup`：CLI 无参数启动 stdout 必须包含 "Phase 1"
    `test_cli_loads_readme_on_startup`: CLI startup with no args stdout must contain "Phase 1"

  - `test_cli_shows_completed_steps`：CLI 启动 stdout 必须包含 "\[x]" 标记
    `test_cli_shows_completed_steps`: CLI startup stdout must contain "\[x]" markers

- 验证 RED：3 failed, 1 passed（pandaone.py 不存在，失败原因正确）
  Verify RED: 3 failed, 1 passed (pandaone.py doesn't exist, failure reason correct)

- 决策：用 pytest（需 `pip install pytest`）
  Decision: use pytest (requires `pip install pytest`)

**产出 / Output**：

- `tests/__init__.py`

- `tests/test_readme_loaded.py`

- `test_project/main.py`（测试用 .py 文件 / test .py file）

- `test_project/utils.py`

***

### Step 2 — 实现 pandaone.py 框架 + 启动读 README / Step 2 — Implement pandaone.py Framework + Startup Read README

**目标 / Goal**：让 Step 1 的 RED 测试通过。
Pass Step 1's RED tests.

**决策 / Decision**：

- argparse 主解析器 + subparsers 占位所有子命令（init/lock/unlock/write/log/status/watch）
  argparse main parser + subparsers placeholder for all subcommands

- `load_readme_summary()` 函数解析 README：
  `load_readme_summary()` parses README:

  - 提取 "## 当前阶段" 段落中的 `**Phase X` 标题行
    Extract `**Phase X` heading lines from "## 当前阶段" section

  - 提取同段落中的 `- [x]` 行作为"已完成步骤"
    Extract `- [x]` lines from same section as "completed steps"

- 启动流程：先 print README 摘要 → 再处理 CLI 参数
  Startup flow: print README summary first → then handle CLI args

**TDD 过程 / TDD Process**：

- GREEN：写 `pandaone.py`，所有 4 个测试通过
  GREEN: write `pandaone.py`, all 4 tests pass

- REFACTOR：改进解析逻辑，让"已完成步骤"清晰列出 Step 标题
  REFACTOR: improve parsing logic, list Step headings clearly under "completed steps"

**第一性原理 / First Principles**：

- 文档是"代码的外部大脑"，CLI 自读取等于让工具永远同步设计
  Documentation is the code's "external brain"; CLI self-reading keeps the tool always in sync with design

- README 与代码审计逻辑解耦：篡改 README 只能误导显示，不影响审计行为
  README decoupled from audit logic: tampering README only misleads display, doesn't affect audit behavior

**对抗式审查 / Adversarial Review**：

- 攻击：篡改 README 误导 CLI 显示 / Attack: tamper README to mislead CLI display

- 缓解：README 不参与审计逻辑，篡改仅影响信息展示
  Mitigation: README not part of audit logic; tampering only affects info display

- 残余风险：低 / Residual risk: low

**产出 / Output**：

- `pandaone.py`（v0.0.1，含 argparse 框架 + README 摘要 / with argparse framework + README summary）

***

### Step 3 — 实现 init 子命令 / Step 3 — Implement init Subcommand

**目标 / Goal**：让 `pandaone init --root <path>` 在指定目录创建 `.pandaone/` 基础设施。
Make `pandaone init --root <path>` create `.pandaone/` infrastructure in the specified directory.

**决策 / Decision**：

- 使用 `Path.mkdir(parents=True, exist_ok=True)` 实现幂等
  Use `Path.mkdir(parents=True, exist_ok=True)` for idempotency

- config.json 字段严格对齐设计文档（version / project_root / protected_extensions / exclude_patterns / git_enabled / watchdog_enabled / min_*_length）
  config.json fields strictly align with design doc

- pandaone.jsonl 用 `Path.touch()` 创建空文件（首次存在即可）
  pandaone.jsonl created empty with `Path.touch()` (just needs to exist initially)

- `--root` 默认 "." 即当前目录
  `--root` defaults to "." (current directory)

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_init.py` 5 个测试
  RED: write `tests/test_init.py` 5 tests

  - 创建 .pandaone/ 目录 / Create .pandaone/ directory

  - 创建合法 config.json（version / project_root / protected_extensions）/ Create valid config.json

  - 创建 pandaone.jsonl / Create pandaone.jsonl

  - 幂等（二次 init 不报错）/ Idempotent (second init doesn't error)

  - --root 参数生效 / --root parameter takes effect

- 验证 RED：5 failed（init 不支持 --root）/ Verify RED: 5 failed (init doesn't support --root)

- GREEN：实现 cmd_init / GREEN: implement cmd_init

- 验证 GREEN：5 passed / Verify GREEN: 5 passed

- 手测：`pandaone init --root test_project` 成功创建 / Manual test: `pandaone init --root test_project` creates successfully

**第一性原理 / First Principles**：

- init 是审计系统的"开机仪式"，三个文件（config/audit/dir）必须同时存在
  init is the audit system's "boot ceremony"; three files (config/audit/dir) must all exist

- 幂等是工程化的体现，避免 agent 重复 init 时报错
  Idempotency is engineering rigor; prevents agent from erroring on repeated init

**对抗式审查 / Adversarial Review**：

- 攻击：agent 在错误的目录 init，污染无关项目 / Attack: agent inits in wrong directory, pollutes unrelated projects

- 缓解：--root 强制显式路径；init 不递归扫描，只在指定目录操作
  Mitigation: --root forces explicit path; init doesn't recursive scan, only operates on specified dir

- 残余风险：低 / Residual risk: low

**产出 / Output**：

- `pandaone.py`（新增 init 子命令 + --root 参数 / added init subcommand + --root param）

***

### Step 4 — 实现 lock / unlock 子命令 / Step 4 — Implement lock / unlock Subcommands

**目标 / Goal**：让 `pandaone lock / unlock --root <path>` 切换项目 .py 文件的只读状态。
Make `pandaone lock / unlock --root <path>` toggle readonly state of project .py files.

**决策 / Decision**：

- 跨平台：使用 Python `os.chmod` + `stat.S_IWUSR/S_IWGRP/S_IWOTH` 位掩码
  Cross-platform: use Python `os.chmod` + `stat.S_IWUSR/S_IWGRP/S_IWOTH` bitmask

- Windows 上 `chmod ~S_IWUSR` 等价于 `attrib +r`（设置只读属性）
  On Windows, `chmod ~S_IWUSR` is equivalent to `attrib +r` (set readonly attribute)

- Linux/Mac 上等价于 `chmod 444` / On Linux/Mac, equivalent to `chmod 444`

- 共享函数 `_apply_readonly(root, readonly)` 给两个命令复用
  Shared function `_apply_readonly(root, readonly)` reused by both commands

- 排除规则从 config.json 读取（`exclude_patterns`）/ Exclude rules read from config.json

- 未 init 的目录 lock → 返回 rc=1 + 错误信息（不崩溃）
  Uninitialized dir lock → return rc=1 + error message (no crash)

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_lock.py` 5 个测试 / RED: write `tests/test_lock.py` 5 tests

  - lock 后 main.py 写入应失败（PermissionError）/ After lock, main.py write should fail (PermissionError)

  - unlock 后可写 / After unlock, writable

  - lock 不锁 _tmp_*.py（排除规则）/ lock doesn't lock _tmp_*.py (exclude rules)

  - lock 输出包含数量 / lock output includes count

  - 未 init 的目录 lock 优雅失败 / Uninitialized dir lock fails gracefully

- 验证 RED：3 failed（lock 无 --root）/ Verify RED: 3 failed (lock lacks --root)

- GREEN：实现 cmd_lock / cmd_unlock / _apply_readonly / GREEN: implement cmd_lock / cmd_unlock / _apply_readonly

- 验证 GREEN：5 passed / Verify GREEN: 5 passed

**第一性原理 / First Principles**：

- L1 文件锁是 OS 级物理屏障，`chmod` 是最可靠的跨平台方法
  L1 file lock is OS-level physical barrier; `chmod` is the most reliable cross-platform method

- 排除规则防止误锁临时文件（如 _tmp_*.py、__pycache__）/ Exclude rules prevent accidentally locking temp files

**对抗式审查 / Adversarial Review**：

- 攻击：agent 用 shell `attrib -r` 解锁后写入 / Attack: agent uses shell `attrib -r` to unlock then write

- 缓解：L2 watchdog 监控后续步骤会捕获并回滚（Phase 2）/ Mitigation: L2 watchdog monitors subsequent steps, catches and rolls back (Phase 2)

- 残余风险：watchdog 未运行时无第二道防线 / Residual risk: no second line of defense when watchdog is not running

**产出 / Output**：

- `pandaone.py`（新增 lock / unlock 子命令 + _apply_readonly 共享函数 / added lock/unlock subcommands + _apply_readonly shared function）

***

### Step 5 — 实现 write 子命令（核心）/ Step 5 — Implement write Subcommand (Core)

**目标 / Goal**：让 `pandaone write --file X --reason Y --problem Z --approach W` 完成完整审计写入流程。
Complete full audit write workflow via `pandaone write --file X --reason Y --problem Z --approach W`.

**决策 / Decision**：

- 完整 8 步流程：水质检测 → 设令牌 → 解锁 → 写入 → 锁回 → 清令牌 → git commit → 审计记录
  Complete 8-step flow: quality check → set token → unlock → write → relock → clear token → git commit → audit log

- 拒绝路径也要写审计记录（含 `attempted_*` 字段）/ Reject path also writes audit (with `attempted_*` fields)

- 字符串替换模式（`--old` / `--new`）和整文件模式（`--content`）/ String replace mode and full-file mode

- `--old` 不在文件中 → 拒绝并回滚 / `--old` not in file → reject and rollback

- git 不可用时 → 不阻塞，审计记录照写，输出 WARN / git unavailable → don't block, audit written anyway, output WARN

- 审计 ID 用 `uuid.uuid4().hex[:8]` / Audit ID uses `uuid.uuid4().hex[:8]`

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_write.py` 8 个测试 / RED: write `tests/test_write.py` 8 tests

  - 4 个水质检测：reason 空 / problem 空 / reason 太短 / 拒绝记录
    4 quality checks: reason empty / problem empty / reason too short / reject record

  - 4 个通过路径：完整元数据 / 整文件模式 / git commit 增加 / 非 .py 拒绝
    4 pass paths: full metadata / full-file mode / git commit increment / non-.py rejected

- 验证 RED：6 failed（write 不支持 --root）+ 2 假阳性（argparse 错误也 rc != 0）
  Verify RED: 6 failed (write doesn't support --root) + 2 false positives (argparse error also rc != 0)

- GREEN：实现 cmd_write 全 8 步流程 / GREEN: implement cmd_write full 8-step flow

- 验证 GREEN：8 passed / Verify GREEN: 8 passed

- 修复一个测试数据问题（approach 长度 < 10）/ Fix a test data issue (approach length < 10)

**第一性原理 / First Principles**：

- 内联审计（写入前）优于事后审计，错误在源头拦截
  Inline audit (pre-write) beats post-audit; errors caught at source

- 拒绝也是数据：attempted_* 字段让"失败的尝试"也成为留痕
  Rejection is data: attempted_* fields make "failed attempts" also traceable

- 锁 + 令牌 + 写 + 锁 + 清令牌 是一个原子事务
  Lock + token + write + lock + clear token is an atomic transaction

**对抗式审查 / Adversarial Review**：

- 攻击：agent 在 write 执行到一半时 kill 进程，留下 .audit_token
  Attack: agent kills write mid-execution, leaves .audit_token behind

  - 缓解：watchdog 监控 .audit_token 的年龄，过期则告警（Phase 2）/ Mitigation: watchdog monitors .audit_token age, alerts on expiry (Phase 2)

- 攻击：用户提供假 reason 绕过审计 / Attack: user provides fake reason to bypass audit

  - 缓解：审计价值在留痕不在判断真假，假 reason 也是证据 / Mitigation: audit value is in record-keeping, not judgment; fake reason is still evidence

- 攻击：手动 git commit --amend 修改历史 / Attack: manual `git commit --amend` to modify history

  - 缓解：commit hash 已记录到审计日志，可对照 / Mitigation: commit hash already recorded in audit log for comparison

**产出 / Output**：

- `pandaone.py`（新增 write 子命令，含完整 8 步流程 / added write subcommand with complete 8-step flow）

***

### Step 5b — 实现 install-git 子命令（用户需求追加）/ Step 5b — Implement install-git Subcommand (User-Requested Addition)

**目标 / Goal**：让 CLI 能探测 git 是否可用，缺失时自动下载 portable 版本。
CLI probes git availability; auto-downloads portable version when missing.

**决策 / Decision**：

- 三层探测策略 / Three-tier probe strategy:

  1. `shutil.which("git")`（PATH 中 / in PATH）
  2. 常见路径列表（D:\软件\Git\cmd、C:\Program Files\Git\cmd 等 / common path list）
  3. 未找到 → 提示 + 可选自动下载 / Not found → prompt + optional auto-download

- `--probe-only`：只探测不下载（默认）/ Probe only, don't download (default)

- `--auto-download`：自动下载 PortableGit zip（约 50MB）到 `<pandaone_dir>/git/` / Auto-download to <pandaone_dir>/git/

- 下载源：GitHub releases 的 portable zip 版（免安装，免管理员权限）/ Source: GitHub releases portable zip

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_install_git.py` 4 个测试 / RED: write `tests/test_install_git.py` 4 tests

  - 子命令存在 / Subcommand exists

  - 探测找到 git 时输出路径 / Probe finds git, outputs path

  - 探测输出有意义内容 / Probe output has meaningful content

  - git 不在 PATH 时优雅处理 / git not in PATH, handled gracefully

- 验证 RED：4 failed / Verify RED: 4 failed

- GREEN：实现 cmd_install_git + _download_portable_git / GREEN: implement cmd_install_git + _download_portable_git

- 验证 GREEN：4 passed（修复 1 个测试预期 — 实际有常见路径 git）/ Verify GREEN: 4 passed (fix 1 test expectation — actual common-path git)

**第一性原理 / First Principles**：

- 用户的开发机 git 装在非标准路径很常见（如 D:\软件\Git\）/ User's dev machine often has git in non-standard path

- CLI 应智能探测而不是假设 PATH / CLI should smart-probe instead of assuming PATH

- 自动下载只作为兜底，给用户选择权 / Auto-download as fallback, give user choice

**对抗式审查 / Adversarial Review**：

- 攻击：恶意网络环境下载到恶意 git / Attack: malicious network downloads malicious git

  - 缓解：使用官方 GitHub releases HTTPS，文件可校验 / Mitigation: official GitHub releases HTTPS, files verifiable

- 攻击：用户没网，--auto-download 卡死 / Attack: user offline, --auto-download hangs

  - 缓解：默认不下载，给出手动安装选项 / Mitigation: don't download by default, offer manual install option

**产出 / Output**：

- `pandaone.py`（新增 install-git 子命令 / added install-git subcommand）

- `tests/conftest.py`（自动探测 git 并加入 PATH / auto-probe git and add to PATH）

***

### Step 6 — 实现 log 子命令 / Step 6 — Implement log Subcommand

**目标 / Goal**：让 `pandaone log` 支持查询、过滤、导出审计记录。
`pandaone log` supports query, filter, export audit records.

**决策 / Decision**：

- 过滤链式：`--file` / `--session` / `--rejected` / `--unauthorized` / `--recent N`
  Chained filters

- 文本格式：表格化输出，每条记录含核心字段 / Text format: tabular output, each record has core fields

- 导出：`--export PATH` 生成 HTML（暗色主题对齐设计文档）/ Export: generate HTML

- 未 init 目录 → 优雅报错（rc=1）/ Uninitialized dir → graceful error (rc=1)

- APPROVED 显示 reason/problem/approach/commit / APPROVED shows reason/problem/approach/commit

- REJECTED 显示 rejection_reason + attempted_* / REJECTED shows rejection_reason + attempted_*

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_log.py` 6 个测试 / RED: write `tests/test_log.py` 6 tests

  - --help 含 --recent / --help contains --recent

  - 默认显示所有（<=20）/ Default shows all (<=20)

  - --recent N 只显示最近 N / --recent N shows only recent N

  - --file X 过滤 / --file X filter

  - --rejected 过滤 / --rejected filter

  - 未 init 优雅报错 / Uninit graceful error

- 验证 RED：6 failed / Verify RED: 6 failed

- GREEN：实现 cmd_log + _print_log + _export_html / GREEN: implement cmd_log + _print_log + _export_html

- 验证 GREEN：6 passed / Verify GREEN: 6 passed

- 端到端手测：write → log 显示 APPROVED + REJECTED 双记录 / E2E: write → log shows APPROVED + REJECTED

**第一性原理 / First Principles**：

- log 是审计的"读取端"，必须和 write 形成闭环 / log is audit's "read side"; must form closed loop with write

- 拒绝留痕是审计系统诚实性的体现 / Rejection records reflect audit system honesty

- 过滤是把大量记录浓缩为有效信号的工具 / Filtering condenses massive records into actionable signal

**对抗式审查 / Adversarial Review**：

- 攻击：agent 篡改 pandaone.jsonl / Attack: agent tampers pandaone.jsonl

- 缓解：将来加 git commit 到 jsonl 文件本身（git 本身不可篡改）/ Mitigation: future add git commit on jsonl file itself

- 攻击：日志无限增长 / Attack: log grows infinitely

- 缓解：当前仅追加不限制；将来按日期归档 / Mitigation: append-only for now; future archive by date

**产出 / Output**：

- `pandaone.py`（新增 log 子命令 + _print_log / _export_html 辅助函数 / added log subcommand + helper funcs）

***

### Step 7 — 实现 SHA256 自指纹保护（L5 防御）/ Step 7 — Implement SHA256 Self-Fingerprint (L5 Defense)

**目标 / Goal**：检测 pandaone.py 自身被篡改，提供合法更新机制。
Detect pandaone.py tampering; provide legitimate update mechanism.

**决策 / Decision**：

- 用 `hashlib.sha256(pandaone.py.read_bytes())` 计算指纹 / Compute fingerprint via `hashlib.sha256`

- 存到 `.pandaone_fp.txt`（项目根目录）/ Store at `.pandaone_fp.txt` (project root)

- main() 启动第一步就校验，篡改直接拒绝 / main() first step validates; tampering rejected immediately

- 首次运行：自动生成初始指纹（不算篡改）/ First run: auto-generate initial fingerprint (not tampering)

- `--update-fingerprint PASSWORD` 更新（默认密码 `0000`）/ Update with default password `0000`

- 密码错误：拒绝（rc != 0）/ Wrong password: rejected

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_fingerprint.py` 5 个测试 / RED: write `tests/test_fingerprint.py` 5 tests

  - 指纹文件创建 / Fingerprint file created

  - 指纹内容 = pandaone.py 的 SHA256 / Fingerprint content = SHA256 of pandaone.py

  - 篡改后检测失败 / Tamper detection fails

  - 默认密码可更新 / Default password can update

  - 错误密码被拒绝 / Wrong password rejected

- 验证 RED：5 failed / Verify RED: 5 failed

- GREEN：实现 check_fingerprint + compute_fingerprint + --update-fingerprint / GREEN: implement check_fingerprint + compute_fingerprint + --update-fingerprint

- 验证 GREEN：5 passed / Verify GREEN: 5 passed

- 修复一个 NameError（误用 PANDAX 变量名）/ Fix a NameError (mistakenly used PANDAX variable name)

**第一性原理 / First Principles**：

- L5 防御是审计系统的"自举保护"——谁来保护保护者？/ L5 is the audit system's "bootstrapping protection" — who guards the guard?

- 指纹是最简方案：二进制哈希 + 比对 / Fingerprint is simplest: binary hash + comparison

- 合法更新必须需要密码，防止 agent 绕过指纹 / Legitimate update requires password, prevents agent bypass

**对抗式审查 / Adversarial Review**：

- 攻击：agent 直接修改 .pandaone_fp.txt / Attack: agent directly modifies .pandaone_fp.txt

  - 缓解：指纹文件应在只读位置 / 用 git 跟踪（agent 改 git 难度大）/ Mitigation: fingerprint file in read-only location / tracked by git

- 攻击：密码泄露后任意修改 / Attack: password leak allows arbitrary modification

  - 缓解：默认密码 `0000` 仅本地用；正式安装时可改 / Mitigation: default password `0000` only for local; change at install

- 残余风险：单用户场景下密码保护强度有限（设计文档承认）/ Residual risk: single-user password protection is limited

**产出 / Output**：

- `pandaone.py`（新增指纹机制 + --update-fingerprint 参数 / added fingerprint mechanism + --update-fingerprint param）

- `.pandaone_fp.txt`（生成的指纹文件 / generated fingerprint file）

***

### Step 8 — 端到端集成测试 / Step 8 — End-to-End Integration Test

**目标 / Goal**：用单一测试覆盖完整用户工作流，验证 Phase 1 核心承诺。
Single test covering complete user workflow; verifies Phase 1 core promise.

**测试场景（test_full_workflow_e2e）/ Test Scenario**：

1. init → .pandaone/ 创建 / .pandaone/ created
2. git init + 初始 commit / git init + initial commit
3. lock → 所有 .py 不可写（PermissionError）/ All .py unwritable
4. write（reason 太短）→ REJECTED + 审计留痕 / REJECTED + audit
5. write（完整字段）→ APPROVED + 文件修改 + git commit + 审计留痕 / APPROVED + file modified + git commit + audit
6. log → 显示两条（APPROVED + REJECTED）/ Show both
7. log --rejected → 只显示拒绝记录（含 attempted 字段）/ Only rejected
8. log --export → 生成 HTML 报告 / Generate HTML
9. 验证最终审计日志含完整字段 / Verify final audit log has complete fields

**TDD 过程 / TDD Process**：

- RED：写 `tests/test_e2e.py` 1 个测试覆盖 10 个检查点 / RED: write `tests/test_e2e.py` 1 test covering 10 checkpoints

- 验证 RED：1 failed（首次跑时前面所有子流程同时验证）/ Verify RED: 1 failed

- GREEN：不需要新代码，只验证 Phase 1 集成正确 / GREEN: no new code, just verify Phase 1 integration

- 验证 GREEN：1 passed / Verify GREEN: 1 passed

**第一性原理 / First Principles**：

- 单元测试各自通过 ≠ 系统工作 / Unit tests passing ≠ system works

- e2e 测试是验证"承诺"而非"组件" / e2e tests verify "promises" not "components"

- 这是 Phase 1 完成的核心证据 / This is core proof of Phase 1 completion

**对抗式审查 / Adversarial Review**：

- 攻击：测试通过 ≠ 生产可用 / Attack: tests passing ≠ production-ready

- 缓解：手动 e2e + 真实 git 项目 + 真实 lock/unlock/write/log 链路 / Mitigation: manual e2e + real git project + real chain

**产出 / Output**：

- `tests/test_e2e.py`

***

## Phase 1 完成总结 / Phase 1 Completion Summary

**Phase 1：CLI MVP（P0）** ✅ 全部完成 / **Phase 1: CLI MVP (P0)** ✅ All done

| Step | 内容          | 关键决策                  |
| ---- | ----------- | --------------------- |
| 0    | README      | 作为 CLI 运行时数据源         |
| 1    | 测试项目        | TDD 起点（4 个测试）         |
| 2    | CLI 框架      | argparse + 启动读 README |
| 3    | init        | 幂等创建 .pandaone/      |
| 4    | lock/unlock | 跨平台 chmod             |
| 5    | write       | 8 步审计流程（含拒绝留痕）        |
| 5b   | install-git | 三层探测 + 自动下载           |
| 6    | log         | 过滤 + 文本 + HTML 导出     |
| 7    | 自指纹         | SHA256 + 密码更新         |
| 8    | e2e         | 完整工作流验证               |

**测试统计 / Test Statistics**：38 个测试，100% 通过 / 38 tests, 100% pass

**核心能力 / Core Capabilities**：

- ✅ 强制审计门禁（write 是唯一入口）/ Mandatory audit gateway (write is the only entry point)

- ✅ 必填元数据（reason/problem/approach）/ Required metadata

- ✅ 拒绝留痕（attempted_*）/ Rejection records

- ✅ 自动 git commit（带审计摘要）/ Auto git commit (with audit summary)

- ✅ L5 自指纹保护（SHA256）/ L5 self-fingerprint protection

- ✅ 审计查询（log + 过滤 + 导出）/ Audit query (log + filter + export)

- ✅ install-git（用户友好的依赖管理）/ install-git (user-friendly dependency management)

**下一步 / Next Step**：Phase 2 — watchdog + git hook + status/watch

***

## TDD 铁律（本项目遵守）/ TDD Iron Rule (This Project Follows)

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

每个 Step 都按 红 → 绿 → 重构 循环：
Each Step follows Red → Green → Refactor cycle:

1. RED：写一个失败测试 / RED: write a failing test
2. 验证：测试失败且失败原因正确（不是 typo）/ Verify: test fails for the right reason (not typo)
3. GREEN：写最小代码让测试通过 / GREEN: write minimal code to pass test
4. 验证：所有测试通过 / Verify: all tests pass
5. REFACTOR：清理但不增加行为 / REFACTOR: clean up without adding behavior

***

## 设计决策日志 / Design Decision Log

### D1 — README 作为 CLI 运行时依赖 / D1 — README as CLI Runtime Dependency

**问题 / Question**：CLI 如何让 agent / 开发者始终知道当前状态、设计意图？
How does CLI let agent/developer always know current state and design intent?

**决策 / Decision**：CLI 启动时必读 README.md，输出：
CLI must read README.md on startup, output:

- 当前阶段 / Current phase

- 上一个完成的 Step / Last completed Step

- 当前正在做的 Step / Current Step

- 下一步要做的 Step / Next Step

**第一性原理 / First Principles**：文档是"代码的外部大脑"，CLI 自读取等于让工具永远同步设计。
Documentation is code's "external brain"; CLI self-reading keeps the tool always in sync with design.

**对抗式审查 / Adversarial Review**：

- 攻击：agent 篡改 README 误导后续 CLI / Attack: agent tampers README to mislead subsequent CLI

- 缓解：README 与 `pandaone.py` 指纹无关；篡改 README 只能误导信息展示，不影响审计逻辑
  Mitigation: README unrelated to `pandaone.py` fingerprint; tampering only misleads info display, not audit logic

- 残余风险：低，因为 README 只影响 display 不影响 behavior / Residual risk: low; README only affects display

***

## 文件结构 / File Structure

```
<your-project-path>\
├── README.md                           # 本文件（实施日志 + CLI 启动读取 / this file (implementation log + CLI startup read)）
├── Pandaone_项目文档.html             # 原始设计文档（v2.0 / original design doc）
├── pandaone.py                        # 主 CLI（待创建 / main CLI, to create）
├── pandaone_guard.py                   # L2 监控（Phase 2 / L2 monitor）
├── install_hook.py                     # L3 hook 安装器（Phase 2 / L3 hook installer）
├── audit_viewer.py                     # 查询工具（可作为 log 后端 / query tool, can be log backend）
├── .pandaone_fp.txt                   # pandaone 自身指纹 / pandaone self-fingerprint
├── templates/
│   └── pre-commit-hook                 # git hook 模板（Phase 2 / git hook template）
├── tests/
│   ├── __init__.py
│   ├── test_readme_loaded.py           # 测试 CLI 启动读 README / test CLI startup reads README
│   ├── test_init.py
│   ├── test_lock.py
│   ├── test_write.py
│   ├── test_log.py
│   └── test_e2e.py
└── test_project/                       # 用 Pandaone 保护的测试项目 / test project protected by Pandaone
    ├── .pandaone/                     # init 创建 / created by init
    ├── main.py                         # 测试 .py / test .py
    └── utils.py
```

***

## 运行测试 / Run Tests

```powershell
cd <your-project-path>
python -m pytest tests/ -v
```

***

## 版本 / Version

- v0.0.1 — 2026-09-03 — README 创建 / README created
