# 快速开始

> **5 分钟上手** — 从安装到第一次审计写入。

## Step 1: 安装（30 秒）

```bash
pip install pandax-guard
pandaone --version
# pandaone-guard v0.7.2
```

## Step 2: 初始化项目（10 秒）

```bash
cd /path/to/your-project
pandaone init --root .
```

自动创建：
- `.pandaone/config.json` — 17 文本 + 24 二进制扩展名
- `.pandaone/pandaone.jsonl` — 审计日志
- `.pandaone/binary_snapshots.json` — 二进制文件 SHA256

## Step 3: 锁定文件（5 秒）

```bash
pandaone lock --root .
```

**所有受保护文件变为只读**：
```
[OK] 锁定 12 个文件（受保护扩展名: .py, .pyx, .json, ...）
```

## Step 4: 合规修改（30 秒）

不要直接编辑文件——用 `pandaone write`：

```bash
pandaone write \
    --file src/main.py \
    --reason "修复用户 ID 类型注解" \
    --problem "原代码用 int，实际可能是 None" \
    --approach "改为 Optional[int]" \
    --old 'def get_user(user_id: int):' \
    --new 'def get_user(user_id: Optional[int]):'
```

输出：
```
[APPROVED] {"status":"APPROVED","commit":"3d52141","audit_id":"audit_xxx","file":"src/main.py"}
```

## Step 5: 查看审计历史（10 秒）

```bash
# 命令行查看
pandaone log --last 10

# 导出为 Excel
pandaone log --format xlsx --output audit.xlsx

# 导出为 PDF（含中文支持）
pandaone log --format pdf --output audit.pdf
```

## Step 6: 项目状态（5 秒）

```bash
pandaone status --root .
```

显示 L1 锁定、L2 watchdog、L5 指纹、最近审计等全部状态。

---

## 下一步

- **保护 Git 提交**：运行 `pandaone install-hook --root .`
- **后台监控**：运行 `pandaone watch --root . --daemon`
- **AI Agent 集成**：配置 [MCP Server](mcp-integration.md)
- **CI 集成**：参考 [CI/CD 集成](ci-integration.md)

## 完整示例

10 个真实工作流：[EXAMPLES.md](../../EXAMPLES.md)

实战验证报告：[实战验证报告.md](../../实战验证报告.md)