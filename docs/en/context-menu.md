# OS Context Menu Integration

Pandaone AI Agent ships with **native right-click menu integration** for **Windows / macOS / Linux**. Right-click any file or folder → "Pandaone" → pick init / lock / unlock / status. **No terminal required**.

## One-liner

```bash
# Any platform — auto-detects OS
pandaone install-context

# Force reinstall (Windows only)
pandaone install-context --force

# Remove
pandaone uninstall-context
```

## Per-Platform Details

### Windows (HKCU registry cascade menu)

- **No admin needed** (HKCU user-level)
- **3 locations**: any file / folder / empty area
- **4 actions**: Init / Lock / Unlock / Status (cascade sub-menu)
- **Icon**: uses `pandaone.exe`'s built-in icon
- **Idempotent**: safe to re-run

Manual run:

```powershell
powershell -ExecutionPolicy Bypass -File installer\windows\install_context_menu.ps1 [-Force] [-DryRun]
```

`DryRun` only prints the plan without writing registry (for testing).

### macOS (Automator Quick Action)

- **Services menu**: Finder right-click → "Services" → "Pandaone"
- **First-time enable**: System Settings → Keyboard → Shortcuts → Services → enable "Files and Folders → Pandaone"
- **Action picker**: dialog chooses init / lock / unlock / status → Terminal.app opens automatically

Manual run:

```bash
bash installer/macos/install_context_menu.sh
```

### Linux (Nautilus + Dolphin)

- **Nautilus (GNOME / Files)**: right-click → "Scripts" → Pandaone
- **Dolphin (KDE)**: right-click → Actions → Pandaone → Init/Lock/Unlock/Status
- **Auto-detects** desktop environment (`$XDG_CURRENT_DESKTOP`)
- **User-level**: `~/.local/share/nautilus/scripts/` and `~/.local/share/kservices5/ServiceMenus/`

Manual run:

```bash
bash installer/linux/install_context_menu.sh
```

## Workflow Example

1. Get a new project
2. **Right-click project folder** → Pandaone → **init** → initialized
3. **Right-click project folder** → Pandaone → **lock** → all files locked
4. AI edits a file → must run `pandaone write --file X.py --reason ...`
5. **Right-click project folder** → Pandaone → **status** → view audit state

## File Layout

```
installer/
├── windows/
│   ├── install_context_menu.ps1
│   └── uninstall_context_menu.ps1
├── macos/
│   ├── install_context_menu.sh
│   ├── uninstall_context_menu.sh
│   └── Pandaone Lock.workflow/
└── linux/
    ├── install_context_menu.sh
    ├── uninstall_context_menu.sh
    ├── nautilus/Pandaone
    └── dolphin/pandaone-lock.desktop
```

## First Principles

Right-click menu makes Pandaone's core mechanism (**all changes must be audited**) **unbypassable**:

- Files are locked at OS level (`attrib +r` / `chmod 444`)
- AI agents must `pandaone unlock` or `pandaone write` to modify
- `pandaone write` forces `reason / problem / approach` fields
- This forces the AI to **think before writing**, not **justify after**

Right-click menu is not a convenience — it's the **last mile of the audit system**.