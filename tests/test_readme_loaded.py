"""
test_readme_loaded.py
=====================
RED 测试：CLI 每次启动必须读取 README.md 并显示当前阶段 / 步骤状态。

第一性原理：
  README 是 CLI 的"运行时数据源"。如果 CLI 不读 README，
  开发者 / agent 就无法同步设计意图与当前进度。

测试策略：
  - 通过 subprocess 调用 `python pandax.py` 无子命令
  - 期望 stdout 包含 README 中的关键标识（"Phase 1"、"CLI MVP"）
  - 这是机制的核心保证，必须从第一个版本就锁定
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandax_dev.py"
README = ROOT / "README.md"


def test_pandax_file_exists():
    """pandax.py 必须存在（前置条件）"""
    assert PANDAX.exists(), f"pandax.py 不存在: {PANDAX}"


def test_readme_file_exists():
    """README.md 必须存在（CLI 启动读取对象）"""
    assert README.exists(), f"README.md 不存在: {README}"


def test_cli_loads_readme_on_startup():
    """
    RED 测试：CLI 无参数启动时必须读取 README，
    输出应包含 README 的"当前阶段"段落标识。
    """
    result = subprocess.run(
        [sys.executable, str(PANDAX)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )

    # 失败当前：pandax.py 还不存在，subprocess 会报 FileNotFoundError 或非零退出
    assert result.returncode == 0, (
        f"CLI 启动失败: rc={result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

    # 必须显示 README 的当前阶段标识
    assert "Phase" in result.stdout, (
        f"CLI 启动输出未包含 README 当前阶段标识 'Phase'\n"
        f"实际输出: {result.stdout}"
    )


def test_cli_shows_completed_steps():
    """
    RED 测试：CLI 启动应显示已完成步骤列表（来自 README）。
    """
    result = subprocess.run(
        [sys.executable, str(PANDAX)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, (
        f"CLI 启动失败: rc={result.returncode}\n"
        f"stderr: {result.stderr}"
    )

    # 必须包含"已完成的 Step"或类似标记（来自 README）
    assert ("已完成" in result.stdout) or ("[x]" in result.stdout), (
        f"CLI 启动输出未显示已完成步骤\n"
        f"实际输出: {result.stdout}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
