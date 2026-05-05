---
phase: 07-additional-playbooks
plan: 06
subsystem: testing
tags: [e2e, parametrized, pytest, slow-marker, uat, phase-7, ai-service, cli, desktop, hub]

# Dependency graph
requires:
  - phase: 07-additional-playbooks
    provides: scaffold_ai_service, scaffold_cli, scaffold_desktop, scaffold_hub — the 4 playbooks under test
  - phase: 06-ship-to-private-github-scalable-defaults
    provides: 06-HUMAN-UAT.md format (mirrored for 07-HUMAN-UAT.md)
provides:
  - scripts/tests/test_e2e_playbooks.py — parametrized 5-step E2E contract across all 4 Phase 7 playbooks
  - .planning/phases/07-additional-playbooks/07-HUMAN-UAT.md — 6 human-judged UAT gates
  - slow marker in pyproject.toml — opt-out gating for E2E test file
affects: [08-production-ready, future-phases-using-e2e-harness]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parametrized E2E with per-playbook TIMEOUTS dict (Pitfall 8 — desktop=120s)"
    - "Module-top _real_run = subprocess.run capture (recursion-safe; STATE.md rule)"
    - "Cross-platform process group teardown: POSIX os.killpg vs Windows proc.terminate()"
    - "pytestmark = pytest.mark.slow at module level gates entire file from default pytest run"
    - "06-HUMAN-UAT.md 4-line per-test shape (expected/test/why_human/result) mirrored for Phase 7"

key-files:
  created:
    - scripts/tests/test_e2e_playbooks.py
    - .planning/phases/07-additional-playbooks/07-HUMAN-UAT.md
  modified:
    - pyproject.toml

key-decisions:
  - "pytestmark = pytest.mark.slow at module level (not per-test decorator) — entire file gated, default run stays fast"
  - "hub E2E boot step is no-op (no uv/pnpm/cargo for hub); assertion is structural diff vs snapshot"
  - "cli E2E boot step uses <app-name> --help (no long-running server needed)"
  - "TIMEOUTS dict uses playbook key strings matching _PLAYBOOK_DISPATCH keys in scaffold_dispatch.py"

patterns-established:
  - "Per-playbook TIMEOUTS dict pattern: any future playbook E2E test should add an entry with install+boot timeouts"
  - "UAT file format: status/phase/source frontmatter + ## Current Test + ## Tests with 4-line shape per test"

requirements-completed: [SCAF-02, SCAF-03, SCAF-04, SCAF-05]

# Metrics
duration: 2min (continuation from prior checkpoint; prior task committed at 6d69ae9)
completed: 2026-05-02
---

# Phase 7 Plan 06: E2E Harness + UAT Summary

**Single parametrized E2E file (test_e2e_playbooks.py) covers 4 playbooks via 5-step contract; 07-HUMAN-UAT.md provides 6 human-judged stranger-clone gates mirroring Phase 6 UAT format**

## Performance

- **Duration:** ~2 min (continuation agent; Task 1 committed prior session at 6d69ae9)
- **Started:** 2026-05-02T17:31:44Z
- **Completed:** 2026-05-02T17:32:34Z
- **Tasks:** 2 (Task 1 committed in prior session; Task 2 committed in this session)
- **Files modified:** 3

## Accomplishments

- D-17 implemented: `test_e2e_playbooks.py` provides a single `@pytest.mark.parametrize` covering ai-service / cli / desktop / hub-platform with the 5-step intake → scaffold → install → boot → stop contract
- D-18 implemented: per-playbook `TIMEOUTS` dict (desktop install=120s, ai-service=60s, cli=30s, hub=5s) prevents cold-Cargo-fetch flakes per Pitfall 8
- D-19 implemented: `07-HUMAN-UAT.md` mirrors 06-HUMAN-UAT.md format with 6 tests (4 stranger-clone gates + Electron-refusal + /summarize Pydantic v2 smoke)
- `slow` marker registered in `pyproject.toml`; default `pytest` run skips the 4 E2E cases, keeping suite runtime at ~18s
- Full test suite: 189 passed, 1 skipped, 4 deselected (E2E gated) — all GREEN

## Task Commits

1. **Task 1: E2E test file + slow marker** - `6d69ae9` (feat)
2. **Task 2: 07-HUMAN-UAT.md** - `5e28483` (docs)

**Plan metadata:** (this commit — docs: complete plan)

## Files Created/Modified

- `scripts/tests/test_e2e_playbooks.py` (247 lines, NEW) — parametrized 5-step E2E test; `_real_run` capture; per-playbook `TIMEOUTS`; cross-platform `os.killpg` / `proc.terminate()` teardown; `pytestmark = pytest.mark.slow`
- `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` (57 lines, NEW) — 6 UAT tests in 4-line shape; mirrors 06-HUMAN-UAT.md format
- `pyproject.toml` (MODIFIED) — `slow` marker added to `[tool.pytest.ini_options].markers`

## Decisions Made

- `pytestmark = pytest.mark.slow` at module level (not per-test decorator) so the entire file is gated in one place — consistent with SC-05 goal of "run E2E only on machines with full preflight"
- hub playbook E2E boot step is a structural diff (no runtime server); avoids requiring pnpm/cargo for hub-specific assertions
- cli playbook boot step uses `<app-name> --help` instead of a long-running server — appropriate for CLI tools

## Deviations from Plan

None — plan executed exactly as written. Task 1 was committed in the prior session; Task 2 (UAT file) was created in the prior session and committed after user approval in this continuation session.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Full E2E execution (SC-05 contract verification) requires `uv`, `pnpm`, and `cargo` on the machine and is gated by `@pytest.mark.slow`; run with `uv run pytest -m slow scripts/tests/test_e2e_playbooks.py`.

## E2E Execution Note

The `test_e2e_playbooks.py` file is skipped by default (`-m 'not slow'`). Full SC-05 verification requires:
- `uv` installed (ai-service + cli playbooks)
- `pnpm` + Rust/cargo installed (desktop playbook)
- A machine with network access (cold uv/cargo installs)

Run: `uv run pytest -m slow scripts/tests/test_e2e_playbooks.py -x -v`

The 5-minute stranger-clone budget (per SC-05) requires human runners following `07-HUMAN-UAT.md`.

## Next Phase Readiness

- Phase 7 plan 06 complete — all 6 Phase 7 plans now complete
- All 4 SCAF-* requirements (SCAF-02..SCAF-05) marked complete
- Phase 8 (`--production-ready`) is unblocked
- The E2E harness pattern (parametrized per-playbook test with TIMEOUTS dict) is available as a template for future playbooks

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
