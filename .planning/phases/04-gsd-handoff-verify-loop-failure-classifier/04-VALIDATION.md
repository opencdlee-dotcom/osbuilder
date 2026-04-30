---
phase: 4
slug: gsd-handoff-verify-loop-failure-classifier
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-30
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/test_gsd_driver.py tests/test_failure_classifier.py tests/test_registry_verify.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_gsd_driver.py tests/test_failure_classifier.py tests/test_registry_verify.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 0 | ROLE-01 | — | N/A | unit | `python -m pytest tests/test_gsd_driver.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 0 | HEAL-01 | — | N/A | unit | `python -m pytest tests/test_failure_classifier.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 0 | HEAL-05 | — | N/A | unit | `python -m pytest tests/test_registry_verify.py -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | ROLE-01 | — | gsd_driver emits skill commands as text, not subprocess | unit | `python -m pytest tests/test_gsd_driver.py::test_emits_gsd_new_project -x -q` | ✅ | ⬜ pending |
| 4-02-02 | 02 | 1 | ROLE-02 | — | Single-threaded sequence, no parallel execution | unit | `python -m pytest tests/test_gsd_driver.py::test_single_threaded_sequence -x -q` | ✅ | ⬜ pending |
| 4-03-01 | 03 | 1 | HEAL-01 | — | transient error → class=transient emitted | unit | `python -m pytest tests/test_failure_classifier.py::test_transient_class -x -q` | ✅ | ⬜ pending |
| 4-03-02 | 03 | 1 | HEAL-02 | — | backoff 1s→4s→16s on transient | unit | `python -m pytest tests/test_failure_classifier.py::test_exponential_backoff -x -q` | ✅ | ⬜ pending |
| 4-03-03 | 03 | 1 | HEAL-03 | — | 3 same failures → escalate to /gsd-debug | unit | `python -m pytest tests/test_failure_classifier.py::test_escalation_after_3 -x -q` | ✅ | ⬜ pending |
| 4-04-01 | 04 | 1 | HEAL-05 | — | hallucinated package blocked before network call | unit | `python -m pytest tests/test_registry_verify.py::test_blocks_hallucinated_package -x -q` | ✅ | ⬜ pending |
| 4-04-02 | 04 | 1 | HEAL-06 | — | retry_count persists across /clear | unit | `python -m pytest tests/test_gsd_driver.py::test_retry_budget_persists -x -q` | ✅ | ⬜ pending |
| 4-05-01 | 05 | 2 | VER-01 | — | VERIFICATION.md has 2-5 falsifiable criteria | unit | `python -m pytest tests/test_gsd_driver.py::test_verification_md_criteria -x -q` | ✅ | ⬜ pending |
| 4-05-02 | 05 | 2 | VER-02 | — | /gsd-verify-work invoked before phase marked done | unit | `python -m pytest tests/test_gsd_driver.py::test_verify_work_before_done -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_gsd_driver.py` — stubs for ROLE-01, ROLE-02, ROLE-03, ROLE-04, ROLE-05, ROLE-06, ROLE-08, HEAL-06, VER-01, VER-02, VER-03, VER-04
- [ ] `tests/test_failure_classifier.py` — stubs for HEAL-01, HEAL-02, HEAL-03, HEAL-04, HEAL-07
- [ ] `tests/test_registry_verify.py` — stubs for HEAL-05
- [ ] `tests/conftest.py` — shared fixtures (fake_shell, fake_which, monkeypatch) already exist from Phases 1-3

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Structured user handoff message readability | HEAL-04 | Content quality judgment | Run 4th failure injection, read handoff message output to user — must contain: state, last_error, what_was_tried, recommended_next_action fields |
| Escalation to /gsd-debug then /problem-solver | HEAL-03 | Requires live Claude Code session | Inject same failure 4x, observe that /gsd-debug is emitted on 3rd, /problem-solver on 4th |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
