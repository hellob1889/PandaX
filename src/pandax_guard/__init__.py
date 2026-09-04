"""
pandax_guard — PandaX L2 防御守护进程

入口:
  - python -m pandax_guard --root <project>
  - python -m pandax_guard --root <project> --daemon
"""

__version__ = "0.1.0"

from .__main__ import main, run_watchdog, PandaXHandler

__all__ = ["main", "run_watchdog", "PandaXHandler", "__version__"]