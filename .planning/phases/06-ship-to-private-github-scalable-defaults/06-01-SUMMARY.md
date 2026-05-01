---
phase: 06-ship-to-private-github-scalable-defaults
plan: 01
subsystem: test-infrastructure
tags: [wave-0, red-stubs, nyquist, state-writer, conftest, fixtures]
dependency_graph:
  requires: []
  provides:
    - scripts/tests/test_gh_handoff.py
    - scripts/tests/test_runbook_writer.py
    - scripts/tests/test_scaffold_extensions.py
    - scripts/tests/test_refusal.py
    - scripts/tests/test_production_ready.py
    - scripts/tests/fixtures/derived_spec_with_k8s.md
    - scripts/tests/fixtures/derived_spec_clean.md
  affects:
    - scripts/state_writer.py (ALLOWED_FIELDS extended)
    - scripts/tests/conftest.py (4 new Phase 6 fixtures)
tech_stack:
  added: []
  patterns:
    - lazy-import fixture (importlib.import_module + pytest.skip on ImportError)
    - pytest.skip("Wave 1 target") stub bodies
    - ALLOWED_FIELDS additive extension (Phase 3/4/5/6 pattern)
    - monkeypatch-based GhShell / GitShell programmable subprocess mocks
key_files:
  created:
    - scripts/tests/test_gh_handoff.py
    - scripts/tests/test_runbook_writer.py
    - scripts/tests/test_scaffold_extensions.py
    - scripts/tests/test_refusal.py
    - scripts/tests/test_production_ready.py
    - scripts/tests/fixtures/derived_spec_with_k8s.md
    - scripts/tests/fixtures/derived_spec_clean.md
  modified:
    - scripts/state_writer.py
    - scripts/tests/conftest.py
decisions:
  - "test_clean_spec_passes added to test_refusal.py (SCL-05 negative case from PATTERNS.md) to reach 144 collected target; VALIDATION.md V-14/V-15 still 1:1 mapped"
  - "test_refusal.py uses ih (intake_handler) fixture per plan open-question resolution: refusal gate lives in intake_handler.py"
  - "scripts/tests/fixtures/ created without __init__.py — pytest discovers fixtures via path not import"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-01"
  tasks_completed: 2
  files_changed: 9
---

# Phase 06 Plan 01: Wave 0 RED Stubs + State Writer Extension Summary

**One-liner:** Nyquist Wave 0 RED stubs for all 17 Phase 6 V-IDs (SHIP-01..05, SCL-01..06) with state_writer.py ALLOWED_FIELDS +5 and conftest Phase 6 fixtures.

## What Was Built

### Task 1: state_writer.py + conftest + fixture .md files

- Extended `scripts/state_writer.py` ALLOWED_FIELDS with 5 Phase 6 fields (`repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`, `production_ready`) following the Phase 3/4/5 additive comment-header pattern.
- Appended 4 new fixtures to `scripts/tests/conftest.py`:
  - `fake_built_app(tmp_path)` — git-init'd tmp directory representing scaffold_dispatch output
  - `fake_state_md(tmp_project_root)` — builder fixture that seeds state.md via state_writer subprocess
  - `mock_gh_subprocess(monkeypatch)` — GhShell class covering 5 gh failure modes (auth-status-fail, repo-create-fail, network-fail, token-expired, not-installed)
  - `mock_git_subprocess(monkeypatch)` — GitShell class covering clean/dirty/no-init/remote-set scenarios
- Created `scripts/tests/fixtures/` directory with two derived_spec markdown fixtures mirroring `intake_handler._render_derived_spec()` output shape:
  - `derived_spec_with_k8s.md` — contains "Kubernetes", "microservices", "Helm" (refusal positive fixture)
  - `derived_spec_clean.md` — TODO list app, no refuse keywords (refusal negative fixture)

### Task 2: Wave 0 RED stubs — 5 test files (17 stubs total)

| File | Stubs | V-IDs Covered |
|------|-------|---------------|
| `test_gh_handoff.py` | 3 | V-01, V-02, V-08 |
| `test_runbook_writer.py` | 1 | V-03 |
| `test_scaffold_extensions.py` | 8 | V-05, V-06, V-07, V-09, V-10, V-11, V-12, V-13 |
| `test_refusal.py` | 3 | V-14 (pos), V-14 (neg), V-15 |
| `test_production_ready.py` | 2 | V-16, V-17 |
| **Total** | **17** | **16 unique V-IDs (V-04 is manual UAT)** |

Every stub body is `pytest.skip("Wave 1 target")`. Every stub has a docstring citing requirement ID and V-ID. `test_gitleaks_blocks_real_secret` has `@pytest.mark.skipif(shutil.which("pre-commit") is None or shutil.which("gitleaks") is None, ...)` pre-installed.

## Verification Results

| Check | Result |
|-------|--------|
| `pytest --collect-only -q` count | 144 tests (127 prior + 17 new) — 0 errors |
| Full suite | 127 passed, 17 skipped, 0 failures, 0 errors |
| ALLOWED_FIELDS Phase 6 fields | 5/5 present (26 total fields) |
| conftest new fixtures | 4/4 present |
| k8s fixture polarity | "kubernetes" in content — OK |
| clean fixture polarity | No refuse keywords — OK |
| Stub bodies | All pytest.skip("Wave 1 target") — no pass/assert False |
| Phase 1-5 regressions | 0 (127/127 still pass) |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `dd343e0` | feat | extend ALLOWED_FIELDS + conftest Phase 6 fixtures + derived_spec fixture files |
| `e55f678` | test | Wave 0 RED stubs — 5 new test files covering 17 Phase 6 V-IDs |

## Deviations from Plan

### Auto-added: test_clean_spec_passes (Rule 2 — missing critical functionality)

- **Found during:** Task 2 stub count reconciliation
- **Issue:** Plan must_haves required >= 144 collected (127 + >= 17), but the 5 V-ID-mapped stubs in test_refusal.py produced only 2 (V-14, V-15) = 16 total stubs = 143 collected (1 short).
- **Fix:** Added `test_clean_spec_passes` to `test_refusal.py` — the SCL-05 negative case explicitly named in `06-PATTERNS.md` (line 659) but omitted from the PLAN.md task count reconciliation note. This is a valid test (the refusal gate must NOT fire on a clean spec) and PATTERNS.md names it as an expected stub.
- **Files modified:** `scripts/tests/test_refusal.py`
- **Commit:** `e55f678`

## Known Stubs

All 17 functions in the 5 new test files are intentional Wave 0 stubs. They will be flipped from `pytest.skip` to GREEN assertions by Wave 1 plans (06-02 through 06-06). This is by design — not a defect.

## Self-Check: PASSED

- [x] `scripts/state_writer.py` exists and contains `repo_visibility` in ALLOWED_FIELDS
- [x] `scripts/tests/conftest.py` contains `def fake_built_app`, `def fake_state_md`, `def mock_gh_subprocess`, `def mock_git_subprocess`
- [x] `scripts/tests/fixtures/derived_spec_with_k8s.md` exists
- [x] `scripts/tests/fixtures/derived_spec_clean.md` exists
- [x] All 5 test files exist with correct stub counts (3+1+8+3+2 = 17)
- [x] `dd343e0` commit found in git log
- [x] `e55f678` commit found in git log
- [x] 144 tests collected, 127 passed, 17 skipped, 0 errors
