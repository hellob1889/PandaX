#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py — Pandaone AI Agent 环境自检工具
==================================

按"对抗式审查"：在用户安装/运行 Pandaone 前主动检测环境问题，
不要等问题在 CI / 用户机器上爆炸。

检测项：
  1. Python 版本（≥ 3.10）
  2. pip 可用
  3. git 可执行（且在 PATH）
  4. pandaone 包已安装（且指向本地源码）
  5. site-packages 没有装老版本
  6. pandaone.exe 在 PATH（Windows / Unix）
  7. ~/.pandaone_fp.txt 是否存在（污染检测）
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
  python scripts/doctor.py --fix           # 尝试自动修复（默认 dry-run + 显示）
  python scripts/doctor.py --fix-only      # 只跑修复 + 重测
  python scripts/doctor.py --fix --json    # CI 模式 + 修复

可自动修复的问题（13 种）：
  - pip 缺失（ensurepip）
  - git 不在 PATH（临时加 PATH）
  - pandaone 未装（pip install -e .）
  - pandaone 装在 site-packages 老版本（uninstall + 装本地）
  - pandaone.exe 不在 PATH（临时加 PATH）
  - ~/.pandaone_fp.txt 污染/空（删除）
  - setuptools 缺失（pip install）
  - 5 个运行时依赖缺失（pip install <dep>）
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
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

    __slots__ = (
        "name", "status", "message", "fix_hint",
        "fix_action", "fix_action_persist", "fixable",
    )

    def __init__(
        self,
        name: str,
        status: str,
        message: str,
        fix_hint: str = "",
        fix_action: "Callable[[], tuple[bool, str]] | None" = None,
        fix_action_persist: "Callable[[], tuple[bool, str]] | None" = None,
        fixable: bool = False,
    ):
        self.name = name
        self.status = status  # "OK" | "WARN" | "FAIL" | "INFO"
        self.message = message
        self.fix_hint = fix_hint
        # fix_action: callable that returns (success: bool, message: str)
        # None means no automatic fix is available
        self.fix_action = fix_action
        # fix_action_persist: same but persistent (writes to HKCU / shell rc).
        # If None, --persist-path will silently fall back to fix_action.
        self.fix_action_persist = fix_action_persist
        # fixable: whether this check has an auto-fix (UI hint only)
        self.fixable = fixable

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "fix_hint": self.fix_hint,
            "fixable": self.fixable,
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
            if self.fixable and self.fix_action is not None:
                line += f"\n          {_color('FIX', GREEN)} 可自动修复：python scripts/doctor.py --fix"
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
        def fix_pip():
            try:
                subprocess.run(
                    [sys.executable, "-m", "ensurepip", "--upgrade"],
                    capture_output=True, timeout=60, check=True,
                )
                return True, f"pip installed via {sys.executable} -m ensurepip --upgrade"
            except Exception as fe:
                return False, f"ensurepip failed: {fe}"
        return CheckResult(
            "pip", "FAIL", f"未找到 pip: {e}",
            fix_hint="python -m ensurepip --upgrade",
            fix_action=fix_pip,
            fixable=True,
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
        def fix_git():
            # 临时加入 PATH（仅当前 Python 进程内）
            os.environ["PATH"] = fallback + os.pathsep + os.environ.get("PATH", "")
            # 验证
            new_path = shutil.which("git")
            if new_path:
                return True, f"git added to PATH (current session only): {fallback}"
            return False, f"failed to add {fallback} to PATH"
        return CheckResult(
            "git", "WARN",
            f"git 不在 PATH，但探测到 {fallback}",
            fix_hint=f"添加 {fallback} 到 PATH，或运行 scripts/install.ps1 自动修",
            fix_action=fix_git,
            fixable=True,
        )
    return CheckResult(
        "git", "FAIL", "未找到 git",
        fix_hint="安装 git: https://git-scm.com/download/ （或运行 scripts/install.sh）",
    )


def check_pandaone_installed() -> CheckResult:
    """pandaone 包可导入且指向本地源码"""
    try:
        import pandaone  # noqa: F401
    except ImportError as e:
        def fix_install_pandaone():
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", ".",
                     "--no-build-isolation"],
                    cwd=str(REPO_ROOT),
                    capture_output=True, timeout=180, check=True,
                )
                return True, f"installed editable from {REPO_ROOT}"
            except subprocess.CalledProcessError as fe:
                return False, f"pip install failed (exit {fe.returncode}): {fe.stderr.decode(errors='replace')[:200] if fe.stderr else 'unknown'}"
        return CheckResult(
            "pandaone 安装", "FAIL", f"未安装: {e}",
            fix_hint=f"cd {REPO_ROOT} && python -m pip install -e . --no-build-isolation",
            fix_action=fix_install_pandaone,
            fixable=True,
        )

    import pandaone
    pkg_file = Path(pandaone.__file__).resolve()
    is_local = str(pkg_file).startswith(str(REPO_ROOT))
    if is_local:
        return CheckResult(
            "pandaone 安装",
            "OK",
            f"{pandaone.__version__}（本地源码：{pkg_file.parent.parent.parent}）",
        )

    # site-packages 装的是老版本 → 自动卸载
    def fix_uninstall_stale():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "pandaone", "-y"],
                capture_output=True, timeout=60,
            )
            if result.returncode == 0:
                # 卸载后重新装本地源码
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", ".",
                     "--no-build-isolation"],
                    cwd=str(REPO_ROOT),
                    capture_output=True, timeout=180, check=True,
                )
                return True, "stale pandaone uninstalled, local source installed"
            return False, f"uninstall failed: {result.stderr.decode(errors='replace')[:200]}"
        except Exception as fe:
            return False, f"exception: {fe}"

    return CheckResult(
        "pandaone 安装",
        "WARN",
        f"{pandaone.__version__}（site-packages：{pkg_file}）",
        fix_hint=(
            "装的是 PyPI 上的旧版。建议本地源码安装：\n"
            f"    python -m pip install -e {REPO_ROOT} --no-build-isolation"
        ),
        fix_action=fix_uninstall_stale,
        fixable=True,
    )


def check_pandaone_exe_in_path() -> CheckResult:
    """pandaone 命令在 PATH"""
    exe = shutil.which("pandaone")
    if exe:
        return CheckResult("pandaone.exe PATH", "OK", exe)

    # 检查 Scripts 目录
    if sys.platform == "win32":
        scripts_dir = Path(sys.executable).parent / "Scripts"
        if (scripts_dir / "pandaone.exe").exists():
            def fix_windows_path():
                """Windows: 临时加入 PATH（不修改注册表，避免破坏系统）"""
                os.environ["PATH"] = str(scripts_dir) + os.pathsep + os.environ.get("PATH", "")
                if shutil.which("pandaone"):
                    return True, f"added to PATH (current session): {scripts_dir}"
                return False, "failed to add to PATH"

            def fix_windows_path_persist():
                """Windows: 持久化到用户级 PATH（用 setx 写 HKCU\Environment）

                setx 写的是 HKEY_CURRENT_USER\Environment\Path，新开的 PowerShell
                会自动看到（无需重新登录）。返回的限制：进程内 PATH 仍要重启
                shell 才生效，但 --fix 会同时调用 fix_windows_path 让当前进程也可见。
                """
                try:
                    # setx PATH "%PATH%;<dir>" 会追加到现有 PATH
                    result = subprocess.run(
                        ["setx", "PATH", f"%PATH%;{scripts_dir}"],
                        capture_output=True, timeout=30,
                    )
                    if result.returncode != 0:
                        return False, f"setx failed (exit {result.returncode})"
                    # 同时让当前进程也能找到
                    os.environ["PATH"] = str(scripts_dir) + os.pathsep + os.environ.get("PATH", "")
                    return True, (
                        f"persisted to user PATH via setx: {scripts_dir}\n"
                        f"         (open new shell for it to take effect)"
                    )
                except FileNotFoundError:
                    return False, "setx not available on this system"
                except Exception as e:
                    return False, f"setx exception: {e}"

            return CheckResult(
                "pandaone.exe PATH", "WARN",
                f"已安装到 {scripts_dir} 但不在 PATH",
                fix_hint=(
                    f"添加 {scripts_dir} 到 PATH（用户级 PATH）\n"
                    f"          默认 fix 只对当前进程生效；加 --persist-path 持久化到用户级"
                ),
                fix_action=fix_windows_path,
                fix_action_persist=fix_windows_path_persist,
                fixable=True,
            )
    else:
        # Unix 上检查 ~/.local/bin
        local_bin = Path.home() / ".local" / "bin" / "pandaone"
        if local_bin.exists():
            def fix_unix_path():
                os.environ["PATH"] = str(local_bin.parent) + os.pathsep + os.environ.get("PATH", "")
                if shutil.which("pandaone"):
                    return True, f"added to PATH (current session): {local_bin.parent}"
                return False, "failed to add to PATH"

            def fix_unix_path_persist():
                """Unix: 持久化到 ~/.bashrc 或 ~/.zshrc"""
                # 检测当前 shell
                shell_rc_candidates = []
                if os.environ.get("BASH_VERSION") or Path.home().joinpath(".bashrc").exists():
                    shell_rc_candidates.append(Path.home() / ".bashrc")
                if os.environ.get("ZSH_VERSION") or Path.home().joinpath(".zshrc").exists():
                    shell_rc_candidates.append(Path.home() / ".zshrc")
                # 至少选一个
                if not shell_rc_candidates:
                    shell_rc_candidates.append(Path.home() / ".profile")
                path_line = f'export PATH="{local_bin.parent}:$PATH"\n'
                panda_marker = "# Added by Pandaone doctor.py\n"
                try:
                    for rc in shell_rc_candidates:
                        existing = rc.read_text(encoding="utf-8") if rc.exists() else ""
                        if str(local_bin.parent) in existing:
                            continue  # 已经加过
                        with rc.open("a", encoding="utf-8") as f:
                            f.write(panda_marker + path_line)
                    os.environ["PATH"] = str(local_bin.parent) + os.pathsep + os.environ.get("PATH", "")
                    return True, (
                        f"persisted to {', '.join(str(r) for r in shell_rc_candidates)}\n"
                        f"         (run `source {shell_rc_candidates[0]}` or open new shell)"
                    )
                except Exception as e:
                    return False, f"shell rc write failed: {e}"

            return CheckResult(
                "pandaone.exe PATH", "WARN",
                f"已安装到 {local_bin} 但不在 PATH",
                fix_hint=(
                    f"添加 {local_bin.parent} 到 PATH\n"
                    f"          默认 fix 只对当前进程生效；加 --persist-path 持久化到 ~/.bashrc"
                ),
                fix_action=fix_unix_path,
                fix_action_persist=fix_unix_path_persist,
                fixable=True,
            )
    return CheckResult(
        "pandaone.exe PATH", "INFO",
        "未在 PATH 找到（可用 `python -m pandaone` 替代）",
    )


def check_fingerprint() -> CheckResult:
    """~/.pandaone_fp.txt 检测（污染 vs 缺失 vs 空文件）"""
    fp_path = Path.home() / ".pandaone_fp.txt"
    if not fp_path.exists():
        return CheckResult(
            "指纹文件", "OK",
            f"{fp_path} 不存在（首次运行会自动生成）",
        )

    def fix_remove_fp():
        try:
            fp_path.unlink(missing_ok=True)
            return True, f"removed {fp_path}"
        except Exception as fe:
            return False, f"unlink failed: {fe}"

    try:
        stored = fp_path.read_text(encoding="utf-8").strip()
        if not stored:
            return CheckResult(
                "指纹文件", "WARN",
                f"{fp_path} 存在但为空",
                fix_hint=f"删除 {fp_path} 让 Pandaone 自动重新生成",
                fix_action=fix_remove_fp,
                fixable=True,
            )
        return CheckResult(
            "指纹文件", "INFO",
            f"{fp_path} 含 {stored[:16]}...（存在即正常，污染会在测试时暴露）",
            fix_action=fix_remove_fp,
            fixable=True,
        )
    except Exception as e:
        return CheckResult(
            "指纹文件", "WARN", f"读取失败: {e}",
            fix_hint=f"删除 {fp_path}",
            fix_action=fix_remove_fp,
            fixable=True,
        )


def check_setuptools() -> CheckResult:
    """setuptools 可用（pip install -e . 需要）"""
    try:
        import setuptools
        return CheckResult(
            "setuptools", "OK", f"{setuptools.__version__}",
        )
    except ImportError:
        def fix_setuptools():
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "setuptools", "wheel"],
                    capture_output=True, timeout=120, check=True,
                )
                return True, "setuptools + wheel installed"
            except Exception as fe:
                return False, f"pip install failed: {fe}"
        return CheckResult(
            "setuptools", "FAIL", "未安装",
            fix_hint="python -m pip install setuptools wheel",
            fix_action=fix_setuptools,
            fixable=True,
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
            def make_fix_dep(name=dep_name):
                def fix_dep():
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", name],
                            capture_output=True, timeout=120, check=True,
                        )
                        return True, f"{name} installed"
                    except Exception as fe:
                        return False, f"pip install {name} failed: {fe}"
                return fix_dep
            results.append(CheckResult(
                f"依赖 {dep_name}", "FAIL", f"未安装",
                fix_hint=f"python -m pip install {dep_name}",
                fix_action=make_fix_dep(),
                fixable=True,
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
# 修复调度
# ============================================================

@dataclass
class FixOutcome:
    """单次修复动作的结果"""
    check_name: str
    applied: bool           # True = 真改了系统，False = dry-run
    success: bool           # True = 修复成功
    message: str

    def to_dict(self) -> dict:
        return {
            "check": self.check_name,
            "applied": self.applied,
            "success": self.success,
            "message": self.message,
        }


def apply_fixes(
    results: list[CheckResult],
    do_apply: bool,
    only_failed: bool = True,
    persist_path: bool = False,
) -> list[FixOutcome]:
    """运行全部可自动修复项

    Args:
        results: run_all_checks() 的输出
        do_apply: True = 真正执行修复；False = dry-run（仅报告"可修"）
        only_failed: 仅对非 OK 状态尝试修复（推荐）
        persist_path: True = 对 PATH 类修复用持久化版本（Windows setx / Unix shell rc）

    Returns:
        修复动作列表（每个 CheckResult 至多一项 FixOutcome）
    """
    outcomes: list[FixOutcome] = []

    for r in results:
        if r.fix_action is None:
            continue
        if only_failed and r.status == "OK":
            continue

        # 选择 fix：persist_path + 有 _persist 变体时用持久化版
        fix_fn = r.fix_action
        if persist_path and r.fix_action_persist is not None:
            fix_fn = r.fix_action_persist

        if not do_apply:
            outcomes.append(FixOutcome(
                check_name=r.name,
                applied=False,
                success=True,
                message=f"[DRY-RUN] would fix: {r.message}",
            ))
            continue

        try:
            ok, msg = fix_fn()
            outcomes.append(FixOutcome(
                check_name=r.name,
                applied=True,
                success=ok,
                message=msg,
            ))
        except Exception as e:
            outcomes.append(FixOutcome(
                check_name=r.name,
                applied=True,
                success=False,
                message=f"exception during fix: {e}",
            ))
    return outcomes


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
        check_pandaone_installed,
        check_pandaone_exe_in_path,
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
        description="Pandaone 环境自检工具（默认 dry-run；加 --fix 真正修复）",
    )
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出（CI 用）")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="只输出 WARN/FAIL")
    parser.add_argument("--fix", action="store_true",
                        help="尝试自动修复可修问题（默认仅 dry-run 报告）")
    parser.add_argument("--fix-only", action="store_true",
                        help="只跑修复，跳过详细诊断输出")
    parser.add_argument("--persist-path", action="store_true",
                        help="对 PATH 类修复持久化（Win setx / Unix shell rc），需与 --fix 同用")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="非交互模式（用于脚本；当前 doctor 无交互 prompt，保留备用）")
    args = parser.parse_args()

    # --fix-only 隐含启用 --fix
    if args.fix_only:
        args.fix = True

    # --persist-path 隐含启用 --fix（用户没意义在 dry-run 时持久化）
    if args.persist_path:
        args.fix = True

    # ---- 1) 初次诊断 ----
    initial_results = run_all_checks()

    # ---- 2) --fix 时跑修复 ----
    fix_outcomes: list[FixOutcome] = []
    if args.fix:
        fix_outcomes = apply_fixes(
            initial_results,
            do_apply=True,
            persist_path=args.persist_path,
        )

    # ---- 3) 修复后重测 ----
    if args.fix:
        post_results = run_all_checks()
    else:
        post_results = initial_results

    # 决定用哪份 results 用于输出
    if args.fix_only:
        # 只显示修复动作 + 重测
        results = post_results
        show_initial = False
    else:
        results = post_results
        show_initial = (args.fix)  # --fix 时也显示初始状态

    # quiet 过滤
    if args.quiet:
        results = [r for r in results if r.status in ("WARN", "FAIL")]

    # ---- JSON 输出 ----
    if args.json:
        payload = {
            "platform": platform.platform(),
            "python": sys.version,
            "results": [r.to_dict() for r in post_results],
            "passed": all(r.status != "FAIL" for r in post_results),
        }
        if fix_outcomes:
            payload["fixes"] = [o.to_dict() for o in fix_outcomes]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["passed"] else 1

    # ---- 人类可读输出 ----
    print("=" * 70)
    print(f" Pandaone 环境自检 — doctor.py")
    print(f" 平台: {platform.platform()}")
    print(f" Python: {sys.version.split()[0]}")
    print(f" 仓库: {REPO_ROOT}")
    print("=" * 70)

    # 显示初始状态（如果 --fix 且非 fix-only）
    if show_initial:
        print()
        print(_color("  [ 初始状态 ]", BLUE))
        for r in initial_results:
            if r.status in ("WARN", "FAIL"):
                print(f"    {r.status}: {r.name}: {r.message}")
        print()

    # 显示修复动作
    if fix_outcomes:
        print()
        print(_color("  [ 自动修复 ]", BLUE))
        for o in fix_outcomes:
            if o.applied:
                marker = _color("[OK]", GREEN) if o.success else _color("[FAIL]", RED)
                print(f"    {marker} {o.check_name}: {o.message}")
            else:
                print(f"    {marker} {o.check_name}: {o.message}")
        print()

    # 显示重测结果（除非 fix-only 模式）
    if not args.fix_only:
        print()
        for r in results:
            print(r.render())
            print()

    # ---- 总结 ----
    print("=" * 70)
    fail_count = sum(1 for r in post_results if r.status == "FAIL")
    warn_count = sum(1 for r in post_results if r.status == "WARN")

    if fail_count == 0:
        if warn_count == 0:
            print(_color(" [OK] All checks passed!", GREEN))
        else:
            print(_color(f" [WARN] {warn_count} WARN remaining", YELLOW))
        print("=" * 70)
        return 0
    print(_color(f" [FAIL] {fail_count} FAIL + {warn_count} WARN remaining", RED))
    print("=" * 70)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[ABORTED]")
        sys.exit(2)
