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


def test_install_copies_orchestrator_scripts(fake_home):
    """v1.0 HUMAN-UAT follow-up: install.sh must copy every orchestrator helper
    script the skill calls at runtime, not just state_writer + bootstrap shims.

    A previous version of install.sh shipped only state_writer.py + the two
    bootstrap shims, which made `/osbuilder` non-functional after a clean
    one-liner install — preflight_check.py / scaffold_dispatch.py / intake_handler.py
    / runbook_writer.py and the rest were missing under ~/.claude/skills/osbuilder/.
    This test pins the full set so that regression cannot recur silently.
    """
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created")
    result = _run_install(fake_home)
    assert result.returncode == 0, f"install.sh failed: {result.stderr}"
    skill_scripts = fake_home / ".claude" / "skills" / "osbuilder" / "scripts"
    required = {
        "state_writer.py",
        "bootstrap.sh",
        "bootstrap.ps1",
        "preflight_check.py",
        "scaffold_dispatch.py",
        "intake_handler.py",
        "stack_researcher.py",
        "runbook_writer.py",
        "narration.py",
        "friendly_error.py",
        "registry_verify.py",
        "gh_handoff.py",
        "gsd_driver.py",
        "failure_classifier.py",
        "production_phase_writer.py",
        "check_skill_md_length.py",
        "check_skill_versions.py",
    }
    present = {p.name for p in skill_scripts.iterdir() if p.is_file()}
    missing = required - present
    assert not missing, (
        f"install.sh did not copy orchestrator scripts: {sorted(missing)}. "
        f"The skill cannot run at /osbuilder invocation without them."
    )


def test_install_copies_runtime_assets(fake_home):
    """v1.0 HUMAN-UAT follow-up: install.sh must copy assets/ subtrees the
    scaffolders read at runtime — without these, scaffold_cli / scaffold_ai_service /
    scaffold_hub fail with FileNotFoundError on the very first OSBuilder run.
    """
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not yet created")
    result = _run_install(fake_home)
    assert result.returncode == 0
    skill_assets = fake_home / ".claude" / "skills" / "osbuilder" / "assets"
    required_files = [
        "readme-template.md",
        "cli-starter/__main__.py.tmpl",
        "cli-starter/pyproject.snippet.toml",
        "fastapi-starter/main.py",
        "hub-template/CLAUDE.md.tmpl",
        "hub-template/subtool-CLAUDE.md.tmpl",
    ]
    missing = [rel for rel in required_files
               if not (skill_assets / rel).is_file()]
    assert not missing, (
        f"install.sh did not copy runtime assets: {missing}. "
        f"Scaffold helpers will fail with FileNotFoundError when called."
    )
