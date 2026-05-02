#!/usr/bin/env python3
"""production_phase_writer.py — OSBuilder --production-ready slash-command emitter (SCL-06).

When state.md production_ready=='true', emits 7 hardcoded `/gsd-add-phase <name>` slash
commands to stdout (one per named upgrade). When production_ready != 'true', emits zero
lines.

Pure stdlib. Subcommand: emit.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"

# Locked decision: 7 named upgrades for `--production-ready` (RESEARCH lines 290-296)
NAMED_UPGRADES = (
    "observability",       # logs/metrics/traces via OpenTelemetry
    "migrations",          # automated migrations via Drizzle Kit / Alembic
    "healthchecks",        # /healthz endpoints
    "secret-manager",      # secret manager integration
    "sentry",              # Sentry error tracking
    "rate-limiting",       # rate limiting middleware
    "backups",             # backup strategy
)


# ---------- helpers (D-05 verbatim duplicates) ----------

def _resolve_project_root(arg: str | None) -> Path:
    """Resolve --project-root to an absolute Path; auto-detect if omitted."""
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


def _read_state(project_root: Path) -> dict:
    """Read state.md as JSON dict via state_writer read subcommand (D-05 duplicate)."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return {}
    result = subprocess.run(
        [sys.executable, str(STATE_WRITER), "read", "--format", "json",
         "--project-root", str(project_root)],
        capture_output=True, text=True, shell=False, check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


# ---------- public API ----------

def _existing_roadmap_phases(project_root: Path) -> set[str]:
    """WR-11: read .planning/ROADMAP.md and return the set of upgrade names already present.

    Looks for upgrades by simple substring match — gsd-add-phase normalises
    phase titles when it writes ROADMAP.md so an exact regex would be brittle
    across versions. We only need to skip emission, not parse the roadmap
    perfectly; if the substring check misses, gsd-add-phase's own idempotency
    is the backstop.
    """
    roadmap = project_root / ".planning" / "ROADMAP.md"
    if not roadmap.exists():
        return set()
    try:
        text = roadmap.read_text(encoding="utf-8").lower()
    except OSError:
        return set()
    return {name for name in NAMED_UPGRADES if name.lower() in text}


def emit(project_root: Path) -> int:
    """SCL-06: emit /gsd-add-phase commands to stdout per state.md production_ready flag.

    Returns 0 always — emission is opportunistic; absence is the default.

    WR-11: skip upgrade names already present in .planning/ROADMAP.md so
    re-running on a project that already added some upgrades does not emit
    duplicate /gsd-add-phase requests.
    """
    state = _read_state(project_root)
    if state.get("production_ready", "false") != "true":
        return 0
    already_present = _existing_roadmap_phases(project_root)
    for name in NAMED_UPGRADES:
        if name in already_present:
            continue
        print(f"/gsd-add-phase {name}")
    return 0


# ---------- CLI ----------

def _cmd_emit(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    return emit(project_root)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="production_phase_writer",
        description="OSBuilder production-ready slash-command emitter (SCL-06).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_emit = sub.add_parser("emit",
                            help="Emit /gsd-add-phase lines when production_ready=true.")
    p_emit.add_argument("--project-root", default=None, dest="project_root")
    p_emit.set_defaults(func=_cmd_emit)
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
