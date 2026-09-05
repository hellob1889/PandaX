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


@pytest.fixture(scope="session", autouse=True)
def force_zh_cn_for_tests():
    """全局 fixture：测试期间强制 ~/.pandax/config.json lang=zh-CN。

    第一性原则：测试断言中包含中文字符串（如 '已安装'、'锁定'、'未运行'）。
    如果某测试改了 lang=config.json=en，这些断言会全部失败，造成 flaky test。
    强制锁定 zh-CN 让测试行为可预测。

    实现策略：直接覆盖用户 ~/.pandax/config.json（不是用 env var）。
    为什么不用 env var：test_i18n.py::test_init_loads_existing_preference 用 monkeypatch
    改 HOME 后调用 init()，验证从 config.json 读取偏好。如果用 env var 覆盖，
    init() 会跳过 config.json 读取，测试失败。

    副作用：测试结束后会恢复用户原始 lang（如果之前存在）。
    """
    cfg_path = Path.home() / ".pandax" / "config.json"
    backup = None
    backup_existed = cfg_path.exists()

    if backup_existed:
        try:
            backup = cfg_path.read_text(encoding="utf-8")
            cfg = json.loads(backup)
            cfg["lang"] = "zh-CN"
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            backup = None

    yield

    # 恢复
    if backup is not None:
        try:
            cfg_path.write_text(backup, encoding="utf-8")
        except Exception:
            pass
    elif backup_existed and not cfg_path.exists():
        # 用户原本有但我们没备份成功——尽量恢复（保守处理）
        pass
