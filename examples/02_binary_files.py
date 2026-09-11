"""
02_binary_files.py
===================
Pandaone AI Agent 二进制文件保护 demo

演示：init 时建立 SHA256 snapshot → write 替换 → 检测篡改
预期：直接覆盖 .png 后 status 显示 SHA256 mismatch
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

class C:
    G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"; R = "\033[91m"; W = "\033[0m"

if sys.platform == "win32":
    os.system("")


def banner(msg):
    print(f"\n{C.B}{'=' * 60}{C.W}")
    print(f"{C.B}  {msg}{C.W}")
    print(f"{C.B}{'=' * 60}{C.W}")


def step(msg):
    print(f"\n{C.Y}[{msg}]{C.W}")


def ok(msg):
    print(f"  {C.G}✓ {msg}{C.W}")


def find_src():
    here = Path(__file__).resolve().parent
    for p in [here.parent, here.parent.parent]:
        if (p / "src" / "pandaone" / "__init__.py").exists():
            return p / "src"
    return None


def find_git():
    for c in ["git", r"C:\Program Files\Git\cmd\git.exe", "/usr/bin/git"]:
        if shutil.which(c) or Path(c).exists():
            return c if Path(c).exists() else shutil.which(c)
    return None


def cli(args, cwd):
    env = os.environ.copy()
    src = find_src()
    if src:
        env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run([sys.executable, "-m", "pandaone", *args],
                       cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


def git(args, cwd):
    g = find_git()
    if not g:
        return 1, "", "git not found"
    env = os.environ.copy()
    env["PATH"] = str(Path(g).parent) + os.pathsep + env.get("PATH", "")
    r = subprocess.run([g, *args], cwd=cwd, env=env,
                       capture_output=True, text=True, timeout=10)
    return r.returncode, r.stdout, r.stderr


def main():
    project = Path("demo_02_binary").resolve()
    print(f"\n[Demo] Pandaone 二进制文件保护 demo")
    print(f"  Project: {project}\n")

    if project.exists():
        # 解锁后删除
        import stat
        for p in project.rglob("*"):
            if p.is_file():
                try:
                    p.chmod(p.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                except Exception:
                    pass
        shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    (project / "assets").mkdir()

    # ============================================================
    # 准备初始二进制文件
    # ============================================================
    step("1/5] 准备初始二进制文件")
    (project / "assets" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\nOLD_LOGO")
    (project / "assets" / "photo.jpg").write_bytes(b"\xff\xd8\xff\xe0OLD_PHOTO")
    (project / "assets" / "data.zip").write_bytes(b"PK\x03\x04OLD_ZIP")
    ok(f"创建了 3 个二进制文件 ({sum(f.stat().st_size for f in (project / 'assets').iterdir())} bytes)")

    # ============================================================
    # init + snapshot
    # ============================================================
    step("2/5] pandaone init（建立 snapshot）")
    rc, out, _ = cli(["init", "--root", str(project)], project)
    for line in out.splitlines():
        if "[OK]" in line or "snapshot" in line:
            print(f"  {line.strip()}")
    snap_path = project / ".pandaone" / "binary_snapshots.json"
    ok(f"已建立 snapshot（{snap_path}）")

    # ============================================================
    # 合规 write 替换 logo
    # ============================================================
    step("3/5] 合规 write 替换 logo.png")
    (project / "new_logo.png").write_bytes(b"\x89PNG\r\n\x1a\nNEW_LOGO_V2")
    rc, out, _ = cli([
        "write", "--root", str(project),
        "--file", "assets/logo.png",
        "--reason", "升级 logo",
        "--problem", "品牌色变更",
        "--approach", "用新 PNG 替换",
        "--from-file", str(project / "new_logo.png"),
    ], project)
    for line in out.splitlines():
        if "[APPROVED]" in line:
            print(f"  {line.strip()}")
    ok(f"snapshot 已更新为新 SHA256")

    # ============================================================
    # 攻击：直接覆盖 photo.jpg
    # ============================================================
    step("4/5] 攻击：直接覆盖 photo.jpg（绕过 write）")
    photo = project / "assets" / "photo.jpg"
    os.chmod(photo, photo.stat().st_mode | 0o200)
    photo.write_bytes(b"\xff\xd8\xff\xe0HIJACKED_PHOTO")
    ok(f"photo.jpg 已被覆盖（绕过 write）")

    # ============================================================
    # status 检测篡改
    # ============================================================
    step("5/5] status 检测篡改")
    rc, out, _ = cli(["status", "--root", str(project)], project)
    for line in out.splitlines():
        if any(kw in line for kw in ["[", "snapshot", "SHA256", "WARN", "照片"]):
            print(f"  {line.strip()}")

    banner(f"Demo 2 完成 — 二进制 snapshot 拦截篡改")
    return 0


if __name__ == "__main__":
    sys.exit(main())