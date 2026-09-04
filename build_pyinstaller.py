#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — PandaX 完整打包脚本（Python 版，跨平台）

用法:
  python build.py

步骤:
  1. 清理旧产物
  2. PyInstaller 打包 pandax.exe
  3. PyInstaller 打包 pandax_guard.exe
  4. 合并 _internal 目录
  5. 准备安装包 staging
  6. 调用 Inno Setup 编译（如可用）

第一性原理:
  - Python 脚本跨平台（Windows / Linux / macOS）
  - 避免 bat 文件的 GBK 编码问题
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> int:
    """执行命令并打印输出"""
    print(f"$ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    return r.returncode


def clean():
    """清理旧产物"""
    print("\n[1/6] 清理旧产物...")
    for d in ["build", "dist", "installer/staging", "installer/Output"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f"  删除: {d}")


def build_pandax():
    print("\n[2/6] 打包 pandax.exe...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "pandax",
        "--onedir",
        "--console",
        "--add-data", "README.md;.",
        "--add-data", "templates;templates",
        "--add-data", "pandax.py;.",
        "--add-data", "pandax_guard.py;.",
        "--add-data", "install_hook.py;.",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        "--hidden-import", "watchdog.observers.polling",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--noconfirm",
        str(ROOT / "pandax.py"),
    ]
    return run(cmd, cwd=ROOT)


def build_watchdog():
    print("\n[3/6] 打包 pandax_guard.exe...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "pandax_guard",
        "--onedir",
        "--console",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        "--hidden-import", "watchdog.observers.polling",
        "--exclude-module", "tkinter",
        "--noconfirm",
        str(ROOT / "pandax_guard.py"),
    ]
    return run(cmd, cwd=ROOT)


def merge_internals():
    print("\n[4/6] 合并 _internal 目录...")
    src = ROOT / "dist" / "pandax_guard" / "_internal"
    dst = ROOT / "dist" / "pandax" / "_internal"
    if src.exists() and dst.exists():
        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        print(f"  合并 {len(list(src.iterdir()))} 个文件到 {dst}")

    # 复制 pandax_guard.exe
    src_exe = ROOT / "dist" / "pandax_guard" / "pandax_guard.exe"
    dst_exe = ROOT / "dist" / "pandax" / "pandax_guard.exe"
    if src_exe.exists():
        shutil.copy2(src_exe, dst_exe)
        print(f"  复制 {dst_exe.name}")

    # 删除 pandax_guard 目录
    shutil.rmtree(ROOT / "dist" / "pandax_guard", ignore_errors=True)


def prepare_staging():
    print("\n[5/6] 准备安装包 staging...")
    staging = ROOT / "installer" / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    src = ROOT / "dist" / "pandax"
    for item in src.iterdir():
        target = staging / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    print(f"  复制 {len(list(src.iterdir()))} 项到 {staging}")


def try_inno_setup():
    print("\n[6/6] 尝试 Inno Setup 编译...")
    iss = ROOT / "installer" / "pandax.iss"
    if not iss.exists():
        print(f"  [WARN] 找不到 {iss}")
        return

    # 检查 iscc 是否可用
    iscc = shutil.which("iscc")
    if iscc is None:
        # Windows 默认路径
        for p in [
            Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
            Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        ]:
            if p.exists():
                iscc = str(p)
                break

    if iscc is None:
        print(f"  [INFO] Inno Setup 未安装")
        print(f"        下载地址: https://jrsoftware.org/isdl.php")
        print(f"        安装后运行: {iscc} {iss}")
        return

    cmd = [iscc, str(iss)]
    rc = run(cmd, cwd=ROOT)
    if rc == 0:
        output = ROOT / "installer" / "Output"
        if output.exists():
            exes = list(output.glob("*.exe"))
            if exes:
                print(f"  [OK] 安装包已生成: {exes[0]}")


def main():
    print("=" * 60)
    print("PandaX 完整打包脚本")
    print("=" * 60)

    clean()
    if build_pandax() != 0:
        print("[ERROR] 打包 pandax.exe 失败")
        return 1
    if build_watchdog() != 0:
        print("[ERROR] 打包 pandax_guard.exe 失败")
        return 1
    merge_internals()
    prepare_staging()
    try_inno_setup()

    print("\n" + "=" * 60)
    print("[OK] 打包完成")
    print("=" * 60)
    print("\n产物:")
    for exe in (ROOT / "dist" / "pandax").glob("*.exe"):
        print(f"  - {exe.name} ({exe.stat().st_size:,} bytes)")
    print("\n分发目录:")
    staging = ROOT / "installer" / "staging"
    if staging.exists():
        for exe in staging.glob("*.exe"):
            print(f"  - installer/staging/{exe.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())