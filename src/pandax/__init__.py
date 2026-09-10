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
  - 版本号单一事实源: pyproject.toml → METADATA → importlib.metadata
    (避免硬编码字面量与 pyproject.toml 漂移)
"""

# ---------------------------------------------------------------------------
# 版本号: 单一事实源 = METADATA
#   - 正常安装(pip install *.whl): importlib.metadata.version("pandax-guard")
#   - 源码直跑(开发模式 / 源码树): 从同级的 pyproject.toml 读取 [project].version
#   - 极端 fallback: 字面量常量(打包脚本异常时仍可启动 CLI)
# ---------------------------------------------------------------------------
try:
    from importlib.metadata import version as _v, PackageNotFoundError as _PNFE
    try:
        __version__ = _v("pandax-guard")
    except _PNFE:
        __version__ = None
except ImportError:  # Python < 3.8 兜底（理论上不支持）
    __version__ = None

if __version__ is None:
    try:
        from pathlib import Path as _Path
        import re as _re
        _toml_text = (_Path(__file__).resolve().parent.parent.parent / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        _m = _re.search(r'^\s*version\s*=\s*"([^"]+)"\s*$', _toml_text, _re.MULTILINE)
        __version__ = _m.group(1) if _m else "0.0.0+unknown"
    except Exception:
        __version__ = "0.0.0+unknown"

from .cli import main

__all__ = ["main", "__version__"]
