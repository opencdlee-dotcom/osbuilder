"""Shared pytest fixtures for OSBuilder Phase 1 tests."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"
SKILL_MD = REPO_ROOT / "SKILL.md"
INSTALL_SH = REPO_ROOT / "install.sh"


@pytest.fixture
def tmp_project_root(tmp_path: Path) -> Path:
    """Project root with .planning/ already created (mirrors a real GSD project)."""
    (tmp_path / ".planning").mkdir()
    return tmp_path


@pytest.fixture
def state_md_path(tmp_project_root: Path) -> Path:
    """Resolved path to the state.md the writer would create."""
    return tmp_project_root / ".planning" / "osbuilder" / "state.md"


def run_state_writer(*args: str, project_root: Path | None = None,
                     check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Invoke `python scripts/state_writer.py <args>` as a subprocess."""
    cmd = [sys.executable, str(STATE_WRITER), *args]
    if project_root is not None:
        cmd += ["--project-root", str(project_root)]
    return subprocess.run(cmd, capture_output=capture, text=True, check=check)


@pytest.fixture
def writer():
    """Return the run_state_writer helper."""
    return run_state_writer


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch) -> Path:
    """An isolated HOME so install.sh writes into tmp_path, not real ~."""
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    return fake


class FakeShell:
    """Records every subprocess.run call and replays canned results.

    Use to test install logic without actually installing anything.
    Match by command-prefix; default to (returncode=0, "", "") if no match.
    """
    def __init__(self):
        self.calls = []  # [(cmd_list_or_str, returncode, stdout, stderr), ...]
        self._programmed = {}  # cmd_signature_prefix -> (returncode, stdout, stderr)

    def program(self, cmd_signature: str, returncode: int = 0,
                stdout: str = "", stderr: str = ""):
        """Pre-program a response for any subprocess.run that startswith(cmd_signature)."""
        self._programmed[cmd_signature] = (returncode, stdout, stderr)

    def __call__(self, cmd, *args, **kwargs):
        sig = " ".join(cmd) if isinstance(cmd, list) else cmd
        for prefix, (rc, so, se) in self._programmed.items():
            if sig.startswith(prefix):
                self.calls.append((cmd, rc, so, se))
                return subprocess.CompletedProcess(cmd, rc, so, se)
        # default: success with empty output
        self.calls.append((cmd, 0, "", ""))
        return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def fake_shell(monkeypatch):
    fs = FakeShell()
    monkeypatch.setattr("subprocess.run", fs)
    return fs


@pytest.fixture
def fake_which(monkeypatch):
    """Programmable shutil.which — set fake_which["node"] = "/usr/bin/node"."""
    found: dict[str, str | None] = {}
    monkeypatch.setattr("shutil.which", lambda name: found.get(name))
    return found


@pytest.fixture
def tmp_install_log(tmp_path, monkeypatch):
    """Isolate ~/.osbuilder/ to a tmp dir for tests.

    Returns the Path that ~/.osbuilder/install-log.json WILL resolve to
    (the file itself does not exist yet — preflight_check creates it).
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    return fake_home / ".osbuilder" / "install-log.json"

