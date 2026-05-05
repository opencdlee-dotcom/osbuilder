---
phase: 04-gsd-handoff-verify-loop-failure-classifier
plan: "01"
subsystem: test-infrastructure
tags: [wave-0, tdd, red-stubs, state-writer, nyquist-gate]
dependency_graph:
  requires: []
  provides:
    - "RED test stubs for gsd_driver (ROLE-01..06, ROLE-08, HEAL-06, HEAL-07, VER-01..04)"
    - "RED test stubs for failure_classifier (HEAL-01..04, HEAL-07)"
    - "RED test stubs for registry_verify (HEAL-05)"
    - "state_writer.py ALLOWED_FIELDS extended with gsd_phase_count, failure_class, escalation_log"
  affects:
    - scripts/state_writer.py
    - scripts/tests/test_gsd_driver.py
    - scripts/tests/test_failure_classifier.py
    - scripts/tests/test_registry_verify.py
tech_stack:
  added: []
  patterns:
    - "Lazy-import fixture pattern (importlib.import_module → pytest.skip on ImportError)"
    - "Nyquist gate: >= 71 collected before Wave 1 implementation begins"
key_files:
  created:
    - scripts/tests/test_gsd_driver.py
    - scripts/tests/test_failure_classifier.py
    - scripts/tests/test_registry_verify.py
  modified:
    - scripts/state_writer.py
decisions:
  - "Added gsd_phase_count, failure_class, escalation_log to ALLOWED_FIELDS only (not REQUIRED_FIELDS) — same pattern as Phase 3 optional fields"
  - "75 tests collected exceeds Nyquist gate of 71; 29 new stubs all SKIP when Wave 1 modules absent"
metrics:
  duration_seconds: 148
  completed_date: "2026-04-30"
  tasks_completed: 2
  files_created: 3
  files_modified: 1
---

# Phase 04 Plan 01: Wave 0 RED Stubs + state_writer Extension Summary

**One-liner:** Three test files with 29 lazy-import RED stubs + three new ALLOWED_FIELDS in state_writer.py establish the Phase 4 Nyquist gate (75 collected) before Wave 1 implementation.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend state_writer.py ALLOWED_FIELDS for Phase 4 | 315adf1 | scripts/state_writer.py |
| 2 | Drop >= 25 RED stubs across three new test files | c3cdcf4 | scripts/tests/test_gsd_driver.py, scripts/tests/test_failure_classifier.py, scripts/tests/test_registry_verify.py |

## What Was Built

### Task 1 — state_writer.py Extension

Extended `ALLOWED_FIELDS` with three Phase 4 fields (ALLOWED only, not REQUIRED — same pattern as Phase 3 `project_path`, `stack_choices`, `stack_overrides`):

- `gsd_phase_count` — total phases discovered from GSD ROADMAP.md
- `failure_class` — last classified failure class for resume
- `escalation_log` — JSON array of escalation steps taken

The existing `_check_field_allowed` V5 allowlist enforcement and `_check_value_safe` V12 path-traversal mitigations automatically protect the new fields without any code changes.

### Task 2 — RED Stub Test Files

**test_gsd_driver.py** — 16 stubs covering the GSD command-emission state machine:
- ROLE-01..06, ROLE-08: `/gsd-new-project`, `/gsd-spec-phase`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/code-tester`, `/predator`, `/gsd-code-review`, escalation at retry limit
- HEAL-06: `--ignore-scripts` in install command
- HEAL-07: `emit_next_command` preserves retry_count on resume
- VER-01..04: VERIFICATION.md written at step 7, falsifiability rule, `/gsd-verify-work` at step 8, `/code-tester` + `/predator` per phase
- State machine: `phase_step` increments after each emission

**test_failure_classifier.py** — 9 stubs:
- HEAL-01: classify() maps ECONNRESET→transient, context window→context-overflow, command-not-found→tool-failure, assertion error→validation-failure
- HEAL-02: handle_transient() applies exponential backoff (1s at retry 0, 4s at retry 1)
- HEAL-03: retry_count >= 3 returns retry_ok=False
- HEAL-04: build_escalation_handoff() produces structured "OSBuilder Escalation Handoff" string

**test_registry_verify.py** — 4 stubs:
- HEAL-05: verify_npm() returns False for 404, True for 200, True for network error (fail-open)
- HEAL-05: verify_pypi() returns False for 404

All three files use the lazy-import fixture pattern: `importlib.import_module` inside a fixture that calls `pytest.skip()` on ImportError — ensuring individual test names always appear in `--collect-only` output even when modules don't exist yet.

## Verification Results

```
75 tests collected (gate: >= 71)  ✓
46 passed, 29 skipped              ✓  (existing: 46 green; new: 29 SKIP)
ALLOWED_FIELDS OK                  ✓
```

Per-file counts:
- test_gsd_driver.py: 16 (gate: >= 14)  ✓
- test_failure_classifier.py: 9 (gate: >= 8)  ✓
- test_registry_verify.py: 4 (gate: >= 3)  ✓

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

By design, all 29 new test stubs skip when their target modules are absent (Wave 1 will implement gsd_driver.py, failure_classifier.py, registry_verify.py). These are intentional RED stubs, not unintentional omissions. Wave 1 plans (04-02 through 04-05) will flip them GREEN.

## Threat Flags

No new security-relevant surface introduced. state_writer.py ALLOWED_FIELDS extension is covered by existing T-04-01-01 mitigation (allowlist enforcement via `_check_field_allowed` remains intact). New fields still pass through `_check_value_safe`.

## Self-Check: PASSED

All created files exist on disk. Both task commits (315adf1, c3cdcf4) confirmed in git log. 75 tests collected, 46 passed, 29 skipped — no ERRORs.
