"""Tests for Phase 7 Plan 07-01 — intake routing + 5-way inference.

Verifies:
- `infer_app_type(text)` returns one of {web, ai-service, cli, desktop, hub-platform}
  with a numeric score per RESEARCH.md §Pattern 2 (D-01).
- `_score_playbooks(text)` returns a per-playbook score dict (helper for callers).
- `_is_low_confidence(scores)` flags low/tied scores so callers fall back to the
  question-bank "I don't know, you decide" branch (D-02 + IN-04).
- `parse_structured` with explicit `app_type` is regression-free (RESEARCH.md
  §07-01 Gotchas — parse_structured was not the deletion target).
- `check_refuse_list` short-circuits BEFORE inference is committed (refusal precedence).

Note: `intake_handler` is imported lazily inside the `ih` fixture so pytest can
COLLECT every test function before Plan 07-01 lands. Hoisting the import to module
scope (e.g. via `pytest.importorskip`) makes the entire module disappear from
--collect-only and breaks the Wave 0 stub-count gate (STATE.md "Test collection
pattern" rule).
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def ih():
    """Lazy import of scripts/intake_handler.py — skips when not yet created."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")


@pytest.fixture
def has_inference(ih):
    """Skip when the Phase 7 inference surface has not yet landed (Wave 1 target)."""
    if (
        not hasattr(ih, "infer_app_type")
        or not hasattr(ih, "PLAYBOOK_KEYWORDS")
        or not hasattr(ih, "_score_playbooks")
        or not hasattr(ih, "_is_low_confidence")
    ):
        pytest.skip(
            "infer_app_type / _score_playbooks / _is_low_confidence / "
            "PLAYBOOK_KEYWORDS not yet added (Wave 1 target)"
        )
    return ih


# ---------- 5 positive inference cases (D-01) ----------


def test_infer_app_type_web(has_inference):
    """D-01: paragraph about a website routes to the 'web' playbook with score >= 2.0."""
    text = "I want a website where students upload notebooks and I grade them"
    playbook, score = has_inference.infer_app_type(text)
    assert playbook == "web", f"Expected 'web', got {playbook!r} (score={score})"
    assert score >= 2.0, f"Web score should be >= 2.0, got {score}"


def test_infer_app_type_ai_service(has_inference):
    """D-01: paragraph about an HTTP API + LLM routes to 'ai-service' with score >= 2.0."""
    text = "I want an HTTP API that summarizes documents with an LLM"
    playbook, score = has_inference.infer_app_type(text)
    assert playbook == "ai-service", f"Expected 'ai-service', got {playbook!r} (score={score})"
    assert score >= 2.0, f"ai-service score should be >= 2.0, got {score}"


def test_infer_app_type_cli(has_inference):
    """D-01: paragraph about a command-line tool routes to 'cli' with score >= 2.0."""
    text = "I want a command-line tool to organize my photo library"
    playbook, score = has_inference.infer_app_type(text)
    assert playbook == "cli", f"Expected 'cli', got {playbook!r} (score={score})"
    assert score >= 2.0, f"cli score should be >= 2.0, got {score}"


def test_infer_app_type_desktop(has_inference):
    """D-01: paragraph about a desktop tray app routes to 'desktop' with score >= 2.0."""
    text = "I want a desktop app that runs locally with a tray icon"
    playbook, score = has_inference.infer_app_type(text)
    assert playbook == "desktop", f"Expected 'desktop', got {playbook!r} (score={score})"
    assert score >= 2.0, f"desktop score should be >= 2.0, got {score}"


def test_infer_app_type_hub(has_inference):
    """D-01: paragraph mentioning a Professor-Hub style umbrella routes to 'hub-platform'."""
    text = "build me a hub like Professor Hub for grading and rostering"
    playbook, score = has_inference.infer_app_type(text)
    assert playbook == "hub-platform", (
        f"Expected 'hub-platform', got {playbook!r} (score={score})"
    )
    assert score >= 2.0, f"hub-platform score should be >= 2.0, got {score}"


# ---------- 2 ambiguous cases (D-02 fallback) ----------


def test_inference_low_confidence_asks(has_inference):
    """D-02: vague paragraph yields top_score < 2.0 → _is_low_confidence True."""
    text = "build me something cool"
    scores = has_inference._score_playbooks(text)
    assert has_inference._is_low_confidence(scores) is True, (
        f"Vague spec should be low-confidence; scores={scores}"
    )


def test_inference_tied_asks(has_inference):
    """D-02: paragraph that scores similarly on web and cli should be flagged tied/low-confidence."""
    # "tool" hits cli; "web UI" hits web; "organize" hits cli; "photos" — neutral.
    # Either dimension wins by < 1.0, OR top score is < 2.0; either way → fallback.
    text = "I want a tool with a web UI to organize photos"
    scores = has_inference._score_playbooks(text)
    assert has_inference._is_low_confidence(scores) is True, (
        f"Tied web-vs-cli spec should be low-confidence; scores={scores}"
    )


# ---------- Refuse precedence ----------


def test_refuse_beats_inference(ih, tmp_project_root, fake_state_md, capsys):
    """Refusal gate fires before inference is committed (microservices is on the global refuse-list).

    Even if `microservices` weren't a refuse keyword, this test stages a derived_spec.md
    that contains it — the refusal short-circuits before any new playbook routing surface
    can be persisted. Mirrors test_refusal.py:31-67's fixture pattern.
    """
    fake_state_md(production_ready="false")

    osbuilder_dir = tmp_project_root / ".planning" / "osbuilder"
    osbuilder_dir.mkdir(parents=True, exist_ok=True)
    # Stage a spec that mentions microservices — refuse-list keyword.
    (osbuilder_dir / "derived_spec.md").write_text(
        "# OSBuilder Derived Spec\n\n"
        "**Goal:** I want microservices for my web app\n\n"
        "**App type:** web\n"
        "**Playbook:** references/playbooks/web.md\n",
        encoding="utf-8",
    )

    result = ih.check_refuse_list(tmp_project_root)
    assert result is True, (
        "check_refuse_list must return True for a spec mentioning 'microservices' — "
        "refusal must beat inference."
    )

    # Sanity: stderr emitted refusal copy
    captured = capsys.readouterr()
    assert captured.err, "Refusal copy must be emitted to stderr."


# ---------- Regression: parse_structured unchanged ----------


def test_parse_structured_unchanged(ih, tmp_project_root):
    """parse_structured with explicit app_type='web' still produces **App type:** web (regression)."""
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    structured = {
        "goal": "Test app",
        "features": ["x"],
        "users": ["single-user"],
        "stack_hints": [],
        "app_type": "web",
    }
    ih.parse_structured(structured, tmp_project_root)
    assert spec_path.exists(), "parse_structured must still write derived_spec.md"
    content = spec_path.read_text(encoding="utf-8")
    assert "**App type:** web" in content, (
        "parse_structured with explicit app_type='web' must render '**App type:** web' "
        "(regression check — Phase 7 Plan 07-01 must NOT touch parse_structured)."
    )
