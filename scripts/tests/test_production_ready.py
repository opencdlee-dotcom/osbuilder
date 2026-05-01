"""test_production_ready.py — GREEN tests for Phase 6 production_phase_writer (Wave 1 — Plan 06-05).

V-16: test_emits_seven_phases — production_ready=true emits exactly 7 /gsd-add-phase lines
V-17: test_no_emit_when_default — production_ready=false (default) emits nothing

Locked test names — DO NOT rename.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_PHASE_WRITER = REPO_ROOT / "scripts" / "production_phase_writer.py"


@pytest.fixture
def pp():
    """Lazy import of scripts/production_phase_writer.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("production_phase_writer")
    except ImportError:
        pytest.skip("production_phase_writer module not yet created (Wave 1 target)")


def test_emits_seven_phases(pp, tmp_project_root, fake_state_md):
    """SCL-06 (V-16): with production_ready='true', emit subcommand prints exactly 7 /gsd-add-phase lines."""
    # Seed state.md with production_ready=true
    fake_state_md(production_ready="true")

    # Run the emit subcommand as a subprocess to capture stdout
    result = subprocess.run(
        [sys.executable, str(PRODUCTION_PHASE_WRITER), "emit",
         "--project-root", str(tmp_project_root)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"emit returned {result.returncode}: {result.stderr}"

    lines = [ln for ln in result.stdout.splitlines() if ln.startswith("/gsd-add-phase")]
    assert len(lines) == 7, f"expected 7 /gsd-add-phase lines, got {len(lines)}: {lines}"

    # Verify all 7 named upgrades appear
    for name in pp.NAMED_UPGRADES:
        assert any(name in ln for ln in lines), (
            f"expected '/gsd-add-phase {name}' in output, got: {lines}"
        )


def test_no_emit_when_default(pp, tmp_project_root, fake_state_md):
    """SCL-06 (V-17): with production_ready='false' (default), emit subcommand prints nothing."""
    # Seed state.md without production_ready (defaults to false)
    fake_state_md()

    result = subprocess.run(
        [sys.executable, str(PRODUCTION_PHASE_WRITER), "emit",
         "--project-root", str(tmp_project_root)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"emit returned {result.returncode}: {result.stderr}"
    assert result.stdout.strip() == "", (
        f"expected empty stdout when production_ready is not 'true', got: {result.stdout!r}"
    )
