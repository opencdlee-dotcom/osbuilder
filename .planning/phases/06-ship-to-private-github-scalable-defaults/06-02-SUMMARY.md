---
phase: 06-ship-to-private-github-scalable-defaults
plan: "02"
subsystem: gh-handoff
tags: [ship, github, gitignore, gitleaks, friendly-errors, tdd, wave-1]
dependency_graph:
  requires:
    - "06-01"  # Wave 0 RED stubs + conftest fixtures
    - "05-02"  # friendly_error.py + dictionary.yaml base
  provides:
    - scripts/gh_handoff.py (ship, verify, _compose_gitignore, _install_gitleaks_hook)
    - assets/gitignore-templates/ (common, node, python)
    - assets/gitleaks/ (.pre-commit-config.yaml, .gitleaks.toml)
    - 5 new gh-* friendly-error dictionary entries
  affects:
    - references/friendly-errors/dictionary.yaml (30 → 35 entries)
    - scripts/tests/test_gh_handoff.py (3 stubs → GREEN)
    - scripts/tests/test_scaffold_extensions.py (2 stubs → GREEN, 1 SKIP-by-design)
tech_stack:
  added:
    - gitleaks v8.30.1 (pinned pre-commit hook config)
    - pre-commit (optional integration; SHIP-04)
  patterns:
    - _GhGitShell test helper: passes state_writer subprocess to real run, intercepts gh/git
    - token-redaction pass in _friendly() via re.sub(r"ghps_[A-Za-z0-9_]{20,}", ...) (T-06-02-03)
    - ASSETS = REPO_ROOT / "assets" constant for template resolution
    - Idempotency via _GITIGNORE_MARKER sentinel in .gitignore
key_files:
  created:
    - scripts/gh_handoff.py
    - assets/gitignore-templates/common.gitignore
    - assets/gitignore-templates/node.gitignore
    - assets/gitignore-templates/python.gitignore
    - assets/gitleaks/.pre-commit-config.yaml
    - assets/gitleaks/.gitleaks.toml
  modified:
    - references/friendly-errors/dictionary.yaml
    - scripts/tests/test_gh_handoff.py
    - scripts/tests/test_scaffold_extensions.py
decisions:
  - "gh-not-installed placed BEFORE gh-not-found (same match_pattern; Phase 6 copy_paste_command brew install gh takes precedence; gh-not-found kept for Phase 5 preflight context)"
  - "_compose_gitignore + _install_gitleaks_hook live in gh_handoff.py (ship boundary, not scaffold boundary) — matches RESEARCH code examples and PATTERNS.md recommendation"
  - "_GhGitShell test helper captures real subprocess.run reference before monkeypatching and passes state_writer calls through — avoids state.md missing-file failures under mock"
  - "gh-repo-view-fail added as 5th new entry (not in original PATTERNS.md but required by plan spec); total dictionary 35 entries"
metrics:
  duration: "9 minutes"
  completed: "2026-05-01T21:54:36Z"
  tasks_completed: 4
  files_created: 7
  files_modified: 3
---

# Phase 06 Plan 02: gh_handoff.py — Terminal Ship Action Summary

**One-liner:** `gh repo create --private` pipeline with idempotent gitignore/gitleaks stamping, 5-failure-mode friendly errors, and token redaction via `re.sub(r"ghps_...", "[REDACTED-TOKEN]", raw)`.

## What Was Built

`scripts/gh_handoff.py` — the terminal ship action that closes SHIP-01 + SHIP-03 + SHIP-04 + SHIP-05. The `ship()` function orchestrates: `gh auth status` preflight → `.gitignore` composition from templates → gitleaks pre-commit config stamping → `git init/add/commit` → `gh repo create --private --source --push` → `gh repo view` visibility verification → 4 state.md field writes.

Five static asset files provide the templates read by `_compose_gitignore()` and `_install_gitleaks_hook()`. Five new friendly-error dictionary entries cover every documented `gh` failure mode.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| A | Static assets: 3 gitignore templates + gitleaks .pre-commit-config.yaml + .gitleaks.toml | 528bc0c |
| B | scripts/gh_handoff.py implementation | ed8d4dd |
| C | 5 new gh-* entries appended to dictionary.yaml (30 → 35) | 452d459 |
| D | Test implementations: test_gh_handoff.py (3 GREEN) + test_scaffold_extensions.py (2 GREEN) | 6372f5e |

## Test Results

| Test | V-ID | Result |
|------|------|--------|
| test_ship_runs_private_create | V-01 | GREEN |
| test_failure_modes_friendly | V-02 | GREEN |
| test_auth_drift_friendly | V-08 | GREEN |
| test_gitignore_composition | V-05 | GREEN |
| test_gitleaks_config | V-06 | GREEN |
| test_gitleaks_blocks_real_secret | V-07 | SKIP (pre-commit/gitleaks not installed locally — skipif guard correct) |

Full suite: **132 passed, 12 skipped, 0 failures** (previously 127 passed, 17 skipped — 5 stubs flipped).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] gh-not-installed dictionary ordering**
- **Found during:** Task C acceptance verification
- **Issue:** `translate('gh: command not found')` returned the old `gh-not-found` entry (pos 8) instead of the new `gh-not-installed` (appended at end). `gh-not-found` title "The GitHub CLI isn't installed yet" does not contain `'gh'` as a substring (`'gh' in 'the github cli...'` is False — "github" = g-i-t-h-u-b, no consecutive g-h). The plan's acceptance criteria `assert 'gh' in m.title.lower()` would fail.
- **Fix:** Moved `gh-not-installed` to appear BEFORE `gh-not-found` in the dictionary (pos 7 vs pos 8). Updated title to "The gh CLI isn't installed" which explicitly contains "gh". The old `gh-not-found` entry is retained as a fallback; no Phase 5 tests reference it by id.
- **Files modified:** references/friendly-errors/dictionary.yaml
- **Commit:** 452d459

**2. [Rule 1 - Bug] test_gh_handoff mock strategy: state.md not written under mock**
- **Found during:** Task D, first test run
- **Issue:** `mock_gh_subprocess` from conftest monkeypatches `subprocess.run` globally. `_write_state_field` in `gh_handoff.py` calls `subprocess.run([sys.executable, STATE_WRITER, "write", ...])` which was intercepted by the mock and returned `(rc=0, "", "")` without actually writing state.md. `state_path.read_text()` raised `FileNotFoundError`.
- **Fix:** Replaced use of `mock_gh_subprocess` fixture with a new `_GhGitShell` class defined in the test module. `_GhGitShell` captures the real `subprocess.run` reference before any monkeypatching and passes calls containing `"state_writer"` through to the real implementation while intercepting gh/git calls.
- **Files modified:** scripts/tests/test_gh_handoff.py
- **Commit:** 6372f5e

## Known Stubs

The following tests in `test_scaffold_extensions.py` remain as `pytest.skip("Wave 1 target")` — they are out of scope for Plan 06-02 (assigned to other Wave 1 tracks):
- `test_env_example_committed` (V-09 — Track B scaffold extensions)
- `test_pick_database` (V-10 — Track B `_pick_database` pure function)
- `test_db_default_per_playbook` (V-11 — Track B compose.yaml conditional write)
- `test_docker_artifacts` (V-12 — Track B Dockerfile multi-stage)
- `test_one_ci_workflow` (V-13 — Track B CI workflow template)

These stubs are intentional and will be resolved by Plan 06-03 (Track B scaffold extensions).

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes beyond what the plan's `<threat_model>` documents. All mitigations confirmed present:

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-06-02-01 | shell=False throughout; project name not user-substituted in gh argv | Confirmed (grep -c shell=True = 0) |
| T-06-02-02 | ctx={"tool": "gh"} only; no user input in ctx | Confirmed |
| T-06-02-03 | Token redaction via `re.sub(r"ghps_[A-Za-z0-9_]{20,}", "[REDACTED-TOKEN]", raw)` in `_friendly()` | Implemented |
| T-06-02-04 | .gitleaks.toml allowlist is static, end-anchored | Confirmed |
| T-06-02-06 | state_writer atomic write + _check_value_safe rejects newlines; ssh_url sanitized before write | Confirmed |

## Self-Check: PASSED

Files created:
- `scripts/gh_handoff.py` — FOUND
- `assets/gitignore-templates/common.gitignore` — FOUND
- `assets/gitignore-templates/node.gitignore` — FOUND
- `assets/gitignore-templates/python.gitignore` — FOUND
- `assets/gitleaks/.pre-commit-config.yaml` — FOUND
- `assets/gitleaks/.gitleaks.toml` — FOUND

Commits verified:
- 528bc0c (static assets) — FOUND
- ed8d4dd (gh_handoff.py) — FOUND
- 452d459 (dictionary entries) — FOUND
- 6372f5e (test implementations) — FOUND

Full pytest suite: 132 passed, 12 skipped, 0 failures — PASSED
