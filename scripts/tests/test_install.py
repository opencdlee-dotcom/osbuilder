"""Tests for install.sh — FOUND-03 (4-dir layout) + BLOCKER-1 (artifacts copied to SKILL_DIR).

All tests fail / skip before Plan 03 lands. test_install_copies_artifacts also
requires Plan 02 (SKILL.md) to exist — RED until both plans land, GREEN after.
"""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"


def _run_install(home_dir: Path) -> subprocess.CompletedProcess:
    """Invoke install.sh with HOME pointed at an isolated tmp dir."""
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    return subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


def test_install_creates_four_dirs(fake_home):
    """1-03-04 (FOUND-03): install.sh creates references/, scripts/, assets/, examples/."""
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created (Plan 03 target)")
    result = _run_install(fake_home)
    assert result.returncode == 0, f"install.sh failed: {result.stderr}"
    skill_dir = fake_home / ".claude" / "skills" / "osbuilder"
    for sub in ("references", "scripts", "assets", "examples"):
        assert (skill_dir / sub).is_dir(), f"missing {sub}/ in {skill_dir}"


def test_install_idempotent(fake_home):
    """1-03-05: running install.sh twice produces no errors and identical layout."""
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created (Plan 03 target)")
    first = _run_install(fake_home)
    assert first.returncode == 0, f"first run failed: {first.stderr}"
    skill_dir = fake_home / ".claude" / "skills" / "osbuilder"
    listing_1 = sorted(p.relative_to(skill_dir).as_posix()
                       for p in skill_dir.rglob("*"))

    second = _run_install(fake_home)
    assert second.returncode == 0, f"second run failed: {second.stderr}"
    listing_2 = sorted(p.relative_to(skill_dir).as_posix()
                       for p in skill_dir.rglob("*"))
    assert listing_1 == listing_2, \
        f"layout drift between runs:\n{set(listing_1) ^ set(listing_2)}"


def test_install_copies_artifacts(fake_home):
    """1-03-06 (BLOCKER 1): after install, ${SKILL_DIR}/SKILL.md exists.

    RED until Plan 02 (SKILL.md) AND Plan 03 (install.sh w/ copy step) land.
    GREEN after both.
    """
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created (Plan 03 target)")
    if not (REPO_ROOT / "SKILL.md").exists():
        pytest.skip("SKILL.md not yet created (Plan 02 target)")
    result = _run_install(fake_home)
    assert result.returncode == 0, f"install.sh failed: {result.stderr}"
    skill_dir = fake_home / ".claude" / "skills" / "osbuilder"
    assert (skill_dir / "SKILL.md").is_file(), \
        "BLOCKER 1: install.sh must copy SKILL.md into SKILL_DIR"


def test_install_no_nested_dirs(fake_home):
    """1-03-07: post-install, no directory nests deeper than one level under SKILL_DIR."""
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created (Plan 03 target)")
    result = _run_install(fake_home)
    assert result.returncode == 0
    skill_dir = fake_home / ".claude" / "skills" / "osbuilder"
    # find SKILL_DIR -mindepth 3 -type d
    deep_dirs = [p for p in skill_dir.rglob("*")
                 if p.is_dir()
                 and len(p.relative_to(skill_dir).parts) >= 3]
    assert deep_dirs == [], \
        f"Anthropic one-level-deep rule violated: {deep_dirs}"
