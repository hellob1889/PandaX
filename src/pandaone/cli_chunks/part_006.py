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
    if os_key == "Windows":
        return _windows_registry_install(action, force)
    handler = PLATFORM_HANDLERS[os_key]
    script_rel = handler[action]
    interpreter = handler["interpreter"]
    script_path = INSTALLER_DIR / script_rel
    if not script_path.exists():
        return 1
    cmd = interpreter + [str(script_path)]
    env = os.environ.copy()
    try:
        from .i18n import get_lang
        env["PANDAX_LANG"] = get_lang()
    except Exception:
        pass
    try:
        result = subprocess.run(cmd, check=False, env=env, timeout=60)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(t("ctx_subprocess_timeout", script=script_path), file=sys.stderr)
        return 124
    except FileNotFoundError:
        print(t("ctx_interp_not_found", interp=interpreter[0]), file=sys.stderr)
        return 127
