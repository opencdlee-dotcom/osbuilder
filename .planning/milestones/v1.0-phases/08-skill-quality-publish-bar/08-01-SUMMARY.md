---
phase: 08-skill-quality-publish-bar
plan: 01
subsystem: test-infra-and-url-lock
tags: [wave-0, red-stubs, url-lock, uat-scaffold]
requires:
  - .planning/phases/08-skill-quality-publish-bar/08-RESEARCH.md
  - .planning/phases/08-skill-quality-publish-bar/08-PATTERNS.md
  - .planning/phases/08-skill-quality-publish-bar/08-VALIDATION.md
provides:
  - "scripts/tests/test_check_skill_md_length.py — 3 RED stubs (QUAL-01 module + CLI)"
  - "scripts/tests/test_check_skill_versions.py — 4 RED stubs (QUAL-05 versions/marker/missing-version)"
  - "scripts/tests/test_ci_workflow.py — 3 RED stubs (QUAL-01 CI surface)"
  - "scripts/tests/test_readme.py — 5 RED stubs (QUAL-02/03/SC-6 README content)"
  - "scripts/tests/test_examples.py — 5 RED stubs (QUAL-04 examples gallery)"
  - ".planning/phases/08-skill-quality-publish-bar/08-URL-LOCK.md — locked public-repo URL (option-personal: cdlee/osbuilder)"
  - ".planning/phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md — 5-row UAT scaffold (status: pending)"
affects:
  - "Wave 1 plans 08-02..08-07 — RED targets to flip to GREEN"
  - "08-04 (CI workflow) and 08-05 (README) — read RAW_INSTALL_URL from URL-LOCK"
  - "08-HUMAN-UAT.md row 1 (clean-machine install) — unblocked by URL lock"
tech-stack:
  added: []
  patterns:
    - "Lazy-import-via-fixture (test_registry_verify.py:13-19) for not-yet-implemented modules"
    - "File-existence skip-guard (test_skill_md.py:16-17) for not-yet-created file artifacts"
    - "RAW_INSTALL_URL constant in 08-URL-LOCK.md grep-able by downstream plans"
key-files:
  created:
    - scripts/tests/test_check_skill_md_length.py
    - scripts/tests/test_check_skill_versions.py
    - scripts/tests/test_ci_workflow.py
    - scripts/tests/test_readme.py
    - scripts/tests/test_examples.py
    - .planning/phases/08-skill-quality-publish-bar/08-URL-LOCK.md
    - .planning/phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md
  modified: []
decisions:
  - "URL-lock choice: option-personal — public repo will live at github.com/cdlee/osbuilder; RAW_INSTALL_URL is https://raw.githubusercontent.com/cdlee/osbuilder/main/install.sh"
  - "Wave 0 collected 20 RED stubs (>= 18 gate, plan minimum was 18 = 2+4+2+5+5; actual 3+4+3+5+5 = 20 due to extra subprocess CLI test in module-length file and ci_workflow file-exists test)"
  - "test_examples.py::test_has_screenshots is a 5th stub (not 4 as plan body summary said) — added as Fix 4 per plan acceptance criteria comment '2 + 4 + 3 + 5 + 5 = 19 minimum'"
metrics:
  duration: ~10min
  completed: 2026-05-04
  tasks: 3
  files: 7
---

# Phase 08 Plan 01: Wave 0 RED test infra + URL lock + UAT scaffold Summary

Wave 0 RED test infrastructure for Phase 8 — 20 skip-guarded RED stubs across 5 new test files give Wave 1 plans (08-02..08-07) a target to flip to GREEN, plus the public-repo URL is locked once (option-personal: cdlee/osbuilder) so downstream README/CI/UAT artifacts never ship with `<TBD: REPO_URL>`.

## URL Decision Outcome

- **Choice:** `option-personal`
- **RAW_INSTALL_URL:** `https://raw.githubusercontent.com/cdlee/osbuilder/main/install.sh`
- **REPO_HTTPS_URL:** `https://github.com/cdlee/osbuilder`
- **REPO_GIT_CLONE_URL:** `https://github.com/cdlee/osbuilder.git`
- **Locked at:** `.planning/phases/08-skill-quality-publish-bar/08-URL-LOCK.md`
- **Decision-by:** Pre-resolved by /gsd-execute-phase orchestrator (08-01 Task 0 checkpoint)

## RED Stub Counts

| File | Plan minimum | Actual | Notes |
|------|--------------|--------|-------|
| `scripts/tests/test_check_skill_md_length.py` | 2 | 3 | adds subprocess CLI exit-code test (CI surface) |
| `scripts/tests/test_check_skill_versions.py` | 4 | 4 | semver-meet, semver-block, missing-version-warn, marker |
| `scripts/tests/test_ci_workflow.py` | 2 | 3 | exists, pinned-versions (V14 guard), invokes-lint |
| `scripts/tests/test_readme.py` | 5 | 5 | one-liner, dev-team roles, demo link, demo asset, --production-ready |
| `scripts/tests/test_examples.py` | 5 | 5 | min-three, has-spec, distinct-playbooks, repo-url, screenshots |
| **Total** | **18** | **20** | exceeds gate by 2 |

## Pytest Collection Delta

- Pre-Phase-8 baseline: 194 collected (190 selected, 4 deselected)
- Post-08-01: 214 collected (210 selected, 4 deselected)
- **Delta: +20 new tests** (matches 5-file count above)
- Full suite: **189 passed, 21 skipped, 4 deselected, 1 warning** — GREEN

The 21 skipped includes 20 new Phase-8 RED stubs (lazy-fixture or file-existence skip-guard fired as designed) plus 1 pre-existing skip from prior phases.

## HUMAN-UAT Scaffold

`.planning/phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md` created with `status: pending` and 5 manual-test rows:

1. Install one-liner end-to-end on a fresh container (QUAL-02 SC-2) — substituted RAW_INSTALL_URL is concrete
2. 60-second demo records an unedited end-to-end build (QUAL-03 SC-3)
3. README dev-team metaphor reads as plain English to a non-developer (QUAL-03)
4. Examples gallery apps were actually built by OSBuilder (QUAL-04 SC-4)
5. Version-drift validator real-world first-session UX (QUAL-05 SC-5)

Downstream Wave 1+ plans append `result:` values; they do NOT add new rows.

## Downstream Unblocked

- **08-02** — `check_skill_md_length.py` lint script: 3 RED stubs in `test_check_skill_md_length.py` waiting for `import check_skill_md_length` to resolve
- **08-03** — `check_skill_versions.py` validator: 4 RED stubs in `test_check_skill_versions.py` waiting for `import check_skill_versions` to resolve
- **08-04** — `.github/workflows/ci.yml`: 3 RED stubs in `test_ci_workflow.py` waiting for the file to exist with pinned `@v6` actions and lint-script invocation; can substitute RAW_INSTALL_URL from 08-URL-LOCK.md if the workflow embeds the install URL anywhere
- **08-05** — `README.md`: 5 RED stubs in `test_readme.py` waiting for one-liner (with locked RAW_INSTALL_URL), 8-role dev-team narration, demo link, --production-ready docs
- **08-06** — `assets/demo/`: `test_demo_asset_present` skip-guarded; will activate once `assets/demo/osbuilder-demo.{gif,cast}` lands
- **08-07** — `examples/`: 5 RED stubs in `test_examples.py` waiting for >=3 example dirs with SPEC.md / repo-url.txt / screenshots; substitute RAW_INSTALL_URL into any example onboarding text
- **08-HUMAN-UAT.md row 1** — already concrete (URL substituted); awaits human runner only

## Deviations from Plan

None — plan executed exactly as written. The test file body for `test_check_skill_md_length.py` and `test_ci_workflow.py` already contained 3 tests each in the verbatim plan body (not 2 as the `min_tests` frontmatter implied), so the "5+5+3+4+3 = 20" landing matches the plan's explicit `acceptance_criteria` formula `"2 + 4 + 3 + 5 + 5 = 19 minimum"` (the formula already accounted for the +1 subprocess test in each file).

## Authentication Gates

None encountered. Task 0 (URL-lock) was pre-resolved upfront by the /gsd-execute-phase orchestrator, so no checkpoint pause occurred during this run.

## Self-Check: PASSED

- File `scripts/tests/test_check_skill_md_length.py` — FOUND
- File `scripts/tests/test_check_skill_versions.py` — FOUND
- File `scripts/tests/test_ci_workflow.py` — FOUND
- File `scripts/tests/test_readme.py` — FOUND
- File `scripts/tests/test_examples.py` — FOUND
- File `.planning/phases/08-skill-quality-publish-bar/08-URL-LOCK.md` — FOUND
- File `.planning/phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md` — FOUND
- Commit `2a67b4e` (docs(08): lock public-repo URL) — FOUND
- Commit `d5ab1cf` (test(08): add RED stubs for QUAL-01..05) — FOUND
- Commit `2267e4a` (docs(08): add HUMAN-UAT scaffold) — FOUND
