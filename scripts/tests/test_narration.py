"""test_narration.py — RED stubs for Phase 5 narration (Wave 0).

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


# ---------- ROLE-09 / UX-04: role-brief inventory and structure ----------

def test_eight_role_briefs_exist(nrt):
    """UX-04: find references/roles -name '*.md' must produce 8 briefs."""
    pytest.skip("Wave 1 target")


def test_brief_has_required_sections(nrt):
    """UX-04: each brief contains the 4 required H2 sections."""
    pytest.skip("Wave 1 target")


def test_role_brief_loaded_at_import(nrt):
    """ROLE-09: _ROLE_BRIEFS dict is non-empty after module import."""
    pytest.skip("Wave 1 target")


# ---------- ROLE-09: emit() core behavior ----------

def test_emit_start_ok_fail_statuses(nrt, capsys):
    """ROLE-09: emit(role, action, status) produces a banner line for each status."""
    pytest.skip("Wave 1 target")


def test_emit_graceful_without_brief(nrt, capsys):
    """ROLE-09: emit('unknown-role', ...) renders generic banner without raising."""
    pytest.skip("Wave 1 target")


def test_forbidden_jargon_not_in_banners(nrt, capsys):
    """UX-04: emitting all 8 role banners ('ok' status) yields no jargon tokens."""
    pytest.skip("Wave 1 target")


def test_eight_banners_in_e2e(nrt, capsys):
    """ROLE-09: end-to-end emit of all 8 roles produces 8 distinct banner lines."""
    pytest.skip("Wave 1 target")


# ---------- ROLE-09 / UX-04: tutor-mode lines (gating tested in test_tutor_mode.py) ----------

def test_tutor_line_has_gt_prefix(nrt, tmp_project_root, writer, capsys):
    """UX-04: in beginner+tutor mode, status='ok' emits a '> ' prefixed line."""
    pytest.skip("Wave 1 target")


def test_quiet_mode_no_tutor_lines(nrt, tmp_project_root, writer, capsys):
    """UX-04: tutor_enabled=false suppresses all '> ' prefixed tutor lines."""
    pytest.skip("Wave 1 target")


# ---------- ROLE-09: subprocess capture routing ----------

def test_capture_subprocess_routes_raw_to_log(nrt, tmp_path, capsys):
    """ROLE-09: raw stdout from a child process is logged but not surfaced to user."""
    pytest.skip("Wave 1 target")


def test_raw_stderr_to_log(nrt, tmp_path, capsys):
    """ROLE-09: raw stderr from a child process is logged but not surfaced to user."""
    pytest.skip("Wave 1 target")


def test_no_python_tracebacks_in_user_output(nrt, tmp_path, capsys):
    """ROLE-09: capture_subprocess never surfaces 'Traceback' text to stdout."""
    pytest.skip("Wave 1 target")


def test_no_node_stack_frames(nrt, tmp_path, capsys):
    """ROLE-09: Node stack-frame lines never appear in captured user stdout."""
    pytest.skip("Wave 1 target")


def test_build_log_created_on_first_capture(nrt, tmp_path):
    """ROLE-09: build.log path is created on the first capture_subprocess call."""
    pytest.skip("Wave 1 target")


# ---------- ROLE-09 integration with gsd_driver ----------

def test_emit_at_every_dispatch(nrt, tmp_project_root, writer, monkeypatch, capsys):
    """ROLE-09: emit_next_command in gsd_driver produces at least one narration emit."""
    pytest.skip("Wave 1 target")
