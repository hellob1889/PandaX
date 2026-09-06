# PandaX v0.7.0 安装与使用指南

## 一、目标电脑前置条件

| 必需 | 版本 | 用途 |
|---|---|---|
| Python | 3.8+ | 运行 PandaX CLI |
| Git | 2.20+ | 自动 commit / pre-commit hook |

Python 验证：`python --version`  (Windows/Linux/Mac 通用)
Git 验证：`git --version`

## 二、安装 PandaX

### 2.1 推荐：pip 安装 wheel（最快）

```bash
# 解压安装包
# 假设 PandaX-0.7.0-install.zip 解压到 D:\pandax-pkg\
cd D:\pandax-pkg

# 安装 wheel（pip 会自动拉依赖）
pip install dist\pandax-0.7.0-py3-none-any.whl

# 或一行完成
pip install pandax-0.7.0-py3-none-any.whl
```

### 2.2 备选：从源码 sdist 安装

```bash
pip install dist\pandax-0.7.0.tar.gz
```

### 2.3 离线安装（目标电脑无网）

在有网的电脑上先下载依赖：
```bash
pip download pandax-0.7.0-py3-none-any.whl -d deps/
# 会下载 watchdog / openpyxl / python-docx / reportlab / pyyaml 等

# 把 PandaX-0.7.0-install.zip + deps/ 一起拷到目标电脑
# 目标电脑上：
pip install --no-index --find-links=deps/ pandax-0.7.0-py3-none-any.whl
```

## 三、验证安装

```bash
# 1. 命令行可用性
python -m pandax --version

# 2. 子命令列表（应包含 export）
python -m pandax --help
# 输出应包含: {init,lock,unlock,log,export,install-git,...}

# 3. 三个 CLI 都可用
python -m pandax --help         # 主 CLI（审计写入 / 查 / 导出）
python -m pandax_guard --help   # watchdog（守护模式）
python -m pandax_mcp --help     # MCP server（AI agent 集成）
```

如果想直接用 `pandax` 而不是 `python -m pandax`：
```bash
# 把 Scripts 目录加到 PATH（通常 pip 会自动做）
# Windows 默认: %APPDATA%\Python\Python3X\Scripts\
# 或:
python -m site --user-site
# 把上面的 `..../site-packages` 替换为 `..../Scripts` 加入 PATH
```

## 四、首次使用（quick start）

```bash
# 1. 进入你的项目目录
cd C:\my-project

# 2. 初始化 PandaX（创建 .pandax/ + 锁定受保护文件）
python -m pandax init

# 3. 第一次写入受保护文件（如 .py）：会被要求审计
python -m pandax write --file main.py \
    --reason "添加 hello world 函数" \
    --problem "需要支持中文输出" \
    --approach "用 print + encoding utf-8" \
    --old "pass" --new "def hello(): print('hello')"

# 4. 查看审计历史
python -m pandax log

# 5. 导出为 HTML 报告（新子命令）
python -m pandax export --format html --output report.html

# 6. 安装 pre-commit hook（防止 AI agent 绕过）
python -m pandax install-hook

# 7. 启动 watchdog（后台监控 + 自动回滚）
python -m pandax watch --daemon
```

## 五、v0.7.0 包含的修复（21 个 bug）

```
P0 安全 (5): #8 #12 v1 #12 v2 #22 #23
P1 (3):       #2  #5  #15
P2 (5):       #21 #6  #20 #9  #10
P3 (3):       #13 #4  #26
i18n 完整 (3): #14 #17 #26(部分)
UX (1):        #25 (独立 export 子命令)
```

主要改进：
- **#28** lock 自动 init（首次使用一键 Lock，不再需先 Init）
- **#22** pre-commit hook CRLF→LF (P0 安全 bug)
- **#23** watchdog dedupe (1 次写入只产 1 条审计)
- **#24** watchdog print flush (前台输出不再被 Python 缓冲)
- **#14 / #17 / #26** i18n 完整性（zh-CN + en 全本地化）
- **#25** 独立 `pandax export` 子命令

## 六、常见问题

### Q1: pip install 时报 "ModuleNotFoundError: No module named 'venv'"
A: 你的 Python 缺 venv 模块。改用：
```bash
pip install --no-build-isolation dist\pandax-0.7.0.tar.gz
# 或
python -m build --no-isolation   # 在打包端
```

### Q2: Windows 上找不到 `pandax` 命令
A: 用 `python -m pandax ...` 代替。或者把 Scripts 目录加到 PATH：
```bash
# PowerShell
$env:PATH += ";$(python -m site --user-site)\..\Scripts"
```

### Q3: git commit 时 hook 报 syntax error near 'elif'
A: 这是已修复的 #22。验证你的 wheel 是 v0.7.0（已包含 fix）：
```bash
python -m pandax install-hook --root .
# 然后 cat .git/hooks/pre-commit | head -5
# 应该看到 #!/bin/sh 后面只有 LF，没有 CRLF
```

### Q4: pre-commit hook 不阻止未授权 commit
A: 检查 hook 是否安装到位：
```bash
ls .git/hooks/pre-commit    # 应该存在
cat .git/hooks/pre-commit | head -3
# 应是 #!/bin/sh + LF 行尾（不是 CRLF）
```

### Q5: 想回退到 v0.6.x？
A: 暂未发布到 PyPI，可手动用 git 切到对应 tag 重装。

## 七、卸载

```bash
pip uninstall pandax
```

## 八、文件清单

```
PandaX-0.7.0-install.zip (210 KB)
├── dist/
│   ├── pandax-0.7.0-py3-none-any.whl   (70 KB, 推荐安装方式)
│   └── pandax-0.7.0.tar.gz             (146 KB, 源码包)
└── PandaX-0.7.0-INSTALL.md             (本文件)
```

## 九、反馈

测试中遇到的任何问题，记录以下信息后反馈：
1. Python 版本: `python --version`
2. Git 版本: `git --version`
3. PandaX 版本: `python -m pandax --version`
4. 错误信息（完整 stderr + exit code）
5. 复现步骤

