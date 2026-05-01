"""test_mode_gating.py — Phase 5 mode gating tests (Wave 1 GREEN).

Wave 0 (Plan 05-01) shipped these as RED stubs that called pytest.skip.
Wave 1 (Plan 05-04) replaces each skip with real assertions against the
mode-gating logic in intake_handler.py and stack_researcher.py.

Forbidden tokens in beginner-mode output (per UX-03 acceptance test):
    Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind
"""
from __future__ import annotations

import importlib
from pathlib import Path
from unittest import mock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

# 9 forbidden technology tokens that must never surface in beginner-mode output
_FORBIDDEN_JARGON = (
    "Next.js", "SvelteKit", "Postgres", "SQLite",
    "Vercel", "Fly.io", "Railway", "Drizzle", "Tailwind",
)


@pytest.fixture
def intake():
    """Lazy import of scripts/intake_handler.py — skips when not yet available."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet available (Wave 1 target)")


@pytest.fixture
def researcher():
    """Lazy import of scripts/stack_researcher.py — skips when not yet available."""
    try:
        return importlib.import_module("stack_researcher")
    except ImportError:
        pytest.skip("stack_researcher module not yet available (Wave 1 target)")


def _init_state(writer, project_root: Path) -> None:
    """Helper: initialize a fresh state.md inside project_root."""
    writer("init", "--goal", "test", "--app-type", "web",
           "--playbook", "web", project_root=project_root)


# ---------- UX-03: state_writer accepts 'mode' field ----------


def test_mode_field_allowed_in_state_writer(writer, tmp_project_root):
    """UX-03: state_writer.py accepts writes for the 'mode' field (beginner/advanced)."""
    _init_state(writer, tmp_project_root)

    # Write mode=beginner
    r = writer("write", "--field", "mode", "--value", "beginner",
               project_root=tmp_project_root, check=False)
    assert r.returncode == 0, f"writer write mode=beginner failed: {r.stderr}"

    # Write mode=advanced (overwrite)
    r = writer("write", "--field", "mode", "--value", "advanced",
               project_root=tmp_project_root, check=False)
    assert r.returncode == 0, f"writer write mode=advanced failed: {r.stderr}"


# ---------- UX-03: beginner-mode jargon gate at intake ----------


def test_beginner_mode_no_jargon_in_prompts(intake, tmp_project_root, writer, capsys):
    """UX-03: parse_paragraph in beginner mode emits no stack-tech tokens to derived_spec."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)

    # parse_paragraph with a paragraph that mentions a TODO web app
    dest = intake.parse_paragraph(
        "I want a TODO web app", project_root=tmp_project_root
    )

    # Read the rendered derived_spec.md and verify no jargon
    content = dest.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    combined = content + "\n" + captured.out + "\n" + captured.err

    for token in _FORBIDDEN_JARGON:
        assert token not in combined, (
            f"Forbidden jargon {token!r} appeared in beginner-mode output:\n{combined}"
        )


def test_beginner_mode_omits_stack_hints_from_structured(intake, tmp_project_root, writer):
    """UX-03: parse_structured in beginner mode strips stack_hints from output."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)

    dest = intake.parse_structured(
        {"goal": "TODO list", "app_type": "web",
         "stack_hints": ["Next.js", "Drizzle", "Postgres"]},
        project_root=tmp_project_root,
    )
    content = dest.read_text(encoding="utf-8")
    for token in _FORBIDDEN_JARGON:
        assert token not in content, (
            f"Forbidden jargon {token!r} leaked into beginner-mode derived_spec:\n{content}"
        )


def test_advanced_mode_includes_stack_hints(intake, tmp_project_root, writer):
    """UX-03 inverse: advanced mode preserves stack_hints in the rendered spec."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "advanced",
           project_root=tmp_project_root)

    dest = intake.parse_structured(
        {"goal": "TODO list", "app_type": "web",
         "stack_hints": ["Next.js", "Drizzle"]},
        project_root=tmp_project_root,
    )
    content = dest.read_text(encoding="utf-8")
    # At least one of the supplied hints must appear in advanced-mode output
    assert "Next.js" in content or "Drizzle" in content, (
        f"Advanced-mode derived_spec should retain stack_hints; got:\n{content}"
    )


# ---------- UX-03: advanced-mode exposes stack ----------


def test_advanced_mode_exposes_stack(researcher, tmp_project_root, writer, monkeypatch):
    """UX-03: research_stack in advanced mode returns stack-menu keys (with brainiac mocked empty)."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "advanced",
           project_root=tmp_project_root)

    # Mock _call_brainiac to return {} so we hit the stack-menu fallback path,
    # which still happens to be exercised in advanced mode.
    monkeypatch.setattr(researcher, "_call_brainiac", lambda app_type: {})

    result = researcher.research_stack("web", project_root=tmp_project_root)

    assert isinstance(result, dict) and result, "research_stack returned empty dict"
    # At least one of the stack-menu keys must be present
    expected_keys = {"framework", "orm", "database", "css", "package_manager"}
    assert expected_keys & set(result.keys()), (
        f"Advanced-mode research_stack missing all stack-menu keys; got {list(result.keys())}"
    )


# ---------- UX-03: defaults and persistence ----------


def test_mode_default_is_beginner(intake, tmp_project_root):
    """UX-03: a project_root with no state.md returns 'beginner' from _mode_from_state."""
    # tmp_project_root has .planning/ but no .planning/osbuilder/state.md
    mode = intake._mode_from_state(tmp_project_root)
    assert mode == "beginner", f"Expected 'beginner' default, got {mode!r}"


def test_mode_persists_across_state_reads(writer, tmp_project_root):
    """UX-03: writing mode='advanced' then reading 'mode' returns 'advanced'."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "advanced",
           project_root=tmp_project_root)

    r = writer("read", "--field", "mode",
               project_root=tmp_project_root, check=False)
    assert r.returncode == 0, f"read mode failed: {r.stderr}"
    assert r.stdout.strip() == "advanced", (
        f"Expected mode='advanced' after write; got {r.stdout.strip()!r}"
    )


def test_beginner_mode_stack_researcher_skips_brainiac(researcher, tmp_project_root, writer, monkeypatch):
    """UX-03: research_stack with mode=beginner makes no call to _call_brainiac."""
    _init_state(writer, tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)

    called = []

    def _spy(app_type):
        called.append(app_type)
        return {}

    monkeypatch.setattr(researcher, "_call_brainiac", _spy)

    result = researcher.research_stack("web", project_root=tmp_project_root)

    assert called == [], (
        f"_call_brainiac should NOT be invoked in beginner mode; was called with {called}"
    )
    # Beginner mode should still return a stack dict (from stack-menu)
    assert isinstance(result, dict) and result, (
        f"Beginner-mode research_stack should return stack-menu defaults; got {result!r}"
    )
