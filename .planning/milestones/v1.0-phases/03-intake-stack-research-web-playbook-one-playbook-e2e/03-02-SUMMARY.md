---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
plan: "02"
subsystem: intake
tags: [python, stdlib, tdd, derived_spec, state_writer, intake_handler]

requires:
  - phase: 03-01
    provides: "16 RED stubs (test_intake.py x5, test_stack_researcher.py x4, test_scaffold_dispatch.py x7) — this plan turns 3 intake stubs GREEN"

provides:
  - "scripts/intake_handler.py: parse_paragraph() and parse_structured() → derived_spec.md"
  - "scripts/state_writer.py: ALLOWED_FIELDS extended with project_path, stack_choices, stack_overrides"
  - "derived_spec.md written atomically to <project-root>/.planning/osbuilder/derived_spec.md"

affects:
  - "03-03 (stack_researcher.py needs state_writer ALLOWED_FIELDS: stack_choices)"
  - "03-04 (scaffold_dispatch.py needs state_writer ALLOWED_FIELDS: project_path)"
  - "03-05 (question-bank.md — IN-03/IN-04 tests currently SKIPPED, will go GREEN)"

tech-stack:
  added: []
  patterns:
    - "Lazy-import fixture pattern (ih fixture) for TDD RED/GREEN without breaking pytest collection"
    - "atomic_write() copy from state_writer.py (idiomatic — not imported to keep stdlib-only boundary)"
    - "_resolve_project_root() copy from state_writer.py (same pattern, consistent behavior)"
    - "ALLOWED_FIELDS extended with | operator — Phase 3 optional fields never break Phase 1/2 validate"

key-files:
  created:
    - scripts/intake_handler.py
  modified:
    - scripts/state_writer.py

key-decisions:
  - "ALLOWED_FIELDS only (not REQUIRED_FIELDS): project_path/stack_choices/stack_overrides are optional so Phase 1/2 state.md files continue to pass validate"
  - "parse_paragraph treats input as data only (T-3-03) — never executed or interpolated into shell"
  - "_validate_project_name uses re.match(r'^[a-zA-Z0-9_-]+$') (T-3-01) — whitelist approach"
  - "intake_handler.py copies atomic_write/resolve_project_root verbatim from state_writer.py rather than importing to preserve stdlib-only isolation"

patterns-established:
  - "Render helper (_render_derived_spec) returns string; caller does atomic_write — separation of concerns"
  - "_REQUIRED_SECTIONS and _SECRET_PATTERNS as module-level tuples — cheap to scan, easy to extend"

requirements-completed: [IN-01, IN-02, IN-03, IN-04, IN-05]

duration: 4min
completed: "2026-04-30"
---

# Phase 03 Plan 02: Intake Handler Summary

**stdlib-only intake_handler.py converts plain-English paragraph or structured dict into derived_spec.md (the /gsd-new-project --auto handoff document) via atomic writes, with path-traversal and secret-pattern guards**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-30T18:33:24Z
- **Completed:** 2026-04-30T18:37:36Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `scripts/intake_handler.py` created (186 lines, stdlib-only): `parse_paragraph()` and `parse_structured()` write canonical `derived_spec.md` to `<project-root>/.planning/osbuilder/derived_spec.md`
- `scripts/state_writer.py` extended: `ALLOWED_FIELDS` now includes `project_path`, `stack_choices`, `stack_overrides` (optional — `REQUIRED_FIELDS` unchanged, Phase 1/2 state files stay valid)
- 3 intake TDD stubs (IN-01, IN-02, IN-05) turned GREEN; 2 question-bank stubs remain SKIPPED (Wave 2, Plan 03-05)
- Full test suite: 33 passed / 13 skipped / 0 failed (up from 30/16/0)

## Task Commits

1. **Task 1: Extend state_writer ALLOWED_FIELDS** — `0599775` (feat)
2. **Task 2: Implement intake_handler.py** — `e85cb4b` (feat)

**Plan metadata:** _(pending docs commit)_

## Files Created/Modified

- `scripts/intake_handler.py` — New: parse_paragraph(), parse_structured(), _render_derived_spec(), atomic_write(), _validate_project_name(), argparse CLI (parse/validate subcommands)
- `scripts/state_writer.py` — Modified: ALLOWED_FIELDS extended with project_path, stack_choices, stack_overrides

## Decisions Made

- ALLOWED_FIELDS extension only (not REQUIRED_FIELDS) so Phase 1/2 state.md files pass `validate` without the new fields
- `intake_handler.py` copies `atomic_write` and `_resolve_project_root` verbatim from `state_writer.py` rather than importing, preserving the stdlib-only / no-cross-script-import boundary
- `_validate_project_name` uses `re.match(r"^[a-zA-Z0-9_-]+$")` (whitelist) — matches T-3-01 threat mitigation
- `parse_paragraph` treats user text as data-only (never passed to eval/exec/subprocess) — T-3-03

## Deviations from Plan

None — plan executed exactly as written. The 186-line refactor was within the REFACTOR step of the TDD cycle (initial draft was 233 lines; condensed section comments and list comprehensions to meet ≤ 200 line acceptance criterion).

## Issues Encountered

Initial write of `intake_handler.py` was 233 lines (exceeds 200-line limit). Condensed during REFACTOR step: replaced multi-line list building with list comprehension extensions, moved `_REQUIRED_SECTIONS` and `_SECRET_PATTERNS` to module-level constants, tightened docstrings. Final: 186 lines.

## Known Stubs

None — `parse_paragraph` and `parse_structured` are fully wired and write real content to disk. The 2 SKIPPED tests (`test_questions_have_no_jargon`, `test_questions_have_you_decide_option`) skip because `references/question-bank.md` does not yet exist — Plan 03-05 (Wave 2) creates it and those tests will go GREEN.

## Threat Flags

None — all threat mitigations from the plan's `<threat_model>` were implemented:
- T-3-01: `_validate_project_name` with `re.match(r"^[a-zA-Z0-9_-]+$")`
- T-3-03: `parse_paragraph` treats text as data-only
- T-3-04: `_cmd_validate` scans for secret patterns
- T-3-05: `_resolve_project_root` rejects `..` segments

## Next Phase Readiness

- Plan 03-03 (`stack_researcher.py`) can now use `state_writer.py write --field stack_choices` — ALLOWED_FIELDS accepts it
- Plan 03-04 (`scaffold_dispatch.py`) can use `state_writer.py write --field project_path` — ALLOWED_FIELDS accepts it
- Plan 03-05 (`question-bank.md`) will turn the 2 remaining SKIPPED intake tests GREEN
- `derived_spec.md` format is validated and ready for `/gsd-new-project --auto` consumption

---
*Phase: 03-intake-stack-research-web-playbook-one-playbook-e2e*
*Completed: 2026-04-30*
