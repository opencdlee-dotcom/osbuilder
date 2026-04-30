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
