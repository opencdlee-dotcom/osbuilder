"""test_scaffold_extensions.py — RED stubs for Phase 6 scaffold extensions (Wave 0 — Plan 06-01).

All tests skip("Wave 1 target") until the corresponding Wave 1 module exists.
Stub bodies are pytest.skip(...) — NOT pass, NOT assert False, NOT xfail.

Locked test names (V-IDs from 06-VALIDATION.md) — DO NOT rename in Wave 1.
"""
from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet created (Wave 1 target)")


def test_gitignore_composition(sd, fake_built_app):
    """SHIP-03 (V-05): _compose_gitignore() writes .gitignore with required env + node entries."""
    pytest.skip("Wave 1 target")


def test_gitleaks_config(sd, fake_built_app):
    """SHIP-04 unit (V-06): _install_gitleaks_hook() writes .pre-commit-config.yaml (rev: v8.30.1) and .gitleaks.toml."""
    pytest.skip("Wave 1 target")


@pytest.mark.skipif(
    shutil.which("pre-commit") is None or shutil.which("gitleaks") is None,
    reason="needs pre-commit and gitleaks installed locally",
)
def test_gitleaks_blocks_real_secret(fake_built_app):
    """SHIP-04 integration (V-07): real secret commit blocked by installed gitleaks hook."""
    pytest.skip("Wave 1 target")


def test_env_example_committed(sd, fake_built_app):
    """SCL-01 (V-09): write_drizzle_files() creates .env.example in project dir."""
    pytest.skip("Wave 1 target")


def test_pick_database(sd):
    """SCL-02 pure function (V-10): _pick_database() returns 'postgres' for web/multi-user-web, 'sqlite' for cli/single-user-cli."""
    pytest.skip("Wave 1 target")


def test_db_default_per_playbook(sd, fake_built_app, monkeypatch):
    """SCL-02 file presence (V-11): compose.yaml written for web playbook (postgres:18-alpine, no 'version:' line); skipped for cli playbook."""
    pytest.skip("Wave 1 target")


def test_docker_artifacts(sd, fake_built_app):
    """SCL-03 (V-12): web scaffold extensions produce multi-stage Dockerfile ('AS builder' + 'AS runtime') and compose.yaml (no ^version: line)."""
    pytest.skip("Wave 1 target")


def test_one_ci_workflow(sd, fake_built_app):
    """SCL-04 (V-13): web scaffold extensions produce EXACTLY one .github/workflows/*.yml with actions/checkout@v6 + pull_request trigger + pnpm/action-setup@v4 before actions/setup-node@v4."""
    pytest.skip("Wave 1 target")
