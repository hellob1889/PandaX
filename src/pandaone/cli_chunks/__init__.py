"""pandaone cli_chunks - chunks of cli.py loaded by cli.py at import time.

V0.7.7 split: since MCP create_or_update_file single push limit ~24KB, full 82KB cli.py
must be split into chunk files, each < 20KB. cli.py loader exec()s them in order
(part_001..part_NNN) at import time, achieving equivalent to single cli.py module.
"""
