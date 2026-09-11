"""
test_fingerprint_password_env.py
================================
回归测试:FINGERPRINT_PASSWORD 走环境变量,默认值不变。

第一性原理:
  旧设计:源码中写死 `FINGERPRINT_PASSWORD = "0000"`。
         推到公开 git 后任何人搜源码即可看到"权威密码"。
  新设计:默认仍是 "0000"(兼容现有用户/测试),但生产/CI 可通过
         PANDAX_FP_PASSWORD 环境变量覆盖,源码不再含"权威"明文。

验证:
  1. 默认密码仍是 "0000"(兼容性)
  2. 环境变量覆盖时,新密码生效,旧密码失效
  3. 环境变量不影响默认行为(unset 时 = "0000")
  4. 源码中不存在模块级常量 `FINGERPRINT_PASSWORD`(安全断言)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "src" / "pandaone" / "cli.py"
# FP_PATH 与 cli.py 一致:Path.home() / ".pandaone_fp.txt"
FP_PATH = Path.home() / ".pandaone_fp.txt"
FP_BACKUP = ROOT / ".pandaone_fp.txt.test_backup"

ENV_KEY = "PANDAX_FP_PASSWORD"


def run(args, env_extra=None):
    """运行 pandaone CLI,允许注入环境变量"""
    env = os.environ.copy()
    env.pop(ENV_KEY, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(PANDAX), *args],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(ROOT), env=env, timeout=30,
    )


def cleanup_fp():
    """删除 home 下的 FP_PATH,并备份恢复(避免污染真实用户配置)"""
    if FP_PATH.exists():
        shutil.copy2(FP_PATH, FP_BACKUP)
        FP_PATH.unlink()
    elif FP_BACKUP.exists():
        FP_BACKUP.unlink()


@pytest.fixture(autouse=True)
def restore_fp():
    """测试结束后恢复 FP_PATH(若曾被备份过)"""
    yield
    if FP_BACKUP.exists():
        if not FP_PATH.exists():
            shutil.move(FP_BACKUP, FP_PATH)
        else:
            FP_BACKUP.unlink()


# ============================================================
# 测试 1:兼容性 —— 默认密码仍是 "0000"
# ============================================================
def test_default_password_still_0000():
    """不设环境变量时,"0000" 必须仍能更新指纹。"""
    cleanup_fp()
    r = run(["--update-fingerprint", "0000"])
    assert r.returncode == 0, f"默认密码 0000 应可用, stderr={r.stderr}"
    assert FP_PATH.exists(), "指纹文件应被写入"


# ============================================================
# 测试 2:安全断言 —— 源码不应暴露模块级 FINGERPRINT_PASSWORD 常量
# ============================================================
def test_no_module_level_FINGERPRINT_PASSWORD_constant():
    """源码不再含模块级 FINGERPRINT_PASSWORD 常量。"""
    src = PANDAX.read_text(encoding="utf-8")
    bad = []
    for i, line in enumerate(src.splitlines(), 1):
        if line.startswith("FINGERPRINT_PASSWORD ="):
            bad.append((i, line))
    assert not bad, (
        f"源码不应再含模块级 FINGERPRINT_PASSWORD 常量, "
        f"找到: {bad}"
    )


def test_get_fingerprint_password_function_exists():
    """get_fingerprint_password() 函数必须存在并行为正确。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pandaone_cli_test", PANDAX)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert hasattr(mod, "get_fingerprint_password"), (
        "应存在 get_fingerprint_password() 函数"
    )

    os.environ.pop(ENV_KEY, None)
    assert mod.get_fingerprint_password() == "0000", (
        "默认密码必须是 '0000'(向后兼容)"
    )

    os.environ[ENV_KEY] = "secret_xyz"
    try:
        assert mod.get_fingerprint_password() == "secret_xyz", (
            "环境变量 PANDAX_FP_PASSWORD 应覆盖默认值"
        )
    finally:
        os.environ.pop(ENV_KEY, None)

    assert mod.get_fingerprint_password() == "0000"


# ============================================================
# 测试 3:CLI 实际使用环境变量密码
# ============================================================
def test_cli_respects_PANDAX_FP_PASSWORD():
    """CLI 端到端:环境变量设置的密码必须能通过,默认密码失效。"""
    cleanup_fp()

    r = run(["--update-fingerprint", "secret_abc"], env_extra={ENV_KEY: "secret_abc"})
    assert r.returncode == 0, f"环境变量密码应可用, stderr={r.stderr}"
    assert FP_PATH.exists()

    cleanup_fp()
    r = run(["--update-fingerprint", "0000"], env_extra={ENV_KEY: "secret_abc"})
    assert r.returncode != 0, "环境变量设置后,默认密码 0000 必须失效"
    assert ("密码" in r.stdout) or ("password" in r.stdout.lower())


# ============================================================
# 测试 4:生产场景示例 —— 用环境变量"禁用"默认密码
# ============================================================
def test_no_env_password_rejects_default_when_password_uses_random():
    """文档承诺:设环境变量后,默认密码失效。"""
    cleanup_fp()
    r_default = run(["--update-fingerprint", "0000"], env_extra={ENV_KEY: "Str0ng!Adm1n"})
    assert r_default.returncode != 0, "默认密码在强密码部署下必须失效"
    cleanup_fp()
    r_strong = run(["--update-fingerprint", "Str0ng!Adm1n"], env_extra={ENV_KEY: "Str0ng!Adm1n"})
    assert r_strong.returncode == 0, "环境变量设置的强密码应可用"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])