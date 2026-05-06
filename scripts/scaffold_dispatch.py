#!/usr/bin/env python3
"""scaffold_dispatch.py — OSBuilder web playbook scaffold dispatcher (SCAF-01, SCAF-06).

Pure stdlib. Subcommands: scaffold.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Phase 5: friendly-error translation layer (graceful degrade if module not yet built)
try:
    import friendly_error as _fe
except ImportError:
    _fe = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"

# Post-scaffold file contents (verbatim from RESEARCH.md Pattern 2)
_DB_TS = """\
// src/lib/db.ts — written post-scaffold by scaffold_dispatch.py
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

const queryClient = postgres(process.env.DATABASE_URL!);
export const db = drizzle({ client: queryClient });
"""

_DRIZZLE_CONFIG = """\
// drizzle.config.ts — written post-scaffold by scaffold_dispatch.py
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
"""

# _ENV_EXAMPLE: DATABASE_URL uses password "myapp" (5 chars) — placeholder only (T-3-04)
_ENV_EXAMPLE = "DATABASE_URL=postgresql://myapp:myapp@localhost:5432/myapp\n"

# _COMPOSE_YAML: POSTGRES_PASSWORD uses "myapp_secret" — dev-only placeholder (T-3-04)
_COMPOSE_YAML = """\
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: myapp_secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

# Phase 6 — assets directory for Dockerfile + CI workflow templates (SCL-03, SCL-04)
ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Phase 7 — ai-service playbook (07-02) vendored starter location
_FASTAPI_STARTER = ASSETS / "fastapi-starter"

# Phase 7 — cli playbook (07-03) vendored starter location
_CLI_STARTER = ASSETS / "cli-starter"


def _pick_database(playbook: str, app_type: str) -> str:
    """SCL-02: deterministic Postgres-vs-SQLite choice.

    Web (multi-user) → postgres; CLI (single-user) → sqlite; AI-service → postgres.
    Pure function: deterministic, testable; no I/O.
    """
    pb = (playbook or "").lower()
    at = (app_type or "").lower()
    if pb == "web":
        return "postgres"
    if pb == "cli":
        return "sqlite"
    if pb == "ai-service":
        return "postgres"
    # Default by app_type when playbook is unknown
    if "single-user" in at:
        return "sqlite"
    return "postgres"


def _write_dockerfile(project_dir: Path, stack_family: str) -> None:
    """SCL-03: stamp a multi-stage Dockerfile from assets/dockerfiles/<family>.Dockerfile.tmpl.

    stack_family: "node-pnpm" or "python-uv".
    """
    src = ASSETS / "dockerfiles" / f"{stack_family}.Dockerfile.tmpl"
    if not src.exists():
        return  # silently no-op for unsupported stacks (Phase 7 may add desktop, etc.)
    content = src.read_text(encoding="utf-8")
    atomic_write(project_dir / "Dockerfile", content)


def _write_ci_workflow(project_dir: Path, stack_family: str) -> None:
    """SCL-04: stamp EXACTLY ONE GitHub Actions workflow at .github/workflows/ci.yml.

    stack_family: "node" or "python" (matches assets/ci-workflows/<family>.yml.tmpl).
    """
    src = ASSETS / "ci-workflows" / f"{stack_family}.yml.tmpl"
    if not src.exists():
        return
    content = src.read_text(encoding="utf-8")
    target = project_dir / ".github" / "workflows" / "ci.yml"
    atomic_write(target, content)


def _resolve_project_root(arg: str | None) -> Path:
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if any(part == ".." for part in Path(arg).parts):
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


def atomic_write(path: Path, content: str) -> None:
    """Atomic file write via os.replace (atomic on POSIX + Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.stem}.{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _validate_project_name(name: str) -> None:
    """T-3-01: reject path traversal and shell-unsafe chars in project_name."""
    if not name:
        raise SystemExit("OSBuilder: project_name cannot be empty.")
    if ".." in name:
        raise SystemExit("OSBuilder: project_name cannot contain '..' (path traversal).")
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise SystemExit("OSBuilder: project_name must contain only [a-zA-Z0-9_-] characters.")


_PNPM_VERSION = "10.33.2"  # keep in sync with stack-menu.md and _WEB_DEFAULTS


def ensure_pnpm() -> None:
    """Install pnpm via npm if absent (Pitfall 5 mitigation)."""
    if shutil.which("pnpm") is not None:
        return
    subprocess.run(
        ["npm", "install", "-g", f"pnpm@{_PNPM_VERSION}"],
        shell=False, check=True,
    )


# === Phase 7 — ai-service playbook (07-02) ===

def ensure_uv() -> None:
    """Install uv via official installer if absent (D-20 fallback safety net).

    Preflight is the primary install path; this is a per-scaffold guard for
    environments where the user skipped preflight. Mirrors ensure_pnpm shape.
    """
    if shutil.which("uv") is not None:
        return
    # Use the curl-pipe-sh installer on Unix; on Windows, raise a SystemExit
    # pointing at preflight (winget needs admin/UAC and is not safe from a
    # scaffold call). T-07-02-06 mitigation.
    if os.name == "nt":
        sys.stderr.write(
            "OSBuilder: uv is not installed. Run preflight first:\n"
            "  python3 scripts/preflight_check.py install\n"
        )
        raise SystemExit(1)
    subprocess.run(
        ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
        shell=False, check=True,
    )


def write_drizzle_files(project_dir: Path, *, db_choice: str = "postgres") -> None:
    """Write Drizzle + (conditionally) Postgres files post-scaffold (SCAF-06, SCL-02).

    db_choice: "postgres" → also writes compose.yaml. "sqlite" → skips compose.yaml.
    Default keeps Phase 3 behavior (postgres) so existing test_db_ts_written + test_compose_yaml_written keep passing.
    """
    atomic_write(project_dir / "src" / "lib" / "db.ts", _DB_TS)
    atomic_write(project_dir / "drizzle.config.ts", _DRIZZLE_CONFIG)
    atomic_write(project_dir / ".env.example", _ENV_EXAMPLE)
    if db_choice == "postgres":
        atomic_write(project_dir / "compose.yaml", _COMPOSE_YAML)


def scaffold_web(project_name: str, project_root: Path) -> Path:
    """Validate name, ensure pnpm, run create-next-app, write Drizzle files. Returns project_dir."""
    _validate_project_name(project_name)
    ensure_pnpm()

    cmd = [
        "pnpm", "create", "next-app@latest", project_name,
        "--typescript", "--tailwind", "--app", "--src-dir",
        "--eslint", "--use-pnpm", "--disable-git",
        "--import-alias", "@/*",
    ]
    try:
        subprocess.run(
            cmd, cwd=str(project_root), check=True,
            capture_output=True, text=True, shell=False,
        )
    except (FileNotFoundError, OSError) as e:
        _raw = f"pnpm: command not found: {e}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "pnpm"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: scaffold failed — pnpm not found: {e}\n")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        _raw = (e.stderr or "").strip() or f"exit {e.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: create-next-app exited {e.returncode}\n{e.stderr}\n")
        raise SystemExit(1)

    project_dir = project_root / project_name
    # Phase 6 — derive db choice from playbook (web is multi-user by default)
    db_choice = _pick_database("web", "multi-user-web")
    write_drizzle_files(project_dir, db_choice=db_choice)
    # Phase 6 — stamp Dockerfile + CI workflow (SCL-03, SCL-04)
    _write_dockerfile(project_dir, stack_family="node-pnpm")
    _write_ci_workflow(project_dir, stack_family="node")

    result = subprocess.run(
        ["pnpm", "add", "drizzle-orm", "postgres"],
        cwd=str(project_dir), shell=False, check=False,
    )
    if result.returncode != 0:
        _raw = f"pnpm add drizzle-orm postgres failed exit {result.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"project_dir": str(project_dir)})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do} Run manually in {project_dir}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(
                f"OSBuilder: warning — pnpm add drizzle-orm postgres failed "
                f"(exit {result.returncode}). Run manually in {project_dir}\n"
            )

    result = subprocess.run(
        ["pnpm", "add", "-D", "drizzle-kit"],
        cwd=str(project_dir), shell=False, check=False,
    )
    if result.returncode != 0:
        _raw = f"pnpm add -D drizzle-kit failed exit {result.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"project_dir": str(project_dir)})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do} Run manually in {project_dir}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(
                f"OSBuilder: warning — pnpm add -D drizzle-kit failed "
                f"(exit {result.returncode}). Run manually in {project_dir}\n"
            )
    return project_dir


def scaffold_ai_service(project_name: str, project_root: Path) -> Path:
    """SCAF-02: scaffold a FastAPI + uv + Pydantic v2 ai-service project.

    4-step shape (mirrors scaffold_web verbatim per RESEARCH.md §Pattern 1):
      1. _validate_project_name (security gate — T-07-02-01)
      2. ensure_uv             (D-20 fallback if preflight skipped)
      3. subprocess.run uv init --app, then uv add 'fastapi[standard]'
      4. atomic_write of starter main.py + Dockerfile + CI workflow
    """
    _validate_project_name(project_name)
    ensure_uv()

    cmd = ["uv", "init", "--app", project_name]
    try:
        subprocess.run(
            cmd, cwd=str(project_root), check=True,
            capture_output=True, text=True, shell=False,
        )
    except (FileNotFoundError, OSError) as e:
        _raw = f"uv: command not found: {e}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "uv"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: scaffold failed — uv not found: {e}\n")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        _raw = (e.stderr or "").strip() or f"exit {e.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: uv init exited {e.returncode}\n{e.stderr}\n")
        raise SystemExit(1)

    project_dir = project_root / project_name
    # Post-scaffold: copy vendored starter main.py
    atomic_write(
        project_dir / "main.py",
        (_FASTAPI_STARTER / "main.py").read_text(encoding="utf-8"),
    )
    # Add fastapi[standard] — single-string element preserves the brackets
    # as one argv token (Pitfall 2 — quoting is meaningless when shell=False).
    result = subprocess.run(
        ["uv", "add", "fastapi[standard]"],
        cwd=str(project_dir), shell=False, check=False,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        _raw = (result.stderr or "").strip() or f"uv add fastapi[standard] exit {result.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "uv"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do} Run manually in {project_dir}\n"
            )
        else:
            sys.stderr.write(
                f"OSBuilder: warning — uv add fastapi[standard] failed "
                f"(exit {result.returncode}). Run manually in {project_dir}\n"
            )
    # Phase 6 — stamp Dockerfile + CI workflow (SCL-03, SCL-04, SHIP-03)
    _write_dockerfile(project_dir, stack_family="python-uv")
    _write_ci_workflow(project_dir, stack_family="python")
    return project_dir


# === Phase 7 — cli playbook (07-03) ===

def _sanitize_module_name(name: str) -> str:
    """Hyphens → underscores for Python import path. Script name keeps hyphens.

    The user-facing script name (e.g. `my-cli`) keeps hyphens so `uv run my-cli`
    works as expected. The Python module dir under it must use underscores
    (`my_cli/__main__.py`) because hyphens are not valid in Python identifiers.
    Reused for the SQLite path under `Path.home()` to avoid mixed-form dirs.
    """
    return name.replace("-", "_")


def _inject_cli_scripts_entry(pyproject_path: Path, project_name: str, module_name: str) -> None:
    """Append [project.scripts] + [tool.uv] package=true to a uv-generated pyproject.toml.

    `uv init --app` produces a pyproject.toml with [project] and dependencies, but
    it does NOT register an entry-point table. Without [project.scripts] +
    `tool.uv.package = true`, `uv run <project_name>` resolves to nothing
    (uv prints "Skipping installation of entry points... because this project is
    not packaged" then "Failed to spawn: <name>"). Both tables are required for
    the documented `uv run <app> --help` UAT contract.

    Idempotent: skips each table independently if already present.
    """
    existing = pyproject_path.read_text(encoding="utf-8")
    addition = ""
    if "[project.scripts]" not in existing:
        addition += (
            f'\n[project.scripts]\n'
            f'"{project_name}" = "{module_name}.__main__:app"\n'
        )
    if "[tool.uv]" not in existing:
        addition += '\n[tool.uv]\npackage = true\n'
    if not addition:
        return
    pyproject_path.write_text(existing.rstrip() + "\n" + addition, encoding="utf-8")


def scaffold_cli(project_name: str, project_root: Path) -> Path:
    """SCAF-03: scaffold a Python + Typer + Rich + SQLite CLI project.

    4-step shape (mirrors scaffold_web verbatim per RESEARCH.md §Pattern 1):
      1. _validate_project_name (security gate — T-07-03-01)
      2. ensure_uv             (D-20 fallback if preflight skipped)
      3. subprocess.run uv init --app, then uv add typer
         (Pitfall 5: rich is hard-deped from typer 0.25.1+; NO `typer[all]`)
      4. atomic_write of substituted __main__.py.tmpl into
         project_dir/<sanitized-module>/__main__.py
    """
    _validate_project_name(project_name)
    ensure_uv()

    cmd = ["uv", "init", "--app", project_name]
    try:
        subprocess.run(
            cmd, cwd=str(project_root), check=True,
            capture_output=True, text=True, shell=False,
        )
    except (FileNotFoundError, OSError) as e:
        _raw = f"uv: command not found: {e}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "uv"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: scaffold failed — uv not found: {e}\n")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        _raw = (e.stderr or "").strip() or f"exit {e.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: uv init exited {e.returncode}\n{e.stderr}\n")
        raise SystemExit(1)

    project_dir = project_root / project_name
    module_name = _sanitize_module_name(project_name)
    # Substitute the {{project_name}} placeholder and write the main module.
    tmpl = (_CLI_STARTER / "__main__.py.tmpl").read_text(encoding="utf-8")
    rendered_main = tmpl.replace("{{project_name}}", project_name)
    atomic_write(project_dir / module_name / "__main__.py", rendered_main)
    # Inject [project.scripts] entry so `uv run <project_name>` resolves.
    # uv init --app does not produce a scripts table; without this, the
    # documented `uv run <app-name> --help` UAT contract fails.
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        _inject_cli_scripts_entry(pyproject_path, project_name, module_name)
    # Add typer dep — rich is transitive (Pitfall 5: NO `typer[all]`).
    result = subprocess.run(
        ["uv", "add", "typer"],
        cwd=str(project_dir), shell=False, check=False,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        _raw = (result.stderr or "").strip() or f"uv add typer exit {result.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "uv"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do} Run manually in {project_dir}\n"
            )
        else:
            sys.stderr.write(
                f"OSBuilder: warning — uv add typer failed "
                f"(exit {result.returncode}). Run manually in {project_dir}\n"
            )
    # CLI ships no Dockerfile (single-user local tool per RESEARCH.md §07-03).
    _write_ci_workflow(project_dir, stack_family="python")
    return project_dir


# === Phase 7 — desktop playbook (07-04) ===

_CREATE_TAURI_APP_VERSION = "4.6.2"  # pinned per D-08; verified npm 2026-05-01
_TAURI_VERSION = "2"


def _build_tauri_identifier(name: str) -> str:
    """Pitfall 7: reverse-DNS identifier required by Tauri bundler.

    Tauri requires `--identifier` in reverse-DNS form (e.g. com.osbuilder.<sanitized>).
    Sanitization rule: lowercase + remove all non-alphanumeric chars (which strips
    hyphens, underscores, dots and any other separator). Output is therefore always
    a valid bundle identifier component.

    Examples:
      _build_tauri_identifier("my-cool-app") -> "com.osbuilder.mycoolapp"
      _build_tauri_identifier("My_App-2")    -> "com.osbuilder.myapp2"
    """
    sanitized = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return f"com.osbuilder.{sanitized}"


def scaffold_desktop(project_name: str, project_root: Path) -> Path:
    """SCAF-04: scaffold a Tauri 2 (Vite + React + Rust) desktop project (D-07..D-09).

    4-step shape (mirrors scaffold_web verbatim):
      1. _validate_project_name (security gate — T-07-04-01)
      2. ensure_pnpm            (Pitfall 1: pnpm forwards --template cleanly;
                                 npm requires `--` to separate flags)
      3. subprocess.run pnpm create tauri-app@latest with verbatim 12-element
         argv (D-07: --manager pnpm --template react-ts --identifier <reverse-dns>
         --tauri-version 2 -y; verified by npx --yes create-tauri-app --help 2026-05-01)
      4. _write_ci_workflow with stack_family="tauri" (Rust+Node combined,
         dtolnay/rust-toolchain action; assets/ci-workflows/tauri.yml.tmpl)

    NO Dockerfile (desktop ships build artifacts, not a container).
    NO post-scaffold writes — Tauri owns the template per D-08.
    """
    _validate_project_name(project_name)
    ensure_pnpm()  # Pitfall 1 — must run BEFORE create-tauri-app

    identifier = _build_tauri_identifier(project_name)
    cmd = [
        "pnpm", "create", "tauri-app@latest", project_name,
        "--manager", "pnpm",
        "--template", "react-ts",
        "--identifier", identifier,
        "--tauri-version", _TAURI_VERSION,
        "-y",
    ]
    # NOTE: tauri-app@latest pins the spec but resolves to current pnpm registry
    # state at scaffold time. D-08 accepts this drift; the playbook .md documents
    # the version pin (4.6.2 as of 2026-05-01). To pin literally, replace the
    # third argv element with f"tauri-app@{_CREATE_TAURI_APP_VERSION}".
    try:
        subprocess.run(
            cmd, cwd=str(project_root), check=True,
            capture_output=True, text=True, shell=False,
        )
    except (FileNotFoundError, OSError) as e:
        _raw = f"pnpm: command not found: {e}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={"tool": "pnpm"})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: scaffold failed — pnpm not found: {e}\n")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        _raw = (e.stderr or "").strip() or f"create-tauri-app exit {e.returncode}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(
                f"OSBuilder: create-tauri-app exited {e.returncode}\n{e.stderr}\n"
            )
        raise SystemExit(1)

    project_dir = project_root / project_name
    # NO Dockerfile (desktop ships build artifacts, not a container).
    # NO post-scaffold writes (Tauri owns the template per D-08).
    _write_ci_workflow(project_dir, stack_family="tauri")
    return project_dir


# === Phase 7 — hub-platform playbook (07-05) ===
_HUB_TEMPLATE = ASSETS / "hub-template"


def scaffold_hub(project_name: str, project_root: Path, *, subtools: "list[str]") -> Path:
    """SCAF-05: scaffold a hub-platform workspace (D-04..D-06; Pattern 4 — pure file-stamping).

    Differs from scaffold_web/_ai_service/_cli/_desktop:
    - NO subprocess (no external scaffolder exists for hub workspaces)
    - NO Dockerfile (hub is a workspace, not an app)
    - NO CI workflow (hub is a workspace, not an app)
    - NO _pick_database (hub doesn't ship a DB)
    - YES validates every subtool name (subtools go on disk too — T-07-05-01)
    """
    _validate_project_name(project_name)
    if not subtools:
        sys.stderr.write(
            "OSBuilder: hub-platform scaffold requires at least one sub-tool name.\n"
            "Re-run intake or pass --subtool flags.\n"
        )
        raise SystemExit(1)
    for sub in subtools:
        _validate_project_name(sub)

    project_dir = project_root / project_name
    # Idempotent: re-running with the same project_name does not crash. The
    # earlier exist_ok=False raised FileExistsError that fell through to the
    # bare-Exception handler in main() with no friendly translation. Honor
    # the same atomic_write contract used elsewhere — if files exist, they
    # are overwritten via os.replace; the directory itself is fine to reuse.
    project_dir.mkdir(parents=True, exist_ok=True)

    # Top-level CLAUDE.md — substitute {{routing_table}} with N rows.
    # Skill cells default to "TBD" (not "n/a") so the user can see at a glance
    # which rows still need a Claude-Code-skill assignment after scaffolding.
    template = (_HUB_TEMPLATE / "CLAUDE.md.tmpl").read_text(encoding="utf-8")
    claude_rows = "\n".join(
        f"| `{s}/` | TODO — describe {s} | TBD |" for s in subtools
    )
    rendered = template.replace("{{routing_table}}", claude_rows).replace(
        "{{project_name}}", project_name
    )
    atomic_write(project_dir / "CLAUDE.md", rendered)

    # Top-level AGENTS.md — same shape but Runtime column instead of Key Skill,
    # mirroring Professor Hub's parallel CLAUDE.md/AGENTS.md split so non-Claude
    # agents (Codex, Cursor, etc.) have a router too.
    agents_tmpl_path = _HUB_TEMPLATE / "AGENTS.md.tmpl"
    if agents_tmpl_path.exists():
        agents_template = agents_tmpl_path.read_text(encoding="utf-8")
        agents_rows = "\n".join(
            f"| `{s}/` | TODO — describe {s} | TBD |" for s in subtools
        )
        agents_rendered = agents_template.replace(
            "{{routing_table}}", agents_rows
        ).replace("{{project_name}}", project_name)
        atomic_write(project_dir / "AGENTS.md", agents_rendered)

    # Per-subtool placeholder dirs + CLAUDE.md.
    sub_template = (_HUB_TEMPLATE / "subtool-CLAUDE.md.tmpl").read_text(encoding="utf-8")
    for s in subtools:
        atomic_write(
            project_dir / s / "CLAUDE.md",
            sub_template.replace("{{subtool}}", s),
        )
    return project_dir


# Phase 7 — multi-playbook dispatch (extended in 07-03, then 07-04, then 07-05)
_PLAYBOOK_DISPATCH = {
    "web":          scaffold_web,
    "ai-service":   scaffold_ai_service,
    "cli":          scaffold_cli,
    "desktop":      scaffold_desktop,
    "hub-platform": scaffold_hub,
}


def _cmd_scaffold(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    scaffold_fn = _PLAYBOOK_DISPATCH.get(args.playbook, scaffold_web)
    # Phase 7 (07-05): hub-platform takes a subtools kwarg; other playbooks
    # use the standard (project_name, project_root) signature.
    if args.playbook == "hub-platform":
        subtools = list(getattr(args, "subtool", None) or [])
        if not subtools:
            # Fallback: read subtools from state.md (comma-separated string).
            state_md = project_root / ".planning" / "osbuilder" / "state.md"
            if state_md.exists():
                try:
                    r = subprocess.run(
                        [sys.executable, str(STATE_WRITER), "read",
                         "--field", "subtools", "--project-root", str(project_root)],
                        capture_output=True, text=True, shell=False, check=False,
                    )
                    raw = (r.stdout or "").strip()
                    if raw:
                        subtools = [s.strip() for s in raw.split(",") if s.strip()]
                except (OSError, subprocess.CalledProcessError):
                    pass
        project_dir = scaffold_fn(args.project_name, project_root, subtools=subtools)
    else:
        project_dir = scaffold_fn(args.project_name, project_root)

    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if state_md.exists():
        try:
            subprocess.run(
                [sys.executable, str(STATE_WRITER), "write",
                 "--field", "project_path", "--value", str(project_dir),
                 "--project-root", str(project_root)],
                shell=False, check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            # WR-12: state.md write failure is non-fatal here, but downstream
            # ship/runbook steps read project_path and will fail confusingly if
            # it is missing. Surface a stderr warning so the silent persistence
            # failure is at least visible to the user.
            sys.stderr.write(
                "OSBuilder: warning — failed to record project_path in state.md "
                f"({type(exc).__name__}: {exc}). Downstream ship/runbook steps "
                "may need --project-path supplied manually.\n"
            )

    print(f"Scaffolded project at: {project_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="scaffold_dispatch",
        description="OSBuilder web playbook scaffold dispatcher.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scaffold = sub.add_parser("scaffold", help="run create-next-app + Drizzle wiring")
    p_scaffold.add_argument("--project-name", required=True, dest="project_name")
    p_scaffold.add_argument("--project-root", default=None, dest="project_root")
    p_scaffold.add_argument("--playbook", default="web")
    # Phase 7 (07-05): hub-platform sub-tool list. Multi-value (nargs="+") for
    # non-interactive driver invocations. When omitted, _cmd_scaffold falls back
    # to reading the comma-separated `subtools` field from state.md.
    p_scaffold.add_argument(
        "--subtool", action="append", default=[],
        help="(hub-platform only) sub-tool name; pass multiple times for multiple subtools",
    )
    p_scaffold.set_defaults(func=_cmd_scaffold)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
