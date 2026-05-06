"""test_runbook_writer.py — GREEN tests for Phase 6 runbook_writer (Wave 1 — Plan 06-04).

Covers V-03: write_readme() produces a clone-and-run README with all required sections,
no unsubstituted placeholders, and idempotent behaviour.

Locked test names (V-IDs from 06-VALIDATION.md) — DO NOT rename.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def rw():
    """Lazy import of scripts/runbook_writer.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("runbook_writer")
    except ImportError:
        pytest.skip("runbook_writer module not yet created (Wave 1 target)")


def test_runbook_writes_quickstart(rw, fake_built_app, fake_state_md, tmp_project_root):
    """SHIP-02 (V-03): rw.write_readme() produces README.md with Quick Start + no unsubstituted placeholders."""
    # Seed state.md with fields matching the plan's behavior spec
    fake_state_md(
        goal="test goal",
        app_type="multi-user-web",
        playbook="web",
        project_path=str(fake_built_app),
        repo_url="git@github.com:user/my-app.git",
    )

    # First write
    result = rw.write_readme(fake_built_app, tmp_project_root)

    # README.md was created
    readme = fake_built_app / "README.md"
    assert readme.exists(), "README.md was not created"
    assert result == readme

    content = readme.read_text(encoding="utf-8")

    # Required H2 sections (sentence-case per humanizer audit; see commit fixing
    # /humanizer flag on `## Quick Start`).
    for section in ("## Quick start", "## Requirements", "## Configuration", "## Development", "## Tests"):
        assert section in content, f"Missing required section: {section!r}"

    # Pitfall 2 mitigation lines (verbatim)
    assert "cp .env.example .env" in content, "Missing Quick Start env copy line"
    assert "pre-commit install" in content, "Missing pre-commit install line (Pitfall 2)"

    # Idempotency marker present (enables idempotency check)
    assert rw.OSBUILDER_MARKER in content, "Missing idempotency marker"

    # No unsubstituted placeholders
    assert "{{" not in content, f"Unsubstituted placeholder found in README: {content}"
    assert "}}" not in content, f"Unsubstituted placeholder found in README: {content}"

    # Project name derived from project_path basename
    assert "fake-built-app" in content, "project_name not substituted from project_path basename"

    # Idempotency: second call must NOT overwrite when marker is present
    # Tamper README to verify it is not re-written
    readme.write_text(content + "\n## TAMPER_SENTINEL\n", encoding="utf-8")
    rw.write_readme(fake_built_app, tmp_project_root)
    content_after = readme.read_text(encoding="utf-8")
    assert "## TAMPER_SENTINEL" in content_after, (
        "Idempotency check failed: write_readme overwrote README.md even though "
        f"{rw.OSBUILDER_MARKER!r} was already present"
    )
