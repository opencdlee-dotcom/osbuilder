---
phase: 08-skill-quality-publish-bar
plan: 03
subsystem: testing
tags: [ci-lint, qual-01, stdlib, argparse, skill-md]

# Dependency graph
requires:
  - phase: 08-skill-quality-publish-bar
    provides: Wave 0 RED stubs in scripts/tests/test_check_skill_md_length.py (08-01) — lazy-import fixture + 3 tests covering check()/CLI surface
provides:
  - scripts/check_skill_md_length.py — pure-stdlib QUAL-01 CI lint script (exit 0/1/2, friendly stderr)
affects:
  - 08-05 (.github/workflows/ci.yml will invoke `python3 scripts/check_skill_md_length.py` in lint-skill-md job)
  - 08-06 (README.md may reference the lint-script as part of contributor docs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Standalone-script-with-CLI (registry_verify.py shape): shebang + module docstring + REPO_ROOT + check()/main() + `if __name__ == '__main__': raise SystemExit(main())`"
    - "Friendly-stderr exit-code lint: 0=ok / 1=block / 2=defensive-missing, with plain-English remediation text"

key-files:
  created:
    - scripts/check_skill_md_length.py
  modified: []

key-decisions:
  - "Pure stdlib only — argparse + pathlib + sys (matches existing scripts/registry_verify.py pattern; honors project's no-third-party rule)"
  - "REPO_ROOT anchored at Path(__file__).resolve().parent.parent — script runs correctly from any CWD (CI checkout, dev shell, pytest tmp dirs)"
  - "Exit code 2 reserved for SKILL.md-not-found (defensive — should never happen in CI but distinguishes 'missing file' from 'over limit' for debugging)"
  - "check() default args use module-level constants (SKILL_MD, LIMIT) so the function is callable from tests with overrides AND from main() with the real defaults"

patterns-established:
  - "QUAL-01 CI surface: in-process pytest assertion (test_skill_md.py) + standalone CLI script (this) — same invariant, two surfaces"
  - "Lazy-import-via-fixture (08-01) flips RED→GREEN the moment `scripts/check_skill_md_length.py` lands on disk (no test edits needed)"

requirements-completed: [QUAL-01]

# Metrics
duration: 2min
completed: 2026-05-04
---

# Phase 08 Plan 03: scripts/check_skill_md_length.py (QUAL-01 standalone CI lint) Summary

**Pure-stdlib 59-line CLI script that fails CI when SKILL.md exceeds 200 lines, with friendly stderr pointing users to references/ progressive disclosure.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-05T02:47:51Z
- **Completed:** 2026-05-05T02:49:27Z
- **Tasks:** 1
- **Files created:** 1
- **Files modified:** 0

## Accomplishments

- Created `scripts/check_skill_md_length.py` (59 lines, pure stdlib — argparse, pathlib, sys only)
- Set executable bit (`chmod +x`) so CI can invoke directly via `python3 scripts/check_skill_md_length.py` without `uv run` or pytest
- Flipped 3 RED stubs in `scripts/tests/test_check_skill_md_length.py` (08-01) from skip → pass
- Verified script runs against real SKILL.md (136/200 lines): rc=0, stdout `"OK: SKILL.md is 136/200 lines."`
- Verified defensive missing-file path: `--skill-md /tmp/does-not-exist-xyz` → rc=2, stderr `"OSBuilder: SKILL.md not found at ..."`

## Task Commits

1. **Task 1: Implement scripts/check_skill_md_length.py** — `4216da1` (feat)

_Note: Task 1 ships as a single feat commit (not RED→GREEN sequence) because the RED stubs already landed in 08-01 — Wave 0 test infra is the explicit RED phase for the entire Phase 8 wave matrix. This plan is the GREEN flip._

## Files Created/Modified

- `scripts/check_skill_md_length.py` (CREATED, 59 lines) — pure-stdlib CLI lint script with `check(skill_md, limit) -> int` (exit codes 0/1/2) and `main(argv) -> int` (argparse entry point); module-level constants `REPO_ROOT`, `SKILL_MD`, `LIMIT = 200`

## Decisions Made

- **No deviations from plan.** Implementation matches the verbatim 08-PATTERNS.md pattern + 08-03-PLAN.md `<action>` block character-for-character.

## Acceptance Gates (re-run + reported)

| Gate | Command | Result |
|------|---------|--------|
| File exists + executable | `test -x scripts/check_skill_md_length.py` | PASS |
| Shebang on line 1 | `head -1 scripts/check_skill_md_length.py` | `#!/usr/bin/env python3` |
| No third-party imports | `grep -E "^(import\|from) (yaml\|requests\|packaging)" scripts/check_skill_md_length.py` | rc=1 (no matches) |
| Module-level constants present | grep `REPO_ROOT \| SKILL_MD \| LIMIT = 200` | All 3 present |
| `check(` and `main(` definitions | grep `def check( \| def main(` | Both present |
| `from __future__ import annotations` | grep | Present |
| Direct invocation against real SKILL.md | `python3 scripts/check_skill_md_length.py` | rc=0, stdout `OK: SKILL.md is 136/200 lines.` |
| Defensive: missing path → rc=2 | `python3 scripts/check_skill_md_length.py --skill-md /tmp/does-not-exist-xyz` | rc=2, stderr contains `not found` |
| File line count within 40-60 | `wc -l scripts/check_skill_md_length.py` | 59 lines |
| Wave 0 tests GREEN | `uv run pytest scripts/tests/test_check_skill_md_length.py -x -v` | **3 passed** (was 3 skipped pre-08-03) |

## Pytest Delta

| Metric | Pre-08-03 (after 08-02) | Post-08-03 | Delta |
|--------|------------------------|-----------|-------|
| Passed | 189 | **192** | **+3** |
| Skipped | 21 | 18 | -3 |
| Failed | 0 | 0 | 0 |
| Deselected (slow) | 4 | 4 | 0 |

The +3 passing tests are exactly the 3 tests in `scripts/tests/test_check_skill_md_length.py` that were skipped (via the lazy-import fixture) until `scripts/check_skill_md_length.py` existed:

- `test_passes_under_limit` — `csml.check(fake_100_lines, limit=200) == 0` ✓
- `test_fails_over_limit` — `csml.check(fake_250_lines, limit=200) == 1` ✓
- `test_cli_subprocess_exit_code` — subprocess invocation rc=1 + stderr contains `"250 lines"` ✓

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Threat Surface Scan

No new security-relevant surface introduced. The script reads a file path from argparse and counts lines — STRIDE register T-08-07/08/09 (in 08-03-PLAN.md) covers all three argv-borne risks (`--skill-md` accepting any path, symlink loops, negative `--limit`) and all three are dispositioned `accept` (CI-runner DoS only, no security impact).

## Self-Check: PASSED

- File `scripts/check_skill_md_length.py` exists at expected path
- Commit `4216da1` exists in `git log` and contains exactly the script
- All 3 Wave 0 tests pass against the new module
- Full pytest suite: 192 passed / 18 skipped / 0 failed (no regression vs 189-pass baseline)

## Next Plan Readiness

- **08-04** (`scripts/check_skill_versions.py` — QUAL-05 first-session validator) is now unblocked (was already unblocked by 08-02; no new gating)
- **08-05** (`.github/workflows/ci.yml`) can now wire the `lint-skill-md` job to invoke `python3 scripts/check_skill_md_length.py` — the script is in place, executable, and proven to run end-to-end with rc=0 against real SKILL.md
- QUAL-01 in-process invariant (test_skill_md.py) AND CI-surface invariant (this script) are both green; the CI pipeline (08-05) is the last piece needed to close QUAL-01 fully

---
*Phase: 08-skill-quality-publish-bar*
*Completed: 2026-05-04*
