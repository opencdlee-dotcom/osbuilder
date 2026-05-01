---
phase: 6
slug: ship-to-private-github-scalable-defaults
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-01
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source of truth for the test map: `06-RESEARCH.md` § Validation Architecture (lines 742–847).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (Python 3.13 stdlib + pytest only — no new deps; matches Phase 4/5) |
| **Config file** | `pyproject.toml` (existing — Phase 1) |
| **Quick run command** | `python3 -m pytest scripts/tests/ -x --tb=short -q` |
| **Full suite command** | `python3 -m pytest scripts/tests/ --tb=short -q` |
| **Estimated runtime** | ~15 seconds (quick, all phases) — Phase 6 adds ~12–18 tests on top of Phase 5's 127 |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest scripts/tests/ -x --tb=short -q`
- **After every plan wave:** Run `python3 -m pytest scripts/tests/ --tb=short -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

> Plan/Wave/Task IDs are stamped during planning. Each row pre-binds a requirement → test command so the planner can drop these directly into task `<acceptance_criteria>` and `<automated>` blocks.

| Test ID | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|-------------|-----------|-------------------|-------------|--------|
| V-01 | SHIP-01 | unit (mock subprocess) | `pytest scripts/tests/test_gh_handoff.py::test_ship_runs_private_create -x` | ❌ W0 | ⬜ pending |
| V-02 | SHIP-01 | unit (failure modes) | `pytest scripts/tests/test_gh_handoff.py::test_failure_modes_friendly -x` | ❌ W0 | ⬜ pending |
| V-03 | SHIP-02 | unit (template stamp) | `pytest scripts/tests/test_runbook_writer.py -x` | ❌ W0 | ⬜ pending |
| V-04 | SHIP-02 | **manual UAT** | n/a (5-min stranger-clone — see Manual-Only) | n/a | ⬜ manual |
| V-05 | SHIP-03 | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_gitignore_composition -x` | ❌ W0 | ⬜ pending |
| V-06 | SHIP-04 | unit (file content) | `pytest scripts/tests/test_scaffold_extensions.py::test_gitleaks_config -x` | ❌ W0 | ⬜ pending |
| V-07 | SHIP-04 | integration (real pre-commit + gitleaks; skipif) | `pytest scripts/tests/test_scaffold_extensions.py::test_gitleaks_blocks_real_secret -x` | ❌ W0 | ⬜ pending |
| V-08 | SHIP-05 | unit (mock `gh auth status` exit 1) | `pytest scripts/tests/test_gh_handoff.py::test_auth_drift_friendly -x` | ❌ W0 | ⬜ pending |
| V-09 | SCL-01 | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_env_example_committed -x` | ❌ W0 | ⬜ pending |
| V-10 | SCL-02 | unit (pure function) | `pytest scripts/tests/test_scaffold_extensions.py::test_pick_database -x` | ❌ W0 | ⬜ pending |
| V-11 | SCL-02 | unit (file presence + content per playbook) | `pytest scripts/tests/test_scaffold_extensions.py::test_db_default_per_playbook -x` | ❌ W0 | ⬜ pending |
| V-12 | SCL-03 | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_docker_artifacts -x` | ❌ W0 | ⬜ pending |
| V-13 | SCL-04 | unit (exactly one workflow file) | `pytest scripts/tests/test_scaffold_extensions.py::test_one_ci_workflow -x` | ❌ W0 | ⬜ pending |
| V-14 | SCL-05 | unit (refusal + state.md write + early return) | `pytest scripts/tests/test_refusal.py::test_kubernetes_refused -x` | ❌ W0 | ⬜ pending |
| V-15 | SCL-05 | unit (refusal copy mentions opt-in) | `pytest scripts/tests/test_refusal.py::test_refusal_copy_mentions_opt_in -x` | ❌ W0 | ⬜ pending |
| V-16 | SCL-06 | unit (slash-command emission count) | `pytest scripts/tests/test_production_ready.py::test_emits_seven_phases -x` | ❌ W0 | ⬜ pending |
| V-17 | SCL-06 | unit (no emit when default) | `pytest scripts/tests/test_production_ready.py::test_no_emit_when_default -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

> **Sampling continuity check:** No requirement has more than 2 consecutive untested gaps; SHIP-04 has both unit (V-06) and integration (V-07) coverage; all 11 phase requirements have at least one automated row except SHIP-02 which has V-03 (automated) **and** V-04 (manual-only — see below).

---

## Wave 0 Requirements

The planner MUST schedule a Wave 0 plan that lands the following RED stubs and shared fixtures BEFORE any Wave 1 implementation. These files do not exist today.

- [ ] `scripts/tests/test_gh_handoff.py` — RED stubs for SHIP-01, SHIP-05 (V-01, V-02, V-08)
- [ ] `scripts/tests/test_runbook_writer.py` — RED stub for SHIP-02 (V-03)
- [ ] `scripts/tests/test_scaffold_extensions.py` — RED stubs for SHIP-03, SHIP-04 unit, SCL-01..04 (V-05, V-06, V-09..V-13)
- [ ] `scripts/tests/test_scaffold_extensions.py::test_gitleaks_blocks_real_secret` — RED integration stub for SHIP-04 (V-07; `skipif` if `pre-commit`/`gitleaks` absent)
- [ ] `scripts/tests/test_refusal.py` — RED stubs for SCL-05 (V-14, V-15)
- [ ] `scripts/tests/test_production_ready.py` — RED stubs for SCL-06 (V-16, V-17)
- [ ] `scripts/tests/conftest.py` — extend with: `fake_built_app(tmp_path)`, `fake_state_md` factory, `mock_gh_subprocess` (5 canned failure modes), `mock_git_subprocess` (clean / dirty / no-init)
- [ ] `scripts/tests/fixtures/derived_spec_with_k8s.md` — refusal positive fixture
- [ ] `scripts/tests/fixtures/derived_spec_clean.md` — refusal negative fixture
- [ ] `scripts/state_writer.py` — extend `ALLOWED_FIELDS` with: `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`, `production_ready` (additive — do NOT add to `REQUIRED_FIELDS`; matches Phase 3/4/5 pattern)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stranger clones the resulting repo on a fresh machine and reaches a working app on `localhost` in ≤ 5 min via README | SHIP-02 (success criterion #2) | "Stranger" + "fresh machine" + "5 min" cannot be deterministically automated; UAT row | After E2E build, on a SECOND machine (or `docker run -it ubuntu` clean container with prerequisites): `gh repo clone <user/repo>; cd <repo>; cat README.md; <follow runbook verbatim>; verify localhost shows working homepage`. Time the run end-to-end. |
| End-to-end refusal of "set up Kubernetes" produces a friendly explanation pointing to `--production-ready` | SCL-05 (success criterion #5) | Default-mode refusal copy is human-judged for friendliness | Submit a spec containing "build me a TODO app with Kubernetes orchestration"; verify state.md `last_failure` matches refusal pattern; verify copy from `references/refuse-list.md` is shown to user; verify offering `--production-ready` is explicit. |
| `--production-ready` adds K8s as a NAMED PHASE in `.planning/ROADMAP.md`, NOT as scaffold code | SCL-06 (success criterion #5) | "Named phase row" content quality is human-judged | Submit same Kubernetes spec with `--production-ready`; verify `.planning/ROADMAP.md` gains rows for: observability, migrations, healthchecks, secret manager, Sentry, rate limiting, backup; verify NO k8s manifest / Helm chart files appear in user's project_path. |

---

## Test Harness Notes

- **SHIP-01 / SHIP-05 mocking strategy:** Mock `subprocess.run` for `gh ...` calls; assert command list contains `--private`. Real-network tests deferred to manual UAT (or opt-in `pytest -m live_gh` marker, default-skipped).
- **SHIP-04 integration test:** Uses real `pre-commit` + `gitleaks` in a tmp git repo. Gated by `@pytest.mark.skipif(shutil.which("pre-commit") is None or shutil.which("gitleaks") is None, ...)` — see `06-RESEARCH.md` § Test Harness Strategy for the full pattern.
- **`fake_built_app` fixture:** A `tmp_path`-rooted directory tree representing what `scaffold_dispatch.py` would produce. Used by all `test_scaffold_extensions.py::*` tests so they don't need a real build run.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s (target met)
- [ ] `nyquist_compliant: true` set in frontmatter (planner sets this when all V-IDs are bound to tasks)

**Approval:** pending
