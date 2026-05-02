#!/usr/bin/env python3
"""runbook_writer.py — OSBuilder deterministic README runbook stamper (SHIP-02).

Reads state.md fields, loads assets/readme-template.md, substitutes placeholders,
and writes README.md to the built project directory.

Pure stdlib. Subcommand: write.

Idempotent: if the target README.md already contains the OSBuilder runbook marker
(`<!-- OSBuilder runbook -->`), the writer returns without overwriting — this preserves
any subsequent edits made by `/gsd-docs-update` (Phase 5 Plan 05-05 LLM-augmented section).
"""
from __future__ import annotations

import argparse
import json
import os
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
ASSETS = REPO_ROOT / "assets"
TEMPLATE_PATH = ASSETS / "readme-template.md"

OSBUILDER_MARKER = "<!-- OSBuilder runbook -->"


# ---------- helpers (duplicated per D-05 — do NOT import from other scripts) ----------

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


def _read_state(project_root: Path) -> dict:
    """Read state.md fields via state_writer.py read --format json."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return {}
    result = subprocess.run(
        [sys.executable, str(STATE_WRITER), "read",
         "--format", "json", "--project-root", str(project_root)],
        capture_output=True, text=True, shell=False, check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


# ---------- pure helpers ----------

def _derive_commands(state: dict) -> dict[str, str]:
    """Map state.md fields to install/run/test commands per playbook.

    Defaults to Next.js + pnpm for the web playbook (Phase 3 only ships web).
    Phase 7 may extend with cli / ai-service / desktop / hub-platform.

    WR-13: refuse to write a runbook for an unknown playbook rather than
    falling back to "see README" placeholders. The previous fallback produced
    a Quick Start that runs without errors but does nothing useful, and the
    "{{" canary did not catch it. Raising SystemExit here surfaces the
    misconfiguration before README.md is written.
    """
    playbook = (state.get("playbook") or "web").lower()
    if playbook == "web":
        return {
            "install_command": "pnpm install",
            "run_command": "pnpm dev",
            "test_command": "pnpm test",
            "stack_summary": "Next.js + Drizzle + Postgres + Tailwind + pnpm",
        }
    if playbook == "cli":
        return {
            "install_command": "uv sync",
            "run_command": "uv run my-cli --help",
            "test_command": "uv run pytest",
            "stack_summary": "Python + Typer + Rich + SQLite",
        }
    if playbook == "ai-service":
        return {
            "install_command": "uv sync",
            "run_command": "uv run fastapi dev",
            "test_command": "uv run pytest",
            "stack_summary": "FastAPI + uv + Pydantic v2",
        }
    raise SystemExit(
        f"OSBuilder: runbook_writer does not know playbook={playbook!r}. "
        "Add a branch to _derive_commands or set state.playbook to a known "
        "value (web, cli, ai-service)."
    )


# ---------- public API ----------

def write_readme(project_dir: Path, project_root: Path) -> Path:
    """SHIP-02: stamp README.md from assets/readme-template.md with state.md substitutions.

    Idempotent: if README.md already contains OSBUILDER_MARKER, return without rewriting.
    """
    target = project_dir / "README.md"
    # Idempotency check
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if OSBUILDER_MARKER in existing:
            return target

    # Read template
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"OSBuilder: readme template missing at {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Read state.md
    state = _read_state(project_root)
    cmds = _derive_commands(state)

    # Derive project_name from project_path basename (or fall back to project_dir.name)
    project_path = state.get("project_path") or str(project_dir)
    project_name = Path(project_path).name or "your-app"

    # Repo URL fallback
    repo_url = state.get("repo_url") or "(repo URL will appear after ship)"

    # Substitution map — close set of placeholders defined in template
    subs = {
        "{{project_name}}": project_name,
        "{{stack_summary}}": cmds["stack_summary"],
        "{{install_command}}": cmds["install_command"],
        "{{run_command}}": cmds["run_command"],
        "{{test_command}}": cmds["test_command"],
        "{{repo_url}}": repo_url,
        "{{playbook}}": (state.get("playbook") or "web"),
    }

    composed = template
    for key, value in subs.items():
        composed = composed.replace(key, value)

    # Sanity: refuse to write a README with leftover OSBuilder placeholders.
    # WR-03: only check the known-placeholder set so a user goal that legitimately
    # contains "{{" (e.g. Jinja-like example syntax) does not trip the canary.
    leftover = [key for key in subs if key in composed]
    if leftover:
        raise SystemExit(
            "OSBuilder: readme template has unsubstituted placeholders: "
            f"{', '.join(sorted(leftover))}. "
            "Update _derive_commands or assets/readme-template.md."
        )

    atomic_write(target, composed)
    return target


# ---------- CLI ----------

def _cmd_write(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    project_dir = project_root / args.project_name
    if not project_dir.is_dir():
        sys.stderr.write(f"OSBuilder: project_dir does not exist: {project_dir}\n")
        return 1
    try:
        path = write_readme(project_dir, project_root)
    except SystemExit:
        raise
    except Exception as e:
        if _fe is not None:
            msg = _fe.translate(str(e), ctx={"tool": "runbook_writer"})
            sys.stderr.write(
                f"## {msg.title}\n{msg.what_broke}\n\n**What to do:** {msg.what_to_do}\n"
            )
        else:
            sys.stderr.write(f"OSBuilder: runbook_writer failed: {e}\n")
        return 1
    print(str(path))
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="runbook_writer",
        description="OSBuilder deterministic README runbook stamper (SHIP-02).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_write = sub.add_parser("write", help="Stamp README.md in the built project directory.")
    p_write.add_argument("--project-name", required=True, dest="project_name")
    p_write.add_argument("--project-root", default=None, dest="project_root")
    p_write.set_defaults(func=_cmd_write)
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
