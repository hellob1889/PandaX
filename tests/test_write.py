"""
test_write.py
=============
RED 测试：pandax write 子命令（核心）

第一性原理：
  write 是审计的"内联检测点"：
    1. 水质检测（reason/problem/approach 必填且满足长度）
    2. 设令牌 → 解锁 → 写入 → 锁回 → 清令牌
    3. git commit + 写审计记录
  拒绝也要留痕（attempted_* 字段）。

测试策略：
  - tmp_path 建 git 项目，init + lock + 初始 commit
  - 验证水质检测（空字段拒绝）
  - 验证写入模式（字符串替换 / 整文件）
  - 验证 git commit + 审计记录
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandax_dev.py"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PANDAX), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=20,
    )


def setup_git_project(tmp_path: Path) -> Path:
    """建 git 项目：init + git init + 初始文件 + 初始 commit + lock"""
    # pandax init
    r = run(["init", "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0

    # git init
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@x"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, capture_output=True, text=True)

    # 初始文件
    (tmp_path / "main.py").write_text("ORIGINAL = 1\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")

    # 初始 commit
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, text=True)

    # pandax lock
    r = run(["lock", "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0

    return tmp_path


def read_audit_log(project: Path) -> list[dict]:
    """读取 .pandax/pandax.jsonl 中所有记录"""
    audit_path = project / ".pandax" / "pandax.jsonl"
    if not audit_path.exists():
        return []
    records = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# ============================================================
# 水质检测
# ============================================================
def test_write_rejects_empty_reason(tmp_path):
    """reason 空 → REJECTED"""
    setup_git_project(tmp_path)
    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "",
        "--problem", "some problem description here",
        "--approach", "some approach here",
    ], cwd=tmp_path)

    # 期望 rc != 0（REJECTED）
    assert r.returncode != 0, f"应拒绝但通过: stdout={r.stdout}"
    assert "REJECTED" in r.stdout or "REJECTED" in r.stderr

    # 文件内容未变
    assert "ORIGINAL = 1" in (tmp_path / "main.py").read_text(encoding="utf-8")


def test_write_rejects_missing_problem(tmp_path):
    """problem 空 → REJECTED"""
    setup_git_project(tmp_path)
    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "修复json作用域错误",
        "--problem", "",
        "--approach", "移除重复import",
    ], cwd=tmp_path)

    assert r.returncode != 0
    assert "REJECTED" in r.stdout or "REJECTED" in r.stderr


def test_write_rejects_too_short_reason(tmp_path):
    """reason 太短（<5字）→ REJECTED"""
    setup_git_project(tmp_path)
    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "短",
        "--problem", "完整的问题描述在这里",
        "--approach", "完整的方法描述在这里",
    ], cwd=tmp_path)

    assert r.returncode != 0


def test_write_records_rejection(tmp_path):
    """拒绝也要写审计记录（attempted_*）"""
    setup_git_project(tmp_path)
    run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "",
        "--problem", "P",
        "--approach", "A",
    ], cwd=tmp_path)

    records = read_audit_log(tmp_path)
    assert len(records) >= 1, "应有审计记录"
    last = records[-1]
    assert last["status"] == "REJECTED"
    assert last["file"] == "main.py"
    assert "rejection_reason" in last or "attempted_reason" in last


# ============================================================
# 通过路径（APPROVED）
# ============================================================
def test_write_approved_with_full_metadata(tmp_path):
    """三字段完整 → APPROVED + 文件写入 + git commit + 审计记录"""
    setup_git_project(tmp_path)
    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "修复json变量作用域错误",
        "--problem", "init函数内重复import json导致UnboundLocalError",
        "--approach", "移除L10782的import json,保留全局导入",
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 2",
    ], cwd=tmp_path)

    assert r.returncode == 0, f"应通过但失败: stdout={r.stdout} stderr={r.stderr}"
    assert "APPROVED" in r.stdout

    # 文件已更新
    assert "UPDATED = 2" in (tmp_path / "main.py").read_text(encoding="utf-8")

    # 审计记录
    records = read_audit_log(tmp_path)
    approved = [x for x in records if x.get("status") == "APPROVED"]
    assert len(approved) >= 1, "应有 APPROVED 记录"
    rec = approved[-1]
    assert rec["file"] == "main.py"
    assert rec["reason"] == "修复json变量作用域错误"
    assert rec["problem"] == "init函数内重复import json导致UnboundLocalError"
    assert "commit_hash" in rec


def test_write_full_file_content_mode(tmp_path):
    """整文件模式（--content）替换整个文件"""
    setup_git_project(tmp_path)
    new_content = "# 全新的文件\ndef new_func():\n    return 'x'\n"

    r = run([
            "write",
            "--root", str(tmp_path),
            "--file", "main.py",
            "--reason", "完全重写文件结构",
            "--problem", "原文件结构不合理需要重写整个文件",
            "--approach", "采用全新模块结构重新组织整个文件",
            "--content", new_content,
        ], cwd=tmp_path)

    assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
    actual = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert actual == new_content


def test_write_git_commit_created(tmp_path):
    """write 通过后 git log 应有新的 commit"""
    setup_git_project(tmp_path)

    # 获取初始 commit 数
    before = subprocess.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip().count("\n") + 1

    run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试git提交功能",
        "--problem", "验证write后是否真的git commit",
        "--approach", "直接运行write命令测试",
        "--old", "ORIGINAL = 1",
        "--new", "MODIFIED = 1",
    ], cwd=tmp_path)

    after = subprocess.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip().count("\n") + 1

    assert after == before + 1, f"git commit 数应增加: {before} → {after}"


def test_write_rejects_non_py_file(tmp_path):
    """write 拒绝对非受保护扩展名的修改（Phase 4.6: .png 不在默认保护列表）"""
    setup_git_project(tmp_path)
    (tmp_path / "data.png").write_bytes(b"\x89PNG\r\n\x1a\nhello\n")

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "data.png",
        "--reason", "尝试改 png 文件",
        "--problem", "测一下非受保护扩展名",
        "--approach", "应该被拒绝",
        "--old", "hello",
        "--new", "world",
    ], cwd=tmp_path)

    assert r.returncode != 0, "非受保护扩展名应被拒绝"
    assert "只允许修改" in r.stdout or "REJECTED" in r.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
