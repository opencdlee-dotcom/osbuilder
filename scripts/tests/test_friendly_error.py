"""test_friendly_error.py — RED stubs for Phase 5 friendly_error (Wave 0).

All tests skip until corresponding Wave 1 module is created.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fe():
    """Lazy import of scripts/friendly_error.py — skips when not yet created."""
    try:
        return importlib.import_module("friendly_error")
    except ImportError:
        pytest.skip("friendly_error module not yet created (Wave 1 target)")


# ---------- UX-02: translate() core behavior ----------

def test_translate_returns_friendly_message(fe):
    """UX-02: translate() returns a FriendlyMessage with title/what_broke/what_to_do/severity."""
    pytest.skip("Wave 1 target")


def test_dictionary_entry_match_wins_over_generic(fe):
    """UX-02: a dictionary hit returns entry copy (not generic fallback)."""
    pytest.skip("Wave 1 target")


def test_generic_fallback_strips_traceback(fe):
    """UX-02: generic fallback strips Python tracebacks from what_broke."""
    pytest.skip("Wave 1 target")


def test_friendly_message_no_raw_stack_frames(fe):
    """UX-02: translated what_broke contains no raw 'File \"...\"' stack-frame substrings."""
    pytest.skip("Wave 1 target")


def test_translate_enoent_returns_title(fe):
    """UX-02: translate('ENOENT: ...') returns a non-empty title and no traceback text."""
    pytest.skip("Wave 1 target")


# ---------- UX-05: dictionary schema and contents ----------

def test_dictionary_has_30_entries(fe):
    """UX-05: load_dictionary() returns >= 30 entries."""
    pytest.skip("Wave 1 target")


def test_dictionary_schema_all_9_fields(fe):
    """UX-05: each entry has all 9 documented fields.

    NOTE: 9 fields (RESEARCH.md authoritative; SPEC's "8" was a pre-research count;
    expansion_note is field 9). Fields: id, match_pattern, category, title, what_broke,
    what_to_do, copy_paste_command, phase_seen, expansion_note.
    """
    pytest.skip("Wave 1 target")


def test_dictionary_format_version_checked(fe, tmp_path):
    """UX-05: load_dictionary() raises SystemExit when format_version is wrong."""
    pytest.skip("Wave 1 target")


def test_dictionary_readme_exists():
    """UX-05: references/friendly-errors/README.md exists."""
    pytest.skip("Wave 1 target")


# ---------- UX-02: import-guard wiring across the 5 known scripts ----------

def test_import_guard_in_all_five_scripts():
    """UX-02: all 5 scripts contain 'import friendly_error' or 'from scripts.friendly_error'.

    The 5 scripts: preflight_check.py, scaffold_dispatch.py, stack_researcher.py,
    intake_handler.py, gsd_driver.py — Wave 1 will assert via grep on each file.
    """
    pytest.skip("Wave 1 target")


def test_error_paths_wrapped_in_known_sites():
    """UX-02: the 3 scripts with known error surfaces (preflight_check.py, scaffold_dispatch.py,
    gsd_driver.py) each contain at least one '_fe.translate' call site (the
    'if _fe is not None:' pattern). stack_researcher.py and intake_handler.py are
    import-guard only — no known error surfaces in current Phase 4 codebase.
    """
    pytest.skip("Wave 1 target")
