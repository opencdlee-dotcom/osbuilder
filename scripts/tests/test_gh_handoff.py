"""test_gh_handoff.py — RED stubs for Phase 6 gh_handoff (Wave 0 — Plan 06-01).

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
def gh():
    """Lazy import of scripts/gh_handoff.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("gh_handoff")
    except ImportError:
        pytest.skip("gh_handoff module not yet created (Wave 1 target)")


def test_ship_runs_private_create(gh, fake_built_app, mock_gh_subprocess,
                                   tmp_project_root, fake_state_md):
    """SHIP-01 (V-01): gh.ship() invokes `gh repo create --private --source=. --push`."""
    pytest.skip("Wave 1 target")


def test_failure_modes_friendly(gh, fake_built_app, mock_gh_subprocess, capsys):
    """SHIP-01 (V-02): all 5 gh failure modes produce friendly_error-formatted stderr."""
    pytest.skip("Wave 1 target")


def test_auth_drift_friendly(gh, fake_built_app, mock_gh_subprocess, capsys):
    """SHIP-05 (V-08): gh auth drift produces stderr with `gh auth login --git-protocol https`."""
    pytest.skip("Wave 1 target")
