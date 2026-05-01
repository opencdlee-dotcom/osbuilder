"""test_refusal.py — GREEN tests for Phase 6 refusal mechanics (Wave 1 — Plan 06-05).

V-14: test_kubernetes_refused — spec containing 'kubernetes' triggers refusal
V-15: test_refusal_copy_mentions_opt_in — references/refuse-list.md mentions 'production-ready'

Locked test names — DO NOT rename.
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
    """Lazy import of scripts/intake_handler.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")


def test_kubernetes_refused(ih, tmp_project_root, fake_state_md, monkeypatch, capsys):
    """SCL-05 (V-14): spec containing 'kubernetes' triggers refusal — last_failure starts with 'refused:' and stderr contains refusal copy."""
    # Seed state.md with production_ready=false (explicit)
    fake_state_md(production_ready="false")

    # Stage the k8s fixture as derived_spec.md
    osbuilder_dir = tmp_project_root / ".planning" / "osbuilder"
    osbuilder_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURE_DIR / "derived_spec_with_k8s.md",
        osbuilder_dir / "derived_spec.md",
    )

    # Invoke the refusal gate
    result = ih.check_refuse_list(tmp_project_root)

    # Must return True (refused)
    assert result is True, "check_refuse_list should return True for k8s spec"

    # state.md last_failure must start with "refused:"
    state_md_path = tmp_project_root / ".planning" / "osbuilder" / "state.md"
    read_result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "state_writer.py"),
         "read", "--field", "last_failure",
         "--project-root", str(tmp_project_root)],
        capture_output=True, text=True,
    )
    last_failure = read_result.stdout.strip()
    assert last_failure.startswith("refused:"), (
        f"last_failure should start with 'refused:', got: {last_failure!r}"
    )

    # stderr must contain the refusal copy mentioning "production-ready"
    captured = capsys.readouterr()
    assert "production-ready" in captured.err.lower(), (
        f"stderr refusal copy should mention 'production-ready', got: {captured.err!r}"
    )


def test_clean_spec_passes(ih, tmp_project_root, fake_state_md, monkeypatch):
    """SCL-05 (V-14 negative): spec with no refuse keywords does NOT trigger refusal — gate returns False."""
    fake_state_md(production_ready="false")

    osbuilder_dir = tmp_project_root / ".planning" / "osbuilder"
    osbuilder_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURE_DIR / "derived_spec_clean.md",
        osbuilder_dir / "derived_spec.md",
    )

    result = ih.check_refuse_list(tmp_project_root)
    assert result is False, "check_refuse_list should return False for clean spec"


def test_refusal_copy_mentions_opt_in():
    """SCL-05 (V-15): references/refuse-list.md content mentions 'production-ready' opt-in path (case-insensitive)."""
    refuse_list_md = REPO_ROOT / "references" / "refuse-list.md"
    assert refuse_list_md.exists(), f"references/refuse-list.md not found at {refuse_list_md}"
    content = refuse_list_md.read_text(encoding="utf-8")
    assert "production-ready" in content.lower(), (
        "references/refuse-list.md must mention 'production-ready' (the opt-in path)"
    )
