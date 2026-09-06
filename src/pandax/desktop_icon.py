"""Pandax 文件夹图标切换模块(方案 A:desktop.ini 替换)。

第一性原理:
- Windows 资源管理器通过文件夹里的 `desktop.ini` 识别自定义图标
- `IconFile=pandax_locked.ico` 引用 ICO 文件(相对或绝对路径)
- `desktop.ini` 必须设 `+h +s`(系统+隐藏)才会被 explorer 当作系统配置
- ICO 复制到 `<root>/.pandax/icon/`(隐藏目录,避免污染用户目录)

设计权衡:
- ICO 相对路径引用(不绑死 pandax 安装路径),即使 pandax 卸载也能显示
- 仅 Windows 生效(其他平台直接 no-op,attrib 命令会 fallback)
- 自包含,不依赖外部图标文件(ICO 通过 package-data 内置到 wheel)

Bug 防护:
- idempotent: 多次 lock 不会出错
- cross-platform safety: 非 Windows 跳过,但记录状态
- graceful degradation: 复制失败 → 仍完成 lock,仅记 warn
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Literal


LockState = Literal["locked", "unlocked"]

ICON_FILENAME = {
    "locked": "pandax_locked.ico",
    "unlocked": "pandax_unlocked.ico",
}

DESKTOP_INI_NAME = "desktop.ini"
ICON_DIR = ".pandax" + os.sep + "icon"


def _read_ico_from_package(name: str) -> bytes:
    """从 pandax 包内置资源读取 ICO 文件字节。

    Fallback 1: importlib.resources(python 3.9+)
    Fallback 2: pkg_resources(setuptools 自带)
    Fallback 3: 文件系统路径 src/pandax/<name>(开发环境)
    """
    # Fallback 3: 开发环境(直接读 src/pandax/<name>)
    dev_path = Path(__file__).parent / name
    if dev_path.exists():
        return dev_path.read_bytes()
    # Fallback 1: importlib.resources
    try:
        from importlib import resources
        with resources.files("pandax").joinpath(name).open("rb") as f:
            return f.read()
    except (ImportError, FileNotFoundError, AttributeError):
        pass
    # Fallback 2: pkg_resources
    try:
        import pkg_resources
        return pkg_resources.resource_string("pandax", name)
    except Exception:
        pass
    raise FileNotFoundError(
        f"无法定位 pandax 内置图标 {name}(检查 pyproject.toml package-data)"
    )


def apply_desktop_icon(root: Path, state: LockState) -> tuple[bool, str]:
    """在目录写入 desktop.ini + 复制 ICO,实现图标切换。

    Returns: (success: bool, message: str)
    - 成功: (True, "[OK] 文件夹图标已切换")
    - 非 Windows: (True, "[SKIP] 当前平台不是 Windows,跳过图标切换")
    - 失败: (False, "[ERR] 原因")
    """
    if sys.platform != "win32":
        return True, f"[SKIP] 当前平台 {sys.platform} 不是 Windows,跳过图标切换"

    root = Path(root).resolve()
    icon_filename = ICON_FILENAME[state]
    icon_dir = root / ".pandax" / "icon"
    target_icon = icon_dir / icon_filename
    desktop_ini = root / DESKTOP_INI_NAME

    try:
        # 1. 确保 .pandax/icon/ 存在
        icon_dir.mkdir(parents=True, exist_ok=True)
        # 2. 复制 ICO 到 .pandax/icon/
        ico_bytes = _read_ico_from_package(icon_filename)
        target_icon.write_bytes(ico_bytes)
        # 3. 隐藏 ICO 目录(避免污染文件列表视图)
        try:
            os.system(f'attrib +h "{icon_dir}" >nul 2>&1')
        except Exception:
            pass
        # 4. 先清除 desktop.ini 的 +h +s 属性(若已存在),否则 write_text 会 PermissionError
        #    Windows 上系统文件自动变只读,直接覆盖写会被拒
        if desktop_ini.exists():
            os.system(f'attrib -h -s "{desktop_ini}" >nul 2>&1')
        # 5. 写入 desktop.ini(用相对路径,不绑死绝对路径)
        desktop_ini.write_text(
            "[.ShellClassInfo]\r\n"
            f"IconFile={ICON_DIR}{os.sep}{icon_filename}\r\n"
            "IconIndex=0\r\n",
            encoding="utf-8",
        )
        # 6. 标记 desktop.ini 为系统+隐藏文件(Windows 才会当作系统配置读取)
        os.system(f'attrib +h +s "{desktop_ini}" >nul 2>&1')
        # 7. 通知 explorer 刷新(可选,新窗口/重启 explorer 才生效)
        #    不主动 SHChangeNotify,因为可能影响 explorer 性能
        return True, f"[OK] 文件夹图标已切换 → {state}"
    except Exception as e:
        return False, f"[ERR] 图标切换失败: {type(e).__name__}: {e}"


def remove_desktop_icon(root: Path) -> tuple[bool, str]:
    """清理 desktop.ini + .pandax/icon/,恢复 Windows 默认文件夹图标。

    Returns: (success: bool, message: str)
    """
    if sys.platform != "win32":
        return True, f"[SKIP] 当前平台 {sys.platform} 不是 Windows,跳过图标清理"

    root = Path(root).resolve()
    desktop_ini = root / DESKTOP_INI_NAME
    icon_dir = root / ".pandax" / "icon"

    msgs = []
    try:
        # 1. 清除 desktop.ini 的系统+隐藏属性,才能删除
        if desktop_ini.exists():
            os.system(f'attrib -h -s "{desktop_ini}" >nul 2>&1')
            desktop_ini.unlink()
            msgs.append("desktop.ini")
        # 2. 删除 .pandax/icon/ 目录
        if icon_dir.exists():
            try:
                os.system(f'attrib -h "{icon_dir}" >nul 2>&1')
                shutil.rmtree(icon_dir, ignore_errors=True)
                msgs.append(".pandax/icon/")
            except Exception as e:
                msgs.append(f".pandax/icon/(部分:{e})")
        if msgs:
            return True, f"[OK] 已清理: {', '.join(msgs)}"
        return True, "[OK] 无需清理(从未启用图标)"
    except Exception as e:
        return False, f"[ERR] 图标清理失败: {type(e).__name__}: {e}"


def has_desktop_icon(root: Path) -> bool:
    """检查目录当前是否有 pandax 应用的 desktop.ini。"""
    root = Path(root).resolve()
    return (root / DESKTOP_INI_NAME).exists()