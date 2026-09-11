# Pandaone AI Agent v0.7.2 安装与使用指南 / Pandaone v0.7.2 Installation & Usage Guide

## 一、目标电脑前置条件 / Prerequisites

| 必需 / Required | 版本 / Version | 用途 / Purpose |
|---|---|---|
| Python | 3.8+ | 运行 Pandaone CLI / Run Pandaone CLI |
| Git | 2.20+ | 自动 commit / pre-commit hook |

Python 验证 / Verify：`python --version`  (Windows/Linux/Mac 通用 / universal)
Git 验证 / Verify：`git --version`

## 二、安装 Pandaone / Install Pandaone

### 2.1 推荐：pip 安装 wheel（最快）/ Recommended: pip Install Wheel (Fastest)

```bash
# 解压安装包
# Extract the installer package
# 假设 Pandaone-0.7.2-install.zip 解压到 D:\pandaone-pkg\
# Assume Pandaone-0.7.2-install.zip is extracted to D:\pandaone-pkg\
cd D:\pandaone-pkg

# 安装 wheel（pip 会自动拉依赖）
# Install wheel (pip auto-pulls dependencies)
pip install dist\pandaone_guard-0.7.2-py3-none-any.whl

# 或一行完成
# Or one-liner
pip install pandaone_guard-0.7.2-py3-none-any.whl
```

### 2.2 备选：从源码 sdist 安装 / Alternative: Install from Source sdist

```bash
pip install dist\pandaone_guard-0.7.2.tar.gz
```

### 2.3 离线安装（目标电脑无网）/ Offline Install (Target Machine Has No Network)

在有网的电脑上先下载依赖：
On a machine with network, download dependencies first:
```bash
pip download pandaone_guard-0.7.2-py3-none-any.whl -d deps/
# 会下载 watchdog / openpyxl / python-docx / reportlab / pyyaml 等
# Will download watchdog / openpyxl / python-docx / reportlab / pyyaml etc.

# 把 Pandaone-0.7.2-install.zip + deps/ 一起拷到目标电脑
# Copy Pandaone-0.7.2-install.zip + deps/ to target machine together
# 目标电脑上：
# On target machine:
pip install --no-index --find-links=deps/ pandaone_guard-0.7.2-py3-none-any.whl
```

### 2.4 在线安装（推荐）/ Online Install (Recommended)

```bash
pip install pandaone-guard==0.7.2
```

## 三、验证安装 / Verify Installation

```bash
# 1. 命令行可用性
# Command-line availability
python -m pandaone --version
# 输出 / Output: pandaone-guard v0.7.2

# 2. 子命令列表（应包含 export）
# Subcommand list (should include export)
python -m pandaone --help
# 输出应包含 / Output should include: {init,lock,unlock,log,export,install-git,...}

# 3. 三个 CLI 都可用
# All three CLIs are available
python -m pandaone --help         # 主 CLI（审计写入 / 查 / 导出）/ main CLI (audit write / query / export)
python -m pandaone_guard --help   # watchdog（守护模式）/ watchdog (daemon mode)
python -m pandaone_mcp --help     # MCP server（AI agent 集成）/ MCP server (AI agent integration)
```

如果想直接用 `pandaone` 而不是 `python -m pandaone`：
If you want to use `pandaone` directly instead of `python -m pandaone`:
```bash
# 把 Scripts 目录加到 PATH（通常 pip 会自动做）
# Add Scripts directory to PATH (usually pip does this automatically)
# Windows 默认 / default: %APPDATA%\Python\Python3X\Scripts\
# 或 / Or:
python -m site --user-site
# 把上面的 `..../site-packages` 替换为 `..../Scripts` 加入 PATH
# Replace `..../site-packages` above with `..../Scripts` and add to PATH
```

## 四、首次使用（quick start）/ First Use (Quick Start)

```bash
# 1. 进入你的项目目录
# Go to your project directory
cd C:\my-project

# 2. 初始化 Pandaone（创建 .pandaone/ + 锁定受保护文件）
# Initialize Pandaone (creates .pandaone/ + locks protected files)
python -m pandaone init

# 3. 第一次写入受保护文件（如 .py）：会被要求审计
# First write to protected file (e.g. .py): will require audit
python -m pandaone write --file main.py \
    --reason "添加 hello world 函数 / Add hello world function" \
    --problem "需要支持中文输出 / Need Chinese output support" \
    --approach "用 print + encoding utf-8 / Use print + encoding utf-8" \
    --old "pass" --new "def hello(): print('hello')"

# 4. 查看审计历史
# View audit history
python -m pandaone log

# 5. 导出为 HTML 报告
# Export as HTML report
python -m pandaone export --format html --output report.html

# 6. 安装 pre-commit hook（防止 AI agent 绕过）
# Install pre-commit hook (prevent AI agent bypass)
python -m pandaone install-hook

# 7. 启动 watchdog（后台监控 + 自动回滚）
# Start watchdog (background monitor + auto rollback)
python -m pandaone watch --daemon
```

## 五、v0.7.2 包含的修复 / Fixes Included in v0.7.2

v0.7.2 与 v0.7.1 行为完全一致，仅修复 CI 发布工程化问题：
v0.7.2 is fully behavior-compatible with v0.7.1; only fixes CI release engineering:

- **CI Tests job 在干净 ubuntu-latest 容器 25s exit 1**（根因：setuptools pin 缺失）
  **CI Tests job exits 1 within 25s on clean ubuntu-latest** (root cause: missing setuptools pin)
  → pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`，与 build 步骤对齐
  → pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`, aligned with build step
- **pytest log artifact 上传**：CI 测试失败时 `tee /tmp/pytest.log` + `actions/upload-artifact@v4`，便于诊断
  **pytest log artifact upload**: on CI test failure, `tee /tmp/pytest.log` + `actions/upload-artifact@v4`, for diagnostics

功能层面未变化，全部 v0.7.1 的 28 个 bug 修复 + 4 大新功能（文件夹熊猫锁图标、Web 实时仪表盘、Git 兼容、右键菜单真实可用验证）继续保留。
Functionality unchanged; all v0.7.1's 28 bug fixes + 4 major features (folder Panda lock icon, web realtime dashboard, Git compatibility, context menu real-verified) are retained.

## 六、常见问题 / FAQ

### Q1: pip install 时报 "ModuleNotFoundError: No module named 'venv'"
A: 你的 Python 缺 venv 模块。改用：
Your Python lacks the venv module. Use instead:
```bash
pip install --no-build-isolation dist\pandaone_guard-0.7.2.tar.gz
# 或 / Or
python -m build --no-isolation   # 在打包端 / on the packaging side
```

### Q2: Windows 上找不到 `pandaone` 命令 / Can't find `pandaone` command on Windows
A: 用 `python -m pandaone ...` 代替。或者把 Scripts 目录加到 PATH：
Use `python -m pandaone ...` instead. Or add Scripts directory to PATH:
```bash
# PowerShell
$env:PATH += ";$(python -m site --user-site)\..\Scripts"
```

### Q3: git commit 时 hook 报 syntax error near 'elif'
A: 这是 v0.7.1 已修复的 #22。验证你的 wheel 是 v0.7.2：
This is #22 fixed in v0.7.1. Verify your wheel is v0.7.2:
```bash
python -m pandaone install-hook --root .
# 然后 cat .git/hooks/pre-commit | head -5
# Then: cat .git/hooks/pre-commit | head -5
# 应该看到 #!/bin/sh 后面只有 LF，没有 CRLF
# Should see only LF after #!/bin/sh, no CRLF
```

### Q4: pre-commit hook 不阻止未授权 commit / pre-commit hook doesn't block unauthorized commit
A: 检查 hook 是否安装到位：
Check if hook is installed correctly:
```bash
ls .git/hooks/pre-commit    # 应该存在 / should exist
cat .git/hooks/pre-commit | head -3
# 应是 #!/bin/sh + LF 行尾（不是 CRLF）
# Should be #!/bin/sh + LF line ending (not CRLF)
```

### Q5: 想回退到 v0.7.1？/ Want to roll back to v0.7.1?
A: 直接指定版本：
Pin version directly:
```bash
pip install pandaone-guard==0.7.1
```

## 七、卸载 / Uninstall

```bash
pip uninstall pandaone-guard
```

## 八、文件清单 / File Listing

```
Pandaone-0.7.2-install.zip (210 KB)
├── dist/
│   ├── pandaone_guard-0.7.2-py3-none-any.whl   (70 KB, 推荐安装方式 / recommended install)
│   └── pandaone_guard-0.7.2.tar.gz             (146 KB, 源码包 / source archive)
└── Pandaone-0.7.2-INSTALL.md             (本文件 / this file)
```

## 九、反馈 / Feedback

测试中遇到的任何问题，记录以下信息后反馈：
If you encounter issues during testing, record the following info and report:
1. Python 版本 / Python version: `python --version`
2. Git 版本 / Git version: `git --version`
3. Pandaone 版本 / Pandaone version: `python -m pandaone --version`
4. 错误信息（完整 stderr + exit code）/ Error info (full stderr + exit code)
5. 复现步骤 / Reproduction steps
