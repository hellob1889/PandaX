#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pandaone.py - 主 CLI

v0.7.7 修复:之前 MCP 推送截断了 cmd_ci/main 部分,导致 pip install 语法错误,Smoke Tests 失败。
本文件通过 cli_chunks 模块组装,见 cli_chunks/part_*.py。
"""
import sys
from pathlib import Path

_CHUNKS_DIR = Path(__file__).resolve().parent / "cli_chunks"
_chunks = sorted(_CHUNKS_DIR.glob("part_*.py"))
if not _chunks:
    print("ERR: no cli_chunks/part_*.py found", file=sys.stderr)
    sys.exit(1)

# PR #32 fix (cli loader): 用模块 globals() 作为 exec namespace,
# 这样 part_*.py 里 `def main():` 的 __globals__ 就是 cli 模块 globals。
# 之前用独立 _exec_ns dict,exec 后再 `for k,v: globals()[k]=v` 复制 — 这是浅复制,
# 之后 monkey-patch `cli.build_parser = patched` 只改 cli 模块 globals,
# main 函数体内查找 `build_parser` 走自己的 __globals__ (_exec_ns),看不到 patched version。
# 让 _exec_ns 直接 = globals() 保证两个 dict 是同一个引用。
_exec_ns = globals()
_exec_ns["__name__"] = "pandaone.cli"
# v0.7.9 fix (PR #36): 把 __file__ 设到每个 chunk 自己的路径,
# 否则 part_001.py 里 `ROOT = Path(__file__).parent.parent` 解析到 cli.py 自己路径
# (因为 _exec_ns["__file__"] 被钉死在 cli.py 绝对路径),导致 ROOT 指错 (site-packages/)
for chunk in _chunks:
    _exec_ns["__file__"] = str(chunk.resolve())
    code = chunk.read_text(encoding="utf-8")
    exec(compile(code, str(chunk), "exec"), _exec_ns)

if __name__ == "__main__":
    sys.exit(main())
