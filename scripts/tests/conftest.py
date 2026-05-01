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


# ---------- Phase 6 fixtures (added by Plan 06-01 Wave 0) ----------

@pytest.fixture
def fake_built_app(tmp_path: Path) -> Path:
    """A tmp_path-rooted directory representing a scaffold_dispatch output.

    Used by test_scaffold_extensions.py and test_gh_handoff.py to test
    file-stamping helpers without running a real `pnpm create next-app`.
    Initializes a git repo so gh_handoff idempotency checks have something to inspect.
    """
    app = tmp_path / "fake-built-app"
    app.mkdir()
    (app / "package.json").write_text(
        '{"name":"fake-built-app","version":"0.1.0","scripts":{"test":"echo ok"}}\n',
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=str(app),
        check=True, shell=False, capture_output=True, text=True,
    )
    return app


@pytest.fixture
def fake_state_md(tmp_project_root: Path):
    """Builder fixture: seed a state.md via the state_writer subprocess.

    Usage:
        def test_x(fake_state_md, tmp_project_root):
            fake_state_md(goal="t", app_type="multi-user-web", playbook="web",
                          production_ready="true")
            # state.md now exists at tmp_project_root/.planning/osbuilder/state.md
    """
    def _seed(**fields):
        # init with required fields; missing ones get safe defaults
        defaults = {
            "goal": "test goal",
            "app_type": "multi-user-web",
            "playbook": "web",
        }
        defaults.update(fields)
        # init with goal first
        run_state_writer("init", "--goal", defaults.pop("goal"),
                         project_root=tmp_project_root)
        # then write each remaining field
        for field, value in defaults.items():
            run_state_writer("write", "--field", field, "--value", str(value),
                             project_root=tmp_project_root)
        return tmp_project_root / ".planning" / "osbuilder" / "state.md"
    return _seed


@pytest.fixture
def mock_gh_subprocess(monkeypatch):
    """Programmable gh subprocess mock — covers the 5 documented gh failure modes.

    Set returncode/stderr per failure mode key:
        mock_gh_subprocess["auth-status-fail"] = (1, "", "You are not logged into any GitHub hosts")
        mock_gh_subprocess["repo-create-fail"] = (1, "", "name already exists on this account")
        mock_gh_subprocess["network-fail"]    = (1, "", "could not resolve host: api.github.com")
        mock_gh_subprocess["token-expired"]   = (1, "", "HTTP 401: Bad credentials")
        mock_gh_subprocess["not-installed"]   = (-1, "", "")  # FileNotFoundError simulated

    Default (no key set): returncode=0, empty stdout/stderr — gh succeeds.
    Records every call as (cmd, returncode, stdout, stderr) in .calls.
    """
    class GhShell:
        def __init__(self):
            self.calls = []
            self.programmed = {}

        def __setitem__(self, key, val):
            # val is (returncode, stdout, stderr)
            self.programmed[key] = val

        def __call__(self, cmd, *args, **kwargs):
            sig = " ".join(cmd) if isinstance(cmd, list) else cmd
            # Match by failure-mode key the test set
            if "gh auth status" in sig and "auth-status-fail" in self.programmed:
                rc, so, se = self.programmed["auth-status-fail"]
            elif "gh repo create" in sig and "repo-create-fail" in self.programmed:
                rc, so, se = self.programmed["repo-create-fail"]
            elif "gh repo view" in sig and "view-fail" in self.programmed:
                rc, so, se = self.programmed["view-fail"]
            elif "not-installed" in self.programmed:
                self.calls.append((cmd, -1, "", ""))
                raise FileNotFoundError(2, "No such file or directory: 'gh'")
            elif "network-fail" in self.programmed and "gh " in sig:
                rc, so, se = self.programmed["network-fail"]
            elif "token-expired" in self.programmed and "gh " in sig:
                rc, so, se = self.programmed["token-expired"]
            else:
                rc, so, se = 0, "", ""
            self.calls.append((cmd, rc, so, se))
            return subprocess.CompletedProcess(cmd, rc, so, se)

    gh = GhShell()
    monkeypatch.setattr("subprocess.run", gh)
    return gh


@pytest.fixture
def mock_git_subprocess(monkeypatch):
    """Programmable git subprocess mock — covers clean tree / dirty tree / no-init scenarios.

    Set scenario key:
        mock_git_subprocess["scenario"] = "no-init"     # .git/ missing — git init succeeds
        mock_git_subprocess["scenario"] = "clean"       # repo exists, no changes
        mock_git_subprocess["scenario"] = "dirty"       # repo exists, uncommitted changes
        mock_git_subprocess["scenario"] = "remote-set"  # origin already configured (idempotent ship)

    Records calls in .calls.
    """
    class GitShell:
        def __init__(self):
            self.calls = []
            self.scenario = "clean"

        def __setitem__(self, key, val):
            if key == "scenario":
                self.scenario = val

        def __call__(self, cmd, *args, **kwargs):
            sig = " ".join(cmd) if isinstance(cmd, list) else cmd
            rc, so, se = 0, "", ""
            if "git remote get-url origin" in sig:
                if self.scenario == "remote-set":
                    so = "git@github.com:user/fake-built-app.git\n"
                else:
                    rc = 1
                    se = "fatal: No such remote 'origin'\n"
            elif "git status --porcelain" in sig:
                if self.scenario == "dirty":
                    so = " M README.md\n"
                else:
                    so = ""
            elif "git init" in sig:
                rc = 0  # git init always "succeeds" in the mock
            self.calls.append((cmd, rc, so, se))
            return subprocess.CompletedProcess(cmd, rc, so, se)

    git = GitShell()
    monkeypatch.setattr("subprocess.run", git)
    return git

