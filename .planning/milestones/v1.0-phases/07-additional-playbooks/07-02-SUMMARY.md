---
phase: 07-additional-playbooks
plan: 02
subsystem: scaffold
tags: [ai-service, fastapi, uv, pydantic, scaffold, preflight, dockerfile, friendly-errors, phase-7]

# Dependency graph
requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    provides: scaffold_dispatch.py shape, _validate_project_name, atomic_write, _pick_database
  - phase: 06-ship-to-private-github-scalable-defaults
    provides: _write_dockerfile/_write_ci_workflow stack-family helpers, ASSETS constant
  - phase: 07-additional-playbooks-plan-01
    provides: app_type='ai-service' routing from intake (PLAYBOOK_KEYWORDS)
provides:
  - "scaffold_ai_service(project_name, project_root) → uv init --app + uv add 'fastapi[standard]' + main.py + Dockerfile + CI"
  - "ensure_uv() helper (mirrors ensure_pnpm; Windows aborts to preflight per T-07-02-06)"
  - "_PLAYBOOK_DISPATCH dict — first multi-playbook routing surface in scaffold_dispatch.py"
  - "_PLAYBOOK_TOOLS dict in preflight (per-playbook lazy install lookup; ai-service/cli/desktop entries)"
  - "uv install matrix entries for macOS/APT/DNF (curl-pipe-sh) + winget (astral-sh.uv)"
  - "references/playbooks/ai-service.md — 56-line spec mirroring web.md's 7-section structure"
  - "assets/fastapi-starter/{main.py, pyproject.snippet.toml, README.md} — vendored FastAPI starter"
  - "assets/dockerfiles/python-uv.Dockerfile.tmpl retargeted to ai-service (fastapi run entrypoint)"
  - "references/friendly-errors/dictionary.yaml — +2 entries (uv-not-installed, fastapi-cli-missing)"
  - "references/stack-menu.md — +ai-service playbook defaults table"
affects:
  - 07-03-cli-playbook (will reuse ensure_uv + _PLAYBOOK_TOOLS lookup)
  - 07-04-desktop-playbook (will extend _PLAYBOOK_TOOLS desktop entry with cargo)
  - 07-05-hub-platform-playbook (cross-references ai-service.md)
  - 07-06-e2e-harness (parametrizes ai-service path)

# Tech tracking
tech-stack:
  added:
    - "fastapi 0.136.1 (transitive uvicorn 0.46.0, fastapi-cli; via [standard] extra)"
    - "pydantic 2.13.3 (v2-native; BaseModel + Field; transitive of fastapi[standard])"
    - "uv 0.11.8 (Astral all-in-one for Python; preflight install via curl-pipe-sh on Unix, winget astral-sh.uv on Windows)"
  patterns:
    - "Per-playbook scaffold function mirrors scaffold_web 4-step shape verbatim (validate → ensure_<tool> → subprocess.run → atomic_write)"
    - "_PLAYBOOK_DISPATCH dict for playbook routing (extension point for 07-03/04/05)"
    - "_PLAYBOOK_TOOLS dict in preflight — lazy install (only when playbook selected); separate from REQUIRED_TOOLS"
    - "Vendored starter assets/<framework>-starter/ — pattern carries forward to cli (Typer) + desktop (Tauri)"
    - "Multi-stage Dockerfile per stack-family (node-pnpm vs python-uv); CMD parameterised per playbook"

key-files:
  created:
    - scripts/tests/test_phase07_ai_service.py (180 lines, 6 tests)
    - scripts/tests/test_phase07_preflight_extensions.py (89 lines, 3 tests; cargo will extend in 07-04)
    - assets/fastapi-starter/main.py (55 lines; verbatim RESEARCH.md Code Example 1)
    - assets/fastapi-starter/pyproject.snippet.toml (8 lines)
    - assets/fastapi-starter/README.md (40 lines)
    - references/playbooks/ai-service.md (56 lines; under 80 cap)
  modified:
    - scripts/scaffold_dispatch.py (+78 lines: _FASTAPI_STARTER constant, ensure_uv, scaffold_ai_service, _PLAYBOOK_DISPATCH, _cmd_scaffold dispatches)
    - scripts/preflight_check.py (+33 lines: _PLAYBOOK_TOOLS dict + 4 install matrix entries)
    - references/friendly-errors/dictionary.yaml (+22 lines: uv-not-installed + fastapi-cli-missing)
    - references/stack-menu.md (+9 lines: ai-service defaults table + cross-ref bullet)
    - assets/dockerfiles/python-uv.Dockerfile.tmpl (retargeted from python -m app placeholder to fastapi run main.py; uses ghcr.io/astral-sh/uv:python3.13-bookworm-slim base)

key-decisions:
  - "D-10 implemented: scaffold_ai_service runs uv init --app then uv add 'fastapi[standard]' (single-element argv preserves brackets per Pitfall 2)"
  - "D-11 implemented: /summarize stub returns text[:200]; no API key required to boot; ANTHROPIC_API_KEY wire-up documented in main.py docstring only"
  - "D-12 implemented: Pydantic v2-native (BaseModel + Field; tests assert NO @validator, NO class Config:)"
  - "D-20 implemented: preflight gains uv install action (auto-install with single confirmation via existing apply() flow); scaffold-time ensure_uv is the fallback safety net"
  - "D-21 corrected: winget package ID is 'astral-sh.uv' (lowercase, hyphenated namespace) — RESEARCH.md flagged the original 'Astral.UV' as a typo; tests assert exact lowercase form and that the typo string is absent"
  - "T-07-02-06 mitigated: ensure_uv aborts on Windows pointing to preflight (winget needs admin/UAC; not safe from a scaffold call)"
  - "_PLAYBOOK_DISPATCH dict introduced — single-playbook dispatch in 03 is now multi-playbook routing; scales cleanly for 07-03/04/05"
  - "Dockerfile decision: previously dormant python-uv.Dockerfile.tmpl (Phase 6, IN-10 TODO) is now retargeted to ai-service. Phase 7 cli playbook will need its own python-uv-cli template (per IN-10 note); deferred to 07-03"

patterns-established:
  - "Per-plan atomic block in scaffold_dispatch.py via '=== Phase 7 — ai-service playbook (07-02) ===' divider — RESEARCH.md Wave Coordination Option A"
  - "Single-element argv for bracket-bearing tokens (\"fastapi[standard]\") — quoting is meaningless when shell=False; one-string token is the ONLY safe way (Pitfall 2)"
  - "Lazy-import-via-fixture pattern carries to phase 7 plan tests (test_phase07_ai_service.py + test_phase07_preflight_extensions.py); has_ai_service guard fixture handles 'Wave 1 not yet landed' gracefully"
  - "Stack-family Dockerfile templates — node-pnpm (web), python-uv (ai-service), to be extended in 07-03 (python-uv-cli) and 07-04 (rust for Tauri)"

requirements-completed: [SCAF-02]

# Metrics
duration: 12min
completed: 2026-05-02
---

# Phase 7 Plan 02: AI-Service Playbook Summary

**Added the ai-service playbook to OSBuilder: a FastAPI + uv + Pydantic v2 scaffold path that turns "an HTTP API that summarizes documents with an LLM" into a working `uv run fastapi dev` server with `/`, `/health`, automatic `/docs`, and a `/summarize` POST stub — no API key required to boot.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-02T08:14Z (after 07-01 completion)
- **Completed:** 2026-05-02
- **Tasks:** 2 (Wave 0 RED tests + Wave 1 GREEN implementation)
- **Files:** 9 (4 created, 5 modified) + 2 test files (created)

## Accomplishments

- `scaffold_ai_service` mirrors `scaffold_web`'s 4-step shape verbatim: validate → ensure_uv → uv init --app → uv add `fastapi[standard]` → atomic_write of vendored main.py + Dockerfile + CI workflow.
- Pydantic v2-native vendored starter (`assets/fastapi-starter/main.py`) — 55 lines, matches RESEARCH.md Code Example 1 byte-for-byte. Pitfall 4 (`@validator` / `class Config:` v1 markers) ruled out by AST-grep tests.
- Preflight extended with **uv** detection + cross-platform install actions (macOS/Linux: curl-pipe-sh; Windows: winget `astral-sh.uv` — RESEARCH.md typo correction of D-21 'Astral.UV'). The lazy `_PLAYBOOK_TOOLS` dict means uv only joins the install plan when an ai-service / cli / desktop playbook is in play.
- Dormant Phase-6 `python-uv.Dockerfile.tmpl` (carrying an `IN-10` TODO since 06-01) gets its first real consumer here — retargeted to use the official Astral uv image (`ghcr.io/astral-sh/uv:python3.13-bookworm-slim`) and `fastapi run main.py` as the production CMD.
- Multi-playbook dispatch in `scaffold_dispatch.py` now exists as `_PLAYBOOK_DISPATCH` — a clean extension point that 07-03 (cli), 07-04 (desktop), and 07-05 (hub-platform) will plug into.
- 9/9 plan tests GREEN; 166/166 full suite passes (1 pre-existing skip; zero regressions in `test_scaffold_dispatch.py` or `test_preflight.py`).

## Task Commits

Each task committed atomically:

1. **Task 1: Wave 0 RED stubs (ai-service + preflight uv extensions)** — `98e9914` (test)
2. **Task 2: Wave 1 GREEN — scaffold_ai_service + ensure_uv + uv preflight + fastapi-starter assets + ai-service.md + dictionary entries + Dockerfile retarget** — `eecde34` (feat)

## Files Created/Modified

### Created

- `scripts/tests/test_phase07_ai_service.py` (180 lines) — 6 tests: playbook .md sections, fastapi-starter presence + Pydantic v2 shape (NO @validator, NO class Config:), scaffold_ai_service subprocess argv shape (uv init --app + uv add fastapi[standard]), post-scaffold artifacts (main.py byte-for-byte match, Dockerfile non-empty).
- `scripts/tests/test_phase07_preflight_extensions.py` (89 lines) — 3 uv-portion tests; cargo portion deferred to 07-04 (will extend this same file additively).
- `assets/fastapi-starter/main.py` (55 lines) — vendored Pydantic v2 starter; routes /, /health, /summarize stub; ANTHROPIC_API_KEY wire-up shown in `summarize()` docstring only.
- `assets/fastapi-starter/pyproject.snippet.toml` (8 lines) — reference-only deps snippet (`uv add` is the actual install path).
- `assets/fastapi-starter/README.md` (40 lines) — user-facing primer; `uv sync && uv run fastapi dev` quickstart; production wiring (`fastapi run`) noted.
- `references/playbooks/ai-service.md` (56 lines, under 80 cap) — 7-section spec mirroring web.md.

### Modified

- `scripts/scaffold_dispatch.py` (+78 lines, -2 lines) — added `_FASTAPI_STARTER` path constant, `ensure_uv()`, `scaffold_ai_service()`, `_PLAYBOOK_DISPATCH` dict, and rewired `_cmd_scaffold` to dispatch by `--playbook` arg.
- `scripts/preflight_check.py` (+33 lines) — `_PLAYBOOK_TOOLS` dict; `_MACOS_INSTALL["uv"]`, `_APT_INSTALL["uv"]`, `_DNF_INSTALL["uv"]` (curl-pipe-sh installer), `_WINGET_INSTALL["uv"]` (`astral-sh.uv` lowercase namespace).
- `references/friendly-errors/dictionary.yaml` (+22 lines) — `uv-not-installed` (preflight category) + `fastapi-cli-missing` (scaffold category, points users at `uv add 'fastapi[standard]'`).
- `references/stack-menu.md` (+9 lines) — `## ai-service playbook defaults` table + cross-ref bullet to ai-service.md in the See-also section.
- `assets/dockerfiles/python-uv.Dockerfile.tmpl` (-7 lines, +14 lines net) — retargeted from placeholder `python -m app` CMD to `fastapi run main.py --host 0.0.0.0 --port 8000`; switched base from `python:3.13-slim` + `pip install uv` to the official `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` builder image.

## Decisions Made

- **Dockerfile retarget vs new file** — the existing `python-uv.Dockerfile.tmpl` carried an `IN-10` TODO since Phase 6 marking it dormant pending Phase 7. The plan asked to "create" the file, but it already existed as a placeholder. Decision: retarget the placeholder rather than create a parallel file. Phase 7 cli playbook (07-03) will need its own `python-uv-cli.Dockerfile.tmpl` per the IN-10 note (different CMD: `python -m mycli` vs `fastapi run main.py`); that fork is deferred to 07-03.
- **`_PLAYBOOK_DISPATCH` dict timing** — introduced now (not deferred to 07-03 when there are 3+ playbooks) because (a) the `--playbook ai-service` arg path needs a dispatch surface anyway, and (b) it's cheaper to add a dict with 2 entries than retrofit into `if/elif` chain later. Cli/desktop/hub-platform plans plug in additively.
- **Preflight uv entries written declaratively at module scope** — chose direct `_MACOS_INSTALL["uv"] = (...)` assignment after the matrix dict declarations rather than rebuilding the dicts. This preserves diff-readability (the change is purely additive) and matches the existing `_PLAYBOOK_TOOLS` pattern style. Trade-off: the four matrices are no longer single literal expressions — but readability wins here.
- **`fastapi[standard]` quoting** — the test asserts the bracket-token travels as a single argv element (`"fastapi[standard]"`). Pitfall 2 in RESEARCH.md is explicit: when `shell=False`, single quotes in the source are syntactic noise; what matters is whether the brackets are split across argv tokens. The implementation passes `["uv", "add", "fastapi[standard]"]` (3 elements) and the test verifies it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] python-uv.Dockerfile.tmpl already existed**
- **Found during:** Task 2 step 2d (`ls assets/dockerfiles/`)
- **Issue:** Plan said "Create assets/dockerfiles/python-uv.Dockerfile.tmpl" with verbatim content; the file already existed from Phase 6 (06-01) as a dormant placeholder with `python -m app` CMD and an explicit `IN-10 / TODO(phase-7)` comment block.
- **Fix:** Retargeted the existing template per the plan's verbatim content. Preserved the IN-10 reference (now noting that cli playbook fork will happen in 07-03).
- **Files modified:** `assets/dockerfiles/python-uv.Dockerfile.tmpl`
- **Committed in:** `eecde34`

**2. [Rule 3 — Blocking] `Astral.UV` typo string in inline comment failed `grep -c 'Astral.UV' returns 0` acceptance criterion**
- **Found during:** Task 2 acceptance verification
- **Issue:** The plan's acceptance criterion `grep -c "Astral.UV" scripts/preflight_check.py returns 0` was tripped by a docstring/comment that referenced "Astral.UV" as the typo to avoid — the comment itself contained the literal string. The test file's negative assertion still works (it scans for `Astral.UV` in the joined argv only), but the plan-level grep is unconditional.
- **Fix:** Rephrased the comment to "an old PascalCase spelling" rather than embedding the literal typo string.
- **Files modified:** `scripts/preflight_check.py`
- **Verification:** `grep -c "Astral.UV" scripts/preflight_check.py` → 0; `grep -c "astral-sh.uv" scripts/preflight_check.py` → 3.
- **Committed in:** `eecde34`

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking the acceptance criteria themselves). No scope creep; no architectural change.

## Issues Encountered

None blocking. Both deviations above were caught at verification time and fixed before committing.

## Threat Flags

None new beyond the plan's `<threat_model>` register. T-07-02-01..06 disposition unchanged:
- T-07-02-01 (Tampering: project_name → uv argv): mitigated by reused `_validate_project_name` regex.
- T-07-02-02 (InfoDisclosure: /summarize stub): accepted — stub doesn't log or call out (D-11 contract).
- T-07-02-03 (Tampering: curl-pipe-sh trust): accepted under same Phase 2 trust model.
- T-07-02-04 (DoS: oversized text): mitigated by `Field(max_length=100_000)`.
- T-07-02-05 (Spoofing: winget ID typo): mitigated by `test_uv_winget_id_exact` regression catcher.
- T-07-02-06 (EoP: Windows admin during install): mitigated by `ensure_uv` Windows abort to preflight.

No new attack surface beyond what the plan anticipated.

## User Setup Required

None at scaffold time. End-user wiring of a real LLM provider (post-scaffold, optional):
1. `cd <project-name>`
2. `uv add anthropic`
3. `export ANTHROPIC_API_KEY=...` in their shell or `.env`
4. Replace `summarize()` body in `main.py` per the docstring example.

This is documented in both `assets/fastapi-starter/main.py` (docstring) and `assets/fastapi-starter/README.md` (## Wiring a real LLM section).

## Next Phase Readiness

- **07-03 (cli playbook)** — unblocked. Will reuse `ensure_uv` + `_PLAYBOOK_TOOLS["cli"]` lookup; adds its own `assets/cli-starter/__main__.py.tmpl` + `python-uv-cli.Dockerfile.tmpl` (per IN-10 deferred fork); plugs `scaffold_cli` into `_PLAYBOOK_DISPATCH`.
- **07-04 (desktop playbook)** — unblocked. Will additively extend `_PLAYBOOK_TOOLS["desktop"]` (already populated with `("uv", "cargo")`) and `test_phase07_preflight_extensions.py` (cargo tests).
- **07-05 (hub-platform)** — unblocked. Cross-references `ai-service.md` for the FastAPI runtime.
- **07-06 (e2e harness)** — unblocked. Parametrized E2E can spin up an ai-service intake → scaffold → boot loop using the now-real `app_type='ai-service'` route from 07-01 and the now-real `scaffold_ai_service` from this plan.

## Self-Check: PASSED

Files:
- `references/playbooks/ai-service.md` — FOUND (56 lines, ≤ 80 cap; 7 mandatory sections present)
- `assets/fastapi-starter/main.py` — FOUND (55 lines; FastAPI + Pydantic v2; NO @validator, NO class Config:)
- `assets/fastapi-starter/pyproject.snippet.toml` — FOUND (contains `fastapi[standard]`)
- `assets/fastapi-starter/README.md` — FOUND (mentions `uv run fastapi dev`)
- `assets/dockerfiles/python-uv.Dockerfile.tmpl` — FOUND (retargeted; `astral-sh/uv` base image; `fastapi run` CMD)
- `scripts/tests/test_phase07_ai_service.py` — FOUND (6 tests)
- `scripts/tests/test_phase07_preflight_extensions.py` — FOUND (3 tests)

Code surface:
- `scaffold_dispatch.scaffold_ai_service` — defined; importable
- `scaffold_dispatch.ensure_uv` — defined
- `scaffold_dispatch._FASTAPI_STARTER` — defined; 2 references
- `scaffold_dispatch._PLAYBOOK_DISPATCH` — defined with `web` + `ai-service` entries
- `preflight_check._PLAYBOOK_TOOLS` — defined with `ai-service`/`cli`/`desktop`/`hub-platform` keys
- `preflight_check._MACOS_INSTALL["uv"]` / `_APT_INSTALL["uv"]` / `_DNF_INSTALL["uv"]` / `_WINGET_INSTALL["uv"]` — all defined; winget ID exact `astral-sh.uv`; Unix uses curl-pipe-sh

Negative assertions:
- `grep -c "Astral.UV" scripts/preflight_check.py` → 0 (typo never appears literally)
- `grep -c "@validator" assets/fastapi-starter/main.py` → 0 (Pydantic v2)
- `grep -c "class Config:" assets/fastapi-starter/main.py` → 0 (Pydantic v2)

Tests:
- `uv run pytest scripts/tests/test_phase07_ai_service.py scripts/tests/test_phase07_preflight_extensions.py` → 9/9 PASSED
- `uv run pytest scripts/tests/test_scaffold_dispatch.py scripts/tests/test_preflight.py` → 20/20 PASSED (no regression)
- `uv run pytest scripts/tests/` → 166 passed, 1 pre-existing skip, 0 failures

Commits:
- `98e9914` (test RED) — FOUND in `git log`
- `eecde34` (feat GREEN) — FOUND in `git log`

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
