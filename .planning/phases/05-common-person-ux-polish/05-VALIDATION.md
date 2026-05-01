---
phase: 5
slug: common-person-ux-polish
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-30
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 05-RESEARCH.md § Validation Architecture (lines 1091–1172) + plan `<automated>` blocks.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python 3.13 stdlib + pytest only — no new deps) |
| **Config file** | `pytest.ini` / `pyproject.toml` (existing — Phase 1) |
| **Quick run command** | `python3 -m pytest scripts/tests/ -x --tb=short -q` |
| **Full suite command** | `python3 -m pytest scripts/tests/ --tb=short -q` |
| **Estimated runtime** | ~12 seconds (quick, Phase 5 only via `-k phase05` or per-file) / ~45 seconds (full, all phases) |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest scripts/tests/ -x --tb=short -q`
- **After every plan wave:** Run `python3 -m pytest scripts/tests/ --tb=short -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 12 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T-05-01-01 | 05-01 | 0 | UX-01..05, ROLE-07, ROLE-09 | T-05-01-01 (Spoofing — fixture impersonation) | Stubs use `pytest.skip("Wave 1 target")`; conftest fixtures isolated to `scripts/tests/` | unit (RED stubs) | `python3 -m pytest scripts/tests/ --collect-only -q` (≥122 collected, 0 errors) | ❌ W0 | ⬜ pending |
| T-05-01-02 | 05-01 | 0 | UX-01..05, ROLE-07, ROLE-09 | T-05-01-02 (Repudiation — silent skips) | Stubs are visible as `skipped`, not `xfail` or `pass`; state_writer ALLOWED_FIELDS extended to include `mode`, `tutor_enabled`, `humanizer_score`, `build_log_path`; `gsd_driver.PHASE_STEP_COMMANDS` advance shifted from step 9 → step 10 | unit (collection + state extension) | `python3 -m pytest scripts/tests/ -x --tb=short -q` (0 failures, 0 errors, ≥44 skipped) | ❌ W0 | ⬜ pending |
| T-05-02-01 | 05-02 | 1 | UX-02, UX-05 | T-05-02-01 (Tampering — dictionary integrity) | YAML hand-rolled subset parser only; load_dictionary asserts ≥30 entries; format-version field rejected on mismatch; FriendlyMessage drops Traceback / errno / module names | unit | `python3 -c "from friendly_error import translate, load_dictionary, FriendlyMessage; e = load_dictionary(); assert len(e) >= 30"` then `python3 -m pytest scripts/tests/test_friendly_error.py -x --tb=short -q` | ❌ W0 | ⬜ pending |
| T-05-02-02 | 05-02 | 1 | UX-02 | T-05-02-02 (Information Disclosure — raw error leaks) | Every error path in 5 scripts (preflight_check, scaffold_dispatch, stack_researcher, intake_handler, gsd_driver) routes through friendly_error.translate() before user-facing emit; raw stderr → debug log | integration | `python3 -m pytest scripts/tests/ -x --tb=short -q` then `grep -l "import friendly_error as _fe" scripts/{preflight_check,scaffold_dispatch,stack_researcher,intake_handler,gsd_driver}.py \| wc -l` (must equal 5) | ❌ W0 | ⬜ pending |
| T-05-03-01 | 05-03 | 1 | UX-01, UX-04, ROLE-09 | T-05-03-01 (Information Disclosure — raw subprocess output) | narration.emit() pure function; thread-per-stream subprocess capture (no select.select for Windows); `> ` tutor prefix in default mode; ASCII fallback `[OK]` / `[FAIL]` for non-Unicode terminals; build.log truncated on first call of new build (state.phase_step==0) | unit + integration | `python3 -c "import narration; narration.emit('pm','test','ok')"` then `python3 -m pytest scripts/tests/test_narration.py scripts/tests/test_tutor_mode.py -x --tb=short -q` | ❌ W0 | ⬜ pending |
| T-05-03-02 | 05-03 | 1 | UX-01, UX-04, ROLE-09 | T-05-03-02 (Spoofing — role brief tampering) | 7 new role briefs (pm, architect, frontend, backend, devops, reviewer, tech-writer) each with 4 sections (banner template, tutor template, per-step copy, failure copy); jargon-scan grep against all briefs reports zero forbidden tokens; gsd_driver.py emits narration at every PHASE_STEP_COMMANDS dispatch boundary | integration | `find references/roles -name "*.md" \| wc -l` (must equal 8) then `python3 -m pytest scripts/tests/test_narration.py scripts/tests/test_tutor_mode.py -x --tb=short -q` | ❌ W0 | ⬜ pending |
| T-05-04-01 | 05-04 | 1 | UX-03 | T-05-04-01 (Elevation of Privilege — advanced flag bypass) | `mode` field in state.md gates all jargon-bearing prompts in intake_handler / stack_researcher / scaffold_dispatch; default-mode question stream contains zero of {Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind}; `--advanced` exposes ≥3 of those terms | unit | `python3 -m pytest scripts/tests/test_mode_gating.py -x --tb=short -q` then `python3 -m pytest scripts/tests/ --tb=short -q` | ❌ W0 | ⬜ pending |
| T-05-05-01 | 05-05 | 2 | UX-01, ROLE-07 | T-05-05-01 (Denial of Service — humanizer skill missing) | gsd_driver.py PHASE_STEP_COMMANDS includes `tech-writer` step (step 9; advance shifted to step 10); invokes `/gsd-docs-update` then `/humanizer @README.md` (one-call per RESEARCH.md OQ-1, deviation from SPEC's `--check`/`--rewrite` flags documented in plan objective); `humanizer_score` persisted to state.md; missing-humanizer fallback emits friendly-error and continues with non-humanizer-gated README; README contains `## How OSBuilder built this` section naming all 8 roles | integration | `python3 -m pytest scripts/tests/test_tech_writer.py -x --tb=short -q` then `python3 -m pytest scripts/tests/ --tb=short -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> ~44 RED stub tests across the 8 phase requirements; all stubs `pytest.skip("Wave 1 target")` until the corresponding Wave 1+ plan implements the production code and updates the stub body.

- [ ] `scripts/tests/test_friendly_error.py` — RED stubs for REQ-1, REQ-2, REQ-3 (translate signature, dictionary load, schema, no-raw-stack-frames assertions, `test_import_guard_in_all_five_scripts`, `test_error_paths_wrapped_in_known_sites`)
- [ ] `scripts/tests/test_narration.py` — RED stubs for REQ-4 (emit signature, role-banner regex, subprocess capture, build.log routing + truncation on phase_step==0)
- [ ] `scripts/tests/test_tutor_mode.py` — RED stubs for REQ-5 (`> ` prefix, jargon scan against captured E2E output, `--quiet` plumbing zero `> ` lines)
- [ ] `scripts/tests/test_role_briefs.py` (or equivalent assertions inside test_narration.py) — RED stubs for REQ-6 (8 role files exist, 4-section structure, jargon scan)
- [ ] `scripts/tests/test_mode_gating.py` — RED stubs for REQ-7 (default-mode prompt jargon-free, `--advanced` exposes ≥3 tech names, state.md `mode` field)
- [ ] `scripts/tests/test_tech_writer.py` — RED stubs for REQ-8 (`emit_next_command(phase_step=9)` stdout contains `/gsd-docs-update`; humanizer one-call invocation; `humanizer_score` persisted; `test_readme_has_dev_team_section` for `## How OSBuilder built this` + 8 role names)
- [ ] `scripts/tests/conftest.py` — shared fixtures: subprocess-capture harness, mode-state factory, role-brief loader, fake humanizer, e2e-build runner
- [ ] `scripts/tests/fixtures/error_dictionary_minimal.yaml` — fixture for friendly-error tests
- [ ] `scripts/tests/fixtures/role_brief_minimal.md` — fixture for narration tests
- [ ] Phase 4 step-value test updates in `scripts/tests/test_gsd_driver.py` — every test that hard-codes `PHASE_STEP_COMMANDS[9]` for the prior advance behavior must move to `[10]` (Pitfall 7 from RESEARCH.md)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| End-to-end TODO web-app build produces ≥8 tutor lines + role banners with no jargon, no raw stack frames | UX-01, UX-02, UX-04, ROLE-09 | E2E build is multi-minute and depends on humanizer skill being installed; can run as nightly integration but not in pytest tight loop | `bash scripts/run_e2e_smoke.sh todo-web-app \| tee /tmp/build.log; grep -E "Traceback\|npm ERR!\|pnpm ERR_\|^Error: ENOENT" /tmp/build.log` (must exit 1); `grep -c "^> " /tmp/build.log` (must be ≥8 in default mode, 0 in `--quiet`) |
| Generated README passes `/humanizer @README.md` audit with zero critical issues | ROLE-07, UX-05 | Humanizer is an LLM slash command, not a deterministic CLI — non-pytest verifiable | After E2E build, run `/humanizer @projects/<built>/README.md`; verify the audit's "critical issues" count is 0 and `state.md` `humanizer_score` field is populated |
| `--advanced` mode exposes ≥3 of {Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind} across prompts | UX-03 | Interactive prompt verification through TTY | `bash scripts/run_e2e_smoke.sh --advanced todo-web-app < /dev/null` (or scripted answers); capture prompt stream; grep for the 9 tech names; count ≥3 |
| Generated README contains `## How OSBuilder built this` section naming all 8 dev-team roles in plain English | ROLE-07, SPEC AC #14 | README content is generated by `/gsd-docs-update` (LLM-driven) — content can be auto-grepped but plain-English readability is human-judged | After E2E build, `grep "## How OSBuilder built this" README.md` exits 0; `grep -E "PM\|Architect\|Frontend\|Backend\|DevOps\|QA\|Reviewer\|Tech Writer" README.md \| wc -l` reports ≥8; reviewer reads section once for non-developer comprehension |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (mapped above)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (8 tasks across 5 plans, every task has automated)
- [x] Wave 0 covers all MISSING references (~44 RED stubs across 5 test files)
- [x] No watch-mode flags (pytest one-shot only, `-x --tb=short -q`)
- [x] Feedback latency < 12s on quick run
- [x] `nyquist_compliant: true` set in frontmatter (per-task map filled)
- [ ] `wave_0_complete: true` — flips to true after 05-01 executes and stubs collect green

**Approval:** approved 2026-04-30 (per-task map filled, paths corrected to scripts/tests/, all 8 tasks mapped)
