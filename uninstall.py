#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uninstall.py — PandaX 卸载清理工具

职责:
  1. 停止所有运行中的 watchdog 进程
  2. 清理用户级指纹文件 (~/.pandax_fp.txt)
  3. 清理 PATH 中的 pandax 条目（可选）
  4. 调用 pip uninstall pandax

用法:
  python uninstall.py
  python uninstall.py --keep-projects   # 不清理项目内 .pandax/ 目录
  python uninstall.py --no-pip          # 只清理，不调 pip

第一性原理:
  - 卸载是普通用户最痛恨的事（残留文件、僵尸进程、PATH 污染）
  - 必须干净、可验证、可重入
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def kill_watchdogs():
    """停止所有运行中的 watchdog 进程"""
    print("[1/4] 停止 watchdog 进程...")
    killed = 0
    if sys.platform == "win32":
        # Windows 用 taskkill
        for name in ["pandax-watchdog.exe", "pandax_guard.exe"]:
            r = subprocess.run(
                ["taskkill", "/F", "/IM", name],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and name in r.stdout:
                killed += 1
    else:
        # Unix 用 pkill
        for sig in ["pandax-watchdog", "pandax_guard"]:
            r = subprocess.run(
                ["pkill", "-9", "-f", sig],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                killed += 1
    print(f"  停止 {killed} 个 watchdog 进程")


def clean_fingerprint():
    """清理用户级指纹文件"""
    print("[2/4] 清理指纹文件...")
    fp_path = Path.home() / ".pandax_fp.txt"
    if fp_path.exists():
        fp_path.unlink()
        print(f"  删除: {fp_path}")
    else:
        print(f"  跳过: 不存在")


def clean_path_windows():
    """从 Windows PATH 移除 pandax"""
    print("[3/4] 清理 PATH...")
    if sys.platform != "win32":
        print("  跳过 (Unix 系统手动改 ~/.bashrc 等)")
        return

    try:
        import winreg
    except ImportError:
        print("  跳过 (winreg 不可用)")
        return

    try:
        # 读用户 PATH
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0, winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            current, _ = winreg.QueryValueEx(key, "Path")
            # 移除含 pandax 的路径
            parts = [p for p in current.split(";") if "pandax" not in p.lower()]
            new = ";".join(parts)
            if new != current:
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new)
                print(f"  PATH 已更新")
            else:
                print(f"  PATH 中无 pandax 条目")
    except Exception as e:
        print(f"  [WARN] 清理 PATH 失败: {e}")


def pip_uninstall():
    """调用 pip uninstall"""
    print("[4/4] 调用 pip uninstall...")
    cmd = [sys.executable, "-m", "pip", "uninstall", "pandax", "-y"]
    r = subprocess.run(cmd, capture_output=False)
    if r.returncode == 0:
        print("[OK] 卸载完成")
    else:
        print(f"[ERROR] pip uninstall 失败 rc={r.returncode}")


def main():
    parser = argparse.ArgumentParser(description="PandaX 卸载清理")
    parser.add_argument("--no-pip", action="store_true", help="只清理，不调 pip")
    parser.add_argument("--keep-projects", action="store_true", help="不清理项目内 .pandax/")
    args = parser.parse_args()

    print("=" * 60)
    print("PandaX 卸载工具")
    print("=" * 60)
    print()

    kill_watchdogs()
    time.sleep(1)  # 等进程真的结束
    clean_fingerprint()
    clean_path_windows()

    if not args.no_pip:
        pip_uninstall()

    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)
    if args.keep_projects:
        print("提示: 项目内的 .pandax/ 目录已保留，可手动删除")
    return 0


if __name__ == "__main__":
    sys.exit(main())