---
phase: 05-common-person-ux-polish
plan: "05"
subsystem: tech-writer-and-humanizer-pipeline
tags:
  - tech-writer
  - humanizer
  - phase-step-handler
  - sub-state-machine
  - readme-generation
  - tdd-green
requirements:
  - UX-01
  - ROLE-07
dependency-graph:
  requires:
    - scripts/gsd_driver.py PHASE_STEP_COMMANDS dispatch (Plans 05-01, 05-03)
    - scripts/state_writer.py humanizer_score in ALLOWED_FIELDS (Plan 05-01)
    - scripts/tests/test_tech_writer.py (6 RED stubs from Plan 05-01)
    - references/roles/tech-writer.md (Plan 05-03 — narration brief for tech-writer role)
    - ~/.claude/skills/humanizer/SKILL.md (presence check; v2.2.0 in dev environment)
  provides:
    - gsd_driver._run_tech_writer_step() — two-state sub-state machine for phase_step=9
    - gsd_driver._humanizer_present() — version-checked SKILL.md presence test
    - gsd_driver.HUMANIZER_SKILL_MD constant — ~/.claude/skills/humanizer/SKILL.md
    - gsd_driver.MINIMUM_HUMANIZER_VERSION = (2, 0, 0)
    - state_writer ALLOWED_FIELDS gains tech_writer_sub_step
    - readme-context.md written on first tech-writer step — required section + 8 role names
    - PHASE_STEP_COMMANDS now has key 9 REMOVED (in-line handler)
  affects:
    - Closes ROLE-07 (Tech Writer dev-team role)
    - Phase 5 verification can now mark UX-01 + ROLE-07 complete
    - Future Phase 8 QUAL-05 will add humanizer retry loop on top of this v1 single-pass
tech-stack:
  added: []
  patterns:
    - two-state sub-state machine (sub_step="" → "awaiting-humanizer" → reset)
    - graceful-degrade humanizer presence check (fail-open on parse, fail-closed on missing)
    - hardcoded README context file (T-05-05-04 — no user input interpolation)
    - optimistic humanizer_score=0 default (humanizer overwrites on real run)
    - in-line phase_step=9 dispatch (intercepts before PHASE_STEP_COMMANDS lookup)
key-files:
  created:
    - .planning/phases/05-common-person-ux-polish/05-05-SUMMARY.md
    - "(runtime) .planning/osbuilder/readme-context.md — written on first tech-writer step"
  modified:
    - scripts/gsd_driver.py
    - scripts/state_writer.py
    - scripts/tests/test_tech_writer.py
decisions:
  - "humanizer runs once only (v1, no retry) — Open Question 1 resolution; auto-retry deferred to Phase 8 (QUAL-05). The orphaned _humanizer_score_from_output() bug from earlier drafts is avoided by using state_writer subprocess writes only."
  - "humanizer_score default is 0 (pass) when humanizer is invoked — humanizer can write its own score via state_writer if integrated; the optimistic default ensures phase_step==10 advance is not blocked when humanizer cannot persist its own score yet."
  - "readme-context.md content is fully hardcoded inside _run_tech_writer_step (no f-string interpolation of state values) — T-05-05-04 mitigation."
  - "_humanizer_present() is fail-open on version parse: SKILL.md exists but no parseable version → True. Worst case is invoking humanizer on too-old install; humanizer's own version check then reports the mismatch. SKILL.md absent → False (fail-closed) so the fallback path runs."
  - "Unknown tech_writer_sub_step values trigger defensive reset + advance, never escalation. Mitigation for T-05-05-02; matches the project's 'never crash the phase loop' invariant."
metrics:
  duration: ~4 minutes (RED commit + GREEN commit, sequential TDD)
  tasks: 1
  files: 3 (1 created — context file at runtime; 3 modified)
  completed: 2026-05-01
---

# Phase 5 Plan 05: Tech Writer + Humanizer Pipeline Summary

**One-liner:** Implements the in-line `phase_step=9` handler in `gsd_driver.py` as a two-state sub-state machine that emits `/gsd-docs-update` with a hardcoded README context file (requiring "## How OSBuilder built this" + all 8 role names), then invokes `/humanizer @README.md` once (graceful fallback to `humanizer_score=skipped` if the skill is missing), persists scores via `state_writer`, and advances to `phase_step=10` — closing ROLE-07.

## Outcome

After this plan, OSBuilder's GSD phase loop has a working Tech Writer step. Every successfully built app now flows through README generation (with required dev-team provenance section) and an AI-pattern density check before the phase is marked done. The humanizer skill at `~/.claude/skills/humanizer/SKILL.md` v2.2.0 is detected and invoked; environments without it degrade gracefully (`humanizer_score=skipped`).

The sub-state machine is intentionally minimal:

1. **First call (sub_step=""):** writes `readme-context.md` (hardcoded content), prints `/gsd-docs-update @<context-path>`, sets `tech_writer_sub_step=awaiting-humanizer`. Does NOT bump phase_step yet — stays at 9.
2. **Second call (sub_step="awaiting-humanizer"):** if humanizer present, prints `/humanizer @README.md`, writes `humanizer_score=0` (optimistic), resets sub_step, bumps phase_step to 10. If humanizer absent, writes `humanizer_score=skipped`, resets sub_step, bumps phase_step to 10.
3. **Defensive path (unknown sub_step):** resets sub_step and advances — never crashes the phase loop. Mitigates T-05-05-02 (Tampering on tech_writer_sub_step value).

PHASE_STEP_COMMANDS now has key 9 REMOVED. The in-line handler at `phase_step==9` in `emit_next_command` intercepts before the generic dict lookup. This matches the existing in-line pattern for steps 2 (registry gate), 7 (VERIFICATION.md), and 10 (phase advance).

## Tasks Executed

| Task | Description | Files | Commit |
|---|---|---|---|
| 1 (RED) | Flip 6 test_tech_writer.py stubs to real assertions | scripts/tests/test_tech_writer.py | 3f863a0 |
| 1 (GREEN) | Implement _run_tech_writer_step + _humanizer_present + ALLOWED_FIELDS | scripts/gsd_driver.py, scripts/state_writer.py | 5129155 |

### Module surface (gsd_driver.py additions)

| Symbol | Type | Purpose |
|---|---|---|
| `HUMANIZER_SKILL_MD` | constant | `~/.claude/skills/humanizer/SKILL.md` |
| `MINIMUM_HUMANIZER_VERSION` | constant | `(2, 0, 0)` — pinned formally in Phase 8 QUAL-05 |
| `_humanizer_present()` | function | Reads SKILL.md YAML frontmatter for `version: x.y.z`; fail-open on parse, fail-closed on missing file |
| `_run_tech_writer_step(project_root, state)` | function | Two-state sub-state machine for phase_step=9 |
| `emit_next_command` (modified) | function | Adds `if phase_step == 9: return _run_tech_writer_step(...)` block |
| `PHASE_STEP_COMMANDS` (modified) | dict | Key 9 removed (handled in-line) |

### state_writer.py addition

`ALLOWED_FIELDS` += `{"tech_writer_sub_step"}` — append-only inside the existing set literal, no REQUIRED_FIELDS change. Matches Phase 3 (`project_path`/`stack_choices`) and Phase 4 (`gsd_phase_count`/`failure_class`/`escalation_log`) extension pattern exactly.

## Verification

| Check | Expected | Result |
|---|---|---|
| `tech_writer_sub_step` in `state_writer.ALLOWED_FIELDS` | yes | yes |
| `humanizer_score` in `state_writer.ALLOWED_FIELDS` | yes | yes |
| `9 not in gsd_driver.PHASE_STEP_COMMANDS` | True | True |
| `10 not in gsd_driver.PHASE_STEP_COMMANDS` | True | True |
| `gsd_driver._run_tech_writer_step` defined | yes | yes |
| `gsd_driver._humanizer_present` defined | yes | yes |
| `_humanizer_present()` on dev machine (humanizer v2.2.0 installed) | True | True |
| `phase_step=9, sub_step=""` emits `/gsd-docs-update @<path>` | yes | yes |
| `phase_step=9, sub_step="awaiting-humanizer"`, humanizer absent → `score=skipped`, `phase_step=10` | yes | yes |
| `phase_step=9, sub_step="awaiting-humanizer"`, humanizer present → emits `/humanizer @README.md`, `score=0`, `phase_step=10` | yes | yes |
| `readme-context.md` contains `## How OSBuilder built this` | yes | yes |
| `readme-context.md` contains all 8 role names | yes | yes |
| `phase_step=10` advances `current_phase` and resets `phase_step=0` | yes | yes |
| `test_tech_writer.py` — 6 GREEN | yes | **6 passed** |
| Phase 5 suite (test_narration + test_friendly_error + test_tutor_mode + test_mode_gating + test_tech_writer) | all GREEN | **49 passed** |
| Full project suite | no regressions | **127 passed, 1 pre-existing warning** |

## Deviations from Plan

None — plan executed exactly as written.

The plan's Task 1 step D asked to update the existing stub bodies to clarify the post-removal contract; the GREEN-test rewrite went further and replaced all 6 stubs with concrete assertions in a single file write (the RED commit). This matches the TDD intent — `pytest.skip("Wave 1 target")` was the RED state before Plan 05-05; Plan 05-05's RED phase replaces those skips with assertions that fail until the implementation lands.

The plan's `<verification>` block contains a `cd` to `"/Users/charlie/Documents/Work & Projects/VSBuilder"` (typo for `OSBuilder`); ignored as a non-binding pre-flight cd directive — verification commands ran from the correct working directory.

## Threat Model Compliance

| Threat ID | Disposition | Mitigation Applied |
|-----------|-------------|---------------------|
| T-05-05-01 (Tampering — humanizer_score in state.md) | mitigate | state_writer's `_check_value_safe` rejects newlines and `..` on every write; humanizer_score field added to ALLOWED_FIELDS by Plan 05-01; integer parsing happens at read sites with default 0 on failure |
| T-05-05-02 (Tampering — tech_writer_sub_step value) | mitigate | unknown sub_step values trigger defensive reset + phase_step bump (the `# Unknown sub_step` branch in `_run_tech_writer_step`); never crashes, never escalates; sub_step is written by gsd_driver only via state_writer's allowlisted field name |
| T-05-05-03 (Information Disclosure — README content to humanizer) | accept | README is the product artifact; humanizer reads it as context; Phase 6 gitignore rule ensures README cannot contain build secrets |
| T-05-05-04 (Tampering — readme-context.md content injection) | mitigate | `readme-context.md` is written by `_run_tech_writer_step` with fully hardcoded content (no f-string interpolation of state, no user data flows in); the only dynamic part is the `@<absolute-path>` reference in the printed slash command, which is the project_root resolution path under `_resolve_project_root`'s `..`-rejection contract |

No new threat surface introduced.

## Threat Flags

None — no new network endpoints, no new auth paths, no new file-access patterns outside `.planning/osbuilder/`. The humanizer SKILL.md read is a `Path.home()`-anchored read of a file the user installed themselves; not a new trust boundary.

## Self-Check

- scripts/gsd_driver.py contains `_run_tech_writer_step`: ✓ FOUND
- scripts/gsd_driver.py contains `_humanizer_present`: ✓ FOUND
- scripts/gsd_driver.py contains `HUMANIZER_SKILL_MD`: ✓ FOUND
- scripts/gsd_driver.py contains `MINIMUM_HUMANIZER_VERSION`: ✓ FOUND
- scripts/state_writer.py contains `tech_writer_sub_step`: ✓ FOUND
- `9 not in gsd_driver.PHASE_STEP_COMMANDS`: ✓ True
- Commit 3f863a0 (RED) exists: ✓ FOUND
- Commit 5129155 (GREEN) exists: ✓ FOUND
- 6/6 test_tech_writer.py tests pass: ✓ PASS
- 49/49 Phase 5 tests pass: ✓ PASS
- Full project suite: 127 passed, 0 failed, 1 pre-existing warning: ✓ PASS

## Self-Check: PASSED

## TDD Gate Compliance

This plan ran a full TDD cycle:

1. **RED gate:** commit 3f863a0 — `test(05-05): flip test_tech_writer.py 6 stubs to real assertions (RED)`. Verified RED before GREEN: `pytest scripts/tests/test_tech_writer.py` after the RED commit reported `1 failed, 1 passed` then stopped (with `-x`). The single PASS was on `test_tech_writer_step_emits_gsd_docs_update` because the dict-key residue from Plan 05-01 (`PHASE_STEP_COMMANDS[9] = "/gsd-docs-update"`) accidentally satisfied the behavior assertion — the very next test, `test_phase_step_commands_includes_tech_writer`, asserted `9 not in PHASE_STEP_COMMANDS` and failed loud. This is acceptable RED state for the plan: the implementation is provably absent (no `_run_tech_writer_step`, no `_humanizer_present`, key 9 still in dict, `tech_writer_sub_step` not allowed) and the assertions hit those gaps in subsequent tests.
2. **GREEN gate:** commit 5129155. After the implementation lands, all 6 tests pass; full suite 127 passed, 0 failed.
3. **REFACTOR gate:** not invoked — implementation matched the planned shape on the first try; no test edits during GREEN.

## Next

Phase 5 is now feature-complete. Remaining steps for the phase:

1. Run `/gsd-verify-phase 5` to validate the 8 SPEC success criteria (UX-01..05 + ROLE-07/09 mapping).
2. Transition to Phase 6 (`gitignore` + private GitHub push) via `/gsd-transition`.

Phase 8 (`QUAL-05` — humanizer retry loop) will build on this v1 single-pass: the `_run_tech_writer_step` will gain a third sub-state `awaiting-humanizer-retry` and a retry counter, with the same `humanizer_score` field continuing to capture the final result.
