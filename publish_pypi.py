#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_pypi.py — 一键发布到 PyPI

功能:
  - 清理旧的 dist/
  - 跑全部测试（确保通过）
  - 检查 git 状态（干净）
  - 检查 version 同步（pyproject.toml + setup.py + __init__.py）
  - 构建 wheel + sdist
  - 校验 wheel 元数据
  - 调用 twine 上传到 TestPyPI 或 PyPI
  - 显示 PyPI 页面预览链接

用法:
  python publish_pypi.py --target testpypi   # 干跑 → TestPyPI
  python publish_pypi.py --target pypi         # 正式发布 → PyPI
  python publish_pypi.py --skip-tests         # 跳过测试（紧急发布）

第一性原理:
  - 发布是高风险操作——必须用脚本而不是手工执行（避免漏步骤）
  - 每个步骤必须有"验证通过才能进入下一步"的硬性闸门
  - Twine 是 PyPA 官方工具，避免直接 curl 上传
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
SETUP = ROOT / "setup.py"
INIT = ROOT / "src" / "pandax" / "__init__.py"
DIST = ROOT / "dist"


# ============================================================
# 颜色输出
# ============================================================
class C:
    H = "\033[95m"   # 高亮（紫红）
    B = "\033[94m"   # 蓝
    G = "\033[92m"   # 绿
    Y = "\033[93m"   # 黄
    R = "\033[91m"   # 红
    W = "\033[0m"    # 重置


def step(msg):
    print(f"\n{C.B}━━━ {msg} ━━━{C.W}")


def ok(msg):
    print(f"{C.G}✓ {msg}{C.W}")


def warn(msg):
    print(f"{C.Y}⚠  {msg}{C.W}")


def err(msg):
    print(f"{C.R}✗ {msg}{C.W}")


def die(msg, code=1):
    err(msg)
    sys.exit(code)


# ============================================================
# 子步骤
# ============================================================
def get_version() -> str:
    """从 pyproject.toml 读取 version（单一事实源）"""
    content = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.M)
    if not m:
        die("pyproject.toml 缺少 version 字段")
    return m.group(1)


def check_version_sync(target_version: str):
    """检查 version 在 3 个地方一致"""
    step("检查 version 同步")

    # pyproject.toml
    pj_ver = re.search(r'^version\s*=\s*"([^"]+)"',
                       PYPROJECT.read_text(encoding="utf-8"), re.M).group(1)
    if pj_ver != target_version:
        die(f"pyproject.toml version={pj_ver} ≠ {target_version}")

    # setup.py
    su_ver = re.search(r'version\s*=\s*"([^"]+)"',
                       SETUP.read_text(encoding="utf-8")).group(1)
    if su_ver != target_version:
        die(f"setup.py version={su_ver} ≠ {target_version}")

    # __init__.py
    init_ver = re.search(r'__version__\s*=\s*"([^"]+)"',
                         INIT.read_text(encoding="utf-8")).group(1)
    if init_ver != target_version:
        die(f"__init__.py __version__={init_ver} ≠ {target_version}")

    ok(f"3 处版本号一致: {target_version}")


def _find_git():
    """探测 git 路径（PyInstaller / 简化 PATH 环境）"""
    candidates = [
        r"D:\软件\Git\cmd\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        shutil.which("git"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    return None


def check_git_clean():
    """检查 git 工作目录干净（无未提交修改）"""
    step("检查 git 状态")

    git_exe = _find_git()
    if not git_exe:
        warn("找不到 git，跳过此检查")
        return

    r = subprocess.run([git_exe, "status", "--porcelain"],
                       cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PATH": str(Path(git_exe).parent) + os.pathsep + os.environ.get("PATH", "")})
    if r.returncode != 0:
        warn(f"git status 失败（rc={r.returncode}），跳过此检查")
        return

    if r.stdout.strip():
        err("git 工作目录不干净：")
        print(r.stdout)
        die("请先提交所有修改再发布", code=2)

    # 查 HEAD
    r = subprocess.run([git_exe, "rev-parse", "--short", "HEAD"],
                       cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PATH": str(Path(git_exe).parent) + os.pathsep + os.environ.get("PATH", "")})
    commit = r.stdout.strip()
    ok(f"git 干净，HEAD={commit}")


def run_tests(skip: bool):
    """跑全部测试"""
    step("跑全部测试")
    if skip:
        warn("跳过测试（用户指定 --skip-tests）")
        return

    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        err("测试失败！")
        print(r.stdout[-2000:])
        print(r.stderr[-1000:])
        die("请先修复测试再发布", code=3)

    # 提取通过数
    m = re.search(r"(\d+) passed", r.stdout)
    count = m.group(1) if m else "?"
    ok(f"全部测试通过 ({count} passed)")


def clean_dist():
    """清理 dist/"""
    step("清理 dist/")
    if DIST.exists():
        shutil.rmtree(DIST)
        ok("旧 dist/ 已删除")
    else:
        ok("dist/ 不存在，跳过")


def build():
    """构建 wheel + sdist"""
    step("构建 wheel + sdist")

    # 1. 装 build（如果缺）
    r = subprocess.run([sys.executable, "-m", "pip", "show", "build"],
                       capture_output=True)
    if r.returncode != 0:
        warn("未安装 build，自动安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "build"],
                       check=True)

    # 2. build
    r = subprocess.run([sys.executable, "-m", "build", "--no-isolation"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        err("build 失败：")
        print(r.stdout[-2000:])
        print(r.stderr[-1000:])
        die("请修复 build 错误", code=4)

    ok("wheel + sdist 构建成功")

    # 列出产物
    print(f"\n{C.W}构建产物：{C.W}")
    for f in sorted(DIST.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"  {C.H}{f.name}{C.W}  ({size_kb:.1f} KB)")


def verify_wheel():
    """校验 wheel 内容"""
    step("校验 wheel 元数据")

    whl_files = list(DIST.glob("*.whl"))
    if not whl_files:
        die("未生成 .whl 文件")
    whl = whl_files[0]
    ok(f"wheel 文件: {whl.name}")

    # 用 twine check 验证元数据
    r = subprocess.run([sys.executable, "-m", "twine", "check", str(whl)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        err("twine check 失败：")
        print(r.stdout)
        print(r.stderr)
        die("元数据不合法", code=5)
    ok("wheel 元数据合法")


def upload(target: str, dry_run: bool):
    """上传到 PyPI / TestPyPI"""
    step(f"上传到 {target}")

    if dry_run:
        warn("--dry-run 指定，跳过实际上传")
        return

    repo_url = {
        "pypi": "https://upload.pypi.org/legacy/",
        "testpypi": "https://test.pypi.org/legacy/",
    }[target]

    r = subprocess.run([
        sys.executable, "-m", "twine", "upload",
        "--repository-url", repo_url,
        str(DIST / f"pandax-{get_version()}-py3-none-any.whl"),
        str(DIST / f"pandax-{get_version()}.tar.gz"),
    ], cwd=ROOT)

    if r.returncode != 0:
        die(f"上传 {target} 失败", code=6)

    ok(f"已上传到 {target}")


def print_preview(target: str):
    """显示 PyPI 页面预览链接"""
    step("PyPI 页面预览")
    ver = get_version()
    if target == "pypi":
        url = f"https://pypi.org/project/pandax/{ver}/"
    else:
        url = f"https://test.pypi.org/project/pandax/{ver}/"
    print(f"\n{C.H}{url}{C.W}\n")


def show_install_instructions(target: str):
    """显示用户安装命令"""
    step("用户安装命令")

    if target == "pypi":
        print(f"\n{C.G}任何用户都可以用以下命令安装：{C.W}\n")
        print(f"  pip install pandax")
        print(f"  pip install pandax=={get_version()}")
        print(f"  pip install pandax --upgrade")
    else:
        print(f"\n{C.G}TestPyPI 测试安装：{C.W}\n")
        print(f"  pip install --index-url https://test.pypi.org/simple/ \\")
        print(f"              --extra-index-url https://pypi.org/simple/ \\")
        print(f"              pandax")


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="一键发布 pandax 到 PyPI")
    parser.add_argument("--target", choices=["pypi", "testpypi"],
                        default="testpypi",
                        help="发布目标（默认 testpypi 干跑）")
    parser.add_argument("--skip-tests", action="store_true",
                        help="跳过测试（紧急发布）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只构建不上传")
    args = parser.parse_args()

    print(f"{C.H}{'=' * 60}{C.W}")
    print(f"{C.H}  pandax 发布脚本 v1.0{C.W}")
    print(f"{C.H}  目标: {args.target.upper()}{C.W}")
    print(f"{C.H}  模式: {'DRY-RUN' if args.dry_run else '实际发布'}{C.W}")
    print(f"{C.H}{'=' * 60}{C.W}")

    # 1. version 检查
    version = get_version()
    ok(f"当前 version: {version}")
    check_version_sync(version)

    # 2. git 干净
    check_git_clean()

    # 3. 测试
    run_tests(args.skip_tests)

    # 4. 清理 + build
    clean_dist()
    build()

    # 5. 验证
    verify_wheel()

    # 6. 上传
    upload(args.target, args.dry_run)

    # 7. 后置
    print_preview(args.target)
    show_install_instructions(args.target)

    print(f"\n{C.G}{'=' * 60}")
    if args.dry_run:
        print(f"  ✓ DRY-RUN 完成")
    else:
        print(f"  ✓ 发布成功到 {args.target}")
    print(f"{'=' * 60}{C.W}\n")


if __name__ == "__main__":
    main()