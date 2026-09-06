"""
test_i18n_log_status.py
=======================
Bug #14 + #17 RED 测试：log / status 命令在 zh-CN 和 en 模式下都应输出本地化标签。

第一性原理（对抗式审查）：
  i18n 的"完整性"≠"字符串被翻译了"，而是"每个面向用户的标签都有对应语言版本"。
  之前 _print_log 和 cmd_status 残留硬编码英文：
    - log: id= / file= / 状态枚举裸输出
    - status: - APPROVED: / - REJECTED: / - UNAUTHORIZED: 计数用裸状态码
  这导致 lang=zh-CN 时输出混合中英文，破坏 i18n 完整性。

修复：
  - log 用 t("log_record_header", id_label=..., file_label=...) 渲染
  - status 用 t("status_count_approved"/"rejected"/"unauthorized") 替代裸 k:v
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"


def _run(args, cwd, env_extra=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PANDAX_LANG"] = "zh-CN"  # 强制 zh-CN，绕开 conftest
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        [sys.executable, "-m", "pandax", *args],
        cwd=cwd, capture_output=True, text=True, env=env, timeout=15,
    )
    return r


def _setup_with_audit(tmp_path: Path) -> Path:
    """建项目 + 写入 1 条 APPROVED 审计"""
    r = _run(["init", "--root", str(tmp_path), "--force"], tmp_path)
    assert r.returncode == 0, f"init failed: {r.stderr}"
    # 直接写 audit jsonl（绕过 git + write 流程，测试聚焦 i18n 输出）
    audit_path = tmp_path / ".pandax" / "pandax.jsonl"
    rec = {
        "id": "audit_test_001",
        "timestamp": "2026-01-01 12:00:00",
        "status": "APPROVED",
        "file": "main.py",
        "reason": "test reason",
        "problem": "test problem description",
        "approach": "test approach details",
        "commit_hash": "abc123",
    }
    audit_path.write_text(
        json.dumps(rec, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return tmp_path


# ============================================================
# Bug #14: log 输出标签本地化
# ============================================================

class TestLogLabelsI18n:
    """Bug #14 — log 输出的 id=/file= 标签必须本地化"""

    def test_log_zh_cn_uses_localized_labels(self, tmp_path):
        """zh-CN 模式：log 不应输出英文硬编码 id=/file="""
        project = _setup_with_audit(tmp_path)
        r = _run(["log", "--lang", "zh-CN"], project)
        assert r.returncode == 0, f"log failed: {r.stderr}"
        # Bug #14 回归：硬编码 id= / file= 必须被本地化标签替换
        assert "id=audit_test_001" not in r.stdout, (
            f"Bug #14 回归：log 含硬编码 'id=' 英文标签: {r.stdout}"
        )
        # 应有 ID= 标签（无论中英都用 ID，因为是数据键）
        assert "ID=" in r.stdout or "ID＝" in r.stdout
        # 中文模式下文件标签应是"文件"
        assert "文件=" in r.stdout, (
            f"Bug #14 回归：log 缺中文'文件='标签: {r.stdout}"
        )

    def test_log_en_uses_english_labels(self, tmp_path):
        """en 模式：log 应输出英文 ID=/File="""
        project = _setup_with_audit(tmp_path)
        r = _run(["log", "--lang", "en"], project)
        assert r.returncode == 0
        assert "ID=audit_test_001" in r.stdout
        assert "File=main.py" in r.stdout

    def test_log_zh_cn_uses_chinese_reason_label(self, tmp_path):
        """zh-CN 模式：log 应输出中文'原因:'标签"""
        project = _setup_with_audit(tmp_path)
        r = _run(["log", "--lang", "zh-CN"], project)
        assert "原因:" in r.stdout, (
            f"Bug #14 回归：log 缺中文'原因:'标签: {r.stdout}"
        )


# ============================================================
# Bug #17: status 审计统计用本地化标签
# ============================================================

class TestStatusCountsI18n:
    """Bug #17 — status 审计统计不能用裸 APPROVED/REJECTED/UNAUTHORIZED"""

    def test_status_zh_cn_uses_localized_status_labels(self, tmp_path):
        """zh-CN 模式：status 不应输出 '  - APPROVED: 1' 这种裸状态码"""
        project = _setup_with_audit(tmp_path)
        r = _run(["status", "--lang", "zh-CN"], project)
        assert r.returncode == 0, f"status failed: {r.stderr}"
        # Bug #17 回归：不能用裸 APPROVED/REJECTED/UNAUTHORIZED 当作 label
        assert "  - APPROVED:" not in r.stdout, (
            f"Bug #17 回归：status 用裸 'APPROVED:' 标签: {r.stdout}"
        )
        assert "  - REJECTED:" not in r.stdout
        assert "  - UNAUTHORIZED:" not in r.stdout
        # 应有本地化标签
        assert "已批准:" in r.stdout, (
            f"Bug #17 回归：status 缺中文'已批准:'标签: {r.stdout}"
        )

    def test_status_en_uses_english_status_labels(self, tmp_path):
        """en 模式：status 应输出 '  - Approved: 1'"""
        project = _setup_with_audit(tmp_path)
        r = _run(["status", "--lang", "en"], project)
        assert r.returncode == 0
        assert "  - Approved: 1" in r.stdout
        # 不应是裸 APPROVED
        assert "  - APPROVED:" not in r.stdout


# ============================================================
# Adversarial 验证：避免回归
# ============================================================

def test_status_no_mixed_chinese_english_labels_zh(tmp_path):
    """对抗式审查：zh-CN 模式下 status 不应输出英文 section header 残留

    例：之前发现 [L2 watchdog] 在 zh-CN 模式仍是英文。
    修复后应是 [L2 watchdog 看门狗]（既保留英文术语又给中文注释）。
    """
    project = _setup_with_audit(tmp_path)
    r = _run(["status", "--lang", "zh-CN"], project)
    # 不应有纯英文 section header（不带任何中文）
    # 但允许 [L2 watchdog 看门狗] 这种中英混合
    for line in r.stdout.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("[L") and line_stripped.endswith("]"):
            # section header 必须是中英混合或纯中文
            inner = line_stripped[1:-1]
            has_chinese = any("\u4e00" <= ch <= "\u9fff" for ch in inner)
            # 之前 buggy 状态：纯英文如 [L2 watchdog]
            assert has_chinese or inner.startswith("L1 文件"), (
                f"section header 缺中文: {line_stripped}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
