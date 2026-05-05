"""test_ci_workflow.py — RED stubs for Phase 8 QUAL-01 CI surface.

Skips until .github/workflows/ci.yml is created in 08-04.
"""
from __future__ import annotations
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    """QUAL-01: .github/workflows/ci.yml is committed."""
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created (08-04 target)")
    assert CI_YML.is_file()


def test_pins_action_versions():
    """Security V14: pin to exact major (@v6), not @latest."""
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created (08-04 target)")
    text = CI_YML.read_text(encoding="utf-8")
    assert "@latest" not in text, "CI workflow must pin actions to exact major version"
    assert "actions/checkout@v6" in text
    assert "actions/setup-python@v6" in text


def test_invokes_lint_script():
    """QUAL-01: CI invokes scripts/check_skill_md_length.py."""
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created (08-04 target)")
    text = CI_YML.read_text(encoding="utf-8")
    assert "scripts/check_skill_md_length.py" in text
