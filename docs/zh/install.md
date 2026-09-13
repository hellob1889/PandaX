# 安装

## 系统要求

- **Python 3.8+**（3.10/3.11/3.12 都验证过）
- **操作系统**：Windows 10+ / macOS 10.14+ / Linux
- **可选**：git（用于 L2 回滚和 L7 CI 验证）

## 一行安装

```bash
pip install pandaone-guard
```

## 验证安装

```bash
pandaone --version
# pandaone-guard v0.7.2
```

## 开发模式安装

如果你想参与开发：

```bash
git clone https://github.com/hellob1889/Pandaone-AI-Agent
cd pandaone
pip install -e .[dev]
pytest tests/ -v
# 340 passed
```

## 依赖说明

安装时自动安装以下依赖（全部纯 Python，跨平台）：

| 包 | 用途 |
|---|---|
| `watchdog>=3.0.0` | L2 文件监控（实时检测变更） |
| `openpyxl>=3.1.0` | Excel 导出 |
| `python-docx>=1.1.0` | Word 导出 |
| `reportlab>=4.0.0` | PDF 导出（含中文支持） |
| `pyyaml>=6.0` | YAML 导出 |

**没有 C 扩展，不需要编译器**——在 Alpine / musl 上也工作。

## 升级

```bash
pip install pandaone-guard --upgrade
```

## 卸载

```bash
pip uninstall pandaone-guard
# 清理 fingerprint
rm -rf ~/.pandaone_fp.txt
# 清理 PATH（如果之前手动添加过 pandaone-mcp）
```

## Docker（可选）

```dockerfile
FROM python:3.11-slim
RUN pip install pandaone-guard
ENTRYPOINT ["pandaone"]
```

## 故障排查

### 问题：找不到 git

L2 watchdog 用 git 回滚篡改文件。如果系统没装 git：

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# Windows
# 从 https://git-scm.com 下载安装

# Pandaone AI Agent 也提供自动安装（但需要用户授权）
pandaone install-git
```

### 问题：PDF 中文显示为方块

PDF 导出依赖系统字体。Windows 默认带 `msyh.ttc`，macOS 自带 `PingFang.ttc`。
Linux 用户：

```bash
sudo apt install fonts-wqy-microhei fonts-noto-cjk
```

### 问题：PermissionError when locking

Pandaone 用 chmod 锁定文件。在 Linux/macOS 上是 POSIX 标准行为。
在 Windows 上用 `attrib +r`，对普通用户透明。
**如果你看到 PermissionError** — 说明锁定生效（这是预期行为）。

---

下一步：[快速开始](quickstart.md) | [命令参考](commands.md)