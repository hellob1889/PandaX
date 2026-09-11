"""
test_i18n_export.py
====================
Bug #26 RED 测试：export html/md/text 报告本地化。

第一性原理：
  export 报告输出给用户/审计员看，必须与 --lang 一致。
  之前导出器（exporters.py）硬编码中文：标题/导出时间/表头。
  后果：--lang=en 输出"审计报告"，破坏英文用户阅读体验。

修复：
  - 新增 export_title/export_summary/export_exported_at/export_col_*
  - export_html/export_markdown/export_text 用 t() 渲染
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"


def _run(args, cwd, lang="zh-CN"):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PANDAX_LANG"] = lang
    r = subprocess.run(
        [sys.executable, "-m", "pandax", *args],
        cwd=cwd, capture_output=True, text=True, env=env, timeout=15,
    )
    return r


def _setup_with_audit(tmp_path: Path) -> Path:
    r = _run(["init", "--root", str(tmp_path), "--force"], tmp_path)
    assert r.returncode == 0, f"init failed: {r.stderr}"
    audit_path = tmp_path / ".pandax" / "pandax.jsonl"
    rec = {
        "id": "audit_test_export",
        "timestamp": "2026-01-01 12:00:00",
        "status": "APPROVED",
        "file": "main.py",
        "reason": "test reason",
        "problem": "test problem",
        "approach": "test approach",
        "commit_hash": "abc123",
    }
    audit_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return tmp_path


# ============================================================
# Bug #26: export 报告本地化
# ============================================================

class TestExportLabelsI18n:
    """Bug #26 — export html/md/text 报告标题/表头必须本地化"""

    def test_html_export_zh_cn(self, tmp_path):
        """zh-CN 模式：html 应有中文标题 + 中文标签（v0.7.3 卡片格式）"""
        project = _setup_with_audit(tmp_path)
        out = project / "out_zh.html"
        r = _run(["log", "--format", "html", "--output", str(out), "--lang", "zh-CN"], project)
        assert r.returncode == 0
        content = out.read_text(encoding="utf-8")
        assert "PandaX 审计报告" in content
        assert "导出时间" in content
        assert "记录数" in content
        # v0.7.3: 卡片格式用 <strong>标签: 值</strong> 而非 <th>
        assert "<strong>文件:</strong>" in content or "文件:" in content
        assert "<strong>状态" in content or "APPROVED" in content
        assert "<strong>原因" in content or "原因:" in content

    def test_html_export_en(self, tmp_path):
        """en 模式：html 应有英文标题 + 英文标签（v0.7.3 卡片格式）"""
        project = _setup_with_audit(tmp_path)
        out = project / "out_en.html"
        r = _run(["log", "--format", "html", "--output", str(out), "--lang", "en"], project)
        assert r.returncode == 0
        content = out.read_text(encoding="utf-8")
        # Bug #26 回归：英文模式下不应有中文标签
        assert "PandaX 审计报告" not in content, (
            f"Bug #26 回归：en 模式 html 含中文标题: {content[:200]}"
        )
        assert "PandaX Audit Report" in content
        assert "Exported at" in content
        assert "Records" in content
        # v0.7.3: 卡片格式
        assert "File:" in content
        assert "APPROVED" in content
        assert "Reason:" in content

    def test_markdown_export_en(self, tmp_path):
        """en 模式：md 报告应有英文标题 + 英文导出时间"""
        project = _setup_with_audit(tmp_path)
        out = project / "out_en.md"
        r = _run(["log", "--format", "md", "--output", str(out), "--lang", "en"], project)
        assert r.returncode == 0
        content = out.read_text(encoding="utf-8")
        assert "# PandaX Audit Report" in content, (
            f"Bug #26 回归：en md 缺英文标题: {content[:200]}"
        )
        assert "- Exported at:" in content
        assert "- Records:" in content

    def test_markdown_export_zh_cn(self, tmp_path):
        """zh-CN 模式：md 报告应有中文"""
        project = _setup_with_audit(tmp_path)
        out = project / "out_zh.md"
        r = _run(["log", "--format", "md", "--output", str(out), "--lang", "zh-CN"], project)
        assert r.returncode == 0
        content = out.read_text(encoding="utf-8")
        assert "# PandaX 审计报告" in content
        assert "- 导出时间:" in content
        assert "- 记录数:" in content

    def test_text_export_en(self, tmp_path):
        """en 模式：text 报告应有英文"""
        project = _setup_with_audit(tmp_path)
        out = project / "out_en.txt"
        r = _run(["log", "--format", "text", "--output", str(out), "--lang", "en"], project)
        assert r.returncode == 0
        content = out.read_text(encoding="utf-8")
        assert "PandaX Audit Report" in content
        assert "Exported at:" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
