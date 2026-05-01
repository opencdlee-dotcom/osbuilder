---
phase: 05-common-person-ux-polish
plan: "04"
subsystem: mode-gating-intake-and-stack-researcher
tags:
  - mode-gating
  - beginner-default
  - advanced-flag
  - jargon-suppression
  - stack-menu-fallback
  - tdd-green
requirements:
  - UX-03
dependency-graph:
  requires:
    - scripts/tests/test_mode_gating.py (6 RED stubs from Plan 05-01)
    - scripts/state_writer.py (mode field in ALLOWED_FIELDS — added by Plan 05-01)
    - scripts/intake_handler.py (friendly_error import guard from Plan 05-02 preserved)
    - scripts/stack_researcher.py (friendly_error import guard from Plan 05-02 preserved)
    - references/stack-menu.md (parsed by _read_stack_menu in beginner mode)
  provides:
    - intake_handler._mode_from_state and mode-aware _render_derived_spec
    - stack_researcher._mode_from_state and mode-gated research_stack
    - 8/8 test_mode_gating.py tests pass (6 stubs flipped + 2 supplementary)
  affects:
    - All future Phase 5 plans that surface stack/deploy choices to the user — they
      can rely on `_mode_from_state` returning "beginner"|"advanced" with safe default
    - test_stack_researcher.py::test_calls_brainiac (Phase 3) — now correctly
      monkeypatches _call_brainiac instead of relying on path-name accidents
tech-stack:
  added: []
  patterns:
    - mode-gate-via-state-md (read mode field via state_writer subprocess; default "beginner")
    - branch-on-mode-then-fallback (beginner → stack-menu defaults; advanced → brainiac then fallback)
    - kwarg-mode-default-beginner (functions accept `mode: str = "beginner"` so callers without mode get safe behavior)
    - monkey-patch-mode-helper-for-tests (tests use monkeypatch on _mode_from_state and _call_brainiac for direct path coverage)
key-files:
  created:
    - .planning/phases/05-common-person-ux-polish/05-04-SUMMARY.md
  modified:
    - scripts/intake_handler.py (add _mode_from_state, REPO_ROOT/STATE_WRITER consts, mode kwarg in _render_derived_spec, mode read in parse_paragraph/parse_structured)
    - scripts/stack_researcher.py (add _mode_from_state, gate _call_brainiac branch on mode value)
    - scripts/tests/test_mode_gating.py (6 RED stubs flipped to real assertions + 2 supplementary tests)
    - scripts/tests/test_stack_researcher.py (test_calls_brainiac strengthened — direct monkeypatch on _call_brainiac and _mode_from_state instead of relying on path-name match)
decisions:
  - "_mode_from_state lives in BOTH intake_handler.py and stack_researcher.py as a verbatim copy — both modules are independent stdlib-only modules; sharing via a third helper module would require a refactor that's out of scope for this plan."
  - "Beginner mode defaults: a missing state.md, missing mode field, parse error, or empty value all collapse to 'beginner'. UX-03 acceptance: forbidden tech-name tokens never leak in default-mode user output, even on broken state files."
  - "scaffold_dispatch.py needed no mode-gate changes — current implementation has no interactive 'are you sure?' prompts (no input() calls). The graceful-degrade friendly_error import guard from Plan 05-02 is the only Phase 5 wiring required."
  - "Pre-existing test_calls_brainiac (Phase 3) was rewritten — the original implementation relied on pytest's tmp_path putting the test function name 'test_calls_brainiac' into the project-root path string, which made the str-substring 'brainiac' match against ANY subprocess call (even state_writer reads/writes). Now monkeypatches _call_brainiac directly: tighter, faster, no path-name dependency."
  - "Two supplementary mode_gating tests added during RED phase: test_beginner_mode_omits_stack_hints_from_structured (parse_structured + supplied stack_hints in beginner mode → output has none) and test_advanced_mode_includes_stack_hints (advanced mode preserves them). The plan's 6 stubs covered the symmetric pair indirectly; explicit tests harden the gate against future refactors of _render_derived_spec."
metrics:
  duration: ~9 minutes (single agent, sequential)
  tasks: 1
  files: 4 (1 created, 3 modified — plus inadvertent test_stack_researcher.py fix)
  completed: 2026-05-01
---

# Phase 5 Plan 04: Mode Gating in intake_handler + stack_researcher Summary

**One-liner:** Adds `_mode_from_state()` helpers to `intake_handler.py` and `stack_researcher.py`, gates jargon-bearing output (Next.js, Drizzle, Postgres, etc.) behind `mode == "advanced"`, and routes beginner-mode `research_stack` calls straight to `references/stack-menu.md` defaults — bypassing the brainiac subprocess entirely.

## Outcome

Default-mode (beginner) users now never see technology names in `derived_spec.md` or `research_stack` output. The `mode` field in `state.md` (added in Plan 05-01) is the single gate, read once per call via the `state_writer.py read --field mode` subprocess. On any failure (missing state.md, parse error, empty value, exception), the helper returns `"beginner"` — the safe default. Advanced mode preserves the original Phase 3 behavior (brainiac → stack-menu fallback for `research_stack`; full `stack_hints` in derived_spec). All 6 `test_mode_gating.py` RED stubs from Plan 05-01 flip to GREEN; 2 supplementary tests harden the symmetric beginner/advanced behavior of `_render_derived_spec`. Full suite is 97 passed, 29 skipped, 0 failed (up from 89 passed, 35 skipped).

A pre-existing Phase 3 test (`test_calls_brainiac`) had to be strengthened — its original "len(brainiac_calls) >= 1" assertion was passing accidentally because pytest's `tmp_path` put the test function name (`test_calls_brainiac`) into the project-root path string, which the loose substring matcher counted as a "brainiac" call. With my mode-gating change forcing default beginner mode (no brainiac call), the path-name match still spuriously passed. Rewrote the test to use `monkeypatch.setattr(sr, "_mode_from_state", ...)` and `monkeypatch.setattr(sr, "_call_brainiac", ...)` for direct, deterministic coverage.

## Tasks Executed

| Task | Description | Files | Commit |
|---|---|---|---|
| 1 (RED) | Flip 6 mode_gating stubs + add 2 supplementary tests | scripts/tests/test_mode_gating.py | d84b733 |
| 1 (GREEN) | Implement `_mode_from_state` + mode-gate research_stack and _render_derived_spec | scripts/intake_handler.py, scripts/stack_researcher.py, scripts/tests/test_stack_researcher.py | dc124fe |

### Changes by file

**scripts/intake_handler.py:**
- Added `import subprocess` and `REPO_ROOT`/`STATE_WRITER` module-level constants (mirroring stack_researcher.py pattern)
- Added `_mode_from_state(project_root: Path) -> str` helper (reads `mode` via state_writer subprocess; default `"beginner"` on any failure — missing state.md, exception, empty stdout)
- `_render_derived_spec` now accepts `mode: str = "beginner"`; stack_hints line only emitted when `mode == "advanced"`
- `parse_paragraph` and `parse_structured` call `_mode_from_state(root)` and pass `mode=_mode` to `_render_derived_spec`

**scripts/stack_researcher.py:**
- Added `_mode_from_state(project_root: Path) -> str` (verbatim copy of intake_handler's helper)
- `research_stack` now reads mode at the top of the function; beginner mode short-circuits to `_read_stack_menu(REFERENCES_ROOT)` and skips `_call_brainiac`. Advanced mode preserves the original Phase 3 brainiac → fallback flow.

**scripts/scaffold_dispatch.py:**
- No changes (no interactive prompts to gate; friendly_error import guard from Plan 05-02 is the only Phase 5 wiring required, already in place)

**scripts/tests/test_mode_gating.py:**
- All 6 RED stubs replaced with real assertions:
  - `test_mode_field_allowed_in_state_writer` — verifies state_writer accepts `mode=beginner` and `mode=advanced` writes
  - `test_beginner_mode_no_jargon_in_prompts` — `parse_paragraph("I want a TODO web app")` in beginner mode → derived_spec.md and stdout/stderr capture grep against the 9-token forbidden list (`Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind`)
  - `test_advanced_mode_exposes_stack` — `research_stack("web")` in advanced mode (with `_call_brainiac` mocked empty) returns a dict containing at least one of `{framework, orm, database, css, package_manager}`
  - `test_mode_default_is_beginner` — project_root with no state.md → `_mode_from_state` returns `"beginner"`
  - `test_mode_persists_across_state_reads` — write `mode=advanced`, read `mode` → `"advanced"`
  - `test_beginner_mode_stack_researcher_skips_brainiac` — `_call_brainiac` monkeypatched as a spy; in beginner mode the spy receives 0 calls
- 2 supplementary tests added during RED phase:
  - `test_beginner_mode_omits_stack_hints_from_structured` — `parse_structured(..., stack_hints=[...])` in beginner mode → output has none of the supplied tech names
  - `test_advanced_mode_includes_stack_hints` — same test in advanced mode → output retains supplied tech names

**scripts/tests/test_stack_researcher.py:**
- Rewrote `test_calls_brainiac` to use `monkeypatch.setattr(sr, "_mode_from_state", lambda root: "advanced")` and a spy on `sr._call_brainiac`. The original loose substring matcher made the assertion pass for any subprocess call whose argv-as-string contained "brainiac" — including the project-root path `pytest-NNN/test_calls_brainiac0`. The new implementation is deterministic and decoupled from pytest's tmp directory naming.

## Verification

| Check | Expected | Result |
|---|---|---|
| `pytest scripts/tests/test_mode_gating.py` | 8 passed (6 stubs + 2 supplementary) | **8 passed in 1.34s** |
| `pytest scripts/tests/test_friendly_error.py` (Plan 05-02 regression) | 11 passed | **11 passed (no regression)** |
| `pytest scripts/tests/test_stack_researcher.py` (Phase 3 regression) | 4 passed | **4 passed (test_calls_brainiac strengthened)** |
| Full suite | 0 failed | **97 passed, 29 skipped, 0 failed, 1 pre-existing warning** |
| `_mode_from_state(project_root_no_state_md)` | "beginner" | **"beginner"** (verified via inline python -c) |
| `research_stack("web", project_root=beginner_root)` calls `_call_brainiac` | no | **no** (verified via mock.patch.object spy) |
| `_render_derived_spec(stack_hints=["Next.js"], mode="beginner")` contains "Next.js" | no | **no** (forbidden-jargon test passes) |
| `_render_derived_spec(stack_hints=["Next.js"], mode="advanced")` contains "Next.js" | yes | **yes** (advanced-mode includes_stack_hints test passes) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Pre-existing test_calls_brainiac assertion was passing accidentally**

- **Found during:** GREEN-phase regression check
- **Issue:** After my mode-gating change, `test_calls_brainiac` continued to pass even though `_call_brainiac` was no longer being invoked. Investigation revealed the loose substring matcher (`if (isinstance(c[0], list) and any("brainiac" in str(part) for part in c[0]))`) was matching against the project-root path string, which pytest's `tmp_path` fixture builds as `pytest-NNN/test_calls_brainiac0` — containing the literal substring "brainiac". The test had a Phase 3 hidden bug that became visible when my mode-gating change broke the brainiac code path under default `tmp_project_root` conditions. The OUTPUT_IS_STRUCTURED and ADVANCED_OVERRIDE tests passed not because brainiac was called, but because `_read_stack_menu()` returns the same `_WEB_DEFAULTS` shape they assert on.
- **Fix:** Rewrote `test_calls_brainiac` to use `monkeypatch.setattr(sr, "_mode_from_state", lambda root: "advanced")` plus a direct `monkeypatch.setattr(sr, "_call_brainiac", spy)`. This decouples the test from pytest's tmp directory naming and from the indirect `subprocess.run` mocking layer.
- **Files modified:** scripts/tests/test_stack_researcher.py
- **Commit:** dc124fe

This is a Rule 1 fix — the test was buggy because of the path-name accident, and my mode-gating change exposed the bug.

**2. [Rule 2 — Missing critical functionality] Added 2 supplementary tests during RED phase**

- **Found during:** RED-phase test design
- **Issue:** Plan 05-01's 6 mode_gating stubs covered `parse_paragraph` (text path) and `_mode_from_state` defaults but not `parse_structured` (dict path) directly, and lacked an explicit advanced-mode counter-test for `_render_derived_spec`. Without explicit symmetric tests, future refactors of `_render_derived_spec` could silently break the advanced path while keeping beginner-mode tests green.
- **Fix:** Added `test_beginner_mode_omits_stack_hints_from_structured` and `test_advanced_mode_includes_stack_hints` to lock in the symmetric behavior at the structured-input level.
- **Files modified:** scripts/tests/test_mode_gating.py
- **Commit:** d84b733

This is a Rule 2 fix — without these tests, the gate is undertested at the dict-input boundary that `parse_structured` exposes.

### Out of Scope (deferred / not done)

- **Module-level extraction of `_mode_from_state`:** The plan explicitly directed verbatim copy of the helper into both modules. A refactor into a shared helper module (`scripts/_mode.py` or similar) would be a small architectural change and is out of scope here.
- **Tutor mode tests (`test_tutor_mode.py`):** Out of scope — Plan 05-03 (running in parallel as Wave 1) targets that. The 8 tutor-mode stubs remain skipped after this plan; that is the expected state.
- **Tech writer / narration tests:** Out of scope — Plans 05-03 and 05-05 target those.

## Threat Model Compliance

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-05-04-01 (Tampering — mode field injection via state.md) | `_mode_from_state` reads via the `state_writer.py read` subprocess, which enforces `_check_value_safe` on writes (rejects newlines, "..") via `_check_field_allowed` allowlist. Invalid mode values stored in state.md (if any) collapse to `"beginner"` via the `r.stdout.strip() or "beginner"` default. | mitigated; verified by `test_mode_default_is_beginner` |
| T-05-04-02 (Information Disclosure — technology names in beginner-mode output) | `test_beginner_mode_no_jargon_in_prompts` greps `parse_paragraph` output against the 9-token forbidden list; `test_beginner_mode_omits_stack_hints_from_structured` does the same for `parse_structured`. CI gate. | mitigated; verified by 2 explicit jargon-grep tests |
| T-05-04-03 (Spoofing — beginner mode bypassed by manipulating next_action in state.md) | accepted as designed | mode gating is UX-only; no security boundary |

No new threat surface introduced. The state_writer subprocess invocation uses `shell=False` and a fully argv-list-based command, mirroring the existing Phase 1–4 pattern.

## Threat Flags

None — `_mode_from_state` reads from a state.md file already validated by Phase 1's `_check_value_safe`. No new network endpoints, file paths, or trust boundaries introduced.

## Self-Check

- File created: `.planning/phases/05-common-person-ux-polish/05-04-SUMMARY.md` ✓ FOUND
- Files modified:
  - scripts/intake_handler.py ✓ FOUND (`_mode_from_state` defined; `_render_derived_spec` has `mode` kwarg; `parse_paragraph` and `parse_structured` call `_mode_from_state`)
  - scripts/stack_researcher.py ✓ FOUND (`_mode_from_state` defined; `research_stack` branches on `mode == "beginner"`)
  - scripts/tests/test_mode_gating.py ✓ FOUND (8 tests, 0 `pytest.skip("Wave 1 target")` calls remain)
  - scripts/tests/test_stack_researcher.py ✓ FOUND (test_calls_brainiac uses `monkeypatch.setattr(sr, "_call_brainiac", ...)`)
- Commit d84b733 (RED) ✓ FOUND
- Commit dc124fe (GREEN) ✓ FOUND
- 6 stubs from Plan 05-01 flipped GREEN ✓ PASS
- 2 supplementary tests pass ✓ PASS
- 4 Phase 3 stack_researcher tests pass ✓ PASS
- 11 Phase 5 friendly_error tests pass (no Plan 05-02 regression) ✓ PASS
- Full suite: 97 passed, 29 skipped, 0 failed ✓ PASS

## Self-Check: PASSED

## TDD Gate Compliance

This plan ran a single TDD cycle (Plan 05-04 has type=execute with task tdd="true"):

1. **RED gate:** commit d84b733 — `test(05-04): add failing tests for beginner/advanced mode gating`. The new tests were verified to fail before any implementation was added (`pytest scripts/tests/test_mode_gating.py` showed 6 failures + 2 passes due to Plan 05-01's pre-shipped state_writer ALLOWED_FIELDS extension that satisfied 2 of the symmetric tests without code changes).
2. **GREEN gate:** commit dc124fe — `feat(05-04): mode-gate intake_handler and stack_researcher (UX-03)`. All 8 mode_gating tests pass; full suite 97 passed, 0 failed.
3. **REFACTOR gate:** not invoked. The implementation matched the planned shape on the first try; no cleanup needed.

## Next

Phase 5 Wave 1 plans 05-03 (narration + tutor mode) and 05-05 (tech writer + humanizer) flip the remaining 29 RED stubs to GREEN. Both are independent of this plan's mode-gating logic — neither imports from intake_handler or stack_researcher.
