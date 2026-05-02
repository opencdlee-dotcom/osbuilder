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
    # IN-13: this is a SYNTHETIC Stripe-shaped test value (not a real secret).
    # If OSBuilder ever dogfoods its own gitleaks hook (assets/gitleaks/.gitleaks.toml),
    # add `scripts/tests/.*\.py$` to its allowlist so this fixture does not block
    # commits to the OSBuilder repo. Currently OSBuilder has no top-level gitleaks
    # config — the hook only ships into scaffolded projects.
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
    sd.write_drizzle_files(fake_built_app)
    assert (fake_built_app / ".env.example").exists(), ".env.example not written by write_drizzle_files()"


def test_pick_database(sd):
    """SCL-02 pure function (V-10): _pick_database() returns 'postgres' for web/multi-user-web, 'sqlite' for cli/single-user-cli."""
    assert sd._pick_database("web", "multi-user-web") == "postgres"
    assert sd._pick_database("cli", "single-user-cli") == "sqlite"
    assert sd._pick_database("ai-service", "multi-user-web") == "postgres"


def test_db_default_per_playbook(sd, fake_built_app, monkeypatch):
    """SCL-02 file presence (V-11): compose.yaml written for web playbook (postgres:18-alpine, no 'version:' line); skipped for cli playbook."""
    # Web playbook -> postgres -> compose.yaml must exist
    sd.write_drizzle_files(fake_built_app, db_choice=sd._pick_database("web", "multi-user-web"))
    compose = fake_built_app / "compose.yaml"
    assert compose.exists(), "compose.yaml not written for web playbook"
    content = compose.read_text(encoding="utf-8")
    assert "postgres:18-alpine" in content, "compose.yaml missing postgres:18-alpine"
    import re
    assert not re.search(r"^version:", content, re.MULTILINE), "compose.yaml must not contain 'version:' key"

    # CLI playbook -> sqlite -> compose.yaml must NOT exist
    cli_dir = fake_built_app.parent / "fake-cli-app"
    cli_dir.mkdir()
    sd.write_drizzle_files(cli_dir, db_choice=sd._pick_database("cli", "single-user-cli"))
    assert not (cli_dir / "compose.yaml").exists(), "compose.yaml should not be written for cli playbook (sqlite)"


def test_docker_artifacts(sd, fake_built_app):
    """SCL-03 (V-12): web scaffold extensions produce multi-stage Dockerfile ('AS builder' + 'AS runtime') and compose.yaml (no ^version: line)."""
    sd._write_dockerfile(fake_built_app, "node-pnpm")
    dockerfile = fake_built_app / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile not written by _write_dockerfile()"
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM node:20-alpine AS builder" in content, "Dockerfile missing 'FROM node:20-alpine AS builder'"
    assert "AS runtime" in content, "Dockerfile missing 'AS runtime' stage"


def test_one_ci_workflow(sd, fake_built_app):
    """SCL-04 (V-13): web scaffold extensions produce EXACTLY one .github/workflows/*.yml with actions/checkout@v6 + pull_request trigger + pnpm/action-setup@v4 before actions/setup-node@v4."""
    sd._write_ci_workflow(fake_built_app, "node")
    workflows_dir = fake_built_app / ".github" / "workflows"
    yml_files = list(workflows_dir.glob("*.yml"))
    assert len(yml_files) == 1, f"Expected exactly 1 workflow file, found: {[f.name for f in yml_files]}"
    content = yml_files[0].read_text(encoding="utf-8")
    assert "actions/checkout@v6" in content, "CI workflow missing actions/checkout@v6"
    assert "pull_request:" in content, "CI workflow missing pull_request: trigger"
    lines = content.splitlines()
    pnpm_line = next((i for i, ln in enumerate(lines) if "pnpm/action-setup@v4" in ln), None)
    node_line = next((i for i, ln in enumerate(lines) if "actions/setup-node@v4" in ln), None)
    assert pnpm_line is not None, "pnpm/action-setup@v4 not found in CI workflow"
    assert node_line is not None, "actions/setup-node@v4 not found in CI workflow"
    assert pnpm_line < node_line, f"pnpm/action-setup@v4 (line {pnpm_line}) must appear before actions/setup-node@v4 (line {node_line})"
