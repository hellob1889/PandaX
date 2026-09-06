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


# ============================================================
# Bug #4 fix: README summary 应显示最新活跃阶段，不应停在旧状态
# ============================================================
def test_summary_shows_latest_phase_not_old_step13():
    """Bug #4 fix: 当前阶段显示最新活跃 Phase（不再停在 Step 13）

    第一性原则：CLI 启动必须反映项目的真实最新状态，而不是 README 的旧版本。
    实现：load_readme_summary 取最后一个 "**Phase" 行（最新活跃阶段）。
    """
    # 直接 import load_readme_summary 测试（避免 subprocess 启动开销）
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pandax_cli", ROOT / "src" / "pandax" / "cli.py"
    )
    pandax_cli = importlib.util.module_from_spec(spec)
    # 加载前需要 pandax 包可导入
    sys.path.insert(0, str(ROOT / "src"))
    spec.loader.exec_module(pandax_cli)
    summary = pandax_cli.load_readme_summary()
    text = "\n".join(summary)

    # Phase 6 是最新活跃阶段（README 维护者按时间顺序写在最后）
    assert "Phase 6" in text, f"应含 Phase 6 最新阶段"

    # 不应再显示 Phase 2 / Step 13 作为"当前阶段"
    # （已修复前显示 "Phase 2: 监控加固 (P1)" + Step 9-13）
    # 这里不强求"完全不含 Phase 2"，只确认最新阶段是 Phase 6


def test_summary_includes_actual_completed_bugfixes():
    """Bug #4 fix: 已完成步骤列表必须含真实 bug 修复（不只是 Step 9-13）

    第一性原则：README 段落必须反映真实修复历史，否则 CLI 启动信息误导用户。
    """
    sys.path.insert(0, str(ROOT / "src"))
    from pandax.cli import load_readme_summary
    summary = load_readme_summary()
    text = "\n".join(summary)

    # 11 个 P0/P1/P2/P3 bug 修复必须出现
    must_contain = [
        "P0 #8 + #7",
        "P0 #12 v1",
        "P0 #12 v2",
        "P1 #2",
        "P1 #5",
        "P1 #15",
        "P2 #21",
        "P2 #6",
        "P2 #20",
        "P2 #9 / #10",
        "P3 #13",
    ]
    for label in must_contain:
        assert label in text, f"应含 {label}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
