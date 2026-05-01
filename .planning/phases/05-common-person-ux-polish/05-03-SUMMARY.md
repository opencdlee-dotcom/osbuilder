---
phase: 05-common-person-ux-polish
plan: "03"
subsystem: narration-and-role-briefs
tags:
  - narration
  - role-banners
  - tutor-mode
  - thread-per-stream
  - build-log-rotation
  - tdd-green
requirements:
  - UX-01
  - UX-04
  - ROLE-09
dependency-graph:
  requires:
    - scripts/tests/test_narration.py (15 RED stubs from Plan 05-01)
    - scripts/tests/test_tutor_mode.py (8 RED stubs from Plan 05-01)
    - scripts/state_writer.py (mode + tutor_enabled in ALLOWED_FIELDS — added by Plan 05-01)
    - scripts/gsd_driver.py (PHASE_STEP_COMMANDS dispatch + step 9 slot from Plan 05-01)
    - references/roles/qa.md (existing 4-section pattern target)
  provides:
    - scripts/narration.py — emit(), capture_subprocess(), _refresh_state(), _load_briefs(), _init_build_log()
    - 7 new role briefs (pm, architect, frontend, backend, devops, reviewer, tech-writer)
    - qa.md extended with 4 Narration Brief sections (preserves existing VERIFICATION.md content)
    - gsd_driver._role_for_step / _emit / _refresh_narration_state / _init_build_log_if_new_build
    - 24/24 narration + tutor_mode tests GREEN
  affects:
    - All future Phase 5+ scripts that surface user-facing progress — they can call
      narration.emit() / capture_subprocess() for role-banner UX with tutor lines
    - Plan 05-05 (tech-writer pipeline) depends on the tech-writer brief existing
tech-stack:
  added: []
  patterns:
    - thread-per-stream subprocess capture (Popen + threading.Thread × 2; Windows-safe)
    - module-init brief loading (_load_briefs reads references/roles/*.md at import)
    - per-step copy override (action key maps to friendlier banner + tutor in brief)
    - graceful-degrade import guard (try: import narration as _narration / except: None)
    - ASCII-default banner symbols ([OK]/[FAIL]/...) with OSBUILDER_UNICODE=1 → ✓/✗ override
    - state.md-driven mode + tutor flags refreshed via state_writer subprocess
    - build.log truncation gated on phase_step==0 (new-build signal)
key-files:
  created:
    - scripts/narration.py
    - references/roles/pm.md
    - references/roles/architect.md
    - references/roles/frontend.md
    - references/roles/backend.md
    - references/roles/devops.md
    - references/roles/reviewer.md
    - references/roles/tech-writer.md
    - .planning/phases/05-common-person-ux-polish/05-03-SUMMARY.md
  modified:
    - scripts/tests/test_narration.py (16 stubs flipped GREEN; +1 build.log rotation test)
    - scripts/tests/test_tutor_mode.py (8 stubs flipped GREEN)
    - references/roles/qa.md (appended 4 Narration Brief sections; existing content preserved)
    - scripts/gsd_driver.py (narration import + 4 helpers + 7 wiring sites)
decisions:
  - "ASCII banner symbols by default ([OK] / [FAIL] / ...) — Phase 2 cross-platform mandate keeps Windows cmd.exe compatible. OSBUILDER_UNICODE=1 env var flips to ✓ / ✗. Banner templates store ✓/✗ as canonical glyphs; emit() rewrites them to the configured symbol set so role briefs stay readable when hand-edited."
  - "qa.md extended in place rather than rewritten — the existing reference content (Format / Falsifiability / Examples) governs VERIFICATION.md generation at phase_step=7, so it must stay. The new Narration Brief sections are appended after a horizontal rule and a # Narration Brief H1; the parser walks ## headings only, so the H1 boundary cleanly separates the two concerns."
  - "Per-step banner override path: when a brief has tutor_per_step[action]['banner'], emit() uses that friendlier label in place of the raw action (e.g., '/predator' renders as '[REVIEWER] Security check'). Banner templates also support {action} / {detail} format substitutions; status markers (✓/✗) are rewritten through emit's symbol map so OSBUILDER_UNICODE actually flips the rendering."
  - "capture_subprocess does NOT call _init_build_log — that is the caller's responsibility (gsd_driver invokes it when phase_step==0). This keeps capture_subprocess stateless w.r.t. build lifecycle so it can be reused outside the driver (preflight, scaffold) without surprising log truncations."
  - "Role-for-step mapping pulls FE/BE selection from state.next_action keywords ('ui'/'frontend'/'homepage'/'screen'/'page' → frontend; 'api'/'backend'/'database'/'model' → backend; default devops). This matches the plan's pseudocode — keywords are conservative (no 'route' to avoid matching unrelated copy)."
  - "test_raw_stderr_to_log payload string changed to STDERR-PAYLOAD (Rule 1 — Bug). The original RED stub used action='boom' with stderr text 'boom', which made the assertion 'boom not in stdout' fail on the legitimate banner '[DEVOPS] boom [OK]'. The fix uses a payload string distinct from the action label so the test exercises real raw-output isolation."
metrics:
  duration: ~14 minutes (3 commits, sequential)
  tasks: 2
  files: 12 (8 created, 4 modified)
  completed: 2026-04-30
---

# Phase 5 Plan 03: Narration + Role Briefs Summary

**One-liner:** Implements `scripts/narration.py` (role-banner emitter, tutor-mode renderer, thread-per-stream subprocess capture, build.log rotation) and creates the 7 missing role briefs so every PHASE_STEP_COMMANDS dispatch in `gsd_driver.py` emits a plain-English banner — with a `> ` tutor line on success in beginner+tutor mode — without leaking jargon, raw subprocess output, or Python tracebacks to the user.

## Outcome

After this plan, OSBuilder's GSD phase loop produces a dev-team-style narration. Every `emit_next_command` invocation:

1. Refreshes mode + tutor_enabled from state.md (graceful degrade if state_writer unavailable).
2. Truncates `.planning/osbuilder/build.log` at the start of each new build (phase_step==0 only — Open Question 6 resolution).
3. Emits a `[ROLE] action...` banner before each dispatch and a `[ROLE] action [OK]` banner after; failure paths emit `[ROLE] action [FAIL] (detail)`.
4. In beginner+tutor mode, also emits `> In plain English: ...` after every successful step.

The thread-per-stream `capture_subprocess` helper is available for callers that need to pipe raw subprocess output into the build log without surfacing tracebacks or stack frames to the user. It does NOT auto-truncate the log — that is the caller's job, gated on the new-build signal.

The forbidden-jargon test (`test_no_jargon_in_banners`) is a CI gate: emitting all 8 roles in beginner mode and grepping captured output against the 6-token list (`framework`, `endpoint`, `responsive`, `ORM`, `dependency injection`, `transpiler`) returns zero hits. Future role-brief edits that introduce jargon fail the test suite.

## Tasks Executed

| Task | Description | Files | Commit |
|---|---|---|---|
| 1 (RED) | Flip 24 narration + tutor_mode stubs to real assertions | scripts/tests/test_narration.py, scripts/tests/test_tutor_mode.py | fb70765 |
| 1 (GREEN) | Implement scripts/narration.py + test_raw_stderr_to_log payload fix | scripts/narration.py, scripts/tests/test_narration.py | fd28701 |
| 2 | 7 new role briefs + qa.md extension + gsd_driver wiring | references/roles/{pm,architect,frontend,backend,devops,reviewer,tech-writer}.md, references/roles/qa.md, scripts/gsd_driver.py | aaa8c69 |

### Module surface (scripts/narration.py)

| Symbol | Type | Purpose |
|---|---|---|
| `emit(role, action, status, detail)` | function | Banner + optional tutor line; reads `_TUTOR_ENABLED` + `_MODE` |
| `capture_subprocess(cmd, role, action, *, log_path, cwd, timeout)` | function | Thread-per-stream Popen capture; routes raw stdout/stderr to log |
| `_refresh_state(project_root)` | function | Reads mode + tutor_enabled via state_writer subprocess |
| `_init_build_log(log_path)` | function | Truncates the log file (open mode "w" with empty content) |
| `_load_briefs()` | function | Re-reads references/roles/*.md into _ROLE_BRIEFS |
| `_parse_brief_markdown(text)` | private | H2-section parser (stdlib regex) |
| `_drain_stream(stream, lines, log_handle)` | private | Background thread body for capture_subprocess |
| `_symbols()` | private | Status → symbol map; ASCII default, Unicode via env var |
| `_safe_format(template, **ctx)` | private | format() with KeyError/IndexError → original template |
| `REPO_ROOT` / `_BRIEF_DIR` / `STATE_WRITER` | constants | Path anchors |
| `FORBIDDEN_JARGON` | frozenset | 6-token list (documentation only — gate is test-time) |
| `_ROLE_BRIEFS` / `_TUTOR_ENABLED` / `_MODE` | module state | Loaded at import; refreshed on demand |

### Role brief inventory (references/roles/*.md)

| File | Status | Owns step | Sections | Per-step keys |
|---|---|---|---|---|
| pm.md | new | 0, 10 | 4 | /gsd-spec-phase, /gsd-new-project --auto, intake-paragraph, intake-structured, spec-lock, phase-complete |
| architect.md | new | 1 | 4 | /gsd-plan-phase, stack-research, plan-lock, design-review |
| frontend.md | new | 3 (UI phases) | 4 | execute-ui, build-component, build-page, style-pass |
| backend.md | new | 3 (API/DB phases) | 4 | execute-api, build-route, build-schema, migrate-data |
| devops.md | new | 2, 3 (default) | 4 | /gsd-execute-phase, registry-gate, scaffold, install-deps |
| reviewer.md | new | 5, 6 | 4 | /predator, /gsd-code-review, lock-review |
| tech-writer.md | new | 9 | 4 | /gsd-docs-update, generate-readme, check-humanizer, rewrite-readme |
| qa.md | extended | 4, 7, 8 | 4 (appended) | /code-tester, /gsd-verify-work, write-VERIFICATION.md |

### gsd_driver.py wiring sites

| Site | phase_step | Role | Action |
|---|---|---|---|
| current_phase==0 special case | (start) | pm | /gsd-new-project --auto |
| Registry gate entry | 2 | devops | registry-gate (start banner; ok/fail emitted in `_run_registry_gate`) |
| VERIFICATION.md write | 7 | qa | write-VERIFICATION.md |
| Phase advance | 10 | pm | phase-complete |
| Generic dispatch | 1, 3, 4, 5, 6, 8, 9 | mapped via `_role_for_step` | corresponding slash command |
| Unknown-step fallback | * | mapped via `_role_for_step` | unknown-step-{N} (status=fail) |

`_init_build_log_if_new_build` runs once per `emit_next_command` call, no-op unless `phase_step == 0`.
`_refresh_narration_state` runs once per `emit_next_command` so per-call mode/tutor changes are picked up.

## Verification

| Check | Expected | Result |
|---|---|---|
| `find references/roles -name "*.md" \| wc -l` | 8 | **8** |
| Each brief has all 4 H2 sections (`Banner Templates`, `Tutor Template`, `Per-Step Copy`, `Failure Copy`) | yes | **yes (8/8)** |
| `narration.emit("pm","test","ok")` prints `[PM]` line | yes | **yes** |
| Beginner+tutor default mode adds `> In plain English: …` | yes | **yes** |
| `_init_build_log` truncates a previously-written log | yes | **yes** ("first build content" not in second-init read) |
| `grep -c "narration" scripts/gsd_driver.py` | ≥ 7 | **19** |
| test_narration.py | 16 GREEN | **16 passed** |
| test_tutor_mode.py | 8 GREEN | **8 passed** |
| Full suite | no regressions | **121 passed, 6 skipped, 0 failed, 1 pre-existing warning** |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Test payload collided with action label in `test_raw_stderr_to_log`**

- **Found during:** Task 1 GREEN-phase verification.
- **Issue:** The Plan-mandated test wrote stderr `'boom'` while passing `action="boom"` to `capture_subprocess`. The role-banner `[DEVOPS] boom [OK]` legitimately contains the substring `boom`, so the assertion `"boom" not in captured` was a false positive — it would fail even if stderr capture worked perfectly.
- **Fix:** Renamed the stderr payload to `STDERR-PAYLOAD` (a string that cannot collide with any action label). The test now exercises true raw-output isolation. The action label is `check` — neutral and reflective of intent.
- **Files modified:** scripts/tests/test_narration.py
- **Commit:** fd28701

**2. [Rule 2 — Missing critical functionality] qa.md needed Narration Brief sections to satisfy the all-files-have-4-sections gate**

- **Found during:** Task 2 verification.
- **Issue:** Test `test_brief_has_required_sections` iterates over every `references/roles/*.md` file and asserts the 4 required sections. The pre-existing qa.md (created in Plan 04-05 for `/gsd-verify-work` content generation) does not have those sections — its purpose is documenting VERIFICATION.md content, not narration. The Plan instructs creating 7 new briefs but is silent on qa.md.
- **Fix:** Appended a `# Narration Brief` H1 followed by the 4 required H2 sections to qa.md. The original reference content (Format / Falsifiability / Examples / Escalation Note) is preserved above the new H1 and continues to govern VERIFICATION.md generation. The H2 parser only walks ## headings — the H1 boundary cleanly separates the two concerns. qa role banners and tutor lines now work alongside the existing reference content.
- **Files modified:** references/roles/qa.md
- **Commit:** aaa8c69

This is a Rule 2 fix — without these sections, `test_brief_has_required_sections` cannot pass and qa banners would degrade to the unparsed-brief fallback (`[QA] action [OK]` works but ignores the per-step copy and tutor template).

### Out of Scope (deferred / not done)

- **Pre-existing forbidden-jargon hits in qa.md reference content.** The qa.md examples include the word "endpoint" twice — both inside the existing `## Forbidden Criterion Patterns` and `## Valid Criterion Examples` sections (specifically: `**"The API returns the correct response."** — Too vague: which API endpoint, which response body, from where?` and `**API liveness:** The health endpoint responds with HTTP 200.`). These pre-date Plan 05-03 and live in the QA *reference* content, not the new Narration Brief sections. The runtime jargon gate (test_no_jargon_in_banners) only inspects emit() output, not file contents — and emit() reads only Banner Templates / Tutor Template / Per-Step Copy. The reference text never enters the captured stdout, so the test passes. A future plan can rename "endpoint" → "URL path" in the QA reference if that polishes the file further.
- **CLI flags `--quiet` and `--advanced` for narration.** Mode and tutor_enabled are already plumbed via state.md (Plan 05-01 + 05-04). A wrapper CLI that flips state via flags is a separate concern (Phase 7 publish polish) and out of scope here.
- **Plan 05-05 tech-writer / humanizer integration.** The 6 test_tech_writer.py stubs remain skipped — those flip GREEN in Plan 05-05.

## Threat Model Compliance

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-05-03-01 (Information Disclosure — build.log raw output) | accepted; build.log is project-local, not committed; phase 6 will add to .gitignore | accepted as designed |
| T-05-03-02 (Tampering — subprocess output as instruction injection) | `capture_subprocess` treats stdout/stderr as data only; never passed back to the LLM as instruction; only routed to log + summarized in role banner | mitigated; verified by `test_capture_subprocess_routes_raw_to_log` and `test_raw_stderr_to_log` |
| T-05-03-03 (DoS — subprocess producing gigabytes of output) | thread-per-stream with per-line write to log file; no in-memory accumulation beyond the per-call lines list (used by callers for last-N error context); `timeout` parameter kills runaway subprocesses | mitigated by design |
| T-05-03-04 (Tampering — forbidden jargon in role briefs) | test_tutor_mode.py::test_no_jargon_in_banners greps emitted output against 6-token list; CI gate at test time | mitigated; verified by `test_no_jargon_in_banners` |
| T-05-03-05 (DoS — build.log rotation deletes data unintentionally) | truncation only on phase_step==0 (explicit new-build signal); partial builds at step > 0 retain their log; `_init_build_log` is idempotent on an empty file | accepted as designed |

No new threat surface introduced. `capture_subprocess` uses `shell=False` and a fully argv-list-based command — mirroring the existing Phase 1–4 pattern.

## Threat Flags

None — the 8 narration-affecting wiring sites in `gsd_driver.py` reuse trust boundaries already reviewed in Plans 04-02 (state machine), 04-04 (registry gate), and 05-02 (friendly_error). No new network endpoints, file-system paths outside `.planning/osbuilder/`, or schema changes.

## Self-Check

- All 8 created files exist:
  - scripts/narration.py ✓ FOUND
  - references/roles/pm.md ✓ FOUND
  - references/roles/architect.md ✓ FOUND
  - references/roles/frontend.md ✓ FOUND
  - references/roles/backend.md ✓ FOUND
  - references/roles/devops.md ✓ FOUND
  - references/roles/reviewer.md ✓ FOUND
  - references/roles/tech-writer.md ✓ FOUND
- Files modified:
  - scripts/tests/test_narration.py ✓ FOUND (lazy-import fixture preserved; 16 tests)
  - scripts/tests/test_tutor_mode.py ✓ FOUND (8 tests)
  - references/roles/qa.md ✓ FOUND (4 sections appended after `# Narration Brief` boundary)
  - scripts/gsd_driver.py ✓ FOUND (`import narration as _narration` present; `_role_for_step`, `_emit`, `_refresh_narration_state`, `_init_build_log_if_new_build` defined; 19 narration references in file)
- Commit fb70765 (RED) ✓ FOUND
- Commit fd28701 (GREEN — narration.py) ✓ FOUND
- Commit aaa8c69 (briefs + driver wiring) ✓ FOUND
- 16 of 16 test_narration.py tests pass ✓ PASS
- 8 of 8 test_tutor_mode.py tests pass ✓ PASS
- Full suite: 121 passed, 6 skipped (Plan 05-05 tech_writer stubs), 0 failed, 1 pre-existing warning ✓ PASS

## Self-Check: PASSED

## TDD Gate Compliance

This plan ran a full TDD cycle:

1. **RED gate:** commit fb70765 — `test(05-03): flip narration + tutor_mode RED stubs to real assertions`. The lazy-import fixture causes all 24 tests to skip when `narration.py` is absent — that is the canonical RED state for the Phase 5 fixture pattern. Direct verification: before fb70765, all 23 stubs read `pytest.skip("Wave 1 target")`; after, the assertions are real and would fail (`AssertionError`) the moment narration.py exists without proper behavior.
2. **GREEN gate:** commits fd28701 (narration.py) + aaa8c69 (briefs + driver wiring). After both, all 24 tests pass; full suite 121 passed, 0 failed.
3. **REFACTOR gate:** not invoked — implementation matched the planned shape on the first try; the only test edit (Rule 1 fix) was a bug correction during the GREEN cycle, not a refactor.

## Next

Phase 5 Plan 05-05 (tech-writer + humanizer) flips the remaining 6 RED stubs in `test_tech_writer.py` to GREEN. It depends on `references/roles/tech-writer.md` (created here) and on the narration.emit hook at phase_step=9 (also wired here, currently emitting `[TECH-WRITER] /gsd-docs-update [OK]` for the tech-writer step).
