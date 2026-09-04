"""
test_lock.py
============
RED 测试：pandax lock / unlock 子命令

第一性原理：
  L1 防御 = OS 级文件锁。lock 后所有 Python 写文件操作（open 'w' / 'a'）必须失败。
  这是物理不可绕过的拦截。

测试策略：
  - 隔离：tmp_path 建临时项目 + init + 写入测试 .py
  - 锁后：用 open('w') 尝试写入，期望 PermissionError
  - 解锁后：写入应成功
  - 排除：__pycache__/test.py、_tmp_test.py 不应被锁
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandax_dev.py"


def run_cmd(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PANDAX), *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        timeout=20,
    )


def setup_project(tmp_path: Path) -> Path:
    """在 tmp_path 建一个最小可测试项目：init + 2 个 .py + 1 个 _tmp_*.py"""
    run_cmd(["init", "--root", str(tmp_path)], cwd=tmp_path)

    (tmp_path / "main.py").write_text("def main(): pass\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")
    # 排除的文件
    (tmp_path / "_tmp_test.py").write_text("# tmp\n", encoding="utf-8")
    return tmp_path


def test_lock_makes_files_readonly(tmp_path):
    """lock 后 .py 文件写入应失败"""
    setup_project(tmp_path)
    result = run_cmd(["lock", "--root", str(tmp_path)], cwd=tmp_path)
    assert result.returncode == 0, f"lock 失败: {result.stderr}"

    target = tmp_path / "main.py"
    with pytest.raises((PermissionError, OSError)):
        with open(target, "w", encoding="utf-8") as f:
            f.write("# should fail\n")


def test_unlock_restores_writable(tmp_path):
    """unlock 后 .py 文件可写"""
    setup_project(tmp_path)
    run_cmd(["lock", "--root", str(tmp_path)], cwd=tmp_path)

    result = run_cmd(["unlock", "--root", str(tmp_path)], cwd=tmp_path)
    assert result.returncode == 0, f"unlock 失败: {result.stderr}"

    # 现在应该可写
    target = tmp_path / "main.py"
    target.write_text("# updated\n", encoding="utf-8")
    assert "# updated" in target.read_text(encoding="utf-8")


def test_lock_excludes_tmp_files(tmp_path):
    """lock 不应锁定 _tmp_*.py（排除规则）"""
    setup_project(tmp_path)
    run_cmd(["lock", "--root", str(tmp_path)], cwd=tmp_path)

    # _tmp_test.py 应仍可写
    tmp_file = tmp_path / "_tmp_test.py"
    try:
        tmp_file.write_text("# still writable\n", encoding="utf-8")
    except (PermissionError, OSError) as e:
        pytest.fail(f"_tmp_*.py 不应被锁定，但仍报: {e}")


def test_lock_reports_count(tmp_path):
    """lock 输出应包含锁定文件数"""
    setup_project(tmp_path)
    result = run_cmd(["lock", "--root", str(tmp_path)], cwd=tmp_path)

    assert result.returncode == 0
    # 应输出数量信息
    assert ("锁定" in result.stdout) or ("locked" in result.stdout.lower())


def test_lock_without_init_fails_gracefully(tmp_path):
    """未 init 的目录 lock 应优雅处理（不崩溃）"""
    # tmp_path 没有 .pandax/，应报错但不崩溃
    result = run_cmd(["lock", "--root", str(tmp_path)], cwd=tmp_path)
    # 期望：要么 rc != 0，要么有警告信息（取决于设计）
    # 决策：rc != 0 + stderr 报错
    assert result.returncode != 0, "未 init 的目录 lock 应失败"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
