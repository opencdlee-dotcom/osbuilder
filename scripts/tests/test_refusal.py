"""test_refusal.py — RED stubs for Phase 6 refusal mechanics (Wave 0 — Plan 06-01).

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
def ih():
    """Lazy import of scripts/intake_handler.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")


def test_kubernetes_refused(ih, tmp_project_root, fake_state_md, monkeypatch, capsys):
    """SCL-05 (V-14): spec containing 'kubernetes' triggers refusal — last_failure starts with 'refused:' and stderr contains refusal copy."""
    pytest.skip("Wave 1 target")


def test_clean_spec_passes(ih, tmp_project_root, fake_state_md, monkeypatch):
    """SCL-05 (V-14 negative): spec with no refuse keywords does NOT trigger refusal — gate returns False."""
    pytest.skip("Wave 1 target")


def test_refusal_copy_mentions_opt_in():
    """SCL-05 (V-15): references/refuse-list.md content mentions 'production-ready' opt-in path (case-insensitive)."""
    pytest.skip("Wave 1 target")
