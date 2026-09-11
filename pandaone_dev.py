#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pandaone.py — 根目录 wrapper（向后兼容）
==========================================

实际代码在 src/pandaone/cli.py。
此 wrapper 用于开发模式（pip install 不需要）。

用户应该:
  - pip install pandaone-guard 后用 `pandaone` 命令
  - 或 `python -m pandaone` 在源码目录运行

第一性原理:
  - pip install 是首选分发方式
  - 保留 wrapper 是为了开发者体验（直接 `python pandaone.py`）
"""
import sys
from pathlib import Path

# 让 `from pandaone.cli import main` 在开发模式下能工作
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pandaone.cli import main

if __name__ == "__main__":
    sys.exit(main())