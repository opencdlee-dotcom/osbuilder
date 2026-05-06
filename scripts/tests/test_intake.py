"""Tests for scripts/intake_handler.py — IN-01..IN-05.

All tests in this file FAIL or SKIP before Plan 03-02 lands.
That is by design (TDD RED state, mirrors Phase 1/2 Wave 0 contract).

Note: `intake_handler` is imported lazily inside the `ih` fixture so pytest
can COLLECT every test function before Plan 03-02 lands. Hoisting the import
to module scope (e.g. via `pytest.importorskip`) makes the entire module
disappear from --collect-only and breaks the >= 16 stubs Wave 0 gate.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest


@pytest.fixture
def ih():
    """Lazy import of scripts/intake_handler.py — skips when not yet created."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")


def test_paragraph_to_derived_spec(ih, tmp_project_root):
    """IN-01: paragraph input → derived_spec.md written to <project>/.planning/osbuilder/derived_spec.md."""
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    ih.parse_paragraph(
        "I want a website where students upload lab notebooks and I grade them",
        tmp_project_root,
    )
    assert spec_path.exists(), "derived_spec.md must be written to disk"
    content = spec_path.read_text(encoding="utf-8")
    assert "**Goal:**" in content, "derived_spec.md must contain **Goal:** section"
    assert "**App type:**" in content, "derived_spec.md must contain **App type:** section"
    assert "**Playbook:**" in content, "derived_spec.md must contain **Playbook:** section"


def test_structured_spec_to_derived_spec(ih, tmp_project_root):
    """IN-02: structured spec (dict) → same derived_spec.md output format as paragraph path."""
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    structured = {
        "goal": "Lab notebook grading platform",
        "features": ["file upload", "per-student grading", "feedback delivery"],
        "users": ["students", "professor"],
        "stack_hints": ["web", "file storage"],
    }
    ih.parse_structured(structured, tmp_project_root)
    assert spec_path.exists(), "derived_spec.md must be written to disk for structured input"
    content = spec_path.read_text(encoding="utf-8")
    assert "**Goal:**" in content, "Structured path must produce same sections as paragraph path"
    assert "**App type:**" in content
    assert "**Playbook:**" in content


def test_questions_have_no_jargon(ih):
    """IN-03: question-bank.md contains no jargon words (responsive, ORM, framework, etc.)."""
    JARGON = {
        "responsive", "ORM", "framework", "endpoint", "middleware",
        "hydration", "SSR", "SSG", "CDN", "schema", "migration",
    }
    bank_path = Path(__file__).resolve().parents[2] / "references" / "question-bank.md"
    if not bank_path.exists():
        pytest.skip("question-bank.md not yet created (Wave 2 target)")
    content = bank_path.read_text(encoding="utf-8")
    found = {w for w in JARGON if re.search(rf"\b{re.escape(w)}\b", content, re.IGNORECASE)}
    assert not found, (
        f"question-bank.md contains forbidden jargon words: {found}. "
        "Questions must be outcome-framed in plain English (IN-03)."
    )


def test_questions_have_you_decide_option(ih):
    """IN-04: every question in question-bank.md has an 'I don't know, you decide' option."""
    bank_path = Path(__file__).resolve().parents[2] / "references" / "question-bank.md"
    if not bank_path.exists():
        pytest.skip("question-bank.md not yet created (Wave 2 target)")
    content = bank_path.read_text(encoding="utf-8")
    # Find all question sections (## Q: ...)
    question_sections = re.split(r"^## Q:", content, flags=re.MULTILINE)
    # Skip the preamble before the first ## Q:
    question_sections = [s for s in question_sections[1:] if s.strip()]
    assert question_sections, "question-bank.md must contain at least one ## Q: section"
    for section in question_sections:
        assert re.search(
            r"I don.t know,? you decide",
            section,
            re.IGNORECASE,
        ), (
            f"Question section missing 'I don't know, you decide' option:\n{section[:200]}"
        )


def test_derived_spec_format(ih, tmp_project_root):
    """IN-05: derived_spec.md format is suitable for /gsd-new-project --auto."""
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    ih.parse_paragraph(
        "Build me a TODO web app where users can add and complete tasks",
        tmp_project_root,
    )
    assert spec_path.exists(), "derived_spec.md must be written"
    content = spec_path.read_text(encoding="utf-8")
    # Required sections for /gsd-new-project --auto handoff (Pattern 3 from RESEARCH.md)
    assert content.startswith("# OSBuilder Derived Spec"), (
        "derived_spec.md must start with '# OSBuilder Derived Spec' heading"
    )
    assert "**Goal:**" in content
    assert "**App type:**" in content
    assert "**Playbook:**" in content
    # Must NOT contain secrets or credentials
    SECRET_PATTERNS = ["api_key", "password", "secret", "token", "DATABASE_URL=postgresql://"]
    for pat in SECRET_PATTERNS:
        assert pat.lower() not in content.lower(), (
            f"derived_spec.md must not contain secrets. Found pattern: {pat}"
        )


def test_parse_structured_string_users_not_iterated_char_by_char(ih, tmp_project_root):
    """v1.0 HUMAN-UAT 05 side-defect: when callers pass `users` as a string,
    `list("students and teachers")` iterates the string char-by-char and renders
    one bullet per character in derived_spec.md. parse_structured must coerce
    string scalars to a single-element list instead.
    """
    ih.parse_structured(
        {
            "goal": "lab notebook upload",
            "users": "students and teachers",
            "features": ["upload", "grade"],
        },
        project_root=tmp_project_root,
    )
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    content = spec_path.read_text(encoding="utf-8")
    assert "- students and teachers" in content, (
        "string `users` must be rendered as a single bullet, not character-by-character"
    )
    # Also assert the per-character symptom does NOT appear
    assert "- s\n- t\n- u\n- d" not in content, (
        "regression: string `users` is being iterated char-by-char"
    )


def test_secret_patterns_do_not_flag_benign_words(ih, tmp_project_root):
    """v1.0 audit: _SECRET_PATTERNS must not include bare nouns like password,
    token, api_key. Otherwise a benign spec ('a login page where users enter
    their password') is rejected as a secret leak.
    """
    # The intake should accept a benign mention of "password" in plain English.
    spec = ih.parse_paragraph(
        "Build a login page where users enter their email and password to sign in.",
        project_root=tmp_project_root,
    )
    content = spec.read_text(encoding="utf-8")
    # Sanity: the word made it through
    assert "password" in content.lower()
    # The validator must NOT flag this as a secret leak.
    import argparse
    args = argparse.Namespace(project_root=str(tmp_project_root))
    rc = ih._cmd_validate(args)
    assert rc == 0, (
        "validate must accept a spec that mentions 'password' as a benign noun"
    )


def test_secret_patterns_still_catch_real_credentials(ih, tmp_project_root):
    """v1.0 audit: _SECRET_PATTERNS must still catch obvious credential paste:
    sk-ant-..., ghp_..., DATABASE_URL=postgresql://, password=foo, etc.
    """
    spec = ih.parse_paragraph(
        "Build an app that uses my Anthropic key sk-ant-abc123def456 for inference.",
        project_root=tmp_project_root,
    )
    content = spec.read_text(encoding="utf-8")
    assert "sk-ant-" in content.lower()
    import argparse
    args = argparse.Namespace(project_root=str(tmp_project_root))
    rc = ih._cmd_validate(args)
    assert rc == 1, (
        "validate must reject a spec containing a pasted Anthropic key prefix"
    )


def test_electron_keyword_in_refuse_keywords(ih):
    """v1.0 HUMAN-UAT 07-5: 'electron' must be in REFUSE_KEYWORDS so the gate fires.

    The Electron rationale copy lives in references/refuse-list.md, but without
    the keyword in the runtime tuple `_matches_refuse_keyword('Electron desktop
    app')` returns None and no refusal ever shows.
    """
    assert "electron" in {kw.lower() for kw in ih.REFUSE_KEYWORDS}, (
        "REFUSE_KEYWORDS must include 'electron' so the v1 gate refuses Electron specs"
    )
    matched = ih._matches_refuse_keyword("I want an Electron desktop app for note-taking")
    assert matched is not None, (
        "_matches_refuse_keyword must match 'Electron' in a desktop-app spec"
    )
    assert matched.lower() == "electron"
