---
phase: 07-additional-playbooks
plan: 03
subsystem: scaffold
tags: [cli, typer, rich, sqlite, scaffold, phase-7]

# Dependency graph
requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    provides: scaffold_dispatch.py shape, _validate_project_name, atomic_write
  - phase: 06-ship-to-private-github-scalable-defaults
    provides: _write_ci_workflow stack-family helper, ASSETS constant
  - phase: 07-additional-playbooks-plan-01
    provides: app_type='cli' routing from intake (PLAYBOOK_KEYWORDS)
  - phase: 07-additional-playbooks-plan-02
    provides: ensure_uv() helper, _PLAYBOOK_DISPATCH dict, assets layout convention
provides:
  - "scaffold_cli(project_name, project_root) → uv init --app + uv add typer + substituted __main__.py + python CI workflow"
  - "_sanitize_module_name(name) → str (hyphens → underscores for Python module path)"
  - "_PLAYBOOK_DISPATCH gains 'cli' entry — third playbook on the routing surface"
  - "references/playbooks/cli.md — 56-line spec mirroring web.md/ai-service.md 7-section structure"
  - "assets/cli-starter/{__main__.py.tmpl, pyproject.snippet.toml} — vendored Typer + Rich + SQLite starter"
  - "references/stack-menu.md — +cli playbook defaults table + cross-ref bullet"
affects:
  - 07-04-desktop-playbook (will additively extend _PLAYBOOK_DISPATCH with 'desktop')
  - 07-05-hub-platform-playbook (cross-references cli.md)
  - 07-06-e2e-harness (parametrizes cli path)

# Tech tracking
tech-stack:
  added:
    - "typer 0.25.1 (CLI framework; rich >=13.8.0 hard-deped — NO [all] extras per Pitfall 5)"
    - "rich 15.0.0 (terminal styling; transitive via typer)"
    - "sqlite3 (stdlib; persistence path: ~/.<app-name>/state.db per D-13)"
  patterns:
    - "Module-name sanitization: hyphens → underscores via _sanitize_module_name (script name keeps hyphens; Python module dir gets underscores)"
    - "Per-playbook scaffold function mirrors scaffold_web's 4-step shape verbatim (validate → ensure_<tool> → subprocess.run → atomic_write); now applied 3 times consistently"
    - "Vendored starter assets/<framework>-starter/ pattern: cli-starter joins fastapi-starter; consistent layout aids debugging + e2e harness"
    - "CLI doesn't ship a Dockerfile (single-user local tool — RESEARCH.md §07-03); scaffold_cli only stamps the python CI workflow"

key-files:
  created:
    - scripts/tests/test_phase07_cli.py (187 lines, 5 tests)
    - assets/cli-starter/__main__.py.tmpl (48 lines; verbatim RESEARCH.md Code Example 2; {{project_name}} placeholder)
    - assets/cli-starter/pyproject.snippet.toml (14 lines; typer>=0.25.1, NO [all])
    - references/playbooks/cli.md (56 lines; under 80 cap)
  modified:
    - scripts/scaffold_dispatch.py (+81 lines / -1 line: _CLI_STARTER, _sanitize_module_name, scaffold_cli, _PLAYBOOK_DISPATCH 'cli' entry)
    - references/stack-menu.md (+10 lines: cli playbook defaults table + cross-ref)

key-decisions:
  - "D-13 implemented: SQLite path at ~/.<app-name>/state.db; APP_NAME holds the user-facing script name (with hyphens preserved); module dir uses underscores"
  - "D-14 implemented: scaffold_cli uses uv init --app + uv add typer (NO [all] extras; rich is hard-deped from typer 0.25.1+)"
  - "Pitfall 5 verified: tests assert (a) `typer[all]` is absent from pyproject.snippet.toml + cli.md, AND (b) `typer[all]` never appears in any subprocess argv emitted by scaffold_cli — catches regressions"
  - "Module-name sanitization rule: `_sanitize_module_name` is a pure str.replace('-', '_'); _validate_project_name regex restricts the input alphabet so the output is always a valid Python identifier (T-07-03-03 accepted)"
  - "CLI ships NO Dockerfile (departure from web/ai-service): single-user local tool per RESEARCH.md §07-03 refuse list; only the python CI workflow is stamped"
  - "Wave coordination: ensure_uv was already added by 07-02 (verified via grep at execution start); reused as-is, no duplication"

patterns-established:
  - "Per-plan atomic block in scaffold_dispatch.py via '=== Phase 7 — cli playbook (07-03) ===' divider — reproduces 07-02's RESEARCH.md Wave Coordination Option A"
  - "Lazy-import-via-fixture pattern carries forward (test_phase07_cli.py uses sd + has_cli guard)"
  - "Multi-playbook _PLAYBOOK_DISPATCH dict scales: 2 → 3 entries with no shape change; 07-04 (desktop) and 07-05 (hub-platform) plug in additively"

requirements-completed: [SCAF-03]

# Metrics
duration: 4min
completed: 2026-05-02
---

# Phase 7 Plan 03: CLI Playbook Summary

**Added the cli playbook to OSBuilder: a Python + Typer + Rich + SQLite scaffold path that turns "a command-line tool to organize my photo library" into a working `uv run <app-name> --help` Rich-formatted help screen and a `<app-name> ping` subcommand that writes/reads `~/.<app-name>/state.db` — proving SC-02's "persists state across runs" contract.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-02T08:26:43Z (after 07-02 completion)
- **Completed:** 2026-05-02T08:30:53Z
- **Tasks:** 2 (Wave 0 RED tests + Wave 1 GREEN implementation)
- **Files:** 5 (4 created, 1 modified to scaffold_dispatch.py + 1 minor edit to stack-menu.md)
- **Test delta:** +5 (166 → 171 passing; 1 pre-existing skip; zero regressions)

## Accomplishments

- `scaffold_cli` mirrors `scaffold_web`'s 4-step shape verbatim: validate → ensure_uv → uv init --app → uv add typer → atomic_write of substituted `__main__.py.tmpl` + python CI workflow.
- Vendored `assets/cli-starter/__main__.py.tmpl` (48 lines, verbatim from RESEARCH.md Code Example 2) — Typer app with `ping` subcommand demonstrating SQLite persistence.
- Module-name sanitization implemented: `my-cli` (script name) → `my_cli/__main__.py` (Python module path) via pure `str.replace("-", "_")`. The `_validate_project_name` regex restricts input to `[a-zA-Z0-9_-]`, so sanitization output is always a valid Python identifier.
- **Pitfall 5 verified explicitly:**
  - Pyproject snippet pins `typer>=0.25.1` (no `[all]` extras — rich is hard-deped from 0.25.1+ per typer changelog).
  - Test `test_scaffold_cli_subprocess_calls` asserts the literal `typer[all]` is absent from EVERY subprocess argv emitted by `scaffold_cli`.
  - Test `test_cli_starter_pyproject_snippet_present` asserts `typer[all]` is absent from the snippet.
- `_PLAYBOOK_DISPATCH` dict gains 3rd entry (`cli`) — the routing surface now spans web / ai-service / cli with no shape change. 07-04 (desktop) plugs in additively.
- 5/5 plan tests GREEN; 171/171 full suite passes (zero regressions).

## Task Commits

Each task committed atomically:

1. **Task 1: Wave 0 RED stubs (cli playbook + scaffold_cli + Pitfall 5 contracts)** — `1728b16` (test)
2. **Task 2: Wave 1 GREEN — scaffold_cli + _sanitize_module_name + cli-starter assets + cli.md + stack-menu entry** — `9b5d6a5` (feat)

## Files Created/Modified

### Created

- `scripts/tests/test_phase07_cli.py` (187 lines) — 5 tests: cli.md presence + 7 sections + ≤80 lines, cli-starter `__main__.py.tmpl` Typer/Rich/SQLite shape, pyproject snippet Pitfall 5 deps (typer>=0.25.1, no `typer[all]`), `scaffold_cli` subprocess argv shape (uv init + uv add typer; literal `typer[all]` absent from any argv), module-name sanitization (hyphens → underscores).
- `assets/cli-starter/__main__.py.tmpl` (48 lines) — Typer app + Rich Console + SQLite `pings` table; `{{project_name}}` placeholder substituted at scaffold time; `APP_NAME = "{{project_name}}"`; `DB_PATH = Path.home() / f".{APP_NAME}" / "state.db"`.
- `assets/cli-starter/pyproject.snippet.toml` (14 lines) — reference-only snippet showing `[project.scripts]` entry-point + `typer>=0.25.1` dep (NO `[all]`).
- `references/playbooks/cli.md` (56 lines, under 80 cap) — 7-section spec mirroring web.md / ai-service.md.

### Modified

- `scripts/scaffold_dispatch.py` (+81 lines / -1 line) — added `_CLI_STARTER` path constant, `_sanitize_module_name()`, `scaffold_cli()`, and a new `"cli": scaffold_cli` entry in `_PLAYBOOK_DISPATCH`. `ensure_uv` already existed from 07-02 — reused, NOT redefined.
- `references/stack-menu.md` (+10 lines) — `## cli playbook defaults` table (typer 0.25.1, rich 15.0.0, sqlite3 stdlib, uv 0.11.8) + `references/playbooks/cli.md` cross-ref bullet in the See-also section.

## Decisions Made

- **`ensure_uv` reuse vs duplication** — At execution start, ran `grep -c "def ensure_uv" scripts/scaffold_dispatch.py` per the plan's resolution rule. Result: 1 (already added by 07-02). Reused as-is; did NOT redefine. The shared dependency works cleanly because both 07-02 and 07-03 share the same parent commit (07-01).
- **No Dockerfile for CLI** — Departure from web/ai-service which both stamp Dockerfiles. CLI is a single-user local tool per RESEARCH.md §07-03 refuse list (Docker container shipping is explicitly refused). `scaffold_cli` only stamps the python CI workflow.
- **Module-name sanitization is a pure function, not a configurable** — `_sanitize_module_name` does exactly one thing: `str.replace("-", "_")`. The `_validate_project_name` regex restricts the input alphabet to `[a-zA-Z0-9_-]`, so collisions like `my--cli` → `my__cli` produce a still-valid Python identifier. T-07-03-03 disposition: accept (no double-underscore-leading edge case worth handling at this surface).
- **Pyproject snippet is reference-only, not consumed** — `scaffold_cli` does NOT splice the snippet into the user's `pyproject.toml`. The snippet documents the shape that `uv init` + `uv add typer` produces, plus the `[project.scripts]` entry-point that uv creates. The actual install path is the subprocess calls; the snippet is documentation that `_PLAYBOOK_TOOLS` and 07-04/05 can copy from.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `typer[all]` literal in pyproject.snippet.toml comment failed test_cli_starter_pyproject_snippet_present**
- **Found during:** Task 2 verification (first `pytest -x` run)
- **Issue:** The plan's recommended comment block in `pyproject.snippet.toml` referenced "do NOT use `typer[all]`" — embedding the literal string `typer[all]` in the snippet itself. The test `test_cli_starter_pyproject_snippet_present` asserts `assert "typer[all]" not in content`, which trips on the comment.
- **Fix:** Rephrased the comment to "the legacy bundled-extras spelling has been deprecated/redundant" — still conveys the Pitfall 5 reasoning without embedding the literal trigger string. Same pattern that 07-02 used for the `Astral.UV` typo.
- **Files modified:** `assets/cli-starter/pyproject.snippet.toml`
- **Committed in:** `9b5d6a5`

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking the acceptance criterion itself). No scope creep; no architectural change.

## Issues Encountered

None blocking. The single deviation above was caught at verification time and fixed before committing.

## Threat Flags

None new beyond the plan's `<threat_model>` register. T-07-03-01..04 disposition unchanged:
- T-07-03-01 (Tampering: SQLite path from project_name): mitigated by reused `_validate_project_name` regex; path lives under `Path.home()`.
- T-07-03-02 (Tampering: SQL injection via `ping`): mitigated by parametrized query in starter (`conn.execute("INSERT INTO pings (ts) VALUES (?)", (ts,))`).
- T-07-03-03 (Tampering: module-name sanitization collision): accepted — `_sanitize_module_name` is pure; the regex gate already restricts input alphabet.
- T-07-03-04 (InfoDisclosure: SQLite DB path in console output): accepted — by design (SC-02 verification UX); user opts in by running the tool.

No new attack surface beyond what the plan anticipated.

## User Setup Required

None at scaffold time. Manual smoke (07-HUMAN-UAT.md) post-scaffold:
1. `cd <project-name>`
2. `uv sync`
3. `uv run <project-name> --help` — should show Rich-formatted help.
4. `uv run <project-name> ping` — should print `ping #1 at <ts>` and write `~/.<project-name>/state.db`.
5. Re-run `uv run <project-name> ping` — count should increment (`ping #2`), proving persistence.

## Next Phase Readiness

- **07-04 (desktop playbook)** — unblocked. Will additively extend `_PLAYBOOK_DISPATCH` with `"desktop": scaffold_desktop`; the dispatch surface now established with 3 entries scales the same way for the 4th. `_PLAYBOOK_TOOLS["desktop"]` was already populated by 07-02 (with `("uv", "cargo")`); 07-04 will add the cargo install matrix entries and the `test_phase07_preflight_extensions.py` cargo tests.
- **07-05 (hub-platform)** — unblocked. Cross-references cli.md from the multi-app section.
- **07-06 (e2e harness)** — unblocked. Parametrized E2E can spin up a cli intake → scaffold → smoke loop using the `app_type='cli'` route from 07-01 and the now-real `scaffold_cli` from this plan.

## Self-Check: PASSED

Files:
- `references/playbooks/cli.md` — FOUND (56 lines, ≤ 80 cap; 7 mandatory sections present)
- `assets/cli-starter/__main__.py.tmpl` — FOUND (48 lines; `import typer`, `from rich.console import Console`, `{{project_name}}`, `@app.command()`, `def ping():`, `CREATE TABLE IF NOT EXISTS pings` all present)
- `assets/cli-starter/pyproject.snippet.toml` — FOUND (14 lines; `typer>=0.25.1` present; `typer[all]` absent)
- `scripts/tests/test_phase07_cli.py` — FOUND (5 tests; lazy-import pattern; literal `typer[all]` only appears in negative assertions/comments)

Code surface:
- `scaffold_dispatch.scaffold_cli` — defined; importable via `python3 -c "import scaffold_dispatch; assert hasattr(scaffold_dispatch, 'scaffold_cli')"` (PASS)
- `scaffold_dispatch._sanitize_module_name` — defined; pure str.replace
- `scaffold_dispatch._CLI_STARTER` — defined; 2 references
- `scaffold_dispatch._PLAYBOOK_DISPATCH` — `"cli": scaffold_cli` entry present (line 451)

Negative assertions:
- `grep -c 'typer\[all\]' assets/cli-starter/pyproject.snippet.toml` → 0
- `grep -c 'typer\[all\]' references/playbooks/cli.md` → 0

Tests:
- `uv run pytest scripts/tests/test_phase07_cli.py` → 5/5 PASSED
- `uv run pytest scripts/tests/test_scaffold_dispatch.py scripts/tests/test_phase07_ai_service.py` → 13/13 PASSED (no regression)
- `uv run pytest scripts/tests/` → 171 passed, 1 pre-existing skip, 0 failures (was 166; +5 new tests)

Commits:
- `1728b16` (test RED) — FOUND in `git log`
- `9b5d6a5` (feat GREEN) — FOUND in `git log`

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
