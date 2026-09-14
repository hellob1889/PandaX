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

    思路:
      - cli.build_parser() 内部调用 sub.add_parser(...) 注册子命令。
      - 我们把 cli.build_parser 包一层,在原始 parser 上额外 add 一个 doctor。
      - subparsers 通过遍历 parser._actions 找到 (_SubParsersAction 类型)。
      - 同时把 cmd_doctor 加到 cli.COMMANDS dict (cli.main() 用它 dispatch)。
    """
    try:
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
            # _SubParsersAction 在 argparse 模块里,这里用 duck-typing
            if hasattr(action, "choices") and isinstance(action.choices, dict):
                sub_action = action
                break
        if sub_action is not None:
            try:
                add_doctor_parser(sub_action)
            except Exception as e:
                # 重复注册会抛错 (subparser 已存在),静默忽略
                if "conflicting" not in str(e).lower() and "already" not in str(e).lower():
                    raise
        return parser

    cli.build_parser = _patched_build_parser
    cli._pandaone_doctor_patched = True


def _git_gate():
    """
    L2/L3 防护强依赖 git。缺失则尝试自动安装。

    Escape hatch:
      - PANDAONE_SKIP_GIT_CHECK=1 环境变量 → 跳过 (CI / 测试)
      - 仅尝试安装一次,失败不抛异常 (用户可以稍后手动装)
    """
    # i18n 安全 fallback
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
        return  # git_installer 模块缺失 (旧版本),静默跳过

    if _git_is_installed():
        return  # 已装,无需操作

    # git 缺失 — 尝试自动装
    try:
        # 仅当 stdout 是 TTY 时才打印 (避免在 CI / pipe 场景噪音)
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
        # 不抛异常:让 pandaone 继续运行,L2/L3 仍会降级 + 提示
    except Exception as e:
        # 任何未预期的错误都不阻塞 CLI
        if sys.stdout.isatty():
            print(_t("_gate_git_install_unexpected", err_type=type(e).__name__, err=str(e)))


# 模块 import 时立即注册 (这样 `from pandaone.__main__ import ...` 也生效)
_ensure_doctor_registered()


if __name__ == "__main__":
    _git_gate()
    # 必须在 _git_gate 之后 import cli,确保 chunks 注册了 COMMANDS
    from pandaone.cli import main
    sys.exit(main())
