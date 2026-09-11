"""
test_log_export_more.py
========================
RED 测试：pandaone log --format <FORMAT> 更多格式导出

新增格式:
  - pdf      (PDF 文档，reportlab 生成)
  - yaml     (YAML 文档，PyYAML)
  - sqlite   (SQLite 数据库，标准库 sqlite3)
  - rst      (reStructuredText)
  - tsv      (Tab 分隔值)
  - asciidoc (AsciiDoc 文档)
  - txt      (text 别名)

第一性原理:
  - "格式全"是核心承诺：AI Agent 不应被导出格式限制
  - 每种格式有它的最佳场景:
    - PDF → 邮件/打印
    - YAML → 配置文件/dashboard
    - SQLite → 程序查询/聚合
    - RST/AsciiDoc → 开源文档
    - TSV → shell 处理
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PANDAX = ROOT / "pandaone_dev.py"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PANDAX), *args],
        cwd=str(cwd), capture_output=True, text=True, timeout=30,
    )


def setup_records(tmp_path: Path) -> Path:
    """复用 test_log_export.py 的 setup"""
    r = run(["init", "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0
    audit_path = tmp_path / ".pandaone" / "pandaone.jsonl"
    records = [
        {"id": "audit_001", "timestamp": "2026-09-03 10:00:00",
         "status": "APPROVED", "file": "main.py",
         "reason": "fix bug", "problem": "p desc",
         "approach": "a desc", "commit_hash": "abc1234"},
        {"id": "audit_002", "timestamp": "2026-09-03 10:01:00",
         "status": "REJECTED", "file": "main.py",
         "rejection_reason": "reason 字段为空"},
        {"id": "audit_003", "timestamp": "2026-09-03 10:02:00",
         "status": "UNAUTHORIZED", "file": "utils.py",
         "detection": "watchdog: bypass",
         "action": "reverted"},
    ]
    with audit_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return tmp_path


# ============================================================
# 列表中应包含这些新格式
# ============================================================

def test_help_includes_new_formats():
    """--format help 应列出 pdf/yaml/sqlite/rst/tsv/asciidoc/txt"""
    r = subprocess.run(
        [sys.executable, str(PANDAX), "log", "--help"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert r.returncode == 0
    out = r.stdout.lower()
    for fmt in ["pdf", "yaml", "sqlite", "rst", "tsv", "asciidoc", "txt"]:
        assert fmt in out, f"--format 应支持 {fmt}"


# ============================================================
# PDF
# ============================================================

def test_export_pdf(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.pdf"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "pdf",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}\nstdout={r.stdout}"

    assert output.exists()
    # PDF 应该有 PDF 头
    with output.open("rb") as f:
        head = f.read(5)
    assert head == b"%PDF-", f"PDF 头错误: {head!r}"
    # 文件大小 > 1KB
    assert output.stat().st_size > 1024


# ============================================================
# YAML
# ============================================================

def test_export_yaml(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.yaml"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "yaml",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    # YAML 标记
    assert "metadata:" in content or "records:" in content
    assert "audit_001" in content
    assert "APPROVED" in content

    # 用 PyYAML 验证可解析
    import yaml
    data = yaml.safe_load(content)
    assert "records" in data or "metadata" in data


# ============================================================
# SQLite
# ============================================================

def test_export_sqlite(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.db"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "sqlite",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()

    # 用 sqlite3 验证可查询
    import sqlite3
    conn = sqlite3.connect(str(output))
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert any("audit" in t.lower() or "record" in t.lower() for t in tables), \
        f"应有审计表: {tables}"

    # 查询记录数
    for tbl in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            if count >= 3:
                assert count == 3
                break
        except Exception:
            pass
    conn.close()


# ============================================================
# reStructuredText
# ============================================================

def test_export_rst(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.rst"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "rst",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    # RST 标题/表格
    assert "=" in content
    assert "audit_001" in content
    assert "APPROVED" in content


# ============================================================
# TSV
# ============================================================

def test_export_tsv(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.tsv"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "tsv",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    # 表头 + 3 条
    assert len(lines) == 4
    # TSV 用 Tab 分隔
    assert "\t" in lines[0]
    assert "\t" in lines[1]
    assert "audit_001" in content


# ============================================================
# AsciiDoc
# ============================================================

def test_export_asciidoc(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.adoc"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "asciidoc",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    # AsciiDoc 标记
    assert "==" in content  # 二级标题
    assert "|===" in content  # 表格标记
    assert "audit_001" in content


# ============================================================
# txt 别名
# ============================================================

def test_export_txt_alias(tmp_path):
    """txt 是 text 的别名"""
    setup_records(tmp_path)
    output = tmp_path / "report.txt"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "txt",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "审计" in content or "audit" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])