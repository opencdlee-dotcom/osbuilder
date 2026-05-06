#!/usr/bin/env python3
"""state_writer.py — OSBuilder's state.md checkpoint manager.

Persists 10 named fields across `/clear` and context compaction:
  goal, app_type, playbook, current_role, current_phase, phase_step,
  last_failure, retry_count, escalation_level, next_action

Format: pure markdown `key: value` lines. Atomic writes via os.replace().
Pure stdlib — no third-party deps.

Subcommands:
  init      Create state.md with all 10 fields.
  write     Set one field's value.
  read      Print fields (plain or --format json).
  bump      Increment a counter field (retry_count, escalation_level, phase_step).
  validate  Exit non-zero if state.md is missing required fields.

`--project-root PATH` accepted before or after the subcommand.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
)
COUNTER_FIELDS = ("retry_count", "escalation_level", "phase_step")
# Phase 3 fields: optional (ALLOWED but not REQUIRED) so Phase 1/2 state files
# continue to pass `validate` without these fields present.
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    "project_path",    # absolute path to scaffolded project on disk
    "stack_choices",   # JSON string: researched/confirmed stack (RES-02)
    "stack_overrides", # JSON string: --advanced user overrides (RES-04)
    # Phase 4 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3)
    "gsd_phase_count",    # total phases discovered from GSD ROADMAP.md
    "failure_class",      # last classified failure class for resume
    "escalation_log",     # JSON array of escalation steps taken
    # Phase 5 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3/4)
    "mode",             # "beginner" | "advanced"
    "tutor_enabled",    # "true" | "false" — set to "false" by --quiet
    "humanizer_score",  # int (count of critical issues) | "skipped" | "0"
    "build_log_path",   # absolute path to .planning/osbuilder/build.log
    "tech_writer_sub_step",  # "" | "awaiting-humanizer" | "done" — Plan 05-05
    # Phase 6 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3/4/5)
    "repo_visibility",       # "PRIVATE" | "PUBLIC" — set by gh_handoff.py after gh repo view
    "repo_url",              # SSH URL of created GitHub repo — set by gh_handoff.py
    "gh_auth_status",        # "ok" | "drift" | "expired" | "unauthenticated" — set by gh_handoff.py preflight
    "pre_commit_installed",  # "true" | "false" — set true after gh_handoff.py stamps .pre-commit-config.yaml
    "production_ready",      # "true" | "false" — gates production_phase_writer.py emission
    # Phase 7 (07-05): subtools — comma-separated list for hub-platform builds (additive, not required).
    "subtools",
}


# ---------- input validation (V5/V12 mitigations) ----------

def _check_field_allowed(field: str) -> None:
    """V5 allowlist enforcement (defense-in-depth: cheap check, fail fast)."""
    if field not in ALLOWED_FIELDS:
        raise SystemExit(
            f"OSBuilder: unknown field '{field}'. Allowed fields: "
            + ", ".join(sorted(ALLOWED_FIELDS))
        )


def _check_value_safe(value: str) -> None:
    """V5 input + V12 path-traversal: reject newlines and `..` in --value."""
    if "\n" in value or "\r" in value:
        raise SystemExit("OSBuilder: --value cannot contain newline characters.")
    if ".." in value:
        raise SystemExit("OSBuilder: --value cannot contain '..' (path traversal).")


def _resolve_project_root(arg: str | None) -> Path:
    """Resolve --project-root to an absolute Path; auto-detect if omitted."""
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if any(part == ".." for part in Path(arg).parts):
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


def _state_md_path(project_root: Path) -> Path:
    return project_root / ".planning" / "osbuilder" / "state.md"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- core read/write ----------

def render_state_md(fields: dict) -> str:
    """Render state.md. Writes required fields first, then any extra allowed fields."""
    lines = ["# OSBuilder State", ""]
    for f in REQUIRED_FIELDS:
        lines.append(f"{f}: {fields.get(f, '')}")
    # Persist optional allowed fields so sequential writes don't erase each other
    extras = sorted(ALLOWED_FIELDS - set(REQUIRED_FIELDS))
    for f in extras:
        if f in fields:
            lines.append(f"{f}: {fields[f]}")
    lines.append(f"updated_at: {fields.get('updated_at', _now_iso())}")
    return "\n".join(lines) + "\n"


def parse_state_md(content: str) -> dict:
    """Parse 'key: value' lines. Tolerant — ignores comments/blanks/non-kv lines."""
    out: dict[str, str] = {}
    for raw in content.splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, _, v = s.partition(":")
        out[k.strip()] = v.strip()
    return out


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


def write_state(path: Path, fields: dict) -> None:
    """Render and atomically write state.md from a fields dict."""
    fields = {**fields, "updated_at": _now_iso()}
    atomic_write(path, render_state_md(fields))


def read_state(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"OSBuilder: no state.md at {path}. Run `state_writer.py init` first."
        )
    return parse_state_md(path.read_text(encoding="utf-8"))


# ---------- subcommands ----------

def _cmd_init(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    path = _state_md_path(project_root)
    fields = {
        "goal": args.goal or "",
        "app_type": args.app_type or "unknown",
        "playbook": args.playbook or "unknown",
        "current_role": "PM",
        "current_phase": "0",
        "phase_step": "0",
        "last_failure": "",
        "retry_count": "0",
        "escalation_level": "0",
        "next_action": "gather-requirements",
    }
    write_state(path, fields)
    print(f"Initialized {path}")
    return 0


def _cmd_write(args: argparse.Namespace) -> int:
    # Defense-in-depth: cheap allowlist check first, then content validation
    _check_field_allowed(args.field)
    _check_value_safe(args.value)
    project_root = _resolve_project_root(args.project_root)
    path = _state_md_path(project_root)
    if not path.exists():
        raise SystemExit(f"OSBuilder: no state.md at {path}. Run `init` first.")
    fields = read_state(path)
    fields[args.field] = args.value
    write_state(path, fields)
    print(f"set {args.field}={args.value}")
    return 0


def _cmd_read(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    path = _state_md_path(project_root)
    fields = read_state(path)
    if args.field:
        _check_field_allowed(args.field)
        print(fields.get(args.field, ""))
    elif args.format == "json":
        print(json.dumps(fields, indent=2))
    else:
        for f in REQUIRED_FIELDS:
            print(f"{f}: {fields.get(f, '')}")
        if "updated_at" in fields:
            print(f"updated_at: {fields['updated_at']}")
    return 0


def _cmd_bump(args: argparse.Namespace) -> int:
    _check_field_allowed(args.field)
    if args.field not in COUNTER_FIELDS:
        raise SystemExit(
            f"OSBuilder: --field '{args.field}' is not a counter. "
            f"Allowed counters: {', '.join(COUNTER_FIELDS)}"
        )
    project_root = _resolve_project_root(args.project_root)
    path = _state_md_path(project_root)
    fields = read_state(path)
    try:
        cur = int(fields.get(args.field, "0") or "0")
    except ValueError:
        cur = 0
    fields[args.field] = str(cur + 1)
    write_state(path, fields)
    print(f"bumped {args.field}={fields[args.field]}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    path = _state_md_path(project_root)
    if not path.exists():
        sys.stderr.write(f"OSBuilder: missing state.md at {path}\n")
        return 1
    fields = read_state(path)
    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    if missing:
        sys.stderr.write(
            "OSBuilder: state.md missing required fields: " + ", ".join(missing) + "\n"
        )
        return 1
    print("OK — state.md has all 10 required fields.")
    return 0


# ---------- argparse ----------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="state_writer", description="OSBuilder state.md checkpoint manager."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize state.md with all 10 fields")
    p_init.add_argument("--goal", default="")
    p_init.add_argument("--app-type", default="unknown", dest="app_type")
    p_init.add_argument("--playbook", default="unknown")
    p_init.set_defaults(func=_cmd_init)

    p_write = sub.add_parser("write", help="set one field's value")
    p_write.add_argument("--field", required=True)
    p_write.add_argument("--value", required=True)
    p_write.set_defaults(func=_cmd_write)

    p_read = sub.add_parser("read", help="print field(s)")
    p_read.add_argument("--field", default=None)
    p_read.add_argument("--format", choices=("plain", "json"), default="plain")
    p_read.set_defaults(func=_cmd_read)

    p_bump = sub.add_parser("bump", help="increment a counter field")
    p_bump.add_argument("--field", required=True)
    p_bump.set_defaults(func=_cmd_bump)

    p_validate = sub.add_parser("validate", help="verify all 10 fields exist")
    p_validate.set_defaults(func=_cmd_validate)

    return parser


def _extract_project_root(argv: list[str]) -> tuple[str | None, list[str]]:
    """Pull --project-root from anywhere in argv so it works before or after the subcommand."""
    project_root: str | None = None
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--project-root":
            if i + 1 >= len(argv):
                sys.stderr.write("OSBuilder: --project-root requires a value\n")
                sys.exit(2)
            project_root = argv[i + 1]
            i += 2
        elif argv[i].startswith("--project-root="):
            project_root = argv[i].split("=", 1)[1]
            i += 1
        else:
            cleaned.append(argv[i])
            i += 1
    return project_root, cleaned


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    project_root, cleaned = _extract_project_root(argv)
    args = _build_parser().parse_args(cleaned)
    args.project_root = project_root
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
