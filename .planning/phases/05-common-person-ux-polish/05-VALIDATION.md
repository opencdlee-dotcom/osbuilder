---
phase: 5
slug: common-person-ux-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-30
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 05-RESEARCH.md § Validation Architecture (lines 1091–1172).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python 3.13 stdlib + pytest only — no new deps) |
| **Config file** | `pytest.ini` / `pyproject.toml` (existing — Phase 1) |
| **Quick run command** | `pytest tests/phase05/ -x --no-header -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~12 seconds (quick) / ~45 seconds (full, all phases) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase05/ -x --no-header -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 12 seconds

---

## Per-Task Verification Map

> Populated by gsd-planner — one row per task with `<automated>` verify command or Wave 0 dependency. Filled at planning time.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _to be filled by planner_ | _ | _ | _ | _ | _ | _ | _ | _ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> ~44 RED stub tests across the 8 phase requirements; all stubs xfail until corresponding Wave 1+ plan turns them green.

- [ ] `tests/phase05/test_friendly_error.py` — RED stubs for REQ-1, REQ-2, REQ-3 (translate signature, dictionary load, schema, no-raw-stack-frames assertions)
- [ ] `tests/phase05/test_narration.py` — RED stubs for REQ-4, REQ-5 (emit signature, role-banner regex, subprocess capture, build.log routing, jargon scan, `--quiet` plumbing)
- [ ] `tests/phase05/test_role_briefs.py` — RED stubs for REQ-6 (8 role files exist, 4-section structure, jargon scan)
- [ ] `tests/phase05/test_mode_gating.py` — RED stubs for REQ-7 (default-mode prompt jargon-free, `--advanced` exposes ≥3 tech names, state.md `mode` field)
- [ ] `tests/phase05/test_tech_writer.py` — RED stubs for REQ-8 (PHASE_STEP_COMMANDS includes `tech-writer`, humanizer invocation, score persisted, README has "How OSBuilder built this")
- [ ] `tests/phase05/conftest.py` — shared fixtures: subprocess-capture harness, mode-state factory, role-brief loader, fake humanizer, e2e-build runner
- [ ] `tests/phase05/fixtures/error_dictionary_minimal.md` — fixture for friendly-error tests
- [ ] `tests/phase05/fixtures/role_brief_minimal.md` — fixture for narration tests
- [ ] `tests/phase05/__init__.py` — package marker

*Wave 0 turns the entire test surface RED before any Wave 1 plan executes; each Wave 1 plan flips its assigned tests GREEN.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| End-to-end TODO web-app build produces ≥8 tutor lines + role banners with no jargon, no raw stack frames | UX-01, UX-02, UX-04, ROLE-09 | E2E build is multi-minute and depends on humanizer skill being installed; can run as nightly integration but not in pytest tight loop | `bash scripts/run_e2e_smoke.sh todo-web-app | tee /tmp/build.log; grep -E "Traceback|npm ERR!|pnpm ERR_|^Error: ENOENT" /tmp/build.log` (must exit 1); `grep -c "^> " /tmp/build.log` (must be ≥8 in default mode, 0 in `--quiet`) |
| Generated README passes `/humanizer @README.md` audit with zero critical issues | ROLE-07, UX-05 | Humanizer is an LLM slash command, not a deterministic CLI — non-pytest verifiable | After E2E build, run `/humanizer @projects/<built>/README.md`; verify the audit's "critical issues" count is 0 and `state.md` `humanizer_score` field is populated |
| `--advanced` mode exposes ≥3 of {Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind} across prompts | UX-03 | Interactive prompt verification through TTY | `bash scripts/run_e2e_smoke.sh --advanced todo-web-app < /dev/null` (or scripted answers); capture prompt stream; grep for the 9 tech names; count ≥3 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (~44 RED stubs)
- [ ] No watch-mode flags (pytest one-shot only)
- [ ] Feedback latency < 12s on quick run
- [ ] `nyquist_compliant: true` set in frontmatter (after planner fills the per-task map)

**Approval:** pending
