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

def _resolve_project_root(arg: str | None) -> Path:
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
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


def write_drizzle_files(project_dir: Path) -> None:
    """Write ONLY 4 Drizzle + Postgres files (SCAF-06): db.ts, drizzle.config.ts, .env.example, compose.yaml."""
    atomic_write(project_dir / "src" / "lib" / "db.ts", _DB_TS)
    atomic_write(project_dir / "drizzle.config.ts", _DRIZZLE_CONFIG)
    atomic_write(project_dir / ".env.example", _ENV_EXAMPLE)
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
    write_drizzle_files(project_dir)

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


def _cmd_scaffold(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    project_dir = scaffold_web(args.project_name, project_root)

    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if state_md.exists():
        try:
            subprocess.run(
                [sys.executable, str(STATE_WRITER), "write",
                 "--field", "project_path", "--value", str(project_dir),
                 "--project-root", str(project_root)],
                shell=False, check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            pass  # state.md write failure is non-fatal

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
