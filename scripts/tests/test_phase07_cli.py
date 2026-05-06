"""Tests for the cli playbook (SCAF-03; phase 7 plan 03).

All tests SKIP (not error) before Wave 1 of plan 07-03 lands. That is by
design (TDD RED state). `scaffold_dispatch` is imported lazily inside the
`sd` fixture; the `has_cli` fixture additionally skips when
`scaffold_cli` has not yet been added.

The 5 tests here lock in:
  - presence of the playbook spec (.md, 7 sections, ≤ 80 lines)
  - presence of the vendored cli-starter template (__main__.py.tmpl)
  - presence of the cli-starter pyproject snippet (typer dep, NO `typer[all]`)
  - subprocess argv shape of scaffold_cli (uv init --app + uv add typer)
    — Pitfall 5: rich is hard-deped since typer 0.25.1; no `[all]` extras
  - module-name sanitization: hyphens → underscores in the substituted
    Python import path (e.g., `my-cli` → `my_cli/__main__.py`)

Subprocess matchers use argv-token style ("uv init --app {name}" fragment in
the joined-signature) per STATE.md decision log.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet importable."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet cli-ready (Wave 1 target)")


@pytest.fixture
def has_cli(sd):
    """Skips the test if scaffold_cli hasn't been added yet (Wave 1 target)."""
    if not hasattr(sd, "scaffold_cli"):
        pytest.skip("scaffold_cli not yet added (Wave 1 target)")
    return sd


# ---------- 1. playbook .md presence + 7-section structure + ≤ 80 lines ----------

def test_cli_playbook_md_present():
    """SCAF-03: references/playbooks/cli.md exists with 7 mandatory sections; ≤ 80 lines."""
    playbook = REPO_ROOT / "references" / "playbooks" / "cli.md"
    if not playbook.exists():
        pytest.skip("references/playbooks/cli.md not yet created (Wave 1 target)")
    content = playbook.read_text(encoding="utf-8")
    required_headings = [
        "## What the cli playbook produces",
        "## Scaffold command",
        "## Post-scaffold files",
        "## Files OSBuilder must NOT write",
        "## Refuse list",
        "## Stack",
        "## See also",
    ]
    missing = [h for h in required_headings if h not in content]
    assert not missing, f"cli.md missing required headings: {missing}"
    line_count = len(content.splitlines())
    assert line_count <= 80, (
        f"cli.md must be ≤ 80 lines (progressive disclosure budget); got {line_count}"
    )


# ---------- 2. cli-starter __main__.py.tmpl presence + Typer/Rich/SQLite shape ----------

def test_cli_starter_main_template_present():
    """SCAF-03: assets/cli-starter/__main__.py.tmpl exists with Typer + Rich + SQLite ping."""
    tmpl = REPO_ROOT / "assets" / "cli-starter" / "__main__.py.tmpl"
    if not tmpl.exists():
        pytest.skip("assets/cli-starter/__main__.py.tmpl not yet created (Wave 1 target)")
    content = tmpl.read_text(encoding="utf-8")
    assert "import typer" in content, "template must import typer"
    assert "from rich.console import Console" in content, (
        "template must import rich.console.Console (transitive via typer 0.25.1+)"
    )
    assert "{{project_name}}" in content, (
        "template must contain the {{project_name}} placeholder for substitution"
    )
    assert "@app.command()" in content, "template must register at least one Typer command"
    assert "def ping():" in content, (
        "template must define ping() — proves SC-02 'persists state across runs'"
    )
    assert "CREATE TABLE IF NOT EXISTS pings" in content, (
        "template must create the pings SQLite table (SC-02 verification path)"
    )


# ---------- 3. cli-starter pyproject snippet present + Pitfall 5 deps ----------

def test_cli_starter_pyproject_snippet_present():
    """SCAF-03 Pitfall 5: pyproject snippet uses `typer>=0.25.1`, NOT `typer[all]`."""
    snippet = REPO_ROOT / "assets" / "cli-starter" / "pyproject.snippet.toml"
    if not snippet.exists():
        pytest.skip("assets/cli-starter/pyproject.snippet.toml not yet created (Wave 1 target)")
    content = snippet.read_text(encoding="utf-8")
    assert "typer>=0.25.1" in content, (
        "snippet must pin typer>=0.25.1 (Pitfall 5 — rich is hard-deped from 0.25.1)"
    )
    assert "[project.scripts]" in content, (
        "snippet must declare [project.scripts] entry-point"
    )
    assert "{{project_name}}" in content, (
        "snippet must contain the {{project_name}} placeholder for substitution"
    )
    assert "typer[all]" not in content, (
        "Pitfall 5: must NOT use typer[all] — rich is now a hard dep, the [all] extras "
        "is deprecated/redundant"
    )


# ---------- 4. scaffold_cli subprocess argv shape (Pitfall 5: no [all] extras) ----------

def test_scaffold_cli_subprocess_calls(has_cli, fake_shell, fake_which, tmp_path):
    """SCAF-03 D-13/D-14: scaffold_cli runs `uv init --app <name>` AND `uv add typer`.

    Pitfall 5: typer 0.25.1+ hard-deps rich >=13.8.0, so `uv add typer` (no [all] extras)
    is the correct dep — NOT `typer[all]`. Test asserts the literal `typer[all]` is
    absent from every subprocess argv to catch regressions.
    """
    sd = has_cli
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add typer", returncode=0, stdout="")
    sd.scaffold_cli("my-cli", tmp_path)

    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    init_calls = [s for s in signatures if "uv init --app my-cli" in s]
    add_calls = [s for s in signatures if "uv add typer" in s]
    assert len(init_calls) == 1, (
        f"Expected exactly 1 'uv init --app my-cli' call; got {init_calls}. "
        f"All calls: {signatures}"
    )
    assert len(add_calls) == 1, (
        f"Expected exactly 1 'uv add typer' call; got {add_calls}. "
        f"All calls: {signatures}"
    )

    # Pitfall 5 — no `typer[all]` anywhere in any subprocess argv.
    typer_all_calls = [s for s in signatures if "typer[all]" in s]
    assert not typer_all_calls, (
        f"Pitfall 5 regression: scaffold_cli used `typer[all]` somewhere — "
        f"rich is hard-deped from typer 0.25.1+, so plain `typer` is correct. "
        f"Offending calls: {typer_all_calls}"
    )


# ---------- 5. scaffold writes substituted __main__.py (hyphens → underscores) ----------

def test_scaffold_cli_writes_main_template(has_cli, fake_shell, fake_which, tmp_path):
    """SCAF-03 D-13: after mocked subprocess, project_dir/<module>/__main__.py exists with
    {{project_name}} substituted; module dir uses underscores (sanitization rule)."""
    sd = has_cli
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add typer", returncode=0, stdout="")
    sd.scaffold_cli("my-cli", tmp_path)
    # Hyphens → underscores for Python module path (sanitization rule from RESEARCH.md §07-03)
    main_py = tmp_path / "my-cli" / "my_cli" / "__main__.py"
    assert main_py.exists(), (
        f"Expected substituted __main__.py at {main_py} "
        f"(module dir = `my-cli`.replace('-', '_') = `my_cli`)"
    )
    content = main_py.read_text(encoding="utf-8")
    assert "{{project_name}}" not in content, (
        "Template substitution incomplete — {{project_name}} placeholder still present"
    )
    # APP_NAME holds the user-facing script name (with hyphens preserved per D-13)
    assert (
        'APP_NAME = "my-cli"' in content
        or 'APP_NAME = "my_cli"' in content
    ), "APP_NAME constant was not substituted from {{project_name}}"
    assert "import typer" in content, "Substituted file must still contain `import typer`"
    assert "CREATE TABLE IF NOT EXISTS pings" in content, (
        "Substituted file must still contain the SQLite ping table (SC-02 verification)"
    )


# ---------- 6. scaffold injects [project.scripts] so `uv run <name>` resolves ----------

def test_scaffold_cli_injects_project_scripts(has_cli, fake_shell, fake_which, tmp_path):
    """v1.0 HUMAN-UAT 07-2(a): generated pyproject.toml gets a [project.scripts] entry.

    Without this, `uv run my-cli --help` fails with `error: Failed to spawn:
    'my-cli' Caused by: No such file or directory (os error 2)` and the documented
    stranger-clone UAT contract for the cli playbook breaks. Seeds a uv-init-like
    pyproject.toml beforehand because the mocked `uv init --app` creates no file.
    """
    sd = has_cli
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add typer", returncode=0, stdout="")
    project_dir = tmp_path / "my-cli"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "my-cli"\nversion = "0.1.0"\n'
        'requires-python = ">=3.13"\ndependencies = []\n',
        encoding="utf-8",
    )
    sd.scaffold_cli("my-cli", tmp_path)
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" in pyproject_text, (
        "scaffold_cli must inject [project.scripts] so `uv run <name>` resolves"
    )
    assert '"my-cli" = "my_cli.__main__:app"' in pyproject_text, (
        "scaffold_cli must point the script entry at the package's app object"
    )
    # [project.scripts] alone isn't enough — uv refuses to install entry points
    # for an unpackaged project. tool.uv.package = true tells uv to install them.
    assert "[tool.uv]" in pyproject_text and "package = true" in pyproject_text, (
        "scaffold_cli must also set tool.uv.package=true so uv installs the entry points"
    )


def test_scaffold_cli_injection_is_idempotent(has_cli, fake_shell, fake_which, tmp_path):
    """Second scaffold_cli call against a project that already has [project.scripts]
    must not duplicate the table."""
    sd = has_cli
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add typer", returncode=0, stdout="")
    project_dir = tmp_path / "my-cli"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "my-cli"\nversion = "0.1.0"\n'
        'requires-python = ">=3.13"\ndependencies = []\n\n'
        '[project.scripts]\n"my-cli" = "my_cli.__main__:app"\n',
        encoding="utf-8",
    )
    sd.scaffold_cli("my-cli", tmp_path)
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert pyproject_text.count("[project.scripts]") == 1, (
        f"Idempotency broken — duplicate [project.scripts] table:\n{pyproject_text}"
    )


# ---------- 7. cli template uses @app.callback() so subcommands stay reachable ----------

def test_cli_starter_template_uses_app_callback():
    """v1.0 HUMAN-UAT 07-2(b): single-`@app.command()` collapses into the root command
    unless an `@app.callback()` is also registered. Without the callback, `python -m
    my_cli ping` fails with "Got unexpected extra argument (ping)".
    """
    tmpl = REPO_ROOT / "assets" / "cli-starter" / "__main__.py.tmpl"
    if not tmpl.exists():
        pytest.skip("cli-starter template not yet created")
    content = tmpl.read_text(encoding="utf-8")
    assert "@app.callback()" in content, (
        "cli starter template must register an @app.callback() to keep Typer in "
        "multi-command mode (otherwise `<app> ping` is interpreted as an extra "
        "positional argument when only one @app.command() is registered)"
    )
