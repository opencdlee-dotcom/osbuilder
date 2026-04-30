#!/usr/bin/env python3
"""uninstall.py — remove anything OSBuilder's preflight installed (PRE-06).

Thin wrapper around preflight_check.uninstall(). The actual algorithm
(read ~/.osbuilder/install-log.json, walk actions in reverse, run each
recorded uninstall_argv) lives in preflight_check.py — see Plan 02-02.

Exists so `/osbuilder uninstall` maps to a script with that exact name,
mirroring state_writer.py's one-CLI-per-script pattern.
"""
import sys
from pathlib import Path

# Ensure scripts/ is importable when invoked directly (pytest sets this via
# pyproject.toml `pythonpath`, but a bare `python scripts/uninstall.py` invocation
# depends on CWD; the line below makes the script self-bootstrapping).
sys.path.insert(0, str(Path(__file__).parent))
from preflight_check import uninstall  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(uninstall())
