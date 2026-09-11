"""
test_installer_dir.py
=====================
回归测试:右键菜单 installer 路径 + pyproject.toml 打包 — v0.7.1 final 修复

修复历史:
  v0.7.1 之前:
    - installer/ 在项目根
    - pyproject.toml package-data 没声明
    - cli.py INSTALLER_DIR = parent.parent.parent / "installer" (只对 dev 模式生效)
    - 结果:`pip install` 后 site-packages/pandaone/ 缺 installer/
            + `pandaone install-context` 报"脚本不存在"

  v0.7.1 修复:
    - installer/ 移入 src/pandaone/installer/(单路径,与 cli.py 同包)
    - pyproject.toml package-data 声明所有平台 installer/*
    - MANIFEST.in 路径同步更新为 src/pandaone/installer/
    - cli.py INSTALLER_DIR = parent / "installer"(单路径,两场景通用)

验证:
  1. installer/ 在 src/pandaone/ 下(dev 模式)
  2. pyproject.toml package-data 包含所有平台 installer/*
  3. _find_installer_dir() 在 dev 模式下返回正确路径
  4. mock 模拟 site-packages 模式也能找到
  5. 端到端: site-packages 安装下,`pandaone install-context --help` 不报脚本缺失
  6. 端到端: site-packages 安装下,site-packages/pandaone/installer/ 存在
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX_SRC = ROOT / "src" / "pandaone" / "cli.py"
PANDAX_DEV_INSTALLER = ROOT / "src" / "pandaone" / "installer"  # v0.7.1+ 新位置
PYPROJECT = ROOT / "pyproject.toml"

# TRAE 自带 Python 的 site-packages
TRAE_PYTHON = Path(r"C:\Users\Administrator\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\vm\tools\python\python.exe")
SITE_PANDAX = TRAE_PYTHON.parent / "lib" / "site-packages" / "pandaone"
SITE_PANDAX_INSTALLER = SITE_PANDAX / "installer"


# ============================================================
# 测试 1: installer/ 在 src/pandaone/ 下(结构正确)
# ============================================================
def test_installer_in_pandaone_package():
    """v0.7.1 修复:installer/ 必须位于 src/pandaone/installer/。"""
    assert PANDAX_DEV_INSTALLER.exists(), \
        f"installer/ 必须位于 src/pandaone/installer/,实际: {PANDAX_DEV_INSTALLER}"
    # 三个平台都应存在
    assert (PANDAX_DEV_INSTALLER / "windows").exists(), "windows/ 子目录缺失"
    assert (PANDAX_DEV_INSTALLER / "macos").exists(), "macos/ 子目录缺失"
    assert (PANDAX_DEV_INSTALLER / "linux").exists(), "linux/ 子目录缺失"
    # Windows 关键脚本
    assert (PANDAX_DEV_INSTALLER / "windows" / "install_context_menu.ps1").exists(), \
        "windows/install_context_menu.ps1 缺失"


# ============================================================
# 测试 2: 函数存在
# ============================================================
def test_find_installer_dir_function_exists():
    """cli.py 必须导出 _find_installer_dir() 函数。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pandaone_cli_test", PANDAX_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "_find_installer_dir"), \
        "应存在 _find_installer_dir() 函数"
    assert callable(mod._find_installer_dir), \
        "_find_installer_dir 应是可调用函数"


# ============================================================
# 测试 3: dev 模式能找到
# ============================================================
def test_find_installer_dir_dev_mode_works():
    """dev 模式下,能定位到 src/pandaone/installer/。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pandaone_cli_test", PANDAX_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod._find_installer_dir()
    assert result.exists(), f"dev 模式应能找到 installer,实际: {result}"
    # 应是 src/pandaone/installer/,不是 site-packages
    assert result.resolve() == PANDAX_DEV_INSTALLER.resolve(), \
        f"dev 模式应返回 {PANDAX_DEV_INSTALLER},实际: {result}"
    # 验证里面有 Windows 脚本
    assert (result / "windows" / "install_context_menu.ps1").exists(), \
        "installer/windows/install_context_menu.ps1 必须存在"


# ============================================================
# 测试 4: mock site-packages 模式
# ============================================================
def test_find_installer_dir_installed_mode_works():
    """mock 模拟 site-packages 模式,验证 _find_installer_dir 仍能定位(同路径)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pandaone_cli_test", PANDAX_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # 模拟 site-packages 结构:tmp/site-packages/pandaone/cli.py + tmp/site-packages/pandaone/installer/
        fake_pandaone = tmp_path / "site-packages" / "pandaone"
        fake_pandaone.mkdir(parents=True)
        (fake_pandaone / "cli.py").write_text("# mock", encoding="utf-8")
        fake_installer = fake_pandaone / "installer"
        fake_installer.mkdir()
        (fake_installer / "windows").mkdir()
        (fake_installer / "windows" / "install_context_menu.ps1").write_text("# mock", encoding="utf-8")

        # 替换 __file__ 让函数认为自己是 site-packages/pandaone/cli.py
        with patch.object(mod, "__file__", str(fake_pandaone / "cli.py")):
            result = mod._find_installer_dir()
            # 应返回 fake_pandaone/installer(同 parent 关系)
            assert result.resolve() == fake_installer.resolve(), \
                f"site-packages 模式应返回 {fake_installer},实际: {result}"


# ============================================================
# 测试 5: pyproject.toml 包含 installer/ 进 package-data
# ============================================================
def test_pyproject_package_data_includes_installer():
    """pyproject.toml 的 package-data 必须包含三个平台 installer/*。"""
    content = PYPROJECT.read_text(encoding="utf-8")

    # 找 package-data 段
    assert "package-data" in content, "应有 package-data 段"
    assert "pandaone" in content, "应有 pandaone package-data 配置"

    # 必须包含三个平台的 installer 通配
    assert 'installer/windows/*.ps1' in content, \
        "package-data 应包含 installer/windows/*.ps1"
    assert 'installer/macos/*.sh' in content, \
        "package-data 应包含 installer/macos/*.sh"
    assert 'installer/linux/*.sh' in content, \
        "package-data 应包含 installer/linux/*.sh"


def test_manifest_in_installer_paths_updated():
    """MANIFEST.in 的 installer 路径必须指向 src/pandaone/installer/。

    旧路径(installer/windows/*.ps1)会让 wheel 不包含 installer。
    新路径(src/pandaone/installer/...)必须存在。
    """
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    # 新的相对路径必须出现
    assert "src/pandaone/installer" in manifest, \
        "MANIFEST.in 应使用 src/pandaone/installer/ 路径"
    # 旧的项目根路径不应再出现(只有相对项目根的 src/pandaone/...)
    # 找独立的 "include installer/" 或 "recursive-include installer/" 模式
    import re
    bad_patterns = re.findall(r"^(?!.*src/pandaone).*\binstaller[/\\]", manifest, re.MULTILINE)
    # 排除带 src/ 前缀的合法行
    bad_lines = [
        line for line in manifest.splitlines()
        if ("installer" in line or "installer/" in line or "installer\\" in line)
        and "src/pandaone/installer" not in line
        and not line.strip().startswith("#")
    ]
    assert not bad_lines, f"MANIFEST.in 仍含项目根级 installer 路径(应改为 src/pandaone/installer):\n" + "\n".join(bad_lines)


# ============================================================
# 测试 6: 端到端 site-packages 验证
# ============================================================
@pytest.mark.skipif(
    not SITE_PANDAX.exists(),
    reason="site-packages/pandaone/ 不存在(无 TRAE Python 或未安装),跳过 e2e"
)
def test_installed_pandaone_has_installer_in_site_packages():
    """site-packages/pandaone/installer/ 必须存在(由 package-data 决定)。"""
    assert SITE_PANDAX_INSTALLER.exists(), (
        f"site-packages/pandaone/installer/ 必须存在(Bug A 已修),"
        f"实际: {SITE_PANDAX_INSTALLER}"
    )
    if sys.platform == "win32":
        assert (SITE_PANDAX_INSTALLER / "windows" / "install_context_menu.ps1").exists(), \
            "site-packages/pandaone/installer/windows/install_context_menu.ps1 必须存在"
        assert (SITE_PANDAX_INSTALLER / "windows" / "uninstall_context_menu.ps1").exists(), \
            "site-packages/pandaone/installer/windows/uninstall_context_menu.ps1 必须存在"


@pytest.mark.skipif(
    not TRAE_PYTHON.exists(),
    reason="TRAE Python 不存在,跳过 e2e"
)
def test_installed_pandaone_install_context_help_works():
    """site-packages 装的 pandaone 跑 `pandaone install-context --help` 不能报 installer 缺失。"""
    result = subprocess.run(
        [str(TRAE_PYTHON), "-m", "pandaone", "install-context", "--help"],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(ROOT), timeout=30
    )
    # 关键:不能因为"脚本不存在"而失败
    assert "脚本不存在" not in result.stdout, \
        f"不应出现 installer 脚本不存在的报错,实际 stdout:\n{result.stdout[:500]}"
    assert "脚本不存在" not in result.stderr, \
        f"不应出现 installer 脚本不存在的报错,实际 stderr:\n{result.stderr[:500]}"
    # help 应成功返回
    assert result.returncode == 0, \
        f"install-context --help 应成功,实际 exit={result.returncode}\nstdout={result.stdout[:500]}\nstderr={result.stderr[:500]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])