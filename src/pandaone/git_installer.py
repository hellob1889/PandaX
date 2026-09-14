# -*- coding: utf-8 -*-
"""
git_installer.py — Pandaone AI Agent 跨平台 git 探测与自动安装
=====================================================

第一性原理:
  - pandaone 的 L2 (watchdog 回滚) 和 L3 (pre-commit hook) 强依赖 git 命令。
  - 用户在新机器 pip install 后立即跑 pandaone init/watch/ci,git 缺失会
    静默降级(之前行为),用户感知不到防护缺了一半。
  - 这个模块的目标:**git 缺失 → 自动探测 → 自动安装 → 清晰告知用户**。
  - 绝不静默降级(之前的 [WARN] write_warn_no_git 行为是错的)。

对抗式审查:
  - Q: 自动装系统包是否越权?
    A: 只装 git 一个命令,且只在该命令缺失时触发。用户可用
       PANDAONE_SKIP_GIT_CHECK=1 跳过自动安装。
  - Q: 跨平台装包会破坏用户系统吗?
    A: 使用各平台标准的包管理器 (apt/yum/brew/winget/choco),不下
       载第三方脚本,不改 PATH(git 安装器自己会改)。
  - Q: subprocess 卡死怎么办?
    A: 全部带 timeout=300 (5 分钟),超时返回明确错误。
  - Q: CI 环境会误触发吗?
    A: CI runner 自带 git,`is_installed()` 返回 True,不走到 install 分支。
       测试用 PANDAONE_SKIP_GIT_CHECK=1 显式跳过。
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# 异常
# ============================================================

class GitNotFoundError(Exception):
    """git 未安装且无法自动安装"""

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


class GitInstallError(Exception):
    """git 自动安装失败"""

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


# ============================================================
# 数据类
# ============================================================

@dataclass
class InstallResult:
    """git 安装结果"""
    success: bool
    version: Optional[str] = None
    path: Optional[str] = None
    channel: Optional[str] = None
    message: str = ""
    log: List[str] = field(default_factory=list)


# ============================================================
# 常见 Windows git 安装路径(当 PATH 被劫持 / 用户级安装时找不到)
# ============================================================

COMMON_GIT_PATHS_WINDOWS = [
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
]

COMMON_GIT_PATHS_MACOS = [
    "/usr/bin/git",
    "/opt/homebrew/bin/git",
    "/usr/local/bin/git",
    "/Library/Developer/CommandLineTools/usr/bin/git",
]


def _find_git_executable() -> Optional[str]:
    """多渠道找 git 可执行文件: PATH → 常见安装路径 → winget 已知位置。"""
    p = shutil.which("git")
    if p and _can_run_git(p):
        return p

    candidates = []
    if sys.platform.startswith("win"):
        candidates.extend(COMMON_GIT_PATHS_WINDOWS)
        local_programs = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "bin")
        if os.path.isdir(local_programs):
            candidates.append(os.path.join(local_programs, "git.exe"))
        scoop = os.path.join(os.environ.get("USERPROFILE", ""), "scoop", "apps", "git", "current", "bin")
        if os.path.isdir(scoop):
            candidates.append(os.path.join(scoop, "git.exe"))
        for prefix in ["D:\\", "C:\\"]:
            for sub in ["软件", "Program Files", "Tools", "dev"]:
                p2 = os.path.join(prefix, sub, "Git", "cmd", "git.exe")
                if os.path.isfile(p2):
                    candidates.append(p2)
                p3 = os.path.join(prefix, sub, "Git", "bin", "git.exe")
                if os.path.isfile(p3):
                    candidates.append(p3)
    elif sys.platform == "darwin":
        candidates.extend(COMMON_GIT_PATHS_MACOS)

    for c in candidates:
        if os.path.isfile(c) and _can_run_git(c):
            return c
    return None


def _can_run_git(git_exe: str) -> bool:
    """测试给定路径的 git 是否可执行 (返回 0)"""
    try:
        r = subprocess.run(
            [git_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, PermissionError):
        return False


def is_installed() -> bool:
    """探测 git 是否已安装(不抛异常)。"""
    return _find_git_executable() is not None


def version() -> Optional[str]:
    """返回 git 版本字符串(如 'git version 2.43.0'),git 不在则 None。"""
    git_exe = _find_git_executable()
    if not git_exe:
        return None
    try:
        result = subprocess.run(
            [git_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def path() -> Optional[str]:
    """git 可执行文件路径 (PATH 或常见安装路径),None 表示未安装"""
    return _find_git_executable()


# ============================================================
# 2. 自动安装
# ============================================================

def _detect_platform() -> str:
    """返回 'Windows' / 'Darwin' / 'Linux'"""
    p = sys.platform
    if p.startswith("win"):
        return "Windows"
    if p.startswith("darwin"):
        return "Darwin"
    if p.startswith("linux") or p.startswith("freebsd"):
        return "Linux"
    return p


def _try_run(cmd: List[str], timeout: int = 300, log: List[str] = None) -> subprocess.CompletedProcess:
    """
    执行命令并实时输出 stdout/stderr 到 log 列表。

    重要: 把 WindowsApps 路径加到子进程 env PATH,
    解决 winget / Windows Store app 在子进程里找不到的问题。
    """
    if log is None:
        log = []
    log.append(f"$ {' '.join(cmd)}")

    env = os.environ.copy()
    extra_paths = []
    if sys.platform.startswith("win"):
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            wa = os.path.join(local_app, "Microsoft", "WindowsApps")
            if os.path.isdir(wa) and wa not in env.get("PATH", ""):
                extra_paths.append(wa)
    if extra_paths:
        env["PATH"] = os.pathsep.join(extra_paths + [env.get("PATH", "")])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.stdout:
            log.append(f"  stdout: {result.stdout.strip()[:500]}")
        if result.stderr:
            log.append(f"  stderr: {result.stderr.strip()[:500]}")
        log.append(f"  exit: {result.returncode}")
        return result
    except subprocess.TimeoutExpired as e:
        log.append(f"  TIMEOUT after {timeout}s")
        raise GitInstallError(f"install timeout ({timeout}s): {' '.join(cmd)}") from e
    except FileNotFoundError as e:
        log.append(f"  Command not found: {e}")
        raise GitInstallError(f"command not found: {cmd[0]}") from e


def _install_windows(log: List[str]) -> InstallResult:
    """Windows 平台:winget > choco > manual"""
    if shutil.which("winget"):
        log.append("channel: winget")
        result = _try_run(
            ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget",
             "--accept-package-agreements", "--accept-source-agreements"],
            timeout=600,
            log=log,
        )
        if result.returncode == 0 and is_installed():
            return InstallResult(
                success=True, version=version(), path=path(),
                channel="winget", message="winget install Git.Git succeeded", log=log,
            )
        log.append("winget install failed, trying choco")

    if shutil.which("choco"):
        log.append("channel: choco")
        result = _try_run(["choco", "install", "git", "-y"], timeout=600, log=log)
        if result.returncode == 0 and is_installed():
            return InstallResult(
                success=True, version=version(), path=path(),
                channel="choco", message="choco install git succeeded", log=log,
            )
        log.append("choco install failed")

    raise GitInstallError(
        "Windows auto-install failed: winget/choco not found.\n"
        "Please install manually (one of):\n"
        "  1. winget install --id Git.Git -e\n"
        "  2. choco install git\n"
        "  3. https://git-scm.com/download/win\n"
        f"Detailed log:\n{chr(10).join(log)}"
    )


def _install_macos(log: List[str]) -> InstallResult:
    """macOS: brew > xcode-select --install"""
    if shutil.which("brew"):
        log.append("channel: brew")
        result = _try_run(["brew", "install", "git"], timeout=900, log=log)
        if result.returncode == 0 and is_installed():
            return InstallResult(
                success=True, version=version(), path=path(),
                channel="brew", message="brew install git succeeded", log=log,
            )
        log.append("brew install failed")

    if shutil.which("xcode-select"):
        log.append("channel: xcode-select")
        try:
            subprocess.Popen(
                ["xcode-select", "--install"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            log.append(f"xcode-select failed: {e}")
        raise GitInstallError(
            "macOS Xcode Command Line Tools installer triggered (system dialog).\n"
            "Please click Install in the popup, then re-run pandaone.\n"
            "Or use Homebrew: brew install git\n"
            f"Log: {chr(10).join(log)}"
        )

    raise GitInstallError(
        "macOS auto-install failed: brew/xcode-select not found.\n"
        "Please install manually:\n"
        "  1. xcode-select --install (recommended, dialog)\n"
        "  2. /usr/bin/ruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\" && brew install git\n"
        "  3. https://git-scm.com/download/mac\n"
        f"Log: {chr(10).join(log)}"
    )


def _install_linux(log: List[str]) -> InstallResult:
    """Linux: apt > yum > dnf > manual"""
    if shutil.which("apt-get"):
        log.append("channel: apt-get")
        try:
            _try_run(["sudo", "-n", "apt-get", "update"], timeout=120, log=log)
            _try_run(["sudo", "-n", "apt-get", "install", "-y", "git"], timeout=600, log=log)
            if is_installed():
                return InstallResult(
                    success=True, version=version(), path=path(),
                    channel="apt-get", message="apt-get install git succeeded", log=log,
                )
        except GitInstallError as e:
            log.append(f"apt-get failed: {e}")
        log.append("apt-get install failed, trying yum")

    if shutil.which("yum"):
        log.append("channel: yum")
        try:
            _try_run(["sudo", "-n", "yum", "install", "-y", "git"], timeout=600, log=log)
            if is_installed():
                return InstallResult(
                    success=True, version=version(), path=path(),
                    channel="yum", message="yum install git succeeded", log=log,
                )
        except GitInstallError as e:
            log.append(f"yum failed: {e}")
        log.append("yum install failed, trying dnf")

    if shutil.which("dnf"):
        log.append("channel: dnf")
        try:
            _try_run(["sudo", "-n", "dnf", "install", "-y", "git"], timeout=600, log=log)
            if is_installed():
                return InstallResult(
                    success=True, version=version(), path=path(),
                    channel="dnf", message="dnf install git succeeded", log=log,
                )
        except GitInstallError as e:
            log.append(f"dnf failed: {e}")
        log.append("dnf install failed")

    raise GitInstallError(
        "Linux auto-install failed: apt-get/yum/dnf not found, or sudo requires password.\n"
        "Please install manually:\n"
        "  Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y git\n"
        "  CentOS/RHEL:   sudo yum install -y git\n"
        "  Fedora:        sudo dnf install -y git\n"
        "  Arch:          sudo pacman -S git\n"
        "  Source:        https://git-scm.com/download/linux\n"
        f"Log: {chr(10).join(log)}"
    )


def install(dry_run: bool = False) -> InstallResult:
    """自动安装 git(如果缺失)。"""
    if is_installed():
        return InstallResult(
            success=True, version=version(), path=path(),
            message="git already installed",
        )

    if dry_run:
        return InstallResult(
            success=False,
            message="dry-run: git not installed, no installation attempted",
        )

    log: List[str] = []
    plat = _detect_platform()
    log.append(f"platform: {plat}")
    log.append(f"python: {platform.python_version()}")

    try:
        if plat == "Windows":
            return _install_windows(log)
        elif plat == "Darwin":
            return _install_macos(log)
        elif plat == "Linux":
            return _install_linux(log)
        else:
            raise GitInstallError(
                f"Unsupported platform: {plat}. Please install git manually: https://git-scm.com/downloads"
            )
    except GitInstallError:
        raise
    except Exception as e:
        raise GitInstallError(
            f"Unexpected install error: {type(e).__name__}: {e}\n"
            f"Log: {chr(10).join(log)}"
        ) from e


# ============================================================
# 3. 手动安装指引
# ============================================================

def get_install_hint() -> str:
    """返回当前平台的手动安装指引(用于 doctor 输出和安装失败 fallback)"""
    plat = _detect_platform()
    if plat == "Windows":
        return (
            "Manual git install on Windows:\n"
            "  1. winget install --id Git.Git -e\n"
            "  2. choco install git\n"
            "  3. Download from https://git-scm.com/download/win"
        )
    elif plat == "Darwin":
        return (
            "Manual git install on macOS:\n"
            "  1. xcode-select --install (system dialog)\n"
            "  2. brew install git\n"
            "  3. Download from https://git-scm.com/download/mac"
        )
    elif plat == "Linux":
        return (
            "Manual git install on Linux:\n"
            "  Debian/Ubuntu: sudo apt-get install -y git\n"
            "  CentOS/RHEL:   sudo yum install -y git\n"
            "  Fedora:        sudo dnf install -y git\n"
            "  Arch:          sudo pacman -S git\n"
            "  Source:        https://git-scm.com/download/linux"
        )
    else:
        return f"Unrecognized platform {plat}. Please visit https://git-scm.com/downloads to install manually"
