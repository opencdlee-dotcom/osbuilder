---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
plan: "01"
subsystem: testing
tags: [pytest, tdd-red, wave-0, lazy-import-fixture, test-infrastructure]

requires:
  - phase: 02-pre-flight-installer-cross-platform
    provides: conftest.py with fake_shell/fake_which/tmp_project_root fixtures; Phase 2 proven Wave 0→Wave 1 pattern
provides:
  - 16 RED test stubs across 3 new test files (IN-01..IN-05, RES-01..RES-04, SCAF-01/SCAF-06)
  - Test contract that Wave 1 plans (03-02, 03-03, 03-04, 03-05) must satisfy to flip stubs GREEN
  - Security assertions encoded as test contracts: --yes absent, no real secrets in .env.example, compose.yaml vs docker-compose.yml
affects: [03-02, 03-03, 03-04, 03-05]

tech-stack:
  added: []
  patterns:
    - "Lazy-import-via-fixture: importlib.import_module inside fixture → pytest.skip on ImportError; keeps stubs collectable before module exists"
    - "Wave 0 RED stubs: placeholder test bodies calling not-yet-existing symbols; all SKIPPED, never ERROR"

key-files:
  created:
    - scripts/tests/test_intake.py
    - scripts/tests/test_stack_researcher.py
    - scripts/tests/test_scaffold_dispatch.py
  modified: []

key-decisions:
  - "Lazy-import-via-fixture pattern (not pytest.importorskip at module top) — importorskip causes whole-file collection skip and breaks >=16 stubs Wave 0 gate"
  - "Security assertions encoded as test contracts: --yes absent (T-3-01), .env.example placeholder-only (T-3-04), compose.yaml not docker-compose.yml (Pitfall 3)"
  - "test_intake.py docstring explicitly mentions pytest.importorskip as the anti-pattern to avoid — word appears in comment, not as a call; both other files have zero occurrences"

requirements-completed: [IN-01, IN-02, IN-03, IN-04, IN-05, RES-01, RES-02, RES-03, RES-04, SCAF-01, SCAF-06]

duration: 3min
completed: 2026-04-30
---

# Phase 03 Plan 01: Wave 0 Test Infrastructure Summary

**16 RED pytest stubs across test_intake.py (5), test_stack_researcher.py (4), test_scaffold_dispatch.py (7) — all SKIPPED, 46 total collected, security guards encoded as test assertions**

## Performance

- **Duration:** 3 min 5 sec
- **Started:** 2026-04-30T18:28:24Z
- **Completed:** 2026-04-30T18:31:29Z
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments

- Created 3 test files with 16 RED stubs covering IN-01..IN-05, RES-01..RES-04, SCAF-01, SCAF-06
- Brought pytest --collect-only from 30 to 46 tests (30 baseline still GREEN, 16 new SKIPPED)
- Encoded Wave 1 implementation contract in test assertions: exact fixture API signatures, file paths, content patterns, security guards
- Security assertions: `--yes` absent from create-next-app command (T-3-01/Pitfall 1), no real credentials in .env.example (T-3-04), `compose.yaml` present and `docker-compose.yml` absent (Compose v2 vs v1)

## Task Commits

1. **Task 1: Create test_intake.py — 5 RED stubs (IN-01..IN-05)** - `2d0d33b` (test)
2. **Task 2: Create test_stack_researcher.py + test_scaffold_dispatch.py — 4+7 RED stubs** - `87a8e1b` (test)

## Files Created/Modified

- `scripts/tests/test_intake.py` — 5 stubs: paragraph→spec (IN-01), structured→spec (IN-02), jargon-free bank (IN-03), you-decide option (IN-04), format+secrets gate (IN-05)
- `scripts/tests/test_stack_researcher.py` — 4 stubs: brainiac call (RES-01), structured output (RES-02), fallback (RES-03), advanced override (RES-04)
- `scripts/tests/test_scaffold_dispatch.py` — 7 stubs: web playbook exists (SCAF-01), create-next-app flags (SCAF-06 x6)

## Decisions Made

- Lazy-import-via-fixture pattern confirmed as the standard for Wave 0 stubs — `pytest.importorskip` at module top causes the entire file to disappear from `--collect-only`, breaking the >=N stubs gate
- `test_intake.py` docstring explains the anti-pattern by name; this is the plan-specified content verbatim; the actual call is absent
- Security threat mitigations (T-3-01, T-3-04, Compose v1 vs v2) encoded directly as test assertions so Wave 1 implementation is forced to satisfy them

## Deviations from Plan

None — plan executed exactly as written. All three test files match the specified content and patterns. All 16 stubs SKIPPED (not ERROR). Forbidden `pytest.importorskip(...)` call pattern absent from all files.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Wave 0 complete: `pytest --collect-only` reports 46 tests (30 baseline + 16 new stubs)
- 03-VALIDATION.md `wave_0_complete` field can be flipped to `true`
- Wave 1 plans (03-02 intake_handler, 03-03 stack_researcher, 03-04 scaffold_dispatch, 03-05 web playbook + state_writer extension) can now proceed — each will flip its assigned RED stubs to GREEN

---
*Phase: 03-intake-stack-research-web-playbook-one-playbook-e2e*
*Completed: 2026-04-30*

## Self-Check: PASSED

Files exist:
- `scripts/tests/test_intake.py`: FOUND
- `scripts/tests/test_stack_researcher.py`: FOUND
- `scripts/tests/test_scaffold_dispatch.py`: FOUND

Commits exist:
- `2d0d33b`: FOUND
- `87a8e1b`: FOUND

Test counts: 46 total (30 passed + 16 skipped) — gate satisfied.
