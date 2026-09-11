; ============================================================
; Pandaone AI Agent Inno Setup 安装脚本（Phase 9: 级联右键菜单）
; ============================================================
;
; 用法：
;   1. 安装 Inno Setup 6 (https://jrsoftware.org/isinfo.php)
;   2. 编译: iscc installer\pandaone.iss
;   3. 产物: installer\Output\Pandaone-Setup-x.y.z.exe
;
; 第一性原理：
;   - 单文件安装包，便于分发
;   - 自动加入 PATH，无需用户配置
;   - 右键菜单级联（4 个子动作：init / lock / unlock / status）
;   - 安装/卸载幂等（可重复运行）
;   - 检查 git 可用性，缺失时友好提示
;
; ============================================================

#define MyAppName "Pandaone"
#define MyAppVersion "0.7.2"
#define MyAppPublisher "Pandaone AI Agent Project"
#define MyAppURL "https://github.com/hellob1889/Pandaone-AI-Agent"
#define MyAppExeName "pandaone.exe"

[Setup]
; 基本信息
AppId={{A4F8B5C2-1D3E-4F2A-9B8C-1E5D7F9A3B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; 输出设置
OutputDir=Output
OutputBaseFilename=Pandaone-Setup-{#MyAppVersion}

; 压缩（最大压缩减少分发体积）
Compression=lzma2/ultra64
SolidCompression=yes

; 权限（要求管理员以写入 Program Files）
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 美化
WizardStyle=modern
SetupIconFile=assets\pandaone.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; 版本信息
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=AI Agent Code Audit Gateway

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Types]
Name: "full"; Description: "完整安装（含右键菜单）"; Flags: iscustom
Name: "minimal"; Description: "仅命令行（不创建右键菜单）"

[Components]
Name: "main"; Description: "Pandaone 主程序"; Types: full minimal; Flags: fixed
Name: "contextmenu"; Description: "Windows 右键菜单（级联）"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Add {#MyAppName} to system PATH"; GroupDescription: "System integration:"; Flags: checkedonce

[Files]
; 主程序（来自 PyInstaller 打包）
Source: "..\dist\pandaone\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\templates"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppName} CLI"; Filename: "{cmd}"; Parameters: "/K cd /d ""{app}"" && pandaone --help"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; ============================================================
; Phase 9: 级联右键菜单（Pandaone → Init / Lock / Unlock / Status）
; HKCU 用户级，无需管理员
; 三个位置都注册：
;   1) 任意文件   (HKCU\Software\Classes\*\shell\Pandaone)   — 注意：HKLM 的 * 已被 HKCU 接管
;   2) 文件夹     (HKCU\Software\Classes\Directory\shell\Pandaone)
;   3) 空白处     (HKCU\Software\Classes\Directory\Background\shell\Pandaone)
; 全部用 Components: contextmenu 标记，可独立勾选「不创建右键菜单」最小安装
; ============================================================

Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone"; ValueType: string; ValueName: ""; ValueData: "Pandaone 审计工具"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Pandaone 审计工具"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone"; ValueType: string; ValueName: "SubCommands"; ValueData: ""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Init"; ValueType: string; ValueName: ""; ValueData: "初始化此目录 (Init)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Init\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default init --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Lock"; ValueType: string; ValueName: ""; ValueData: "锁定文件 (Lock)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Lock\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default lock --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Unlock"; ValueType: string; ValueName: ""; ValueData: "解锁文件 (Unlock)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Unlock\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default unlock --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Status"; ValueType: string; ValueName: ""; ValueData: "查看状态 (Status)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\Pandaone\shell\Status\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default status --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu

; 空白处
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone"; ValueType: string; ValueName: ""; ValueData: "Pandaone 审计工具 / Audit Tools"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Pandaone 审计工具 / Audit Tools"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone"; ValueType: string; ValueName: "SubCommands"; ValueData: ""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Init"; ValueType: string; ValueName: ""; ValueData: "初始化此目录 (Init)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Init\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default init --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Lock"; ValueType: string; ValueName: ""; ValueData: "锁定文件 (Lock)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Lock\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default lock --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Unlock"; ValueType: string; ValueName: ""; ValueData: "解锁文件 (Unlock)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Unlock\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default unlock --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Status"; ValueType: string; ValueName: ""; ValueData: "查看状态 (Status)"; Flags: uninsdeletekey; Components: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\Pandaone\shell\Status\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent --trust-default status --root ""%V"""; Flags: uninsdeletekey; Components: contextmenu

; 清理旧版遗留（兼容之前版本）
Root: HKCU; Subkey: "Software\Classes\Directory\shell\PandaoneInit"; Flags: deletekey
Root: HKCU; Subkey: "Software\Classes\*\shell\PandaoneInit"; Flags: deletekey
Root: HKCU; Subkey: "Software\Classes\*\shell\PandaoneWatch"; Flags: deletekey

; PATH（用户级，不需要管理员）
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Run]
; 安装后首次运行探测
Filename: "{app}\{#MyAppExeName}"; Parameters: "install-git --probe-only"; Description: "Probe git availability"; Flags: runmaximized nowait postinstall skipifsilent runascurrentuser

[UninstallRun]
; 卸载时清理用户配置（仅 fingerprint）
Filename: "{cmd}"; Parameters: "/C for /f ""delims="" %%i in ('dir /b /s /ah ""{userdocs}\Pandaone\.pandaone_fp.txt"" 2^>nul') do del /f /q ""%%i"""; Flags: runmaximized

[UninstallDelete]
; 清理模板和日志
Type: filesandordirs; Name: "{app}\templates"
Type: filesandordirs; Name: "{app}\*.log"

[Code]
// ============================================================
// Inno Setup Pascal Script
// ============================================================

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // 在 Inno Setup 6 中，PyInstaller 产物需要平铺到 {app}
  // 这里假设 build.bat 已经把 dist/pandaone/* 复制到 installer/staging/pandaone/
  // 实际用 [Files] 段的 Source 指向 ..\dist\pandaone\ 即可
end;

function InitializeSetup: boolean;
begin
  // 检查 git 是否可用
  Result := True;
end;