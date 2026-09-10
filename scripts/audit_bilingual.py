#!/usr/bin/env python3
"""
双语覆盖率检查工具 / Bilingual Coverage Audit Tool

扫描指定目录下的所有 .md 文件，检测"纯中文行"（含中文字符但不含英文字符）
报告覆盖率，用于确保 markdown 文件已双语化。

Scans all .md files under a directory, detects "pure Chinese lines"
(lines containing Chinese characters but no English letters), and reports
coverage to ensure markdown files are bilingualized.

排除规则 / Exclude Rules:
- docs/zh/*.md 和 docs/en/*.md（分语言站点，已用 i18n 分隔）
  docs/zh/*.md and docs/en/*.md (language-separated sites)
- examples/demo_05_full/*（demo 数据，gitignored）
  examples/demo_05_full/* (demo data, gitignored)
- .pytest_cache/*（pytest 自动生成）
  .pytest_cache/* (pytest auto-generated)
- *.py 文件（Python 源码不是文档）
  *.py files (Python source, not docs)

判断标准 / Detection Criteria:
- 纯中文行 = 包含 [\u4e00-\u9fff] 但不包含 [a-zA-Z]
- 已被双语化 = 文档中"纯中文行 / 总含中文行 < 30%"
- 已双语化 = `pure_chinese_lines / total_chinese_lines < 30%`
  Already bilingualized = ratio < 30%

Usage:
    python scripts/audit_bilingual.py [ROOT_DIR]
    python scripts/audit_bilingual.py --json    # JSON output
    python scripts/audit_bilingual.py --strict  # ratio < 10%

退出码 / Exit Codes:
- 0: 全部文件双语化覆盖率达标 / All files meet coverage threshold
- 1: 存在未双语化文件 / Some files don't meet coverage threshold
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Pure Chinese line: contains Chinese characters but no English letters
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
ENGLISH_RE = re.compile(r"[a-zA-Z]")

# Excluded paths (language-separated sites + demo data + auto-generated)
EXCLUDE_PATTERNS = [
    "docs/zh/",         # 中文文档站（保持单语）/ Chinese doc site (kept monolingual)
    "docs/en/",         # 英文文档站（保持单语）/ English doc site (kept monolingual)
    "examples/demo_05_full/",  # demo 数据（gitignored）/ demo data (gitignored)
    ".pytest_cache/",   # pytest 缓存 / pytest cache
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
]

# 阈值：纯中文行 / 总含中文行 < THRESHOLD = 已双语化
# Threshold: pure_chinese_lines / total_chinese_lines < THRESHOLD = bilingualized
DEFAULT_THRESHOLD = 0.30
STRICT_THRESHOLD = 0.10


def is_excluded(path: Path, root: Path) -> bool:
    """Check if path matches any exclude pattern."""
    rel = str(path.relative_to(root)).replace("\\", "/")
    return any(pat in rel for pat in EXCLUDE_PATTERNS)


def analyze_file(path: Path) -> dict:
    """Analyze a single .md file for bilingual coverage."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {"file": str(path), "error": "read_failed"}

    lines = text.splitlines()
    total = len(lines)
    pure_chinese = 0
    total_chinese = 0  # lines that contain at least one Chinese char
    blank_or_code = 0

    in_code_block = False
    for line in lines:
        # 跳过代码块（避免误判代码注释里的中文）/ Skip code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            blank_or_code += 1
            continue
        if in_code_block:
            blank_or_code += 1
            continue

        has_chinese = bool(CHINESE_RE.search(line))
        has_english = bool(ENGLISH_RE.search(line))
        is_blank = not line.strip()

        if is_blank:
            blank_or_code += 1
            continue

        if has_chinese:
            total_chinese += 1
            if not has_english:
                pure_chinese += 1

    ratio = pure_chinese / total_chinese if total_chinese > 0 else 0.0
    return {
        "file": str(path),
        "total_lines": total,
        "chinese_lines": total_chinese,
        "pure_chinese_lines": pure_chinese,
        "ratio": round(ratio, 3),
        "bilingualized": ratio < DEFAULT_THRESHOLD,
    }


def scan(root: Path, threshold: float) -> list[dict]:
    """Scan all .md files under root, return analysis list."""
    results = []
    for md in sorted(root.rglob("*.md")):
        if is_excluded(md, root):
            continue
        result = analyze_file(md)
        result["bilingualized"] = (
            result.get("ratio", 1.0) < threshold
            and "error" not in result
        )
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", default=".", help="扫描根目录 / scan root dir (default: cwd)")
    parser.add_argument("--json", action="store_true", help="JSON 输出 / JSON output")
    parser.add_argument("--strict", action="store_true", help="严格模式（阈值 0.10）/ strict mode (threshold 0.10)")
    parser.add_argument("--show-passed", action="store_true", help="显示已通过的文件 / show files that pass")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    threshold = STRICT_THRESHOLD if args.strict else DEFAULT_THRESHOLD

    if not root.is_dir():
        print(f"[ERROR] {root} 不是目录 / not a directory", file=sys.stderr)
        return 2

    results = scan(root, threshold)

    passed = [r for r in results if r.get("bilingualized")]
    failed = [r for r in results if not r.get("bilingualized")]

    if args.json:
        print(json.dumps({
            "root": str(root),
            "threshold": threshold,
            "passed": len(passed),
            "failed": len(failed),
            "total_files": len(results),
            "results": results,
        }, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print(f"扫描根目录 / Scan root: {root}")
        print(f"双语阈值 / Bilingual threshold: ratio < {threshold:.0%}")
        print(f"扫描到 .md 文件 / Scanned .md files: {len(results)}")
        print()
        print("=" * 70)
        print(f"❌ 未通过 / FAILED: {len(failed)} 文件")
        print("=" * 70)
        if not failed:
            print("  (无 / none)")
        for r in failed:
            err = r.get("error", "")
            if err:
                print(f"  [ERROR] {r['file']} ({err})")
            else:
                print(
                    f"  {r['file']}\n"
                    f"    总行 / total: {r['total_lines']}, "
                    f"含中文行 / Chinese lines: {r['chinese_lines']}, "
                    f"纯中文行 / pure: {r['pure_chinese_lines']}, "
                    f"比例 / ratio: {r['ratio']:.1%}"
                )

        if args.show_passed:
            print()
            print("=" * 70)
            print(f"✅ 已通过 / PASSED: {len(passed)} 文件")
            print("=" * 70)
            for r in passed:
                err = r.get("error", "")
                if err:
                    continue
                print(
                    f"  {r['file']} "
                    f"(中文 {r['chinese_lines']}, 纯 {r['pure_chinese_lines']}, "
                    f"ratio {r['ratio']:.1%})"
                )

        print()
        print("=" * 70)
        summary = "全部通过 / ALL PASSED ✅" if not failed else "存在未通过文件 / SOME FAILED ❌"
        print(f"汇总 / Summary: {summary}")
        print(f"  通过 / passed: {len(passed)}, 失败 / failed: {len(failed)}, 总计 / total: {len(results)}")
        print("=" * 70)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
