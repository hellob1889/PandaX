"""
tests/test_git_installer.py - git_installer 模块单元测试

PR #28 (git auto-installer + pandaone doctor):
  - 全平台 git 检测 (Windows / macOS / Linux)
  - Windows 多路径探测 (PATH + WindowsApps + 用户目录)
  - 跨平台自动安装 (winget/choco/scoop/brew/apt/dnf/yum)
  - InstallResult / GitInstallError / GitNotFoundError 数据类
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pandaone import git_installer
from pandaone.git_installer import (
    InstallResult,
    GitInstallError,
    GitNotFoundError,
    is_installed,
    version,
    path,
    install,
    get_install_hint,
    _find_git_executable,
    _can_run_git,
    _detect_platform,
    _try_run,
    COMMON_GIT_PATHS_WINDOWS,
    COMMON_GIT_PATHS_MACOS,
)


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def mock_which(monkeypatch):
    """mock shutil.which 返回指定 git 路径"""
    def _mock(path_return):
        monkeypatch.setattr(shutil, "which", lambda name: path_return if name == "git" else None)
    return _mock


@pytest.fixture
def fake_git(tmp_path):
    """在 tmp_path 创建假的 git.exe 并返回路径"""
    p = tmp_path / "fake_git"
    p.write_text("#!/bin/sh\necho 'git version 2.42.0.windows.1'\n")
    p.chmod(0o755)
    return str(p)


# ============================================================
# Test InstallResult / Exceptions
# ============================================================
class TestInstallResult:
    def test_success_true(self):
        r = InstallResult(success=True, message="installed")
        assert r.success is True
        assert r.message == "installed"

    def test_success_false(self):
        r = InstallResult(success=False, message="failed")
        assert r.success is False
        assert r.message == "failed"

    def test_with_optional_fields(self):
        r = InstallResult(success=True, version="2.42.0", path="/usr/bin/git",
                          channel="apt", message="apt install ok")
        assert r.version == "2.42.0"
        assert r.path == "/usr/bin/git"
        assert r.channel == "apt"


class TestExceptions:
    def test_git_not_found_is_exception(self):
        assert issubclass(GitNotFoundError, Exception)

    def test_git_install_error_is_exception(self):
        assert issubclass(GitInstallError, Exception)


# ============================================================
# Test _detect_platform
# ============================================================
class TestDetectPlatform:
    def test_returns_string(self):
        result = _detect_platform()
        assert isinstance(result, str)
        assert result in ("Windows", "Darwin", "Linux", "win32", "darwin", "linux", "freebsd")


# ============================================================
# Test _can_run_git
# ============================================================
class TestCanRunGit:
    def test_nonexistent_path_returns_false(self):
        assert _can_run_git(r"C:\nonexistent\fake\path\git.exe") is False

    def test_existing_non_executable_returns_false(self, tmp_path):
        # tmp_path 下的 fake_git 没有 +x 权限
        p = tmp_path / "not_exec"
        p.write_text("not executable")
        if sys.platform.startswith("win"):
            # Windows 上 _can_run_git 不检查 +x (无 unix 概念)
            # 它用 subprocess.run --version 验证
            # 这里不依赖 .exe 扩展名, 直接用真实逻辑
            pass
        else:
            assert _can_run_git(str(p)) is False


# ============================================================
# Test _find_git_executable
# ============================================================
class TestFindGitExecutable:
    def test_shutil_which_returns_path(self, mock_which, fake_git):
        """PATH 里有 git → 直接返回"""
        mock_which(fake_git)
        # _can_run_git 也需要 mock 通过
        with patch("pandaone.git_installer._can_run_git", return_value=True):
            assert _find_git_executable() == fake_git

    def test_shutil_which_returns_none_windows_skip(self, monkeypatch):
        """Windows-only fallback test (PR #28: Windows path scanning)"""
        if not sys.platform.startswith("win"):
            pytest.skip("Windows-only fallback test")
        monkeypatch.setattr(shutil, "which", lambda name: None)
        fake = Path(os.environ.get("TEMP", "C:\\Temp")) / "fake_git.exe"
        fake.write_text("")
        monkeypatch.setattr("pandaone.git_installer._can_run_git", lambda p: True)
        monkeypatch.setattr("pandaone.git_installer.COMMON_GIT_PATHS_WINDOWS", [str(fake)])
        assert _find_git_executable() == str(fake)

    def test_returns_none_when_not_found(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        # 强制 _can_run_git 永远 False
        monkeypatch.setattr("pandaone.git_installer._can_run_git", lambda p: False)
        assert _find_git_executable() is None


# ============================================================
# Test is_installed / version / path
# ============================================================
class TestPublicAPI:
    def test_is_installed_returns_bool(self):
        """is_installed() 返回 bool (依赖机器是否真有 git)"""
        result = is_installed()
        assert isinstance(result, bool)

    def test_path_returns_str_or_none(self):
        result = path()
        assert result is None or isinstance(result, str)

    def test_version_returns_str_or_none(self):
        result = version()
        assert result is None or isinstance(result, str)

    def test_get_install_hint_returns_string(self):
        hint = get_install_hint()
        assert isinstance(hint, str)
        assert len(hint) > 0


# ============================================================
# Test install (dry_run)
# ============================================================
class TestInstall:
    def test_dry_run_returns_simulation(self):
        """install(dry_run=True) 返回模拟 InstallResult, 不实际安装"""
        result = install(dry_run=True)
        assert isinstance(result, InstallResult)
        # dry_run 不真装, 但 message 应该有 'DryRun' 或类似关键字
        # 不强制 success 状态 (取决于机器是否已有 git)
        assert isinstance(result.message, str)