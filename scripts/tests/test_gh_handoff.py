"""test_gh_handoff.py — Phase 6 gh_handoff tests (Wave 1 — Plan 06-02).

Tests for SHIP-01 (V-01), SHIP-01 failure modes (V-02), SHIP-05 auth-drift (V-08).
Locked test names — DO NOT rename.
"""
from __future__ import annotations

import importlib
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def gh():
    """Lazy import of scripts/gh_handoff.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("gh_handoff")
    except ImportError:
        pytest.skip("gh_handoff module not yet created (Wave 1 target)")


# Real subprocess.run captured before any monkeypatching
_real_run = subprocess.run


class _GhGitShell:
    """Combined gh + git mock that passes state_writer subprocess calls through to real subprocess.run.

    gh calls: intercepted per failure-mode key.
    git calls: intercepted with configurable scenario.
    state_writer calls (sys.executable + state_writer.py): delegated to the real subprocess.run.
    """

    def __init__(self):
        self.calls = []
        self.programmed = {}
        self._scenario = "clean"  # "clean" | "dirty" | "remote-set"

    def __setitem__(self, key, val):
        if key == "scenario":
            self._scenario = val
        else:
            self.programmed[key] = val

    def __call__(self, cmd, *args, **kwargs):
        sig = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

        # Pass state_writer subprocess calls through to the real subprocess.run
        if "state_writer" in sig:
            return _real_run(cmd, *args, **kwargs)

        # gh failure-mode routing
        if "gh auth status" in sig and "auth-status-fail" in self.programmed:
            rc, so, se = self.programmed["auth-status-fail"]
        elif "gh repo create" in sig and "repo-create-fail" in self.programmed:
            rc, so, se = self.programmed["repo-create-fail"]
        elif "gh repo view" in sig and "view-fail" in self.programmed:
            rc, so, se = self.programmed["view-fail"]
        elif "gh " in sig and "not-installed" in self.programmed:
            self.calls.append((cmd, -1, "", ""))
            raise FileNotFoundError(2, "No such file or directory: 'gh'")
        elif "gh " in sig and "network-fail" in self.programmed:
            rc, so, se = self.programmed["network-fail"]
        elif "gh " in sig and "token-expired" in self.programmed:
            rc, so, se = self.programmed["token-expired"]
        # git routing (scenario-based)
        elif "git remote get-url origin" in sig:
            if self._scenario == "remote-set":
                rc, so, se = 0, "git@github.com:user/fake-built-app.git\n", ""
            else:
                rc, so, se = 1, "", "fatal: No such remote 'origin'\n"
        elif "git status --porcelain" in sig:
            if self._scenario == "dirty":
                rc, so, se = 0, " M README.md\n", ""
            else:
                rc, so, se = 0, "", ""
        elif "git add" in sig or "git commit" in sig or "git init" in sig:
            rc, so, se = 0, "", ""
        # gh repo view (success path — return valid JSON)
        elif "gh repo view" in sig:
            import json as _json
            out = _json.dumps({
                "visibility": "PRIVATE",
                "nameWithOwner": "user/fake-built-app",
                "sshUrl": "git@github.com:user/fake-built-app.git",
            })
            rc, so, se = 0, out, ""
        else:
            rc, so, se = 0, "", ""

        self.calls.append((cmd, rc, so, se))
        return subprocess.CompletedProcess(cmd, rc, so, se)


def test_ship_runs_private_create(gh, fake_built_app, monkeypatch, tmp_project_root, fake_state_md):
    """SHIP-01 (V-01): gh.ship() invokes `gh repo create --private --source=. --push`."""
    fake_state_md(goal="test", app_type="multi-user-web", playbook="web")

    shell = _GhGitShell()
    monkeypatch.setattr("subprocess.run", shell)

    result = gh.ship(fake_built_app, tmp_project_root)

    assert result == 0, f"ship() returned {result}, expected 0"

    # Verify gh repo create --private was called
    cmd_strings = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in shell.calls
    ]
    create_calls = [s for s in cmd_strings if "gh repo create" in s]
    assert len(create_calls) >= 1, f"gh repo create not called. Calls:\n" + "\n".join(cmd_strings)
    assert any("--private" in s for s in create_calls), \
        f"--private not in gh repo create calls: {create_calls}"

    # Verify state.md has repo_visibility=PRIVATE (written by real state_writer via _real_run passthrough)
    state_path = tmp_project_root / ".planning" / "osbuilder" / "state.md"
    assert state_path.exists(), "state.md not found after ship()"
    state_content = state_path.read_text(encoding="utf-8")
    assert "repo_visibility: PRIVATE" in state_content, \
        f"repo_visibility not written to state.md. Content:\n{state_content}"


def test_failure_modes_friendly(gh, fake_built_app, monkeypatch, capsys,
                                 tmp_project_root, fake_state_md):
    """SHIP-01 (V-02): all 5 gh failure modes produce friendly_error-formatted stderr."""
    fake_state_md(goal="test", app_type="multi-user-web", playbook="web")

    # --- mode: auth-status-fail ---
    shell = _GhGitShell()
    shell["auth-status-fail"] = (1, "", "You are not logged into any GitHub hosts. Please run 'gh auth login'")
    monkeypatch.setattr("subprocess.run", shell)

    result = gh.ship(fake_built_app, tmp_project_root)
    captured = capsys.readouterr()
    assert result == 1, "ship() should return 1 on auth failure"
    assert "##" in captured.err, f"Expected '##' in stderr (auth-status-fail), got: {captured.err!r}"
    assert "What to do:" in captured.err
    assert "gh auth login" in captured.err

    # --- mode: not-installed (FileNotFoundError) ---
    shell2 = _GhGitShell()
    shell2["not-installed"] = (-1, "", "")
    monkeypatch.setattr("subprocess.run", shell2)

    result2 = gh.ship(fake_built_app, tmp_project_root)
    captured2 = capsys.readouterr()
    assert result2 == 1, "ship() should return 1 when gh not installed"
    assert "##" in captured2.err, f"Expected '##' in stderr (not-installed), got: {captured2.err!r}"
    assert "What to do:" in captured2.err

    # --- mode: repo-create-fail (HTTP 422 name collision) ---
    shell3 = _GhGitShell()
    shell3["repo-create-fail"] = (1, "", "HTTP 422: name already exists on this account")
    monkeypatch.setattr("subprocess.run", shell3)

    result3 = gh.ship(fake_built_app, tmp_project_root)
    captured3 = capsys.readouterr()
    assert result3 == 1
    assert "##" in captured3.err, f"Expected '##' in stderr (repo-create-fail), got: {captured3.err!r}"
    assert "What to do:" in captured3.err

    # --- mode: network-fail ---
    shell4 = _GhGitShell()
    shell4["network-fail"] = (1, "", "could not resolve host: api.github.com")
    monkeypatch.setattr("subprocess.run", shell4)

    result4 = gh.ship(fake_built_app, tmp_project_root)
    captured4 = capsys.readouterr()
    assert result4 == 1
    assert "##" in captured4.err, f"Expected '##' in stderr (network-fail), got: {captured4.err!r}"
    assert "What to do:" in captured4.err

    # --- mode: token-expired (HTTP 401) ---
    shell5 = _GhGitShell()
    shell5["token-expired"] = (1, "", "HTTP 401: Bad credentials")
    monkeypatch.setattr("subprocess.run", shell5)

    result5 = gh.ship(fake_built_app, tmp_project_root)
    captured5 = capsys.readouterr()
    assert result5 == 1
    assert "##" in captured5.err, f"Expected '##' in stderr (token-expired), got: {captured5.err!r}"
    assert "What to do:" in captured5.err
    assert "gh auth login" in captured5.err, \
        f"Expected 'gh auth login' in stderr for token-expired. Got: {captured5.err!r}"


def test_auth_drift_friendly(gh, fake_built_app, monkeypatch, capsys,
                              tmp_project_root, fake_state_md):
    """SHIP-05 (V-08): gh auth drift produces stderr with `gh auth login --git-protocol https`."""
    fake_state_md(goal="test", app_type="multi-user-web", playbook="web")

    shell = _GhGitShell()
    shell["auth-status-fail"] = (
        1, "", "You are not logged into any GitHub hosts. Please run 'gh auth login'"
    )
    monkeypatch.setattr("subprocess.run", shell)

    result = gh.ship(fake_built_app, tmp_project_root)
    captured = capsys.readouterr()

    assert result == 1
    assert "gh auth login --git-protocol https" in captured.err, \
        f"Expected 'gh auth login --git-protocol https' in stderr. Got:\n{captured.err!r}"
