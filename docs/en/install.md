# Install

## Requirements

- **Python 3.8+** (tested on 3.10/3.11/3.12)
- **OS**: Windows 10+ / macOS 10.14+ / Linux
- **Optional**: git (for L2 rollback and L7 CI verification)

## One-line Install

```bash
pip install pandax-guard
```

## Verify

```bash
pandaone --version
# pandaone-guard v0.7.2
```

## Dev Install

```bash
git clone https://github.com/hellob1889/Pandaone-AI-Agent
cd pandaone
pip install -e .[dev]
pytest tests/ -v
# 340 passed
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
pip install pandax-guard --upgrade
```

## Uninstall

```bash
pip uninstall pandax-guard
rm -rf ~/.pandaone_fp.txt
```

---

Next: [Quick Start](quickstart.md) | [Commands](commands.md)