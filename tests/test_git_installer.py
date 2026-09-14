# -*- coding: utf-8 -*-
"""
test_git_installer.py — PR #28 git_installer 模块单元测试
"""
import os
import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pandaone.git_installer import (
    is_installed, version, path, install,
    _find_git_executable, _can_run_git, _detect_platform,
    get_install_hint, GitInstallError, GitNotFoundError,
)


class TestDetection:
    def test_is_installed_returns_bool(self):
        assert isinstance(is_installed(), bool)

    def test_version_returns_string_or_none(self):
        v = version()
        assert v is None or isinstance(v, str)
        if v is not None:
            assert v.startswith("git version")

    def test_path_returns_string_or_none(self):
        p = path()
        assert p is None or isinstance(p, str)
        if p is not None:
            assert "git" in p.lower()

    def test_consistency(self):
        installed = is_installed()
        v, p = version(), path()
        if installed:
            assert v is not None and p is not None
        else:
            assert v is None and p is None


class TestFindExecutable:
    def test_path_first(self, monkeypatch):
        fake_git = r"C:\fake\path\git.exe"
        monkeypatch.setattr(shutil, "which", lambda name: fake_git if name == "git" else None)
        with mock.patch("pandaone.git_installer._can_run_git", return_value=True):
            assert _find_git_executable() == fake_git

    def test_fallback_to_common_paths(self, monkeypatch, tmp_path):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        fake_git = tmp_path / "fake_git.exe"
        fake_git.write_text("")
        monkeypatch.setattr("pandaone.git_installer._can_run_git", lambda p: str(fake_git) in p)
        monkeypatch.setattr("pandaone.git_installer.COMMON_GIT_PATHS_WINDOWS", [str(fake_git)])
        assert _find_git_executable() == str(fake_git)

    def test_returns_none_when_nothing_found(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        monkeypatch.setattr("pandaone.git_installer.COMMON_GIT_PATHS_WINDOWS", [])
        monkeypatch.setattr("pandaone.git_installer.COMMON_GIT_PATHS_MACOS", [])
        monkeypatch.setattr("pandaone.git_installer._can_run_git", lambda p: False)
        assert _find_git_executable() is None


class TestCanRunGit:
    def test_valid_git_returns_true(self):
        git_exe = shutil.which("git")
        if not git_exe:
            pytest.skip("git not in PATH")
        assert _can_run_git(git_exe) is True

    def test_nonexistent_returns_false(self):
        assert _can_run_git(r"C:\nonexistent\fake_git.exe") is False


class TestPlatformDetection:
    def test_returns_string(self):
        assert isinstance(_detect_platform(), str)
        assert len(_detect_platform()) > 0


class TestInstallDryRun:
    def test_dry_run_when_missing(self, monkeypatch):
        monkeypatch.setattr("pandaone.git_installer._find_git_executable", lambda: None)
        result = install(dry_run=True)
        assert result.success is False
        assert "dry-run" in result.message.lower()

    def test_dry_run_when_present(self, monkeypatch):
        monkeypatch.setattr("pandaone.git_installer._find_git_executable", lambda: r"C:\fake\git.exe")
        monkeypatch.setattr("pandaone.git_installer.is_installed", lambda: True)
        monkeypatch.setattr("pandaone.git_installer.version", lambda: "git version 2.43.0")
        monkeypatch.setattr("pandaone.git_installer.path", lambda: r"C:\fake\git.exe")
        assert install(dry_run=True).success is True


class TestGetInstallHint:
    def test_returns_string_with_url(self):
        hint = get_install_hint()
        assert isinstance(hint, str)
        assert len(hint) > 20


class TestInstallFailure:
    def test_install_raises_when_no_channel(self, monkeypatch):
        monkeypatch.setattr("pandaone.git_installer._find_git_executable", lambda: None)
        monkeypatch.setattr("pandaone.git_installer.is_installed", lambda: False)
        monkeypatch.setattr("pandaone.git_installer.shutil.which", lambda name: None)
        with pytest.raises(GitInstallError):
            install()


class TestExceptions:
    def test_git_install_error_has_hint(self):
        e = GitInstallError("test error", "test hint")
        assert str(e) == "test error"
        assert e.hint == "test hint"

    def test_git_install_error_no_hint(self):
        e = GitInstallError("test error")
        assert str(e) == "test error"
        assert getattr(e, "hint", "") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
