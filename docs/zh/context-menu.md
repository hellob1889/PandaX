# 右键菜单集成（OS Context Menu）

PandaX 在 **Windows / macOS / Linux** 三大平台上都提供原生右键菜单集成。右键点击文件或文件夹 → 「PandaX」→ 选择 init / lock / unlock / status，**不用打开终端**。

## 一键启用

```bash
# 任意平台，自动检测 OS
pandax install-context

# 强制重新安装（仅 Windows）
pandax install-context --force

# 卸载
pandax uninstall-context
```

## 各平台细节

### Windows（HKCU 注册表级联菜单）

- **无需管理员**（HKCU 用户级）
- **3 个位置**：任意文件 / 文件夹 / 空白处
- **4 个动作**：Init / Lock / Unlock / Status（级联子菜单）
- **图标**：使用 `pandax.exe` 自带图标
- **幂等**：重复运行安全

手动运行：

```powershell
powershell -ExecutionPolicy Bypass -File installer\windows\install_context_menu.ps1 [-Force] [-DryRun]
```

DryRun 仅打印计划不写注册表（用于测试）。

### macOS（Automator Quick Action）

- **服务菜单**：Finder 右键 → 「服务」→ 「PandaX」
- **首次启用**：系统设置 → 键盘 → 快捷键 → 服务 → 勾选「文件和文件夹 → PandaX」
- **操作菜单**：弹窗选择 init / lock / unlock / status → Terminal.app 自动打开并执行

手动运行：

```bash
bash installer/macos/install_context_menu.sh
```

### Linux（Nautilus + Dolphin）

- **Nautilus（GNOME / Files）**：右键 → 「脚本」→ PandaX
- **Dolphin（KDE）**：右键 → Actions → PandaX → Init/Lock/Unlock/Status
- **自动检测桌面环境**（`$XDG_CURRENT_DESKTOP`）
- **用户级**：`~/.local/share/nautilus/scripts/` 和 `~/.local/share/kservices5/ServiceMenus/`

手动运行：

```bash
bash installer/linux/install_context_menu.sh
```

## 工作流示例

1. 拿到一个新项目
2. **右键项目文件夹** → PandaX → **init** → 初始化完成
3. **右键项目文件夹** → PandaX → **lock** → 所有文件锁住
4. AI 修改文件 → 通过 `pandax write --file X.py --reason ...` 审计
5. **右键项目文件夹** → PandaX → **status** → 查看审计状态

## 文件清单

```
installer/
├── windows/
│   ├── install_context_menu.ps1       # PowerShell 安装（HKCU）
│   └── uninstall_context_menu.ps1     # PowerShell 卸载
├── macos/
│   ├── install_context_menu.sh        # bash 安装
│   ├── uninstall_context_menu.sh      # bash 卸载
│   └── PandaX Lock.workflow/          # Automator Quick Action
│       └── Contents/
│           ├── Info.plist
│           └── document.wflow
└── linux/
    ├── install_context_menu.sh        # bash 安装（自动检测）
    ├── uninstall_context_menu.sh      # bash 卸载
    ├── nautilus/PandaX                # Nautilus 脚本
    └── dolphin/pandax-lock.desktop    # KDE 服务菜单
```

## 第一性原理

右键菜单让 PandaX 的核心机制（**所有改动必须经过审计**）变得**不可绕过**：

- 文件被 OS 锁住（`attrib +r` / `chmod 444`）
- AI Agent 想要修改，必须先 `pandax unlock` 或 `pandax write`
- 而 `pandax write` 强制 `reason / problem / approach` 三段必填
- 这强制 AI "想清楚再写"，不是"写完再编理由"

右键菜单不是便利功能，是**审计系统的最后一米**。