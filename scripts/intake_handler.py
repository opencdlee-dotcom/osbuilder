#!/usr/bin/env python3
"""intake_handler.py — OSBuilder intake handler.

Parses a plain-English paragraph OR a structured dict/JSON spec into a
canonical derived_spec.md at <project-root>/.planning/osbuilder/derived_spec.md.
Writes state.md fields: goal, app_type, playbook via state_writer.py.

Pure stdlib — no third-party deps.

Subcommands:
  parse     paragraph text or @path-to-spec → derived_spec.md (IN-01, IN-02).
  validate  check derived_spec.md is suitable for /gsd-new-project --auto (IN-05).
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

_REQUIRED_SECTIONS = ("# OSBuilder Derived Spec", "**Goal:**", "**App type:**", "**Playbook:**")
_SECRET_PATTERNS = ("api_key", "password", "token", "database_url=postgresql://")


def _derived_spec_path(project_root: Path) -> Path:
    return project_root / ".planning" / "osbuilder" / "derived_spec.md"


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


def _validate_project_name(name: str) -> None:
    """V5 input + T-3-01: reject path traversal and shell-unsafe chars in project_name."""
    if not name:
        raise SystemExit("OSBuilder: project_name cannot be empty.")
    if ".." in name:
        raise SystemExit("OSBuilder: project_name cannot contain '..' (path traversal).")
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise SystemExit("OSBuilder: project_name must contain only [a-zA-Z0-9_-] characters.")


def _mode_from_state(project_root: Path) -> str:
    """Read mode field from state.md; default 'beginner' on any failure (UX-03)."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return "beginner"
    try:
        r = subprocess.run(
            [sys.executable, str(STATE_WRITER), "read",
             "--field", "mode", "--project-root", str(project_root)],
            capture_output=True, text=True, shell=False, check=False,
        )
        return r.stdout.strip() or "beginner"
    except Exception:
        return "beginner"


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


def _render_derived_spec(
    goal: str,
    app_type: str = "web",
    features: list | None = None,
    users: list | None = None,
    stack_hints: list | None = None,
    mode: str = "beginner",
) -> str:
    """Render derived_spec.md content in /gsd-new-project --auto handoff format.

    UX-03: stack_hints are only included when mode == 'advanced'. Beginner
    mode (default) omits the **Stack hints:** line entirely so technology
    names (Next.js, Drizzle, Postgres, etc.) never surface to the user.
    """
    features = features or []
    users = users or []
    stack_hints = stack_hints or []
    lines = ["# OSBuilder Derived Spec", "", f"**Goal:** {goal}", ""]
    if users:
        lines += ["**User types:**"] + [f"- {u}" for u in users] + [""]
    if features:
        lines += ["**Core features:**"] + [f"- {f}" for f in features] + [""]
    lines.append(f"**App type:** {app_type}")
    lines.append(f"**Playbook:** references/playbooks/{app_type}.md")
    if stack_hints and mode == "advanced":
        lines.append(f"**Stack hints:** {', '.join(stack_hints)}")
    lines += ["", "**Build with:** /gsd-new-project --auto"]
    return "\n".join(lines) + "\n"


def parse_paragraph(text: str, project_root: Path | None = None) -> Path:
    """IN-01: Parse plain-English paragraph → derived_spec.md.

    T-3-03: text is treated as data only — never executed or interpolated.
    UX-03: mode (beginner/advanced) is read from state.md; beginner mode
    suppresses stack_hints in the rendered spec.
    Returns the Path of the written derived_spec.md.
    """
    root = _resolve_project_root(str(project_root) if project_root is not None else None)
    dest = _derived_spec_path(root)
    _mode = _mode_from_state(root)
    atomic_write(dest, _render_derived_spec(
        goal=text.strip(), app_type="web", mode=_mode,
    ))
    return dest


def parse_structured(data: dict, project_root: Path | None = None) -> Path:
    """IN-02: Parse structured dict spec → derived_spec.md.

    Keys: goal (required), features, users, app_type, stack_hints (all optional).
    UX-03: mode (beginner/advanced) is read from state.md; beginner mode
    suppresses stack_hints in the rendered spec.
    Returns the Path of the written derived_spec.md.
    """
    root = _resolve_project_root(str(project_root) if project_root is not None else None)
    dest = _derived_spec_path(root)
    _mode = _mode_from_state(root)
    atomic_write(dest, _render_derived_spec(
        goal=str(data.get("goal", "")),
        app_type=str(data.get("app_type", "web")),
        features=list(data.get("features", [])),
        users=list(data.get("users", [])),
        stack_hints=list(data.get("stack_hints", [])),
        mode=_mode,
    ))
    return dest


def _cmd_parse(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    inp: str = args.input
    if inp.startswith("@"):
        fp = Path(inp[1:])
        if not fp.exists():
            sys.stderr.write(f"OSBuilder: spec file not found: {fp}\n")
            return 1
        raw = fp.read_text(encoding="utf-8")
        try:
            parse_structured(json.loads(raw), project_root)
        except json.JSONDecodeError:
            parse_paragraph(raw, project_root)
    else:
        parse_paragraph(inp, project_root)
    print(f"Written: {_derived_spec_path(project_root)}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    dest = _derived_spec_path(_resolve_project_root(args.project_root))
    if not dest.exists():
        sys.stderr.write(f"OSBuilder: derived_spec.md not found at {dest}\n")
        return 1
    content = dest.read_text(encoding="utf-8")
    missing = [s for s in _REQUIRED_SECTIONS if s not in content]
    if missing:
        sys.stderr.write("OSBuilder: derived_spec.md missing: " + ", ".join(missing) + "\n")
        return 1
    found = [p for p in _SECRET_PATTERNS if p in content.lower()]
    if found:
        sys.stderr.write("OSBuilder: derived_spec.md contains secrets: " + ", ".join(found) + "\n")
        return 1
    print("OK — derived_spec.md is valid for /gsd-new-project --auto")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="intake_handler", description="OSBuilder intake handler.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_parse = sub.add_parser("parse", help="parse input → derived_spec.md")
    p_parse.add_argument("--input", required=True, help="paragraph string or @path-to-spec-file")
    p_parse.add_argument("--project-root", default=None, dest="project_root")
    p_parse.set_defaults(func=_cmd_parse)

    p_validate = sub.add_parser("validate", help="check derived_spec.md format")
    p_validate.add_argument("--project-root", default=None, dest="project_root")
    p_validate.set_defaults(func=_cmd_validate)

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
