"""test_friendly_error.py — Phase 5 friendly_error tests (Wave 1 GREEN).

Wave 0 (Plan 05-01) shipped these as RED stubs that called pytest.skip.
Wave 1 (Plan 05-02) replaces each skip with real assertions against the
friendly_error module + dictionary + 5-script wiring.
"""
from __future__ import annotations

import importlib
import re
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
    msg = fe.translate("EADDRINUSE: address already in use :::3000")
    assert isinstance(msg, fe.FriendlyMessage)
    assert msg.title and isinstance(msg.title, str)
    assert msg.what_broke and isinstance(msg.what_broke, str)
    assert msg.what_to_do and isinstance(msg.what_to_do, str)
    assert msg.severity in ("info", "warn", "error", "fatal")


def test_dictionary_entry_match_wins_over_generic(fe):
    """UX-02: a dictionary hit returns entry copy (not generic fallback)."""
    msg = fe.translate("pnpm: command not found")
    assert msg.title != "Something went wrong"
    # The pnpm-not-found entry's title should mention pnpm in plain English.
    assert "pnpm" in msg.title.lower() or "pnpm" in msg.what_broke.lower()


def test_generic_fallback_strips_traceback(fe):
    """UX-02: generic fallback strips Python tracebacks from what_broke."""
    raw = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 1, in foo\n'
        "RuntimeError: boom"
    )
    msg = fe.translate(raw)
    assert "Traceback" not in msg.what_broke
    assert 'File "' not in msg.what_broke


def test_friendly_message_no_raw_stack_frames(fe):
    """UX-02: translated what_broke contains no raw 'File "...' stack-frame substrings."""
    raw = (
        "Traceback (most recent call last):\n"
        '  File "/long/path/to/module.py", line 42, in caller\n'
        "    do_thing()\n"
        '  File "/long/path/to/module.py", line 99, in do_thing\n'
        "    raise ValueError('nope')\n"
        "ValueError: nope"
    )
    msg = fe.translate(raw)
    assert 'File "' not in msg.what_broke
    assert "Traceback" not in msg.what_broke


def test_translate_enoent_returns_title(fe):
    """UX-02: translate('ENOENT: ...') returns a non-empty title and no traceback text."""
    msg = fe.translate("ENOENT: no such file or directory, open '/tmp/missing'")
    assert msg.title
    assert "Traceback" not in msg.what_broke
    # ENOENT should hit the enoent-generic dictionary entry.
    assert msg.title != "Something went wrong"


# ---------- UX-05: dictionary schema and contents ----------


def test_dictionary_has_30_entries(fe):
    """UX-05: load_dictionary() returns >= 30 entries."""
    entries = fe.load_dictionary()
    assert len(entries) >= 30


def test_dictionary_schema_all_9_fields(fe):
    """UX-05: each entry has all 9 documented fields.

    Fields: id, match_pattern, category, title, what_broke, what_to_do,
    copy_paste_command, phase_seen, expansion_note.
    """
    entries = fe.load_dictionary()
    required = {
        "id",
        "match_pattern",
        "category",
        "title",
        "what_broke",
        "what_to_do",
        "copy_paste_command",
        "phase_seen",
        "expansion_note",
    }
    for entry in entries:
        missing = required - set(entry.keys())
        assert not missing, f"Entry {entry.get('id')!r} missing fields: {missing}"


def test_dictionary_format_version_checked(fe, tmp_path):
    """UX-05: load_dictionary() raises SystemExit when format_version is wrong."""
    bad = tmp_path / "dictionary.yaml"
    bad.write_text(
        "- format_version: \"9.9\"\n"
        "  schema_fields:\n"
        "    - id\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        fe.load_dictionary(bad)


def test_dictionary_readme_exists():
    """UX-05: references/friendly-errors/README.md exists."""
    readme = REPO_ROOT / "references" / "friendly-errors" / "README.md"
    assert readme.exists(), f"README missing at {readme}"
    text = readme.read_text(encoding="utf-8")
    # Spot-check the 5 required H2 sections.
    for section in (
        "## Location and Format",
        "## Field Schema",
        "## How to Test",
        "## Inclusion Criteria",
        "## Format Version",
    ):
        assert section in text, f"README missing section: {section}"


# ---------- UX-02: import-guard wiring across the 5 known scripts ----------


_SCRIPTS = (
    "preflight_check.py",
    "scaffold_dispatch.py",
    "stack_researcher.py",
    "intake_handler.py",
    "gsd_driver.py",
)


def test_import_guard_in_all_five_scripts():
    """UX-02: all 5 scripts contain 'import friendly_error' guard."""
    scripts_dir = REPO_ROOT / "scripts"
    for name in _SCRIPTS:
        text = (scripts_dir / name).read_text(encoding="utf-8")
        assert "import friendly_error" in text, (
            f"{name} missing 'import friendly_error' guard"
        )


def test_error_paths_wrapped_in_known_sites():
    """UX-02: the 3 scripts with known error surfaces each contain at least one
    '_fe.translate' call site (the 'if _fe is not None:' pattern).

    stack_researcher.py and intake_handler.py are import-guard only — no known
    error surfaces in current Phase 4 codebase.
    """
    scripts_dir = REPO_ROOT / "scripts"
    for name in ("preflight_check.py", "scaffold_dispatch.py", "gsd_driver.py"):
        text = (scripts_dir / name).read_text(encoding="utf-8")
        assert "_fe.translate" in text, (
            f"{name} missing '_fe.translate' call site"
        )
        assert re.search(r"if\s+_fe\s+is\s+not\s+None", text), (
            f"{name} missing 'if _fe is not None' guard pattern"
        )
