"""
test_fix_29_39.py
=================
Bug #29 + #39 专属回归测试

Bug #29 (P1 数据丢失): pandaone init 不再覆盖用户自定义 config.json
Bug #39 (P3 i18n 漏): cmd_write 4 处硬编码中文改为 i18n
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"


def _run(args, cwd, lang="zh-CN"):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PANDAX_LANG"] = lang
    return subprocess.run(
        [sys.executable, "-m", "pandaone", *args],
        cwd=cwd, capture_output=True, text=True, env=env, timeout=15,
    )


# ============================================================
# Bug #29: init 不覆盖用户自定义 config.json
# ============================================================

class TestBug29InitPreserveUserConfig:
    """Bug #29 — init 二次运行保留用户自定义字段"""

    def test_preserves_arbitrary_user_fields(self, tmp_path):
        """init 应保留用户任意自定义字段（如团队策略）"""
        project = tmp_path / "p"
        project.mkdir()
        # 首次 init
        _run(["init", "--root", str(project)], project)
        cfg_path = project / ".pandaone" / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["team_policy"] = "require_pair_review"
        cfg["min_reason_length"] = 99
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

        # 二次 init
        r = _run(["init", "--root", str(project)], project)
        assert r.returncode == 0

        new = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert new.get("team_policy") == "require_pair_review", (
            "Bug #29 回归：用户自定义字段 team_policy 被覆盖"
        )
        assert new.get("min_reason_length") == 99, (
            "Bug #29 回归：用户自定义阈值被覆盖"
        )

    def test_preserves_custom_protected_extensions(self, tmp_path):
        """init 应保留用户加的扩展名（除非显式传 --ext）"""
        project = tmp_path / "p"
        project.mkdir()
        _run(["init", "--root", str(project)], project)
        cfg_path = project / ".pandaone" / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["protected_extensions"] = [".py", ".proto", ".thrift"]
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

        # 二次 init（不带 --ext）→ 应保留 .proto/.thrift
        _run(["init", "--root", str(project)], project)
        new = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert ".proto" in new["protected_extensions"], (
            "Bug #29 回归：用户自定义扩展名 .proto 被覆盖"
        )
        assert ".thrift" in new["protected_extensions"], (
            "Bug #29 回归：用户自定义扩展名 .thrift 被覆盖"
        )

    def test_force_reset_overrides_user_config(self, tmp_path):
        """--force-reset 应能强制覆盖（高级用户显式选择）"""
        project = tmp_path / "p"
        project.mkdir()
        _run(["init", "--root", str(project)], project)
        cfg_path = project / ".pandaone" / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["custom_team_field"] = "should_be_lost"
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

        # --force-reset 应清空自定义
        _run(["init", "--root", str(project), "--force-reset"], project)
        new = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "custom_team_field" not in new, (
            "Bug #29 回归：--force-reset 没清空自定义字段"
        )

    def test_explicit_ext_overrides_existing(self, tmp_path):
        """二次 init 显式传 --ext 应覆盖（用户主动选择）"""
        project = tmp_path / "p"
        project.mkdir()
        _run(["init", "--root", str(project)], project)
        cfg_path = project / ".pandaone" / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["protected_extensions"] = [".py", ".proto"]
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

        # 二次 init + --ext=js,ts → 应用 .js, .ts 覆盖
        _run(["init", "--root", str(project), "--ext", "js,ts"], project)
        new = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert ".js" in new["protected_extensions"]
        assert ".ts" in new["protected_extensions"]

    def test_init_shows_warning_when_config_exists(self, tmp_path):
        """二次 init 应打印 WARN 提示用户"""
        project = tmp_path / "p"
        project.mkdir()
        _run(["init", "--root", str(project)], project)
        r = _run(["init", "--root", str(project)], project, lang="zh-CN")
        assert "[WARN]" in r.stdout or "保留" in r.stdout or "customiz" in r.stdout.lower(), (
            f"Bug #29 回归：二次 init 未打印 WARN: {r.stdout[:300]}"
        )


# ============================================================
# Bug #39: cmd_write 硬编码中文 → i18n
# ============================================================

class TestBug39WriteI18n:
    """Bug #39 — cmd_write 4 处硬编码中文改为 i18n"""

    def test_empty_reason_in_zh(self, tmp_path):
        """zh-CN 模式：reason 空应显示中文"""
        project = tmp_path / "p"
        project.mkdir()
        (project / "test.py").write_text("# hi\n", encoding="utf-8")
        _run(["init", "--root", str(project)], project)
        # 不传 --reason
        r = _run(["write", "--file", "test.py",
                  "--problem", "问题说明足够长足够长足够长足够长",
                  "--approach", "方案说明足够长足够长足够长足够长",
                  "--old", "# hi", "--new", "# hi"],
                 project, lang="zh-CN")
        # 应该失败（reason 空）+ 中文错误
        assert r.returncode != 0
        combined = r.stdout + r.stderr
        assert "reason 字段为空" in combined or "reason" in combined

    def test_empty_reason_in_en(self, tmp_path):
        """en 模式：reason 空应显示英文（修复前是中文）"""
        project = tmp_path / "p"
        project.mkdir()
        (project / "test.py").write_text("# hi\n", encoding="utf-8")
        _run(["init", "--root", str(project)], project)
        r = _run(["write", "--file", "test.py",
                  "--problem", "problem description long enough",
                  "--approach", "approach description long enough",
                  "--old", "# hi", "--new", "# hi"],
                 project, lang="en")
        assert r.returncode != 0
        combined = r.stdout + r.stderr
        # 修复前是中文硬编码，修复后应为英文
        assert "reason" in combined.lower()
        assert "字段为空" not in combined, (
            f"Bug #39 回归：en 模式仍含中文硬编码: {combined[:500]}"
        )

    def test_binary_old_new_in_en(self, tmp_path):
        """en 模式：二进制文件用 --old/--new 应显示英文错误"""
        project = tmp_path / "p"
        project.mkdir()
        (project / "test.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        _run(["init", "--root", str(project)], project)
        r = _run(["write", "--file", "test.png",
                  "--reason", "test reason long enough",
                  "--problem", "test problem long enough long enough",
                  "--approach", "test approach long enough long enough",
                  "--old", "fake", "--new", "fake2"],
                 project, lang="en")
        assert r.returncode != 0
        combined = r.stdout + r.stderr
        assert "Binary" in combined or "binary" in combined.lower(), (
            f"Bug #39 回归：en 模式二进制错误未本地化: {combined[:500]}"
        )
        assert "二进制" not in combined, (
            f"Bug #39 回归：en 模式仍含中文二进制错误"
        )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
