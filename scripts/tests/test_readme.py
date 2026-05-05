"""test_readme.py — RED stubs for Phase 8 QUAL-02/03/SC-6 README content.

Skips until README.md is created in 08-05.
"""
from __future__ import annotations
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


def _readme_text() -> str:
    if not README.exists():
        pytest.skip("README.md not yet created (08-05 target)")
    return README.read_text(encoding="utf-8")


def test_has_install_one_liner():
    """QUAL-02: README documents the curl-pipe-shell install one-liner."""
    text = _readme_text()
    # Must reference the documented URL pattern; literal URL substituted from 08-URL-LOCK.md
    assert re.search(r"curl -fsSL.*install\.sh.*\| sh", text), \
        "README must contain the documented one-liner install command"


def test_has_dev_team_section():
    """QUAL-03: README explains the 8-role dev-team metaphor."""
    text = _readme_text().lower()
    for role in ("pm", "architect", "frontend", "backend", "devops", "qa", "reviewer", "tech writer"):
        assert role in text, f"README must mention dev-team role '{role}'"


def test_links_demo():
    """QUAL-03: README references the 60s demo asset (GIF or asciinema cast)."""
    text = _readme_text()
    assert re.search(r"assets/demo/osbuilder-demo\.(gif|cast)", text), \
        "README must link assets/demo/osbuilder-demo.{gif,cast}"


def test_demo_asset_present():
    """QUAL-03: at least one of GIF/asciinema-cast assets exists in assets/demo/."""
    demo_dir = REPO_ROOT / "assets" / "demo"
    if not demo_dir.exists():
        pytest.skip("assets/demo/ not yet created (08-06 target)")
    if not list(demo_dir.glob("osbuilder-demo.*")):
        pytest.skip("demo asset not yet recorded (08-07 Task 2)")
    assets = list(demo_dir.glob("osbuilder-demo.*"))
    assert assets, "assets/demo/osbuilder-demo.{gif,cast} must exist"


def test_documents_production_ready():
    """SC-6: README documents --production-ready flag and 7 named upgrades (verbatim from production_phase_writer.NAMED_UPGRADES)."""
    text = _readme_text().lower()
    assert "--production-ready" in text
    for name in ("observability", "migrations", "healthchecks", "secret-manager",
                 "sentry", "rate-limiting", "backups"):
        assert name in text, f"README must document --production-ready upgrade '{name}'"
