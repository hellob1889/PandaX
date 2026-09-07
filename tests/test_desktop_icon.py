"""方案 A: 测试 desktop.ini + 图标切换功能。

第一性原则:
- 验证 desktop.ini 在 lock 时被正确写入
- 验证 unlock 时被正确清理
- 验证 ICO 文件被正确复制到 .pandax/icon/
- 验证 desktop.ini 内容引用相对路径(卸载 pandax 后图标仍能显示)
- 验证非 Windows 平台 silent skip
- 验证 lock 主流程不被图标问题阻塞
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# === 单元测试: desktop_icon 模块 ===

class TestDesktopIconUnit:
    """desktop_icon.py 单元测试。"""

    def test_read_ico_from_dev_path(self, tmp_path: Path):
        """开发模式:ICO 在 src/pandax/ 下,应能读取。"""
        from pandax.desktop_icon import _read_ico_from_package
        # 实际 ICO 在 src/pandax/ 下,直接读
        ico_bytes = _read_ico_from_package("pandax_locked.ico")
        assert len(ico_bytes) > 1000, f"ICO 文件太小: {len(ico_bytes)} bytes"
        # ICO 文件头检查
        assert ico_bytes[:4] == b"\x00\x00\x01\x00", "不是有效的 ICO 文件头"

    def test_read_ico_unlocked(self):
        """未锁定 ICO 也能读取。"""
        from pandax.desktop_icon import _read_ico_from_package
        ico_bytes = _read_ico_from_package("pandax_unlocked.ico")
        assert len(ico_bytes) > 1000
        assert ico_bytes[:4] == b"\x00\x00\x01\x00"

    def test_apply_creates_desktop_ini(self, tmp_path: Path):
        """apply_desktop_icon 写入 desktop.ini。"""
        from pandax.desktop_icon import apply_desktop_icon
        # 模拟 Windows 平台
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            ok, msg = apply_desktop_icon(tmp_path, "locked")
        assert ok is True, f"apply 失败: {msg}"
        assert "[OK]" in msg
        # 验证 desktop.ini 存在
        desktop_ini = tmp_path / "desktop.ini"
        assert desktop_ini.exists(), "desktop.ini 未创建"
        # 验证内容
        content = desktop_ini.read_text(encoding="utf-8")
        assert "[.ShellClassInfo]" in content
        assert "IconFile=" in content
        assert "pandax_locked.ico" in content
        assert "IconIndex=0" in content

    def test_apply_uses_relative_path(self, tmp_path: Path):
        """IconFile 必须用相对路径(不绑死绝对路径)。"""
        from pandax.desktop_icon import apply_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            apply_desktop_icon(tmp_path, "locked")
        content = (tmp_path / "desktop.ini").read_text(encoding="utf-8")
        # 必须包含 .pandax\icon\pandax_locked.ico(相对)
        assert ".pandax" in content
        assert "icon" in content
        # 不能包含绝对路径驱动器
        assert ":\\" not in content or "IconFile=.pandax" in content

    def test_apply_copies_ico_to_pandax_dir(self, tmp_path: Path):
        """ICO 复制到 .pandax/icon/ 而不是污染用户目录。"""
        from pandax.desktop_icon import apply_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            apply_desktop_icon(tmp_path, "locked")
        icon_path = tmp_path / ".pandax" / "icon" / "pandax_locked.ico"
        assert icon_path.exists(), f"ICO 未复制到 {icon_path}"
        # 不应直接复制到 tmp_path 根目录
        assert not (tmp_path / "pandax_locked.ico").exists()

    def test_apply_unlocked_uses_correct_ico(self, tmp_path: Path):
        """unlocked 状态使用 pandax_unlocked.ico。"""
        from pandax.desktop_icon import apply_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            apply_desktop_icon(tmp_path, "unlocked")
        content = (tmp_path / "desktop.ini").read_text(encoding="utf-8")
        assert "pandax_unlocked.ico" in content
        assert (tmp_path / ".pandax" / "icon" / "pandax_unlocked.ico").exists()

    def test_remove_cleans_desktop_ini(self, tmp_path: Path):
        """remove_desktop_icon 清理 desktop.ini。"""
        from pandax.desktop_icon import apply_desktop_icon, remove_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            apply_desktop_icon(tmp_path, "locked")
            assert (tmp_path / "desktop.ini").exists()
            ok, msg = remove_desktop_icon(tmp_path)
        assert ok is True, f"remove 失败: {msg}"
        assert not (tmp_path / "desktop.ini").exists(), "desktop.ini 未清理"
        assert not (tmp_path / ".pandax" / "icon").exists(), ".pandax/icon 未清理"

    def test_remove_idempotent(self, tmp_path: Path):
        """无 desktop.ini 时 remove 也是 idempotent。"""
        from pandax.desktop_icon import remove_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            ok, msg = remove_desktop_icon(tmp_path)
        assert ok is True
        # Bug #20 fix: 改用 i18n key 检测（不再硬编码中文）
        # 期望是 desktop_icon_clean_none 或 desktop_icon_skip
        assert "No cleanup needed" in msg or "无需清理" in msg or "[SKIP]" in msg

    def test_apply_non_windows_skip(self, tmp_path: Path):
        """非 Windows 平台 silent skip。"""
        from pandax.desktop_icon import apply_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "linux"
            ok, msg = apply_desktop_icon(tmp_path, "locked")
        assert ok is True
        assert "[SKIP]" in msg
        assert not (tmp_path / "desktop.ini").exists()

    def test_remove_non_windows_skip(self, tmp_path: Path):
        """非 Windows 平台 unlock 也 skip。"""
        from pandax.desktop_icon import remove_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "darwin"
            ok, msg = remove_desktop_icon(tmp_path)
        assert ok is True
        assert "[SKIP]" in msg

    def test_apply_idempotent(self, tmp_path: Path):
        """多次 apply 不会出错。"""
        from pandax.desktop_icon import apply_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            ok1, _ = apply_desktop_icon(tmp_path, "locked")
            ok2, _ = apply_desktop_icon(tmp_path, "locked")
            ok3, _ = apply_desktop_icon(tmp_path, "locked")
        assert ok1 and ok2 and ok3

    def test_has_desktop_icon(self, tmp_path: Path):
        """has_desktop_icon 正确探测。"""
        from pandax.desktop_icon import apply_desktop_icon, has_desktop_icon
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            assert not has_desktop_icon(tmp_path)
            apply_desktop_icon(tmp_path, "locked")
            assert has_desktop_icon(tmp_path)


# === 集成测试: cmd_lock/cmd_unlock 端到端 ===

class TestLockUnlockWithIcon:
    """验证 cmd_lock/cmd_unlock 集成 desktop_icon 后的端到端行为。"""

    @pytest.fixture
    def pandax_root(self, tmp_path: Path):
        """创建已 init 的 pandax 临时目录。"""
        import subprocess
        from pathlib import Path as P
        # 创建一些 .py 文件
        (tmp_path / "main.py").write_text("# main\n", encoding="utf-8")
        (tmp_path / "config.json").write_text("{}", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
        # init
        cmd_init_args = MagicMock(root=str(tmp_path), ext=None, no_binary=False)
        from pandax.cli import cmd_init
        rc = cmd_init(cmd_init_args)
        assert rc == 0
        # 验证 .pandax/config.json 已创建
        assert (tmp_path / ".pandax" / "config.json").exists()
        return tmp_path

    def test_lock_creates_desktop_ini(self, pandax_root: Path):
        """pandax lock 应自动创建 desktop.ini。"""
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            from pandax.cli import cmd_lock
            args = MagicMock(root=str(pandax_root), no_auto_init=True)
            rc = cmd_lock(args)
        assert rc == 0
        assert (pandax_root / "desktop.ini").exists()
        assert (pandax_root / ".pandax" / "icon" / "pandax_locked.ico").exists()

    def test_unlock_removes_desktop_ini(self, pandax_root: Path):
        """pandax unlock 应清理 desktop.ini。"""
        with patch("pandax.desktop_icon.sys") as mock_sys:
            mock_sys.platform = "win32"
            from pandax.cli import cmd_lock, cmd_unlock
            # 先 lock
            cmd_lock(MagicMock(root=str(pandax_root), no_auto_init=True))
            assert (pandax_root / "desktop.ini").exists()
            # 再 unlock
            cmd_unlock(MagicMock(root=str(pandax_root), no_auto_init=True))
            assert not (pandax_root / "desktop.ini").exists()

    def test_lock_icon_failure_does_not_block(self, pandax_root: Path):
        """图标切换失败不应阻塞 lock 主流程(对抗式审查)。"""
        from pandax.cli import cmd_lock
        # 模拟图标写入失败
        with patch("pandax.desktop_icon.apply_desktop_icon",
                   side_effect=OSError("模拟权限失败")):
            args = MagicMock(root=str(pandax_root), no_auto_init=True)
            rc = cmd_lock(args)
        # lock 仍应成功(只读属性已应用)
        assert rc == 0
        # 但 desktop.ini 未创建
        assert not (pandax_root / "desktop.ini").exists()


# === 合规测试: ICO 多尺寸 ===

class TestICOFiles:
    """验证 ICO 文件本身的合规性。"""

    def test_ico_has_multiple_sizes(self):
        """ICO 包含 16/32/48/64/128/256 多个尺寸。"""
        from PIL import Image
        for name in ["pandax_locked", "pandax_unlocked"]:
            img = Image.open(
                Path(__file__).parent.parent
                / "src" / "pandax" / f"{name}.ico"
            )
            sizes = img.info.get("sizes", set())
            expected = {(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)}
            assert sizes == expected, f"{name}.ico 尺寸不匹配: {sizes}"

    def test_ico_visual_distinct(self):
        """locked 和 unlocked ICO 视觉不同(锁符号差异)。"""
        from PIL import Image
        from pathlib import Path
        locked = Image.open(Path(__file__).parent.parent / "src" / "pandax" / "pandax_locked.ico")
        unlocked = Image.open(Path(__file__).parent.parent / "src" / "pandax" / "pandax_unlocked.ico")
        # 256x256 主图逐像素比对
        l_bytes = locked.resize((256, 256)).tobytes()
        u_bytes = unlocked.resize((256, 256)).tobytes()
        # 不完全相同(锁符号差异)
        assert l_bytes != u_bytes, "locked/unlocked ICO 完全相同(设计缺陷)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])