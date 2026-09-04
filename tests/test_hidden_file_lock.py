"""
test_hidden_file_lock.py
========================
Phase 4.6+ — 隐藏文件（如 .env, .gitignore, .env.local）也应被锁定。

第一性原理：
  隐藏文件（如 .env）经常包含敏感信息（密码、token、数据库连接）。
  它们必须和普通文件一样被审计门禁保护。
  但 Path('.env').suffix 返回 ''（空字符串），不能用标准后缀匹配。

对抗式审查：
  - 攻击：改 .env 文件注入恶意数据库连接
    缓解：lock 应包含 .env，watchdog 应监控
  - 攻击：改 .gitignore 隐藏攻击痕迹
    缓解：lock 应包含 .gitignore（如果 config 包含）
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"


def _run_cli(*args, cwd=None, env_extra=None):
    """运行 pandax CLI"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, "-m", "pandax", *args]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or ROOT_DIR, env=env)
    return r.returncode, r.stdout, r.stderr


def _is_locked(p: Path) -> bool:
    """文件是否不可写"""
    mode = p.stat().st_mode
    return not (mode & 0o200)


def _force_unlock(p: Path):
    """强制解锁（测试用）"""
    mode = p.stat().st_mode
    os.chmod(p, mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)


# ============================================================
# Step 59: RED 测试
# ============================================================

class TestLockIncludesDotfiles:
    """lock 应锁定隐藏文件"""

    def test_lock_includes_dotenv(self, tmp_path):
        """lock 应锁定 .env 文件"""
        (tmp_path / ".env").write_text("SECRET=abc\n", encoding="utf-8")

        _run_cli("init", "--root", str(tmp_path))
        _run_cli("lock", "--root", str(tmp_path))

        # .env 应被锁
        assert _is_locked(tmp_path / ".env"), ".env 应被锁定"
        _force_unlock(tmp_path / ".env")

    def test_lock_includes_gitignore(self, tmp_path):
        """lock 应锁定 .gitignore 文件"""
        _run_cli("init", "--root", str(tmp_path))
        (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")

        # 修改 config 加入 .gitignore（默认不含）
        config_path = tmp_path / ".pandax" / "config.json"
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        cfg["protected_extensions"] = [".py", ".gitignore"]
        config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        _run_cli("lock", "--root", str(tmp_path))
        assert _is_locked(tmp_path / ".gitignore"), ".gitignore 应被锁定"
        _force_unlock(tmp_path / ".gitignore")

    def test_lock_includes_env_local(self, tmp_path):
        """lock 应锁定 .env.local 等带点的扩展名文件"""
        _run_cli("init", "--root", str(tmp_path))
        (tmp_path / ".env.local").write_text("ENV=local\n", encoding="utf-8")
        (tmp_path / ".env.production").write_text("ENV=prod\n", encoding="utf-8")

        # 修改 config 加入 .local / .production
        config_path = tmp_path / ".pandax" / "config.json"
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        cfg["protected_extensions"] = [".py", ".local", ".production"]
        config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        _run_cli("lock", "--root", str(tmp_path))
        assert _is_locked(tmp_path / ".env.local"), ".env.local 应被锁定"
        assert _is_locked(tmp_path / ".env.production"), ".env.production 应被锁定"
        _force_unlock(tmp_path / ".env.local")
        _force_unlock(tmp_path / ".env.production")

    def test_lock_includes_dotenv_in_subdir(self, tmp_path):
        """lock 应锁定子目录中的 .env"""
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / ".env").write_text("DB=postgres\n", encoding="utf-8")

        _run_cli("init", "--root", str(tmp_path))
        _run_cli("lock", "--root", str(tmp_path))

        assert _is_locked(tmp_path / "config" / ".env"), "config/.env 应被锁定"
        _force_unlock(tmp_path / "config" / ".env")


class TestWriteSupportsDotfiles:
    """write 应能修改隐藏文件"""

    def test_write_supports_dotenv(self, tmp_path):
        """write 应能审计写入 .env"""
        (tmp_path / ".env").write_text("OLD=x\n", encoding="utf-8")

        _run_cli("init", "--root", str(tmp_path))

        # 用 --content 替换
        rc, out, err = _run_cli(
            "write", "--root", str(tmp_path),
            "--file", ".env",
            "--reason", "更新数据库连接配置",
            "--problem", "原 .env 指向错误的数据库",
            "--approach", "改为新的生产数据库连接",
            "--content", "NEW=y\n",
        )
        assert rc == 0, f"write .env 失败: rc={rc}, out={out[-200:]}, err={err}"
        assert (tmp_path / ".env").read_text(encoding="utf-8") == "NEW=y\n"


class TestWatchdogMonitorsDotfiles:
    """watchdog 应监控隐藏文件（如果它们在保护扩展名中）"""

    def test_watchdog_detects_dotenv_modification(self, tmp_path):
        """修改 .env 应被 watchdog 捕获"""
        (tmp_path / ".env").write_text("INITIAL=x\n", encoding="utf-8")
        _run_cli("init", "--root", str(tmp_path))

        # 改 .env
        env_file = tmp_path / ".env"
        env_file.chmod(env_file.stat().st_mode | stat.S_IWUSR)
        env_file.write_text("HIJACKED=y\n", encoding="utf-8")

        # 直接实例化 handler 触发 on_modified
        sys.path.insert(0, str(ROOT_DIR))
        from pandax_guard import PandaXHandler
        handler = PandaXHandler(tmp_path)

        class FakeEvent:
            def __init__(self, p):
                self.src_path = p
                self.dest_path = p
                self.is_directory = False

        handler.on_modified(FakeEvent(str(env_file)))

        # 审计日志应有 UNAUTHORIZED 记录
        audit_path = tmp_path / ".pandax" / "pandax.jsonl"
        records = [
            json.loads(line) for line in
            audit_path.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        unauthorized = [r for r in records if r["status"] == "UNAUTHORIZED"]
        assert len(unauthorized) >= 1
        assert ".env" in unauthorized[-1]["file"] or "env" in unauthorized[-1]["file"].lower()