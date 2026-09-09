# PandaX 实施日志（Living Doc）

> **核心机制**：CLI 每次运行都会读取本文件，并在启动时显示当前阶段 / 已完成步骤 / 待办。
> 所以本文件不是"写完就不管"的文档，而是 **CLI 自身依赖的运行时数据**。

***

## 项目目标

实现 `PandaX` —— 一个 OS 级物理强制的 AI Agent 代码审计门禁系统。
详见 `PandaX_项目文档.html`（v2.0 设计文档）。

***

## 当前阶段

**v0.7.0 — 生产就绪（25 个 bug 全修，243 测试通过）**

### P0 安全 (5)
- [x] **#8 + #7** — install-context 通配符阻塞（PS5.1 registry provider 改用 .NET API）
- [x] **#12 v1** — write 失败时 mode 恢复（try/finally + 原始 mode 恢复）
- [x] **#12 v2** — write 默认拒绝 ReadOnly 锁定文件（`--force-write` 显式 opt-in）
- [x] **#22** — pre-commit hook CRLF→LF（bash 在 *nix 上不支持 CRLF，P0 安全）
- [x] **#23** — watchdog dedupe（1 次写入只产 1 条审计，2 秒去重窗口）

### P1 (4)
- [x] **#2** — status 用 `_iter_protected_files` 共享 helper（19 种扩展名全覆盖）
- [x] **#5** — `--lang` 全局参数支持任意位置（main() 预扫描 argv）
- [x] **#15** — PowerShell subprocess `-NoProfile -NonInteractive` + timeout=60
- [x] **#29** — pandax init merge-preserve（不再覆盖用户自定义 config.json）

### P2 (5)
- [x] **#21** — doctor/write git 检测一致性（共享 `_resolve_git_exe()`）
- [x] **#6** — log 标签 i18n 完整（REJECTED/UNAUTHORIZED 走 t()）
- [x] **#20** — ci 区分空仓库 vs 首次 commit（智能 baseline fallback）
- [x] **#9 / #10** — 智能长度阈值（`_info_length` unicode 宽度，1 中文字 = 2 宽度）

### P3 (4)
- [x] **#13** — log `-n` 简写作为 `--recent` 别名
- [x] **#4** — README summary 显示最新 Phase 而非旧 Step
- [x] **#26** — export html/md/text 报告标签本地化
- [x] **#39** — cmd_write 4 处硬编码中文改为 i18n

### UX + 横切 i18n (3)
- [x] **#14** — log 在 lang=en 时 Reason 字段本地化
- [x] **#17** — status i18n 完整性
- [x] **#48** — `--trust-default` 自动接受新指纹（pip install --upgrade 场景）

### UX (2)
- [x] **#25** — 独立 `pandax export` 子命令（语义清晰，不再借用 log）
- [x] **#28** — `pandax lock` 一键启用（未 init 时自动 init，首次使用友好）

### Phase 进度

**Phase 1：CLI MVP（P0）** ✅ 全部完成（Step 0–8）
**Phase 2：监控加固（P1）** ✅ 全部完成（Step 9–13）
**Phase 3：标准 Python 包分发（P0）** ✅ 全部完成（Step 14–18）
**Phase 4：跨平台右键菜单（P1）** ✅ 全部完成（Windows/macOS/Linux + i18n）
**Phase 5：环境诊断（P1）** ✅ 全部完成（doctor.py + 13 类 auto-fix + PATH 持久化）

**当前测试数**：264 passed（覆盖 i18n / write / status / lock / ci / watchdog / export / init / e2e / version-source-of-truth）

**Phase 6：MCP Server / TRAE Skill（P2）**：下一步

***

## 实施步骤记录

### Step 0 — 创建 README（本次）

**目标**：建立实施日志结构，使 CLI 启动可读取。
**决策**：

- README 顶部固定段落（`## 当前阶段`、`## 实施步骤记录`）让 CLI 可以结构化解析

- 每个 Step 一个三级标题，含"目标 / 决策 / TDD过程 / 产出"

- 完成的 Step 标记 `[x]`，进行中 `[~]`，待办 `[ ]`

**产出**：

- `README.md`

**下一步**：建立 test\_project 测试项目，写第一个 RED 测试。

***

### Step 1 — 第一个 RED 测试（CLI 必读 README）

**目标**：用 TDD 锁定 "CLI 启动必读 README" 的机制。

**TDD 过程**：

- RED：写 `tests/test_readme_loaded.py` 共 4 个测试

  - `test_pandax_file_exists`：pandax.py 必须存在

  - `test_readme_file_exists`：README.md 必须存在

  - `test_cli_loads_readme_on_startup`：CLI 无参数启动 stdout 必须包含 "Phase 1"

  - `test_cli_shows_completed_steps`：CLI 启动 stdout 必须包含 "\[x]" 标记

- 验证 RED：3 failed, 1 passed（pandax.py 不存在，失败原因正确）

- 决策：用 pytest（需 `pip install pytest`）

**产出**：

- `tests/__init__.py`

- `tests/test_readme_loaded.py`

- `test_project/main.py`（测试用 .py 文件）

- `test_project/utils.py`

***

### Step 2 — 实现 pandax.py 框架 + 启动读 README

**目标**：让 Step 1 的 RED 测试通过。

**决策**：

- argparse 主解析器 + subparsers 占位所有子命令（init/lock/unlock/write/log/status/watch）

- `load_readme_summary()` 函数解析 README：

  - 提取 "## 当前阶段" 段落中的 `**Phase X` 标题行

  - 提取同段落中的 `- [x]` 行作为"已完成步骤"

- 启动流程：先 print README 摘要 → 再处理 CLI 参数

**TDD 过程**：

- GREEN：写 `pandax.py`，所有 4 个测试通过

- REFACTOR：改进解析逻辑，让"已完成步骤"清晰列出 Step 标题

**第一性原理**：

- 文档是"代码的外部大脑"，CLI 自读取等于让工具永远同步设计

- README 与代码审计逻辑解耦：篡改 README 只能误导显示，不影响审计行为

**对抗式审查**：

- 攻击：篡改 README 误导 CLI 显示

- 缓解：README 不参与审计逻辑，篡改仅影响信息展示

- 残余风险：低

**产出**：

- `pandax.py`（v0.0.1，含 argparse 框架 + README 摘要）

***

### Step 3 — 实现 init 子命令

**目标**：让 `pandax init --root <path>` 在指定目录创建 `.pandax/` 基础设施。

**决策**：

- 使用 `Path.mkdir(parents=True, exist_ok=True)` 实现幂等

- config.json 字段严格对齐设计文档（version / project\_root / protected\_extensions / exclude\_patterns / git\_enabled / watchdog\_enabled / min\_\*\_length）

- agent\_audit.jsonl 用 `Path.touch()` 创建空文件（首次存在即可）

- `--root` 默认 "." 即当前目录

**TDD 过程**：

- RED：写 `tests/test_init.py` 5 个测试

  - 创建 .pandax/ 目录

  - 创建合法 config.json（version / project\_root / protected\_extensions）

  - 创建 agent\_audit.jsonl

  - 幂等（二次 init 不报错）

  - \--root 参数生效

- 验证 RED：5 failed（init 不支持 --root）

- GREEN：实现 cmd\_init

- 验证 GREEN：5 passed

- 手测：`pandax init --root test_project` 成功创建

**第一性原理**：

- init 是审计系统的"开机仪式"，三个文件（config/audit/dir）必须同时存在

- 幂等是工程化的体现，避免 agent 重复 init 时报错

**对抗式审查**：

- 攻击：agent 在错误的目录 init，污染无关项目

- 缓解：--root 强制显式路径；init 不递归扫描，只在指定目录操作

- 残余风险：低

**产出**：

- `pandax.py`（新增 init 子命令 + --root 参数）

***

### Step 4 — 实现 lock / unlock 子命令

**目标**：让 `pandax lock / unlock --root <path>` 切换项目 .py 文件的只读状态。

**决策**：

- 跨平台：使用 Python `os.chmod` + `stat.S_IWUSR/S_IWGRP/S_IWOTH` 位掩码

- Windows 上 `chmod ~S_IWUSR` 等价于 `attrib +r`（设置只读属性）

- Linux/Mac 上等价于 `chmod 444`

- 共享函数 `_apply_readonly(root, readonly)` 给两个命令复用

- 排除规则从 config.json 读取（`exclude_patterns`）

- 未 init 的目录 lock → 返回 rc=1 + 错误信息（不崩溃）

**TDD 过程**：

- RED：写 `tests/test_lock.py` 5 个测试

  - lock 后 main.py 写入应失败（PermissionError）

  - unlock 后可写

  - lock 不锁 _tmp_\*.py（排除规则）

  - lock 输出包含数量

  - 未 init 的目录 lock 优雅失败

- 验证 RED：3 failed（lock 无 --root）

- GREEN：实现 cmd\_lock / cmd\_unlock / \_apply\_readonly

- 验证 GREEN：5 passed

**第一性原理**：

- L1 文件锁是 OS 级物理屏障，`chmod` 是最可靠的跨平台方法

- 排除规则防止误锁临时文件（如 _tmp_\*.py、__pycache__）

**对抗式审查**：

- 攻击：agent 用 shell `attrib -r` 解锁后写入

- 缓解：L2 watchdog 监控后续步骤会捕获并回滚（Phase 2）

- 残余风险：watchdog 未运行时无第二道防线

**产出**：

- `pandax.py`（新增 lock / unlock 子命令 + \_apply\_readonly 共享函数）

***

### Step 5 — 实现 write 子命令（核心）

**目标**：让 `pandax write --file X --reason Y --problem Z --approach W` 完成完整审计写入流程。

**决策**：

- 完整 8 步流程：水质检测 → 设令牌 → 解锁 → 写入 → 锁回 → 清令牌 → git commit → 审计记录

- 拒绝路径也要写审计记录（含 `attempted_*` 字段）

- 字符串替换模式（`--old` / `--new`）和整文件模式（`--content`）

- `--old` 不在文件中 → 拒绝并回滚

- git 不可用时 → 不阻塞，审计记录照写，输出 WARN

- 审计 ID 用 `uuid.uuid4().hex[:8]`

**TDD 过程**：

- RED：写 `tests/test_write.py` 8 个测试

  - 4 个水质检测：reason 空 / problem 空 / reason 太短 / 拒绝记录

  - 4 个通过路径：完整元数据 / 整文件模式 / git commit 增加 / 非 .py 拒绝

- 验证 RED：6 failed（write 不支持 --root）+ 2 假阳性（argparse 错误也 rc != 0）

- GREEN：实现 cmd\_write 全 8 步流程

- 验证 GREEN：8 passed

- 修复一个测试数据问题（approach 长度 < 10）

**第一性原理**：

- 内联审计（写入前）优于事后审计，错误在源头拦截

- 拒绝也是数据：attempted\_\* 字段让"失败的尝试"也成为留痕

- 锁 + 令牌 + 写 + 锁 + 清令牌 是一个原子事务

**对抗式审查**：

- 攻击：agent 在 write 执行到一半时 kill 进程，留下 .audit\_token

  - 缓解：watchdog 监控 .audit\_token 的年龄，过期则告警（Phase 2）

- 攻击：用户提供假 reason 绕过审计

  - 缓解：审计价值在留痕不在判断真假，假 reason 也是证据

- 攻击：手动 git commit --amend 修改历史

  - 缓解：commit hash 已记录到审计日志，可对照

**产出**：

- `pandax.py`（新增 write 子命令，含完整 8 步流程）

***

### Step 5b — 实现 install-git 子命令（用户需求追加）

**目标**：让 CLI 能探测 git 是否可用，缺失时自动下载 portable 版本。

**决策**：

- 三层探测策略：

  1. `shutil.which("git")`（PATH 中）
  2. 常见路径列表（D:\软件\Git\cmd、C:\Program Files\Git\cmd 等）
  3. 未找到 → 提示 + 可选自动下载

- `--probe-only`：只探测不下载（默认）

- `--auto-download`：自动下载 PortableGit zip（约 50MB）到 `<pandax_dir>/git/`

- 下载源：GitHub releases 的 portable zip 版（免安装，免管理员权限）

**TDD 过程**：

- RED：写 `tests/test_install_git.py` 4 个测试

  - 子命令存在

  - 探测找到 git 时输出路径

  - 探测输出有意义内容

  - git 不在 PATH 时优雅处理

- 验证 RED：4 failed

- GREEN：实现 cmd\_install\_git + \_download\_portable\_git

- 验证 GREEN：4 passed（修复 1 个测试预期 — 实际有常见路径 git）

**第一性原理**：

- 用户的开发机 git 装在非标准路径很常见（如 D:\软件\Git\）

- CLI 应智能探测而不是假设 PATH

- 自动下载只作为兜底，给用户选择权

**对抗式审查**：

- 攻击：恶意网络环境下载到恶意 git

  - 缓解：使用官方 GitHub releases HTTPS，文件可校验

- 攻击：用户没网，--auto-download 卡死

  - 缓解：默认不下载，给出手动安装选项

**产出**：

- `pandax.py`（新增 install-git 子命令）

- `tests/conftest.py`（自动探测 git 并加入 PATH）

***

### Step 6 — 实现 log 子命令

**目标**：让 `pandax log` 支持查询、过滤、导出审计记录。

**决策**：

- 过滤链式：`--file` / `--session` / `--rejected` / `--unauthorized` / `--recent N`

- 文本格式：表格化输出，每条记录含核心字段

- 导出：`--export PATH` 生成 HTML（暗色主题对齐设计文档）

- 未 init 目录 → 优雅报错（rc=1）

- APPROVED 显示 reason/problem/approach/commit

- REJECTED 显示 rejection\_reason + attempted\_\*

**TDD 过程**：

- RED：写 `tests/test_log.py` 6 个测试

  - \--help 含 --recent

  - 默认显示所有（<=20）

  - \--recent N 只显示最近 N

  - \--file X 过滤

  - \--rejected 过滤

  - 未 init 优雅报错

- 验证 RED：6 failed

- GREEN：实现 cmd\_log + \_print\_log + \_export\_html

- 验证 GREEN：6 passed

- 端到端手测：write → log 显示 APPROVED + REJECTED 双记录

**第一性原理**：

- log 是审计的"读取端"，必须和 write 形成闭环

- 拒绝留痕是审计系统诚实性的体现

- 过滤是把大量记录浓缩为有效信号的工具

**对抗式审查**：

- 攻击：agent 篡改 agent\_audit.jsonl

- 缓解：将来加 git commit 到 jsonl 文件本身（git 本身不可篡改）

- 攻击：日志无限增长

- 缓解：当前仅追加不限制；将来按日期归档

**产出**：

- `pandax.py`（新增 log 子命令 + \_print\_log / \_export\_html 辅助函数）

***

### Step 7 — 实现 SHA256 自指纹保护（L5 防御）

**目标**：检测 pandax.py 自身被篡改，提供合法更新机制。

**决策**：

- 用 `hashlib.sha256(pandax.py.read_bytes())` 计算指纹

- 存到 `.pandax_fp.txt`（项目根目录）

- main() 启动第一步就校验，篡改直接拒绝

- 首次运行：自动生成初始指纹（不算篡改）

- `--update-fingerprint PASSWORD` 更新（默认密码 `0000`）

- 密码错误：拒绝（rc != 0）

**TDD 过程**：

- RED：写 `tests/test_fingerprint.py` 5 个测试

  - 指纹文件创建

  - 指纹内容 = pandax.py 的 SHA256

  - 篡改后检测失败

  - 默认密码可更新

  - 错误密码被拒绝

- 验证 RED：5 failed

- GREEN：实现 check\_fingerprint + compute\_fingerprint + --update-fingerprint

- 验证 GREEN：5 passed

- 修复一个 NameError（误用 PANDAX 变量名）

**第一性原理**：

- L5 防御是审计系统的"自举保护"——谁来保护保护者？

- 指纹是最简方案：二进制哈希 + 比对

- 合法更新必须需要密码，防止 agent 绕过指纹

**对抗式审查**：

- 攻击：agent 直接修改 .pandax\_fp.txt

  - 缓解：指纹文件应在只读位置 / 用 git 跟踪（agent 改 git 难度大）

- 攻击：密码泄露后任意修改

  - 缓解：默认密码 `0000` 仅本地用；正式安装时可改

- 残余风险：单用户场景下密码保护强度有限（设计文档承认）

**产出**：

- `pandax.py`（新增指纹机制 + --update-fingerprint 参数）

- `.pandax_fp.txt`（生成的指纹文件）

***

### Step 8 — 端到端集成测试

**目标**：用单一测试覆盖完整用户工作流，验证 Phase 1 核心承诺。

**测试场景（test\_full\_workflow\_e2e）**：

1. init → .pandax/ 创建
2. git init + 初始 commit
3. lock → 所有 .py 不可写（PermissionError）
4. write（reason 太短）→ REJECTED + 审计留痕
5. write（完整字段）→ APPROVED + 文件修改 + git commit + 审计留痕
6. log → 显示两条（APPROVED + REJECTED）
7. log --rejected → 只显示拒绝记录（含 attempted 字段）
8. log --export → 生成 HTML 报告
9. 验证最终审计日志含完整字段

**TDD 过程**：

- RED：写 `tests/test_e2e.py` 1 个测试覆盖 10 个检查点

- 验证 RED：1 failed（首次跑时前面所有子流程同时验证）

- GREEN：不需要新代码，只验证 Phase 1 集成正确

- 验证 GREEN：1 passed

**第一性原理**：

- 单元测试各自通过 ≠ 系统工作

- e2e 测试是验证"承诺"而非"组件"

- 这是 Phase 1 完成的核心证据

**对抗式审查**：

- 攻击：测试通过 ≠ 生产可用

- 缓解：手动 e2e + 真实 git 项目 + 真实 lock/unlock/write/log 链路

**产出**：

- `tests/test_e2e.py`

***

## Phase 1 完成总结

**Phase 1：CLI MVP（P0）** ✅ 全部完成

| Step | 内容          | 关键决策                  |
| ---- | ----------- | --------------------- |
| 0    | README      | 作为 CLI 运行时数据源         |
| 1    | 测试项目        | TDD 起点（4 个测试）         |
| 2    | CLI 框架      | argparse + 启动读 README |
| 3    | init        | 幂等创建 .pandax/      |
| 4    | lock/unlock | 跨平台 chmod             |
| 5    | write       | 8 步审计流程（含拒绝留痕）        |
| 5b   | install-git | 三层探测 + 自动下载           |
| 6    | log         | 过滤 + 文本 + HTML 导出     |
| 7    | 自指纹         | SHA256 + 密码更新         |
| 8    | e2e         | 完整工作流验证               |

**测试统计**：38 个测试，100% 通过

**核心能力**：

- ✅ 强制审计门禁（write 是唯一入口）

- ✅ 必填元数据（reason/problem/approach）

- ✅ 拒绝留痕（attempted\_\*）

- ✅ 自动 git commit（带审计摘要）

- ✅ L5 自指纹保护（SHA256）

- ✅ 审计查询（log + 过滤 + 导出）

- ✅ install-git（用户友好的依赖管理）

**下一步**：Phase 2 — watchdog + git hook + status/watch

***

## TDD 铁律（本项目遵守）

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

每个 Step 都按 红 → 绿 → 重构 循环：

1. RED：写一个失败测试
2. 验证：测试失败且失败原因正确（不是 typo）
3. GREEN：写最小代码让测试通过
4. 验证：所有测试通过
5. REFACTOR：清理但不增加行为

***

## 设计决策日志

### D1 — README 作为 CLI 运行时依赖

**问题**：CLI 如何让 agent / 开发者始终知道当前状态、设计意图？

**决策**：CLI 启动时必读 README.md，输出：

- 当前阶段

- 上一个完成的 Step

- 当前正在做的 Step

- 下一步要做的 Step

**第一性原理**：文档是"代码的外部大脑"，CLI 自读取等于让工具永远同步设计。

**对抗式审查**：

- 攻击：agent 篡改 README 误导后续 CLI

- 缓解：README 与 `pandax.py` 指纹无关；篡改 README 只能误导信息展示，不影响审计逻辑

- 残余风险：低，因为 README 只影响 display 不影响 behavior

***

## 文件结构

```
<your-project-path>\
├── README.md                           # 本文件（实施日志 + CLI 启动读取）
├── PandaX_项目文档.html             # 原始设计文档（v2.0）
├── pandax.py                        # 主 CLI（待创建）
├── pandax_guard.py                   # L2 监控（Phase 2）
├── install_hook.py                     # L3 hook 安装器（Phase 2）
├── audit_viewer.py                     # 查询工具（可作为 log 后端）
├── .pandax_fp.txt                   # pandax 自身指纹
├── templates/
│   └── pre-commit-hook                 # git hook 模板（Phase 2）
├── tests/
│   ├── __init__.py
│   ├── test_readme_loaded.py           # 测试 CLI 启动读 README
│   ├── test_init.py
│   ├── test_lock.py
│   ├── test_write.py
│   ├── test_log.py
│   └── test_e2e.py
└── test_project/                       # 用 PandaX 保护的测试项目
    ├── .pandax/                     # init 创建
    ├── main.py                         # 测试 .py
    └── utils.py
```

***

## 运行测试

```powershell
cd <your-project-path>
python -m pytest tests/ -v
```

***

## 版本

- v0.0.1 — 2026-09-03 — README 创建

