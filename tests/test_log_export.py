"""
test_log_export.py
==================
RED 测试：pandaone log --format <FORMAT> 多格式导出

支持的格式:
  - text   (默认表格)
  - csv    (CSV 表格)
  - json   (JSON Lines)
  - md     (Markdown 表格)
  - html   (HTML 表格，dark theme)
  - xlsx   (Excel 工作簿，含样式)
  - docx   (Word 文档，含样式)

第一性原理:
  - 审计结果要"易消费"，不同的受众用不同的格式
  - 数据 → JSON 是通用中间表示；其他格式都是它的映射

测试策略:
  - 准备一组审计记录（JSONL 文件）
  - 用 log --format X --output Y 触发导出
  - 验证输出文件存在 + 内容可解析 + 含预期字段
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
    """建项目 + 注入 5 条审计记录"""
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
         "status": "APPROVED", "file": "utils.py",
         "reason": "add feat", "problem": "p desc 2",
         "approach": "a desc 2", "commit_hash": "def5678"},
        {"id": "audit_004", "timestamp": "2026-09-03 10:03:00",
         "status": "UNAUTHORIZED", "file": "main.py",
         "detection": "watchdog: on_modified without audit token",
         "action": "reverted from git HEAD"},
        {"id": "audit_005", "timestamp": "2026-09-03 10:04:00",
         "status": "APPROVED", "file": "main.py",
         "reason": "refactor", "problem": "p desc 3",
         "approach": "a desc 3", "commit_hash": "ghi9012"},
    ]
    with audit_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return tmp_path


# ============================================================
# 接口测试：--format 选项存在
# ============================================================

def test_log_format_option_exists():
    """log --format 应被 argparse 支持"""
    r = subprocess.run(
        [sys.executable, str(PANDAX), "log", "--help"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert "--format" in r.stdout
    # 应列出支持的格式
    out = r.stdout.lower()
    for fmt in ["csv", "json", "md", "html", "xlsx", "docx"]:
        assert fmt in out, f"--format 应支持 {fmt}"


def test_log_output_option_exists():
    """log --output 应被支持（取代 --export）"""
    r = subprocess.run(
        [sys.executable, str(PANDAX), "log", "--help"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert "--output" in r.stdout


# ============================================================
# CSV 格式
# ============================================================

def test_export_csv(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.csv"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "csv",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    # 表头 + 5 条记录
    assert len(lines) == 6
    # 第一行是表头
    assert "id" in lines[0].lower() and "status" in lines[0].lower()
    # 含 audit_001
    assert "audit_001" in content
    # 各种 status 都有
    assert "APPROVED" in content
    assert "REJECTED" in content
    assert "UNAUTHORIZED" in content


# ============================================================
# JSON 格式
# ============================================================

def test_export_json(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.json"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "json",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    # 应该是 {metadata, records} 结构
    assert "metadata" in data
    assert "records" in data
    assert data["metadata"]["count"] == 5
    assert len(data["records"]) == 5
    # 检查第一条
    assert data["records"][0]["id"] == "audit_001"
    assert data["records"][0]["status"] == "APPROVED"


# ============================================================
# Markdown 格式
# ============================================================

def test_export_markdown(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.md"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "md",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    # Markdown 表格标记
    assert "|" in content
    assert "---" in content
    assert "audit_001" in content
    assert "APPROVED" in content
    assert "REJECTED" in content


# ============================================================
# HTML 格式（已有）
# ============================================================

def test_export_html(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.html"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "html",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}"

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "<html" in content or "<table" in content
    assert "audit_001" in content


# ============================================================
# Excel 格式
# ============================================================

def test_export_xlsx(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.xlsx"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "xlsx",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}\nstdout={r.stdout}"

    assert output.exists()
    # 文件大小应 > 1KB
    assert output.stat().st_size > 1024

    # 用 openpyxl 验证可打开 + 含数据
    from openpyxl import load_workbook
    wb = load_workbook(str(output))
    ws = wb.active
    # 表头 + 5 条
    assert ws.max_row >= 6
    # 检查某个单元格
    audit_ids = [ws.cell(row=i, column=1).value for i in range(2, ws.max_row + 1)]
    assert any("audit_001" in str(v) for v in audit_ids)


# ============================================================
# Word 格式
# ============================================================

def test_export_docx(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.docx"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "docx",
        "--output", str(output),
    ], cwd=tmp_path)
    assert r.returncode == 0, f"stderr={r.stderr}\nstdout={r.stdout}"

    assert output.exists()
    # 文件大小应 > 1KB（docx 是 zip）
    assert output.stat().st_size > 1024

    # 用 python-docx 验证可打开 + 含段落/表格
    from docx import Document
    doc = Document(str(output))
    # 至少有标题 + 表格
    assert len(doc.paragraphs) >= 1
    assert len(doc.tables) >= 1
    # 表格第一行是表头
    table = doc.tables[0]
    header = [cell.text for cell in table.rows[0].cells]
    assert "id" in " ".join(header).lower() or "ID" in header


# ============================================================
# 边界情况
# ============================================================

def test_format_invalid_rejected(tmp_path):
    setup_records(tmp_path)
    output = tmp_path / "report.xyz"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "xyz",
        "--output", str(output),
    ], cwd=tmp_path)
    # 应报错
    assert r.returncode != 0
    assert "format" in r.stdout.lower() or "format" in r.stderr.lower() or "xyz" in r.stdout or "xyz" in r.stderr


def test_export_no_records(tmp_path):
    """空项目导出（无审计记录）应优雅处理"""
    r = run(["init", "--root", str(tmp_path)], cwd=tmp_path)
    assert r.returncode == 0
    output = tmp_path / "report.csv"

    r = run([
        "log", "--root", str(tmp_path),
        "--format", "csv",
        "--output", str(output),
    ], cwd=tmp_path)
    # 应成功（即使没记录，输出空表）
    assert r.returncode == 0
    assert output.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])