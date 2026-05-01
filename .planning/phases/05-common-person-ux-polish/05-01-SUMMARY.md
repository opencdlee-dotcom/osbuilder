---
phase: 05-common-person-ux-polish
plan: "01"
subsystem: phase-5-wave-0-test-scaffolding
tags:
  - red-tdd
  - test-scaffolding
  - state-extension
  - tech-writer-slot
  - nyquist-compliance
requirements:
  - UX-01
  - UX-02
  - UX-03
  - UX-04
  - UX-05
  - ROLE-07
  - ROLE-09
dependency-graph:
  requires:
    - scripts/tests/conftest.py (writer + tmp_project_root fixtures)
    - scripts/tests/test_failure_classifier.py (lazy-import fixture pattern)
    - scripts/state_writer.py (existing ALLOWED_FIELDS set literal)
    - scripts/gsd_driver.py (existing PHASE_STEP_COMMANDS dict + phase-advance block)
  provides:
    - 46 Phase 5 RED test stubs (collected, all skip until Wave 1)
    - state_writer.ALLOWED_FIELDS gain mode/tutor_enabled/humanizer_score/build_log_path
    - gsd_driver.PHASE_STEP_COMMANDS gains key 9 → /gsd-docs-update
    - phase-advance condition shifted to phase_step == 10
  affects:
    - All Phase 5 Wave 1 plans (05-02 through 05-05) — their test targets exist before code
tech-stack:
  added: []
  patterns:
    - lazy-import-fixture (copied from test_failure_classifier.py)
    - pytest.skip("Wave 1 target") for every stub body
    - ALLOWED-only state-field extension (no new REQUIRED fields)
key-files:
  created:
    - scripts/tests/test_narration.py
    - scripts/tests/test_friendly_error.py
    - scripts/tests/test_tutor_mode.py
    - scripts/tests/test_mode_gating.py
    - scripts/tests/test_tech_writer.py
    - .planning/phases/05-common-person-ux-polish/05-01-SUMMARY.md
  modified:
    - scripts/state_writer.py
    - scripts/gsd_driver.py
decisions:
  - "Stub bodies use pytest.skip not xfail — skips are visible in collection and Wave 1 simply replaces the skip line with assertions."
  - "Key 9 in PHASE_STEP_COMMANDS is a temporary placeholder — Plan 05-05 will remove it and replace with an in-line handler invoking the tech-writer + humanizer pipeline."
  - "test_tech_writer.py stubs assert on emit_next_command stdout (behavior), never on PHASE_STEP_COMMANDS[9] dict access — guards Wave 2 refactor from breaking the test surface."
  - "Schema field count is 9 (not the SPEC's pre-research 8); RESEARCH.md is authoritative — expansion_note is field 9."
  - "Phase-advance shifts to phase_step == 10 in Wave 0 even though no Wave 1 test pins step 9 advance behavior; the Wave 1 test test_phase_step_10_advances_phase will exercise the new condition."
metrics:
  duration: ~6 minutes (small file edits + verification)
  tasks: 2
  files: 7 (5 created, 2 modified)
  completed: 2026-05-01
---

# Phase 5 Plan 01: Wave 0 RED Stubs + Phase-Step Wiring Summary

**One-liner:** Drops 46 Phase 5 RED test stubs and wires the four ALLOWED state fields plus the tech-writer step-9 slot, so Phase 5 Wave 1 plans have a verification surface from the moment they start.

## Outcome

Plan 05-01 closes the Nyquist-compliance gap for Phase 5: every Phase 5 feature now has at least one named, collected test before any module is written. The full pytest collection went from 78 → 124, all new stubs skip cleanly with `Wave 1 target` (no errors, no failures), and the existing 78 Phase 4 tests stay green after the gsd_driver step renumber. State_writer accepts four new beginner/advanced/tutor/humanizer/build-log fields without forcing them into REQUIRED_FIELDS, preserving Phase 1–4 backward compatibility. PHASE_STEP_COMMANDS gains a `/gsd-docs-update` slot at key 9, with the phase-advance condition shifted to `phase_step == 10` so step 9 can host the tech-writer pipeline in Plan 05-05.

## Tasks Executed

| Task | Description | Files | Commit |
|---|---|---|---|
| 1 | Wave 0 RED stubs — 5 new test files (46 stubs) | scripts/tests/test_{narration,friendly_error,tutor_mode,mode_gating,tech_writer}.py | 854666f |
| 2 | state_writer ALLOWED_FIELDS + gsd_driver step 9→10 renumber | scripts/state_writer.py, scripts/gsd_driver.py | 6679097 |

### Stub inventory (Task 1)

| File | Stubs | Coverage |
|---|---|---|
| test_narration.py | 15 | UX-04, ROLE-09 |
| test_friendly_error.py | 11 | UX-02, UX-05 |
| test_tutor_mode.py | 8 | UX-01 |
| test_mode_gating.py | 6 | UX-03 |
| test_tech_writer.py | 6 | ROLE-07 |
| **Total** | **46** | 7 requirements × ≥1 stub each |

All bodies are `pytest.skip("Wave 1 target")`; lazy-import fixtures mirror the `test_failure_classifier.py` pattern verbatim (renamed `fc` → `nrt` / `fe` / `gd` / `intake` / `researcher`).

### State + dispatch wiring (Task 2)

- `state_writer.ALLOWED_FIELDS` += `{ "mode", "tutor_enabled", "humanizer_score", "build_log_path" }` — appended inside the existing set literal, no REQUIRED_FIELDS change, no new write paths.
- `gsd_driver.PHASE_STEP_COMMANDS[9]` = `"/gsd-docs-update"` (was a comment-only in-line slot).
- `gsd_driver.emit_next_command` phase-advance check shifted from `phase_step == 9` to `phase_step == 10`.
- Header comment updated: in-line steps are now 2, 7, 10.

## Verification

| Check | Expected | Result |
|---|---|---|
| `pytest --collect-only` count | ≥ 122 | **124** |
| Phase 4 suite | 78 passed, 0 failed, 0 errors | **78 passed, 46 skipped, 1 pre-existing warning** |
| `state_writer.ALLOWED_FIELDS` contains 4 new fields | yes | yes (verified via `python3 -c "..."`) |
| `gsd_driver.PHASE_STEP_COMMANDS[9]` == `/gsd-docs-update` | yes | yes |
| `10 not in gsd_driver.PHASE_STEP_COMMANDS` (phase advance is in-line) | true | true |
| `test_friendly_error.py` has renamed stubs (no `test_all_error_paths_wrapped`) | both renamed pair | both present |
| `test_tech_writer.py` no direct `gd.PHASE_STEP_COMMANDS[9]` code access | comment-only mention permitted | only the warning docstring mentions it; no code-level access |

## Deviations from Plan

None — plan executed exactly as written.

The plan's Task 2 step C asked me to grep `test_gsd_driver.py` for any test pinning `phase_step=9 → current_phase increments`; no such test exists, so no test edit was needed. (Existing tests at `phase_step=8` for `/gsd-verify-work` and at increment-to-1 for `test_state_updates_after_emission` continue to pass — the renumber only touches the advance path, which no Phase 4 test currently exercises.)

## Threat Model Compliance

- **T-05-01-01 (Tampering — ALLOWED_FIELDS extension):** Mitigated. Four new fields appended inside the existing set literal; `_check_field_allowed` automatically gates them via the same allowlist check; `_check_value_safe` continues to reject newlines and `..` in values.
- **T-05-01-02 (Repudiation — silent skips):** Accepted as designed. All 46 stubs use `pytest.skip("Wave 1 target")` not `xfail`; skip lines are visible in `pytest -v` output; Wave 1 plans replace each skip with concrete assertions.
- **T-05-01-03 (Tampering — PHASE_STEP_COMMANDS step 9 insertion):** Mitigated. All 78 Phase 4 tests re-run green after the change; `/gsd-docs-update` is a slash command (not a shell command), and the dict-key insertion path uses no shell interpolation.

No new threat surface introduced.

## Self-Check

- All 5 test files exist: ✓ FOUND
- state_writer.py contains the 4 new ALLOWED fields: ✓ FOUND
- gsd_driver.py PHASE_STEP_COMMANDS has key 9 → "/gsd-docs-update": ✓ FOUND
- gsd_driver.py phase-advance condition is `phase_step == 10`: ✓ FOUND
- Commit 854666f exists: ✓ FOUND
- Commit 6679097 exists: ✓ FOUND
- Task 1 verify command: 124 tests collected (target ≥ 122): ✓ PASS
- Task 2 verify command: 78 passed, 46 skipped, 0 failed, 0 errored: ✓ PASS

## Self-Check: PASSED

## Next

Phase 5 Wave 1 plans (05-02 through 05-05) flip these stubs from RED to GREEN by creating the corresponding modules: `scripts/narration.py`, `scripts/friendly_error.py`, `references/friendly-errors/dictionary.yaml`, `references/roles/{pm,architect,frontend,backend,devops,reviewer,tech-writer}.md`, and the mode-gate / error-translate wiring in `preflight_check.py` / `scaffold_dispatch.py` / `stack_researcher.py` / `intake_handler.py` / `gsd_driver.py`.
