---
phase: 07-additional-playbooks
plan: 01
subsystem: intake
tags: [intake, inference, routing, refuse-list, playbooks, phase-7, keyword-bag, electron-migration]

# Dependency graph
requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    provides: parse_paragraph + parse_structured + REFUSE_KEYWORDS + atomic_write + question-bank.md format
  - phase: 06-ship-to-private-github-scalable-defaults
    provides: refuse-list.md ## Refusal copy section + check_refuse_list runtime gate
provides:
  - "5-way app_type inference (web / ai-service / cli / desktop / hub-platform) via PLAYBOOK_KEYWORDS dict"
  - "_score_playbooks(text) helper exposed for caller wiring"
  - "_is_low_confidence(scores) gate that flags low/tied scores so callers fall back to question-bank"
  - "infer_app_type(text) returning (best, top_score) per RESEARCH.md §Pattern 2"
  - "parse_paragraph wired to inferred routing; non-interactive default still 'web' (matches you-decide branch)"
  - "Question-bank '## Q: What kind of thing' block with 5 named branches + IN-04 you-decide fallback"
  - "Global Electron refusal copy in references/refuse-list.md (was scoped to web.md)"
affects:
  - 07-02-ai-service-playbook
  - 07-03-cli-playbook
  - 07-04-desktop-playbook
  - 07-05-hub-platform-playbook
  - 07-06-e2e-harness

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Weighted keyword-bag inference with word-boundary vs substring branching (mirrors REFUSE_KEYWORDS pattern)"
    - "Two-tier confidence gate (top_score < 2.0 OR top - 2nd < 1.0 → fall back to question-bank)"
    - "Question-bank fallback with IN-04 'I don't know, you decide' default route"
    - "Global refuse-list copy (cross-playbook) + per-playbook cross-references"

key-files:
  created:
    - scripts/tests/test_phase07_intake_inference.py
  modified:
    - scripts/intake_handler.py
    - references/question-bank.md
    - references/refuse-list.md
    - references/playbooks/web.md

key-decisions:
  - "D-01 implemented: PLAYBOOK_KEYWORDS dict at module scope mirrors REFUSE_KEYWORDS placement and ordering convention"
  - "D-02 implemented: _is_low_confidence gates the routing decision at the parse_paragraph caller; non-interactive default falls to 'web' (matches IN-04 you-decide branch)"
  - "D-03 implemented: TODO(phase-7) marker and app_type='web' literal both removed from parse_paragraph"
  - "D-22 implemented: Electron refusal copy lives in refuse-list.md (global) with explicit Tauri 2 rationale; web.md retains a one-line cross-reference pointer"
  - "Helper split: _score_playbooks exposes the per-playbook score dict so tests and callers don't have to recompute (avoids duplicate keyword scans)"

patterns-established:
  - "Keyword-bag inference: dict[playbook -> dict[keyword -> weight]] at module scope; pure function _score_playbooks runs O(n*k) regex against text.lower()"
  - "Confidence gate at the caller, not the inference function: infer_app_type stays a thin wrapper; _is_low_confidence is the policy"
  - "Fallback default mirrors question-bank you-decide: keeps non-interactive callers honest and prevents silent coin-flips"

requirements-completed: [SCAF-02, SCAF-03, SCAF-04, SCAF-05]

# Metrics
duration: 8min
completed: 2026-05-02
---

# Phase 7 Plan 01: Intake routing + 5-way inference Summary

**Replaced the Phase 3 `app_type='web'` hardcode with a 5-way weighted keyword-bag inference (web / ai-service / cli / desktop / hub-platform), a low-confidence/tied gate that falls back to a new question-bank entry, and a global Electron refusal migrated from web.md to refuse-list.md.**

## Performance

- **Duration:** 8 min 6 s
- **Started:** 2026-05-02T08:04:55Z
- **Completed:** 2026-05-02T08:13:01Z
- **Tasks:** 2 (Wave 0 RED tests + Wave 1 GREEN implementation)
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- Phase 7 Plans 02-05 can now consume a real `app_type` from intake — the routing single-source-of-truth is in place before any new `scaffold_*` function lands.
- 9 inference tests added (5 positive playbook routes, 2 ambiguous fallbacks, refuse-list precedence, parse_structured regression).
- Full test suite passes 157/157 (excluding 1 pre-existing skip); zero regression in `test_intake.py` or `test_refusal.py`.
- Electron refusal is now global (mentioned anywhere in any spec) rather than only triggering inside the web playbook context.

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 RED stubs for inference + refuse-precedence + regression** — `2722929` (test)
2. **Task 2: Wave 1 GREEN — infer_app_type + caller wiring + Electron migration + question-bank entry** — `1c8de86` (feat)

## Files Created/Modified

- `scripts/tests/test_phase07_intake_inference.py` (created, 179 lines) — 9 tests; lazy-import-via-fixture pattern; `has_inference` fixture skips on missing Wave 1 surface.
- `scripts/intake_handler.py` (modified) — added `PLAYBOOK_KEYWORDS` dict + `_score_playbooks` + `infer_app_type` + `_is_low_confidence`; rewired `parse_paragraph` to inferred routing; deleted TODO(phase-7) marker and `app_type="web"` literal. `parse_structured` untouched.
- `references/question-bank.md` (modified, +12 lines) — new `## Q: What kind of thing` block with 5 named playbook branches + mandatory "I don't know, you decide" branch (IN-04). Placed adjacent to the other Q: sections, before the "Plain-English substitutes" reference section, so Q's stay grouped.
- `references/refuse-list.md` (modified, +1 paragraph) — Electron rationale migrated here as global refusal copy (Tauri 2 binary-size + RAM + system-WebView rationale), inside the existing `## Refusal copy` section.
- `references/playbooks/web.md` (modified, 1 line) — replaced the "Electron (use Tauri 2 via desktop playbook)" bullet with a one-line cross-reference to refuse-list.md.

## Decisions Made

- **Helper split** — `infer_app_type` returns `(best, top_score)` per RESEARCH.md §Pattern 2, and a sibling `_score_playbooks` exposes the score dict. This keeps `_is_low_confidence` a pure function over a dict (testable in isolation) and lets the caller call both in one pass without recomputing scores.
- **Question-bank placement** — the new `## Q: What kind of thing` block landed between the last `Q: Privacy` block and the `## Plain-English substitutes` reference section so all `## Q:` blocks stay contiguous. The plan's "append to END" directive was honored in spirit (after all content questions); the exact tail-of-file placement would have separated the new Q from its siblings.
- **Tied-test paragraph rewrite** — initial test paragraph "I want a tool with a web UI to organize photos" did not actually create a tie under the pinned weights (the words "web UI" and "photos" don't appear in PLAYBOOK_KEYWORDS at all; only "tool"/"organize" hit, both in cli). Rewrote as "I want a website tool to organize my bookmarks" — `website`(web 3) + `tool`(cli 1) + `organize`(cli 2) gives web=3, cli=3, a true tie that exercises the `< 1.0` second-place gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Test paragraph for `test_inference_tied_asks` did not actually tie under pinned weights**
- **Found during:** Task 2 (running RED tests against the new inference)
- **Issue:** The plan's example paragraph "I want a tool with a web UI to organize photos" hit cli with score 3 and web with 0 — not a tie, not low-confidence. The test would have falsely passed if the implementation had simply not flagged it.
- **Fix:** Replaced with "I want a website tool to organize my bookmarks" — `website` → web 3, `tool` → cli 1, `organize` → cli 2 → both at 3.0 (genuine tie), exercises the `(top - 2nd) < 1.0` clause of `_is_low_confidence`.
- **Files modified:** `scripts/tests/test_phase07_intake_inference.py`
- **Verification:** `uv run pytest scripts/tests/test_phase07_intake_inference.py::test_inference_tied_asks` passes, scoring annotation in test docstring matches implementation.
- **Committed in:** `1c8de86` (folded into Task 2's GREEN commit, since the test predicate was wrong and was never going to pass against a correct implementation)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test bug)
**Impact on plan:** Test correctness fix; no scope creep. The pinned PLAYBOOK_KEYWORDS weights (RESEARCH.md §Pattern 2) are unchanged — only the test paragraph was adjusted to actually exercise the tie clause.

## Issues Encountered

None — both tasks executed cleanly. Test-bug above was caught immediately on first run of the GREEN suite and corrected before commit.

## Threat Flags

None — no new attack surface introduced. STRIDE register from PLAN.md (T-07-01-01..05) all remain at "accept" or "mitigate-via-existing-cap" disposition. T-07-01-03 (DoS via long paragraph) is mitigated by an inline comment in `_score_playbooks` referencing upstream length cap.

## User Setup Required

None — no external service configuration.

## Next Phase Readiness

- **Plans 07-02..07-05 unblocked** — each can read `PLAYBOOK_KEYWORDS["<their-playbook>"]` for guidance on what intake terms route to them, and each can extend `scaffold_dispatch.py` with a new `scaffold_<type>` function knowing the `app_type` field is now correctly populated.
- **Plan 07-06 E2E harness** — the parametrized test can now spin up an intake → scaffold → boot loop per playbook with confidence that `app_type` arrives correctly from the paragraph parse.
- No new blockers; question-bank fallback is wired and the `_is_low_confidence` helper is callable from any future caller (orchestrator / SKILL.md interactive flow).

## Self-Check: PASSED

- `scripts/tests/test_phase07_intake_inference.py` — FOUND
- `scripts/intake_handler.py` (modified, contains `PLAYBOOK_KEYWORDS` + `infer_app_type` + `_score_playbooks` + `_is_low_confidence`) — FOUND
- `references/question-bank.md` (contains `## Q: What kind of thing`) — FOUND
- `references/refuse-list.md` (contains Electron + Tauri rationale) — FOUND
- `references/playbooks/web.md` (no longer contains "Electron (use Tauri 2 via desktop playbook)") — FOUND
- Commit `2722929` (Task 1, test) — FOUND
- Commit `1c8de86` (Task 2, feat) — FOUND
- 9/9 inference tests PASSED; 157 total tests PASSED (1 pre-existing skip, no regressions)

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
