"""
01_basic_workflow.py
====================
PandaX 基础工作流 demo

演示：init → lock → write → log → status 完整流程
预期：每个步骤输出对应状态，所有 write 记录 APPROVED

跨平台：纯 Python（不依赖 bash），Windows / macOS / Linux 通用
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 颜色（跨平台 ANSI 支持）
class C:
    G = "\033[92m"   # green
    Y = "\033[93m"   # yellow
    B = "\033[94m"   # blue
    R = "\033[91m"   # red
    W = "\033[0m"    # reset

# Windows CMD 默认不支持 ANSI，需要启用
if sys.platform == "win32":
    os.system("")  # 触发 VT100 模式


def banner(msg):
    print(f"\n{C.B}{'=' * 60}{C.W}")
    print(f"{C.B}  {msg}{C.W}")
    print(f"{C.B}{'=' * 60}{C.W}")


def step(msg):
    print(f"\n{C.Y}[{msg}]{C.W}")


def ok(msg):
    print(f"  {C.G}✓ {msg}{C.W}")


def err(msg):
    print(f"  {C.R}❌ {msg}{C.W}")


def find_git():
    """跨平台查找 git"""
    candidates = [
        "git",  # PATH
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        "/usr/bin/git",  # Git Bash
        "/usr/local/bin/git",  # macOS
    ]
    for c in candidates:
        if shutil.which(c) or Path(c).exists():
            return c if Path(c).exists() else shutil.which(c)
    return None


def find_git_root():
    """找 pandax 项目的 src 目录（用于 PYTHONPATH）"""
    here = Path(__file__).resolve().parent
    # 向上找 src/
    for p in [here.parent, here.parent.parent]:
        if (p / "src" / "pandax" / "__init__.py").exists():
            return p / "src"
    return None


def run_cli(args, cwd=None, env_extra=None):
    """运行 pandax CLI"""
    env = os.environ.copy()
    src_root = find_git_root()
    if src_root:
        env["PYTHONPATH"] = str(src_root) + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)

    r = subprocess.run(
        [sys.executable, "-m", "pandax", *args],
        cwd=str(cwd or Path.cwd()),
        env=env, capture_output=True, text=True, timeout=60,
    )
    return r.returncode, r.stdout, r.stderr


def run_git(args, cwd=None):
    """运行 git 命令"""
    git = find_git()
    if not git:
        return 1, "", "git not found"
    env = os.environ.copy()
    git_dir = Path(git).parent
    env["PATH"] = str(git_dir) + os.pathsep + env.get("PATH", "")

    r = subprocess.run([git, *args], cwd=str(cwd or Path.cwd()),
                       env=env, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


def main():
    project = Path("demo_01_basic").resolve()
    print(f"\n[Demo] PandaX 基础工作流 demo")
    print(f"  Project: {project}\n")

    # 清理
    if project.exists():
        _force_unlock_and_rmtree(project)
    project.mkdir(parents=True)
    (project / "src").mkdir()


def _force_unlock_and_rmtree(path):
    """解锁所有文件后删除（避免 PermissionError）"""
    import stat
    if not path.exists():
        return
    for p in path.rglob("*"):
        if p.is_file():
            try:
                p.chmod(p.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            except Exception:
                pass
    try:
        shutil.rmtree(path, onerror=lambda f, p, e: (
            os.chmod(p, os.stat(p).st_mode | 0o200) if os.path.exists(p) else None
        ))
    except Exception:
        pass

    # 准备初始文件
    (project / "src" / "hello.py").write_text(
        'def hello(name):\n    return f"Hello, {name}!"\n',
        encoding="utf-8")
    (project / "README.md").write_text("# Demo Project\n", encoding="utf-8")

    # 1. git init
    step("1/7] git init")
    run_git(["init", "-q"], project)
    run_git(["config", "user.email", "demo@example.com"], project)
    run_git(["config", "user.name", "Demo"], project)
    ok("git initialized")

    # 2. pandax init
    step("2/7] pandax init")
    rc, out, _ = run_cli(["init", "--root", str(project)], project)
    for line in out.splitlines():
        if "[OK]" in line or "[snapshot]" in line:
            print(f"  {line.strip()}")
    ok(f"PandaX initialized (rc={rc})")

    # 3. pandax lock
    step("3/7] pandax lock")
    rc, out, _ = run_cli(["lock", "--root", str(project)], project)
    for line in out.splitlines():
        if "[OK]" in line or "锁定" in line:
            print(f"  {line.strip()}")
    ok(f"Files locked (rc={rc})")

    # 4. 验证锁定（Python 尝试写）
    step("4/7] 攻击测试：尝试直接写入锁定文件")
    try:
        (project / "src" / "hello.py").write_text("X = 1\n", encoding="utf-8")
        err("BUG: 锁定文件居然可写！")
        return 1
    except (PermissionError, OSError) as e:
        ok(f"PermissionError（{type(e).__name__}）— 文件被锁")

    # 5. 通过 write 修改
    step("5/7] pandax write 合规修改")
    rc, out, _ = run_cli([
        "write", "--root", str(project),
        "--file", "src/hello.py",
        "--reason", "添加默认 name 参数",
        "--problem", "调用者经常忘传 name",
        "--approach", "默认值为 World",
        "--old", 'def hello(name):',
        "--new", 'def hello(name="World"):',
    ], project)
    for line in out.splitlines():
        if "APPROVED" in line or "[OK]" in line:
            print(f"  {line.strip()}")
    ok(f"Write approved (rc={rc})")

    # 6. 查看审计日志
    step("6/7] 查看审计日志")
    rc, out, _ = run_cli(["log", "--root", str(project), "--last", "5"], project)
    for line in out.splitlines():
        if "APPROVED" in line or "audit_" in line:
            print(f"  {line.strip()}")

    # 7. status 仪表盘
    step("7/7] status 仪表盘")
    rc, out, _ = run_cli(["status", "--root", str(project)], project)
    for line in out.splitlines():
        if any(kw in line for kw in ["[L", "总记录", "APPROVED", "[Phase", "[WARN]"]):
            print(f"  {line.strip()}")

    banner(f"Demo 1 完成 — 基础工作流演示")
    print(f"  项目保留: {project}")
    print(f"  清理: rm -rf {project}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())