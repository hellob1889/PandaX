"""
test_install_hook.py
====================
RED 测试：install_hook.py + pre-commit hook 模板

第一性原理：
  L3 防御 = git pre-commit hook。
  即使 L1（文件锁）和 L2（watchdog）都被绕过，
  直接 `git commit` 也应被拒绝（除非通过 pandaone write）。

机制：
  - pre-commit hook 检查 staged 是否有 .py 文件
  - 如有，验证 .pandaone/pandaone.jsonl 也被 staged
  - 否则拒绝 commit

测试策略：
  - 调用 install_hook.py 在 tmp_path
  - 验证 .git/hooks/pre-commit 被创建 + 可执行
  - 手动 git commit（不通过 pandaone write）应失败
  - git commit 通过 pandaone write 应成功
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandaone_dev.py"
INSTALL_HOOK = ROOT / "src" / "pandaone" / "install_hook.py"
TEMPLATE = ROOT / "templates" / "pre-commit-hook"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=15,
    )


def setup_git(tmp_path: Path) -> Path:
    """init + git init + 初始 commit"""
    r = run([str(PANDAX), "init", "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, capture_output=True, text=True)

    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, text=True)
    return tmp_path


def test_template_file_exists():
    """templates/pre-commit-hook 必须存在"""
    assert TEMPLATE.exists(), f"模板文件不存在: {TEMPLATE}"


def test_install_hook_script_exists():
    """install_hook.py 必须存在"""
    assert INSTALL_HOOK.exists(), f"install_hook.py 不存在: {INSTALL_HOOK}"


def test_install_hook_creates_git_hook(tmp_path):
    """install-hook 后 .git/hooks/pre-commit 应被创建且可执行"""
    setup_git(tmp_path)

    r = run([str(INSTALL_HOOK), "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
    assert hook_path.exists(), f"pre-commit 未创建: {hook_path}"

    # 在 Windows 上"可执行"通过 file content 而非 mode
    content = hook_path.read_text(encoding="utf-8")
    assert "pandaone" in content.lower() or "Pandaone AI Agent" in content


def test_install_hook_normalizes_to_lf(tmp_path):
    """Bug #22 RED：安装后 hook 必须 LF-only（bash 在 *nix 上不支持 CRLF）

    对抗式审查：仅靠 shutil.copy(TEMPLATE, hook) 在 Windows git checkout 后会保留 CRLF，
    导致 hook 完全失效（L3 防御被绕过）。
    修复：install_hook 必须 read_bytes + 替换 \\r\\n → \\n 后 write_bytes。
    """
    project = setup_git(tmp_path)

    # 先把模板写成 CRLF（模拟 Windows git checkout 污染）
    template = ROOT / "templates" / "pre-commit-hook"
    raw = template.read_bytes()
    if b"\r\n" not in raw:
        # 临时注入 CRLF（不影响 fixture 之后的使用——teardown 自动还原）
        polluted = raw.replace(b"\n", b"\r\n")
        template.write_bytes(polluted)
        try:
            r = run([str(INSTALL_HOOK), "--root", str(project)], cwd=project)
            assert r.returncode == 0
            hook_path = project / ".git" / "hooks" / "pre-commit"
            hook_bytes = hook_path.read_bytes()
            assert b"\r\n" not in hook_bytes, (
                "Bug #22 回归：hook 含 CRLF，bash 在 *nix 上无法解析，L3 防御完全失效"
            )
            assert b"\r" not in hook_bytes, "hook 不应含裸 \\r"
            # 内容完整性
            assert b"Pandaone" in hook_bytes
            assert b"#!/bin/sh" in hook_bytes
        finally:
            template.write_bytes(raw)  # 还原
    else:
        # 模板本来就是 CRLF（极少见），直接验证修复
        r = run([str(INSTALL_HOOK), "--root", str(project)], cwd=project)
        assert r.returncode == 0
        hook_path = project / ".git" / "hooks" / "pre-commit"
        hook_bytes = hook_path.read_bytes()
        assert b"\r\n" not in hook_bytes, "Bug #22: install_hook 未规范化 CRLF"


def test_pre_commit_blocks_manual_py_change(tmp_path):
    """直接修改 .py 后 git commit 应被 pre-commit 拒绝"""
    project = setup_git(tmp_path)

    # 安装 hook
    run([str(INSTALL_HOOK), "--root", str(project)], cwd=project)

    # 直接修改 .py（绕过 pandaone write）
    main_py = project / "main.py"
    main_py.chmod(main_py.stat().st_mode | stat.S_IWUSR)
    main_py.write_text("y = 999\n", encoding="utf-8")

    # git add 但不通过 pandaone write
    subprocess.run(["git", "add", "main.py"], cwd=project, capture_output=True, text=True)

    # git commit 应失败
    r = subprocess.run(
        ["git", "commit", "-m", "manual change"],
        cwd=project, capture_output=True, text=True,
    )
    assert r.returncode != 0, "未审计的 .py commit 应被拒绝"
    # 应有 pandaone 错误信息
    combined = (r.stdout + r.stderr).lower()
    assert "pandaone" in combined or "audit" in combined


def test_pre_commit_allows_audited_change(tmp_path):
    """通过 pandaone write 改 .py 应自动 commit（含审计日志）"""
    project = setup_git(tmp_path)

    # 安装 hook
    run([str(INSTALL_HOOK), "--root", str(project)], cwd=project)

    # 获取初始 commit 数
    before = subprocess.run(
        ["git", "log", "--oneline"], cwd=project, capture_output=True, text=True,
    ).stdout.strip().count("\n") + 1

    # 通过 pandaone write 修改
    r = run([
        str(PANDAX), "write",
        "--root", str(project),
        "--file", "main.py",
        "--reason", "通过审计修改测试",
        "--problem", "测试预提交钩子是否正确放行审计通过的提交",
        "--approach", "使用pandaone write命令走完整审计流程",
        "--old", "x = 1",
        "--new", "x = 100",
    ], cwd=project)
    assert r.returncode == 0, f"write 失败: stdout={r.stdout}"

    # write 应自动 commit（hook 放行）
    after = subprocess.run(
        ["git", "log", "--oneline"], cwd=project, capture_output=True, text=True,
    ).stdout.strip().count("\n") + 1
    assert after == before + 1, f"write 后 commit 应增加: {before} → {after}"

    # commit message 应含审计信息
    log_msg = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=project, capture_output=True, text=True,
    ).stdout
    assert "audit:" in log_msg, f"commit message 应含 audit 标记: {log_msg}"
    assert "APPROVED" in log_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
