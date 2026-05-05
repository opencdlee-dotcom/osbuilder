---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
plan: 05
subsystem: references
tags: [nextjs, drizzle, postgres, pnpm, tailwindcss, playbook, stack-menu, question-bank]

requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    provides: test stubs (test_web_playbook_exists, test_questions_have_no_jargon, test_questions_have_you_decide_option in RED/SKIPPED state)

provides:
  - references/playbooks/web.md: verified pnpm create next-app scaffold command, 4 post-scaffold files, forbidden files list, refuse list, pinned stack versions
  - references/stack-menu.md: fallback stack defaults table parseable by stack_researcher.py _read_stack_menu()
  - references/question-bank.md: 6 jargon-free outcome-framed questions each with I-dont-know-you-decide option

affects:
  - scaffold_dispatch.py (reads web.md as spec)
  - stack_researcher.py (reads stack-menu.md as fallback)
  - SKILL.md PM role (loads question-bank.md on-demand during intake)
  - gsd-verify-phase 3 (phase gate now unblocked: all 16 Phase 3 stubs GREEN)

tech-stack:
  added: []
  patterns:
    - "Reference docs: load-on-demand blockquote + ## sections + tables + See also footer (analog: references/preflight/README.md)"
    - "Stack table format: 5-column parseable by _read_stack_menu() regex; component names match component_map keys exactly"
    - "Question bank format: ## Q: section per question; exactly 3 options; 'I don't know, you decide' as third option"

key-files:
  created:
    - references/playbooks/web.md
    - references/stack-menu.md
    - references/question-bank.md
  modified: []

key-decisions:
  - "question-bank.md jargon ban applies to entire file content (not just Q sections) — jargon section uses circumlocutions, not the banned words"
  - "Removed explicit --yes mention from web.md to satisfy acceptance criteria (acceptance criteria: grep for --yes must exit non-zero)"
  - "question-bank.md has 6 Q sections (not minimum 5) — Privacy added as 6th for better coverage"

requirements-completed: [SCAF-01, RES-03, IN-03, IN-04]

duration: 4min
completed: 2026-04-30
---

# Phase 3 Plan 05: Web Playbook + Stack Menu + Question Bank — Summary

**Three reference files ship the human-readable spec layer: web.md documents the verified pnpm create next-app 7-flag command and 4 post-scaffold Drizzle files; stack-menu.md provides the _read_stack_menu()-parseable fallback defaults table; question-bank.md delivers 6 jargon-free intake questions each with "I don't know, you decide" defaults — flipping all 3 remaining SKIPPED stubs to GREEN and completing Phase 3.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-30T18:53:26Z
- **Completed:** 2026-04-30T18:58:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `references/playbooks/web.md` created: scaffold command (7 explicit flags), 4 post-scaffold files table, forbidden files list (SCAF-06), refuse list (K8s/microservices/Electron), pinned versions table (verified 2026-04-30)
- `references/stack-menu.md` created: "## Web playbook defaults" table with 5 components, all parseable by `_read_stack_menu()` regex; stack-menu parse smoke test passes
- `references/question-bank.md` created: 6 outcome-framed Q sections (devices, users, data, external access, file uploads, privacy), zero jargon words, every Q section has "I don't know, you decide" option
- All 46 Phase 3 tests GREEN (46 passed, 0 SKIPPED, 0 FAIL) — `test_web_playbook_exists`, `test_questions_have_no_jargon`, `test_questions_have_you_decide_option` flipped from SKIPPED to GREEN

## Task Commits

1. **Task 1: Create references/playbooks/web.md** - `d7a9cc1` (feat)
2. **Task 2: Create references/stack-menu.md and references/question-bank.md** - `04e33c6` (feat)

**Plan metadata:** (final commit below)

## Files Created/Modified

- `references/playbooks/web.md` (77 lines) — web scaffold spec: pnpm create next-app command, post-scaffold files, forbidden files, refuse list, stack versions
- `references/stack-menu.md` (43 lines) — stack fallback defaults table for _read_stack_menu(); includes How-this-file-is-consumed section and update instructions
- `references/question-bank.md` (56 lines) — 6 plain-English intake questions with 3-option format; jargon-ban section uses circumlocutions (not the banned words)

## Decisions Made

- **Jargon ban applies to entire file:** The `test_questions_have_no_jargon` test scans the whole file content, not just Q sections. The jargon-ban guidance section at the bottom of question-bank.md avoids spelling out the forbidden words, using plain-English descriptions instead ("technical layout term", "technical API term").
- **Removed --yes mention from web.md:** The plan acceptance criteria requires `grep -q "\-\-yes" web.md` to exit non-zero. The note was rewritten to warn against the "shortcut flag that accepts all defaults" without naming it.
- **6 Q sections (not minimum 5):** Added a Privacy question as the 6th for better intake coverage (private vs. public access default).

## Deviations from Plan

None — plan executed exactly as written. The only adjustment was rewording the `--yes` warning in web.md to satisfy the acceptance criteria without changing the meaning.

## Issues Encountered

None — all tests passed on first write. The jargon scan pattern requires care: the test uses whole-file word-boundary regex, so the jargon-ban section itself cannot contain the forbidden words.

## User Setup Required

None — no external service configuration required. All files are static reference documents.

## Next Phase Readiness

- Phase 3 Wave 2 complete: all 5 plans executed, all 46 tests GREEN
- `gsd-verify-phase 3` gate is unblocked: all 16 Phase 3 stubs are GREEN; `03-VALIDATION.md` can be set to `nyquist_compliant: true`
- Phase 4 (verify loop / pnpm dev UAT) can begin — scaffold_dispatch.py and all reference files are in place

## Self-Check: PASSED

- FOUND: references/playbooks/web.md
- FOUND: references/stack-menu.md
- FOUND: references/question-bank.md
- FOUND commit: d7a9cc1 (Task 1)
- FOUND commit: 04e33c6 (Task 2)
- 46 passed, 0 SKIPPED, 0 FAIL

---
*Phase: 03-intake-stack-research-web-playbook-one-playbook-e2e*
*Completed: 2026-04-30*
