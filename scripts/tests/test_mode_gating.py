"""test_mode_gating.py — RED stubs for Phase 5 mode gating (Wave 0).

All tests skip until corresponding Wave 1 module is created.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def intake():
    """Lazy import of scripts/intake_handler.py — skips when not yet available."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet available (Wave 1 target)")


@pytest.fixture
def researcher():
    """Lazy import of scripts/stack_researcher.py — skips when not yet available."""
    try:
        return importlib.import_module("stack_researcher")
    except ImportError:
        pytest.skip("stack_researcher module not yet available (Wave 1 target)")


# ---------- UX-03: state_writer accepts 'mode' field ----------

def test_mode_field_allowed_in_state_writer(writer, tmp_project_root):
    """UX-03: state_writer.py accepts writes for the 'mode' field (beginner/advanced)."""
    pytest.skip("Wave 1 target")


# ---------- UX-03: beginner-mode jargon gate at intake ----------

def test_beginner_mode_no_jargon_in_prompts(intake, tmp_project_root, writer, capsys):
    """UX-03: parse_paragraph in beginner mode emits no stack-tech tokens to stdout."""
    pytest.skip("Wave 1 target")


# ---------- UX-03: advanced-mode exposes stack ----------

def test_advanced_mode_exposes_stack(researcher, tmp_project_root, writer, monkeypatch):
    """UX-03: research_stack in advanced mode surfaces tech-name tokens (Next.js, etc.)."""
    pytest.skip("Wave 1 target")


# ---------- UX-03: defaults and persistence ----------

def test_mode_default_is_beginner(intake, tmp_project_root):
    """UX-03: state.md with no 'mode' field returns 'beginner' from _mode_from_state."""
    pytest.skip("Wave 1 target")


def test_mode_persists_across_state_reads(writer, tmp_project_root):
    """UX-03: writing mode='advanced' then reading 'mode' returns 'advanced'."""
    pytest.skip("Wave 1 target")


def test_beginner_mode_stack_researcher_skips_brainiac(researcher, tmp_project_root, writer, monkeypatch):
    """UX-03: research_stack with mode=beginner makes no subprocess call to brainiac."""
    pytest.skip("Wave 1 target")
