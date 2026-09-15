# ============================================================
# Pandaone AI Agent 一键硬隔离安装脚本 (Windows)
# ============================================================
#
# 第一性原理:
#   - "硬隔离" = 强制 venv, 不允许 pip install 到 system / user site-packages
#   - venv 路径固定到 %LOCALAPPDATA%\pandaone\, 与 wheel 文件同目录
#   - wheel 源永远从 GitHub API 拉最新 release (不硬编码 URL, 不从 PyPI 拉)
#   - 自动把 venv/Scripts 加到用户 PATH (持久化, 新 cmd 生效)
#
# 对抗式审查:
#   - 不支持 pip install --user 兜底 (硬隔离承诺不能开后门)
#   - 不依赖 pipx (用户机器可能没装, 多一个依赖)
#   - 不从 PyPI 拉 (用户明确要 "GitHub 下载")
#   - 已存在 venv 时直接复用 (升级而非重建)
#
# 用法:
#   # 默认: 装最新版
#   irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex
#
#   # 装指定版本
#   .\install.ps1 -Version v0.7.11
#
#   # 装本地 wheel (开发/调试用)
#   .\install.ps1 -WheelPath C:\path\to\pandaone_guard-0.7.11-py3-none-any.whl
#
[CmdletBinding()]
param(
    [string]$Version = "",
    [string]$WheelPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# ---- 配置 ----
$RepoOwner = "hellob1889"
$RepoName = "Pandaone-AI-Agent"
$InstallRoot = Join-Path $env:LOCALAPPDATA "pandaone"
$VenvDir = Join-Path $InstallRoot "venv"
$WheelCacheDir = Join-Path $InstallRoot "wheels"
$GitHubApi = "https://api.github.com/repos/$RepoOwner/$RepoName"

# ---- ANSI color helpers ----
function Write-Step($msg)  { Write-Host "▶ $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "✗ $msg" -ForegroundColor Red }

# ---- 1. 检测 Python ----
Write-Step "Detecting Python..."
$py = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $v = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v -match "Python (\d+)\.(\d+)") {
            $maj = [int]$Matches[1]; $min = [int]$Matches[2]
            if ($maj -ge 3 -and $min -ge 8) {
                $py = $cmd
                Write-OK "Python $maj.$min ($cmd)"
                break
            }
        }
    } catch {}
}
if (-not $py) {
    Write-Err "Python ≥ 3.8 not found."
    Write-Host "  Download: https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    Write-Host "  During install, CHECK 'Add Python to PATH'!" -ForegroundColor Yellow
    exit 1
}

# ---- 2. 创建隔离目录结构 ----
Write-Step "Creating isolation layout at $InstallRoot..."
foreach ($d in @($InstallRoot, $WheelCacheDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# ---- 3. 决定 wheel 源 ----
if ($WheelPath) {
    # 用户指定本地 wheel
    if (-not (Test-Path $WheelPath)) {
        Write-Err "Local wheel not found: $WheelPath"
        exit 1
    }
    $wheelFile = Copy-Item $WheelPath -Destination $WheelCacheDir -PassThru -Force
    Write-OK "Using local wheel: $($wheelFile.Name)"
} else {
    # 从 GitHub API 拉最新 release 的 wheel URL
    Write-Step "Fetching latest release from GitHub..."
    $apiUrl = if ($Version) {
        "$GitHubApi/releases/tags/$Version"
    } else {
        "$GitHubApi/releases/latest"
    }
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -Headers @{"Accept"="application/vnd.github+json"} -TimeoutSec 30
    } catch {
        Write-Err "Failed to fetch release from GitHub: $_"
        exit 1
    }
    Write-OK "Release: $($release.tag_name)  ($($release.published_at))"

    # 找 .whl asset
    $wheelAsset = $release.assets | Where-Object { $_.name -like "*.whl" } | Select-Object -First 1
    if (-not $wheelAsset) {
        Write-Err "No .whl asset found in release $($release.tag_name)"
        exit 1
    }

    $expectedSha = $wheelAsset.digest -replace "^sha256:", ""
    $wheelFile = Join-Path $WheelCacheDir $wheelAsset.name

    if ((Test-Path $wheelFile) -and -not $Force) {
        $actualSha = (Get-FileHash -Algorithm SHA256 -Path $wheelFile).Hash.ToLower()
        if ($actualSha -eq $expectedSha) {
            Write-OK "Wheel already cached: $($wheelAsset.name)"
        } else {
            Write-Warn "Cached wheel SHA256 mismatch, re-downloading"
            Remove-Item $wheelFile -Force
        }
    }
    if (-not (Test-Path $wheelFile)) {
        Write-Step "Downloading $($wheelAsset.name) ($($wheelAsset.size) bytes)..."
        Invoke-WebRequest -Uri $wheelAsset.browser_download_url -OutFile $wheelFile -UseBasicParsing
        $actualSha = (Get-FileHash -Algorithm SHA256 -Path $wheelFile).Hash.ToLower()
        if ($actualSha -ne $expectedSha) {
            Write-Err "SHA256 mismatch!"
            Write-Host "  expected: $expectedSha" -ForegroundColor Red
            Write-Host "  actual:   $actualSha"   -ForegroundColor Red
            exit 1
        }
        Write-OK "SHA256 verified: $actualSha"
    }
}

# ---- 4. 创建/复用 venv ----
if (Test-Path $VenvDir) {
    Write-Step "Reusing existing venv at $VenvDir"
} else {
    Write-Step "Creating venv at $VenvDir..."
    & $py -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Err "venv creation failed"
        exit 1
    }
    Write-OK "venv created"
}

$venvPython = Join-Path $VenvDir "Scripts\python.exe"
$venvPip = Join-Path $VenvDir "Scripts\pip.exe"

# ---- 5. pip install 到 venv (不碰任何 site-packages) ----
Write-Step "Installing $($wheelFile.Name) into venv..."
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet --upgrade $wheelFile
if ($LASTEXITCODE -ne 0) {
    Write-Err "pip install failed inside venv"
    exit 1
}
Write-OK "Installed in venv"

# ---- 6. 把 venv/Scripts 加到用户 PATH (持久化) ----
$venvScripts = Join-Path $VenvDir "Scripts"
$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentUserPath -notlike "*$venvScripts*") {
    Write-Step "Adding $venvScripts to user PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$currentUserPath;$venvScripts", "User")
    Write-OK "PATH updated (new shells will pick up)"
} else {
    Write-OK "$venvScripts already in PATH"
}

# ---- 7. 验证 ----
Write-Step "Verifying..."
$versionOutput = & $venvPython -m pandaone --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Err "pandaone --version failed: $versionOutput"
    exit 1
}
Write-OK "pandaone $versionOutput"

# venv 里 importlib.metadata 验证（确认真实装的是 wheel 的版本）
$importedVer = & $venvPython -c "import importlib.metadata; print(importlib.metadata.version('pandaone-guard'))"
Write-OK "importlib.metadata.version = $importedVer"

# ---- 8. 提示下一步 ----
Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Installation complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "安装位置 / Install location:" -ForegroundColor Cyan
Write-Host "  venv:  $VenvDir"
Write-Host "  wheel: $wheelFile"
Write-Host ""
Write-Host "下一步 / Next steps (新开 cmd/PowerShell):" -ForegroundColor Cyan
Write-Host "  pandaone doctor              # 环境检查"
Write-Host "  pandaone install-context     # 安装 Windows 右键菜单"
Write-Host "  pandaone install-hook        # 安装 git pre-commit hook"
Write-Host "  pandaone --help              # 全部命令"
Write-Host ""
Write-Host "升级 / Upgrade:" -ForegroundColor Cyan
Write-Host "  irm https://raw.githubusercontent.com/$RepoOwner/$RepoName/main/install.ps1 | iex"
Write-Host ""
Write-Host "完全卸载 / Uninstall:" -ForegroundColor Cyan
Write-Host "  Remove-Item -Recurse '$InstallRoot'"
Write-Host "  # 然后手动从 PATH 移除: $venvScripts"
