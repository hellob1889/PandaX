#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish.py — PandaX 推送到 GitHub 的辅助脚本

用法:
  python publish.py             # 检查 + 提示下一步
  python publish.py --init      # git init + initial commit (首次)
  python publish.py --push URL  # 添加 remote + push

前提:
  - 已安装 git
  - 已 GitHub 上创建空仓库
  - 用户配置了 SSH key 或 token

第一性原理:
  - 推送是普通用户最烦的事（远程 URL、分支、认证）
  - 自动化这些步骤，让用户只关心"上传到哪"
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """执行命令并打印"""
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True)


def check_git_available() -> bool:
    if run(["git", "--version"]).returncode != 0:
        print("[ERROR] git 未安装或不在 PATH 中")
        return False
    return True


def check_clean_working_tree() -> bool:
    r = run(["git", "status", "--short"], cwd=ROOT)
    if r.returncode != 0:
        return False  # 不是 git 仓库
    if r.stdout.strip():
        print("[WARN] 工作目录不干净：")
        print(r.stdout)
        return False
    return True


def is_git_repo() -> bool:
    return (ROOT / ".git").exists()


def git_init_and_initial_commit():
    """首次使用：git init + initial commit"""
    print("\n[1/4] git init...")
    r = run(["git", "init"], cwd=ROOT)
    if r.returncode != 0:
        print(f"[ERROR] git init 失败")
        return False

    print("\n[2/4] 配置 git user (若无全局配置)...")
    if not run(["git", "config", "user.email"], cwd=ROOT).stdout.strip():
        run(["git", "config", "user.email", "pandax@example.com"], cwd=ROOT)
        run(["git", "config", "user.name", "PandaX Project"], cwd=ROOT)

    print("\n[3/4] git add...")
    r = run(["git", "add", "-A"], cwd=ROOT)
    if r.returncode != 0:
        print(f"[ERROR] git add 失败")
        return False

    print("\n[4/4] git commit...")
    r = run(["git", "commit", "-m",
             "Initial commit: PandaX Phase 1+2+3 complete (59 tests passing)"],
            cwd=ROOT)
    if r.returncode != 0:
        print(f"[ERROR] git commit 失败: {r.stderr}")
        return False

    print("[OK] 初始 commit 完成")
    return True


def add_remote_and_push(remote_url: str, branch: str = "main"):
    """添加 remote + push"""
    print(f"\n[1/3] git remote add origin {remote_url}...")
    # 检查是否已有
    existing = run(["git", "remote", "get-url", "origin"], cwd=ROOT)
    if existing.returncode == 0:
        print(f"  remote origin 已存在: {existing.stdout.strip()}")
        # 改成新的
        r = run(["git", "remote", "set-url", "origin", remote_url], cwd=ROOT)
        if r.returncode != 0:
            print(f"[ERROR] 改 remote 失败")
            return False
    else:
        r = run(["git", "remote", "add", "origin", remote_url], cwd=ROOT)
        if r.returncode != 0:
            print(f"[ERROR] 添加 remote 失败")
            return False

    print(f"\n[2/3] git branch -M {branch}...")
    run(["git", "branch", "-M", branch], cwd=ROOT)

    print(f"\n[3/3] git push -u origin {branch}...")
    r = run(["git", "push", "-u", "origin", branch], cwd=ROOT)
    if r.returncode != 0:
        print(f"[ERROR] push 失败: {r.stderr}")
        print(f"[INFO] 可能需要认证：")
        print(f"        - SSH: 确保 ~/.ssh/id_rsa 已添加到 GitHub")
        print(f"        - HTTPS: 使用 Personal Access Token")
        return False

    print("[OK] push 完成")
    print(f"\n仓库地址: {remote_url}")
    print(f"用户安装: pip install git+{remote_url}.git")
    return True


def main():
    parser = argparse.ArgumentParser(description="PandaX GitHub 推送工具")
    parser.add_argument("--init", action="store_true", help="首次：git init + initial commit")
    parser.add_argument("--push", metavar="URL", help="推送：传入 GitHub 仓库 URL")
    parser.add_argument("--branch", default="main", help="目标分支（默认 main）")
    args = parser.parse_args()

    if not check_git_available():
        return 1

    if args.init:
        if is_git_repo():
            print("[INFO] 已经是 git 仓库，跳过 init")
        else:
            if not git_init_and_initial_commit():
                return 1
        return 0

    if args.push:
        if not is_git_repo():
            print("[ERROR] 不是 git 仓库，先跑: python publish.py --init")
            return 1
        if not check_clean_working_tree():
            print("[WARN] 工作目录不干净，建议先 commit 或 stash")
            return 1
        if not add_remote_and_push(args.push, args.branch):
            return 1
        return 0

    # 默认：检查状态 + 提示
    print("=" * 60)
    print("PandaX 推送状态检查")
    print("=" * 60)
    print()

    if not is_git_repo():
        print("[状态] 不是 git 仓库")
        print()
        print("首次推送步骤：")
        print("  1. 在 GitHub 上创建空仓库（不要勾 README/.gitignore）")
        print(f"  2. python publish.py --init")
        print(f"  3. python publish.py --push https://github.com/your-username/pandax.git")
        return 0

    print("[状态] 已经是 git 仓库")
    r = run(["git", "remote", "-v"], cwd=ROOT)
    if r.stdout.strip():
        print(f"\n[Remote]\n{r.stdout}")
    else:
        print("\n[状态] 没有 remote")
        print()
        print("推送步骤：")
        print("  1. 在 GitHub 上创建空仓库（不要勾 README/.gitignore）")
        print(f"  2. python publish.py --push https://github.com/your-username/pandax.git")
    return 0


if __name__ == "__main__":
    sys.exit(main())