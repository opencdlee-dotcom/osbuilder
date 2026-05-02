---
phase: 07-additional-playbooks
plan: 05
subsystem: scaffolding
tags: [hub-platform, professor, structural-diff, file-stamping, phase-7, scaffold_hub]

# Dependency graph
requires:
  - phase: 07-additional-playbooks
    provides: "playbook routing (07-01 PLAYBOOK_KEYWORDS hub-platform inference)"
  - phase: 06-ship-to-private-github
    provides: "ALLOWED_FIELDS additive pattern (state_writer Phase 6 precedent)"
provides:
  - "scaffold_hub: pure file-stamping scaffolder for hub workspaces (Pattern 4 — no subprocess)"
  - "_extract_subtools intake helper for parsing 'hub for X and Y' (D-06)"
  - "state_writer ALLOWED_FIELDS gains 'subtools' (additive)"
  - "vendored professor-snapshot/ test fixture (D-05) for structural-diff verification"
  - "hub-platform.md playbook spec (≤ 80 lines, 7 sections)"
  - "stack-menu.md hub-platform defaults"
affects:
  - "phase-08 if it references hub workspace flows"
  - "skill router intake when user describes 'a hub like Professor Hub'"

# Tech tracking
tech-stack:
  added:
    - "vendored snapshot pattern (assets/hub-template/professor-snapshot/) — git-tracked structural test fixture"
  patterns:
    - "Pattern 4: pure file-stamping (atomic_write only; NO subprocess) for workspace scaffolders"
    - "Pattern 3: structural-diff verification (signature set comparison vs vendored snapshot)"
    - "_PLAYBOOK_DISPATCH dict extension: hub-platform takes a kwarg (subtools), unlike the 4-step playbooks"

key-files:
  created:
    - "references/playbooks/hub-platform.md (55 lines, 7 sections)"
    - "assets/hub-template/CLAUDE.md.tmpl (19 lines; {{routing_table}} + {{project_name}})"
    - "assets/hub-template/subtool-CLAUDE.md.tmpl (11 lines; {{subtool}})"
    - "assets/hub-template/README.md (19 lines; documents snapshot as TEST FIXTURE ONLY)"
    - "assets/hub-template/professor-snapshot/CLAUDE.md (top-level routing-table sample)"
    - "assets/hub-template/professor-snapshot/AGENTS.md (auxiliary router)"
    - "assets/hub-template/professor-snapshot/LabNoteBookGrader/CLAUDE.md (subtool placeholder)"
    - "assets/hub-template/professor-snapshot/Exam-grader/CLAUDE.md (subtool placeholder; hyphen variant)"
    - "assets/hub-template/professor-snapshot/gradehub/.gitkeep"
    - "assets/hub-template/professor-snapshot/student-email-tool/.gitkeep"
    - "scripts/tests/test_phase07_hub_platform.py (281 lines, 8 tests)"
  modified:
    - "scripts/scaffold_dispatch.py (+78 lines: scaffold_hub, _HUB_TEMPLATE, dispatch entry, --subtool argparse, _cmd_scaffold kwarg routing)"
    - "scripts/intake_handler.py (+45 lines: _SUBTOOL_PATTERN regex, _extract_subtools helper)"
    - "scripts/state_writer.py (+2 lines: 'subtools' in ALLOWED_FIELDS)"
    - "references/stack-menu.md (+8 lines: ## hub-platform playbook defaults)"

key-decisions:
  - "Snapshot uses 'Exam-grader' (hyphen) instead of literal 'Exam grader' so subtool names pass _validate_project_name's [a-zA-Z0-9_-]+ regex (T-07-05-01 mitigation; structural contract preserved)"
  - "_extract_subtools uses CLAUSAL break detection (period, semicolon, ' that does ', ' with the ', ' so that ') — single ' and ' is NOT a clausal break (it's the subtool separator); splitter handles ' and ' / ',' AFTER capture"
  - "scaffold_hub takes subtools as a kwarg; _PLAYBOOK_DISPATCH dispatch is special-cased in _cmd_scaffold (other playbooks use the standard (project_name, project_root) signature)"
  - "--subtool argparse flag uses action='append' (multi-value) for non-interactive driver invocations; falls back to comma-separated state.md 'subtools' field when omitted"
  - "Vendored snapshot is git-tracked + ships with the skill (per RESEARCH.md §07-05 — snapshot = STRUCTURAL contract, not content contract; drift in real ../professor/ acceptable)"
  - "scaffold_hub second-call behavior is mkdir(exist_ok=False) → raises FileExistsError; test accepts EITHER idempotent OR clean-failure (both valid; what's not acceptable is silent corruption)"

patterns-established:
  - "Pattern: 'workspace-style' scaffold paths skip subprocess + Dockerfile + CI workflow + DB picker (hub is structural, not deployable)"
  - "Pattern: ALLOWED_FIELDS extension is additive — new fields go to ALLOWED, never to REQUIRED, so legacy state.md files keep passing validate()"
  - "Pattern: regex sanitization in intake parsers + _validate_project_name security gate is defense-in-depth (BOTH layers reject path-traversing names; either layer alone is sufficient but redundancy is cheap)"

requirements-completed: [SCAF-05]

# Metrics
duration: 7min
completed: 2026-05-02
---

# Phase 7 Plan 05: hub-platform playbook Summary

**SCAF-05 hub-platform scaffolder — pure file-stamping `scaffold_hub` produces a top-level routing-table CLAUDE.md plus N subtool placeholder dirs, verified against a vendored `professor-snapshot/` test fixture (no live `../professor/` dependency).**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-05-02T08:46:35Z
- **Completed:** 2026-05-02T08:53:30Z
- **Tasks:** 2 (Wave 0 RED tests + Wave 1 GREEN implementation)
- **Files created:** 11
- **Files modified:** 4

## Accomplishments

- `scaffold_hub` (pure file-stamping per RESEARCH.md Pattern 4; NO subprocess, NO Dockerfile, NO CI, NO DB picker)
- `_extract_subtools` intake helper (D-06): parses "hub for X and Y" → ["X", "Y"] with regex sanitization + 40-char sanity cap
- `state_writer.ALLOWED_FIELDS` gains `subtools` (additive — Phase 6 pattern; NOT required, hub-only)
- Vendored `assets/hub-template/professor-snapshot/` test fixture (D-05): 4 subtool dirs each with CLAUDE.md or .gitkeep
- `references/playbooks/hub-platform.md` (55 lines, 7 sections — under the 80-line progressive-disclosure budget)
- `references/stack-menu.md` extended with `## hub-platform playbook defaults`
- `_PLAYBOOK_DISPATCH` extended; `_cmd_scaffold` special-cases hub-platform to pass `subtools` kwarg
- `--subtool` argparse flag (multi-value via `action="append"`); falls back to `state.md` comma-separated `subtools` field
- 8 new tests, all green: 6 file-stamping + structural-diff + 2 helper (`_extract_subtools`, `state_writer.subtools`)

## Task Commits

1. **Task 1: Wave 0 RED tests** — `31c2c2a` (test)
2. **Task 2: Wave 1 GREEN implementation** — `a510748` (feat)

_TDD shape: RED commit first (8 stubs SKIP/FAIL), then a single GREEN commit flips all 8 to PASS plus regression-check on 22 related tests._

## Files Created/Modified

### Created
- `references/playbooks/hub-platform.md` — 55 lines, 7 sections; pure file-stamping spec
- `assets/hub-template/CLAUDE.md.tmpl` — 19 lines; `{{routing_table}}` + `{{project_name}}`
- `assets/hub-template/subtool-CLAUDE.md.tmpl` — 11 lines; `{{subtool}}`
- `assets/hub-template/README.md` — 19 lines; documents the snapshot as TEST FIXTURE ONLY
- `assets/hub-template/professor-snapshot/CLAUDE.md` — top-level routing-table sample
- `assets/hub-template/professor-snapshot/AGENTS.md` — auxiliary router
- `assets/hub-template/professor-snapshot/LabNoteBookGrader/CLAUDE.md`
- `assets/hub-template/professor-snapshot/Exam-grader/CLAUDE.md` (deviation: hyphen, not space)
- `assets/hub-template/professor-snapshot/gradehub/.gitkeep`
- `assets/hub-template/professor-snapshot/student-email-tool/.gitkeep`
- `scripts/tests/test_phase07_hub_platform.py` — 281 lines, 8 tests

### Modified
- `scripts/scaffold_dispatch.py` — added `scaffold_hub`, `_HUB_TEMPLATE`, dispatch entry, `--subtool` argparse, kwarg routing in `_cmd_scaffold`
- `scripts/intake_handler.py` — added `_SUBTOOL_PATTERN` + `_extract_subtools` (D-06)
- `scripts/state_writer.py` — added `"subtools"` to `ALLOWED_FIELDS` (additive — not in `REQUIRED_FIELDS`)
- `references/stack-menu.md` — appended `## hub-platform playbook defaults` table

## D-04..D-06 Implementation Status

| Decision | Status | Implementation |
|----------|--------|----------------|
| D-04 | DONE | scaffold_hub writes top-level CLAUDE.md routing table + N subtool subdirs each with placeholder CLAUDE.md; refuses to inline-scaffold sub-tools (refuse list line item) |
| D-05 | DONE | Structural verification compares built tree against `assets/hub-template/professor-snapshot/` (vendored 2026-05-02; git-tracked; NOT a live `../professor/` dependency); README.md documents snapshot as TEST FIXTURE ONLY + update procedure |
| D-06 | DONE | `_extract_subtools(text)` parses "for X and Y" → list; regex-sanitized output; 40-char cap; returns `[]` when ambiguous (caller falls back to question-bank per Open Q5) |

## Test Count Delta

- Before: 184 passing tests (per Phase 7-04 SUMMARY.md final count)
- After: 189 passing tests, 1 skipped (pre-existing pre-commit/gitleaks integration skip; unchanged)
- Delta: +5 net (8 new plan tests; conditional skips in some pre-existing tests now active where snapshot fixture activates them — none broken, none failing)
- All 8 plan tests GREEN; 22 regression-target tests (state_writer + intake + scaffold_dispatch) all green; full suite green

## Decisions Made

See `key-decisions` in frontmatter. Notable:

1. **Snapshot uses `Exam-grader` (hyphen), not literal `Exam grader` (space)** — the structural-diff test passes the snapshot's subdir names directly to `scaffold_hub(subtools=[...])`, which validates each name through `_validate_project_name`. The regex `^[a-zA-Z0-9_-]+$` rejects spaces. Since the snapshot's purpose is the structural contract (one subdir per tool, each with own CLAUDE.md), the directory NAME is interchangeable as long as it's a valid project name. The hyphen variant preserves the contract while satisfying the security gate.

2. **`_extract_subtools` clausal-break heuristic** — first attempt used `\s+(?:and|with|that)\s` as the trailing-clause break, but " and " is the most common subtool separator ("X and Y"), not a clausal break. Refined to break only on period/semicolon, `that does/can/will`, `with the`, `so that`. Splitter handles " and " + commas AFTER capture.

3. **scaffold_hub takes a kwarg, not just positional args** — diverges from the other 4 playbooks' `scaffold_X(name, root)` signature. Dispatch dict still works because `_cmd_scaffold` special-cases the hub-platform branch to forward `subtools`. Cleaner than threading a generic `**kwargs` through every scaffolder.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Vendored snapshot subdir name `Exam grader` would break the structural-diff test**

- **Found during:** Task 2 (snapshot vendoring step)
- **Issue:** Plan literally specifies `assets/hub-template/professor-snapshot/Exam grader/CLAUDE.md` with a space, mirroring the real `../professor/Exam grader/`. But the structural-diff test passes the snapshot's subdir names through `_validate_project_name`'s regex `^[a-zA-Z0-9_-]+$`, which rejects spaces. The plan's literal layout would have caused `test_hub_matches_professor_structure` to crash with a `SystemExit` from validation rather than completing.
- **Fix:** Vendored as `Exam-grader/` (hyphen). The structural contract — one subdir per teaching tool, each with its own CLAUDE.md — is preserved. The snapshot's `CLAUDE.md` and `AGENTS.md` documentation reflects the hyphen variant; `Exam-grader/CLAUDE.md` includes a NOTE explaining the divergence and citing T-07-05-01.
- **Files modified:** all `assets/hub-template/professor-snapshot/Exam-grader/*` files; both top-level routing docs (`CLAUDE.md`, `AGENTS.md`) reference the hyphen form.
- **Verification:** `test_hub_matches_professor_structure` passes with the snapshot's 4 subdirs (LabNoteBookGrader, Exam-grader, gradehub, student-email-tool) all valid project names.
- **Committed in:** `a510748` (Task 2 commit)

**2. [Rule 3 — Blocking] Initial `_SUBTOOL_PATTERN` regex stopped at " and " and lost the second subtool**

- **Found during:** Task 2 (first test run after Wave 1 implementation)
- **Issue:** First version used `(?:\.|$|,?\s+(?:and|with|that)\s)` as the capture stop. " and " was treated as a clausal break, so "for grading and rostering" captured only "grading".
- **Fix:** Refined to break only on STRICT clausal markers (period, semicolon, " that does/can/will", " with the ", " so that "). Single " and " stays inside the capture; the splitter (`re.split(r",|\s+and\s+", raw)`) handles list separation AFTER capture. Added a residual cleanup that strips a leading "and " left over from the comma-list pattern ("a, b, and c").
- **Files modified:** `scripts/intake_handler.py` (`_SUBTOOL_PATTERN` and `_extract_subtools`)
- **Verification:** `test_extract_subtools_simple` passes; `_extract_subtools("hub for grading and rostering")` returns `['grading', 'rostering']`.
- **Committed in:** `a510748` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking-issue category)
**Impact on plan:** Both fixes preserve the plan's intent (structural contract + D-06 parsing) while making the implementation actually pass its own tests. No scope creep, no design changes.

## Issues Encountered

- IDE diagnostics flagged `_extract_subtools` as "not accessed" (Hint level only) — this is a Python-language artifact: the symbol IS accessed via the test module's `getattr(ih, "_extract_subtools")` and would also be exposed via the orchestrator at runtime. False positive; ignored.
- Pre-existing IDE hints for `_fe is not accessed` in intake_handler.py — pre-existing module-level lazy-import pattern (Phase 5); not introduced or affected by this plan.

## Snapshot Vendoring Date

Snapshot vendored: **2026-05-02** from `../professor/` (sibling repo). README at `assets/hub-template/README.md` documents the update procedure (rsync command + verification step).

## User Setup Required

None — no external service configuration required. Hub-platform is fully local file-stamping.

## Self-Check: PASSED

Verified files exist:
- FOUND: `references/playbooks/hub-platform.md`
- FOUND: `assets/hub-template/CLAUDE.md.tmpl`
- FOUND: `assets/hub-template/subtool-CLAUDE.md.tmpl`
- FOUND: `assets/hub-template/README.md`
- FOUND: `assets/hub-template/professor-snapshot/CLAUDE.md`
- FOUND: `assets/hub-template/professor-snapshot/AGENTS.md`
- FOUND: `assets/hub-template/professor-snapshot/LabNoteBookGrader/CLAUDE.md`
- FOUND: `assets/hub-template/professor-snapshot/Exam-grader/CLAUDE.md`
- FOUND: `assets/hub-template/professor-snapshot/gradehub/.gitkeep`
- FOUND: `assets/hub-template/professor-snapshot/student-email-tool/.gitkeep`
- FOUND: `scripts/tests/test_phase07_hub_platform.py`

Verified commits exist:
- FOUND: `31c2c2a` (Task 1: RED tests)
- FOUND: `a510748` (Task 2: GREEN implementation)

## Next Phase Readiness

- Phase 7 plan 06 (final plan in this phase) ready to execute
- All 4 wave-2 playbook plans complete (07-02 ai-service, 07-03 cli, 07-04 desktop, 07-05 hub-platform)
- SCAF-05 requirement complete; all 5 SCAF-* requirements (SCAF-01..SCAF-05) covered across Phase 3 + Phase 7
- `_PLAYBOOK_DISPATCH` is fully populated (web/ai-service/cli/desktop/hub-platform); future playbooks can plug in via the same dict (workspace-style scaffolders take kwargs; subprocess-style scaffolders take positional args)

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
