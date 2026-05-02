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
import re
import subprocess
import sys
from pathlib import Path

# Phase 5: friendly-error translation layer (graceful degrade if module not yet built)
try:
    import friendly_error as _fe
except ImportError:
    _fe = None  # type: ignore[assignment]

# Phase 5: narration layer — role banners + tutor lines (graceful degrade pre-Phase 5)
try:
    import narration as _narration
except ImportError:
    _narration = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"
REGISTRY_VERIFY = REPO_ROOT / "scripts" / "registry_verify.py"

# Phase 5 Plan 05-05: humanizer skill location + minimum version (RESEARCH lines 617–623)
HUMANIZER_SKILL_MD = Path.home() / ".claude" / "skills" / "humanizer" / "SKILL.md"
MINIMUM_HUMANIZER_VERSION = (2, 0, 0)

# Phase step → slash command mapping.
# Steps 2, 7, 9, and 10 are handled in-line (registry gate, VERIFICATION.md,
# tech-writer + humanizer pipeline, phase advance) and do NOT emit a slash
# command directly through this dict.
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
    # 9: tech-writer step — handled in-line via _run_tech_writer_step()
    #    (sub-state machine: emits /gsd-docs-update then /humanizer @README.md)
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

def _build_escalation_output(state: dict) -> str:  # noqa: ARG001 — reserved
    """ROLE-08: Build escalation sequence string for retry_count >= 3.

    Emits /gsd-debug then /problem-solver.
    T-04-02-02: never interpolates raw error strings into emitted slash commands.

    WR-14: `state` is currently unused — the output is constant. The parameter
    is kept (and silenced via noqa) so future variants of the escalation
    sequence can branch on retry context (e.g. last_failure category) without
    a signature change at every caller.
    """
    return "/gsd-debug\n/problem-solver"


# ---------- narration helpers (Phase 5 ROLE-09) ----------

def _role_for_step(phase_step: int, state: dict) -> str:
    """Return the narration role name for the given phase step.

    Maps the GSD phase loop's PHASE_STEP_COMMANDS dispatch into the 8 dev-team roles.
    For phase_step==3 (the execute step), inspects state.next_action to choose
    frontend / backend / devops based on plain-English keywords.
    """
    if phase_step == 0:
        return "pm"
    if phase_step == 1:
        return "architect"
    if phase_step == 2:
        return "devops"
    if phase_step == 4:
        return "qa"
    if phase_step in (5, 6):
        return "reviewer"
    if phase_step in (7, 8):
        return "qa"
    if phase_step == 9:
        return "tech-writer"
    if phase_step == 10:
        return "pm"
    # phase_step == 3 (execute) — pick FE / BE / DevOps based on the next_action hint.
    title = str(state.get("next_action", "")).lower()
    if any(w in title for w in ("ui", "frontend", "homepage", "screen", "page")):
        return "frontend"
    if any(w in title for w in ("api", "backend", "database", "model")):
        return "backend"
    return "devops"


def _emit(role: str, action: str, status: str, detail: str | None = None) -> None:
    """Wrapper around narration.emit that no-ops when narration is unavailable."""
    if _narration is not None:
        try:
            _narration.emit(role, action, status, detail)  # type: ignore[arg-type]
        except Exception:
            pass  # never let narration failure break a phase emission


def _refresh_narration_state(project_root: Path) -> None:
    """Refresh narration's mode + tutor_enabled flags from state.md.

    IN-07: `_narration._refresh_state` is named with a leading underscore but is
    documented in narration.py's module docstring as part of the public surface
    (Phase 5 ROLE-09). Treat it as a stable contract — if narration ever renames
    or removes it, this caller and `_init_build_log_if_new_build` below break.
    """
    if _narration is not None:
        try:
            _narration._refresh_state(project_root)
        except Exception:
            pass


def _init_build_log_if_new_build(project_root: Path, phase_step: int) -> None:
    """Truncate build.log when a new build starts (phase_step == 0).

    Resolves Open Question 6: build.log must not grow across builds.
    Called once per emit_next_command invocation; only truncates at step 0.

    IN-07: depends on `_narration._init_build_log` — see `_refresh_narration_state`
    above for the public-contract note covering both calls.
    """
    if phase_step != 0:
        return
    if _narration is None:
        return
    log_path = project_root / ".planning" / "osbuilder" / "build.log"
    try:
        _narration._init_build_log(log_path)
    except Exception:
        pass  # non-fatal if narration or path unavailable


# ---------- ROLE-07 tech-writer helpers (Phase 5 Plan 05-05) ----------

def _humanizer_present() -> bool:
    """Check if humanizer skill >= MINIMUM_HUMANIZER_VERSION is installed.

    Reads ~/.claude/skills/humanizer/SKILL.md frontmatter for `version: x.y.z`.
    Fail-open: if SKILL.md exists but no version field is parseable, treat as
    present (the skill exists; version is just unverifiable).

    Returns False only when SKILL.md is missing entirely OR when an explicit
    parseable version is below the minimum.

    T-05-05 (Tampering — humanizer SKILL.md version field): malformed version
    parsing falls through to True (fail-open). Worst case: humanizer is invoked
    on a too-old install and the slash command itself reports the version
    mismatch. No injection surface — version string is never interpolated into
    a shell or LLM prompt.
    """
    if not HUMANIZER_SKILL_MD.exists():
        return False
    # WR-08: capture parse exceptions so the user sees a tutor-line rather than
    # a silent fail-open. The fail-open behaviour itself is intentional (per
    # design + T-05-05); we just surface the unverifiable state so it's visible.
    parse_error: str | None = None
    try:
        text = HUMANIZER_SKILL_MD.read_text(encoding="utf-8")
        # IN-08: use a single regex against the YAML frontmatter rather than a
        # hand-rolled line-by-line parser. The regex handles optional quotes
        # around the version value and is anchored to the frontmatter block via
        # `re.MULTILINE` so a stray `version:` later in the document does not
        # match. Falls back to "no version field found" if absent.
        ver_match = re.search(
            r'^version:\s*["\']?([\d.]+)["\']?\s*$',
            text,
            re.MULTILINE,
        )
        if ver_match is not None:
            ver_str = ver_match.group(1)
            parts = tuple(int(x) for x in ver_str.split(".")[:3])
            # Pad to 3 components if shorter (e.g., "2.0" → (2, 0, 0))
            while len(parts) < 3:
                parts = parts + (0,)
            return parts >= MINIMUM_HUMANIZER_VERSION
    except Exception as exc:
        parse_error = f"{type(exc).__name__}: {exc}"
    _emit(
        "tech-writer",
        "version-check",
        "fail",
        detail=(
            f"could not parse humanizer SKILL.md version "
            f"({parse_error or 'no version field found'}); "
            "treating as present (fail-open)"
        ),
    )
    return True  # SKILL.md present but version unparseable → fail-open


def _run_tech_writer_step(project_root: Path, state: dict) -> int:
    """ROLE-07: Tech Writer phase step handler (phase_step == 9).

    v1 sub-state machine (two states only — no retry loop per Plan 05-05):

      sub_step="" → emit /gsd-docs-update (with @-reference to readme-context.md
        which requires the "## How OSBuilder built this" section naming all 8
        roles) → set tech_writer_sub_step=awaiting-humanizer; do NOT bump phase_step
        (stays at 9 until humanizer check completes).

      sub_step="awaiting-humanizer":
        - if humanizer absent → write humanizer_score=skipped, reset sub_step,
          bump phase_step to 10, emit fallback narration.
        - else → emit /humanizer @README.md, write humanizer_score=0 optimistically,
          reset sub_step, bump phase_step to 10. (Humanizer's actual score, if it
          writes one to state, overrides the optimistic default on the next read.)

    v1 deviation from SPEC (Open Question 1 resolution, RESEARCH Option 3):
    humanizer runs once only; no auto-retry. If the user wants to re-run, they
    invoke /humanizer manually. Retry loop deferred to Phase 8 (QUAL-05).

    Threat boundaries (T-05-05-04): readme-context.md content is fully hardcoded
    here — no user input flows in, so the file is safe to use as a /-command @-ref.
    """
    sub_step = state.get("tech_writer_sub_step", "")

    if sub_step == "":
        # Sub-step A: emit /gsd-docs-update with README section requirement.
        _emit("tech-writer", "generate-readme", "start")

        # Write the README context/prompt file that /gsd-docs-update reads.
        # Content is fully hardcoded — no user data interpolated (T-05-05-04).
        planning_dir = project_root / ".planning" / "osbuilder"
        planning_dir.mkdir(parents=True, exist_ok=True)
        readme_context_path = planning_dir / "readme-context.md"
        readme_context_path.write_text(
            "# README Generation Context\n"
            "\n"
            "The generated README MUST include a section with the exact heading:\n"
            "\n"
            "## How OSBuilder built this\n"
            "\n"
            "This section must name all 8 dev-team roles in plain English:\n"
            "PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer.\n"
            "\n"
            "Describe each role's contribution in 1–2 sentences a non-developer\n"
            "can follow. Do not use jargon. Do not name frameworks in this\n"
            "section — keep it about what each role contributed, not the tools\n"
            "they used.\n",
            encoding="utf-8",
        )

        # Emit the docs-update slash command with the context file as an @-reference.
        print(f"/gsd-docs-update @{readme_context_path}")
        _write_field(project_root, "tech_writer_sub_step", "awaiting-humanizer")
        # Do NOT bump phase_step — stays at 9 until humanizer check completes.
        return 0

    if sub_step == "awaiting-humanizer":
        # Sub-step B: /gsd-docs-update has run. Now invoke humanizer (once).
        if not _humanizer_present():
            # Fallback: humanizer missing — log skipped score, advance to step 10.
            _emit(
                "tech-writer", "check-humanizer", "fail",
                detail="humanizer skill not found; README ships without AI-pattern check",
            )
            _write_field(project_root, "humanizer_score", "skipped")
            _write_field(project_root, "tech_writer_sub_step", "")
            _bump_field(project_root, "phase_step")  # 9 → 10
            return 0

        # Invoke humanizer once (v1 — no retry).
        _emit("tech-writer", "check-humanizer", "start")
        print("/humanizer @README.md")
        # IN-02: surface the optimistic-write caveat to any reader who inspects
        # state.md between this write and humanizer's actual score write.
        _emit(
            "tech-writer", "check-humanizer", "ok",
            detail=(
                "humanizer_score=0 written optimistically; humanizer's own score "
                "(if any) overrides on the next state read. Plan 05-05 deviation."
            ),
        )
        # Optimistic default: humanizer_score=0 (pass). If humanizer writes its
        # own score via state_writer this is overwritten on the next read. The
        # sub_step resets so the phase-advance runs on the next call.
        _write_field(project_root, "humanizer_score", "0")
        _write_field(project_root, "tech_writer_sub_step", "")
        _bump_field(project_root, "phase_step")  # 9 → 10
        return 0

    # Unknown sub_step — defensive reset + advance (no crash, no escalation).
    # Mitigation for T-05-05-02 (Tampering: tech_writer_sub_step value).
    _emit(
        "tech-writer", "unknown-sub-step", "fail",
        detail=f"sub_step={sub_step!r}; resetting and advancing",
    )
    _write_field(project_root, "tech_writer_sub_step", "")
    _bump_field(project_root, "phase_step")
    return 0


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
        _emit("devops", "registry-gate", "ok", detail="no package info yet")
        return 0

    try:
        choices = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Malformed JSON — skip gate rather than crashing the phase loop.
        _bump_field(project_root, "phase_step")
        _emit("devops", "registry-gate", "ok", detail="package info unreadable")
        return 0

    pkg = choices.get("pkg", "").strip()
    eco = choices.get("ecosystem", "").strip()

    if not pkg or not eco:
        # Package or ecosystem not resolved yet — skip gate.
        _bump_field(project_root, "phase_step")
        _emit("devops", "registry-gate", "ok", detail="package not yet resolved")
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
        _emit("devops", "registry-gate", "fail", detail="package not verified")
        return 1

    _bump_field(project_root, "phase_step")
    _emit("devops", "registry-gate", "ok")
    return 0


def emit_next_command(project_root: Path) -> int:
    """Read state.md and emit the next GSD slash command to stdout.

    Returns 0 on success. Never resets retry_count — always reads from state.md.

    T-04-02-01: all integer field parsing via _safe_int() with default=0.
    T-04-02-05: retry_count is always read from state; cap enforced at >= 3.

    Phase 5 (ROLE-09): Wraps every dispatch with a narration banner. The narration
    layer reads mode + tutor_enabled from state.md (graceful degrade if unavailable).
    """
    # 1. Always read state first — never initialize counters from Python defaults.
    state = _read_state(project_root)

    current_phase = _safe_int(state.get("current_phase", "0"))
    phase_step = _safe_int(state.get("phase_step", "0"))
    retry_count = _safe_int(state.get("retry_count", "0"))

    # Phase 5: refresh narration mode/tutor flags + truncate build.log on new build.
    _refresh_narration_state(project_root)
    _init_build_log_if_new_build(project_root, phase_step)

    # 2. T-04-02-05: check escalation cap before dispatching normal step command.
    if retry_count >= _ESCALATION_THRESHOLD:
        print(_build_escalation_output(state))
        return 0

    # 3. initial state (current_phase=0): emit /gsd-new-project --auto
    if current_phase == 0:
        _emit("pm", "/gsd-new-project --auto", "start")
        print("/gsd-new-project --auto")
        _bump_field(project_root, "phase_step")
        _emit("pm", "/gsd-new-project --auto", "ok")
        return 0

    # 3b. Phase 6 — ship step (SHIP-01, SHIP-02, SCL-06)
    # Fires when all GSD phases are complete: current_phase > gsd_phase_count.
    # Sequence: runbook_writer (stamp README) → gh_handoff (create private repo + push)
    #           → production_phase_writer (emit /gsd-add-phase if production_ready=true)
    # This check runs BEFORE per-step dispatch so a fresh call after phase_step==10
    # (which bumped current_phase past gsd_phase_count) is intercepted here.
    try:
        gsd_phase_count = int(state.get("gsd_phase_count", "0") or "0")
    except ValueError:
        gsd_phase_count = 0
    if gsd_phase_count > 0 and current_phase > gsd_phase_count:
        project_path = state.get("project_path") or ""
        if not project_path:
            sys.stderr.write("OSBuilder: project_path not set in state.md; cannot ship.\n")
            return 1
        project_dir = Path(project_path).resolve()
        project_name = project_dir.name
        if not project_dir.is_dir():
            sys.stderr.write(
                f"OSBuilder: project_path does not exist on disk: {project_dir}\n"
            )
            return 1
        # WR-05: child scripts (runbook_writer, gh_handoff) reconstruct the project
        # directory as project_root / project_name. If project_path lives outside
        # project_root that reconstruction silently points at a different (or empty)
        # directory than scaffold built. Assert containment up front so the failure
        # mode is loud rather than mysterious.
        if project_dir.parent.resolve() != project_root.resolve():
            sys.stderr.write(
                "OSBuilder: project_path is not a direct child of project_root; "
                f"refusing to ship.\n  project_path={project_dir}\n  "
                f"project_root={project_root}\n"
            )
            return 1

        # 1. Stamp the README (idempotent — uses OSBuilder runbook marker)
        rb = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "runbook_writer.py"),
             "write", "--project-name", project_name,
             "--project-root", str(project_root)],
            shell=False, capture_output=True, text=True,
        )
        if rb.returncode != 0:
            sys.stderr.write(rb.stderr or "OSBuilder: runbook_writer failed.\n")
            return 1

        # 2. Ship the private repo (idempotent — checks `git remote get-url origin`)
        sh = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "gh_handoff.py"),
             "ship", "--project-name", project_name,
             "--project-root", str(project_root)],
            shell=False,
            # capture_output intentionally omitted — let stderr flow to user
            # (friendly_error in gh_handoff already formats it)
        )
        if sh.returncode != 0:
            # gh_handoff already wrote friendly stderr; don't double-print
            return 1

        # 3. Emit production-ready slash commands (zero lines if production_ready != "true")
        pp = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "production_phase_writer.py"),
             "emit", "--project-root", str(project_root)],
            shell=False, capture_output=True, text=True,
        )
        # IN-14: production_phase_writer.emit() is documented to always exit 0
        # (see scripts/production_phase_writer.py docstring). Assert the contract
        # rather than blindly trusting it: if a future change makes pp fail (e.g.
        # ROADMAP read raises), surface the stderr instead of swallowing it.
        if pp.returncode != 0:
            sys.stderr.write(pp.stderr or "")
            sys.stderr.write(
                "OSBuilder: production_phase_writer exited non-zero "
                f"(returncode={pp.returncode}); contract violation. "
                "Ship pipeline succeeded but post-ship phase emission failed.\n"
            )
            sys.stdout.write(pp.stdout)
            return 1
        sys.stdout.write(pp.stdout)
        return 0

    # 4. dispatch by phase_step

    # Phase 6 — refusal gate at architect-role boundary (SCL-05)
    # Runs at phase_step == 1 (just before /gsd-plan-phase emit). On hit:
    #   - intake_handler writes last_failure="refused: <kw>" to state.md
    #   - intake_handler prints refusal copy to stderr
    #   - we DO NOT advance phase_step; user must rephrase or re-run with --production-ready
    if phase_step == 1:
        refusal = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "intake_handler.py"),
             "check-refuse-list", "--project-root", str(project_root)],
            shell=False,
            # capture_output intentionally omitted — let stderr flow to the user
        )
        if refusal.returncode == 2:
            # Refused — do not advance, do not emit /gsd-plan-phase
            # state.md last_failure was already written by intake_handler
            return 0
        # else fall through to the existing PHASE_STEP_COMMANDS[1] emit path

    if phase_step == 2:
        # HEAL-05: Registry verify gate — check package against public registry.
        # Delegates to _run_registry_gate which reads stack_choices from state.
        # The "start" banner fires here; ok/fail emits live inside the gate.
        _emit("devops", "registry-gate", "start")
        return _run_registry_gate(project_root, state)

    if phase_step == 7:
        # VER-01: write VERIFICATION.md
        _emit("qa", "write-VERIFICATION.md", "start")
        _write_verification_md(project_root, current_phase)
        _bump_field(project_root, "phase_step")
        _emit("qa", "write-VERIFICATION.md", "ok")
        return 0

    if phase_step == 9:
        # ROLE-07: Tech Writer step — handled in-line via sub-state machine.
        # Emits /gsd-docs-update on first call, /humanizer @README.md (or
        # skipped fallback) on second call. See _run_tech_writer_step docstring.
        return _run_tech_writer_step(project_root, state)

    if phase_step == 10:
        # Phase advance: reset phase_step to 0, increment current_phase
        _emit("pm", "phase-complete", "start")
        _write_field(project_root, "phase_step", "0")
        _write_field(project_root, "current_phase", str(current_phase + 1))
        _emit("pm", "phase-complete", "ok")
        return 0

    cmd = PHASE_STEP_COMMANDS.get(phase_step)
    if cmd is not None:
        role = _role_for_step(phase_step, state)
        _emit(role, cmd, "start")
        print(cmd)
        _bump_field(project_root, "phase_step")
        _emit(role, cmd, "ok")
        return 0

    # Unknown step — print status and advance
    _emit(_role_for_step(phase_step, state),
          f"unknown-step-{phase_step}", "fail",
          detail="advancing")
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
