# Install

## Requirements

- **OS**: Windows 10+ / macOS 10.14+ / Linux
- **Optional**: git (for L3 pre-commit hook + L2 rollback + L7 CI verification)
- **Python**: As of v0.7.13, the one-line installer auto-installs embedded Python 3.12 on Windows (**no admin required**)

---

## Recommended: One-line hard-isolated install (v0.7.11+, v0.7.13 zero-preinstall)

**One command configures everything** — Python auto-installed, venv auto-created, wheel auto-downloaded, PATH auto-configured, Windows right-click menu + git pre-commit hook (all platforms) auto-set-up.

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex
```

### macOS / Linux

```bash
curl -sSL https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.sh | bash
```

### What the installer does automatically

| Step | Behavior |
|---|---|
| 1. Detect Python ≥ 3.8 | Use what's in PATH; if missing → Windows auto-downloads embedded Python 3.12 to `%LOCALAPPDATA%\pandaone\python\` (**no admin**) |
| 2. Detect Git | Use what's in PATH; if missing → print platform-specific install command (winget / brew / xcode-select / apt / dnf / yum / pacman / apk) |
| 3. Create hard-isolated venv | `venv` at `%LOCALAPPDATA%\pandaone\venv\` (Windows) or `~/.local/share/pandaone/venv` (macOS/Linux) — **does NOT pollute system site-packages** |
| 4. Download wheel | From GitHub Release API + **SHA256 verify** (does not trust PyPI mirror) |
| 5. Install pandaone | `pip install` into venv |
| 6. Add PATH | venv/Scripts persisted to user environment (Windows HKCU / macOS `~/.zshrc` / Linux `~/.bashrc`) |
| 7. Windows right-click menu | Auto-runs `pandaone install-context` (HKCU registry) |
| 8. Git pre-commit hook | Auto-runs `pandaone install-hook` (**only if cwd is a git repo + git available**) |

### Verify

```powershell
pandaone --version
# pandaone-guard v0.7.13

pandaone doctor
# Environment diagnostics (9 checks + 13 auto-fix categories)
```

### Opt-out flags

```powershell
# Windows: skip right-click menu + git hook auto-config
irm ... | iex -SkipContext -SkipHook

# macOS/Linux: skip git hook
curl ... | bash --skip-hook
```

---

## Alternative: Traditional pip install (pre-v0.7.11, still supported)

```bash
pip install pandaone-guard

# Manually configure environment
pandaone install-context   # Windows right-click menu
pandaone install-hook      # git pre-commit hook (in git repo)
```

**Comparison**:
- ✅ Simple (one pip line)
- ⚠️ Requires Python ≥ 3.8 pre-installed (Windows: download .msi from `python.org`)
- ⚠️ Installs to system site-packages (conflicts with multi-Python versions)
- ⚠️ Right-click menu / git hook need manual setup

---

## Upgrade

### One-line installer upgrade (recommended, auto-pulls latest release)

```powershell
# Windows
irm https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.ps1 | iex

# macOS / Linux
curl -sSL https://raw.githubusercontent.com/hellob1889/Pandaone-AI-Agent/main/install.sh | bash
```

The installer **auto-detects**:
- venv exists → upgrade wheel (don't recreate venv)
- Already latest version → skip download

### Traditional way

```bash
pip install pandaone-guard --upgrade
pandaone install-context   # Reinstall right-click menu (idempotent)
pandaone install-hook      # Reinstall git hook (idempotent)
```

---

## Uninstall

### One-line install (recommended)

**Windows**:
```powershell
Remove-Item -Recurse -Force $env:LOCALAPPDATA\pandaone
# Manually remove venv/Scripts from user PATH
```

**macOS / Linux**:
```bash
rm -rf ~/.local/share/pandaone
# Manually remove PATH append from shell rc
```

### Traditional pip install

```bash
pip uninstall pandaone-guard
rm -rf ~/.pandaone_fp.txt
# Right-click menu + git hook need manual cleanup
pandaone install-context --uninstall   # Windows
rm .git/hooks/pre-commit .pandaone/pre-commit-check.py   # git hook
```

---

## Docker (optional)

```dockerfile
FROM python:3.11-slim
RUN pip install pandaone-guard
ENTRYPOINT ["pandaone"]
```

No right-click menu / git hook needed inside Docker (those are host integrations).

---

## Troubleshooting

### PowerShell refuses to run install.ps1

PowerShell's default ExecutionPolicy is `Restricted`, which blocks scripts.
`irm ... | iex` (iex = Invoke-Expression) implicitly uses `-ExecutionPolicy Bypass` — no manual setup needed.

If you manually downloaded `install.ps1` and run it directly:
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Python not installed (Windows)

As of v0.7.13, the one-line installer **auto-downloads embedded Python 3.12.7** to `%LOCALAPPDATA%\pandaone\python\`:
- No admin required
- No GUI required
- 11 MB download
- Auto-enables `import site` (otherwise venv pip install would fail)

If download fails (network issue):
- Manually install Python: https://www.python.org/downloads/windows/ (**check "Add Python to PATH"**)
- Then re-run install.ps1

### Git not installed

The installer auto-prints **platform-specific install commands**:

| Platform | Command |
|---|---|
| Windows (with winget) | `winget install Git.Git` (requires admin) |
| Windows (no winget) | https://git-scm.com/download/win |
| macOS | `xcode-select --install` or `brew install git` |
| Ubuntu/Debian | `sudo apt install git` |
| Fedora | `sudo dnf install git` |
| CentOS/RHEL | `sudo yum install git` |
| Arch | `sudo pacman -S git` |
| Alpine | `sudo apk add git` |

After installing git, **re-run install.ps1** to complete git pre-commit hook setup.

### Windows right-click menu not appearing

1. Restart Explorer:
   ```powershell
   Stop-Process -Name explorer -Force
   Start-Process explorer
   ```

2. Or reinstall right-click menu:
   ```powershell
   pandaone install-context --force
   ```

### macOS/Linux right-click menu

**Pandaone does NOT auto-install macOS/Linux right-click menu** (no standardized registry mechanism):

| Platform | Alternative |
|---|---|
| macOS Finder | Automator Quick Action running `pandaone audit "$@"` |
| Linux Nautilus | Write `~/.local/share/nautilus/scripts/Pandaone Audit` shell script |
| Linux Nemo | Write `.nemo_action` file |
| Linux Dolphin | Write `.desktop` ServiceMenu file |

See [context-menu.md](context-menu.md).

### PermissionError when locking

Pandaone uses chmod / `attrib +r` to lock files.
- Linux/macOS: POSIX standard behavior
- Windows: `attrib +R`, transparent to regular users
- **If you see PermissionError** — it means locking is working (this is expected)

### PDF Chinese shows as squares

PDF export depends on system fonts. Windows ships with `msyh.ttc`, macOS with `PingFang.ttc`.
Linux users:
```bash
sudo apt install fonts-wqy-microhei fonts-noto-cjk
```

---

## Advanced: Source install (developers)

```bash
git clone https://github.com/hellob1889/Pandaone-AI-Agent
cd Pandaone-AI-Agent
pip install -e .[dev]
pytest tests/ -v
# 342+ passed
```

**Not recommended** for regular users — no isolated venv, will pollute system site-packages.

---

## Dependencies

Auto-installed dependencies (all pure Python, cross-platform, **no C extensions**):

| Package | Purpose |
|---|---|
| `watchdog>=3.0.0` | L2 file monitoring (real-time change detection) |
| `openpyxl>=3.1.0` | Excel export |
| `python-docx>=1.1.0` | Word export |
| `reportlab>=4.0.0` | PDF export (with CJK support) |
| `pyyaml>=6.0` | YAML export |

---

Next: [Quick Start](quickstart.md) | [Commands](commands.md) | [MCP Integration](mcp-integration.md)