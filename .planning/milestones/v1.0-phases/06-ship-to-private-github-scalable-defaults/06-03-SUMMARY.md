---
phase: 06-ship-to-private-github-scalable-defaults
plan: "03"
subsystem: scaffold-dispatch-extensions
tags: [tdd, scaffold, docker, ci, database-choice, scalable-defaults]
dependency_graph:
  requires: ["06-01", "06-02"]
  provides: ["_pick_database", "_write_dockerfile", "_write_ci_workflow", "compose-gated-on-db-choice"]
  affects: ["scripts/scaffold_dispatch.py", "assets/dockerfiles", "assets/ci-workflows"]
tech_stack:
  added: ["assets/dockerfiles/node-pnpm.Dockerfile.tmpl", "assets/dockerfiles/python-uv.Dockerfile.tmpl", "assets/ci-workflows/node.yml.tmpl", "assets/ci-workflows/python.yml.tmpl"]
  patterns: ["multi-stage-dockerfile", "pull-request-ci", "pure-function-db-choice", "asset-template-read"]
key_files:
  created:
    - assets/dockerfiles/node-pnpm.Dockerfile.tmpl
    - assets/dockerfiles/python-uv.Dockerfile.tmpl
    - assets/ci-workflows/node.yml.tmpl
    - assets/ci-workflows/python.yml.tmpl
  modified:
    - scripts/scaffold_dispatch.py
    - scripts/tests/test_scaffold_extensions.py
decisions:
  - "ASSETS constant resolves to <repo>/assets via Path(__file__).resolve().parent.parent/assets — no env var needed"
  - "write_drizzle_files default db_choice='postgres' preserves backwards compatibility with all Phase 3 tests"
  - "_write_dockerfile and _write_ci_workflow silently no-op when template file is missing — safe for future playbooks"
  - "scaffold_web uses hardcoded ('web','multi-user-web') args to _pick_database — intrinsic to function name, no state coupling"
metrics:
  duration_seconds: 195
  completed_date: "2026-05-01"
  tasks_completed: 2
  files_changed: 6
---

# Phase 06 Plan 03: Scaffold Extensions — _pick_database + Dockerfile + CI Workflow Summary

**One-liner:** Multi-stage Dockerfile + GitHub Actions CI workflow + Postgres-vs-SQLite pure-function choice wired into scaffold_web(), with compose.yaml gated on db_choice.

## What Was Built

Extended `scripts/scaffold_dispatch.py` with three new helpers and fixed the unconditional `compose.yaml` write bug:

1. **`_pick_database(playbook, app_type) -> str`** — Pure function. Returns `"postgres"` for web/ai-service playbooks, `"sqlite"` for cli. Testable with no I/O.
2. **`_write_dockerfile(project_dir, stack_family)`** — Reads `assets/dockerfiles/<family>.Dockerfile.tmpl`, writes `Dockerfile` via `atomic_write`. No-ops gracefully if template is missing.
3. **`_write_ci_workflow(project_dir, stack_family)`** — Reads `assets/ci-workflows/<family>.yml.tmpl`, writes `.github/workflows/ci.yml` via `atomic_write`.
4. **`write_drizzle_files` fix** — Added `db_choice: str = "postgres"` keyword-only arg; `compose.yaml` write is now gated on `db_choice == "postgres"`. Default preserves Phase 3 backwards compatibility.
5. **`scaffold_web()` wiring** — Added three Phase 6 calls after the existing `write_drizzle_files()` boundary: `_pick_database` → `write_drizzle_files(db_choice=...)` → `_write_dockerfile` → `_write_ci_workflow`.

Four asset template files created:
- `assets/dockerfiles/node-pnpm.Dockerfile.tmpl` — Node 20-alpine multi-stage (AS builder + AS runtime, pnpm 10.33.2 via corepack)
- `assets/dockerfiles/python-uv.Dockerfile.tmpl` — python:3.13-slim multi-stage with uv
- `assets/ci-workflows/node.yml.tmpl` — PR-triggered CI; `pnpm/action-setup@v4` BEFORE `actions/setup-node@v4` (cache engagement order, T-06-03-05)
- `assets/ci-workflows/python.yml.tmpl` — PR-triggered CI with `setup-python@v6` + `astral-sh/setup-uv@v6`

## TDD Gate Compliance

- **RED gate commit:** `a8ae753` — `test(06-03): add RED stubs for SCL-01..04 (V-09..V-13)` — 5 tests failing as expected
- **GREEN gate commit:** `424d376` — `feat(06-03): add _pick_database, _write_dockerfile, _write_ci_workflow + 4 asset templates` — all 5 tests passing
- REFACTOR gate: no structural cleanup needed; code was clean on first pass.

## Test Results

| Test | V-ID | Before | After |
|------|------|--------|-------|
| test_env_example_committed | V-09 | SKIP | GREEN |
| test_pick_database | V-10 | SKIP | GREEN |
| test_db_default_per_playbook | V-11 | SKIP | GREEN |
| test_docker_artifacts | V-12 | SKIP | GREEN |
| test_one_ci_workflow | V-13 | SKIP | GREEN |
| Full suite | — | 132 passed, 12 skip | 137 passed, 7 skip |

## Deviations from Plan

None — plan executed exactly as written. All steps from the `<implementation>` section were applied verbatim: ASSETS constant placement, function signatures, `write_drizzle_files` kwarg default, `scaffold_web()` wiring location.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced. Asset templates contain no secrets (T-06-03-03 accepted). Path construction uses literal `stack_family` values from `scaffold_web()`, not user-supplied input (T-06-03-01 mitigated). `_COMPOSE_YAML` contains no `version:` key (T-06-03-02 verified by test assertion and direct grep).

## Self-Check: PASSED
