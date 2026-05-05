---
phase: 08-skill-quality-publish-bar
plan: 06
subsystem: documentation
tags: [readme, install-one-liner, dev-team-metaphor, production-ready, qual-02, qual-03, sc-6]

# Dependency graph
requires:
  - phase: 08-01
    provides: URL lock (08-URL-LOCK.md) — RAW_INSTALL_URL + REPO_GIT_CLONE_URL substituted into README install sections
  - phase: 08-01
    provides: test_readme.py RED stubs (5 tests) for content invariants
  - phase: 08-04
    provides: examples gallery (web, cli, ai-service) cross-linked from README
  - phase: 08-07
    provides: assets/demo/RECORDING-CHECKLIST.md (referenced from README's demo honesty callout)
  - phase: 08-08
    provides: SKILL.md `requires:` block + references/version-policy.md (cross-linked from README sub-skill section)
provides:
  - repo-root README.md (154 lines) — install + dev-team metaphor + demo + --production-ready doc
  - 4/5 Wave 0 README test stubs flipped RED→GREEN
  - SC-6 documentation pass: --production-ready flag + all 7 NAMED_UPGRADES verbatim
affects: [08-HUMAN-UAT, future-publishing-phases, gh-pages-style-publish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - URL substitution from planning artifact (08-URL-LOCK.md) into committed text
    - README structure: hero blockquote + dual-install (one-liner + audited) + dev-team table + demo + flag doc
    - Honest-demo callout linking RECORDING-CHECKLIST.md (Pitfall 6 mitigation in committed text)

key-files:
  created:
    - README.md
  modified: []

key-decisions:
  - "URL substitution used the locked option-personal values from 08-URL-LOCK.md (cdlee/osbuilder); no deferred-decision banner needed."
  - "Demo asset deferred per phase orchestration; README still references assets/demo/osbuilder-demo.gif as planned, with an honest-demo callout pointing readers to RECORDING-CHECKLIST.md as the source of truth until the recording lands."
  - "Tech Writer (the 8th role) added as supplementary narration in stage 8 alongside DevOps, since the SKILL.md table only ships 8 stages × 7 distinct roles — explicit text addition keeps test_has_dev_team_section happy without modifying SKILL.md."
  - "GSD project-status link uses gsd-skill placeholder owner per plan instruction (informational, not OSBuilder's URL)."

patterns-established:
  - "Pattern: README cross-references planning artifacts (08-URL-LOCK.md) without including planning paths in the rendered prose — only the substituted URL ships."
  - "Pattern: README modes/upgrades tables stay in sync with implementation by literal grep contracts (test_readme.py greps each NAMED_UPGRADE verbatim)."

requirements-completed: [QUAL-02, QUAL-03]

# Metrics
duration: 3min
completed: 2026-05-05
---

# Phase 8 Plan 06: README.md Summary

**Repo-root README (154 lines) shipping the install one-liner, 8-role dev-team metaphor table, embedded 60s demo block, and SC-6 `--production-ready` documentation with all 7 NAMED_UPGRADES verbatim.**

## Performance

- **Duration:** ~3 min (128 s wall-clock)
- **Started:** 2026-05-05T07:09:29Z
- **Completed:** 2026-05-05T07:11:37Z
- **Tasks:** 1 (single-task plan)
- **Files created:** 1 (README.md)

## Accomplishments

- Created `README.md` at repo root (154 lines, target was ~120 — slightly above target due to honest-demo callout and Tech Writer narration paragraph)
- Substituted the locked URL `https://raw.githubusercontent.com/cdlee/osbuilder/main/install.sh` into the curl one-liner; substituted `https://github.com/cdlee/osbuilder.git` into the audited-install git-clone command
- Documented all 7 production-ready NAMED_UPGRADES verbatim (observability, migrations, healthchecks, secret-manager, sentry, rate-limiting, backups) — SC-6 verification pass
- Mapped all 8 dev-team roles to plain-English terminal narration
- Embedded honest-demo callout linking `assets/demo/RECORDING-CHECKLIST.md` (Pitfall 6 mitigation; demo asset itself deferred)
- Cross-linked `examples/README.md`, `references/version-policy.md`, `SKILL.md`, and `.planning/ROADMAP.md`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create README.md (install + dev-team metaphor + demo + production-ready)** — `fee4729` (docs)

## Files Created/Modified

- `README.md` — Created (154 lines). Contains: hero blockquote, Quick Install one-liner with locked URL, Audited Install (git clone) alternative, How OSBuilder Works (dev-team metaphor table), 60-Second Demo block + honest-demo callout, What you get, Modes table, --production-ready section listing all 7 NAMED_UPGRADES, Examples cross-link, Sub-skill version requirements section, Project status, License, See also.

## Decisions Made

- Used the locked `option-personal` URLs from 08-URL-LOCK.md verbatim (no deferred-decision banner; URLs are concrete).
- Tech Writer (8th role) added as supplementary narration paragraph beneath the dev-team table because SKILL.md's stage table maps 8 stages to 7 distinct roles. Adding it inline (rather than expanding the table) keeps the table's "stage = sequential gate" semantics clean while satisfying `test_has_dev_team_section`.
- Linked `assets/demo/RECORDING-CHECKLIST.md` from the demo section as the honest-demo policy source-of-truth. Demo asset itself is documented as deferred per phase orchestration; broken-image-in-README is the accepted interim state.
- GSD project-status link uses `gsd-skill` placeholder per plan instruction (informational, not OSBuilder's URL).

## Deviations from Plan

None — plan executed exactly as written. The plan explicitly anticipated:
- the README still referencing `assets/demo/osbuilder-demo.gif` while the asset is deferred (test_demo_asset_present skip is documented as expected);
- `<gsd-owner>` placeholder for the GSD project-status link (substituted to `gsd-skill`).

The Tech Writer 8th-role narration paragraph is in keeping with the plan's `read_first` pointer to SKILL.md lines 17-30 ("copy verbatim, then expand each row with a one-line plain-English narration") — the plan's own dev-team table example in `<interfaces>` already collapses Frontend/Backend/DevOps into one row, so 8 stages × 7 distinct rows is the correct shape and Tech Writer needed an explicit mention to satisfy the case-insensitive role grep.

## Issues Encountered

None.

## Pytest Delta

| Metric | Baseline (pre-08-06) | After 08-06 | Delta |
|--------|----------------------|-------------|-------|
| Passed | 203 | 207 | **+4** (test_readme.py: test_has_install_one_liner, test_has_dev_team_section, test_links_demo, test_documents_production_ready) |
| Skipped | 7 | 3 | **−4** (the 4 README stubs flipped RED→GREEN; test_demo_asset_present remains SKIP because demo asset is deferred — plan-anticipated) |
| Failed | 0 | 0 | 0 |
| Deselected | 4 | 4 | 0 |

`uv run pytest scripts/tests/test_readme.py -v` reports `4 passed, 1 skipped`.

## Acceptance Gates (re-run results)

- [x] `test -f README.md` — present
- [x] `wc -l README.md` reports 154 (>= 80)
- [x] `head -1 README.md` is `# OSBuilder`
- [x] `grep -E "curl -fsSL.*install\.sh.*\| sh"` matches
- [x] All 8 roles found case-insensitive (pm, architect, frontend, backend, devops, qa, reviewer, tech writer)
- [x] `grep -E "assets/demo/osbuilder-demo\.(gif|cast)"` matches (3 occurrences: 1 .gif image, 2 .cast references)
- [x] `--production-ready` literal present
- [x] All 7 NAMED_UPGRADES verbatim (observability, migrations, healthchecks, secret-manager, sentry, rate-limiting, backups)
- [x] Substituted URL begins with `https://` (T-08-19 mitigation)
- [x] SKILL.md not modified
- [x] install.sh not modified

## Threat Model Verification

- T-08-18 (info disclosure): Accepted — published URL is `https://github.com/cdlee/osbuilder`, owned by user, locked at 08-01 with explicit consent.
- T-08-19 (https tampering): Mitigated — verified substituted URL begins with `https://` (`grep -oE "https://[a-zA-Z0-9./-]+install\.sh"` matches).
- T-08-20 (NAMED_UPGRADES drift): Mitigated — all 7 names verified verbatim against `scripts/production_phase_writer.py:22-30`.

## User Setup Required

None.

## Next Phase Readiness

- README is publishable as soon as 08-07 lands the demo asset (then `test_demo_asset_present` flips from SKIP to PASS automatically — no further README edit needed).
- 08-HUMAN-UAT.md install one-liner check (manual gate) can now be executed against the published README content.

## Self-Check: PASSED

- README.md exists at repo root: FOUND
- Commit fee4729 in git log: FOUND
- All 5 acceptance grep invariants hold (re-verified above)
- Pytest count increased by exactly +4 vs baseline (203 → 207); no regressions

---
*Phase: 08-skill-quality-publish-bar*
*Plan: 06*
*Completed: 2026-05-05*
