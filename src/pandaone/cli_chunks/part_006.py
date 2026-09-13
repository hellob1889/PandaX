# cli.py chunk 6/6: lines 2069-2351
# Phase 9: OS 右键菜单集成
# ============================================================
def _find_installer_dir():
    """定位 installer/ 目录。"""
    return Path(__file__).resolve().parent / "installer"


INSTALLER_DIR = _find_installer_dir()

PLATFORM_HANDLERS = {
    "Windows": {
        "install": "windows/install_context_menu.ps1",
        "uninstall": "windows/uninstall_context_menu.ps1",
        "interpreter": ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File"],
    },
    "Darwin": {
        "install": "macos/install_context_menu.sh",
        "uninstall": "macos/uninstall_context_menu.sh",
        "interpreter": ["bash"],
    },
    "Linux": {
        "install": "linux/install_context_menu.sh",
        "uninstall": "linux/uninstall_context_menu.sh",
        "interpreter": ["bash"],
    },
}


def detect_os_key():
    """sys.platform → PLATFORM_HANDLERS key"""
    p = sys.platform
    if p.startswith("win"):
        return "Windows"
    if p.startswith("darwin"):
        return "Darwin"
    if p.startswith("linux") or p.startswith("freebsd"):
        return "Linux"
    return ""


def _run_installer(action, force=False):
    """action: install|uninstall"""
    os_key = detect_os_key()
    if not os_key:
        return 2
    handler = PLATFORM_HANDLERS[os_key]
    script_rel = handler[action]
    interpreter = handler["interpreter"]
    script_path = INSTALLER_DIR / script_rel
    if not script_path.exists():
        return 1
    cmd = interpreter + [str(script_path)]
    if action == "install" and force and os_key == "Windows":
        cmd += ["-Force"]
    env = os.environ.copy()
    try:
        from .i18n import get_lang
        env["PANDAX_LANG"] = get_lang()
    except Exception:
        pass
    try:
        result = subprocess.run(cmd, check=False, env=env, timeout=60, capture_output=True, text=True)
        return result.returncode
    except subprocess.TimeoutExpired:
        return 124
    except FileNotFoundError:
        return 127


def cmd_install_context(args):
    """Phase 9 - 安装 OS 右键菜单"""
    force = getattr(args, "force", False)
    lang = getattr(args, "lang", None)
    if lang:
        i18n_init(lang)
    return _run_installer("install", force=force)


def cmd_uninstall_context(args):
    """Phase 9 - 卸载 OS 右键菜单"""
    return _run_installer("uninstall")


COMMANDS = {
    "init": cmd_init,
    "lock": cmd_lock,
    "unlock": cmd_unlock,
    "write": cmd_write,
    "log": cmd_log,
    "export": cmd_export,
    "install-git": cmd_install_git,
    "install-hook": cmd_install_hook,
    "status": cmd_status,
    "watch": cmd_watch,
    "serve": cmd_serve,
    "ci": cmd_ci,
    "install-context": cmd_install_context,
    "uninstall-context": cmd_uninstall_context,
}


def main(argv=None):
    argv_list = argv if argv is not None else sys.argv[1:]
    import re as _re
    has_trust_default = any(a == "--trust-default" or a.startswith("--trust-default=") for a in argv_list)
    has_silent = any(a == "--silent" or a.startswith("--silent=") for a in argv_list)
    cleaned_argv = []
    lang_override = None
    i = 0
    while i < len(argv_list):
        arg = argv_list[i]
        m_eq = _re.fullmatch(r"--lang=(\S+)", arg)
        if m_eq:
            lang_override = m_eq.group(1)
            i += 1
            continue
        if arg == "--lang" and i + 1 < len(argv_list):
            lang_override = argv_list[i + 1]
            i += 2
            continue
        if arg == "--trust-default" or arg.startswith("--trust-default="):
            i += 1
            continue
        if arg == "--silent" or arg.startswith("--silent="):
            i += 1
            continue
        cleaned_argv.append(arg)
        i += 1
    if has_silent:
        cleaned_argv.insert(0, "--silent")
    if has_trust_default:
        cleaned_argv.insert(0, "--trust-default")
    if lang_override is not None and lang_override not in ("zh-CN", "en"):
        cleaned_argv.append(f"--lang={lang_override}")
        lang_override = None
    parser = build_parser()
    args, _ = parser.parse_known_args(cleaned_argv)
    if lang_override is not None:
        args.lang = lang_override
    i18n_init(args.lang)
    if "--update-fingerprint" in argv_list:
        pass
    elif getattr(args, "trust_default", False):
        if not check_fingerprint(silent=True):
            new_fp = compute_fingerprint()
            FP_PATH.parent.mkdir(parents=True, exist_ok=True)
            FP_PATH.write_text(new_fp, encoding="utf-8")
    else:
        if not check_fingerprint():
            return 1
    if not getattr(args, "silent", False):
        banner = load_banner()
        for line in banner:
            print(line)
        summary = load_readme_summary()
        for line in summary:
            print(line)
    if getattr(args, "version", False):
        from pandaone import __version__
        print(f"pandaone v{__version__}")
        return 0
    if getattr(args, "update_fingerprint", None):
        pwd = args.update_fingerprint
        expected = get_fingerprint_password()
        if pwd != expected:
            print(t("err_password_wrong"))
            return 1
        new_fp = compute_fingerprint()
        FP_PATH.write_text(new_fp, encoding="utf-8")
        print(t("ok_fp_updated", fp=new_fp[:16]))
        return 0
    if args.command is None:
        parser.print_help()
        return 0
    handler = COMMANDS.get(args.command)
    if handler is None:
        print(t("err_unknown_cmd", cmd=args.command))
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
