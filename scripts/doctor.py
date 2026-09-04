#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py — PandaX 环境自检工具
==================================

按"对抗式审查"：在用户安装/运行 PandaX 前主动检测环境问题，
不要等问题在 CI / 用户机器上爆炸。

检测项：
  1. Python 版本（≥ 3.10）
  2. pip 可用
  3. git 可执行（且在 PATH）
  4. pandax 包已安装（且指向本地源码）
  5. site-packages 没有装老版本
  6. pandax.exe 在 PATH（Windows / Unix）
  7. ~/.pandax_fp.txt 是否存在（污染检测）
  8. setuptools / wheel 可用
  9. 所有运行时依赖（watchdog / openpyxl / python-docx / reportlab / pyyaml）

输出格式：
  [OK]   ✅ 通过
  [WARN] ⚠️  不致命，但建议修复
  [FAIL] ❌  必须修复才能用
  [INFO] ℹ️   信息

退出码：
  0 = 所有检查通过或仅有 WARN
  1 = 有 FAIL（用户必须修复）
  2 = doctor 自身错误

用法：
  python scripts/doctor.py                 # 人类可读
  python scripts/doctor.py --json          # CI 用 JSON
  python scripts/doctor.py --quiet         # 只输出 FAIL/WARN
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

# ============================================================
# 常量
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
MIN_PYTHON = (3, 10)

# 必需依赖（与 pyproject.toml dependencies 同步）
REQUIRED_DEPS = [
    ("watchdog", "3.0.0"),
    ("openpyxl", "3.1.0"),
    ("openpyxl-styles", None),  # openpyxl 子模块
    ("docx", "1.1.0"),  # python-docx 导入名是 docx
    ("reportlab", "4.0.0"),
    ("yaml", "6.0"),  # pyyaml 导入名是 yaml
]

# Windows 上常见的 git 安装路径（探测时补充 PATH）
WINDOWS_GIT_CANDIDATES = [
    r"D:\软件\Git\cmd",
    r"D:\Program Files\Git\cmd",
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files (x86)\Git\cmd",
    r"C:\Program Files\Git\bin",
]

# ANSI 颜色（Windows 10+ 支持 ANSI）
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def _supports_color() -> bool:
    """检测终端是否支持 ANSI 颜色"""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _color(s: str, color: str) -> str:
    return f"{color}{s}{RESET}" if USE_COLOR else s


# ============================================================
# Check 数据结构
# ============================================================

class CheckResult:
    """单次检查结果"""

    __slots__ = ("name", "status", "message", "fix_hint")

    def __init__(self, name: str, status: str, message: str, fix_hint: str = ""):
        self.name = name
        self.status = status  # "OK" | "WARN" | "FAIL" | "INFO"
        self.message = message
        self.fix_hint = fix_hint

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "fix_hint": self.fix_hint,
        }

    def render(self) -> str:
        marker = {
            "OK": _color("[OK]  ", GREEN),
            "WARN": _color("[WARN]", YELLOW),
            "FAIL": _color("[FAIL]", RED),
            "INFO": _color("[INFO]", BLUE),
        }[self.status]
        line = f"  {marker}  {self.name}: {self.message}"
        if self.fix_hint and self.status in ("WARN", "FAIL"):
            line += f"\n          {_color('→', BLUE)} {self.fix_hint}"
        return line


# ============================================================
# 检查函数
# ============================================================

def check_python() -> CheckResult:
    """Python 版本 ≥ 3.10"""
    current = sys.version_info
    version_str = f"{current.major}.{current.minor}.{current.micro}"
    if (current.major, current.minor) >= MIN_PYTHON:
        return CheckResult(
            "Python 版本",
            "OK",
            f"{version_str}（≥ {'.'.join(map(str, MIN_PYTHON))}）",
        )
    return CheckResult(
        "Python 版本",
        "FAIL",
        f"{version_str}（需要 ≥ {'.'.join(map(str, MIN_PYTHON))}）",
        fix_hint=f"安装 Python {'.'.join(map(str, MIN_PYTHON))}+: https://www.python.org/downloads/",
    )


def check_pip() -> CheckResult:
    """pip 可用"""
    if shutil.which("pip"):
        return CheckResult("pip", "OK", shutil.which("pip"))
    # 退化：python -m pip
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, timeout=5, check=True,
        )
        return CheckResult("pip", "OK", f"{sys.executable} -m pip")
    except Exception as e:
        return CheckResult(
            "pip", "FAIL", f"未找到 pip: {e}",
            fix_hint="python -m ensurepip --upgrade",
        )


def _find_git_in_windows() -> str | None:
    """Windows 上探测 git.exe 候选路径"""
    if sys.platform != "win32":
        return None
    for cand in WINDOWS_GIT_CANDIDATES:
        if Path(cand, "git.exe").exists():
            return cand
    return None


def check_git() -> CheckResult:
    """git 可执行（在 PATH 或候选路径）"""
    git_path = shutil.which("git")
    if git_path:
        return CheckResult("git", "OK", git_path)

    # Windows 探测
    fallback = _find_git_in_windows()
    if fallback:
        return CheckResult(
            "git", "WARN",
            f"git 不在 PATH，但探测到 {fallback}",
            fix_hint=f"添加 {fallback} 到 PATH，或运行 scripts/install.ps1 自动修",
        )
    return CheckResult(
        "git", "FAIL", "未找到 git",
        fix_hint="安装 git: https://git-scm.com/download/ （或运行 scripts/install.sh）",
    )


def check_pandax_installed() -> CheckResult:
    """pandax 包可导入且指向本地源码"""
    try:
        import pandax  # noqa: F401
    except ImportError as e:
        return CheckResult(
            "pandax 安装", "FAIL", f"未安装: {e}",
            fix_hint=f"cd {REPO_ROOT} && python -m pip install -e . --no-build-isolation",
        )

    import pandax
    pkg_file = Path(pandax.__file__).resolve()
    is_local = str(pkg_file).startswith(str(REPO_ROOT))
    if is_local:
        return CheckResult(
            "pandax 安装",
            "OK",
            f"{pandax.__version__}（本地源码：{pkg_file.parent.parent.parent}）",
        )
    return CheckResult(
        "pandax 安装",
        "WARN",
        f"{pandax.__version__}（site-packages：{pkg_file}）",
        fix_hint=(
            "装的是 PyPI 上的旧版。建议本地源码安装：\n"
            f"    python -m pip install -e {REPO_ROOT} --no-build-isolation"
        ),
    )


def check_pandax_exe_in_path() -> CheckResult:
    """pandax 命令在 PATH"""
    exe = shutil.which("pandax")
    if exe:
        return CheckResult("pandax.exe PATH", "OK", exe)

    # 检查 Scripts 目录
    if sys.platform == "win32":
        scripts_dir = Path(sys.executable).parent / "Scripts"
        if (scripts_dir / "pandax.exe").exists():
            return CheckResult(
                "pandax.exe PATH", "WARN",
                f"已安装到 {scripts_dir} 但不在 PATH",
                fix_hint=f"添加 {scripts_dir} 到 PATH（用户级 PATH）",
            )
    else:
        # Unix 上检查 ~/.local/bin
        local_bin = Path.home() / ".local" / "bin" / "pandax"
        if local_bin.exists():
            return CheckResult(
                "pandax.exe PATH", "WARN",
                f"已安装到 {local_bin} 但不在 PATH",
                fix_hint=f"添加 {local_bin.parent} 到 PATH",
            )
    return CheckResult(
        "pandax.exe PATH", "INFO",
        "未在 PATH 找到（可用 `python -m pandax` 替代）",
    )


def check_fingerprint() -> CheckResult:
    """~/.pandax_fp.txt 检测（污染 vs 缺失）"""
    fp_path = Path.home() / ".pandax_fp.txt"
    if not fp_path.exists():
        return CheckResult(
            "指纹文件", "OK",
            f"{fp_path} 不存在（首次运行会自动生成）",
        )

    try:
        stored = fp_path.read_text(encoding="utf-8").strip()
        if not stored:
            return CheckResult(
                "指纹文件", "WARN",
                f"{fp_path} 存在但为空",
                fix_hint=f"删除 {fp_path} 让 PandaX 自动重新生成",
            )
        return CheckResult(
            "指纹文件", "INFO",
            f"{fp_path} 含 {stored[:16]}...（存在即正常，污染会在测试时暴露）",
        )
    except Exception as e:
        return CheckResult(
            "指纹文件", "WARN", f"读取失败: {e}",
            fix_hint=f"删除 {fp_path}",
        )


def check_setuptools() -> CheckResult:
    """setuptools 可用（pip install -e . 需要）"""
    try:
        import setuptools
        return CheckResult(
            "setuptools", "OK", f"{setuptools.__version__}",
        )
    except ImportError:
        return CheckResult(
            "setuptools", "FAIL", "未安装",
            fix_hint="python -m pip install setuptools wheel",
        )


def check_runtime_deps() -> list[CheckResult]:
    """所有运行时依赖（watchdog / openpyxl / python-docx / reportlab / pyyaml）"""
    results = []
    import_map = {
        "watchdog": ("watchdog", None),
        "openpyxl": ("openpyxl", None),
        "python-docx": ("docx", None),
        "reportlab": ("reportlab", None),
        "pyyaml": ("yaml", None),
    }
    for dep_name, (module_name, _) in import_map.items():
        try:
            __import__(module_name)
            results.append(CheckResult(
                f"依赖 {dep_name}", "OK", "已安装",
            ))
        except ImportError:
            results.append(CheckResult(
                f"依赖 {dep_name}", "FAIL", f"未安装",
                fix_hint=f"python -m pip install {dep_name}",
            ))
    return results


def check_python_version_in_pyproject() -> CheckResult:
    """pyproject.toml requires-python 与实际 Python 是否匹配"""
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return CheckResult("pyproject.toml", "WARN", f"{pyproject} 不存在")

    text = pyproject.read_text(encoding="utf-8")
    if "requires-python" not in text:
        return CheckResult(
            "pyproject.requires-python", "WARN",
            "未设置 requires-python",
            fix_hint="在 pyproject.toml [project] 加 requires-python = '>=3.10'",
        )
    return CheckResult("pyproject.requires-python", "OK", "已声明")


# ============================================================
# 主入口
# ============================================================

def run_all_checks() -> list[CheckResult]:
    """运行全部检查"""
    results: list[CheckResult] = []
    checks: list[Callable[[], CheckResult]] = [
        check_python,
        check_pip,
        check_git,
        check_pandax_installed,
        check_pandax_exe_in_path,
        check_fingerprint,
        check_setuptools,
        check_python_version_in_pyproject,
    ]
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            results.append(CheckResult(
                check.__name__, "FAIL", f"check 自身异常: {e}",
            ))
    results.extend(check_runtime_deps())
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PandaX 环境自检工具",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出（CI 用）")
    parser.add_argument("--quiet", "-q", action="store_true", help="只输出 WARN/FAIL")
    args = parser.parse_args()

    results = run_all_checks()

    # 过滤 quiet 模式
    if args.quiet:
        results = [r for r in results if r.status in ("WARN", "FAIL")]

    if args.json:
        payload = {
            "platform": platform.platform(),
            "python": sys.version,
            "results": [r.to_dict() for r in results],
            "passed": all(r.status != "FAIL" for r in results),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["passed"] else 1

    # 人类可读输出
    print("=" * 70)
    print(f" PandaX 环境自检 — doctor.py")
    print(f" 平台: {platform.platform()}")
    print(f" Python: {sys.version.split()[0]}")
    print(f" 仓库: {REPO_ROOT}")
    print("=" * 70)
    print()

    fail_count = 0
    warn_count = 0
    for r in results:
        print(r.render())
        if r.status == "FAIL":
            fail_count += 1
        elif r.status == "WARN":
            warn_count += 1
        print()

    # 总结
    print("=" * 70)
    if fail_count == 0:
        if warn_count == 0:
            print(_color(" ✅ 全部通过！", GREEN))
        else:
            print(_color(f" ⚠️  {warn_count} 项 WARN（不致命，但建议修复）", YELLOW))
        print("=" * 70)
        return 0
    print(_color(f" ❌ {fail_count} 项 FAIL（必须修复）+ {warn_count} 项 WARN", RED))
    print("=" * 70)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[ABORTED]")
        sys.exit(2)
