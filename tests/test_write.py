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


def setup_git_project(tmp_path: Path, lock: bool = True) -> Path:
    """建 git 项目：init + git init + 初始文件 + 初始 commit + (可选) lock

    Args:
        tmp_path: pytest tmp_path fixture
        lock: True = 锁定（默认），False = 不锁定（适合 write 测试加 --force-write 验证）
    """
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

    # pandax lock（可选）
    if lock:
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
    """三字段完整 → APPROVED + 文件写入 + git commit + 审计记录

    Bug #12 v2: write 默认拒绝 ReadOnly 文件，需 --force-write 显式解锁。
    setup_git_project 中已经 lock，所以这里必须加 --force-write。
    """
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
        "--force-write",  # Bug #12 v2: 锁定文件需显式 force
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
    # Bug #12 v2: 审计应记录 force_write=True
    assert rec.get("force_write") is True, f"force_write 字段应记录 True: {rec}"


def test_write_full_file_content_mode(tmp_path):
    """整文件模式（--content）替换整个文件

    Bug #12 v2: 锁定文件需 --force-write。
    """
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
            "--force-write",  # Bug #12 v2
        ], cwd=tmp_path)

    assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
    actual = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert actual == new_content


def test_write_git_commit_created(tmp_path):
    """write 通过后 git log 应有新的 commit

    Bug #12 v2: 锁定文件需 --force-write。
    """
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
        "--force-write",  # Bug #12 v2
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


# ============================================================
# Bug #12 v2: L1 ReadOnly 前置检查
# ============================================================
def test_write_rejects_readonly_without_force(tmp_path):
    """Bug #12 v2: 锁定文件不带 --force-write → REJECTED

    第一性原则：write 默认严格，必须显式 --force-write 才允许覆盖锁定文件。
    对抗场景：防止 AI Agent 或脚本意外绕过用户意图的 lock。
    """
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试未加 force 时被拒绝",
        "--problem", "默认严格以确保审计门禁不被绕过",
        "--approach", "应当 REJECTED 直到用户显式 --force-write",
        "--old", "ORIGINAL = 1",
        "--new", "HACKED = 1",
    ], cwd=tmp_path)

    assert r.returncode != 0, f"锁定文件应被 REJECTED: stdout={r.stdout}"
    assert "REJECTED" in r.stdout

    # 文件内容未变
    assert "ORIGINAL = 1" in (tmp_path / "main.py").read_text(encoding="utf-8")
    assert "HACKED" not in (tmp_path / "main.py").read_text(encoding="utf-8")

    # 审计记录 REJECTED
    records = read_audit_log(tmp_path)
    rejected = [x for x in records if x.get("status") == "REJECTED"]
    assert len(rejected) >= 1, "应有 REJECTED 审计记录"
    last_rej = rejected[-1]
    # 修复测试断言：实际 i18n 输出含 "read-only"（带连字符）或 "locked"/"L1"
    assert ("readonly" in last_rej.get("rejection_reason", "").lower()) or \
           ("locked" in last_rej.get("rejection_reason", "").lower()) or \
           ("l1" in last_rej.get("rejection_reason", "").lower()) or \
           ("锁定" in last_rej.get("rejection_reason", "")) or \
           ("只读" in last_rej.get("rejection_reason", "")), \
        f"rejection_reason 应提及 read-only/locked/L1/锁定/只读: {last_rej}"


def test_write_accepts_readonly_with_force(tmp_path):
    """Bug #12 v2: 锁定文件带 --force-write → APPROVED + 审计记录 force_write=true"""
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试加 force 后能正常写入锁定文件",
        "--problem", "force 标志应解锁并完整审计记录",
        "--approach", "走完整 unlock-write-lock 流程",
        "--old", "ORIGINAL = 1",
        "--new", "FORCED = 1",
        "--force-write",
    ], cwd=tmp_path)

    assert r.returncode == 0, f"--force-write 应 APPROVED: stdout={r.stdout} stderr={r.stderr}"
    assert "APPROVED" in r.stdout

    # 文件已更新
    assert "FORCED = 1" in (tmp_path / "main.py").read_text(encoding="utf-8")

    # 文件应被重新锁定（mode=0o100444 + ReadOnly=True）
    import os
    import stat as stat_mod
    target_mode = (tmp_path / "main.py").stat().st_mode
    assert target_mode & stat_mod.S_IWUSR == 0, f"写完后应重新锁定，但 mode={oct(target_mode)}"

    # 审计记录 force_write=true
    records = read_audit_log(tmp_path)
    approved = [x for x in records if x.get("status") == "APPROVED"]
    assert len(approved) >= 1
    last_app = approved[-1]
    assert last_app.get("force_write") is True, f"force_write 应记录 True: {last_app}"


# ============================================================
# Bug #9 / #10: 中文短句不被阈值误伤
# ============================================================
def test_write_accepts_short_chinese_reason(tmp_path):
    """Bug #9 fix: 中文 3 字 reason (e.g. '测试写') 应当 APPROVED

    修复前：len("测试写") == 3，被 5 chars 阈值误伤 → REJECTED
    修复后：_info_length("测试写") == 6（每个中文字 = 2 宽度单位），≥ 5 通过
    """
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试写",  # 中文 3 字 = 6 宽度
        "--problem", "需要修复初始化的全局变量问题",  # 中文 ≥ 10 宽度
        "--approach", "移除重复声明并使用统一的模块级单例模式",  # 中文 ≥ 10 宽度
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 1",
        "--force-write",
    ], cwd=tmp_path)

    assert r.returncode == 0, f"中文 3 字 reason 应 APPROVED: {r.stdout}"
    assert "APPROVED" in r.stdout


def test_write_rejects_short_chinese_reason(tmp_path):
    """Bug #9 fix: 中文 1 字 reason (e.g. '修') 仍应当 REJECTED

    修复后：_info_length("修") == 2 < 5 → 仍被拒（避免阈值过松）
    """
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "修",  # 太短
        "--problem", "需要修复初始化的全局变量问题",
        "--approach", "移除重复声明并使用统一的模块级单例模式",
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 1",
    ], cwd=tmp_path)

    assert r.returncode != 0, "1 字 reason 应被拒"
    assert "REJECTED" in r.stdout
    assert "reason" in r.stdout.lower()


def test_write_accepts_chinese_problem_short(tmp_path):
    """Bug #10 fix: 中文 problem ≥ 5 字 (10 宽度) 通过

    修复前：中文 6 字 = 6 chars，被 10 chars 阈值误伤
    修复后：_info_length("问题在这里") == 10，刚好通过阈值
    """
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试写流程",
        "--problem", "问题在这里发生",  # 中文 7 字 = 14 宽度 ≥ 10
        "--approach", "移除重复声明并使用统一的模块级单例模式",
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 1",
        "--force-write",
    ], cwd=tmp_path)

    assert r.returncode == 0, f"中文 7 字 problem 应 APPROVED: {r.stdout}"


def test_write_rejects_short_chinese_problem(tmp_path):
    """Bug #10 fix: 中文 2 字 problem (4 宽度) 仍被拒"""
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "测试写流程",
        "--problem", "太短",  # 中文 2 字 = 4 宽度 < 10
        "--approach", "移除重复声明并使用统一的模块级单例模式",
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 1",
    ], cwd=tmp_path)

    assert r.returncode != 0, "2 字 problem 应被拒"
    assert "REJECTED" in r.stdout


def test_write_accepts_english_5chars_reason(tmp_path):
    """Bug #9 fix: 英文 5 chars reason (e.g. 'fixxx') 仍通过

    确保修复未破坏英文阈值：英文 5 chars 仍能通过
    """
    setup_git_project(tmp_path)

    r = run([
        "write",
        "--root", str(tmp_path),
        "--file", "main.py",
        "--reason", "fixxx",  # 英文 5 chars
        "--problem", "fix the init order problem",  # 英文 ≥ 10
        "--approach", "refactor the init logic step by step now",  # 英文 ≥ 10
        "--old", "ORIGINAL = 1",
        "--new", "UPDATED = 1",
        "--force-write",
    ], cwd=tmp_path)

    assert r.returncode == 0, f"英文 5 chars 应 APPROVED: {r.stdout}"


def test_write_no_force_for_unlocked_file(tmp_path):
    """Bug #12 v2: 未锁定文件不需要 --force-write 也能 write"""
    # init 但不 lock
    p = tmp_path
    r = run(["init", "--root", str(p)], cwd=p)
    assert r.returncode == 0

    subprocess.run(["git", "init"], cwd=p, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@x"], cwd=p, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=p, capture_output=True, text=True)
    (p / "main.py").write_text("INITIAL = 0\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=p, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=p, capture_output=True, text=True)

    # 不加 --force-write（因为文件未锁定）
    r = run([
        "write",
        "--root", str(p),
        "--file", "main.py",
        "--reason", "未锁定文件可直接 write",
        "--problem", "测试未锁定时正常路径",
        "--approach", "应当 APPROVED",
        "--old", "INITIAL = 0",
        "--new", "INITIAL = 1",
    ], cwd=p)

    assert r.returncode == 0, f"未锁定应直接通过: stdout={r.stdout}"
    assert "APPROVED" in r.stdout

    # audit 应记录 force_write=False
    records = read_audit_log(p)
    approved = [x for x in records if x.get("status") == "APPROVED"]
    assert approved[-1].get("force_write") is False, \
        f"未锁定文件 force_write 应为 False: {approved[-1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
