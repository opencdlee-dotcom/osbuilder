---
phase: 04-gsd-handoff-verify-loop-failure-classifier
plan: "02"
subsystem: gsd-phase-loop-driver
tags: [wave-1, tdd, green-phase, state-machine, gsd-handoff]
dependency_graph:
  requires:
    - "04-01 (RED stubs: test_gsd_driver.py + state_writer ALLOWED_FIELDS extension)"
  provides:
    - "scripts/gsd_driver.py — emit_next_command, build_install_cmd, main() with emit-next + status subcommands"
    - "All 16 test_gsd_driver.py stubs GREEN (ROLE-01..06, ROLE-08, HEAL-06, HEAL-07, VER-01..04)"
  affects:
    - scripts/gsd_driver.py
tech_stack:
  added: []
  patterns:
    - "PHASE_STEP_COMMANDS dispatch table: int step -> slash command string"
    - "Escalation threshold pattern: retry_count >= 3 → /gsd-debug + /problem-solver before normal dispatch"
    - "_safe_int() guard: all state.md integer fields parsed via try/except ValueError (T-04-02-01)"
    - "Atomic write pattern: copied verbatim from scaffold_dispatch.py via os.replace"
    - "subprocess.run(shell=False) for all state_writer.py and registry_verify.py calls (T-04-02-03)"
key_files:
  created:
    - scripts/gsd_driver.py
  modified: []
decisions:
  - "Step 2 (registry_verify gate) advances phase_step with no slash command printed — consistent with plan interface block"
  - "Step 9 (phase advance) writes phase_step=0 + current_phase=N+1 via two write calls rather than bump; bump is increment-only and cannot reset to zero"
  - "VERIFICATION.md criteria use observable-behavior language only; content verified to never contain 'tests pass'"
  - "Escalation output is /gsd-debug then /problem-solver on separate lines; test checks for either substring (OR logic in stub)"
metrics:
  duration_seconds: 135
  completed_date: "2026-04-30"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 04 Plan 02: gsd_driver.py GSD Phase Loop State Machine Summary

**One-liner:** Implemented gsd_driver.py TDD GREEN phase — PHASE_STEP_COMMANDS dispatch table, escalation at retry_count >= 3, VERIFICATION.md write at step 7, and build_install_cmd with --ignore-scripts; all 16 stubs GREEN.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement scripts/gsd_driver.py (GREEN phase) | facda36 | scripts/gsd_driver.py |

## What Was Built

### gsd_driver.py — GSD Phase Loop State Machine

A 322-line pure-stdlib Python module implementing the OSBuilder quality moat orchestrator.

**Core function: `emit_next_command(project_root: Path) -> int`**

1. Reads state.md via `state_writer.py read --format json` subprocess call — never reads from Python defaults.
2. Checks `retry_count >= 3` (T-04-02-05 escalation cap) before any dispatch — prints `/gsd-debug` + `/problem-solver` and returns.
3. `current_phase=0` → prints `/gsd-new-project --auto` + bumps `phase_step`.
4. `phase_step` dispatch via `PHASE_STEP_COMMANDS` dict:
   - 0 → `/gsd-spec-phase`
   - 1 → `/gsd-plan-phase`
   - 2 → registry verify gate (in-line, no command printed)
   - 3 → `/gsd-execute-phase`
   - 4 → `/code-tester`
   - 5 → `/predator`
   - 6 → `/gsd-code-review`
   - 7 → write VERIFICATION.md (in-line, no command printed)
   - 8 → `/gsd-verify-work`
   - 9 → advance `current_phase`, reset `phase_step=0`
5. After each emission: bumps `phase_step` via `state_writer.py bump`.

**`build_install_cmd(package, ecosystem) -> list[str]`** (HEAL-06)
- npm: `["npm", "install", "--ignore-scripts", package]`
- pip: `["pip", "install", "--no-deps", package]`
- cargo: `["cargo", "add", package]`
- Returns list form only — never shell string (T-04-02-03).

**VERIFICATION.md at step 7** (VER-01)
- Written atomically to `project_root/.planning/osbuilder/VERIFICATION.md`
- Two observable-behavior criteria (never "tests pass" language)
- Path uses `_resolve_project_root` which already rejected '..' traversal (T-04-02-04)

**Security mitigations (all from threat model):**
- T-04-02-01: `_safe_int()` wraps all `int(state.get(...))` calls with try/except ValueError
- T-04-02-02: slash commands are hardcoded strings from `PHASE_STEP_COMMANDS` — raw error strings never interpolated into output
- T-04-02-03: `build_install_cmd` returns `list[str]` only; all subprocess calls use `shell=False`
- T-04-02-04: VERIFICATION.md path constructed from `_resolve_project_root` (with '..' guard) + atomic write
- T-04-02-05: `retry_count` check happens before dispatch; always read from state.md

## Verification Results

```
# gsd_driver tests
16 passed, 0 skipped    ✓  (gate: 16 GREEN, 0 skipped)

# Full test suite
62 passed, 13 skipped   ✓  (failure_classifier + registry_verify still SKIP by design)

# Success criteria
SC1: pytest test_gsd_driver.py exits 0, 16 GREEN            ✓
SC2: pytest scripts/tests/ exits 0, 62 total                ✓
SC3: emit-next --project-root /tmp exits 1, no traceback    ✓
SC4: grep -c "shell=True" gsd_driver.py → 0                ✓
SC5: PHASE_STEP_COMMANDS in gsd_driver.py                   ✓
SC6: retry_count never initialized to 0 in driver           ✓
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all 16 test_gsd_driver.py stubs are now GREEN. The 13 remaining skipped tests (failure_classifier.py × 9 + registry_verify.py × 4) are intentional Wave 1 targets for plans 04-03 and 04-04.

## Threat Flags

No new security-relevant surface introduced beyond what the threat model already covers. All five T-04-02-xx mitigations are implemented as specified.

## TDD Gate Compliance

This plan is `type: tdd`. RED stubs were created in Plan 04-01 (commit c3cdcf4). GREEN implementation committed here (facda36). The RED→GREEN gate sequence is satisfied.

## Self-Check: PASSED
