---
phase: 01-foundation
plan: 01
subsystem: testing
tags: [pytest, gitattributes, test-infra, wave-0, line-endings, tdd-red-state]

# Dependency graph
requires: []
provides:
  - "pytest harness with pythonpath=['scripts'] so test files can import scripts/state_writer.py"
  - "15 RED-state test stubs (8 state_writer + 3 SKILL.md + 4 install.sh) ready for Wave 1 to turn GREEN"
  - "Cross-platform line-ending discipline (.gitattributes glob form, BLOCKER 4 fix)"
  - "Shared pytest fixtures (tmp_project_root, state_md_path, writer, fake_home)"
  - ".gitignore for Python build/cache artifacts"
affects: [01-02-skill-md, 01-03-install-sh, 01-04-state-writer, 01-05-bootstrap, all-future-phases-with-tests]

# Tech tracking
tech-stack:
  added:
    - pytest>=8.0 (dev-only)
    - ruff>=0.6 (dev-only)
  patterns:
    - "Lazy-import-via-fixture for not-yet-implemented modules (keeps tests COLLECTABLE in RED state)"
    - "pytest tmp_path-based isolation for HOME-modifying tests (T-1-W0-04 mitigation)"
    - "In-process monkeypatch (not subprocess) for atomicity tests (WARNING 3 fix)"
    - "Glob-form .gitattributes (matches VALIDATION row 1-W0-02 regex)"

key-files:
  created:
    - pyproject.toml
    - .gitattributes
    - .gitignore
    - scripts/tests/__init__.py
    - scripts/tests/conftest.py
    - scripts/tests/test_state_writer.py
    - scripts/tests/test_skill_md.py
    - scripts/tests/test_install.py
  modified: []

key-decisions:
  - "Lazy-import pattern via `sw` fixture instead of module-top `pytest.importorskip` so all 8 state_writer tests stay individually COLLECTABLE before Plan 04 lands (otherwise the file is skipped wholesale and the >=15 acceptance gate cannot be verified)"
  - "Added .gitignore at Wave 0 (not in original plan) to keep __pycache__/.pytest_cache/ out of git status (Rule 3 — blocking issue: pytest collection auto-creates __pycache__/ which would pollute every subsequent task's git status)"
  - "Glob form (`*.sh text eol=lf`) chosen over per-file form for .gitattributes — VALIDATION row 1-W0-02's regex (`^\\*\\.sh text eol=lf$`) only matches glob form (BLOCKER 4 closure)"
  - "test_atomic_replace_no_partial uses in-process monkeypatch with monkeypatch.setattr(sw, 'render_state_md', boom) — subprocess-based monkeypatch cannot reach across process boundary (WARNING 3 fix)"
  - "fake_home fixture isolates install.sh tests via HOME env override so the developer's real ~/.claude/skills/ is never touched (T-1-W0-04 mitigation)"

patterns-established:
  - "Test collection MUST stay green even when production code does not exist yet (lazy-import via fixture, never module-top importorskip)"
  - "Every <automated> verify command in later plans references a test that EXISTS HERE in RED state — Nyquist compliance pattern"
  - "Pure-stdlib YAML hand-parser in test_skill_md.py — no PyYAML dependency, keeps test deps minimal"

requirements-completed: []

# Metrics
duration: 85min
completed: 2026-04-29
---

# Phase 01 Plan 01: Wave 0 Test Infrastructure Summary

**pytest harness + 15 RED-state test stubs (8 state_writer / 3 SKILL.md / 4 install.sh) + glob-form .gitattributes + minimal pyproject.toml — every Wave 1 plan's `<automated>` verify command now resolves to a real test function instead of a forward reference.**

## Performance

- **Duration:** ~85 min (incl. one auto-fix iteration for lazy-import collection issue)
- **Started:** 2026-04-30T02:57:53Z
- **Completed:** 2026-04-30T04:24:21Z (UTC; commit timestamp 21:24 PDT)
- **Tasks:** 2 / 2
- **Files created:** 8 (pyproject.toml, .gitattributes, .gitignore, scripts/tests/{__init__,conftest,test_state_writer,test_skill_md,test_install}.py)

## Accomplishments

- 15 test functions COLLECTABLE by pytest (verified via `pytest scripts/tests/ --collect-only -q`); all 15 currently SKIP because Wave 1 production code is absent — RED state by design
- 8 stubs in `test_state_writer.py` cover VALIDATION rows 1-04-01..08 (atomicity, input-validation V5, init, line-count, round-trip, validate-rejects-missing, resume-after-clear, path-traversal V12)
- 3 stubs in `test_skill_md.py` cover rows 1-01-02..04 (frontmatter validity, line-count cap, references/ link)
- 4 stubs in `test_install.py` cover rows 1-03-04..07 (4-dir creation FOUND-03, idempotency, BLOCKER 1 artifact-copy, no-nested-dirs)
- `.gitattributes` matches the BLOCKER-4 regex `^\*\.sh text eol=lf$` literally — VALIDATION row 1-W0-02 will turn GREEN as soon as tracked
- `pyproject.toml` declares `pythonpath = ["scripts"]` and pytest>=8 / ruff>=0.6 as dev deps; no `[build-system]` (skill, not wheel)
- HOME-isolation `fake_home` fixture ensures install.sh tests never touch the real `~/.claude/skills/` (T-1-W0-04 mitigation)

## Task Commits

1. **Task 1: pyproject.toml + .gitattributes** — `bedee58` (feat)
2. **Task 2: scripts/tests/ scaffolding (5 files) + .gitignore** — `e3758de` (test)

_Note: .gitignore added inside Task 2's commit as Rule-3 deviation (see below)._

## Files Created/Modified

- `pyproject.toml` — pytest config (`pythonpath=["scripts"]`, `testpaths=["scripts/tests"]`, `addopts="-x --tb=short"`); dev deps pytest>=8 + ruff>=0.6
- `.gitattributes` — `* text=auto`; `*.sh`/`*.py`/`*.md` LF; `*.ps1` CRLF (Pitfall 9 fix)
- `.gitignore` — `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`, `.env*` (Rule-3 deviation)
- `scripts/tests/__init__.py` — empty package marker
- `scripts/tests/conftest.py` — fixtures: `tmp_project_root`, `state_md_path`, `writer`, `fake_home`; `run_state_writer` helper that subprocess-invokes `scripts/state_writer.py` with `--project-root`
- `scripts/tests/test_state_writer.py` — 8 RED-state stubs; lazy-imports state_writer via `sw` fixture so all 8 tests stay collectable
- `scripts/tests/test_skill_md.py` — 3 RED-state stubs; pure-stdlib YAML hand-parser; per-test `pytest.skip` when SKILL.md absent
- `scripts/tests/test_install.py` — 4 RED-state stubs; uses `fake_home` HOME-isolation; per-test `pytest.skip` when install.sh absent

## Decisions Made

1. **Lazy-import via fixture, NOT module-top importorskip.** The plan's verify command grep-counts test names from `--collect-only` output and requires >=15 hits. `pytest.importorskip("state_writer")` at module top causes the WHOLE FILE to be skipped at collection time (only the file path appears, not the 8 individual function names). Switched to a `sw` fixture that lazy-imports inside each test — collection succeeds for all 8 tests; runtime skip kicks in only when `state_writer` is imported. Result: 15/15 names appear in collection.
2. **Glob form for .gitattributes** — explicitly chosen because VALIDATION row 1-W0-02 regex `^\*\.sh text eol=lf$` only matches the glob line, not per-file lines. (BLOCKER 4 closure.)
3. **`addopts = "-x --tb=short"` in pyproject.toml** — short tracebacks reduce information disclosure (T-1-W0-03 mitigation); `-x` enables fast feedback per VALIDATION's "max latency 15s" requirement.
4. **In-process monkeypatch in `test_atomic_replace_no_partial`** — `monkeypatch.setattr(sw, "render_state_md", boom)` only works if `sw` is the in-process module; subprocess-based fixture cannot be reached. (WARNING 3 fix.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Switched from module-top `pytest.importorskip` to lazy-import-via-fixture in test_state_writer.py**
- **Found during:** Task 2 verify (`pytest --collect-only -q`)
- **Issue:** Plan's action block specified `state_writer = pytest.importorskip("state_writer")` at module top. Pytest skips the entire file in this case, meaning only 7 tests appear in `--collect-only` output (3 SKILL.md + 4 install) instead of 15. The plan's own verify command requires `1[5-9]` matches, so this would fail.
- **Fix:** Replaced module-top importorskip with a `sw` pytest fixture that runs `importlib.import_module("state_writer")` lazily and `pytest.skip(...)` on ImportError. Each of the 8 test functions now takes `sw` as a parameter. Result: 15 collected, 15 skipped at runtime when production code absent — same RED behavior, but all 15 names appear in collection.
- **Files modified:** `scripts/tests/test_state_writer.py`
- **Verification:** `python3 -m pytest scripts/tests/ --collect-only -q | wc -l` → 15; verify command `grep ... | wc -l | grep -E "^\s*1[5-9]"` exits 0
- **Committed in:** `e3758de` (Task 2 commit)

**2. [Rule 3 — Blocking] Added .gitignore at Wave 0 (not in original plan)**
- **Found during:** Task 2 staging (`git status --short`)
- **Issue:** pytest's `--collect-only` auto-creates `scripts/tests/__pycache__/` which would otherwise show up as untracked in every subsequent task's `git status`. Per task_commit_protocol step 7, generated runtime output must be ignored.
- **Fix:** Created `.gitignore` covering `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`, editor dirs, and `.env*`. Scope kept minimal — every entry is either Python build artifact, OS cruft, or a CLAUDE.md "never commit secrets" guard.
- **Files modified:** `.gitignore` (new)
- **Verification:** `git status --short` no longer shows `__pycache__/` after running pytest
- **Committed in:** `e3758de` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking)
**Impact on plan:** Both deviations were necessary to satisfy the plan's OWN verify commands. Zero scope creep — fixes are mechanical / hygienic, not feature additions.

## Authentication Gates

None — this plan creates only local test scaffolding. No external services, no auth surface.

## Issues Encountered

- pyright "not accessed" hints on fixture parameters in `test_state_writer.py`. False positive — pytest injects fixtures by parameter name at runtime, but pyright's static analysis cannot see the injection. Severity is "Hint" (lowest), not warning/error; non-blocking. Documented here so future contributors do not "fix" the warnings by removing the fixture parameters.

## TDD Gate Compliance

This plan is `type: execute` (NOT `type: tdd`), so per-plan RED/GREEN/REFACTOR commits are not required. However, the entire plan's PURPOSE is to create RED-state stubs for Wave 1 plans 02/03/04 to turn GREEN — the gate enforcement lives at the cross-plan level:

- **Plan 02 (SKILL.md)** turns GREEN: `test_frontmatter_valid`, `test_skill_md_line_count_under_200`, `test_has_references_link`
- **Plan 03 (install.sh)** turns GREEN: `test_install_creates_four_dirs`, `test_install_idempotent`, `test_install_no_nested_dirs`; AND with Plan 02's SKILL.md present, also `test_install_copies_artifacts`
- **Plan 04 (state_writer.py)** turns GREEN: all 8 in `test_state_writer.py`

If any of those plans complete without flipping their assigned tests from skip → pass, that is a Nyquist compliance failure traceable back to this plan's stubs.

## Known Stubs

All 15 test bodies are intentional stubs for Wave 1 to satisfy:

- `scripts/tests/test_state_writer.py` (8 stubs) — skip when `import state_writer` raises ImportError; will fail/pass once Plan 04 lands `scripts/state_writer.py`
- `scripts/tests/test_skill_md.py` (3 stubs) — skip when `SKILL.md` does not exist; will fail/pass once Plan 02 lands `SKILL.md`
- `scripts/tests/test_install.py` (4 stubs) — skip when `install.sh` does not exist; will fail/pass once Plan 03 lands `install.sh`

These stubs are NOT a bug: they are the deliverable. Per Nyquist rule, no production task may declare an `<automated>` verify command unless its target test exists. This plan is the test-creation phase that satisfies the precondition for plans 02–05.

## Threat Flags

None new this plan — all surface introduced (subprocess-driven test runs, HOME-override fixture) is already covered by the plan's `<threat_model>` (T-1-W0-01..04).

## User Setup Required

None — pure test scaffolding, no external services, no environment variables.

## Next Phase Readiness

- Wave 1 ready: plans 02/03/04/05 can run in parallel because their files are disjoint (`SKILL.md`, `install.sh`+`.gitkeep`, `scripts/state_writer.py`, `scripts/bootstrap.{sh,ps1}`) and all four already have their RED gate tests on disk.
- BLOCKER 4 closed via `^\*\.sh text eol=lf$` glob match in `.gitattributes`.
- WARNING 3 closed via in-process monkeypatch in `test_atomic_replace_no_partial`.
- WARNING 4 closed via `test_install.py` (4 stubs automating idempotency + nesting + artifact-copy that were previously manual-only).
- BLOCKER 1 (`install.sh` copies SKILL.md into install location) has its CI gate ready (`test_install_copies_artifacts`); closure happens when Plan 03 lands.
- BLOCKER 2 / BLOCKER 3 verify gates are documented in 01-VALIDATION.md rows 1-01-05/06 and 1-03-08/09 respectively — those are smoke/grep-based, not pytest-based, so this plan does not own their stubs.

## Self-Check: PASSED

Verified existence of all created files and commits:

- pyproject.toml — FOUND
- .gitattributes — FOUND
- .gitignore — FOUND
- scripts/tests/__init__.py — FOUND
- scripts/tests/conftest.py — FOUND
- scripts/tests/test_state_writer.py — FOUND (8 `def test_` lines)
- scripts/tests/test_skill_md.py — FOUND (3 `def test_` lines)
- scripts/tests/test_install.py — FOUND (4 `def test_` lines)
- Commit `bedee58` — FOUND in `git log`
- Commit `e3758de` — FOUND in `git log`
- `pytest scripts/tests/ --collect-only -q` — 15 collected, exit 0
- `grep -qE '^\*\.sh text eol=lf$' .gitattributes` — match on line `*.sh text eol=lf`

---
*Phase: 01-foundation*
*Completed: 2026-04-29*
