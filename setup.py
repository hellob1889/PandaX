#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py — PandaX 包安装配置

安装方式:
  pip install .              # 生产安装
  pip install -e .           # 开发模式（任何修改即时生效）
  pip install git+https://github.com/hellob1889/PandaX.git  # GitHub 一键安装

第一性原理:
  - setup.py 是最经典的打包工具，跨 Python 版本可靠
  - 兼容 pip < 21（虽然我们要求 setuptools>=61）
  - 与 Hermes 等成熟 Python CLI 的分发方式一致
"""
from setuptools import setup, find_packages

# setup.py is now a minimal stub — all metadata lives in pyproject.toml (PEP 621).
# This file exists only for `pip install .` on legacy pip (<21) which lacks
# PEP 517 pyproject.toml-only support. setuptools will read metadata from
# pyproject.toml and ignore this stub (it sees no conflicting fields).
from setuptools import setup
setup()