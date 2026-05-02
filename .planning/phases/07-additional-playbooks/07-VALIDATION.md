---
phase: 7
slug: additional-playbooks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-01
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `uv run pytest scripts/tests/test_phase07_*.py -x --timeout=30` |
| **Full suite command** | `uv run pytest scripts/tests/ -x` |
| **Estimated runtime** | ~30s for unit tests; ~8min for full E2E parametrized matrix (4 cases × ~2min) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest scripts/tests/test_phase07_<plan_slug>*.py -x --timeout=30`
- **After every plan wave:** Run `uv run pytest scripts/tests/test_phase07_*.py -x --timeout=120`
- **Before `/gsd-verify-work`:** Full suite must be green (including parametrized E2E in 07-06)
- **Max feedback latency:** 30 seconds for unit tests; 120 seconds per E2E case

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-XX | 01 | 1 | SCAF-02..05 | — | Inference does not silently coin-flip; ambiguous → question-bank | unit | `uv run pytest scripts/tests/test_phase07_intake_inference.py -x` | ❌ W0 | ⬜ pending |
| 07-02-XX | 02 | 2 | SCAF-02 | — | fastapi-starter ships v2-native syntax; no API key required to boot | unit + E2E | `uv run pytest scripts/tests/test_phase07_ai_service.py -x` | ❌ W0 | ⬜ pending |
| 07-03-XX | 03 | 2 | SCAF-03 | — | CLI persists state across runs (SQLite write/read) | unit + E2E | `uv run pytest scripts/tests/test_phase07_cli.py -x` | ❌ W0 | ⬜ pending |
| 07-04-XX | 04 | 2 | SCAF-04 | — | Tauri scaffolds non-interactively; Electron globally refused | unit + E2E | `uv run pytest scripts/tests/test_phase07_desktop.py -x --timeout=180` | ❌ W0 | ⬜ pending |
| 07-05-XX | 05 | 2 | SCAF-05 | — | Hub structural diff matches vendored snapshot | unit + structural diff | `uv run pytest scripts/tests/test_phase07_hub_platform.py -x` | ❌ W0 | ⬜ pending |
| 07-06-XX | 06 | 3 | SCAF-02..05 | — | Stranger-clone ≤5min for all 4 playbooks (parametrized) | E2E | `uv run pytest scripts/tests/test_e2e_playbooks.py -x --timeout=180` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/tests/test_phase07_intake_inference.py` — RED stubs for inference scoring + tie-break + question-bank fallback (D-01..D-03)
- [ ] `scripts/tests/test_phase07_ai_service.py` — RED stubs for `scaffold_ai_service`, fastapi-starter file presence, Pydantic v2 syntax assertions (D-10..D-12)
- [ ] `scripts/tests/test_phase07_cli.py` — RED stubs for `scaffold_cli`, post-scaffold writes, SQLite ping round-trip (D-13..D-14)
- [ ] `scripts/tests/test_phase07_desktop.py` — RED stubs for `scaffold_desktop`, create-tauri-app dispatch, Electron refusal (D-07..D-09)
- [ ] `scripts/tests/test_phase07_hub_platform.py` — RED stubs for `scaffold_hub`, structural diff vs `assets/hub-template/professor-snapshot/` (D-04..D-06)
- [ ] `scripts/tests/test_e2e_playbooks.py` — Wave 0 stub: `pytest.skip("Wave 1 target")` parametrized matrix (D-17..D-19)
- [ ] `scripts/tests/conftest.py` — extend with per-playbook timeout dict + new mock fixtures if needed (mock_pnpm_subprocess, mock_uv_subprocess, mock_cargo_subprocess)
- [ ] `assets/hub-template/professor-snapshot/` — vendor `../professor/` snapshot at planning time (per research recommendation)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stranger-clone ≤5min for ai-service | SCAF-02 / SC-01 | Subjective UX timing — automated test covers contract, human gate covers feel | Per `07-HUMAN-UAT.md` runbook (mirror Phase 6) |
| Stranger-clone ≤5min for cli | SCAF-03 / SC-02 | Same | Same |
| Stranger-clone ≤5min for desktop | SCAF-04 / SC-03 | Same; also requires interactive system permission grants on first Tauri build | Same — note Rust toolchain install is not counted in 5-min budget |
| Stranger-clone ≤5min for hub-platform | SCAF-05 / SC-04 | Hub is workspace-level — UX measured by "does CLAUDE.md routing make sense to a fresh human" | Same |
| `pnpm tauri dev` opens native window | SC-03 | OS-level GUI assertion not feasible in CI | Manual confirmation in 07-HUMAN-UAT.md |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s per E2E case, < 30s for unit
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
