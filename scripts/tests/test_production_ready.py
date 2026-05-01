"""test_production_ready.py — RED stubs for Phase 6 production_phase_writer (Wave 0 — Plan 06-01).

All tests skip("Wave 1 target") until the corresponding Wave 1 module exists.
Stub bodies are pytest.skip(...) — NOT pass, NOT assert False, NOT xfail.

Locked test names (V-IDs from 06-VALIDATION.md) — DO NOT rename in Wave 1.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def pp():
    """Lazy import of scripts/production_phase_writer.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("production_phase_writer")
    except ImportError:
        pytest.skip("production_phase_writer module not yet created (Wave 1 target)")


def test_emits_seven_phases(pp, tmp_project_root, fake_state_md):
    """SCL-06 (V-16): with production_ready='true', emit subcommand prints exactly 7 /gsd-add-phase lines."""
    pytest.skip("Wave 1 target")


def test_no_emit_when_default(pp, tmp_project_root, fake_state_md):
    """SCL-06 (V-17): with production_ready='false' (default), emit subcommand prints nothing."""
    pytest.skip("Wave 1 target")
