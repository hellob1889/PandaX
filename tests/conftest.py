"""
conftest.py
===========
pytest 全局配置：自动探测 git 路径并加入 PATH。

第一性原理：
  - git 是 PandaX 的关键依赖（用于自动 commit）
  - 用户可能 git 装在非默认路径（如 D:\软件\Git\）
  - 测试不应假设 git 在 PATH 中

策略：
  - 探测常见 git 安装路径
  - 找到第一个存在的 git.exe 加到 PATH
  - 测试用 subprocess 启动时就会继承此 PATH
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

# 常见 git 安装位置（Windows）
GIT_CANDIDATES = [
    r"D:\软件\Git\cmd",
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files (x86)\Git\cmd",
    r"C:\Program Files\Git\bin",
]


def _find_git_dir() -> str | None:
    """返回第一个含 git.exe 的目录"""
    # 1. 先看 PATH 里有没有
    if shutil.which("git"):
        return None  # 已在 PATH，不动
    # 2. 探测候选路径
    for cand in GIT_CANDIDATES:
        if Path(cand, "git.exe").exists():
            return cand
    # 3. 用 where.exe 兜底
    try:
        r = subprocess.run(["where.exe", "git"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            first = r.stdout.strip().splitlines()[0]
            return str(Path(first).parent)
    except Exception:
        pass
    return None


# 把 src/ 加到 sys.path 和 PYTHONPATH（让 subprocess 启动的 python 也能找到 package）
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# PYTHONPATH 让 subprocess 继承（开发模式下 `python -m pandax_guard` 能找到）
os.environ["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + os.environ.get("PYTHONPATH", "")


# 模块导入时立即把 git 加入 PATH
_git_dir = _find_git_dir()
if _git_dir:
    os.environ["PATH"] = _git_dir + os.pathsep + os.environ.get("PATH", "")


@pytest.fixture(scope="session", autouse=True)
def verify_git_available():
    """全局 fixture：测试开始前确认 git 可用，否则 skip"""
    if not shutil.which("git"):
        pytest.skip("git 未安装且未在 PATH 中找到，PandaX 测试需要 git")
