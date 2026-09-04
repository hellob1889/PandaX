"""
test_watchdog.py
================
RED 测试：pandax_guard.py 的 PandaXHandler

第一性原理：
  L2 防御必须在 L1 被绕过时捕获并回滚。
  但 Observer 启动测试很重，所以我们直接测试 Handler 类，
  验证：on_modified / on_created / on_moved 在不同令牌状态下的行为。

测试策略：
  - 用 tmp_path 建 git 项目
  - 创建 PandaXHandler 实例
  - 构造事件（直接调用 handler.on_modified() 等）
  - 验证副作用（git checkout 是否回滚 / auto_lock 是否生效 / 审计记录）
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pandax_guard import PandaXHandler  # noqa: E402


def setup_git_project(tmp_path: Path) -> Path:
    """建 git 项目 + init + lock + 初始 commit"""
    # pandax init
    r = subprocess.run(
        [sys.executable, str(ROOT / "pandax_dev.py"), "init", "--root", str(tmp_path)],
        cwd=str(tmp_path), capture_output=True, text=True,
    )
    assert r.returncode == 0

    # git init
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, capture_output=True, text=True)

    # 初始文件
    (tmp_path / "main.py").write_text("ORIGINAL = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, text=True)

    # pandax lock
    r = subprocess.run(
        [sys.executable, str(ROOT / "pandax_dev.py"), "lock", "--root", str(tmp_path)],
        cwd=str(tmp_path), capture_output=True, text=True,
    )
    assert r.returncode == 0

    return tmp_path


def make_event(src_path: str, dest_path: str | None = None, is_directory: bool = False):
    """构造一个 watchdog 事件的伪对象"""
    class FakeEvent:
        pass
    e = FakeEvent()
    e.src_path = src_path
    e.dest_path = dest_path or src_path
    e.is_directory = is_directory
    return e


def test_handler_exists():
    """PandaXHandler 必须可导入"""
    from pandax_guard import PandaXHandler
    assert PandaXHandler is not None


def test_modified_without_token_reverts(tmp_path):
    """on_modified 在无令牌时应回滚并写 UNAUTHORIZED 记录"""
    project = setup_git_project(tmp_path)
    main_py = project / "main.py"

    handler = PandaXHandler(project)
    # 模拟无令牌时直接修改（先 unlock 再写）
    main_py.chmod(main_py.stat().st_mode | stat.S_IWUSR)
    main_py.write_text("TAMPERED = 1\n", encoding="utf-8")

    # 触发 on_modified
    event = make_event(str(main_py))
    handler.on_modified(event)

    # 应被回滚
    content = main_py.read_text(encoding="utf-8")
    assert "TAMPERED" not in content, "文件应被回滚"
    assert "ORIGINAL" in content

    # 审计日志应有 UNAUTHORIZED 记录
    audit_path = project / ".pandax" / "pandax.jsonl"
    records = [
        json.loads(line) for line in
        audit_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    unauthorized = [r for r in records if r["status"] == "UNAUTHORIZED"]
    assert len(unauthorized) >= 1, "应有 UNAUTHORIZED 记录"
    assert "main.py" in unauthorized[-1]["file"]


def test_modified_with_token_passes(tmp_path):
    """on_modified 在有令牌时应放行"""
    project = setup_git_project(tmp_path)
    main_py = project / "main.py"

    # 设令牌
    token = project / ".pandax" / ".audit_token"
    token.write_text("test-token", encoding="utf-8")

    # 模拟合法写入
    main_py.chmod(main_py.stat().st_mode | stat.S_IWUSR)
    main_py.write_text("LEGITIMATE = 1\n", encoding="utf-8")

    handler = PandaXHandler(project)
    event = make_event(str(main_py))
    handler.on_modified(event)

    # 不应被回滚
    content = main_py.read_text(encoding="utf-8")
    assert "LEGITIMATE" in content, "合法写入应放行"

    # 不应有 UNAUTHORIZED 记录
    audit_path = project / ".pandax" / "pandax.jsonl"
    records = [
        json.loads(line) for line in
        audit_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    unauthorized = [r for r in records if r["status"] == "UNAUTHORIZED"]
    assert len(unauthorized) == 0, "有令牌时不应有 UNAUTHORIZED"


def test_created_auto_locks(tmp_path):
    """on_created 对新 .py 应自动锁定"""
    project = setup_git_project(tmp_path)
    new_py = project / "new_module.py"
    new_py.write_text("def new(): pass\n", encoding="utf-8")

    handler = PandaXHandler(project)
    event = make_event(str(new_py))
    handler.on_created(event)

    # 文件应被设为只读
    mode = new_py.stat().st_mode
    assert not (mode & stat.S_IWUSR), f"新文件应被自动锁定, mode={oct(mode)}"


def test_excluded_files_ignored(tmp_path):
    """__pycache__、_tmp_* 等应被忽略"""
    project = setup_git_project(tmp_path)

    # 创建 __pycache__
    cache_dir = project / "__pycache__"
    cache_dir.mkdir(exist_ok=True)
    cache_py = cache_dir / "main.cpython-310.pyc"
    cache_py.write_text("# cache\n", encoding="utf-8")

    # 创建 _tmp_*.py
    tmp_py = project / "_tmp_test.py"
    tmp_py.write_text("# tmp\n", encoding="utf-8")

    handler = PandaXHandler(project)

    # 这两个事件应被忽略
    handler.on_modified(make_event(str(cache_py)))
    handler.on_modified(make_event(str(tmp_py)))

    # 不应有 UNAUTHORIZED 记录
    audit_path = project / ".pandax" / "pandax.jsonl"
    records = [
        json.loads(line) for line in
        audit_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    unauthorized = [r for r in records if r["status"] == "UNAUTHORIZED"]
    assert len(unauthorized) == 0


# ============================================================
# Phase 4.6 — watchdog 应监控所有受保护格式（不只是 .py）
# ============================================================

def test_modified_md_without_token_reverts(tmp_path):
    """watchdog 应捕获并回滚 .md 文件的无令牌修改"""
    project = setup_git_project(tmp_path)
    md_file = project / "README.md"
    md_file.write_text("# Original\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=project, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "add md"], cwd=project, capture_output=True, text=True)

    handler = PandaXHandler(project)
    # 解锁 + 写
    md_file.chmod(md_file.stat().st_mode | stat.S_IWUSR)
    md_file.write_text("# Hacked\n", encoding="utf-8")

    handler.on_modified(make_event(str(md_file)))

    # 应被回滚
    content = md_file.read_text(encoding="utf-8")
    assert "Hacked" not in content, "md 文件应被 watchdog 回滚"
    assert "Original" in content

    # 审计日志应有 UNAUTHORIZED 记录
    audit_path = project / ".pandax" / "pandax.jsonl"
    records = [
        json.loads(line) for line in
        audit_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    unauthorized = [r for r in records if r["status"] == "UNAUTHORIZED"]
    assert len(unauthorized) >= 1
    assert "README.md" in unauthorized[-1]["file"]


def test_modified_png_ignored(tmp_path):
    """watchdog 不应监控 .png（二进制不在 protected_extensions）"""
    project = setup_git_project(tmp_path)
    png_file = project / "logo.png"
    png_file.write_bytes(b"\x89PNG\r\n\x1a\nORIGINAL")

    handler = PandaXHandler(project)
    # 修改 .png 不应触发回滚（不在监控范围）
    png_file.write_bytes(b"NEW")

    handler.on_modified(make_event(str(png_file)))

    # .png 应保持新内容（watchdog 没碰它）
    assert png_file.read_bytes() == b"NEW"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
