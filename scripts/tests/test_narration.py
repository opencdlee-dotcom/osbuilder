"""test_narration.py — Phase 5 narration GREEN tests.

Tests narration.emit(), capture_subprocess(), brief loading, and gsd_driver
integration. The fixture lazily imports the narration module so collection
remains visible even before the module is created.
"""
from __future__ import annotations

import importlib
import re
import sys
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


@pytest.fixture
def nrt_beginner(nrt, tmp_project_root, writer):
    """narration with mode=beginner + tutor_enabled=true (default)."""
    writer("init", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    writer("write", "--field", "tutor_enabled", "--value", "true",
           project_root=tmp_project_root)
    nrt._refresh_state(tmp_project_root)
    return nrt


@pytest.fixture
def nrt_quiet(nrt, tmp_project_root, writer):
    """narration with mode=beginner + tutor_enabled=false."""
    writer("init", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    writer("write", "--field", "tutor_enabled", "--value", "false",
           project_root=tmp_project_root)
    nrt._refresh_state(tmp_project_root)
    return nrt


# ---------- ROLE-09 / UX-04: role-brief inventory and structure ----------

def test_eight_role_briefs_exist(nrt):
    """UX-04: find references/roles -name '*.md' must produce 8 briefs."""
    briefs = list((REPO_ROOT / "references" / "roles").glob("*.md"))
    assert len(briefs) == 8, f"expected 8 briefs, got {len(briefs)}: {briefs}"


def test_brief_has_required_sections(nrt):
    """UX-04: each brief contains the 4 required H2 sections."""
    required = ["## Banner Templates", "## Tutor Template",
                "## Per-Step Copy", "## Failure Copy"]
    for brief in (REPO_ROOT / "references" / "roles").glob("*.md"):
        text = brief.read_text(encoding="utf-8")
        for section in required:
            assert section in text, (
                f"{brief.name} missing section: {section!r}"
            )


def test_role_brief_loaded_at_import(nrt):
    """ROLE-09: _ROLE_BRIEFS dict is non-empty after module import."""
    assert isinstance(nrt._ROLE_BRIEFS, dict)
    assert len(nrt._ROLE_BRIEFS) >= 1
    # At least pm and qa should be loaded
    for role in ("pm", "qa"):
        assert role in nrt._ROLE_BRIEFS, f"role {role!r} missing from _ROLE_BRIEFS"


# ---------- ROLE-09: emit() core behavior ----------

def test_emit_start_ok_fail_statuses(nrt, capsys):
    """ROLE-09: emit(role, action, status) produces a banner line for each status."""
    nrt.emit("pm", "working", "start")
    out_start = capsys.readouterr().out
    assert "[PM]" in out_start
    assert "..." in out_start

    nrt.emit("pm", "working", "ok")
    out_ok = capsys.readouterr().out
    assert "[PM]" in out_ok
    assert ("[OK]" in out_ok) or ("✓" in out_ok)

    nrt.emit("pm", "working", "fail", detail="reason")
    out_fail = capsys.readouterr().out
    assert "[PM]" in out_fail
    assert ("[FAIL]" in out_fail) or ("✗" in out_fail)


def test_emit_graceful_without_brief(nrt, capsys):
    """ROLE-09: emit('unknown-role', ...) renders generic banner without raising."""
    nrt.emit("unknown-role", "foo", "ok")
    out = capsys.readouterr().out
    assert "[UNKNOWN-ROLE]" in out


def test_forbidden_jargon_not_in_banners(nrt_beginner, capsys):
    """UX-04: emitting all 8 role banners ('ok' status) yields no jargon tokens."""
    for role in ALL_ROLES:
        nrt_beginner.emit(role, "working", "ok")
    captured = capsys.readouterr().out
    for token in FORBIDDEN_JARGON:
        assert token not in captured, (
            f"jargon token {token!r} appeared in banners: {captured!r}"
        )


def test_eight_banners_in_e2e(nrt_beginner, capsys):
    """ROLE-09: end-to-end emit of all 8 roles produces 8 distinct banner lines."""
    for role in ALL_ROLES:
        nrt_beginner.emit(role, "working", "ok")
    captured = capsys.readouterr().out
    banner_pat = re.compile(
        r"^\[(PM|ARCHITECT|FRONTEND|BACKEND|DEVOPS|QA|REVIEWER|TECH-WRITER)\]"
    )
    matched = [ln for ln in captured.splitlines() if banner_pat.match(ln)]
    assert len(matched) == 8, (
        f"expected 8 banner lines, got {len(matched)}: {matched}"
    )


# ---------- ROLE-09 / UX-04: tutor-mode lines (gating tested in test_tutor_mode.py) ----------

def test_tutor_line_has_gt_prefix(nrt_beginner, capsys):
    """UX-04: in beginner+tutor mode, status='ok' emits a '> ' prefixed line."""
    nrt_beginner.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) >= 1, (
        f"expected at least one tutor line, got: {captured!r}"
    )


def test_quiet_mode_no_tutor_lines(nrt_quiet, capsys):
    """UX-04: tutor_enabled=false suppresses all '> ' prefixed tutor lines."""
    nrt_quiet.emit("pm", "working", "ok")
    captured = capsys.readouterr().out
    tutor_lines = [ln for ln in captured.splitlines() if ln.startswith("> ")]
    assert len(tutor_lines) == 0, (
        f"expected no tutor lines, got: {tutor_lines}"
    )
    # banner still present
    assert "[PM]" in captured


# ---------- ROLE-09: subprocess capture routing ----------

def test_capture_subprocess_routes_raw_to_log(nrt, tmp_path, capsys):
    """ROLE-09: raw stdout from a child process is logged but not surfaced to user."""
    log_path = tmp_path / "build.log"
    rc, out_lines, err_lines = nrt.capture_subprocess(
        [sys.executable, "-c", "print('hello')"],
        role="devops", action="echo-test", log_path=log_path,
    )
    captured = capsys.readouterr().out
    assert "hello" not in captured
    assert "hello" in log_path.read_text(encoding="utf-8")
    assert rc == 0
    assert any("hello" in ln for ln in out_lines)


def test_raw_stderr_to_log(nrt, tmp_path, capsys):
    """ROLE-09: raw stderr from a child process is logged but not surfaced to user.

    The stderr payload string is intentionally unique ("STDERR-PAYLOAD") so we can
    distinguish it from the banner action label, which also appears in stdout.
    """
    log_path = tmp_path / "build.log"
    rc, _, err_lines = nrt.capture_subprocess(
        [sys.executable, "-c",
         "import sys; sys.stderr.write('STDERR-PAYLOAD')"],
        role="devops", action="check", log_path=log_path,
    )
    captured = capsys.readouterr().out
    assert "STDERR-PAYLOAD" not in captured
    assert "STDERR-PAYLOAD" in log_path.read_text(encoding="utf-8")


def test_no_python_tracebacks_in_user_output(nrt, tmp_path, capsys):
    """ROLE-09: capture_subprocess never surfaces 'Traceback' text to stdout."""
    log_path = tmp_path / "build.log"
    nrt.capture_subprocess(
        [sys.executable, "-c", "raise RuntimeError('x')"],
        role="devops", action="raise", log_path=log_path,
    )
    captured = capsys.readouterr().out
    assert "Traceback" not in captured


def test_no_node_stack_frames(nrt, tmp_path, capsys):
    """ROLE-09: Node stack-frame lines never appear in captured user stdout."""
    log_path = tmp_path / "build.log"
    nrt.capture_subprocess(
        [sys.executable, "-c",
         "import sys; sys.stderr.write('    at fn (file.js:1:1)\\n')"],
        role="devops", action="node-stack", log_path=log_path,
    )
    captured = capsys.readouterr().out
    assert "at fn (file.js" not in captured


def test_build_log_created_on_first_capture(nrt, tmp_path):
    """ROLE-09: build.log path is created on the first capture_subprocess call."""
    log_path = tmp_path / "build.log"
    assert not log_path.exists()
    nrt.capture_subprocess(
        [sys.executable, "-c", "print('hi')"],
        role="devops", action="hi", log_path=log_path,
    )
    assert log_path.exists()


# ---------- ROLE-09 integration with gsd_driver ----------

def test_emit_at_every_dispatch(nrt, tmp_project_root, writer, capsys):
    """ROLE-09: emit_next_command in gsd_driver produces at least one narration emit."""
    import gsd_driver as gd
    writer("init", project_root=tmp_project_root)
    # Set current_phase=1 to bypass step-0 special case and exercise PHASE_STEP_COMMANDS dispatch
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "0",
           project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    writer("write", "--field", "tutor_enabled", "--value", "true",
           project_root=tmp_project_root)

    # Refresh narration state so it picks up the writer-set fields.
    nrt._refresh_state(tmp_project_root)
    gd.emit_next_command(tmp_project_root)
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    # At minimum, emit_next_command must produce a banner line. Output may go to
    # stdout (slash command + banner) or stderr (banner-only sites).
    assert re.search(r"\[(PM|ARCHITECT|FRONTEND|BACKEND|DEVOPS|QA|REVIEWER|TECH-WRITER)\]",
                     combined), (
        f"expected at least one role banner in driver output, got: {combined!r}"
    )


# ---------- Build-log rotation (Open Question 6) ----------

def test_build_log_truncated_on_new_build(nrt, tmp_path):
    """ROLE-09: _init_build_log truncates the log so it does not grow across builds."""
    log_path = tmp_path / "build.log"
    nrt._init_build_log(log_path)
    log_path.write_text("first build content\n", encoding="utf-8")
    assert log_path.read_text(encoding="utf-8") == "first build content\n"
    nrt._init_build_log(log_path)
    content = log_path.read_text(encoding="utf-8")
    assert "first build content" not in content, (
        f"build.log not truncated on second init: {content!r}"
    )
    assert content == ""
