"""test_gsd_driver.py — RED stubs for Phase 4 gsd_driver.py (Wave 0).

All tests skip until gsd_driver module is created in Wave 1.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def gd():
    """Lazy import of scripts/gsd_driver.py — skips when not yet created."""
    try:
        return importlib.import_module("gsd_driver")
    except ImportError:
        pytest.skip("gsd_driver module not yet created (Wave 1 target)")


# ROLE-01: initial state emits /gsd-new-project --auto
def test_initial_state_emits_gsd_new_project(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-new-project" in captured.out
    assert "--auto" in captured.out


# ROLE-02: current_phase=1, phase_step=0 emits /gsd-spec-phase
def test_phase_1_step_0_emits_spec_phase(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-spec-phase" in captured.out


# ROLE-03: current_phase=1, phase_step=1 emits /gsd-plan-phase
def test_phase_1_step_1_emits_plan_phase(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-plan-phase" in captured.out


# ROLE-04: phase_step=3 emits /gsd-execute-phase
def test_step_3_emits_execute_phase(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "3",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-execute-phase" in captured.out


# ROLE-05: phase_step=4 emits /code-tester
def test_step_4_emits_code_tester(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "4",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/code-tester" in captured.out


# ROLE-06: phase_step=5 emits /predator; phase_step=6 emits /gsd-code-review
def test_step_5_emits_predator(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "5",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/predator" in captured.out


def test_step_6_emits_gsd_code_review(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "6",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-code-review" in captured.out


# ROLE-08: retry_count=3 triggers escalation sequence (/gsd-debug then /problem-solver)
def test_escalation_at_retry_limit(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "retry_count", "--value", "3",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-debug" in captured.out or "/problem-solver" in captured.out


# HEAL-06: install command that gsd_driver constructs includes --ignore-scripts
def test_install_uses_ignore_scripts(gd):
    cmd = gd.build_install_cmd("next", ecosystem="npm")
    assert "--ignore-scripts" in cmd


# HEAL-07: resume reads retry_count from state.md, does not reset to 0
def test_resume_preserves_retry_count(gd, tmp_project_root, writer):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "retry_count", "--value", "2",
           project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    result = writer("read", "--field", "retry_count",
                    project_root=tmp_project_root, check=True, capture=True)
    assert result.stdout.strip() == "2"


# VER-01: VERIFICATION.md is written with 2-5 falsifiable criteria
def test_verification_md_written(gd, tmp_project_root, writer, tmp_path):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "7",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    ver_path = tmp_project_root / ".planning" / "osbuilder" / "VERIFICATION.md"
    assert ver_path.exists(), "VERIFICATION.md must be written at phase_step=7"


# VER-01: criteria must not contain "tests pass" (falsifiability rule)
def test_criteria_not_tests_pass(gd, tmp_project_root, writer):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "7",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    ver_path = tmp_project_root / ".planning" / "osbuilder" / "VERIFICATION.md"
    if ver_path.exists():
        content = ver_path.read_text()
        assert "tests pass" not in content.lower()


# VER-02: /gsd-verify-work emitted at phase_step=8
def test_verify_work_emitted(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "8",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-verify-work" in captured.out


# VER-03: /code-tester emitted per phase (phase_step=4)
def test_code_tester_emitted(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "4",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/code-tester" in captured.out


# VER-04: /predator emitted per phase (phase_step=5)
def test_predator_emitted(gd, tmp_project_root, writer, capsys):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "5",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/predator" in captured.out


# State machine: phase_step increments after each emission
def test_state_updates_after_emission(gd, tmp_project_root, writer):
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    result = writer("read", "--field", "phase_step",
                    project_root=tmp_project_root, check=True, capture=True)
    step = int(result.stdout.strip())
    assert step == 1, "phase_step must increment to 1 after first emission"
