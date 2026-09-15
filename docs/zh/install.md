# 安装

## 系统要求

- **操作系统**：Windows 10+ / macOS 10.14+ / Linux
- **可选**：git（用于 L3 pre-commit hook + L2 回滚 + L7 CI 验证）
- **Python**：v0.7.13 起，一键安装脚本会自动装嵌入式 Python 3.12（**Windows 无需管理员**）

---

## 推荐：一键硬隔离安装（v0.7.11+，v0.7.13 零前置）

**一行命令搞定所有环境**——Python 自动装、venv 自动建、wheel 自动下、PATH 自动配、右键菜单（Windows）+ git pre-commit hook（所有平台）全部自动配置。

### Windows（PowerShell）

```powershell
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex
```

### macOS / Linux

```bash
curl -sSL https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.sh | bash
```

### 自动做的事

| 步骤 | 行为 |
|---|---|
| 1. 检测 Python ≥ 3.8 | PATH 里有就用；没有 → Windows 自动下载嵌入式 Python 3.12 到 `%LOCALAPPDATA%\pandaone\python\`（**无需管理员**） |
| 2. 检测 Git | PATH 里有就用；没有 → 打印平台特定安装命令（winget / brew / xcode-select / apt / dnf / yum / pacman / apk） |
| 3. 创建硬隔离 venv | `venv` 在 `%LOCALAPPDATA%\pandaone\venv\`（Windows）或 `~/.local/share/pandaone/venv`（macOS/Linux）——**不污染系统 site-packages** |
| 4. 下载 wheel | 从 GitHub Release API 拉最新版 + **SHA256 校验**（不信任 PyPI mirror） |
| 5. 装 pandaone | `pip install` 到 venv |
| 6. 加 PATH | venv/Scripts 持久化到用户环境变量（Windows HKCU / macOS `~/.zshrc` / Linux `~/.bashrc`） |
| 7. Windows 右键菜单 | 自动跑 `pandaone install-context`（HKCU 注册表） |
| 8. Git pre-commit hook | 自动跑 `pandaone install-hook`（**仅当 cwd 是 git repo + git 可用**） |

### 验证

```powershell
pandaone --version
# pandaone-guard v0.7.13

pandaone doctor
# 环境诊断（9 项 + 13 类自动修复）
```

### Opt-out flags

```powershell
# Windows: 跳过右键菜单 + git hook 自动配置
irm ... | iex -SkipContext -SkipHook

# macOS/Linux: 跳过 git hook
curl ... | bash --skip-hook
```

---

## 备选：传统 pip 安装（v0.7.11 之前的方式，仍支持）

```bash
pip install pandaone-guard

# 手动配置环境
pandaone install-context   # Windows 右键菜单
pandaone install-hook      # git pre-commit hook（在 git repo 内）
```

**对比**：
- ✅ 简单（pip 一行）
- ⚠️ 需要 Python ≥ 3.8 已预装（Windows 上 `python.org` 下载 .msi 安装器）
- ⚠️ 装到系统 site-packages（多 Python 版本会冲突）
- ⚠️ 右键菜单 / git hook 需手动跑

---

## 升级

### 一键脚本升级（推荐，自动拉最新 release）

```powershell
# Windows
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex

# macOS / Linux
curl -sSL https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.sh | bash
```

脚本会**自动检测**：
- venv 已存在 → 升级 wheel（不重建 venv）
- 已是最新版 → 跳过下载

### 传统方式

```bash
pip install pandaone-guard --upgrade
pandaone install-context   # 重装右键菜单（idempotent）
pandaone install-hook      # 重装 git hook（idempotent）
```

---

## 卸载

### 一键脚本安装的（推荐）

**Windows**：
```powershell
Remove-Item -Recurse -Force $env:LOCALAPPDATA\pandaone
# 删除用户 PATH 里 venv/Scripts (手动)
```

**macOS / Linux**：
```bash
rm -rf ~/.local/share/pandaone
# 删除 shell rc 里的 PATH 追加 (手动)
```

### 传统 pip 安装的

```bash
pip uninstall pandaone-guard
rm -rf ~/.pandaone_fp.txt
# 右键菜单 + git hook 需要手动清理
pandaone install-context --uninstall   # Windows
rm .git/hooks/pre-commit .pandaone/pre-commit-check.py   # git hook
```

---

## Docker（可选）

```dockerfile
FROM python:3.11-slim
RUN pip install pandaone-guard
ENTRYPOINT ["pandaone"]
```

Docker 镜像内**不需要**右键菜单 / git hook（这些是主机集成）。

---

## 故障排查

### PowerShell 拒绝运行 install.ps1

PowerShell 默认 ExecutionPolicy 是 `Restricted`，会拒绝脚本运行。
`irm ... | iex`（iex = Invoke-Expression）已隐式用 `-ExecutionPolicy Bypass`，无需手动设置。

如果是手动下载 `install.ps1` 后运行：
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Python 没装（Windows）

v0.7.13 起一键脚本会**自动下载嵌入式 Python 3.12.7** 到 `%LOCALAPPDATA%\pandaone\python\`：
- 无需管理员
- 无需 GUI
- 11 MB 下载量
- 自动启用 `import site`（否则 venv 装 pip 包会失败）

如果下载失败（网络问题）：
- 手动装 Python：https://www.python.org/downloads/windows/（**勾选 "Add Python to PATH"**）
- 然后再跑 install.ps1

### Git 没装

一键脚本会自动打印**平台特定的安装命令**：

| 平台 | 命令 |
|---|---|
| Windows（有 winget） | `winget install Git.Git`（需管理员） |
| Windows（无 winget） | https://git-scm.com/download/win |
| macOS | `xcode-select --install` 或 `brew install git` |
| Ubuntu/Debian | `sudo apt install git` |
| Fedora | `sudo dnf install git` |
| CentOS/RHEL | `sudo yum install git` |
| Arch | `sudo pacman -S git` |
| Alpine | `sudo apk add git` |

装好 git 后**重跑 install.ps1** 即可补装 git pre-commit hook。

### Windows 右键菜单没出现

1. 重启资源管理器：
   ```powershell
   Stop-Process -Name explorer -Force
   Start-Process explorer
   ```

2. 或重新装右键菜单：
   ```powershell
   pandaone install-context --force
   ```

### macOS/Linux 右键菜单

**Pandaone 不自动装 macOS/Linux 的右键菜单**（无标准化注册表机制）：

| 平台 | 替代方案 |
|---|---|
| macOS Finder | Automator 创建 Quick Action 跑 `pandaone audit "$@"` |
| Linux Nautilus | 写 `~/.local/share/nautilus/scripts/Pandaone Audit` shell 脚本 |
| Linux Nemo | 写 `.nemo_action` 文件 |
| Linux Dolphin | 写 `.desktop` ServiceMenu 文件 |

详见 [context-menu.md](context-menu.md)。

### PermissionError when locking

Pandaone 用 chmod / `attrib +r` 锁定文件。
- Linux/macOS：POSIX 标准行为
- Windows：`attrib +R`，普通用户透明
- **如果看到 PermissionError**——说明锁定生效（这是预期行为）

### PDF 中文显示为方块

PDF 导出依赖系统字体。Windows 默认带 `msyh.ttc`，macOS 自带 `PingFang.ttc`。
Linux 用户：
```bash
sudo apt install fonts-wqy-microhei fonts-noto-cjk
```

---

## 进阶：从源码安装（开发者）

```bash
git clone https://github.com/hellob1889/Pandaone-AI-Agent
cd Pandaone-AI-Agent
pip install -e .[dev]
pytest tests/ -v
# 342+ passed
```

**不推荐**普通用户用源码安装——没有隔离 venv，会污染系统 site-packages。

---

## 依赖说明

自动安装的依赖（全部纯 Python，跨平台，**无 C 扩展**）：

| 包 | 用途 |
|---|---|
| `watchdog>=3.0.0` | L2 文件监控（实时检测变更） |
| `openpyxl>=3.1.0` | Excel 导出 |
| `python-docx>=1.1.0` | Word 导出 |
| `reportlab>=4.0.0` | PDF 导出（含中文支持） |
| `pyyaml>=6.0` | YAML 导出 |

---

下一步：[快速开始](quickstart.md) | [命令参考](commands.md) | [MCP 集成](mcp-integration.md)