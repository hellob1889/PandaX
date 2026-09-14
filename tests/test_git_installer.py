    def test_fallback_to_common_paths(self, monkeypatch, tmp_path):
        """PATH 没有时,探测常见路径

        PR #28: Windows 路径扫描只在 Windows 平台生效。
        在 Linux/macOS CI 上,这个测试 skip(因为 sys.platform != win*)。
        """
        import sys as _sys
        if not _sys.platform.startswith("win"):
            pytest.skip("Windows-only fallback test (PR #28: Windows path scanning)")
        monkeypatch.setattr(shutil, "which", lambda name: None)
        fake_git = tmp_path / "fake_git.exe"
        fake_git.write_text("")
        monkeypatch.setattr("pandaone.git_installer._can_run_git", lambda p: str(fake_git) in p)
        monkeypatch.setattr("pandaone.git_installer.COMMON_GIT_PATHS_WINDOWS", [str(fake_git)])
        assert _find_git_executable() == str(fake_git)