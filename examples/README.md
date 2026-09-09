# PandaX Examples

> **可运行的演示脚本** — 每个脚本都是真实工作流，自带预期验证。

## 5 个演示脚本

| 脚本 | 演示内容 | 运行时长 |
|---|---|---|
| [`01_basic_workflow.sh`](01_basic_workflow.sh) | init → lock → write → log → status 基础流程 | ~10s |
| [`02_binary_files.sh`](02_binary_files.sh) | 二进制文件 SHA256 snapshot + 篡改检测 | ~10s |
| [`03_bypass_attempt.sh`](03_bypass_attempt.sh) | 5 种攻击尝试 → 验证 L1/L3/L7 拦截 | ~15s |
| [`04_mcp_client.py`](04_mcp_client.py) | MCP 协议客户端（JSON-RPC over stdio） | ~5s |
| [`05_full_project.py`](05_full_project.py) | 完整 20 文件项目实战（7 层防御全跑） | ~30s |

## 快速运行

```bash
cd examples

# 方式 A：逐个跑（推荐新手）
bash 01_basic_workflow.sh
bash 02_binary_files.sh
bash 03_bypass_attempt.sh
python 04_mcp_client.py
python 05_full_project.py

# 方式 B：一次性跑全部
for f in 01_basic_workflow.sh 02_binary_files.sh 03_bypass_attempt.sh; do
  bash "$f" || exit 1
done
python 04_mcp_client.py && python 05_full_project.py
```

## 前置要求

- 已安装 pandax：`pip install pandax`
- Windows + Git（脚本通过 `shutil.which("git")` 自动检测）
- macOS/Linux 用户：把 `GIT_EXE="/d/软件/Git/cmd/git.exe"` 改为 `which git` 的结果

## 输出

每个脚本跑完会在当前目录创建 `demo_XX_xxx/` 工作目录，保留中间产物供检查。
跑完可以手动 `rm -rf demo_*` 清理。

## 验证标准

每个脚本失败时**会自动 exit 1**，CI 可直接用：

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

## 自定义

要测试自己的场景？修改对应脚本的 `files = {...}` 字典即可。

## 预期输出概览

### 01_basic_workflow.sh 输出关键行
```
✓ git initialized
✓ PandaX initialized
✓ Files locked
✓ PermissionError（文件被锁）
✓ Demo 1 完成 — 基础工作流演示
```

### 02_binary_files.sh 输出关键行
```
[snapshot] 已记录 3 个二进制文件的 SHA256
[APPROVED] {... "file":"assets/logo.png"}
⚠️  photo.jpg 已被覆盖（绕过 write）
status 检测到篡改
```

### 03_bypass_attempt.sh 输出关键行
```
✓ L1 拦截：PermissionError
✓ L3 拦截：hook 拒绝 commit
✓ L7 拦截：CI 检测到未审计的 src/evil.py
```

### 04_mcp_client.py 输出关键行
```
Server: pandax v0.6.x
发现 11 个工具
Result: ...
```

### 05_full_project.py 输出关键行
```
创建 10 文本 + 5 二进制 = 15 文件
✓ 实际锁定文件数: 15
✓ L1 拦截: PermissionError
✓ L3 hook 拦截: rc=1
13 种格式全部生成
✓ Demo 5 完成 — 完整 20 文件项目走完 7 层防御
```