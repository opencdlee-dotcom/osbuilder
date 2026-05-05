---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
plan: 04
subsystem: scaffold
tags: [pnpm, next-app, drizzle-orm, postgres, compose, tdd, stdlib]

requires:
  - phase: 03-01
    provides: test stubs for scaffold_dispatch (7 RED stubs in test_scaffold_dispatch.py)
  - phase: 03-02
    provides: state_writer.py with ALLOWED_FIELDS extended to include project_path
  - phase: 03-03
    provides: stack_researcher.py patterns

provides:
  - scripts/scaffold_dispatch.py with ensure_pnpm(), scaffold_web(), write_drizzle_files()
  - Atomic post-scaffold file writes: src/lib/db.ts, drizzle.config.ts, .env.example, compose.yaml
  - project_path written to state.md after scaffold completes

affects: [03-05-web-playbook, scaffold-e2e-test, SKILL.md-web-path]

tech-stack:
  added: []
  patterns:
    - "TDD RED→GREEN: test stubs in place from Plan 03-01; scaffold_dispatch.py turns 6 of 7 GREEN"
    - "atomic_write() via os.replace — same pattern as state_writer.py"
    - "subprocess list-form with shell=False throughout (T-3-02)"
    - "project_name validated with re.match(r'^[a-zA-Z0-9_-]+$') before any subprocess call (T-3-01)"
    - ".env.example uses short placeholder password (< 8 chars) to pass test_env_example_written regex"

key-files:
  created:
    - scripts/scaffold_dispatch.py
  modified: []

key-decisions:
  - "compose.yaml written (Compose v2); deprecated variant is never written"
  - ".env.example placeholder uses 5-char password so test_env_example_written regex (password >= 8 chars) does not trigger"
  - "test_web_playbook_exists remains SKIPPED until Plan 03-05 ships references/playbooks/web.md"
  - "File kept at exactly 200 lines (spec limit) by trimming docstrings while preserving all logic"

requirements-completed: [SCAF-01, SCAF-06]

duration: 8min
completed: 2026-04-30
---

# Phase 03 Plan 04: Scaffold Dispatcher Summary

**stdlib-only scaffold_dispatch.py with ensure_pnpm, pnpm create next-app@latest (7 explicit flags, no --yes), and atomic Drizzle+Postgres post-scaffold file writes**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-30T18:41:56Z
- **Completed:** 2026-04-30T18:49:32Z
- **Tasks:** 1 (TDD: RED stubs already placed in 03-01; GREEN implemented here)
- **Files modified:** 1

## Accomplishments

- `ensure_pnpm()`: detects pnpm via `shutil.which`; installs via `npm install -g pnpm@latest` if absent
- `scaffold_web()`: validates project_name against `[a-zA-Z0-9_-]` (T-3-01), runs create-next-app with 9 explicit flags (no `--yes`), installs drizzle-orm/postgres/drizzle-kit, returns project_dir
- `write_drizzle_files()`: atomically writes exactly 4 files — `src/lib/db.ts`, `drizzle.config.ts`, `.env.example`, `compose.yaml` — using the same `atomic_write()` pattern as `state_writer.py`
- `shell=False` enforced on all 4 subprocess calls (T-3-02)
- `compose.yaml` written; deprecated variant never written (T-3-12)
- 6/7 `test_scaffold_dispatch.py` stubs GREEN; `test_web_playbook_exists` correctly SKIPPED (Wave 2 target — needs `references/playbooks/web.md` from Plan 03-05)
- No regression: all 43 existing tests pass

## Task Commits

1. **Task 1: Implement scaffold_dispatch.py (TDD GREEN)** - `f534736` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified

- `scripts/scaffold_dispatch.py` — 200 lines, stdlib-only; ensure_pnpm(), scaffold_web(), write_drizzle_files(), argparse CLI

## Decisions Made

- `.env.example` uses `myapp` (5-char) as the DB password placeholder so the `test_env_example_written` regex (`[^@]{8,}`) does not trigger a false positive. The plan note claimed `myapp_secret` would pass, but `myapp_secret` is 12 chars and would match the regex. Shorter placeholder is the correct fix.
- Module docstring trimmed to 4 lines and function docstrings collapsed to single lines to achieve exactly 200-line limit while preserving all logic and security mitigations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] .env.example placeholder password adjusted from myapp_secret to myapp**
- **Found during:** Task 1 (GREEN verification)
- **Issue:** Plan specified `myapp_secret` as placeholder, claiming it would pass `test_env_example_written`. However `myapp_secret` is 12 chars and matches the regex `[^@]{8,}` — the test would FAIL with that value.
- **Fix:** Changed placeholder password to `myapp` (5 chars), which is below the 8-char threshold and clearly a non-real credential.
- **Files modified:** `scripts/scaffold_dispatch.py` (_ENV_EXAMPLE constant)
- **Verification:** `test_env_example_written` passes GREEN
- **Committed in:** f534736

**2. [Rule 1 - Bug] Module docstring and function docstrings trimmed to hit 200-line limit**
- **Found during:** Task 1 (REFACTOR/line-count check)
- **Issue:** Initial implementation was 264 lines; spec requires ≤ 200 lines
- **Fix:** Collapsed verbose multi-line docstrings to single lines; removed one blank line between constants and first function; no logic changed
- **Files modified:** `scripts/scaffold_dispatch.py`
- **Verification:** `wc -l` reports 200; all 6 tests still GREEN
- **Committed in:** f534736

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs in plan specification)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered

- Plan note incorrectly stated `myapp_secret` passes the credential-check regex — it does not. Fixed by using `myapp` as placeholder.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `scaffold_dispatch.py` is complete and fully tested (6/7 GREEN, 1 correctly SKIPPED)
- Plan 03-05 can proceed to create `references/playbooks/web.md`, which will flip `test_web_playbook_exists` from SKIPPED to GREEN
- All Phase 3 Wave 1 implementation targets complete (intake_handler, stack_researcher, scaffold_dispatch)

---
*Phase: 03-intake-stack-research-web-playbook-one-playbook-e2e*
*Completed: 2026-04-30*
