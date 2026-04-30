"""Tests for scripts/scaffold_dispatch.py — SCAF-01, SCAF-06.

All tests in this file FAIL or SKIP before Plans 03-04 and 03-05 land.
That is by design (TDD RED state).

`scaffold_dispatch` is imported lazily inside the `sd` fixture.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet created."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet created (Wave 1 target)")


def test_web_playbook_exists(sd):
    """SCAF-01: references/playbooks/web.md exists and contains the scaffold command."""
    playbook_path = Path(__file__).resolve().parents[2] / "references" / "playbooks" / "web.md"
    if not playbook_path.exists():
        pytest.skip("references/playbooks/web.md not yet created (Wave 2 target)")
    content = playbook_path.read_text(encoding="utf-8")
    assert "pnpm create next-app" in content, (
        "web.md must document the pnpm create next-app scaffold command (SCAF-01)"
    )
    assert "--typescript" in content, "web.md must document the --typescript flag"
    assert "--disable-git" in content, "web.md must document the --disable-git flag"
    assert "drizzle" in content.lower(), "web.md must document Drizzle wiring steps"
    assert "compose.yaml" in content, (
        "web.md must reference compose.yaml (Docker Compose v2 filename)"
    )


def test_scaffold_cmd_flags(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: scaffold_web() runs create-next-app with the correct flags and never uses --yes."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    scaffold_calls = [s for s in signatures if "next-app@latest" in s]
    assert len(scaffold_calls) == 1, (
        f"Expected exactly 1 create-next-app call, got {len(scaffold_calls)}. "
        f"All calls: {signatures}"
    )
    cmd = scaffold_calls[0]
    assert "--typescript" in cmd, "Must pass --typescript flag (SCAF-06)"
    assert "--tailwind" in cmd, "Must pass --tailwind flag (SCAF-06)"
    assert "--app" in cmd, "Must pass --app flag (App Router; SCAF-06)"
    assert "--src-dir" in cmd, "Must pass --src-dir flag (SCAF-06)"
    assert "--eslint" in cmd, "Must pass --eslint flag (SCAF-06)"
    assert "--disable-git" in cmd, "Must pass --disable-git flag (Pitfall 2 mitigation)"
    assert "--use-pnpm" in cmd, "Must pass --use-pnpm flag (SCAF-06)"
    assert "--yes" not in cmd, (
        "--yes MUST NOT be used — it reads saved machine preferences (Pitfall 1)"
    )


def test_drizzle_deps_added(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: post-scaffold installs drizzle-orm, postgres, and drizzle-kit via pnpm."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    # Also verify pnpm add commands were issued (when scaffold_dispatch does it)
    fake_shell.program("pnpm add drizzle-orm", returncode=0)
    fake_shell.program("pnpm add -D drizzle-kit", returncode=0)
    # At minimum write_drizzle_files must write the file artifacts (tested below)
    # This test specifically targets the pnpm install invocations when called via scaffold_web
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app2", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    drizzle_calls = [s for s in signatures if "drizzle" in s]
    assert len(drizzle_calls) >= 1, (
        "scaffold_web() must invoke pnpm to install drizzle-orm + drizzle-kit (SCAF-06). "
        f"All calls seen: {signatures}"
    )


def test_db_ts_written(sd, fake_which, tmp_path):
    """SCAF-06: write_drizzle_files() writes src/lib/db.ts with drizzle-orm/postgres-js import."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    db_ts = project_dir / "src" / "lib" / "db.ts"
    assert db_ts.exists(), "src/lib/db.ts must be written by write_drizzle_files() (SCAF-06)"
    content = db_ts.read_text(encoding="utf-8")
    assert "drizzle-orm/postgres-js" in content, (
        "src/lib/db.ts must import from drizzle-orm/postgres-js (RESEARCH.md Pattern 2)"
    )
    assert "process.env.DATABASE_URL" in content, (
        "src/lib/db.ts must read DATABASE_URL from environment"
    )


def test_drizzle_config_written(sd, fake_which, tmp_path):
    """SCAF-06: write_drizzle_files() writes drizzle.config.ts with postgresql dialect."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    config_ts = project_dir / "drizzle.config.ts"
    assert config_ts.exists(), "drizzle.config.ts must be written by write_drizzle_files()"
    content = config_ts.read_text(encoding="utf-8")
    assert "postgresql" in content, (
        "drizzle.config.ts must specify dialect: 'postgresql' (RESEARCH.md Pattern 2)"
    )
    assert "process.env.DATABASE_URL" in content, (
        "drizzle.config.ts must read DATABASE_URL from environment"
    )


def test_env_example_written(sd, fake_which, tmp_path):
    """SCAF-06: write_drizzle_files() writes .env.example with DATABASE_URL placeholder only."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    env_example = project_dir / ".env.example"
    assert env_example.exists(), ".env.example must be written by write_drizzle_files()"
    content = env_example.read_text(encoding="utf-8")
    assert "DATABASE_URL=" in content, ".env.example must contain DATABASE_URL= line"
    # Security: .env.example must contain only placeholder values, never real credentials
    import re
    real_secret_pattern = re.compile(
        r"DATABASE_URL=postgresql://[^:]+:[^@]{8,}@",  # real password in URL
        re.IGNORECASE,
    )
    assert not real_secret_pattern.search(content), (
        ".env.example must NOT contain real credentials — only placeholder values (T-3-04)"
    )


def test_compose_yaml_written(sd, fake_which, tmp_path):
    """SCAF-06: write_drizzle_files() writes compose.yaml (Compose v2 name — NOT docker-compose.yml)."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    assert (project_dir / "compose.yaml").exists(), (
        "Must write compose.yaml (Docker Compose v2 filename; RESEARCH.md State of the Art)"
    )
    assert not (project_dir / "docker-compose.yml").exists(), (
        "Must NOT write docker-compose.yml — deprecated Compose v1 filename"
    )
    content = (project_dir / "compose.yaml").read_text(encoding="utf-8")
    assert "postgres:18-alpine" in content, (
        "compose.yaml must use postgres:18-alpine image (pinned; RESEARCH.md Pattern 2)"
    )
