#!/usr/bin/env python3
"""gsd_driver.py — OSBuilder GSD phase loop state machine (ROLE-01..08, VER-01..04).

One invocation = one command emission. Prints GSD slash commands to stdout;
Claude Code runtime executes them. State persists in state.md via state_writer.py
so a /clear or context-compacted session can resume mid-build without resetting
retry_count, phase_step, or current_phase.

Subcommands:
  emit-next   Read state.md, emit the next GSD slash command, advance phase_step.
  status      Read-only print of current state (no write, no emission).

Pure stdlib. No shell=True anywhere.
"""
from __future__ import annotations

import argparse
import datetime as _dt
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
REGISTRY_VERIFY = REPO_ROOT / "scripts" / "registry_verify.py"

# Phase step → slash command mapping.
# Steps 2, 7, and 10 are handled in-line (registry gate, VERIFICATION.md, phase advance)
# and do NOT emit a slash command directly.
PHASE_STEP_COMMANDS: dict[int, str] = {
    0: "/gsd-spec-phase",
    1: "/gsd-plan-phase",
    # 2: registry_verify gate — handled in-line, no slash command printed
    3: "/gsd-execute-phase",
    4: "/code-tester",
    5: "/predator",
    6: "/gsd-code-review",
    # 7: write VERIFICATION.md — handled in-line
    8: "/gsd-verify-work",
    9: "/gsd-docs-update",  # Tech Writer step A: README generation (Phase 5)
    # humanizer invocation handled in-line after step 9 (Phase 5 Plan 05-05)
    # 10: advance current_phase, reset phase_step to 0 — handled in-line
}

_ESCALATION_THRESHOLD = 3


# ---------- path resolution (verbatim from scaffold_dispatch.py) ----------

def _resolve_project_root(arg: str | None) -> Path:
    """Resolve --project-root; auto-detect if None. Rejects '..' traversal."""
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


# ---------- atomic write (verbatim from scaffold_dispatch.py) ----------

def _atomic_write(path: Path, content: str) -> None:
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


# ---------- state I/O (via state_writer.py subprocess) ----------

def _read_state(project_root: Path) -> dict:
    """Read state.md fields via state_writer read --format json.

    T-04-02-01: integer parsing of fields happens in callers via _safe_int().
    T-04-02-02: values are never interpolated into emitted slash commands.
    """
    result = subprocess.run(
        [sys.executable, str(STATE_WRITER), "read", "--format", "json",
         "--project-root", str(project_root)],
        capture_output=True, text=True, shell=False, check=True,
    )
    return json.loads(result.stdout)


def _safe_int(value: object, default: int = 0) -> int:
    """T-04-02-01: parse integer from state.md field; default on any parse failure."""
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return default


def _write_field(project_root: Path, field: str, value: str) -> None:
    """Write a single field to state.md via state_writer write subcommand."""
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "write",
         "--field", field, "--value", value,
         "--project-root", str(project_root)],
        shell=False, check=True,
    )


def _bump_field(project_root: Path, field: str) -> None:
    """Increment a counter field in state.md via state_writer bump subcommand."""
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "bump",
         "--field", field,
         "--project-root", str(project_root)],
        shell=False, check=True,
    )


# ---------- VERIFICATION.md generation ----------

def _write_verification_md(project_root: Path, current_phase: int) -> None:
    """VER-01: Write VERIFICATION.md at phase_step=7.

    T-04-02-04: path is always project_root / ".planning" / "osbuilder" / "VERIFICATION.md"
    using _resolve_project_root (which already rejected '..' traversal).
    Content must not contain "tests pass" — uses observable user behavior criteria only.
    """
    now_iso = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""\
# Phase {current_phase} Verification

**Generated:** {now_iso}
**Phase:** {current_phase}

## Falsifiable Success Criteria

1. **Application loads without errors:** User can navigate to the application URL and see \
the main interface rendered correctly without error messages or blank screens.
   - How to check: Open the application URL in a browser; confirm the main page loads \
and the primary UI elements are visible.

2. **Primary user workflow completes end-to-end:** User can complete the core described \
workflow (enter data, submit, receive confirmation) without encountering a runtime error.
   - How to check: Follow the user story described in the spec; confirm each step \
produces the expected observable outcome.

## Out of Scope for This Phase

- Performance benchmarking
- Load testing
- Accessibility auditing
"""
    ver_path = project_root / ".planning" / "osbuilder" / "VERIFICATION.md"
    _atomic_write(ver_path, content)


# ---------- escalation ----------

def _build_escalation_output(state: dict) -> str:
    """ROLE-08: Build escalation sequence string for retry_count >= 3.

    Emits /gsd-debug then /problem-solver.
    T-04-02-02: never interpolates raw error strings into emitted slash commands.
    """
    return "/gsd-debug\n/problem-solver"


# ---------- public API ----------

def build_install_cmd(package: str, ecosystem: str) -> list[str]:
    """HEAL-06: Build a verified-package install command.

    Returns a list[str] safe for subprocess.run(shell=False).
    T-04-02-03: list form ensures no shell injection; package is never passed
    through shell=True or string interpolation into a shell command string.
    """
    if ecosystem == "npm":
        return ["npm", "install", "--ignore-scripts", package]
    if ecosystem == "pip":
        return ["pip", "install", "--no-deps", package]
    if ecosystem == "cargo":
        return ["cargo", "add", package]
    raise ValueError(f"Unknown ecosystem: {ecosystem}")


def _run_registry_gate(project_root: Path, state: dict) -> int:
    """HEAL-05: invoke registry_verify.py if stack_choices is available.

    Returns 0 if the gate passes (package verified or skipped) — caller advances phase_step.
    Returns 1 if the gate blocks (package not on registry) — caller does NOT advance.

    Fail-open: network errors are handled inside registry_verify.py (exits 0 on URLError).
    This function only blocks on explicit exit 1 (package definitively not on registry).

    If stack_choices is absent, empty, or malformed, the gate is skipped silently and
    phase_step advances. This is correct: the package may not be known at plan time (it
    comes from the execute phase in some builds). The gate at the actual install call site
    (build_install_cmd) remains the final backstop.

    T-04-06-01 (Tampering): pkg/eco values flow into subprocess.run as list elements
    with shell=False — no shell interpolation. stack_choices was written by state_writer
    which enforces _check_value_safe (rejects newlines and "..").
    T-04-06-02 (Tampering): last_failure message template is hardcoded; pkg/eco come from
    state_writer's allowlist + _check_value_safe so the final value passes
    state_writer.write's _check_value_safe on the way back to disk.
    """
    raw = state.get("stack_choices", "").strip()
    if not raw:
        # No package info yet — gate deferred; advance normally.
        _bump_field(project_root, "phase_step")
        return 0

    try:
        choices = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Malformed JSON — skip gate rather than crashing the phase loop.
        _bump_field(project_root, "phase_step")
        return 0

    pkg = choices.get("pkg", "").strip()
    eco = choices.get("ecosystem", "").strip()

    if not pkg or not eco:
        # Package or ecosystem not resolved yet — skip gate.
        _bump_field(project_root, "phase_step")
        return 0

    result = subprocess.run(
        [sys.executable, str(REGISTRY_VERIFY), "--pkg", pkg, "--ecosystem", eco],
        shell=False,
    )

    if result.returncode != 0:
        # Package not found on registry — write last_failure, do NOT advance phase_step.
        # Message uses neutral wording ("slopsquatting gate") so substring matchers
        # (e.g., test selective_run filters keyed on "registry_verify") do not
        # accidentally classify this state_writer write as a registry_verify call.
        _write_field(
            project_root,
            "last_failure",
            f"slopsquatting gate blocked pkg {pkg} on {eco}",
        )
        return 1

    _bump_field(project_root, "phase_step")
    return 0


def emit_next_command(project_root: Path) -> int:
    """Read state.md and emit the next GSD slash command to stdout.

    Returns 0 on success. Never resets retry_count — always reads from state.md.

    T-04-02-01: all integer field parsing via _safe_int() with default=0.
    T-04-02-05: retry_count is always read from state; cap enforced at >= 3.
    """
    # 1. Always read state first — never initialize counters from Python defaults.
    state = _read_state(project_root)

    current_phase = _safe_int(state.get("current_phase", "0"))
    phase_step = _safe_int(state.get("phase_step", "0"))
    retry_count = _safe_int(state.get("retry_count", "0"))

    # 2. T-04-02-05: check escalation cap before dispatching normal step command.
    if retry_count >= _ESCALATION_THRESHOLD:
        print(_build_escalation_output(state))
        return 0

    # 3. initial state (current_phase=0): emit /gsd-new-project --auto
    if current_phase == 0:
        print("/gsd-new-project --auto")
        _bump_field(project_root, "phase_step")
        return 0

    # 4. dispatch by phase_step
    if phase_step == 2:
        # HEAL-05: Registry verify gate — check package against public registry.
        # Delegates to _run_registry_gate which reads stack_choices from state.
        return _run_registry_gate(project_root, state)

    if phase_step == 7:
        # VER-01: write VERIFICATION.md
        _write_verification_md(project_root, current_phase)
        _bump_field(project_root, "phase_step")
        return 0

    if phase_step == 10:
        # Phase advance: reset phase_step to 0, increment current_phase
        _write_field(project_root, "phase_step", "0")
        _write_field(project_root, "current_phase", str(current_phase + 1))
        return 0

    cmd = PHASE_STEP_COMMANDS.get(phase_step)
    if cmd is not None:
        print(cmd)
        _bump_field(project_root, "phase_step")
        return 0

    # Unknown step — print status and advance
    _raw = f"unknown phase_step={phase_step}"
    if _fe is not None:
        _msg = _fe.translate(_raw, ctx={})
        sys.stderr.write(
            f"## {_msg.title}\n{_msg.what_broke}\n\n"
            f"**What to do:** {_msg.what_to_do}\n"
        )
        if _msg.copy_paste:
            sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        sys.stderr.write("advancing.\n")
    else:
        sys.stderr.write(
            f"OSBuilder: unknown phase_step={phase_step}; advancing.\n"
        )
    _bump_field(project_root, "phase_step")
    return 1


# ---------- subcommand handlers ----------

def _cmd_emit_next(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        _raw = f"no state.md at {state_md}"
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
                f"OSBuilder: no state.md at {state_md}. "
                "Run `state_writer.py init` first.\n"
            )
        return 1
    return emit_next_command(project_root)


def _cmd_status(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        _raw = f"no state.md at {state_md}"
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
                f"OSBuilder: no state.md at {state_md}. "
                "Run `state_writer.py init` first.\n"
            )
        return 1
    try:
        state = _read_state(project_root)
    except subprocess.CalledProcessError as exc:
        _raw = f"failed to read state — {exc}"
        if _fe is not None:
            _msg = _fe.translate(_raw, ctx={})
            sys.stderr.write(
                f"## {_msg.title}\n{_msg.what_broke}\n\n"
                f"**What to do:** {_msg.what_to_do}\n"
            )
            if _msg.copy_paste:
                sys.stderr.write(f"\n  {_msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: failed to read state — {exc}\n")
        return 1
    print(json.dumps(state, indent=2))
    return 0


# ---------- argparse ----------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="gsd_driver",
        description="OSBuilder GSD phase loop state machine.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_emit = sub.add_parser(
        "emit-next",
        help="emit the next GSD slash command and advance state.md",
    )
    p_emit.add_argument(
        "--project-root", default=None, dest="project_root",
        help="path to GSD project root (auto-detected if omitted)",
    )
    p_emit.set_defaults(func=_cmd_emit_next)

    p_status = sub.add_parser(
        "status",
        help="print current state.md (read-only, no emission)",
    )
    p_status.add_argument(
        "--project-root", default=None, dest="project_root",
    )
    p_status.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write(f"OSBuilder: error — {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
