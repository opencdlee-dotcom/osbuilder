"""test_runbook_writer.py — RED stubs for Phase 6 runbook_writer (Wave 0 — Plan 06-01).

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
def rw():
    """Lazy import of scripts/runbook_writer.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("runbook_writer")
    except ImportError:
        pytest.skip("runbook_writer module not yet created (Wave 1 target)")


def test_runbook_writes_quickstart(rw, fake_built_app, fake_state_md, tmp_project_root):
    """SHIP-02 (V-03): rw.write_readme() produces README.md with Quick Start + no unsubstituted placeholders."""
    pytest.skip("Wave 1 target")
