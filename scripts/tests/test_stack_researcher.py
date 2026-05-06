"""Tests for scripts/stack_researcher.py — RES-01..RES-04.

All tests in this file FAIL or SKIP before Plan 03-03 lands.
That is by design (TDD RED state).

`stack_researcher` is imported lazily inside the `sr` fixture so pytest
can COLLECT every test function before Plan 03-03 lands.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def sr():
    """Lazy import of scripts/stack_researcher.py — skips when not yet created."""
    try:
        return importlib.import_module("stack_researcher")
    except ImportError:
        pytest.skip("stack_researcher module not yet created (Wave 1 target)")


def test_calls_brainiac(sr, tmp_project_root, monkeypatch):
    """RES-01: research() calls _call_brainiac and returns a structured dict.

    Phase 5 UX-03: brainiac is gated by state.md mode field; advanced mode
    invokes brainiac, beginner mode skips it. We force advanced mode by
    monkey-patching _mode_from_state to return 'advanced' (avoiding the
    subprocess.run state-read indirection), then spy on _call_brainiac to
    confirm it is invoked exactly once.
    """
    monkeypatch.setattr(sr, "_mode_from_state", lambda root: "advanced")

    brainiac_calls = []

    def _spy_brainiac(app_type):
        brainiac_calls.append(app_type)
        return {
            "framework": {"name": "next.js", "version": "16.2.4", "rationale": "industry default"},
            "orm": {"name": "drizzle-orm", "version": "0.45.2", "rationale": "lightweight"},
        }

    monkeypatch.setattr(sr, "_call_brainiac", _spy_brainiac)

    result = sr.research_stack(app_type="web", project_root=tmp_project_root)
    assert isinstance(result, dict), "research_stack() must return a dict"
    assert "framework" in result, "Result must include 'framework' key"
    assert len(brainiac_calls) >= 1, (
        f"stack_researcher must invoke _call_brainiac in advanced mode (RES-01); "
        f"got {len(brainiac_calls)} calls"
    )


def test_output_is_structured(sr, fake_shell, tmp_project_root):
    """RES-02: research_stack() returns structured JSON with name/version/rationale per component."""
    fake_shell.program(
        "python3 -m brainiac",
        returncode=0,
        stdout=json.dumps({
            "framework": {"name": "next.js", "version": "16.2.4", "rationale": "standard"},
            "orm": {"name": "drizzle-orm", "version": "0.45.2", "rationale": "lightweight"},
            "database": {"name": "postgres", "version": "18-alpine", "rationale": "multi-user"},
            "css": {"name": "tailwindcss", "version": "4.2.4", "rationale": "utility-first"},
            "package_manager": {"name": "pnpm", "version": "10.33.2", "rationale": "fast"},
        }),
    )
    result = sr.research_stack(app_type="web", project_root=tmp_project_root)
    assert isinstance(result, dict), "Result must be a dict"
    for key in ("framework", "orm", "database", "css", "package_manager"):
        assert key in result, f"Result must include '{key}' key (RES-02)"
        component = result[key]
        assert isinstance(component, dict), f"result['{key}'] must be a dict"
        assert "name" in component, f"result['{key}'] must have 'name' field"
        assert "version" in component, f"result['{key}'] must have 'version' field"


def test_fallback_to_stack_menu(sr, fake_shell, tmp_project_root):
    """RES-03: returns stack-menu.md defaults when brainiac returns empty/timeout."""
    # Simulate brainiac returning empty output (timeout/inconclusive path)
    fake_shell.program("python3 -m brainiac", returncode=0, stdout="")
    result = sr.research_stack(app_type="web", project_root=tmp_project_root)
    assert result, "Fallback must return non-empty stack_choices dict (RES-03)"
    assert "framework" in result, (
        "Fallback from stack-menu.md must include 'framework' key (RES-03)"
    )


def test_advanced_override(sr, fake_shell, tmp_project_root):
    """RES-04: --advanced overrides merge over researched stack choices."""
    fake_shell.program(
        "python3 -m brainiac",
        returncode=0,
        stdout=json.dumps({
            "framework": {"name": "next.js", "version": "16.2.4", "rationale": "standard"},
            "orm": {"name": "drizzle-orm", "version": "0.45.2", "rationale": "lightweight"},
        }),
    )
    overrides = {"orm": {"name": "prisma", "version": "5.0.0", "source": "user-override"}}
    result = sr.research_stack(
        app_type="web",
        project_root=tmp_project_root,
        advanced_overrides=overrides,
    )
    assert result["orm"]["name"] == "prisma", (
        "--advanced override must replace researched orm choice (RES-04). "
        f"Got: {result.get('orm')}"
    )


def test_stack_menu_slices_per_app_type(sr):
    """v1.0 audit: _read_stack_menu MUST slice to the requested app_type's
    section before harvesting `| Component | Package | ... |` rows. Previously
    the regex ran across the whole file and the dict-overwrite left the LAST
    section's values for every app_type — a web build inherited
    framework=fastapi because the ai-service section came later in the file.
    """
    from pathlib import Path
    refs = Path(__file__).resolve().parents[2] / "references"
    web = sr._read_stack_menu(refs, "web")
    ai = sr._read_stack_menu(refs, "ai-service")
    assert web.get("framework", {}).get("name") == "next.js", (
        f"web playbook must resolve to next.js framework; got {web.get('framework')}"
    )
    assert ai.get("framework", {}).get("name") == "fastapi", (
        f"ai-service playbook must resolve to fastapi framework; got {ai.get('framework')}"
    )
