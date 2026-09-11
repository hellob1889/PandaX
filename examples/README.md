# Pandaone AI Agent Examples

> **可运行的演示脚本** — 每个脚本都是真实工作流，自带预期验证。
> **Runnable demo scripts** — each script is a real workflow with built-in expected validation.

## 5 个演示脚本 / 5 Demo Scripts

| 脚本 / Script | 演示内容 / Demo | 运行时长 / Runtime |
|---|---|---|
| [`01_basic_workflow.sh`](01_basic_workflow.sh) | init → lock → write → log → status 基础流程 / basic workflow | ~10s |
| [`02_binary_files.sh`](02_binary_files.sh) | 二进制文件 SHA256 snapshot + 篡改检测 / binary SHA256 snapshot + tamper detection | ~10s |
| [`03_bypass_attempt.sh`](03_bypass_attempt.sh) | 5 种攻击尝试 → 验证 L1/L3/L7 拦截 / 5 attack attempts → verify L1/L3/L7 interception | ~15s |
| [`04_mcp_client.py`](04_mcp_client.py) | MCP 协议客户端（JSON-RPC over stdio）/ MCP protocol client (JSON-RPC over stdio) | ~5s |
| [`05_full_project.py`](05_full_project.py) | 完整 20 文件项目实战（7 层防御全跑）/ full 20-file project exercise (all 7 layers) | ~30s |

## 快速运行 / Quick Run

```bash
cd examples

# 方式 A：逐个跑（推荐新手）
# Method A: Run one by one (recommended for beginners)
bash 01_basic_workflow.sh
bash 02_binary_files.sh
bash 03_bypass_attempt.sh
python 04_mcp_client.py
python 05_full_project.py

# 方式 B：一次性跑全部
# Method B: Run all at once
for f in 01_basic_workflow.sh 02_binary_files.sh 03_bypass_attempt.sh; do
  bash "$f" || exit 1
done
python 04_mcp_client.py && python 05_full_project.py
```

## 前置要求 / Prerequisites

- 已安装 pandaone：`pip install pandaone-guard`
  pandaone installed: `pip install pandaone-guard`
- Windows + Git（脚本通过 `shutil.which("git")` 自动检测）
  Windows + Git (script auto-detects via `shutil.which("git")`)
- macOS/Linux 用户：把 `GIT_EXE="/d/软件/Git/cmd/git.exe"` 改为 `which git` 的结果
  macOS/Linux users: change `GIT_EXE="/d/软件/Git/cmd/git.exe"` to `which git` output

## 输出 / Output

每个脚本跑完会在当前目录创建 `demo_XX_xxx/` 工作目录，保留中间产物供检查。
Each script creates a `demo_XX_xxx/` working directory after running, preserving intermediate artifacts for inspection.
跑完可以手动 `rm -rf demo_*` 清理。
After running, you can `rm -rf demo_*` to clean up.

## 验证标准 / Validation Criteria

每个脚本失败时**会自动 exit 1**，CI 可直接用：
Each script **auto-exits 1 on failure**, ready for direct CI use:

```yaml
- name: Run examples
  run: |
    cd examples
    bash 01_basic_workflow.sh
    bash 02_binary_files.sh
    bash 03_bypass_attempt.sh
    python 04_mcp_client.py
    python 05_full_project.py
```

## 自定义 / Customization

要测试自己的场景？修改对应脚本的 `files = {...}` 字典即可。
Want to test your own scenario? Edit the `files = {...}` dict in the corresponding script.

## 预期输出概览 / Expected Output Overview

### 01_basic_workflow.sh 输出关键行 / Output key lines
```
✓ git initialized
✓ Pandaone initialized
✓ Files locked
✓ PermissionError（文件被锁 / file is locked）
✓ Demo 1 完成 — 基础工作流演示 / Demo 1 done — basic workflow demo
```

### 02_binary_files.sh 输出关键行 / Output key lines
```
[snapshot] 已记录 3 个二进制文件的 SHA256 / 3 binary files' SHA256 recorded
[APPROVED] {... "file":"assets/logo.png"}
⚠️  photo.jpg 已被覆盖（绕过 write）/ photo.jpg was overwritten (bypassing write)
status 检测到篡改 / status detected tampering
```

### 03_bypass_attempt.sh 输出关键行 / Output key lines
```
✓ L1 拦截：PermissionError / L1 blocked: PermissionError
✓ L3 拦截：hook 拒绝 commit / L3 blocked: hook rejects commit
✓ L7 拦截：CI 检测到未审计的 src/evil.py / L7 blocked: CI detected unaudited src/evil.py
```

### 04_mcp_client.py 输出关键行 / Output key lines
```
Server: pandaone v0.6.x
发现 11 个工具 / found 11 tools
Result: ...
```

### 05_full_project.py 输出关键行 / Output key lines
```
创建 10 文本 + 5 二进制 = 15 文件 / created 10 text + 5 binary = 15 files
✓ 实际锁定文件数: 15 / actual locked file count: 15
✓ L1 拦截: PermissionError / L1 blocked: PermissionError
✓ L3 hook 拦截: rc=1 / L3 hook blocked: rc=1
13 种格式全部生成 / all 13 formats generated
✓ Demo 5 完成 — 完整 20 文件项目走完 7 层防御 / Demo 5 done — full 20-file project through all 7 layers
```