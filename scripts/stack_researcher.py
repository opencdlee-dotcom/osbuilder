#!/usr/bin/env python3
"""stack_researcher.py — OSBuilder per-build stack researcher.

Delegates to /brainiac for current library recommendations.
Falls back to references/stack-menu.md on timeout or inconclusive result.
Writes stack_choices to state.md.

Pure stdlib — no third-party deps.

Subcommands:
  research  research stack for a given app_type → writes stack_choices to state.md (RES-01..04)
"""
from __future__ import annotations

import argparse
import json
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
REFERENCES_ROOT = REPO_ROOT / "references"

# Hardcoded web defaults — used when stack-menu.md is absent (Wave 2 target)
# and when brainiac returns empty/inconclusive result (RES-03)
_WEB_DEFAULTS: dict = {
    "framework": {"name": "next.js", "version": "16.2.4", "source": "stack-menu"},
    "orm": {"name": "drizzle-orm", "version": "0.45.2", "source": "stack-menu"},
    "database": {"name": "postgres", "version": "18-alpine", "source": "stack-menu"},
    "css": {"name": "tailwindcss", "version": "4.2.4", "source": "stack-menu"},
    "package_manager": {"name": "pnpm", "version": "10.33.2", "source": "stack-menu"},
}


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


_APP_TYPE_TO_SECTION = {
    "web": "Web playbook defaults",
    "ai-service": "ai-service playbook defaults",
    "cli": "cli playbook defaults",
    "desktop": "desktop playbook defaults",
    "hub-platform": "hub-platform playbook defaults",
}


def _read_stack_menu(references_root: Path, app_type: str = "web") -> dict:
    """RES-03 fallback: read stack-menu.md; return hardcoded defaults if absent.

    Slices the markdown to the `## <app_type> playbook defaults` section before
    running the row regex. Without this slice, the regex picked up rows from
    every section (web, ai-service, cli, ...) and the dict-overwrite left the
    LAST section's values (e.g. framework=fastapi) for any app_type — so a web
    build would inherit fastapi as its framework. Surfaced by the v1.0 codebase
    audit on stack_researcher.research_stack('web') in beginner mode.
    """
    p = references_root / "stack-menu.md"
    if not p.exists():
        # Wave 2 has not shipped yet — return hardcoded defaults
        return dict(_WEB_DEFAULTS)
    try:
        import re
        content = p.read_text(encoding="utf-8")
        section_title = _APP_TYPE_TO_SECTION.get(app_type)
        if section_title:
            # Slice from this section's H2 to the next H2 (or EOF).
            section_re = re.compile(
                r"^##\s*" + re.escape(section_title) + r"\s*$(.*?)(?=^##\s|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            m = section_re.search(content)
            if m:
                content = m.group(1)
        # Table rows: | Component | Package | Version | Rationale |
        rows = re.findall(
            r"^\|\s*(\w[\w\s]*?)\s*\|\s*([\w@./\-]+)\s*\|\s*([\w.\-]+)\s*\|",
            content,
            re.MULTILINE,
        )
        result = {}
        component_map = {
            "framework": "framework", "orm": "orm", "database": "database",
            "css": "css", "package manager": "package_manager",
        }
        for component, package, version in rows:
            key = component_map.get(component.lower().strip())
            if key:
                result[key] = {"name": package, "version": version, "source": "stack-menu"}
        return result if result else dict(_WEB_DEFAULTS)
    except Exception:
        return dict(_WEB_DEFAULTS)


def _call_brainiac(app_type: str) -> dict:
    """RES-01: invoke brainiac subprocess; return parsed dict or {} on failure."""
    query = f"modern stack for {app_type} app 2026"
    try:
        result = subprocess.run(
            ["python3", "-m", "brainiac", "scan", query],
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        return json.loads(result.stdout.strip())
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return {}


def research_stack(
    app_type: str,
    project_root: Path | None = None,
    advanced_overrides: dict | None = None,
) -> dict:
    """Research and return stack_choices; write to state.md. (RES-01..RES-04)

    UX-03: in beginner mode (default), skips _call_brainiac entirely and
    auto-resolves to references/stack-menu.md defaults. Advanced mode keeps
    the original brainiac → fallback behavior. The mode field is read from
    state.md via _mode_from_state.
    """
    resolved_root = _resolve_project_root(None if project_root is None else str(project_root))

    # UX-03: read mode from state.md — beginner skips brainiac entirely
    mode = _mode_from_state(resolved_root)

    if mode == "beginner":
        # Auto-resolve to stack-menu defaults (RES-03 path; no brainiac call)
        stack_choices = _read_stack_menu(REFERENCES_ROOT, app_type)
    else:
        # Advanced mode: original behavior (RES-01 brainiac → RES-03 fallback)
        brainiac_result = _call_brainiac(app_type)

        if not brainiac_result or not isinstance(brainiac_result, dict):
            stack_choices = _read_stack_menu(REFERENCES_ROOT, app_type)
        else:
            # Tag each component with its source
            stack_choices = {}
            for key, val in brainiac_result.items():
                if isinstance(val, dict):
                    stack_choices[key] = {**val, "source": "brainiac"}
                else:
                    stack_choices[key] = val
            # Fill in any missing required keys from fallback
            defaults = _read_stack_menu(REFERENCES_ROOT, app_type)
            for key in defaults:
                if key not in stack_choices:
                    stack_choices[key] = defaults[key]

    # RES-04: apply --advanced overrides (override wins on any conflicting key)
    if advanced_overrides:
        for key, override_val in advanced_overrides.items():
            stack_choices[key] = override_val

    # Write stack_choices to state.md (reuses Phase 3 ALLOWED_FIELDS extension)
    state_md = resolved_root / ".planning" / "osbuilder" / "state.md"
    if state_md.exists():
        try:
            subprocess.run(
                [sys.executable, str(STATE_WRITER), "write",
                 "--field", "stack_choices",
                 "--value", json.dumps(stack_choices),
                 "--project-root", str(resolved_root)],
                shell=False,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            pass  # state.md write failure is non-fatal; stack_choices returned regardless

    return stack_choices


def _cmd_research(args: argparse.Namespace) -> int:
    overrides = None
    if args.advanced_overrides:
        try:
            overrides = json.loads(args.advanced_overrides)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"OSBuilder: --advanced-overrides is not valid JSON: {e}\n")
            return 1
    project_root = _resolve_project_root(args.project_root)
    result = research_stack(args.app_type, project_root=project_root, advanced_overrides=overrides)
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="stack_researcher",
        description="OSBuilder per-build stack researcher.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_research = sub.add_parser("research", help="research stack for app_type")
    p_research.add_argument("--app-type", required=True, dest="app_type")
    p_research.add_argument("--advanced-overrides", default=None, dest="advanced_overrides",
                            help="JSON string of user overrides (--advanced flag path)")
    p_research.add_argument("--project-root", default=None, dest="project_root")
    p_research.set_defaults(func=_cmd_research)

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
