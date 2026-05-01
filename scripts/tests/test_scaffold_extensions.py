"""test_scaffold_extensions.py — Phase 6 scaffold extension tests (Wave 1 — Plan 06-02).

Tests for SHIP-03 (V-05), SHIP-04 unit (V-06), SHIP-04 integration (V-07),
and SCL-01..04 (V-09..V-13).
Locked test names (V-IDs from 06-VALIDATION.md) — DO NOT rename.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
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


@pytest.fixture
def gh():
    """Lazy import of scripts/gh_handoff.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("gh_handoff")
    except ImportError:
        pytest.skip("gh_handoff module not yet created (Wave 1 target)")


def test_gitignore_composition(gh, fake_built_app):
    """SHIP-03 (V-05): _compose_gitignore() writes .gitignore with required env + node entries."""
    gh._compose_gitignore(fake_built_app, "node")

    gitignore = fake_built_app / ".gitignore"
    assert gitignore.exists(), ".gitignore not written by _compose_gitignore()"

    content = gitignore.read_text(encoding="utf-8")
    # Required env-file blocks (from common.gitignore)
    assert ".env\n" in content, "Missing '.env' line in .gitignore"
    assert ".env.*\n" in content, "Missing '.env.*' line in .gitignore"
    assert "!.env.example\n" in content, "Missing '!.env.example' line in .gitignore"
    # node stack entries
    assert "node_modules/\n" in content, "Missing 'node_modules/' in .gitignore"
    assert "dist/\n" in content, "Missing 'dist/' in .gitignore"
    # OS/IDE cruft from common.gitignore
    assert ".DS_Store\n" in content, "Missing '.DS_Store' in .gitignore"
    assert ".vscode/\n" in content, "Missing '.vscode/' in .gitignore"

    # Idempotency: calling again must not overwrite
    gh._compose_gitignore(fake_built_app, "node")
    content2 = gitignore.read_text(encoding="utf-8")
    assert content == content2, "_compose_gitignore() is not idempotent"


def test_gitleaks_config(gh, fake_built_app):
    """SHIP-04 unit (V-06): _install_gitleaks_hook() writes .pre-commit-config.yaml (rev: v8.30.1) and .gitleaks.toml."""
    gh._install_gitleaks_hook(fake_built_app)

    pre_commit = fake_built_app / ".pre-commit-config.yaml"
    assert pre_commit.exists(), ".pre-commit-config.yaml not written"
    pre_commit_content = pre_commit.read_text(encoding="utf-8")
    assert "rev: v8.30.1" in pre_commit_content, \
        f"Expected 'rev: v8.30.1' in .pre-commit-config.yaml. Got:\n{pre_commit_content}"

    gitleaks_toml = fake_built_app / ".gitleaks.toml"
    assert gitleaks_toml.exists(), ".gitleaks.toml not written"
    toml_content = gitleaks_toml.read_text(encoding="utf-8")
    # Allowlist must contain the .env.example pattern (as a TOML raw string regex)
    assert r"\.env\.example" in toml_content, \
        f"Expected '.env.example' allowlist regex in .gitleaks.toml. Got:\n{toml_content}"


@pytest.mark.skipif(
    shutil.which("pre-commit") is None or shutil.which("gitleaks") is None,
    reason="needs pre-commit and gitleaks installed locally",
)
def test_gitleaks_blocks_real_secret(fake_built_app):
    """SHIP-04 integration (V-07): real secret commit blocked by installed gitleaks hook."""
    import gh_handoff as gh  # noqa: F401 — local import for integration test

    # Stamp the gitleaks files into the fake repo
    gh._install_gitleaks_hook(fake_built_app)

    # Install the pre-commit hook
    install_result = subprocess.run(
        ["pre-commit", "install"],
        cwd=str(fake_built_app),
        capture_output=True, text=True, shell=False,
    )
    assert install_result.returncode == 0, \
        f"pre-commit install failed: {install_result.stderr}"

    # Create a file with a fake secret (not allowlisted)
    secret_file = fake_built_app / "secrets.txt"
    secret_file.write_text("STRIPE_KEY=sk_test_abcdefghijklmnop1234567890\n", encoding="utf-8")

    # Stage the file
    subprocess.run(["git", "add", "secrets.txt"], cwd=str(fake_built_app),
                   check=True, shell=False)

    # Try to commit — gitleaks should block it
    commit_result = subprocess.run(
        ["git", "commit", "-m", "add secret"],
        cwd=str(fake_built_app),
        capture_output=True, text=True, shell=False,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "test",
             "GIT_AUTHOR_EMAIL": "test@test.com",
             "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@test.com"},
    )
    assert commit_result.returncode != 0, \
        "Expected commit to be blocked by gitleaks but it succeeded"
    output = (commit_result.stdout + commit_result.stderr).lower()
    assert "gitleaks" in output, \
        f"Expected 'gitleaks' in output but got:\n{commit_result.stdout}\n{commit_result.stderr}"


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
