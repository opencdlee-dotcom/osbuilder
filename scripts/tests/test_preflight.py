"""Tests for scripts/preflight_check.py — PRE-01..05 + PRE-07.

All tests in this file FAIL or SKIP before Plans 02-02 / 02-03 / 02-04 land.
That is by design (TDD RED state, mirrors Phase 1 Wave 0 contract).

Note: `preflight_check` is imported lazily inside the `pf` fixture so pytest
can COLLECT every test function before Plan 02-02 lands. Hoisting the import
to module scope (e.g. via importorskip) makes the entire module disappear
from --collect-only and breaks the >= 14 stubs Wave 0 gate.
"""
from __future__ import annotations
import importlib
import json
import pytest


@pytest.fixture
def pf():
    """Lazy import of scripts/preflight_check.py — skips when Plan 02-02 has not landed yet."""
    try:
        return importlib.import_module("preflight_check")
    except ImportError:
        pytest.skip("preflight_check module not yet created (Plan 02-02 target)")


def test_detect_missing_tools_macos(pf, fake_shell, fake_which, monkeypatch):
    """PRE-01: detect() returns 5 missing tools on a fresh macOS fixture."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    # node, python3, git, gh, docker all missing → fake_which returns None
    statuses = pf.detect(no_docker=False)
    missing = [t for t, s in statuses.items() if not s.detected]
    assert set(missing) >= {"node", "python3", "git", "gh", "docker"}


def test_detect_node_below_required(pf, fake_shell, fake_which, monkeypatch):
    """PRE-01: detect() reports node version_ok=False when Node < 20."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["node"] = "/usr/local/bin/node"
    fake_shell.program("node --version", stdout="v18.20.4\n")
    statuses = pf.detect(no_docker=False)
    node_status = statuses.get("node")
    assert node_status is not None, "node must appear in detect() output"
    assert not node_status.version_ok, "Node 18 should fail version_ok (requires >= 20)"


def test_vm_detected_blocks_install(pf, fake_shell, fake_which, monkeypatch):
    """PRE-01: When nvm is present, plan().blocked_by_vm includes 'node' and no node install action."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["nvm"] = "/Users/x/.nvm/nvm.sh"
    plan = pf.plan()
    assert "node" in plan.blocked_by_vm, "nvm should block node install"
    node_actions = [a for a in plan.actions if getattr(a, "tool", None) == "node"]
    assert len(node_actions) == 0, "plan must NOT contain a node install action when nvm is detected"


def test_detect_linux_distro_ubuntu(pf, fake_shell, fake_which, monkeypatch):
    """PRE-01: On Linux+Ubuntu, plan().os starts with 'linux-debian'."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.freedesktop_os_release", lambda: {"ID": "ubuntu", "ID_LIKE": "debian"})
    plan = pf.plan()
    assert plan.os.startswith("linux-debian"), f"Expected linux-debian prefix, got: {plan.os!r}"


def test_single_confirmation_for_batch(pf, fake_shell, fake_which, monkeypatch):
    """PRE-02: Exactly one input() call covers a 5-tool batch (not 5 individual prompts).

    Asserts len(prompts) == 1 — NOT '<= 1'. This falsifies both 'zero prompts'
    (batch silently skips confirmation) AND 'five prompts' (one-per-tool behavior).
    """
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    # All 5 tools missing → batch of 5
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    prompts = []
    monkeypatch.setattr("builtins.input", lambda *a, **kw: prompts.append(a) or "y")
    plan = pf.plan(no_docker=False)
    pf.apply(plan)
    assert len(prompts) == 1, (
        f"Expected exactly 1 confirmation prompt for a 5-tool batch; got {len(prompts)}"
    )


def test_macos_uses_brew(pf, fake_shell, fake_which, monkeypatch):
    """PRE-03: On Darwin with no VMs, missing node → install_command starts with 'brew install'."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    # node missing
    plan = pf.plan()
    node_actions = [a for a in plan.actions if getattr(a, "tool", None) == "node"]
    assert len(node_actions) >= 1, "Expected a node install action on macOS"
    assert node_actions[0].install_command.startswith("brew install"), (
        f"Expected brew install; got: {node_actions[0].install_command!r}"
    )


def test_linux_debian_uses_apt(pf, fake_shell, fake_which, monkeypatch):
    """PRE-03: On Linux+Ubuntu, git install_command contains 'apt-get install'."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.freedesktop_os_release", lambda: {"ID": "ubuntu", "ID_LIKE": "debian"})
    plan = pf.plan()
    git_actions = [a for a in plan.actions if getattr(a, "tool", None) == "git"]
    assert len(git_actions) >= 1, "Expected a git install action on Linux/Ubuntu"
    assert "apt-get install" in git_actions[0].install_command, (
        f"Expected apt-get install; got: {git_actions[0].install_command!r}"
    )


def test_linux_fedora_uses_dnf(pf, fake_shell, fake_which, monkeypatch):
    """PRE-03: On Linux+Fedora, git install_command contains 'dnf install'."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.freedesktop_os_release", lambda: {"ID": "fedora", "ID_LIKE": "rhel"})
    plan = pf.plan()
    git_actions = [a for a in plan.actions if getattr(a, "tool", None) == "git"]
    assert len(git_actions) >= 1, "Expected a git install action on Linux/Fedora"
    assert "dnf install" in git_actions[0].install_command, (
        f"Expected dnf install; got: {git_actions[0].install_command!r}"
    )


def test_windows_uses_winget(pf, fake_shell, fake_which, monkeypatch):
    """PRE-03: On Windows, first install action starts with 'winget install'."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    plan = pf.plan()
    assert len(plan.actions) >= 1, "Expected at least one install action on Windows"
    assert plan.actions[0].install_command.startswith("winget install"), (
        f"Expected winget install; got: {plan.actions[0].install_command!r}"
    )


def test_failure_triggers_rollback(pf, fake_shell, fake_which, monkeypatch):
    """PRE-04: A failed install triggers rollback of successfully-installed earlier tools.

    Program: brew install gh → success, brew install docker → failure.
    Assert fake_shell.calls contains 'brew uninstall gh' (rollback of prior success).
    """
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    fake_shell.program("brew install gh", returncode=0)
    fake_shell.program("brew install docker", returncode=1)
    plan = pf.plan(no_docker=False)
    pf.apply(plan)
    signatures = [
        c[0] if isinstance(c[0], str) else " ".join(c[0])
        for c in fake_shell.calls
    ]
    rollback_calls = [s for s in signatures if "brew uninstall gh" in s]
    assert len(rollback_calls) >= 1, (
        f"Expected 'brew uninstall gh' rollback after docker install failure; calls: {signatures}"
    )


def test_log_recorded_before_subprocess(pf, fake_shell, fake_which, monkeypatch, tmp_install_log):
    """PRE-04: install-log.json 'started' entry is written BEFORE the subprocess call.

    Asserts strict event ordering: write(started) < subprocess(install_command).
    This falsifies implementations that write 'started' AFTER calling subprocess.run.
    """
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"

    events: list[tuple] = []

    # Wrap pf._write_install_log to record write events
    original_write = pf._write_install_log

    def recording_write(log):
        if log.get("actions"):
            last = log["actions"][-1]
            events.append(("write", last.get("status"), last.get("tool")))
        return original_write(log)

    monkeypatch.setattr(pf, "_write_install_log", recording_write)

    # Wrap subprocess.run (already via fake_shell) to record subprocess events
    original_fake_shell_call = fake_shell.__class__.__call__

    def recording_call(self, cmd, *args, **kwargs):
        sig = " ".join(cmd) if isinstance(cmd, list) else cmd
        events.append(("subprocess", sig))
        return original_fake_shell_call(self, cmd, *args, **kwargs)

    fake_shell.__class__.__call__ = recording_call

    # Build single-tool plan (node only)
    plan = pf.plan(no_docker=True)
    node_actions = [a for a in plan.actions if getattr(a, "tool", None) == "node"]
    if not node_actions:
        pytest.skip("No node action in plan — cannot test ordering")

    pf.apply(plan)

    # Find the write(started, node) and subprocess(node install) events
    write_indices = [
        i for i, e in enumerate(events)
        if e[0] == "write" and e[1] == "started" and e[2] == "node"
    ]
    install_sig = node_actions[0].install_command
    subprocess_indices = [
        i for i, e in enumerate(events)
        if e[0] == "subprocess" and install_sig in e[1]
    ]
    assert write_indices, f"No 'started' write event found; events: {events}"
    assert subprocess_indices, f"No subprocess install event found; events: {events}"
    assert write_indices[0] < subprocess_indices[0], (
        f"install-log.json must be written BEFORE subprocess call; "
        f"write at {write_indices[0]}, subprocess at {subprocess_indices[0]}; events: {events}"
    )


def test_dry_run_no_state_change(pf, fake_shell, fake_which, monkeypatch, tmp_install_log):
    """PRE-05: render_preview() returns non-empty string; zero subprocess calls; no log file created."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    plan = pf.plan()
    preview = pf.render_preview(plan)
    assert preview, "render_preview() must return a non-empty string"
    assert len(fake_shell.calls) == 0, (
        f"render_preview() must NOT invoke subprocess.run; calls: {fake_shell.calls}"
    )
    assert not tmp_install_log.exists(), (
        "render_preview() must NOT create install-log.json"
    )


def test_no_docker_mode_skips_docker(pf, fake_shell, fake_which, monkeypatch):
    """PRE-07: plan(no_docker=True) has no docker action and no docker detection prompt."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    plan = pf.plan(no_docker=True)
    docker_actions = [a for a in plan.actions if getattr(a, "tool", None) == "docker"]
    assert len(docker_actions) == 0, (
        "plan(no_docker=True) must contain no docker install action"
    )
    statuses = pf.detect(no_docker=True)
    # docker should either be absent or marked as detected=True (no prompt needed)
    if "docker" in statuses:
        assert statuses["docker"].detected, (
            "With no_docker=True, docker must be absent from statuses or marked detected=True"
        )
