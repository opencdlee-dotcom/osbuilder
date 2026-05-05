---
phase: 04-gsd-handoff-verify-loop-failure-classifier
plan: "03"
subsystem: failure-handling
tags: [failure-classifier, tdd, green, regex, backoff, escalation, pure-function]

dependency_graph:
  requires:
    - phase: "04-01"
      provides: "RED stubs for test_failure_classifier.py (9 stubs, HEAL-01..04)"
  provides:
    - "classify() pure function: 4-class pattern matching with validation-first priority"
    - "handle_transient() with BACKOFF_SECONDS {0:1, 1:4, 2:16} exponential backoff"
    - "build_escalation_handoff() producing structured markdown handoff"
    - "CLI subcommand: failure_classifier classify --error --retry-count"
  affects:
    - scripts/gsd_driver.py

tech-stack:
  added: []
  patterns:
    - "Validation-before-transient pattern: VALIDATION_FAILURE_PATTERNS checked first to prevent test.*failed misclassification"
    - "Pure-function pattern: classify() and build_escalation_handoff() have no file I/O, no subprocess, no global state"
    - "Hard-coded backoff table pattern: BACKOFF_SECONDS dict caps sleep at 21s total across 3 retries"

key-files:
  created:
    - scripts/failure_classifier.py
  modified: []

key-decisions:
  - "VALIDATION_FAILURE_PATTERNS checked before TRANSIENT_PATTERNS in classify() — prevents 'test.*failed' matching transient; test asserts class=validation-failure"
  - "handle_transient() called from classify() for transient class — avoids duplicating backoff logic in two places"
  - "time.sleep() called directly on time module (import time; time.sleep()) so monkeypatch.setattr('time.sleep', ...) intercepts correctly in tests"
  - "utcnow() used in build_escalation_handoff() per plan template — deprecation warning acceptable in Python 3.12+; stdlib only, no third-party deps"

requirements-completed: [HEAL-01, HEAL-02, HEAL-03, HEAL-04, HEAL-07]

duration: 8min
completed: "2026-04-30"
---

# Phase 04 Plan 03: failure_classifier.py Summary

**Pure-function error classifier with 4-class pattern matching (validation-first), exponential backoff handler, and structured markdown escalation handoff — all 9 RED stubs now GREEN.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-30T20:40:00Z
- **Completed:** 2026-04-30T20:48:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Implemented `classify()` with validation-first pattern priority: VALIDATION_FAILURE_PATTERNS checked before TRANSIENT_PATTERNS, preventing "test.*failed" from being misclassified as transient
- Implemented `handle_transient()` with `BACKOFF_SECONDS = {0: 1, 1: 4, 2: 16}` and `time.sleep()` side effect; monkeypatch-compatible
- Implemented `build_escalation_handoff()` returning structured markdown with "OSBuilder Escalation Handoff", "Last Error", "What Was Tried", "State Checkpoint", and "Recommended Next Action" sections
- All 9 `test_failure_classifier.py` stubs now GREEN; full suite: 71 passed, 4 skipped (no regressions)
- Security: 0 occurrences of `eval`, `exec`, or `shell=True`; error string treated as data only (regex matching)

## Task Commits

1. **Task 1: Implement failure_classifier.py** - `46e28d9` (feat)

**Plan metadata:** _(to be added with final metadata commit)_

## Files Created/Modified

- `scripts/failure_classifier.py` — Pure-function classifier: `classify()`, `handle_transient()`, `build_escalation_handoff()`, `main()` CLI via argparse

## Decisions Made

- VALIDATION_FAILURE_PATTERNS declared and checked first — the plan explicitly flags this as the "most dangerous pitfall" since `r"test.*failed"` would match "pnpm install failed: ..." if transient were checked first
- `handle_transient()` is called from within `classify()` when TRANSIENT_PATTERNS match, avoiding duplication of the `retry_count >= 3` / `BACKOFF_SECONDS` logic
- Used `import time; time.sleep(wait)` (not `from time import sleep`) so `monkeypatch.setattr("time.sleep", ...)` patches the attribute on the `time` module object and is correctly intercepted by `handle_transient()`
- `datetime.utcnow()` used per plan's implementation template — deprecation warning is harmless (stdlib only, no third-party deps added)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. All 9 tests passed on first implementation attempt.

## Known Stubs

None — `failure_classifier.py` is fully implemented with real logic. No hardcoded empty values or placeholder text.

## Threat Flags

No new security-relevant surface beyond what was in the plan's threat model:

- T-04-03-01 (Tampering/error string): mitigated — `classify()` uses regex matching only; no `eval()`, `exec()`, or `shell=True`
- T-04-03-02 (Tampering/misclassification): mitigated — VALIDATION_FAILURE_PATTERNS at line 27, TRANSIENT_PATTERNS at line 49; test_validation_failure asserts `class=validation-failure` for "test.*failed" inputs
- T-04-03-03 (Tampering/escalation injection): mitigated — `last_error` is interpolated inside a fenced code block in the markdown template
- T-04-03-04 (DoS/sleep): accepted — BACKOFF_SECONDS hard-coded; maximum 21 seconds total across 3 retries

## Next Phase Readiness

- `failure_classifier.py` is ready to be imported by `gsd_driver.py` (Phase 04 Plan 02 already GREEN)
- Remaining RED stubs in `test_registry_verify.py` (4 stubs) are the target of Plan 04-04
- `test_gsd_driver.py` stubs for HEAL-06, HEAL-07 are covered by the gsd_driver.py GREEN state from Plan 04-02

## Self-Check: PASSED

- `scripts/failure_classifier.py` exists on disk: confirmed
- Commit `46e28d9` confirmed in git log
- `python3 -m pytest scripts/tests/test_failure_classifier.py` → 9 passed
- `python3 -m pytest scripts/tests/` → 71 passed, 4 skipped, 0 errors

---
*Phase: 04-gsd-handoff-verify-loop-failure-classifier*
*Completed: 2026-04-30*
