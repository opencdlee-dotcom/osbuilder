---
phase: 08-skill-quality-publish-bar
plan: 05
subsystem: infra
tags: [github-actions, ci, qual-01, security-v14, pinned-versions, uv, pytest]

# Dependency graph
requires:
  - phase: 08-skill-quality-publish-bar
    provides: scripts/check_skill_md_length.py (08-03 — the lint script the workflow invokes)
  - phase: 08-skill-quality-publish-bar
    provides: scripts/tests/test_ci_workflow.py RED stubs (08-01 Wave 0)
provides:
  - .github/workflows/ci.yml (CI surface enforcing QUAL-01 on every PR + push to main)
  - First GitHub Actions workflow in the OSBuilder repo
  - "Eats own dog food" demonstration — workflow shape mirrors assets/ci-workflows/python.yml.tmpl that OSBuilder emits for built repos
affects:
  - "Phase 9+ workflow extensions (e.g., adding ruff/mypy jobs) plug into this same file"
  - "Phase 8 remaining plans (08-06 README, 08-07 examples, 08-08 UAT) will benefit from CI auto-running on PR"

# Tech tracking
tech-stack:
  added: [github-actions]
  patterns:
    - "Two-job CI with needs: dependency — fast-fail lint before slow pytest"
    - "Pinned action versions to exact major (@v6) per Security V14 — no @latest"
    - "Single trigger surface: PR to main + push to main (no workflow_dispatch, no schedule — out of scope)"

key-files:
  created:
    - .github/workflows/ci.yml (33 lines, 2 jobs)
  modified: []

key-decisions:
  - "CI workflow shape mirrors assets/ci-workflows/python.yml.tmpl (the same template OSBuilder emits for built repos) — eats own dog food"
  - "lint-skill-md is a separate job (not a step in test job) so it appears as its own check on the PR — easier to grep failures and explain to the user"
  - "test job uses needs: lint-skill-md so a >200-line SKILL.md fails the PR before the slower pytest job even starts"

patterns-established:
  - "Pattern: GitHub Actions workflows in OSBuilder pin to exact major version (@v6); upgrade cadence will live in references/version-policy.md (08-02 already landed it for sub-skills; CI actions follow same policy)"
  - "Pattern: Workflow file header comments cite the source template + verification date (Security V14 traceability)"

requirements-completed: [QUAL-01]

# Metrics
duration: 2min
completed: 2026-05-05
---

# Phase 8 Plan 05: CI Workflow (QUAL-01 CI Surface) Summary

**.github/workflows/ci.yml with two jobs (lint-skill-md → test) pinned to actions/checkout@v6, actions/setup-python@v6, astral-sh/setup-uv@v6 — fails PRs that push SKILL.md > 200 lines before pytest even runs**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-05T07:05:01Z
- **Completed:** 2026-05-05T07:07:00Z (approx)
- **Tasks:** 1
- **Files created:** 1

## Accomplishments

- First GitHub Actions workflow in the OSBuilder repo (.github/workflows/ci.yml, 33 lines)
- Two-job pipeline: `lint-skill-md` (runs `python3 scripts/check_skill_md_length.py`) → `test` (runs `uv run pytest` after lint passes)
- All actions pinned to exact major (`@v6`) per Security V14 — zero `@latest` references
- CI triggers on `pull_request` to main AND `push` to main (covers both PR review and post-merge confirmation)
- Workflow shape mirrors `assets/ci-workflows/python.yml.tmpl` verbatim (eats own dog food)
- Wave 0 RED stubs in `scripts/tests/test_ci_workflow.py` flipped RED → GREEN: 3/3 passing

## Task Commits

1. **Task 1: Create .github/workflows/ci.yml** — `6f478dd` (feat)

## Files Created

- `.github/workflows/ci.yml` (33 lines) — CI pipeline with `lint-skill-md` and `test` jobs; the lint job fails fast on SKILL.md > 200 lines, the test job runs full pytest suite

## Acceptance Gates — All Pass

| Gate | Result |
|------|--------|
| File `.github/workflows/ci.yml` exists | PASS |
| `wc -l` >= 25 | PASS (33 lines) |
| Contains `lint-skill-md:` and `test:` jobs | PASS |
| Contains `needs: lint-skill-md` | PASS |
| Contains `actions/checkout@v6` | PASS |
| Contains `actions/setup-python@v6` | PASS |
| Contains `astral-sh/setup-uv@v6` | PASS |
| Does NOT contain `@latest` | PASS (grep returns 0 matches) |
| Contains `scripts/check_skill_md_length.py` | PASS |
| Contains `uv run pytest` | PASS |
| Contains both `pull_request:` AND `push:` triggers | PASS |
| No tabs in YAML indent | PASS |
| `uv run pytest scripts/tests/test_ci_workflow.py -x` | PASS (3 passed, 0 skipped) |

## Pytest Delta

| Metric | Before (08-04 baseline) | After (08-05) | Delta |
|--------|-------------------------|---------------|-------|
| passed | 200 | 203 | **+3** |
| skipped | 10 | 7 | **-3** |
| failed | 0 | 0 | 0 |

The +3 passes correspond exactly to the 3 RED stubs in `test_ci_workflow.py` flipping GREEN. No other test changes; no regressions.

## Decisions Made

- **lint-skill-md as a separate job (not a step in `test`):** Two surfaces the failure separately on the PR check list — `lint-skill-md` failed vs `test` failed are distinguishable at a glance.
- **`needs: lint-skill-md` ordering:** Test job is the slow one (uv sync + full pytest). Failing the cheap lint first saves CI minutes when the obvious case happens (someone pushes a 250-line SKILL.md).
- **No additional jobs (no Black, ruff format, mypy):** Phase 8 scope is QUAL-01 only. Future expansion plugs into this same file.
- **No `workflow_dispatch` / `schedule` / cron triggers:** Out of scope; would add ambiguity without value.
- **`act` not run locally:** Optional per the plan; YAML structurally validated (no tabs, proper indentation, mirrors verified template). Real validation will happen on first PR push to a remote (currently no remote — covered in `08-HUMAN-UAT.md`).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Threat Flags

None — no new security surface introduced beyond what the plan's `<threat_model>` already covers (T-08-15 mitigated by `@v6` pinning; T-08-16, T-08-17 explicitly accepted).

## User Setup Required

None — once a remote (`origin`) is added and the branch is pushed, GitHub Actions will pick up `.github/workflows/ci.yml` automatically. No secrets, no environment variables, no dashboard configuration.

## Next Phase Readiness

- `.github/workflows/ci.yml` is the gate that enforces QUAL-01 on every future PR (combined with the in-process pytest assertion in `scripts/tests/test_skill_md.py`, this gives two surfaces enforcing the same invariant — one in-process, one CI).
- 08-06 (README), 08-07 (examples gallery), 08-08 (HUMAN-UAT) can now be developed knowing each PR will be auto-checked once a remote exists.
- `08-HUMAN-UAT.md` row 1 (manual QUAL-01 confirmation: push a synthetic 201-line PR and watch CI fail) is the natural next test for this surface.

## Self-Check: PASSED

- FOUND: `.github/workflows/ci.yml`
- FOUND: commit `6f478dd` (`git log --oneline | grep 6f478dd`)
- FOUND: 3/3 tests in `scripts/tests/test_ci_workflow.py` GREEN
- FOUND: full suite 203 passed / 7 skipped (was 200 / 10 — exactly +3 / -3)

---
*Phase: 08-skill-quality-publish-bar*
*Completed: 2026-05-05*
