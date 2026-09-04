"""
PandaX — AI Agent 代码审计门禁系统

主包入口:
  - CLI:    pandax <command> [args]
  - Module: python -m pandax <command> [args]
  - API:    from pandax import main; main()

第一性原理:
  - pip install 后立即可用，无须配置 PYTHONPATH
  - 与 Hermes 等成熟 Python CLI 的分发模式对齐
  - 跨平台: Windows / Linux / macOS
"""

__version__ = "0.6.2"

from .cli import main

__all__ = ["main", "__version__"]