"""test_check_skill_md_length.py — RED stubs for Phase 8 QUAL-01 standalone lint script.

All tests skip until check_skill_md_length module is created in 08-02.
"""
from __future__ import annotations
import importlib
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECK_SKILL_MD = REPO_ROOT / "scripts" / "check_skill_md_length.py"


@pytest.fixture
def csml():
    """Lazy import of scripts/check_skill_md_length.py — skips when not yet created (08-02 target)."""
    try:
        return importlib.import_module("check_skill_md_length")
    except ImportError:
        pytest.skip("check_skill_md_length module not yet created (08-02 target)")


def test_passes_under_limit(csml, tmp_path):
    """QUAL-01: returns 0 when SKILL.md is at or under the limit."""
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 100), encoding="utf-8")
    assert csml.check(fake, limit=200) == 0


def test_fails_over_limit(csml, tmp_path):
    """QUAL-01: returns 1 when SKILL.md exceeds the limit."""
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 250), encoding="utf-8")
    assert csml.check(fake, limit=200) == 1


def test_cli_subprocess_exit_code(tmp_path):
    """QUAL-01: invoked as a subprocess, returns non-zero on over-limit (CI surface)."""
    if not CHECK_SKILL_MD.exists():
        pytest.skip("check_skill_md_length.py not yet created (08-02 target)")
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 250), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(CHECK_SKILL_MD), "--skill-md", str(fake), "--limit", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "250 lines" in result.stderr
