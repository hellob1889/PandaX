# PandaX v0.7.0 安装与使用指南 / PandaX v0.7.0 Installation & Usage Guide

> **历史归档**：v0.7.0 是第一个"完整功能版本"，包含 21 个 bug 修复（与 v0.7.1/v0.7.2 行为完全一致，差异在 CI 工程化）。
> **Historical archive**: v0.7.0 is the first "complete feature version", with 21 bug fixes (behavior fully compatible with v0.7.1/v0.7.2; differences only in CI engineering).

## 一、目标电脑前置条件 / Prerequisites

| 必需 / Required | 版本 / Version | 用途 / Purpose |
|---|---|---|
| Python | 3.8+ | 运行 PandaX CLI / Run PandaX CLI |
| Git | 2.20+ | 自动 commit / pre-commit hook |

Python 验证 / Verify：`python --version`  (Windows/Linux/Mac 通用 / universal)
Git 验证 / Verify：`git --version`

## 二、安装 PandaX / Install PandaX

### 2.1 推荐：pip 安装 wheel（最快）/ Recommended: pip Install Wheel (Fastest)

```bash
# 解压安装包 / Extract the installer package
# 假设 PandaX-0.7.0-install.zip 解压到 D:\pandax-pkg\ / Assume PandaX-0.7.0-install.zip extracted to D:\pandax-pkg\
cd D:\pandax-pkg

# 安装 wheel（pip 会自动拉依赖）/ Install wheel (pip auto-pulls dependencies)
pip install dist\pandax-0.7.0-py3-none-any.whl

# 或一行完成 / Or one-liner
pip install pandax-0.7.0-py3-none-any.whl
```

### 2.2 备选：从源码 sdist 安装 / Alternative: Install from Source sdist

```bash
pip install dist\pandax-0.7.0.tar.gz
```

### 2.3 离线安装（目标电脑无网）/ Offline Install (Target Machine Has No Network)

在有网的电脑上先下载依赖 / On a machine with network, download dependencies first:
```bash
pip download pandax-0.7.0-py3-none-any.whl -d deps/
# 会下载 watchdog / openpyxl / python-docx / reportlab / pyyaml 等
# Will download watchdog / openpyxl / python-docx / reportlab / pyyaml etc.

# 把 PandaX-0.7.0-install.zip + deps/ 一起拷到目标电脑
# Copy PandaX-0.7.0-install.zip + deps/ to target machine together
# 目标电脑上 / On target machine:
pip install --no-index --find-links=deps/ pandax-0.7.0-py3-none-any.whl
```

## 三、验证安装 / Verify Installation

```bash
# 1. 命令行可用性 / Command-line availability
python -m pandax --version

# 2. 子命令列表（应包含 export）/ Subcommand list (should include export)
python -m pandax --help
# 输出应包含 / Output should include: {init,lock,unlock,log,export,install-git,...}

# 3. 三个 CLI 都可用 / All three CLIs are available
python -m pandax --help         # 主 CLI（审计写入 / 查 / 导出）/ main CLI (audit write / query / export)
python -m pandax_guard --help   # watchdog（守护模式）/ watchdog (daemon mode)
python -m pandax_mcp --help     # MCP server（AI agent 集成）/ MCP server (AI agent integration)
```

如果想直接用 `pandax` 而不是 `python -m pandax` / If you want to use `pandax` directly instead of `python -m pandax`:
```bash
# 把 Scripts 目录加到 PATH（通常 pip 会自动做）/ Add Scripts directory to PATH (usually pip does this automatically)
# Windows 默认 / default: %APPDATA%\Python\Python3X\Scripts\
# 或 / Or:
python -m site --user-site
# 把上面的 `..../site-packages` 替换为 `..../Scripts` 加入 PATH
# Replace `..../site-packages` above with `..../Scripts` and add to PATH
```

## 四、首次使用（quick start）/ First Use (Quick Start)

```bash
# 1. 进入你的项目目录 / Go to your project directory
cd C:\my-project

# 2. 初始化 PandaX（创建 .pandax/ + 锁定受保护文件）/ Initialize PandaX (creates .pandax/ + locks protected files)
python -m pandax init

# 3. 第一次写入受保护文件（如 .py）：会被要求审计 / First write to protected file (e.g. .py): will require audit
python -m pandax write --file main.py \
    --reason "添加 hello world 函数 / Add hello world function" \
    --problem "需要支持中文输出 / Need Chinese output support" \
    --approach "用 print + encoding utf-8 / Use print + encoding utf-8" \
    --old "pass" --new "def hello(): print('hello')"

# 4. 查看审计历史 / View audit history
python -m pandax log

# 5. 导出为 HTML 报告（新子命令）/ Export as HTML report (new subcommand)
python -m pandax export --format html --output report.html

# 6. 安装 pre-commit hook（防止 AI agent 绕过）/ Install pre-commit hook (prevent AI agent bypass)
python -m pandax install-hook

# 7. 启动 watchdog（后台监控 + 自动回滚）/ Start watchdog (background monitor + auto rollback)
python -m pandax watch --daemon
```

## 五、v0.7.0 包含的修复（21 个 bug）/ Fixes Included in v0.7.0 (21 Bugs)

```
P0 安全 (5) / P0 Security (5): #8 #12 v1 #12 v2 #22 #23
P1 (3):       #2  #5  #15
P2 (5):       #21 #6  #20 #9  #10
P3 (3):       #13 #4  #26
i18n 完整 (3) / i18n complete (3): #14 #17 #26(部分 / partial)
UX (1):        #25 (独立 export 子命令 / independent export subcommand)
```

主要改进 / Major Improvements：
- **#28** lock 自动 init（首次使用一键 Lock，不再需先 Init）/ lock auto-init (one-click Lock on first use, no longer requires Init first)
- **#22** pre-commit hook CRLF→LF (P0 安全 bug / P0 security bug)
- **#23** watchdog dedupe (1 次写入只产 1 条审计 / 1 write produces 1 audit entry)
- **#24** watchdog print flush (前台输出不再被 Python 缓冲 / foreground output no longer buffered by Python)
- **#14 / #17 / #26** i18n 完整性（zh-CN + en 全本地化）/ i18n completeness (zh-CN + en fully localized)
- **#25** 独立 `pandax export` 子命令 / independent `pandax export` subcommand

## 六、常见问题 / FAQ

### Q1: pip install 时报 "ModuleNotFoundError: No module named 'venv'"
A: 你的 Python 缺 venv 模块。改用 / Your Python lacks the venv module. Use instead:
```bash
pip install --no-build-isolation dist\pandax-0.7.0.tar.gz
# 或 / Or
python -m build --no-isolation   # 在打包端 / on the packaging side
```

### Q2: Windows 上找不到 `pandax` 命令 / Can't find `pandax` command on Windows
A: 用 `python -m pandax ...` 代替。或者把 Scripts 目录加到 PATH / Use `python -m pandax ...` instead. Or add Scripts directory to PATH:
```bash
# PowerShell
$env:PATH += ";$(python -m site --user-site)\..\Scripts"
```

### Q3: git commit 时 hook 报 syntax error near 'elif'
A: 这是已修复的 #22。验证你的 wheel 是 v0.7.0（已包含 fix）/ This is #22 (already fixed). Verify your wheel is v0.7.0 (includes fix):
```bash
python -m pandax install-hook --root .
# 然后 cat .git/hooks/pre-commit | head -5
# 应该看到 #!/bin/sh 后面只有 LF，没有 CRLF
# Should see only LF after #!/bin/sh, no CRLF
```

### Q4: pre-commit hook 不阻止未授权 commit / pre-commit hook doesn't block unauthorized commit
A: 检查 hook 是否安装到位 / Check if hook is installed correctly:
```bash
ls .git/hooks/pre-commit    # 应该存在 / should exist
cat .git/hooks/pre-commit | head -3
# 应是 #!/bin/sh + LF 行尾（不是 CRLF）/ Should be #!/bin/sh + LF line ending (not CRLF)
```

### Q5: 想回退到 v0.6.x？/ Want to roll back to v0.6.x?
A: 暂未发布到 PyPI，可手动用 git 切到对应 tag 重装 / Not yet published to PyPI; manually checkout the tag via git and reinstall.

## 七、卸载 / Uninstall

```bash
pip uninstall pandax
```

## 八、文件清单 / File Listing

```
PandaX-0.7.0-install.zip (210 KB)
├── dist/
│   ├── pandax-0.7.0-py3-none-any.whl   (70 KB, 推荐安装方式 / recommended install)
│   └── pandax-0.7.0.tar.gz             (146 KB, 源码包 / source archive)
└── PandaX-0.7.0-INSTALL.md             (本文件 / this file)
```

## 九、反馈 / Feedback

测试中遇到的任何问题，记录以下信息后反馈 / If you encounter issues during testing, record the following info and report:
1. Python 版本 / Python version: `python --version`
2. Git 版本 / Git version: `git --version`
3. PandaX 版本 / PandaX version: `python -m pandax --version`
4. 错误信息（完整 stderr + exit code）/ Error info (full stderr + exit code)
5. 复现步骤 / Reproduction steps
