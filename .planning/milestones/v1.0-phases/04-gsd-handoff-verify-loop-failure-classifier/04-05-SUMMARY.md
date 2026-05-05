---
phase: 04-gsd-handoff-verify-loop-failure-classifier
plan: "05"
subsystem: qa-reference-docs
tags: [wave-2, qa-role, verification, falsifiable-criteria, reference-doc]

dependency_graph:
  requires:
    - "04-02 (gsd_driver.py — phase_step=7 writes VERIFICATION.md; format must match qa.md)"
  provides:
    - "references/roles/qa.md — QA role falsifiable criteria reference; VERIFICATION.md format contract; 6 observable-behavior examples; forbidden pattern list"
  affects:
    - scripts/gsd_driver.py (loads qa.md as LLM context when generating VERIFICATION.md at phase_step=7)
    - future phases using gsd_driver.py (QA criteria authorship guided by this file)

tech-stack:
  added: []
  patterns:
    - "Flat reference doc pattern: no YAML frontmatter, # title, > blockquote scope disclaimer, ## sections, no ### nesting (mirrors references/playbooks/web.md)"
    - "Observable-behavior criterion format: bold label + description, How to check line, Acceptable because line"

key-files:
  created:
    - references/roles/qa.md
  modified: []

key-decisions:
  - "qa.md documents the VERIFICATION.md format exactly as gsd_driver.py phase_step=7 writes it — single source of truth for both the LLM authoring criteria and the Python code writing the file"
  - "Criteria examples use 'Acceptable because' sub-line to explain the falsifiability property explicitly — avoids ambiguity about what makes a criterion valid"
  - "Escalation note added: when a phase produces no observable user behavior, scope-review rather than generating un-falsifiable criteria"

patterns-established:
  - "references/roles/ subdirectory established for role-specific reference docs loaded on-demand (not in SKILL.md)"

requirements-completed:
  - VER-01
  - VER-02
  - VER-03
  - VER-04

duration: 4min
completed: "2026-04-30"
---

# Phase 04 Plan 05: QA Role Falsifiable Criteria Reference Summary

**Created `references/roles/qa.md` — the falsifiability contract for VERIFICATION.md: format template matching gsd_driver.py phase_step=7, 6 observable-behavior examples, 5 forbidden patterns, and the 2-5 count rule.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-30T20:44:00Z
- **Completed:** 2026-04-30T20:47:09Z
- **Tasks:** 1
- **Files created:** 1

## Accomplishments

- Created `references/roles/` directory and `references/roles/qa.md`
- Documented the exact VERIFICATION.md format that `gsd_driver.py` writes at phase_step=7 (headers, placeholders, section names match exactly)
- Listed 5 forbidden criterion patterns with explanations ("tests pass", "pytest exits 0", "no errors in logs", vague API, subjective feature)
- Provided 6 falsifiable criterion examples covering route navigation, data persistence, API liveness, error handling, dev server boot, and file-on-disk observable behaviors
- Stated the 2-5 criteria count rule and added an escalation note for phases with no observable user behavior

## Task Commits

1. **Task 1: Create references/roles/qa.md** — `4ba6fb7` (feat)

## Files Created/Modified

- `references/roles/qa.md` — QA role reference: VERIFICATION.md format contract, falsifiability rule, forbidden patterns, 6 valid examples, count rule (91 lines, no frontmatter)

## Decisions Made

- Used `Acceptable because:` sub-line on each example to make the falsifiability property explicit — the plan specified the format as bold + How-to-check only, but this addition gives the LLM a clear signal for why each example qualifies (Rule 2: missing critical context for LLM authoring quality)
- Scope disclaimer blockquote matches the `references/playbooks/web.md` structural pattern exactly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added "Acceptable because" sub-line to each example**
- **Found during:** Task 1 (authoring the 6 valid criterion examples)
- **Issue:** The plan specified bold label + How-to-check for each example. Without explaining WHY each example is falsifiable, the LLM loading this file has format-only guidance but no reasoning to generalize from.
- **Fix:** Added an "Acceptable because: [one sentence]" sub-line to each example so the LLM can reason about new criteria using the same logic.
- **Files modified:** references/roles/qa.md
- **Committed in:** 4ba6fb7 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical context)
**Impact on plan:** Additive only — the plan's required content is fully present; the "Acceptable because" lines are supplementary. No scope creep; line count stays at 91 (well under 150 limit).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Verification Results

```
# All acceptance criteria
test -f references/roles/qa.md                           PASS
grep -c "OSBuilder QA Role" → 1                          PASS (>= 1)
grep -c "Falsifiable Success Criteria" → 1               PASS (>= 1)
grep -c "tests pass|pytest exits 0|no errors.*logs" → 3  PASS (>= 2)
grep -c "How to check" → 7                               PASS (>= 5)
grep -c "2 to 5|2-5" → 3                                 PASS (>= 1)
wc -l → 91                                               PASS (< 150)
grep "^---" → (empty)                                    PASS (no frontmatter)
python3 -m pytest scripts/tests/ → 75 passed             PASS (all green)
```

## Threat Model Review

T-04-05-01 (Tampering via prompt injection): No user-controlled content in `qa.md`; developer-authored reference doc committed to OSBuilder skill. Accept disposition confirmed.
T-04-05-02 (DoS via line-limit budget): `qa.md` is 91 lines; NOT in SKILL.md; loaded on-demand only. Mitigate disposition satisfied.

No new threat surface introduced beyond what the threat model covers.

## Next Phase Readiness

Phase 04 is now complete — all 5 plans executed:
- 04-01: Wave 0 RED stubs for gsd_driver, failure_classifier, registry_verify + state_writer ALLOWED_FIELDS extension
- 04-02: gsd_driver.py GREEN (PHASE_STEP_COMMANDS state machine, VERIFICATION.md write at step 7)
- 04-03: failure_classifier.py GREEN (4-class taxonomy, exponential backoff, structured handoff)
- 04-04: registry_verify.py GREEN (npm/PyPI/crates.io existence gate, fail-open policy)
- 04-05: references/roles/qa.md (falsifiable criteria reference doc)

Test suite at 75 passed — the quality moat is in place. Ready for Phase 5 (UX polish / narration).

---
*Phase: 04-gsd-handoff-verify-loop-failure-classifier*
*Completed: 2026-04-30*

## Self-Check: PASSED
