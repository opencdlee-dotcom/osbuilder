---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
plan: "03"
subsystem: stack-research
tags: [python, subprocess, brainiac, stack-menu, fallback, json, stdlib]

# Dependency graph
requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    plan: "01"
    provides: test stubs for stack_researcher (RES-01..RES-04 RED state)
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    plan: "02"
    provides: state_writer.py ALLOWED_FIELDS extended with stack_choices/stack_overrides/project_path
provides:
  - scripts/stack_researcher.py — research_stack(app_type, project_root, advanced_overrides) -> dict
  - brainiac subprocess delegation with 30s timeout and fallback
  - hardcoded _WEB_DEFAULTS fallback when stack-menu.md absent (Wave 2 pre-ship safety)
  - stack_choices written to state.md via state_writer.py subprocess
  - argparse CLI: `python3 scripts/stack_researcher.py research --app-type web`
affects:
  - scaffold_dispatch.py (Plan 03-04) — reads stack_choices from state.md to select scaffolder
  - web playbook (Plan 03-05) — uses stack_choices to determine which packages to install

# Tech tracking
tech-stack:
  added: []
  patterns:
    - subprocess list-form (shell=False) for external process calls — T-3-02 shell injection mitigation
    - timeout=30 with exception-caught fallback to hardcoded defaults (T-3-07 DoS mitigation)
    - lazy import fixture (importlib.import_module) for TDD stubs already used in Phase 1/2

key-files:
  created:
    - scripts/stack_researcher.py
  modified: []

key-decisions:
  - "Hardcoded _WEB_DEFAULTS returned when stack-menu.md absent — ensures fallback works pre-Wave-2 without requiring the reference file to exist first"
  - "brainiac result augmented with source='brainiac' tag per key; fallback uses source='stack-menu' — enables downstream traceability of where each choice came from"
  - "state.md write failure is non-fatal (catch OSError + CalledProcessError, pass) — stack_choices always returned even when state.md not yet initialized"

patterns-established:
  - "Subprocess shell=False pattern: all external process calls use list-form argv, never shell=True, never interpolate user input into shell string"
  - "Fallback-then-fill pattern: brainiac result fills required keys; missing keys backfilled from _read_stack_menu() defaults"
  - "TDD RED->GREEN via importlib lazy fixture: test stubs skip before module exists, pass after"

requirements-completed: [RES-01, RES-02, RES-03, RES-04]

# Metrics
duration: 5min
completed: 2026-04-30
---

# Phase 03 Plan 03: Stack Researcher Summary

**stdlib-only stack_researcher.py with brainiac delegation, 30s timeout fallback to hardcoded web defaults, --advanced overrides, and state.md write — all 4 RES-01..RES-04 stubs GREEN**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-30T18:38:40Z
- **Completed:** 2026-04-30T18:40:45Z
- **Tasks:** 1 (TDD: RED confirmed SKIP -> GREEN)
- **Files modified:** 1

## Accomplishments
- Implemented `research_stack(app_type, project_root, advanced_overrides) -> dict` — the primary public function
- Brainiac subprocess call uses list-form argv, shell=False, timeout=30 (T-3-02 + T-3-07 mitigations)
- `_read_stack_menu()` parses `references/stack-menu.md` when present; returns hardcoded `_WEB_DEFAULTS` when absent (Wave 2 pre-ship safety net)
- `--advanced` overrides merge over researched result with override winning on any conflicting key (RES-04)
- `stack_choices` written to `state.md` via `state_writer.py` subprocess after research completes; write failure is non-fatal
- 190 lines, stdlib-only, no third-party deps

## Task Commits

1. **Task 1: Implement scripts/stack_researcher.py (RES-01..RES-04 GREEN)** — `1304f9f` (feat)

**Plan metadata:** (see final docs commit)

## Files Created/Modified
- `scripts/stack_researcher.py` — per-build stack researcher: brainiac delegation + stack-menu fallback + state.md write (190 lines, stdlib-only)

## Decisions Made
- Hardcoded `_WEB_DEFAULTS` returned by `_read_stack_menu()` when `stack-menu.md` absent — this is the documented fallback for pre-Wave-2 development, not a hand-rolled stack
- Brainiac result dict keys are augmented with `source="brainiac"` inline; missing keys backfilled from defaults — downstream code sees uniform `{name, version, source}` shape regardless of which source won
- `state.md` write failure wrapped in `try/except` and silenced — `research_stack()` always returns a usable dict, even if the project state file doesn't exist yet

## Deviations from Plan

None — plan executed exactly as written. Implementation followed the module structure, subprocess pattern, fallback pattern, and argparse pattern specified verbatim in the plan action block.

## Issues Encountered
None.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- `stack_researcher.py` is complete and tested (4/4 GREEN)
- `scaffold_dispatch.py` (Plan 03-04) can now read `stack_choices` from `state.md` to select the correct scaffolder command
- `references/stack-menu.md` (Wave 2 target) will augment the fallback when it ships; `_read_stack_menu()` is already wired to parse it

## Threat Surface Scan
No new network endpoints, auth paths, file access patterns, or schema changes introduced beyond what the plan's threat model covers. T-3-02, T-3-06, T-3-07, T-3-08 mitigations all implemented as specified.

---
*Phase: 03-intake-stack-research-web-playbook-one-playbook-e2e*
*Completed: 2026-04-30*
