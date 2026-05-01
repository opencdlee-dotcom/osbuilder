"""test_tutor_mode.py — RED stubs for Phase 5 tutor mode gating (Wave 0).

All tests skip until corresponding Wave 1 module is created.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_JARGON = ["framework", "endpoint", "responsive", "ORM",
                    "dependency injection", "transpiler"]


@pytest.fixture
def nrt():
    """Lazy import of scripts/narration.py — skips when not yet created."""
    try:
        return importlib.import_module("narration")
    except ImportError:
        pytest.skip("narration module not yet created (Wave 1 target)")


# ---------- UX-01: tutor-line emission gating ----------

def test_tutor_line_emitted_default(nrt, tmp_project_root, writer, capsys):
    """UX-01: in beginner+tutor mode, emit('pm','working','ok') yields a '> ' tutor line."""
    pytest.skip("Wave 1 target")


def test_quiet_suppresses_tutor(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor_enabled=false → emit all roles 'ok' yields zero '> ' lines."""
    pytest.skip("Wave 1 target")


def test_quiet_keeps_banners(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor_enabled=false still preserves role banner output (e.g., '[PM]')."""
    pytest.skip("Wave 1 target")


def test_no_jargon_in_banners(nrt, tmp_project_root, writer, capsys):
    """UX-01: emitting all 8 role banners in beginner mode yields no jargon tokens."""
    pytest.skip("Wave 1 target")


def test_eight_tutor_lines_for_eight_roles(nrt, tmp_project_root, writer, capsys):
    """UX-01: emit all 8 roles 'ok' in beginner mode → exactly 8 '> ' tutor lines."""
    pytest.skip("Wave 1 target")


def test_tutor_only_in_ok_status(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor lines appear only on status='ok' (not on 'start' or 'fail')."""
    pytest.skip("Wave 1 target")


def test_advanced_mode_no_tutor(nrt, tmp_project_root, writer, capsys):
    """UX-01: mode=advanced suppresses tutor lines even when tutor_enabled=true."""
    pytest.skip("Wave 1 target")


def test_tutor_prefix_is_gt_space(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor line starts with the exact two-character prefix '> '."""
    pytest.skip("Wave 1 target")
