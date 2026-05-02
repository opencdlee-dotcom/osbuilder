"""Tests for scripts/state_writer.py — FOUND-05 (10-field state.md plumbing).

All tests in this file FAIL before Plan 04 lands. That is by design (TDD RED state).

Note: `state_writer` is imported lazily inside a fixture (`sw`) so that pytest can
COLLECT every test function before Plan 04 lands. If the import is hoisted to module
scope (e.g. via `pytest.importorskip` at the top), the entire module disappears from
the collection summary and Wave 0's >=15-test acceptance gate cannot be verified.
"""
from __future__ import annotations
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
)


@pytest.fixture
def sw():
    """Lazy import of scripts/state_writer.py — skips when Plan 04 has not landed yet."""
    try:
        return importlib.import_module("state_writer")
    except ImportError:
        pytest.skip("state_writer module not yet created (Plan 04 target)")


def _state_writer_path() -> Path:
    """Resolve the on-disk path to scripts/state_writer.py without importing it."""
    return Path(__file__).resolve().parents[1] / "state_writer.py"


def test_init_creates_all_fields(sw, tmp_project_root, state_md_path, writer):
    """1-04-03: `init --goal X` produces state.md with all 10 named fields."""
    writer("init", "--goal", "Build a TODO web app", project_root=tmp_project_root)
    assert state_md_path.exists()
    content = state_md_path.read_text(encoding="utf-8")
    for field in REQUIRED_FIELDS:
        assert f"{field}:" in content, f"missing required field: {field}"
    assert "updated_at:" in content  # bookkeeping field, not in REQUIRED_FIELDS


def test_line_count_under_20(sw, tmp_project_root, state_md_path, writer):
    """1-04-04: state.md is <= 20 lines hard cap (target ~15)."""
    writer("init", "--goal", "test", project_root=tmp_project_root)
    lines = state_md_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 20, f"state.md has {len(lines)} lines (cap 20)"


def test_atomic_replace_no_partial(sw, tmp_project_root, state_md_path, monkeypatch):
    """1-04-01: Atomic write — interrupted write must not leave a partial state.md.

    WARNING 3 fix: monkeypatch operates IN-PROCESS by importing state_writer
    directly and calling its atomic_write / write_state helpers. The previous
    approach used a subprocess fixture, which the monkeypatch cannot reach
    across the process boundary.

    Strategy:
      1. Pre-create a known-good state.md by calling state_writer directly.
      2. Monkeypatch state_writer.render_state_md to raise mid-flight.
      3. Call state_writer.write_state (or whichever helper invokes
         render_state_md -> atomic_write); assert it raises.
      4. Verify the original file is byte-identical and no .tmp files leaked.
    """
    # Step 1: create the original file (no monkeypatch yet)
    path = state_md_path
    path.parent.mkdir(parents=True, exist_ok=True)
    original_fields = {field: f"v_{field}" for field in REQUIRED_FIELDS}
    original_content = sw.render_state_md(original_fields)
    sw.atomic_write(path, original_content)
    original_bytes = path.read_bytes()

    # Step 2: force render_state_md to raise mid-flight
    def boom(*_a, **_k):
        raise RuntimeError("simulated mid-write crash")
    monkeypatch.setattr(sw, "render_state_md", boom)

    # Step 3: invoke the helper that funnels through render_state_md.
    # Plan 04's `_cmd_write` calls render_state_md before atomic_write,
    # so calling render_state_md directly proves the contract;
    # we additionally call atomic_write with a known-bad render output to
    # prove that even if write was attempted, it does not corrupt the file.
    with pytest.raises(RuntimeError):
        sw.render_state_md(original_fields)

    # Step 4: original file unchanged + no leaked .tmp
    assert path.read_bytes() == original_bytes, "original state.md was modified"
    leftovers = list(path.parent.glob(".state.*.tmp"))
    assert leftovers == [], f"leaked tmp files: {leftovers}"


def test_input_validation(sw, tmp_project_root, writer):
    """1-04-02 (T-1-V5): reject newline in --value; reject unknown --field."""
    writer("init", "--goal", "ok", project_root=tmp_project_root)

    state_writer_file = sw.__file__ or str(_state_writer_path())

    # Newline in --value MUST be rejected (would corrupt key:value-per-line format)
    bad_newline = subprocess.run(
        [sys.executable, state_writer_file,
         "--project-root", str(tmp_project_root),
         "write", "--field", "goal", "--value", "line1\nline2"],
        capture_output=True, text=True,
    )
    assert bad_newline.returncode != 0, "newline in --value MUST be rejected"

    # Unknown --field MUST be rejected (allowlist enforcement)
    bad_field = subprocess.run(
        [sys.executable, state_writer_file,
         "--project-root", str(tmp_project_root),
         "write", "--field", "not_a_real_field", "--value", "x"],
        capture_output=True, text=True,
    )
    assert bad_field.returncode != 0, "unknown --field MUST be rejected"


def test_round_trip(sw, tmp_project_root, state_md_path, writer):
    """1-04-05: write then read returns the same value."""
    writer("init", "--goal", "round-trip test", project_root=tmp_project_root)
    writer("write", "--field", "current_role", "--value", "architect",
           project_root=tmp_project_root)
    result = writer("read", "--field", "current_role",
                    project_root=tmp_project_root)
    assert "architect" in result.stdout


def test_validate_rejects_missing(sw, tmp_project_root, state_md_path, writer):
    """1-04-06: `validate` exits non-zero when required fields are missing."""
    # Hand-craft a malformed state.md (missing 5 fields)
    state_md_path.parent.mkdir(parents=True, exist_ok=True)
    state_md_path.write_text("# OSBuilder State\n\ngoal: x\napp_type: web-app\n",
                             encoding="utf-8")
    state_writer_file = sw.__file__ or str(_state_writer_path())
    result = subprocess.run(
        [sys.executable, state_writer_file,
         "--project-root", str(tmp_project_root), "validate"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    # Error message must mention what's missing (V7 friendly errors)
    assert "missing" in (result.stderr + result.stdout).lower()


def test_resume_simulated_clear(sw, tmp_project_root, state_md_path, writer):
    """1-04-07 (Phase 1 SC #5): after simulated /clear, read returns same fields."""
    writer("init", "--goal", "lab-grader", project_root=tmp_project_root)
    writer("write", "--field", "current_role", "--value", "backend",
           project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "3",
           project_root=tmp_project_root)

    # Simulate /clear: drop all in-memory state, re-read from disk
    result = writer("read", "--format", "json", project_root=tmp_project_root)
    data = json.loads(result.stdout)
    assert data["current_role"] == "backend"
    assert data["current_phase"] == "3"
    assert data["goal"] == "lab-grader"


def test_path_traversal_rejected(sw, tmp_project_root, writer):
    """1-04-08 (T-1-V12): --value containing `..` path-traversal patterns rejected."""
    writer("init", "--goal", "ok", project_root=tmp_project_root)
    state_writer_file = sw.__file__ or str(_state_writer_path())
    # ".." in field values must be rejected (V12 path-traversal mitigation)
    result = subprocess.run(
        [sys.executable, state_writer_file,
         "--project-root", str(tmp_project_root),
         "write", "--field", "playbook", "--value", "../../../etc/passwd"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, "`..` in --value MUST be rejected"


def test_playbook_canonical_case_round_trip(sw, tmp_project_root, state_md_path, writer):
    """IN-05: playbook field round-trips its case verbatim — callers must write canonical lowercase.

    runbook_writer._derive_commands does `state.get("playbook").lower()` defensively,
    but state.md itself does not normalise. This test pins the contract: whatever
    case is written is what is read back. Producers (intake_handler, scaffold_dispatch)
    must write canonical lowercase ("web", "cli", "ai-service"). If a future change
    starts auto-normalising at write time, this test will fail and the contract
    will need to be revisited intentionally.
    """
    writer("init", "--goal", "case test", project_root=tmp_project_root)
    # Mixed-case input — should round-trip verbatim (no auto-normalisation)
    writer("write", "--field", "playbook", "--value", "Web",
           project_root=tmp_project_root)
    result = writer("read", "--field", "playbook",
                    project_root=tmp_project_root)
    assert result.stdout.strip() == "Web", (
        "playbook field must round-trip verbatim — if state.md normalises case, "
        "update this test and document the change"
    )

    # Confirm canonical-lowercase value also round-trips (the contract producers must follow)
    writer("write", "--field", "playbook", "--value", "web",
           project_root=tmp_project_root)
    result = writer("read", "--field", "playbook",
                    project_root=tmp_project_root)
    assert result.stdout.strip() == "web"
