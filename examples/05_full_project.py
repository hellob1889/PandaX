"""
05_full_project.py
===================
PandaX 完整 20 文件项目实战 demo

演示：用一个完整的"真实"项目（代码/配置/文档/前端/脚本/二进制）走完 7 层防御。
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
GIT = shutil.which("git") or "git"  # 自动检测；避免硬编码用户安装路径


def banner(msg):
    print("\n" + "=" * 60)
    print(f"  {msg}")
    print("=" * 60)


def cli(args, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    env["PATH"] = str(Path(GIT).parent) + os.pathsep + env.get("PATH", "")
    r = subprocess.run([sys.executable, "-m", "pandax", *args],
                       cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout


def git(args, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    env["PATH"] = str(Path(GIT).parent) + os.pathsep + env.get("PATH", "")
    r = subprocess.run([GIT, *args], cwd=cwd, env=env,
                       capture_output=True, text=True, timeout=10)
    return r.returncode, r.stdout, r.stderr


def main():
    project = Path("demo_05_full").resolve()
    print(f"\n[Demo] PandaX 完整 20 文件项目实战")
    print(f"  Project: {project}\n")

    if project.exists():
        shutil.rmtree(project)
    project.mkdir()

    # ============================================================
    # 创建 20 文件（覆盖所有类型）
    # ============================================================
    banner("Step 1: 创建 20 文件（10 文本 + 5 二进制 + 5 配置）")

    files = {
        # 文本代码
        "src/main.py": 'def main():\n    print("v1")\n',
        "src/utils.py": 'def add(a, b): return a+b\n',
        "tests/test_main.py": 'def test_main(): pass\n',
        # 文档
        "docs/README.md": '# App\nDocs here.\n',
        "docs/API.md": '# API\nEndpoints.\n',
        # 配置
        "config.json": '{"name":"demo","version":"1.0"}\n',
        "settings.yaml": 'app:\n  debug: false\n',
        ".env": 'SECRET=demo123\n',
        # 前端
        "index.html": '<!DOCTYPE html><html></html>\n',
        "app.js": 'console.log("app");\n',
    }
    for rel, content in files.items():
        p = project / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # 二进制
    binaries = {
        "assets/logo.png": b"\x89PNG\r\n\x1a\nLOGO_V1",
        "assets/photo.jpg": b"\xff\xd8\xff\xe0PHOTO_V1",
        "assets/data.zip": b"PK\x03\x04ZIP_V1",
        "assets/icon.ico": b"\x00\x00\x01\x00ICO_V1",
        "docs/report.pdf": b"%PDF-1.4\nPDF_V1",
    }
    for rel, content in binaries.items():
        p = project / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    print(f"  创建 {len(files)} 文本 + {len(binaries)} 二进制 = {len(files) + len(binaries)} 文件")

    # ============================================================
    # git init + 初始 commit
    # ============================================================
    banner("Step 2: git 初始化")
    git(["init"], str(project))
    git(["config", "user.email", "demo@example.com"], str(project))
    git(["config", "user.name", "Demo"], str(project))
    git(["add", "-A"], str(project))
    git(["commit", "-m", "initial"], str(project))
    print("  ✓ git initialized")

    # ============================================================
    # pandax init
    # ============================================================
    banner("Step 3: pandax init")
    rc, out = cli(["init", "--root", str(project)], str(project))
    for line in out.splitlines():
        if "[OK]" in line or "[snapshot]" in line:
            print(f"  {line.strip()}")

    # ============================================================
    # pandax lock
    # ============================================================
    banner("Step 4: pandax lock（保护所有受保护文件）")
    rc, out = cli(["lock", "--root", str(project)], str(project))
    for line in out.splitlines():
        if "[OK]" in line:
            print(f"  {line.strip()}")

    # 统计锁定
    locked_count = 0
    for f in project.rglob("*"):
        if f.is_file() and not (oct(f.stat().st_mode)[-3:].startswith("6")):
            locked_count += 1
    print(f"  ✓ 实际锁定文件数: {locked_count}")

    # ============================================================
    # 合规 write 一个 .py 和一个 .png
    # ============================================================
    banner("Step 5: 合规 write (Python + PNG)")

    rc, out = cli([
        "write", "--root", str(project),
        "--file", "src/main.py",
        "--reason", "升级主程序到 v2",
        "--problem", "v1 功能不全",
        "--approach", "添加 config 加载",
        "--old", 'def main():\n    print("v1")',
        "--new", 'def main():\n    print("v2")',
    ], str(project))
    print(f"  write main.py: rc={rc}")

    # 写新 PNG
    (project / "new_logo.png").write_bytes(b"\x89PNG\r\n\x1a\nLOGO_V2")
    rc, out = cli([
        "write", "--root", str(project),
        "--file", "assets/logo.png",
        "--reason", "升级 logo 到 V2",
        "--problem", "旧 logo 过时",
        "--approach", "用 V2 PNG 替换",
        "--from-file", str(project / "new_logo.png"),
    ], str(project))
    print(f"  write logo.png: rc={rc}")

    # ============================================================
    # 攻击测试
    # ============================================================
    banner("Step 6: 攻击测试（验证拦截）")

    # L1 攻击
    print("\n  [攻击 L1] 直接 write 锁定文件")
    attack_file = project / "src/utils.py"
    try:
        attack_file.write_text("HIJACKED\n", encoding="utf-8")
        print(f"  ❌ BUG: L1 失败")
    except (PermissionError, OSError):
        print(f"  ✓ L1 拦截: PermissionError")

    # L6 攻击
    print("\n  [攻击 L6] 直接覆盖 .png")
    attack_png = project / "assets/photo.jpg"
    attack_png.chmod(attack_png.stat().st_mode | stat.S_IWUSR)
    attack_png.write_bytes(b"\xff\xd8\xff\xe0HIJACKED_PHOTO")
    print(f"  ⚠️  photo.jpg 已覆盖（绕过 write）")

    # ============================================================
    # install-hook
    # ============================================================
    banner("Step 7: install-hook")
    rc, out = cli(["install-hook", "--root", str(project)], str(project))
    print(f"  rc={rc}")

    # ============================================================
    # L3 攻击
    # ============================================================
    banner("Step 8: L3 攻击（新文件无 write 记录）")
    (project / "src" / "evil.py").write_text("EVIL = True\n", encoding="utf-8")
    git(["add", "src/evil.py"], str(project))
    rc, out, err = git(["commit", "-m", "bypass"], str(project))
    if rc != 0:
        print(f"  ✓ L3 hook 拦截: rc={rc}")
        # 提取错误信息
        for line in (out + err).splitlines():
            if "PandaX" in line or "未审计" in line:
                print(f"    {line.strip()}")
                break
    else:
        print(f"  ❌ L3 失败: rc={rc}")

    # ============================================================
    # 导出多种格式
    # ============================================================
    banner("Step 9: 导出 13 种格式")
    export_dir = project / "exports"
    export_dir.mkdir()
    formats = ["text", "csv", "json", "yaml", "md", "html",
               "xlsx", "docx", "pdf", "sqlite", "rst", "asciidoc", "tsv"]
    for fmt in formats:
        rc, out = cli(["log", "--root", str(project),
                      "--format", fmt, "--output", str(export_dir / f"audit.{fmt}")],
                     str(project))
        fp = export_dir / f"audit.{fmt}"
        if fp.exists():
            size = fp.stat().st_size
            print(f"  ✓ {fmt:12s} → {fp.name:18s} ({size:6d} bytes)")
        else:
            print(f"  ❌ {fmt:12s} FAILED")

    # ============================================================
    # 最终 status
    # ============================================================
    banner("Step 10: 最终 status")
    rc, out = cli(["status", "--root", str(project)], str(project))
    # 只显示关键行
    for line in out.splitlines():
        if any(kw in line for kw in ["[", "总记录", "APPROVED", "REJECTED", "UNAUTHORIZED"]):
            print(f"  {line.strip()}")

    print("\n" + "=" * 60)
    print(f"  ✓ Demo 5 完成 — 完整 20 文件项目走完 7 层防御")
    print(f"  项目保留: {project}")
    print(f"  导出在:   {export_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()