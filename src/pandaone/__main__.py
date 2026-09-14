"""让 `python -m pandaone` 工作.

PR #28 在这里加两件事:
  1. Git gate: 启动时探测 git,L2/L3 防护强依赖它。缺失则尝试自动安装。
  2. Monkey-patch: 注册 `pandaone doctor` 子命令 (cmd_doctor.py)。
     因为 cli.py 84KB 超大,MCP 单次推送限制 ~24KB,改 cli.py 不便。
     这里 monkey-patch 注册避免动 cli.py。
"""
import os
import sys


def _ensure_doctor_registered():
    """
    Monkey-patch: 注册 doctor 子命令到 cli 模块。
    """
    try:
        # 1. 先注册 i18n_extras (PR #28 doctor/git gate 的翻译 key)
        from pandaone import i18n
        try:
            from pandaone.i18n_extras import register_extras
            register_extras(i18n.TRANSLATIONS)
        except ImportError:
            pass  # i18n_extras 模块缺失 (旧版本),静默跳过

        # 2. 注册 doctor 子命令到 cli
        from pandaone import cli
        from pandaone.cmd_doctor import add_doctor_parser, cmd_doctor
    except ImportError as e:
        # 静默 — 缺 cmd_doctor 不应该阻塞 CLI
        try:
            from pandaone.i18n import t as _t
        except Exception:
            def _t(k, **kw): return k
        print(_t("_doctor_register_failed", err=str(e)), file=sys.stderr)
        return

    # 1. 注册到 COMMANDS dict (dict 引用语义,cli.main() 可见)
    if "doctor" not in cli.COMMANDS:
        cli.COMMANDS["doctor"] = cmd_doctor

    # 2. Monkey-patch build_parser,自动加 doctor subparser
    if getattr(cli, "_pandaone_doctor_patched", False):
        return  # 防止重复 patch

    _orig_build_parser = cli.build_parser

    def _patched_build_parser():
        parser = _orig_build_parser()
        # 找 subparsers action
        sub_action = None
        for action in parser._actions:
            if hasattr(action, "choices") and isinstance(action.choices, dict):
                sub_action = action
                break
        if sub_action is not None:
            try:
                add_doctor_parser(sub_action)
            except Exception as e:
                if "conflicting" not in str(e).lower() and "already" not in str(e).lower():
                    raise
        return parser

    cli.build_parser = _patched_build_parser
    cli._pandaone_doctor_patched = True


def _git_gate():
    """L2/L3 防护强依赖 git。缺失则尝试自动安装。

    Escape hatch: PANDAONE_SKIP_GIT_CHECK=1 环境变量 → 跳过 (CI / 测试)
    """
    try:
        from pandaone.i18n import t as _t
    except Exception:
        def _t(k, **kw):
            if "err" in kw:
                return f"[ERR] {kw['err']}"
            return k

    if os.environ.get("PANDAONE_SKIP_GIT_CHECK") == "1":
        return

    try:
        from pandaone.git_installer import (
            is_installed as _git_is_installed,
            install as _git_install,
            GitInstallError,
        )
    except ImportError:
        return

    if _git_is_installed():
        return

    try:
        if sys.stdout.isatty():
            print(_t("_gate_git_missing_attempt_install"))
        result = _git_install()
        if sys.stdout.isatty():
            print(_t("_gate_git_installed", ver=result.version, channel=result.channel))
            print(_t("_gate_git_installed_path", path=result.path))
            print(_t("_gate_git_restart_shell"))
    except GitInstallError as e:
        if sys.stdout.isatty():
            print(_t("_gate_git_install_failed", err=str(e)))
            from pandaone.git_installer import get_install_hint
            print(_t("_doctor_manual_hint"))
            print(get_install_hint())
    except Exception as e:
        if sys.stdout.isatty():
            print(_t("_gate_git_install_unexpected", err_type=type(e).__name__, err=str(e)))


# 模块 import 时立即注册
_ensure_doctor_registered()


def main():
    """CLI 入口: 让 entry point (`pandaone` 命令) 走这里。

    PR #32 fix: 之前 `if __name__ == "__main__":` 保护块只在 `python -m pandaone`
    时跑;entry point `pandaone` (pyproject.toml `pandaone = "pandaone:main"`)
    走 `pandaone/__init__.py:main`,**完全跳过 __main__.py**,导致 monkey-patch
    注册的 doctor 子命令不可用。
    改用顶层 `def main()` + entry point 改 `"pandaone.__main__:main"`,保证 import
    副作用(_ensure_doctor_registered)和 git_gate 都被调用。
    """
    _git_gate()
    from pandaone.cli import main as _cli_main
    sys.exit(_cli_main())


if __name__ == "__main__":
    sys.exit(main())
