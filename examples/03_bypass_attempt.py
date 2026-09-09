"""
03_bypass_attempt.py
=====================
PandaX 7 层防御实战 demo

演示：尝试用各种方法绕过审计门禁，验证拦截
预期：所有攻击都被对应层拦截
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


def fail(msg):
    print(f"  {C.R}❌ {msg}{C.W}")


def warn(msg):
    print(f"  {C.Y}⚠️  {msg}{C.W}")


def find_src():
    here = Path(__file__).resolve().parent
    for p in [here.parent, here.parent.parent]:
        if (p / "src" / "pandax" / "__init__.py").exists():
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
    r = subprocess.run([sys.executable, "-m", "pandax", *args],
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
    project = Path("demo_03_bypass").resolve()
    print(f"\n[Demo] PandaX 7 层防御实战")
    print(f"  Project: {project}\n")

    if project.exists():
        import stat
        for p in project.rglob("*"):
            if p.is_file():
                try:
                    p.chmod(p.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                except Exception:
                    pass
        shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    (project / "src").mkdir()

    # 准备
    (project / "src" / "main.py").write_text("INITIAL = 1\n", encoding="utf-8")
    git(["init", "-q"], project)
    git(["config", "user.email", "demo@example.com"], project)
    git(["config", "user.name", "Demo"], project)
    cli(["init", "--root", str(project)], project)
    cli(["lock", "--root", str(project)], project)

    # 先做一次合规 write + 初始 commit（建立基线）
    cli(["write", "--root", str(project),
         "--file", "src/main.py",
         "--reason", "initial commit",
         "--problem", "需要初始 commit 作为 CI 基线",
         "--approach", "通过 write 创建初始审计记录",
         "--old", "INITIAL = 1",
         "--new", "INITIAL = 1"], project)
    git(["add", "-A"], project)
    git(["commit", "-m", "initial"], project)
    print(f"  ✓ 初始 commit 已建立")

    # ================================================================
    # 攻击 1: 直接 write 锁定文件（L1 拦截）
    # ================================================================
    step("攻击 1/5] 直接 write 锁定文件（攻击 L1）")
    main_file = project / "src" / "main.py"
    try:
        main_file.write_text("HIJACK = True\n", encoding="utf-8")
        fail("BUG: L1 失效！")
        return 1
    except (PermissionError, OSError):
        ok("L1 拦截：PermissionError")

    # ================================================================
    # 攻击 2: chmod +w 后 write（L1 失守，依赖 L2 兜底）
    # ================================================================
    step("攻击 2/5] chmod +w + write（L1 失守）")
    os.chmod(main_file, main_file.stat().st_mode | 0o200)
    try:
        main_file.write_text("HIJACK = True\n", encoding="utf-8")
        warn("L1 被 chmod 解除（攻击者拿到 root 权限场景）")
        warn("现实：依赖 L2/L3/L7 多层兜底")
    except (PermissionError, OSError):
        ok("L1 仍拦截")

    # ================================================================
    # 攻击 3: install-hook + 直接 git commit（攻击 L3）
    # ================================================================
    step("攻击 3/5] 装 hook + 提交新文件（攻击 L3）")
    cli(["install-hook", "--root", str(project)], project)
    (project / "src" / "evil.py").write_text("EVIL = True\n", encoding="utf-8")
    git(["add", "src/evil.py"], project)
    rc, out, err = git(["commit", "-m", "bypass"], project)
    if rc != 0:
        ok(f"L3 拦截：hook 拒绝 commit (rc={rc})")
        for line in (out + err).splitlines():
            if "PandaX" in line or "未审计" in line:
                print(f"    {line.strip()}")
                break
    else:
        fail("BUG: L3 hook 失效！")
        return 1

    # ================================================================
    # 攻击 4: --no-verify 绕过 hook（依赖 L7 CI 兜底）
    # ================================================================
    step("攻击 4/5] git commit --no-verify（绕过 L3）")
    rc, out, err = git(["commit", "--no-verify", "-m", "force bypass"], project)
    if rc == 0:
        warn("L3 被 --no-verify 绕过（攻击者用逃生通道）")
        warn("现实：依赖 L7 CI 兜底")

    # ================================================================
    # 攻击 5: CI 验证（最终兜底）
    # ================================================================
    step("攻击 5/5] pandax ci（L7 最终验证）")
    # 先看有几个 commit，确保 HEAD~1 存在
    _, out, _ = git(["log", "--oneline"], project)
    commit_count = len([l for l in out.splitlines() if l.strip()])
    if commit_count < 2:
        warn(f"只有 {commit_count} 个 commit，CI 需要至少 2 个，跳过")
    else:
        rc, out, _ = cli(["ci", "--root", str(project), "--base", "HEAD~1"], project)
        if rc != 0:
            ok(f"L7 拦截：CI 检测到未审计的 src/evil.py (rc={rc})")
            for line in out.splitlines():
                if "FAIL" in line or "未审计" in line or "[文本" in line:
                    print(f"    {line.strip()}")
        else:
            fail("BUG: L7 CI 失效！")
            return 1

    banner("Demo 3 完成 — 所有攻击都被对应层拦截")
    return 0


if __name__ == "__main__":
    sys.exit(main())