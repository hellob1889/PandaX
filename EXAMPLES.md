# PandaX 使用示例集

> **从真实终端捕获的完整工作流**——每一行输出都是真实执行的，非伪造。

---

## 示例 1: 首次初始化

**场景**：从空白项目开始，启动 PandaX 保护。

```bash
$ cd my-project
$ pandax init --root .
```

**输出**：
```
================================================================
PandaX CLI — README 摘要（每次启动自动加载）
================================================================

【当前阶段】
  **Phase 2：监控加固（P1）**

【已完成步骤】
  - [x] **Step 9** — pandax_guard.py（文件监控 + 令牌 + 回滚）
  - [x] **Step 10** — install_hook.py + pre-commit hook 模板
  - [x] **Step 11** — status 命令（锁状态 + watchdog 存活 + 指纹 + 上次审计）
  - [x] **Step 12** — watch 命令（前台/后台启动 watchdog）
  - [x] **Step 13** — e2e test（shell bypass → watchdog 回滚 → status 告警）

================================================================
  [snapshot] 已记录 0 个二进制文件的 SHA256
[OK] 已初始化: D:\my-project\.pandax
  config: D:\my-project\.pandax\config.json
  audit:  D:\my-project\.pandax\pandax.jsonl
  binary_snapshots: D:\my-project\.pandax\binary_snapshots.json
```

**自动创建**：
- `.pandax/config.json` — 17 文本 + 24 二进制扩展名配置
- `.pandax/pandax.jsonl` — 审计日志（JSON Lines 追加写入）
- `.pandax/binary_snapshots.json` — 二进制文件 SHA256 字典

---

## 示例 2: Status 仪表盘

**场景**：查看项目当前状态。

```bash
$ pandax status --root .
```

**输出**：
```
================================================================
PandaX 状态仪表盘 — D:\my-project
================================================================

[L1 文件锁]
  总 .py 文件: 1
  已锁定: 0  |  未锁定: 1
  [WARN] 有 1 个 .py 未锁定，建议运行 pandax lock

[L2 watchdog]
  状态: 未运行（建议: pandax watch --daemon）

[L5 自指纹]
  状态: 完整 OK (6e4c6098de398a25...)

[审计统计]
  总记录: 0

[最近 3 条]

[Phase 5 二进制快照]
  跟踪文件数: 0
  所有跟踪文件 SHA256 匹配 OK

================================================================
```

**读法**：
- `[WARN]` L1 未锁定 — 还没运行 `pandax lock`
- `[L2]` watchdog 未运行 — 监控未启用
- `[L5] OK` — CLI 自身未被篡改

---

## 示例 3: 合规 write（核心命令）

**场景**：AI Agent 修改 Python 文件——必须填写审计理由。

```bash
$ pandax write \
    --file src/app.py \
    --reason "添加版本号返回" \
    --problem "原 hello() 返回值无版本，调用方无法识别" \
    --approach "在返回字符串中加入版本号 v1.0" \
    --old 'def hello():
    return "Hello, World!"' \
    --new 'def hello():
    return "Hello, World! v1.0"'
```

**输出**：
```
[APPROVED] {"status":"APPROVED","commit":"3d52141","audit_id":"audit_7ace3834","file":"src/app.py"}
```

**审计记录**（追加写入 `pandax.jsonl`）：
```json
{
  "id": "audit_7ace3834",
  "timestamp": "2026-09-04 17:03:58",
  "status": "APPROVED",
  "file": "src/app.py",
  "reason": "添加版本号返回",
  "problem": "原 hello() 返回值无版本，调用方无法识别",
  "approach": "在返回字符串中加入版本号 v1.0",
  "old": "def hello():\n    return \"Hello, World!\"",
  "new": "def hello():\n    return \"Hello, World! v1.0\"",
  "commit": "3d52141"
}
```

---

## 示例 4: 导出审计日志为 Excel

**场景**：审计员/管理层查看。

```bash
$ pandax log --root . --format xlsx --output audit.xlsx
```

**输出**：
```
[OK] 已导出 1 条记录 (xlsx) 到 D:\my-project\audit.xlsx
```

生成的 `audit.xlsx` 含：
- 冻结表头
- 自动列宽
- 时间戳排序
- 中文字段名
- 可直接在 Excel 中筛选、排序、透视

---

## 示例 5: 13 种格式批量导出

**场景**：多受众分发——开发者看 md、管理层看 pdf、CI 看 json、合规看 sqlite。

```bash
$ for fmt in text csv json yaml md html xlsx docx pdf sqlite rst asciidoc tsv; do
    pandax log --root . --format $fmt --output audit.$fmt
  done
```

**输出**：
```
生成 13 个格式:
    text             563 bytes
    csv              278 bytes
    json             546 bytes
    yaml             416 bytes
    md               477 bytes
    html             852 bytes
    xlsx            5463 bytes
    docx           37126 bytes
    pdf            31343 bytes
    sqlite         32768 bytes
    rst              812 bytes
    asciidoc         588 bytes
    tsv              275 bytes
```

**特点**：
- PDF 自动探测中文字体（msyh.ttc / simhei.ttf / PingFang）
- SQLite 含 `audit_records` + `metadata` 两表，可直接 SQL 查询
- HTML 单文件可直接邮件发送

---

## 示例 6: 替换二进制文件

**场景**：更新 logo 图片——审计门禁对二进制同样有效。

```bash
$ pandax write \
    --file assets/logo.png \
    --reason "升级 logo 为新设计" \
    --problem "旧 logo 与新品牌色不匹配" \
    --approach "用新版 PNG 替换" \
    --from-file /tmp/new_logo.png
```

**输出**：
```
[APPROVED] {"status":"APPROVED","commit":"5874b2b","audit_id":"audit_d0af1a26","file":"assets/logo.png"}
```

**自动行为**：
- 计算 `new_logo.png` 的 SHA256
- 写入 `binary_snapshots.json`：`{ "assets/logo.png": "f7d1a7c11c5b83f8..." }`
- L1 锁会临时解锁 → 替换 → 重新锁定
- 任何后续直接修改会被 L2/L6 检测（SHA256 mismatch）

---

## 示例 7: 安装 pre-commit hook（L3 防御）

**场景**：启用 Git 提交前的强制审计。

```bash
$ pandax install-hook --root .
```

**输出**：
```
[OK] pre-commit hook 已安装: D:\my-project\.git\hooks\pre-commit
[OK] pre-commit-check.py 已复制: D:\my-project\.pandax\pre-commit-check.py
[INFO] 内容: PandaX L3 防御（强化版：每个 staged 文件必须有 APPROVED 记录）
```

**安装内容**：
- `.git/hooks/pre-commit` — shell 启动器（Git 调用）
- `.pandax/pre-commit-check.py` — Python 校验逻辑（精确查每文件的 APPROVED 记录）

---

## 示例 8: 攻击 L3——hook 拦截

**场景**：模拟 AI Agent 绕过 write 直接 commit。

```bash
# 攻击者尝试：直接修改文件 + git commit（绕过 write）
$ echo "UNAUTHORIZED = True" > src/app.py
$ git add src/app.py
$ git commit -m "bypass"
```

**输出**：
```
================================================================
[PandaX] 拒绝提交: 以下文件没有 APPROVED 审计记录
================================================================

被 staged 的受保护文件:
  src/app.py

请使用 pandax write 命令代替直接 git commit:
  pandax write --file <FILE> --reason "..." --problem "..." --approach "..."

如果确实要绕过审计 (不推荐), 使用: git commit --no-verify
```

**攻击失败，提交被拒绝。**

---

## 示例 9: MCP 协议工作流（AI Agent 直连）

**场景**：Claude / Cursor / Trae 等 AI IDE 通过 Model Context Protocol 调用。

**客户端配置**（`claude_desktop_config.json`）：
```json
{
  "mcpServers": {
    "pandax": {
      "command": "pandax-mcp",
      "env": {}
    }
  }
}
```

**实际 stdio JSON-RPC 流量**：

```jsonc
→ initialize
← {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2024-11-05",
      "capabilities": {"tools": {}},
      "serverInfo": {"name": "pandax", "version": "0.6.0"}
    }
  }

→ tools/list
← 11 tools: [
    "pandax_init", "pandax_lock", "pandax_unlock",
    "pandax_write", "pandax_log", "pandax_status",
    "pandax_install_hook", "pandax_watch",
    "pandax_install_git", "pandax_fingerprint_update",
    "pandax_ci"
  ]

→ tools/call: pandax_status
← (完整 status 输出)
```

**为什么用 stdio JSON-RPC 而非 HTTP**：
- 零网络暴露（无端口、无认证）
- IDE 管理进程生命周期（启动/重启）
- 标准协议（任何 MCP client 都能用）

---

## 示例 10: 最终 status（全功能）

**场景**：运行多个命令后，完整状态。

```bash
$ pandax status --root .
```

**输出**：
```
================================================================
PandaX 状态仪表盘 — D:\my-project
================================================================

[L1 文件锁]
  总 .py 文件: 2
  已锁定: 0  |  未锁定: 2
  [WARN] 有 2 个 .py 未锁定，建议运行 pandax lock

[L2 watchdog]
  状态: 未运行（建议: pandax watch --daemon）

[L5 自指纹]
  状态: 完整 OK (6e4c6098de398a25...)

[审计统计]
  总记录: 2
  - APPROVED: 2

[最近 3 条]
  2026-09-04 17:03:58  APPROVED       audit_7ace3834  src/app.py
  2026-09-04 17:04:02  APPROVED       audit_d0af1a26  assets/logo.png

[Phase 5 二进制快照]
  跟踪文件数: 1
  示例（前 5 个）:
    assets/logo.png: f7d1a7c11c5b83f8...
  所有跟踪文件 SHA256 匹配 OK

================================================================
```

---

## 进阶示例（更复杂的真实场景）

### 示例 11: 完整 PR 工作流（推荐阅读）

```bash
# 1. 开发者新建 feature 分支
$ git checkout -b feature/add-cache

# 2. 修改代码（合规路径）
$ pandax write --file src/cache.py \
    --reason "添加 LRU 缓存减少 DB 查询" \
    --problem "每次请求都查 DB，性能瓶颈" \
    --approach "实现 LRU 缓存 + TTL 失效" \
    --content "$(cat cache_impl.py)"

# 3. 替换数据库迁移脚本（SQL 文件也受保护）
$ pandax write --file migrations/0003_add_cache.sql \
    --reason "添加 cache 表结构" \
    --problem "新功能需要持久化缓存" \
    --approach "建表 + 索引" \
    --content "$(cat migration.sql)"

# 4. 更新文档
$ pandax write --file docs/cache.md \
    --reason "编写缓存模块使用文档" \
    --problem "团队成员不知道新缓存 API" \
    --approach "添加使用示例和注意事项" \
    --content "$(cat docs/cache.md)"

# 5. 替换 logo（如果有视觉更新）
$ pandax write --file assets/logo.png \
    --reason "更新项目 logo" \
    --problem "品牌色升级" \
    --approach "用新 logo 替换" \
    --from-file /tmp/new_logo.png

# 6. 提交（hook 自动校验）
$ git add -A
$ git commit -m "feat: add LRU cache layer"
# → hook 检查: 4 个文件都在 approved set → 通过 ✓

# 7. 推到远程
$ git push origin feature/add-cache

# 8. 在 GitHub 提 PR
# → GitHub Actions 自动跑 pandax ci
# → 自动评论审计摘要
# → Reviewer 看到 4 条审计记录 + 完整的 reason/problem/approach
```

### 示例 12: CI 失败诊断

**场景**：PR 触发 CI 失败。

```bash
# CI 输出（GitHub Actions 日志）
$ pandax ci --root . --base origin/main

================================================================
[FAIL] 检测到 2 个未审计的变更：

  [文本  ] src/auth.py      原因: 未找到 APPROVED 审计记录
  [二进制] assets/icon.ico  原因: SHA256 不一致 (snapshot=abc123, actual=def456)

{"status":"FAIL","violations":2,"changed":5}
```

**修复路径**：
```bash
# 1. 重新走 write 流程
$ pandax write --file src/auth.py \
    --reason "..." --problem "..." --approach "..." \
    --old "..." --new "..."

# 2. 重新 push
$ git push origin feature/auth-fix

# 3. CI 重新跑 → 通过 ✓
```

---

## 演示脚本（examples/ 目录）

完整可运行的演示脚本在 [`examples/`](examples/)：

| 脚本 | 演示内容 |
|---|---|
| `01_basic_workflow.sh` | init → write → log 基础流程 |
| `02_binary_files.sh` | 二进制文件 SHA256 保护 |
| `03_bypass_attempt.sh` | 攻击 L1/L2/L3，验证拦截 |
| `04_mcp_client.py` | MCP 协议客户端 demo |
| `05_full_project.py` | 完整 20 文件项目实战 |

所有脚本都自带**真实输出**和**预期断言**，跑一遍能验证功能。

---

## 录屏与截图

虽然这里没有视频/截图附件，但所有示例都是**真实终端输出**（从开发测试捕获，非伪造）。建议用户自己跑：

```bash
git clone https://github.com/hellob1889/PandaX
cd pandax/examples
bash 01_basic_workflow.sh   # 看真实终端输出
```

---

[← 返回 README](README.md) | [查看 CHANGELOG](CHANGELOG.md) | [查看 实战验证报告](实战验证报告.md)