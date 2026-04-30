---
phase: 04-gsd-handoff-verify-loop-failure-classifier
plan: 06
subsystem: security
tags: [slopsquatting, registry-verify, subprocess, gsd-driver, heal-05, gap-closure, tdd]

# Dependency graph
requires:
  - phase: 04-gsd-handoff-verify-loop-failure-classifier
    provides: REGISTRY_VERIFY constant declared in gsd_driver.py (Plan 04-02), registry_verify.py CLI gate (Plan 04-04)
provides:
  - "Live HEAL-05 wiring: registry_verify.py invoked from gsd_driver.py phase_step==2 before any install"
  - "Three integration tests covering: (a) call wiring with stack_choices, (b) blocking on exit 1, (c) graceful skip when stack_choices absent"
  - "Recursion-safe selective_run monkeypatch pattern (capture _real_run pre-patch; match by argv-token script-path suffix)"
affects: [05-execute-loop, 06-error-translation, future-install-call-sites]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-install registry gate at the phase-loop level (slopsquatting defense, Snyk 2025 + Lasso AI 2025 research)"
    - "Selective subprocess monkeypatch: capture real run before patching to avoid recursion when patched function delegates"
    - "Tight argv-token matching (path.endswith) instead of loose substring scan for script-call discrimination"

key-files:
  created: []
  modified:
    - "scripts/gsd_driver.py — added _run_registry_gate helper (lines 191-249); replaced step 2 handler (lines 281-284)"
    - "scripts/tests/test_gsd_driver.py — appended 3 HEAL-05 integration tests (now 19 tests, 331 lines)"

key-decisions:
  - "last_failure message uses neutral 'slopsquatting gate blocked pkg X on Y' instead of 'registry_verify blocked: X on Y' so future test substring matchers do not misclassify the state_writer write as a registry_verify call"
  - "Gate fails-OPEN on absent/empty/malformed stack_choices (advances phase_step) rather than blocking — package may not be known at plan time; build_install_cmd remains the install-time backstop"
  - "Tests intercept gsd_driver.subprocess.run via setattr on the module object; capture _real_run reference BEFORE patching so state_writer subprocess calls forwarded by selective_run do not re-enter the patched function (RecursionError otherwise)"
  - "Test selective_run matches by argv-token suffix (`c.endswith('registry_verify.py')`) rather than ' '.join substring scan, so values containing the substring 'registry_verify' do not trigger false positives"

patterns-established:
  - "HEAL-05 gate pattern: state_writer.read → JSON parse stack_choices → subprocess.run([REGISTRY_VERIFY, --pkg, --ecosystem]) → on exit 1, _write_field('last_failure', ...) and return 1 without bumping phase_step"
  - "Recursion-safe monkeypatch: `_real_run = subprocess.run` BEFORE `monkeypatch.setattr(...)`; selective_run delegates non-target calls to `_real_run`, never to `subprocess.run` (which is now the patched proxy)"
  - "Skip-gracefully semantics for missing optional state fields: empty stack_choices, malformed JSON, missing pkg/eco → bump phase_step + return 0 (do not crash the phase loop)"

requirements-completed: [HEAL-05]

# Metrics
duration: 6min
completed: 2026-04-30
---

# Phase 04 Plan 06: Wire registry_verify.py into gsd_driver step 2 (HEAL-05) Summary

**Closes the SC5 gap from Phase 04 verification — REGISTRY_VERIFY constant goes from dead-code declaration to live slopsquatting gate invoked from gsd_driver.emit_next_command at phase_step==2, with three integration tests proving the wiring blocks bad packages, advances on verified packages, and skips gracefully when stack_choices is absent.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-30T21:25:09Z
- **Completed:** 2026-04-30T21:31:11Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 2 (scripts/gsd_driver.py, scripts/tests/test_gsd_driver.py)

## Accomplishments

- **HEAL-05 fully satisfied** — registry_verify.py is now invoked from gsd_driver.py at phase_step=2 BEFORE any install command runs (was: `_bump_field` no-op).
- **Three integration tests (19 total in test_gsd_driver.py, was 16):**
  - `test_step_2_calls_registry_verify` — confirms subprocess invokes REGISTRY_VERIFY with `--pkg next --ecosystem npm` derived from `stack_choices` JSON.
  - `test_step_2_blocks_on_registry_failure` — confirms exit-1 from registry causes return 1, phase_step remains at 2, last_failure populated.
  - `test_step_2_skips_gate_without_stack_choices` — confirms gate is skipped silently when stack_choices is absent (advances to step 3).
- **Threat mitigations T-04-06-01 (Tampering on subprocess args) and T-04-06-02 (Tampering on last_failure message) implemented** via list-form subprocess.run(shell=False) + hardcoded message template + state_writer allowlist pre-validation.
- **Zero regressions:** full pytest suite went from 75 → 78 tests, all GREEN.

## Task Commits

Each task was committed atomically following the TDD RED → GREEN cycle:

1. **Task 1 (RED): Three failing integration tests for step 2 registry gate** — `7b525e1` (test)
2. **Task 2 (GREEN): _run_registry_gate helper + step 2 handler replacement** — `298b27c` (feat)

The Task 2 commit also includes the test-pattern tightening (Rule 1 auto-fix — see Deviations) since both edits are required for the GREEN gate to be observable.

## Files Created/Modified

- **`scripts/gsd_driver.py`** (modified, +47 lines) — Added `_run_registry_gate(project_root, state) -> int` helper function above `emit_next_command` (lines 191-249); replaced step 2 handler from `_bump_field + return 0` (4 lines) to `return _run_registry_gate(project_root, state)` (3 lines + comment).
- **`scripts/tests/test_gsd_driver.py`** (modified, +128 lines) — Appended `test_step_2_calls_registry_verify`, `test_step_2_blocks_on_registry_failure`, `test_step_2_skips_gate_without_stack_choices`. Each uses a recursion-safe selective_run monkeypatch that captures `_real_run = subprocess.run` BEFORE `monkeypatch.setattr(gd.subprocess, "run", selective_run)` so state_writer subprocess calls forwarded inside selective_run do not re-enter the patched function.

## Decisions Made

- **Neutral last_failure message** ("slopsquatting gate blocked pkg X on Y") instead of the plan's literal `"registry_verify blocked: ..."` — the latter contains the substring "registry_verify" which collided with test pattern matchers. Choosing neutral wording is also more user-friendly: "slopsquatting" is the threat class, "registry_verify" is just the tool name.
- **Tight selective_run argv-token matching** instead of loose substring scan in tests. `c.endswith("registry_verify.py")` over `"registry_verify" in " ".join(...)` — robustness against future state values containing tool names.
- **Skip-gracefully semantics** when stack_choices is absent/empty/malformed — fails open at the phase-loop level because the package may not be known yet (e.g., still in research). The install-call-site gate (`build_install_cmd`) remains the final mandatory checkpoint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Recursion in test selective_run pattern as written in plan**
- **Found during:** Task 1 RED verification
- **Issue:** The plan's `selective_run` did `import subprocess as _real_subprocess` and then `_real_subprocess.run(cmd, ...)` for the delegate path. After `monkeypatch.setattr(gd.subprocess, "run", selective_run)`, the `subprocess` module's `run` attribute IS the same object as `gd.subprocess.run` (Python module objects are singletons). So `_real_subprocess.run` resolved to `selective_run` itself → infinite recursion → RecursionError before the assertion could even fire.
- **Fix:** Capture the real run as a local function reference BEFORE monkeypatching: `_real_run = _real_subprocess.run` at the top of each test; `selective_run` then calls `_real_run(...)` for non-registry calls. Plan's hint text incorrectly described `gd.subprocess` as "the module's reference, not the global" — Python doesn't distinguish; module attribute mutation is global.
- **Files modified:** scripts/tests/test_gsd_driver.py (all three tests)
- **Verification:** Re-ran the three tests; RecursionError replaced with proper assertion failures (Test 1 FAIL "registry_verify.py was not invoked", Test 2 FAIL "must return 1", Test 3 PASS — exactly as plan predicted for RED state).
- **Committed in:** `7b525e1` (Task 1 RED commit)

**2. [Rule 1 - Bug] Substring collision: state_writer write of last_failure misclassified as registry_verify call**
- **Found during:** Task 2 GREEN verification (Test 2 still failed after implementation)
- **Issue:** With the plan's literal message `"registry_verify blocked: {pkg} not found on {eco} registry"`, the value contains substring "registry_verify". The test's selective_run did `" ".join(cmd)` and then `if "registry_verify" in sig`. When `_write_field` called `subprocess.run([state_writer.py, "write", "--field", "last_failure", "--value", "registry_verify blocked: ..."])`, that joined string DID contain "registry_verify" → selective_run short-circuited with `CompletedProcess(returncode=1)` instead of forwarding to real subprocess → write was dropped → last_failure remained empty → Test 2 assertion failed.
- **Fix:** Two complementary corrections (the plan's watch-out hinted at the second; the first is robust against future regressions of the same class):
  1. **Implementation:** Changed last_failure message to `f"slopsquatting gate blocked pkg {pkg} on {eco}"` — the plan-suggested fallback template, which doesn't contain the substring "registry_verify".
  2. **Tests:** Tightened selective_run pattern to argv-token suffix match: `any(isinstance(c, str) and c.endswith("registry_verify.py") for c in cmd)`. Even if a future state value mentions "registry_verify", the matcher won't be fooled.
- **Files modified:** scripts/gsd_driver.py (`_run_registry_gate` last_failure message), scripts/tests/test_gsd_driver.py (both `selective_run` definitions in tests 1 and 2; test 3 also updated for consistency).
- **Verification:** All 19 tests in test_gsd_driver.py GREEN; full suite 78/78 GREEN.
- **Committed in:** `298b27c` (Task 2 GREEN commit — the test fix and impl message change ship together because both are required to observe GREEN).

---

**Total deviations:** 2 auto-fixed (both Rule 1 bug fixes — neither was scope creep; both were strictly necessary to make the plan's intent observable.)
**Impact on plan:** No scope changes. Both fixes corrected mistakes inside the plan's own test code and message template. The three plan behaviors were preserved exactly.

## Issues Encountered

- **Acceptance criterion `grep -c 'shell=True' = 0` literal check fails (returns 2):** The two hits are in pre-existing docstrings (line 13 module docstring "No shell=True anywhere"; line 180 build_install_cmd docstring "no shell=True or string interpolation"). There are zero actual `subprocess.run(..., shell=True)` call sites — verified by `grep -nE 'subprocess\.run\([^)]*shell=True'` returning no matches. The criterion's spirit (no actual shell=True usage) is met; the literal grep counts pre-existing docstring text. Leaving the docstrings intact preserves the security principle as living documentation.

## User Setup Required

None — no external service configuration required. registry_verify.py uses public registries (npm, PyPI, crates.io) anonymously.

## Threat Flags

No new security-relevant surface introduced beyond what the plan's `<threat_model>` already captured (T-04-06-01, T-04-06-02 — both mitigated as planned).

## Next Phase Readiness

- HEAL-05 is now FULLY SATISFIED (was PARTIALLY — gate existed but was never invoked).
- Phase 04 SC5 ("registry_verify.py is wired into the gsd phase loop") flips from FAILED to VERIFIED.
- Plan 04-06 closes the gap identified in `04-VERIFICATION.md` and the code review findings (commit `d06cce5`).
- All 6 plans in Phase 04 now complete; Phase 04 ready for re-verification via `/gsd-verify-phase 4`.

## Self-Check: PASSED

- `scripts/gsd_driver.py` modifications present (lines 191-249 helper, 281-284 dispatch): VERIFIED
- `scripts/tests/test_gsd_driver.py` 3 new tests present: VERIFIED (`grep -c 'def test_step_2_'` returns 3)
- Commit `7b525e1` (test): FOUND in `git log`
- Commit `298b27c` (feat): FOUND in `git log`
- 19/19 tests in test_gsd_driver.py GREEN: VERIFIED
- 78/78 tests in full suite GREEN: VERIFIED
- `REGISTRY_VERIFY` no longer dead code (2 hits): VERIFIED
- `_run_registry_gate` defined and called (3 hits): VERIFIED
- `subprocess.run(shell=True)` actual call sites: 0 — VERIFIED
- last_failure write present in registry block path: VERIFIED

---
*Phase: 04-gsd-handoff-verify-loop-failure-classifier*
*Completed: 2026-04-30*
