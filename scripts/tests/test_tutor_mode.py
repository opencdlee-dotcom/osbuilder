"""test_tutor_mode.py — Phase 5 tutor mode gating GREEN tests.

Verifies emit() respects mode + tutor_enabled state for the '> ' tutor lines.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_JARGON = ["framework", "endpoint", "responsive", "ORM",
                    "dependency injection", "transpiler"]

ALL_ROLES = ["pm", "architect", "frontend", "backend",
             "devops", "qa", "reviewer", "tech-writer"]


@pytest.fixture
def nrt():
    """Lazy import of scripts/narration.py — skips when not yet created."""
    try:
        return importlib.import_module("narration")
    except ImportError:
        pytest.skip("narration module not yet created (Wave 1 target)")


def _set_state(writer, project_root, mode, tutor_enabled):
    writer("init", project_root=project_root)
    writer("write", "--field", "mode", "--value", mode,
           project_root=project_root)
    writer("write", "--field", "tutor_enabled", "--value", tutor_enabled,
           project_root=project_root)


# ---------- UX-01: tutor-line emission gating ----------

def test_tutor_line_emitted_default(nrt, tmp_project_root, writer, capsys):
    """UX-01: in beginner+tutor mode, emit('pm','working','ok') yields a '> ' tutor line."""
    _set_state(writer, tmp_project_root, "beginner", "true")
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) >= 1, (
        f"expected tutor line, got: {captured!r}"
    )


def test_quiet_suppresses_tutor(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor_enabled=false → emit all roles 'ok' yields zero '> ' lines."""
    _set_state(writer, tmp_project_root, "beginner", "false")
    nrt._refresh_state(tmp_project_root)
    for role in ALL_ROLES:
        nrt.emit(role, "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) == 0, (
        f"expected no tutor lines, got: {tutor_lines}"
    )


def test_quiet_keeps_banners(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor_enabled=false still preserves role banner output (e.g., '[PM]')."""
    _set_state(writer, tmp_project_root, "beginner", "false")
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    assert "[PM]" in captured


def test_no_jargon_in_banners(nrt, tmp_project_root, writer, capsys):
    """UX-01: emitting all 8 role banners in beginner mode yields no jargon tokens."""
    _set_state(writer, tmp_project_root, "beginner", "true")
    nrt._refresh_state(tmp_project_root)
    for role in ALL_ROLES:
        nrt.emit(role, "working", "ok")
    captured = capsys.readouterr().out
    for token in FORBIDDEN_JARGON:
        assert token not in captured, (
            f"jargon token {token!r} appeared in default-mode output: {captured!r}"
        )


def test_eight_tutor_lines_for_eight_roles(nrt, tmp_project_root, writer, capsys):
    """UX-01: emit all 8 roles 'ok' in beginner mode → exactly 8 '> ' tutor lines."""
    _set_state(writer, tmp_project_root, "beginner", "true")
    nrt._refresh_state(tmp_project_root)
    for role in ALL_ROLES:
        nrt.emit(role, "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) == 8, (
        f"expected 8 tutor lines, got {len(tutor_lines)}: {tutor_lines}"
    )


def test_tutor_only_in_ok_status(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor lines appear only on status='ok' (not on 'start' or 'fail')."""
    _set_state(writer, tmp_project_root, "beginner", "true")
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "working", "start")
    out_start = capsys.readouterr().out
    assert not any(ln.startswith("> ") for ln in out_start.splitlines()), (
        f"'start' should not produce tutor lines: {out_start!r}"
    )

    nrt.emit("pm", "working", "fail", detail="x")
    out_fail = capsys.readouterr().out
    assert not any(ln.startswith("> ") for ln in out_fail.splitlines()), (
        f"'fail' should not produce tutor lines: {out_fail!r}"
    )


def test_advanced_mode_no_tutor(nrt, tmp_project_root, writer, capsys):
    """UX-01: mode=advanced suppresses tutor lines even when tutor_enabled=true."""
    _set_state(writer, tmp_project_root, "advanced", "true")
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) == 0, (
        f"advanced mode should suppress tutor lines: {tutor_lines}"
    )


def test_tutor_prefix_is_gt_space(nrt, tmp_project_root, writer, capsys):
    """UX-01: tutor line starts with the exact two-character prefix '> '."""
    _set_state(writer, tmp_project_root, "beginner", "true")
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) >= 1
    for ln in tutor_lines:
        assert ln[:2] == "> ", f"tutor line prefix should be '> ', got: {ln[:5]!r}"
