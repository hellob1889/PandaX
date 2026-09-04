# Install

## Requirements

- **Python 3.8+** (tested on 3.10/3.11/3.12)
- **OS**: Windows 10+ / macOS 10.14+ / Linux
- **Optional**: git (for L2 rollback and L7 CI verification)

## One-line Install

```bash
pip install pandax
```

## Verify

```bash
pandax --version
# pandax v0.6.2
```

## Dev Install

```bash
git clone https://github.com/pandax/pandax
cd pandax
pip install -e .[dev]
pytest tests/ -v
# 140 passed
```

## Dependencies

Auto-installed (all pure Python, cross-platform):

| Package | Purpose |
|---|---|
| `watchdog>=3.0.0` | L2 file monitoring |
| `openpyxl>=3.1.0` | Excel export |
| `python-docx>=1.1.0` | Word export |
| `reportlab>=4.0.0` | PDF export (with CJK support) |
| `pyyaml>=6.0` | YAML export |

**No C extensions** — works on Alpine / musl.

## Upgrade

```bash
pip install pandax --upgrade
```

## Uninstall

```bash
pip uninstall pandax
rm -rf ~/.pandax_fp.txt
```

---

Next: [Quick Start](quickstart.md) | [Commands](commands.md)