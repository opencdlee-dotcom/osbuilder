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


# HEAL-05: step 2 invokes registry_verify.py when stack_choices has pkg + ecosystem
def test_step_2_calls_registry_verify(gd, tmp_project_root, writer, monkeypatch):
    import subprocess as _real_subprocess
    # Capture the real run BEFORE monkeypatching so state_writer subprocess
    # calls (issued from inside selective_run) don't re-enter selective_run.
    _real_run = _real_subprocess.run

    calls = []

    def selective_run(cmd, *args, **kwargs):
        sig = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "registry_verify" in sig:
            calls.append(list(cmd))
            return _real_subprocess.CompletedProcess(cmd, 0, "", "")
        return _real_run(cmd, *args, **kwargs)

    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "2",
           project_root=tmp_project_root)
    writer("write", "--field", "stack_choices",
           "--value", '{"pkg": "next", "ecosystem": "npm"}',
           project_root=tmp_project_root)

    monkeypatch.setattr(gd.subprocess, "run", selective_run)
    result = gd.emit_next_command(project_root=tmp_project_root)

    assert result == 0
    assert any("registry_verify" in str(c) for call in calls for c in call), \
        "registry_verify.py was not invoked at phase_step=2"
    assert any(c == "--pkg" for call in calls for c in call), \
        "--pkg flag missing from registry_verify call"
    assert any(c == "next" for call in calls for c in call), \
        "package name 'next' not passed to registry_verify"
    assert any(c == "--ecosystem" for call in calls for c in call), \
        "--ecosystem flag missing from registry_verify call"
    assert any(c == "npm" for call in calls for c in call), \
        "ecosystem 'npm' not passed to registry_verify"


# HEAL-05: step 2 blocks when registry_verify exits 1 (hallucinated package)
def test_step_2_blocks_on_registry_failure(gd, tmp_project_root, writer, monkeypatch):
    import subprocess as _real_subprocess
    _real_run = _real_subprocess.run

    def selective_run(cmd, *args, **kwargs):
        sig = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "registry_verify" in sig:
            return _real_subprocess.CompletedProcess(cmd, 1, "", "not found")
        return _real_run(cmd, *args, **kwargs)

    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "2",
           project_root=tmp_project_root)
    writer("write", "--field", "stack_choices",
           "--value", '{"pkg": "fake-hallucinated-pkg", "ecosystem": "npm"}',
           project_root=tmp_project_root)

    monkeypatch.setattr(gd.subprocess, "run", selective_run)
    result = gd.emit_next_command(project_root=tmp_project_root)

    assert result == 1, "emit_next_command must return 1 when registry check fails"

    # phase_step must NOT have advanced
    step_result = writer("read", "--field", "phase_step",
                         project_root=tmp_project_root, check=True, capture=True)
    assert step_result.stdout.strip() == "2", \
        "phase_step must remain at 2 when registry gate blocks"

    # last_failure must be written
    lf_result = writer("read", "--field", "last_failure",
                       project_root=tmp_project_root, check=True, capture=True)
    assert lf_result.stdout.strip() != "", \
        "last_failure must be written when registry gate blocks"


# HEAL-05: step 2 advances normally when stack_choices is absent (gate deferred)
def test_step_2_skips_gate_without_stack_choices(gd, tmp_project_root, writer, monkeypatch):
    import subprocess as _real_subprocess
    _real_run = _real_subprocess.run

    calls = []

    def selective_run(cmd, *args, **kwargs):
        sig = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "registry_verify" in sig:
            calls.append(list(cmd))
            return _real_subprocess.CompletedProcess(cmd, 0, "", "")
        return _real_run(cmd, *args, **kwargs)

    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "2",
           project_root=tmp_project_root)
    # Intentionally do NOT write stack_choices

    monkeypatch.setattr(gd.subprocess, "run", selective_run)
    result = gd.emit_next_command(project_root=tmp_project_root)

    assert result == 0, "emit_next_command must return 0 when stack_choices absent"
    assert calls == [], "registry_verify must NOT be called when stack_choices absent"

    # phase_step must have advanced to 3
    step_result = writer("read", "--field", "phase_step",
                         project_root=tmp_project_root, check=True, capture=True)
    assert step_result.stdout.strip() == "3", \
        "phase_step must advance to 3 when gate is skipped"
