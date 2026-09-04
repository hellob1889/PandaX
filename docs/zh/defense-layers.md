# 7 层防御体系

PandaX 的核心是**冗余防御**——任何受保护文件的修改必须同时绕过 L1-L7 中至少 5 层才能成功。
每层防御**独立工作**，**互相兜底**。

## 全景图

```
┌─────────────────────────────────────────────────────────────┐
│                    受保护的文件                              │
│  main.py  README.md  config.json  .env  logo.png  report.pdf │
└─────────────────────────────────────────────────────────────┘
         ↓ ↑           ↓ ↑           ↓ ↑            ↓ ↑
    L1 file lock    L2 watchdog    L3 hook       L6 binary
    (chmod -w)     (实时监控)    (git commit)    (SHA256)
                                          ↓
                                    L7 CI verification
                                    (PR 合入前)

所有层之上的元数据：
  L4 README 启动加载        L5 self-fingerprint
```

## 各层详解

### L1：file chmod 锁定

**作用**：让文件在 OS 层面不可写。

**实现**：
- Windows：`attrib +R file.py`
- macOS/Linux：`chmod 444 file.py`

**绕过难度**：低（root 用户可 chmod +w）

**被绕过后**：L2 watchdog 通过文件修改事件兜底。

### L2：watchdog 实时监控

**作用**：后台守护进程监控所有受保护文件的变化。

**实现**：watchdog 库 + 审计令牌机制。

**检测机制**：
- 任何文件修改 → 检查是否在 pandax write 期间（即有 audit_token）
- 如果没有 audit_token → git checkout HEAD 还原 + 记录 UNAUTHORIZED

**绕过难度**：中（需先 kill watchdog 进程）

**被绕过后**：L3 hook 兜底（git commit 时校验）。

### L3：pre-commit hook

**作用**：阻止任何未审计的代码进入 git 历史。

**实现**：`pre-commit-check.py`（Python 校验逻辑）

**校验逻辑**：
```python
for staged_file in git_diff_cached:
    if staged_file not in audit_log.approved_files:
        exit(1)  # 拒绝 commit
```

**绕过难度**：中（攻击者可用 `--no-verify` 跳过）

**被绕过后**：L7 CI 兜底（PR 合入前再校验）。

### L4：启动读 README

**作用**：CLI 启动时加载项目元数据（当前阶段、已完成步骤）。

**实现**：CLI 每次运行自动读取项目根的 `.pandax/README`。

**价值**：让审计门禁成为项目**日常工作流**的一部分（透明可见）。

### L5：自指纹校验

**作用**：防止 CLI 自身被篡改。

**实现**：CLI 自身代码的 SHA256 指纹，存放在 `~/.pandax_fp.txt`。

**校验时机**：每次 pandax CLI 启动。

**绕过难度**：极高（需修改指纹存储位置 + 重新计算所有 hash）。

### L6：二进制 SHA256 snapshot

**作用**：保护图片、PDF、Word 等二进制文件。

**实现**：init 时建立 SHA256 字典，写入时更新。

**校验时机**：watchdog 检测到二进制文件变更时比对 SHA256。

**绕过难度**：低（写时 snapshot 自动更新）——但**审计记录在日志里**。

### L7：GitHub Actions CI

**作用**：PR 合入主分支前的最终验证。

**实现**：`pandax ci --root . --base origin/main`

**校验逻辑**：
```bash
# PR 修改的文件 vs 审计日志的 APPROVED 记录
git diff --name-only origin/main..HEAD
for each file:
    if file not in audit_log.approved_files:
        FAIL  # PR 失败
```

**绕过难度**：极高（需直接改 main 分支 + 绕过 GitHub 权限）。

---

## 对抗式审查

| 攻击 | 攻击路径 | 防御层 |
|---|---|---|
| 攻击者 chmod +w 直接改文件 | L1 → L2 兜底 | L2 |
| 攻击者 kill watchdog 进程 | L2 → L3 兜底 | L3 |
| 攻击者用 `--no-verify` 绕过 hook | L3 → L7 兜底 | L7 |
| 攻击者改 pandax CLI 自身 | L5 检测指纹不匹配 → L4 启动失败 | L5 |
| 攻击者改 .gitignore 隐藏攻击 | L1 lock + L2 监控 | L1+L2 |
| 攻击者覆盖 .png 二进制 | L1 lock + L6 SHA256 mismatch | L1+L6 |
| 攻击者直接 push 到 main 分支 | GitHub 权限保护 + 分支规则 | (GitHub settings) |

**结论**：7 层防御是**纵深防御**（defense in depth）——单层被绕过不致命。

---

## 第一性原理

> **审计的核心是"每一次改动都有证据"**——证据 = 审计日志条目 = reason/problem/approach 三段式说明。
> 7 层防御的目的是**让"没有证据的改动"成为不可能**，而不是"让改动本身不可能"。
> 区别在于：阻止只是延迟攻击，让攻击**留下痕迹**才是审计的本质。

---

[← 返回首页](index.md) | [查看命令参考](commands.md) | [查看 实战验证报告](../../实战验证报告.md)