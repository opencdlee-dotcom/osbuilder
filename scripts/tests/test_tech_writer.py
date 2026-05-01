"""test_tech_writer.py — Phase 5 Plan 05-05 GREEN tests for ROLE-07 tech-writer step.

Verifies the in-line phase_step=9 handler in scripts/gsd_driver.py:
  - sub_step="" → emits /gsd-docs-update with @-reference to readme-context.md
  - sub_step="awaiting-humanizer" + humanizer present → emits /humanizer @README.md
  - sub_step="awaiting-humanizer" + humanizer absent → writes humanizer_score=skipped
    and advances phase_step to 10 (graceful fallback)
  - phase_step=10 advances current_phase and resets phase_step
  - state_writer accepts humanizer_score writes
  - readme-context.md requires '## How OSBuilder built this' section + 8 role names
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def gd():
    """Lazy import of scripts/gsd_driver.py — skips when not yet available."""
    try:
        return importlib.import_module("gsd_driver")
    except ImportError:
        pytest.skip("gsd_driver module not yet available (Wave 1 target)")


# ---------- ROLE-07: tech-writer step emits /gsd-docs-update ----------

def test_tech_writer_step_emits_gsd_docs_update(gd, tmp_project_root, writer, capsys):
    """ROLE-07: emit_next_command at phase_step=9, sub_step="" prints /gsd-docs-update.

    Behavior test — does NOT check PHASE_STEP_COMMANDS dict key. Key 9 is removed
    from PHASE_STEP_COMMANDS and the step is handled in-line by _run_tech_writer_step.
    """
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "9",
           project_root=tmp_project_root)
    rc = gd.emit_next_command(tmp_project_root)
    captured = capsys.readouterr()
    assert rc == 0
    assert "/gsd-docs-update" in captured.out, (
        f"Expected '/gsd-docs-update' in stdout, got: {captured.out!r}"
    )


def test_phase_step_commands_includes_tech_writer(gd):
    """ROLE-07: key 9 is REMOVED from PHASE_STEP_COMMANDS — step 9 is in-line.

    The dict-removal contract: emit_next_command's in-line block at phase_step==9
    intercepts before the generic dict lookup. Test asserts the key is absent so
    that any future regression that puts a slash command back into the dict at
    key 9 (which would short-circuit the sub-state machine) fails immediately.
    """
    assert 9 not in gd.PHASE_STEP_COMMANDS, (
        "key 9 must be removed from PHASE_STEP_COMMANDS — step 9 is handled in-line"
    )


# ---------- ROLE-07: phase advance shifted to step 10 ----------

def test_phase_step_10_advances_phase(gd, tmp_project_root, writer):
    """ROLE-07: emit_next_command at phase_step=10 increments current_phase, resets phase_step."""
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "2",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "10",
           project_root=tmp_project_root)
    rc = gd.emit_next_command(tmp_project_root)
    assert rc == 0
    cp = writer("read", "--field", "current_phase",
                project_root=tmp_project_root, capture=True).stdout.strip()
    ps = writer("read", "--field", "phase_step",
                project_root=tmp_project_root, capture=True).stdout.strip()
    assert cp == "3", f"current_phase should advance from 2 → 3, got {cp!r}"
    assert ps == "0", f"phase_step should reset to 0, got {ps!r}"


# ---------- ROLE-07: humanizer_score state field ----------

def test_humanizer_score_field_allowed(writer, tmp_project_root):
    """ROLE-07: state_writer.py accepts writes for the 'humanizer_score' field."""
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    result = writer("write", "--field", "humanizer_score", "--value", "0",
                    project_root=tmp_project_root, check=False, capture=True)
    assert result.returncode == 0, (
        f"state_writer must accept humanizer_score; stderr: {result.stderr!r}"
    )
    val = writer("read", "--field", "humanizer_score",
                 project_root=tmp_project_root, capture=True).stdout.strip()
    assert val == "0"


def test_humanizer_missing_fallback(gd, tmp_project_root, writer, monkeypatch):
    """ROLE-07: humanizer absent → score=skipped, phase advances to 10 (no crash)."""
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "9",
           project_root=tmp_project_root)
    # First call: sub_step="" — emits /gsd-docs-update, sets sub_step=awaiting-humanizer
    gd.emit_next_command(tmp_project_root)
    sub = writer("read", "--field", "tech_writer_sub_step",
                 project_root=tmp_project_root, capture=True).stdout.strip()
    assert sub == "awaiting-humanizer", (
        f"After first emit_next_command, sub_step should be 'awaiting-humanizer', got {sub!r}"
    )
    # Second call: sub_step=awaiting-humanizer, humanizer absent → score=skipped, advance
    monkeypatch.setattr(gd, "_humanizer_present", lambda: False)
    rc = gd.emit_next_command(tmp_project_root)
    assert rc == 0
    score = writer("read", "--field", "humanizer_score",
                   project_root=tmp_project_root, capture=True).stdout.strip()
    assert score == "skipped", f"Expected humanizer_score=skipped, got {score!r}"
    ps = writer("read", "--field", "phase_step",
                project_root=tmp_project_root, capture=True).stdout.strip()
    assert ps == "10", f"phase_step should advance to 10, got {ps!r}"


# ---------- ROLE-07: README dev-team section ----------

def test_readme_has_dev_team_section(gd, tmp_project_root, writer):
    """ROLE-07 AC#14: readme-context.md (passed to /gsd-docs-update) requires
    '## How OSBuilder built this' section AND all 8 role names.

    The context file is what the slash command reads; it must be specific enough
    that a downstream /gsd-docs-update implementation will produce the section.
    """
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "9",
           project_root=tmp_project_root)
    gd.emit_next_command(tmp_project_root)
    ctx_path = tmp_project_root / ".planning" / "osbuilder" / "readme-context.md"
    assert ctx_path.exists(), f"readme-context.md must be written at {ctx_path}"
    text = ctx_path.read_text(encoding="utf-8")
    assert "## How OSBuilder built this" in text, (
        "readme-context.md must require '## How OSBuilder built this' section"
    )
    for role in ("PM", "Architect", "Frontend", "Backend",
                 "DevOps", "QA", "Reviewer", "Tech Writer"):
        assert role in text, f"readme-context.md must name role: {role}"
