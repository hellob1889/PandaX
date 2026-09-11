"""
test_init.py
============
RED 测试：pandaone init 子命令

第一性原理：
  init 必须在当前文件夹创建 .pandaone/ 目录 + config.json + pandaone.jsonl。
  这三个文件是审计系统存在的前提。

测试策略：
  - 使用 pytest tmp_path 隔离文件系统
  - 子进程调用 `python pandaone.py init --root <tmp>`
  - 检查目录与文件是否创建
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandaone_dev.py"


def run_init(target_dir: Path):
    """调用 pandaone init --root <target_dir>"""
    return subprocess.run(
        [sys.executable, str(PANDAX), "init", "--root", str(target_dir)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_init_creates_pandaone_directory(tmp_path):
    """init 后 .pandaone/ 目录必须存在"""
    result = run_init(tmp_path)
    assert result.returncode == 0, (
        f"init 失败: rc={result.returncode}\nstderr: {result.stderr}"
    )

    pandaone_dir = tmp_path / ".pandaone"
    assert pandaone_dir.exists(), f".pandaone/ 目录未创建: {pandaone_dir}"
    assert pandaone_dir.is_dir(), ".pandaone 必须是目录"


def test_init_creates_config_json(tmp_path):
    """init 后 .pandaone/config.json 必须存在且合法"""
    run_init(tmp_path)

    config_path = tmp_path / ".pandaone" / "config.json"
    assert config_path.exists(), f"config.json 未创建: {config_path}"

    # 必须是合法 JSON
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "version" in data, "config.json 必须含 version 字段"
    assert "project_root" in data, "config.json 必须含 project_root 字段"
    assert "protected_extensions" in data, "config.json 必须含 protected_extensions 字段"


def test_init_creates_audit_log(tmp_path):
    """init 后 .pandaone/pandaone.jsonl 必须存在（空文件可）"""
    run_init(tmp_path)

    audit_path = tmp_path / ".pandaone" / "pandaone.jsonl"
    assert audit_path.exists(), f"pandaone.jsonl 未创建: {audit_path}"


def test_init_idempotent(tmp_path):
    """二次 init 不能崩溃（覆盖或追加皆可，但不应报错）"""
    r1 = run_init(tmp_path)
    r2 = run_init(tmp_path)

    assert r1.returncode == 0, f"首次 init 失败: {r1.stderr}"
    assert r2.returncode == 0, f"二次 init 失败: {r2.stderr}"


def test_init_uses_specified_root(tmp_path):
    """--root 参数指定路径必须生效"""
    custom = tmp_path / "my_project"
    custom.mkdir()

    run_init(custom)

    assert (custom / ".pandaone").exists(), "--root 路径未生效"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
