#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py — PandaX 包安装配置

安装方式:
  pip install .              # 生产安装
  pip install -e .           # 开发模式（任何修改即时生效）
  pip install git+https://github.com/your/pandax.git  # GitHub 一键安装

第一性原理:
  - setup.py 是最经典的打包工具，跨 Python 版本可靠
  - 兼容 pip < 21（虽然我们要求 setuptools>=61）
  - 与 Hermes 等成熟 Python CLI 的分发方式一致
"""
from setuptools import setup, find_packages

setup(
    name="pandax",
    version="0.7.1",
    description="AI Agent code audit gateway (PandaX) - OS-level mandatory review of every code change",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="PandaX Project",
    author_email="pandax@example.com",
    url="https://github.com/hellob1889/PandaX",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "pandax": ["templates/*", "README.md", "banner.txt"],
        # Phase 9: OS 右键菜单集成脚本
        # 顶层 installer/ 通过 include_package_data + MANIFEST.in 打包
    },
    include_package_data=True,
    install_requires=[
        "watchdog>=3.0.0",
        "openpyxl>=3.1.0",     # Excel export
        "python-docx>=1.1.0",  # Word export
        "reportlab>=4.0.0",    # PDF export
        "pyyaml>=6.0",         # YAML export
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
        "download": [],  # urllib3 现在是标准库一部分
    },
    entry_points={
        "console_scripts": [
            "pandax=pandax:main",
            "pandax-guard=pandax_guard:main",
            "pandax-mcp=pandax_mcp:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="audit ai agent code-review compliance",
)