---
phase: 3
slug: intake-stack-research-web-playbook-one-playbook-e2e
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-30
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python3 -m pytest scripts/tests/ -x --tb=short` |
| **Full suite command** | `python3 -m pytest scripts/tests/ --tb=short` |
| **Estimated runtime** | ~5 seconds (unit tests only; no subprocess side-effects) |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest scripts/tests/ -x --tb=short`
- **After every plan wave:** Run `python3 -m pytest scripts/tests/ --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green (≥ 46 tests collected)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | IN-01..05, RES-01..04, SCAF-01, SCAF-06 | T-3-01 | Path traversal blocked in project_name; shell=False | unit | `python3 -m pytest scripts/tests/test_intake.py scripts/tests/test_stack_researcher.py scripts/tests/test_scaffold_dispatch.py --collect-only` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | IN-01 | — | N/A | unit | `pytest scripts/tests/test_intake.py::test_paragraph_to_derived_spec -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | IN-02 | — | N/A | unit | `pytest scripts/tests/test_intake.py::test_structured_spec_to_derived_spec -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | IN-03 | — | N/A | unit | `pytest scripts/tests/test_intake.py::test_questions_have_no_jargon -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 1 | IN-04 | — | N/A | unit | `pytest scripts/tests/test_intake.py::test_questions_have_you_decide_option -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 1 | IN-05 | — | derived_spec.md contains no secrets | unit | `pytest scripts/tests/test_intake.py::test_derived_spec_format -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | RES-01 | — | N/A | unit | `pytest scripts/tests/test_stack_researcher.py::test_calls_brainiac -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 1 | RES-02 | — | N/A | unit | `pytest scripts/tests/test_stack_researcher.py::test_output_is_structured -x` | ❌ W0 | ⬜ pending |
| 3-03-03 | 03 | 1 | RES-03 | — | N/A | unit | `pytest scripts/tests/test_stack_researcher.py::test_fallback_to_stack_menu -x` | ❌ W0 | ⬜ pending |
| 3-03-04 | 03 | 1 | RES-04 | — | N/A | unit | `pytest scripts/tests/test_stack_researcher.py::test_advanced_override -x` | ❌ W0 | ⬜ pending |
| 3-04-01 | 04 | 2 | SCAF-01 | — | N/A | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_web_playbook_exists -x` | ❌ W0 | ⬜ pending |
| 3-04-02 | 04 | 2 | SCAF-06 | T-3-01 | project_name validated [a-zA-Z0-9_-]; subprocess list form (no shell=True) | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_scaffold_cmd_flags -x` | ❌ W0 | ⬜ pending |
| 3-04-03 | 04 | 2 | SCAF-06 | — | N/A | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_drizzle_deps_added -x` | ❌ W0 | ⬜ pending |
| 3-04-04 | 04 | 2 | SCAF-06 | — | N/A | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_db_ts_written -x` | ❌ W0 | ⬜ pending |
| 3-04-05 | 04 | 2 | SCAF-06 | — | N/A | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_drizzle_config_written -x` | ❌ W0 | ⬜ pending |
| 3-04-06 | 04 | 2 | SCAF-06 | — | .env.example has no real secrets | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_env_example_written -x` | ❌ W0 | ⬜ pending |
| 3-04-07 | 04 | 2 | SCAF-06 | — | compose.yaml filename (not docker-compose.yml) | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_compose_yaml_written -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/tests/test_intake.py` — 5 RED stubs covering IN-01..IN-05
- [ ] `scripts/tests/test_stack_researcher.py` — 4 RED stubs covering RES-01..RES-04
- [ ] `scripts/tests/test_scaffold_dispatch.py` — 7 RED stubs covering SCAF-01, SCAF-06

Total new tests Wave 0 must drop: ≥ 16 RED stubs (brings collected total from 30 to ≥ 46)

Existing infrastructure covers pytest config and FakeShell/fake_which fixtures (conftest.py) — no new framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `pnpm install && pnpm dev` boots scaffolded project on localhost:3000 | SCAF-06 (SC 5) | Requires real pnpm install + running Next.js server + Docker for Postgres; not a unit test | Run `cd <scaffolded-project> && pnpm install && pnpm dev`; verify browser shows Next.js homepage on localhost:3000 |
| E2E paragraph → working project in ≤ 60 seconds (excluding pnpm install) | Phase 3 SC 7 | Wall-clock measurement across full flow; requires real brainiac + scaffold run | Measure with `time` from paragraph input to `scaffold_dispatch.py` completion (exclude `pnpm install` download) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (16 new test stubs)
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
