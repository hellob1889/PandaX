"""
test_lock_auto_init.py
=======================
Bug #28 (方案 A) RED 测试：pandaone lock 未初始化时自动调用 init。

第一性原理（用户痛点）：
  - 首次用户右击文件夹 → Pandaone AI Agent → Lock
  - 现状：失败 [ERROR] not initialized → 用户困惑 → 必须再点 Init
  - 修复：lock 检测到未 init 时自动调用 init（一步到位）
  - 反向控制：--no-auto-init 让高级用户分阶段操作

测试场景：
  1. test_lock_auto_init_when_uninitialized：未 init 目录 lock → 自动 init + lock
  2. test_lock_no_auto_init_skips_when_uninitialized：--no-auto-init 仍报 [ERROR]
  3. test_lock_no_auto_init_when_already_inited：已 init 目录 lock 不重复 init
  4. test_unlock_does_not_auto_init：unlock 在未 init 目录应报错（不解锁空目录）
  5. test_lock_auto_init_creates_config_and_locks_files：端到端验证
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"


def _run(args, cwd, env_extra=None, lang="zh-CN"):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PANDAX_LANG"] = lang
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "pandaone", *args],
        cwd=cwd, capture_output=True, text=True, env=env, timeout=15,
    )


def _make_py_project(project: Path, file_count: int = 3):
    """建项目目录 + 若干 .py 文件 + .json 文件"""
    project.mkdir(parents=True, exist_ok=True)
    for i in range(file_count):
        (project / f"module_{i}.py").write_text(f"# module {i}\n", encoding="utf-8")
    (project / "config.json").write_text('{"key": "value"}', encoding="utf-8")
    # 加一个非受保护文件
    (project / "README.txt").write_text("hello", encoding="utf-8")


# ============================================================
# Bug #28 (方案 A): lock 自动 init
# ============================================================

class TestLockAutoInit:
    """Bug #28 — pandaone lock 未初始化时自动 init（方案 A）"""

    def test_lock_auto_init_when_uninitialized(self, tmp_path):
        """未 init 目录 lock 应自动 init + 锁定文件（一键到底）"""
        project = tmp_path / "fresh"
        _make_py_project(project)

        # 关键断言：未 init 之前没有 .pandaone/
        assert not (project / ".pandaone").exists()

        r = _run(["lock", "--root", str(project)], project, lang="zh-CN")
        assert r.returncode == 0, f"lock failed: {r.stderr}"

        # 自动 init 应创建 .pandaone/
        assert (project / ".pandaone" / "config.json").exists(), (
            "Bug #28 回归：lock 未自动创建 .pandaone/config.json"
        )
        # 应打印自动 init 提示
        assert "自动调用 init" in r.stdout or "info_lock_auto_init" in r.stdout or \
               "[INFO]" in r.stdout, (
            f"Bug #28 回归：lock 未打印自动 init 提示: {r.stdout}"
        )

    def test_lock_no_auto_init_flag_skips_init(self, tmp_path):
        """--no-auto-init 时未 init 目录 lock 应报错（保持旧行为）"""
        project = tmp_path / "fresh"
        _make_py_project(project)

        r = _run(["lock", "--root", str(project), "--no-auto-init"], project, lang="zh-CN")
        # 返回非 0
        assert r.returncode != 0, (
            f"Bug #28 回归：--no-auto-init 应报错，但仍成功: {r.stdout}"
        )
        # 不应创建 .pandaone/
        assert not (project / ".pandaone").exists(), (
            "Bug #28 回归：--no-auto-init 仍创建了 .pandaone/（应为禁止）"
        )
        # 应打印未初始化错误
        combined = r.stdout + r.stderr
        assert "未初始化" in combined or "not initialized" in combined.lower()

    def test_lock_no_auto_init_when_already_inited(self, tmp_path):
        """已 init 目录 lock 不应重复 init（无论 --no-auto-init 与否）"""
        project = tmp_path / "inited"
        _make_py_project(project)

        # 先正常 init
        r = _run(["init", "--root", str(project)], project)
        assert r.returncode == 0
        config_mtime_before = (project / ".pandaone" / "config.json").stat().st_mtime

        # 等 1 秒确保 mtime 不同
        import time
        time.sleep(1.1)

        # lock --no-auto-init
        r = _run(["lock", "--root", str(project), "--no-auto-init"], project)
        assert r.returncode == 0, f"lock failed: {r.stderr}"
        # config.json 不应被重新写入
        config_mtime_after = (project / ".pandaone" / "config.json").stat().st_mtime
        assert config_mtime_after == config_mtime_before, (
            f"Bug #28 回归：已 init 目录 lock 重复初始化（mtime 变化）"
        )

    def test_lock_skips_auto_init_when_already_inited(self, tmp_path):
        """已 init 目录 lock（无 flag）不应重复 init（默认行为）"""
        project = tmp_path / "inited"
        _make_py_project(project)
        _run(["init", "--root", str(project)], project)

        import time
        mtime_before = (project / ".pandaone" / "config.json").stat().st_mtime
        time.sleep(1.1)

        r = _run(["lock", "--root", str(project)], project)
        assert r.returncode == 0
        mtime_after = (project / ".pandaone" / "config.json").stat().st_mtime
        assert mtime_after == mtime_before, (
            f"Bug #28 回归：已 init 目录 lock 默认行为重复初始化"
        )

    def test_unlock_does_not_auto_init(self, tmp_path):
        """unlock 在未 init 目录应报错（不解锁空目录）"""
        project = tmp_path / "fresh"
        _make_py_project(project)

        r = _run(["unlock", "--root", str(project)], project, lang="zh-CN")
        assert r.returncode != 0, (
            f"Bug #28 回归：unlock 未 init 目录不应成功: {r.stdout}"
        )
        assert not (project / ".pandaone").exists(), (
            "Bug #28 回归：unlock 触发了 init（不应触发）"
        )
        combined = r.stdout + r.stderr
        assert "未初始化" in combined or "not initialized" in combined.lower()

    def test_lock_auto_init_actually_locks_files(self, tmp_path):
        """端到端：lock 应真实修改文件权限"""
        project = tmp_path / "fresh"
        _make_py_project(project)
        sample_py = project / "module_0.py"

        r = _run(["lock", "--root", str(project)], project)
        assert r.returncode == 0

        # 检查文件权限：Windows 下用 os.access 测试，Unix 用 stat.st_mode
        import stat as _stat
        mode = sample_py.stat().st_mode
        # 文件应只读（user write 被移除）
        assert not (mode & _stat.S_IWUSR), (
            f"Bug #28 回归：lock 后文件仍可写: mode={oct(mode)}"
        )

    def test_lock_auto_init_en_message(self, tmp_path):
        """en 模式下自动 init 提示应英文"""
        project = tmp_path / "fresh"
        _make_py_project(project)

        r = _run(["lock", "--root", str(project)], project, lang="en")
        assert r.returncode == 0
        assert "First use detected" in r.stdout or "auto-running init" in r.stdout, (
            f"Bug #28 回归：en 模式自动 init 提示未本地化: {r.stdout}"
        )


# ============================================================
# 对抗式审查（adversarial review）
# ============================================================

class TestLockAutoInitAdversarial:
    """对抗式审查：极端场景下 auto-init 行为正确"""

    def test_lock_auto_init_does_not_overwrite_existing_config(self, tmp_path):
        """如果目录里有别人的 config.json（不是 Pandaone 的），不应被覆盖"""
        project = tmp_path / "has_other_config"
        _make_py_project(project)
        # 模拟其他工具的 config.json
        config_path = project / "config.json"
        original_content = '{"other_tool": "value"}'
        config_path.write_text(original_content, encoding="utf-8")

        # 但 .pandaone/config.json 不存在 → lock 应自动 init → 创建 .pandaone/config.json
        # 而**项目根的 config.json**（受保护）不应被覆盖
        r = _run(["lock", "--root", str(project)], project)
        assert r.returncode == 0
        # 项目根 config.json（被 lock 锁定的）内容不变
        assert config_path.read_text(encoding="utf-8") == original_content
        # .pandaone/config.json 应被创建
        assert (project / ".pandaone" / "config.json").exists()

    def test_lock_auto_init_uses_default_extensions(self, tmp_path):
        """auto-init 应使用默认 17 种扩展名（不是空）"""
        project = tmp_path / "fresh"
        _make_py_project(project)

        r = _run(["lock", "--root", str(project)], project)
        assert r.returncode == 0

        config = json.loads((project / ".pandaone" / "config.json").read_text(encoding="utf-8"))
        assert len(config["protected_extensions"]) >= 10, (
            f"auto-init 应使用默认扩展名，实际只有 {len(config['protected_extensions'])}"
        )
        assert ".py" in config["protected_extensions"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
