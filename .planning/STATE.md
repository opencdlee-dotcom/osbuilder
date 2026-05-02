---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready_to_plan
stopped_at: Completed 07-06 (E2E harness + slow marker + 07-HUMAN-UAT.md; all 6 Phase 7 plans complete)
last_updated: "2026-05-02T17:33:28.770Z"
progress:
  total_phases: 8
  completed_phases: 8
  total_plans: 37
  completed_plans: 37
  percent: 100
---

# Project State: OSBuilder

**Last Updated:** 2026-04-29 (after Plan 01-01 completion)

## Project Reference

**Core Value:** A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.

**Current Focus:** Phase --phase — 07

## Current Position

Phase: 07 (additional-playbooks) — EXECUTING
Plan: Not started
Plans complete: 1/6 in Phase 7 (32/37 overall)

- **Milestone:** v1 (initial open-source publish-ready release)
- **Phase:** 8
- **Plans:** 04-01 (Wave 0 RED stubs), 04-02 (gsd_driver state machine), 04-03 (failure_classifier), 04-04 (registry_verify), 04-05 (qa.md), 04-06 (HEAL-05 gap closure — registry gate wired into step 2) — all complete
- **Status:** Ready to plan
- **Progress:** [██████████] 100%

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases planned | 1 / 8 |
| Phases completed | 1 / 8 |
| Plans executed | 5 |
| v1 requirements mapped | 68 / 68 (100%) |
| v1 requirements completed | 5 / 68 (FOUND-01..05 ✓) |

| Plan | Tasks | Files | Completed | Commit |
|------|-------|-------|-----------|--------|
| 01-01 (Wave 0 test infra) | 2 | 8 | 2026-04-29 | bedee58 + e3758de |
| 01-02 (SKILL.md + references seed) | 2 | 2 | 2026-04-29 | 5c3a8d2 |
| 01-03 (install.sh + .gitkeep) | 2 | 4 | 2026-04-29 | cee92cb |
| 01-04 (state_writer.py [TDD]) | 1 | 1 | 2026-04-29 | 271640c |
| 01-05 (bootstrap.sh + bootstrap.ps1) | 2 | 2 | 2026-04-29 | 99af455 |
| Phase 02-pre-flight-installer-cross-platform P01 | 3min | 2 tasks | 3 files |
| Phase 02-pre-flight-installer-cross-platform P02 | 572 | 2 tasks | 1 files |
| Phase 02-pre-flight-installer-cross-platform P03 | 3 | 1 tasks | 2 files |
| Phase 02-pre-flight-installer-cross-platform P04 | 8 | 2 tasks | 4 files |
| Phase 03-intake-stack-research-web-playbook-one-playbook-e2e P01 | 3 | 2 tasks | 3 files |
| Phase 03-intake-stack-research-web-playbook-one-playbook-e2e P02 | 4min | 2 tasks | 2 files |
| Phase 03-intake-stack-research-web-playbook-one-playbook-e2e P03 | 5 | 1 tasks | 1 files |
| Phase 03-intake-stack-research-web-playbook-one-playbook-e2e P04 | 8 | 1 tasks | 1 files |
| Phase 03-intake-stack-research-web-playbook-one-playbook-e2e P05 | 4 | 2 tasks | 3 files |
| Phase 04-gsd-handoff-verify-loop-failure-classifier P01 | 148 | 2 tasks | 4 files |
| Phase 04 P02 | 135 | 1 tasks | 1 files |
| Phase 04 P03 | 8 | 1 tasks | 1 files |
| Phase 04 P04 | 102 | 1 tasks | 1 files |
| Phase 04 P05 | 4 | 1 tasks | 1 files |
| Phase 04 P06 (HEAL-05 gap closure) | 6 | 2 tasks | 2 files |
| Phase 05 P01 | 6min | 2 tasks | 7 files |
| Phase 05 P02 | 12min | 2 tasks | 9 files |
| Phase 05-common-person-ux-polish P04 | 9min | 1 tasks | 4 files |
| Phase 05-common-person-ux-polish P03 | 14min | 2 tasks | 12 files |
| Phase Phase 05 PP05 | 4min | 1 tasks | 3 files |
| Phase 06 P06-01 | 8min | 2 tasks | 9 files |
| Phase 06 P06-02 | 9min | 4 tasks | 10 files |
| Phase 06 P06-03 | 195 | 2 tasks | 6 files |
| Phase 06 P06-04 | 2 | 1 tasks | 3 files |
| Phase 06 P06-05 | 253 | 4 tasks | 5 files |
| Phase 06-ship-to-private-github-scalable-defaults P06-06 | 15 | 2 tasks | 2 files |
| Phase 07 P01 | 8min | 2 tasks | 5 files |
| Phase 07 P02 | 12min | 2 tasks | 9 files |
| Phase Phase 07 PP03 | 4min | 2 tasks tasks | 5 files files |
| Phase 07 P04 | 6min | 2 tasks tasks | 9 files files |
| Phase 07-additional-playbooks P05 | 7min | 2 tasks | 15 files |
| Phase 07 P06 | 2min | 2 tasks | 3 files |

## Accumulated Context

### Key Decisions Locked In (from PROJECT.md + research + execution)

- **Form:** Claude Code skill at `~/.claude/skills/osbuilder/` — never a standalone CLI/web app
- **Helper-script language:** Python 3.13 (cross-platform; bash fails Windows; Node has chicken-and-egg with preflight)
- **Test collection pattern (added 01-01):** Lazy-import-via-fixture for not-yet-implemented modules — `pytest.importorskip` at module top causes whole-file collection skip and breaks Nyquist `>=N tests collected` gates; use a `sw`-style fixture so individual test names always appear in `--collect-only`
- **Line-ending discipline (added 01-01):** Glob form `*.sh text eol=lf` (not per-file form) — VALIDATION regex `^\*\.sh text eol=lf$` only matches glob, BLOCKER 4 closure pattern
- **Architecture:** Orchestrator-with-playbooks (Anthropic Pattern 1 + 2 fused); SKILL.md ≤ 200 lines; progressive disclosure to `references/`
- **Execution model:** Strictly single-threaded; dev-team metaphor is **narration only**, never parallel agents (DeepMind Dec 2025 documented 41-86.7% multi-agent failure rates)
- **Reflection cap:** Hard 3 per failure (Aider's empirically-validated limit); structured escalation beyond
- **Scaffolder rule:** Always-deterministic-scaffolder-first; never hand-write `package.json` / `tsconfig.json` / `pyproject.toml`
- **State checkpoint:** `<project-root>/.planning/osbuilder/state.md` (~15 lines) for compaction-resume
- **Privacy default:** Private GitHub repos via `gh repo create --private`; explicit `--public` required to override
- **Refuse-list (v1 default):** K8s, microservices, service-mesh, Helm, Electron, native mobile, auto-deploy, public repos by default
- **Composition rule:** If a sub-skill (gsd, brainiac, predator, code-tester, problem-solver, gsd-debug) is missing functionality, fix the sub-skill — never fork it into OSBuilder
- **Recursion-safe monkeypatch (added 04-06):** When tests intercept `gd.subprocess.run` to selectively mock specific subprocess calls, capture `_real_run = subprocess.run` BEFORE `monkeypatch.setattr(...)`; the patched function must delegate to `_real_run`, never to `subprocess.run` (which is now the patched proxy → infinite recursion). Python module-attribute mutation is global; there is no separate "module-local reference" semantically distinct from the global module attribute.
- **Argv-token script-path matching (added 04-06):** Test predicates that classify subprocess calls should match by argv token (`c.endswith("script.py")`) not loose `" ".join(cmd)` substring scan — values written through state_writer can legitimately contain tool/script names and would otherwise be misclassified.
- **Neutral last_failure messaging (added 04-06):** Avoid embedding tool names like "registry_verify" in last_failure values; use threat-class names ("slopsquatting gate") instead. Both keeps test substring matchers honest AND surfaces user-facing language closer to "what threat was prevented" rather than "what tool ran".
- **Per-playbook scaffold shape (added 07-02):** Every `scaffold_<playbook>` mirrors `scaffold_web`'s 4-step shape verbatim: validate name → ensure_<tool> → subprocess.run scaffold cmd → atomic_write of vendored starter + Dockerfile + CI workflow. `_PLAYBOOK_DISPATCH` dict in `scaffold_dispatch.py` is the multi-playbook routing surface; `_PLAYBOOK_TOOLS` dict in `preflight_check.py` is the lazy install lookup (per-playbook tools NOT in REQUIRED_TOOLS).
- **D-21 typo correction (added 07-02):** winget package ID for uv is `astral-sh.uv` (lowercase, hyphenated namespace) — RESEARCH.md flagged `Astral.UV` as a typo. Tests assert exact lowercase form AND the absence of the typo string in the joined argv (catches regressions if a future change pastes the wrong ID).
- **Bracket-token argv preservation (added 07-02):** Tokens like `fastapi[standard]` MUST travel as a SINGLE argv element when `shell=False`. Source-level quoting is meaningless — what matters is whether brackets stay in one string token (correct) vs split across multiple (broken). Pattern applies to any extras-bearing pip/uv/gem invocation.
- **D-13/D-14 implementation (added 07-03):** `scaffold_cli` uses `uv add typer` (NO `[all]` extras); rich is hard-deped from typer 0.25.1+ (Pitfall 5). Tests assert the literal `typer[all]` is absent both from `pyproject.snippet.toml` AND from every subprocess argv emitted by `scaffold_cli` — catches regressions if a future change re-introduces the legacy bundled-extras spelling.
- **Module-name sanitization rule (added 07-03):** `_sanitize_module_name` is a pure `str.replace("-", "_")`. The user-facing script name keeps hyphens (`uv run my-cli` works); the Python module dir uses underscores (`my_cli/__main__.py` is a valid identifier). The `_validate_project_name` regex restricts the input alphabet to `[a-zA-Z0-9_-]`, so sanitization output is always safe — collisions like `my--cli` → `my__cli` produce a still-valid identifier.
- **CLI playbook ships NO Dockerfile (added 07-03):** Single-user local tool per RESEARCH.md §07-03 refuse list. `scaffold_cli` only stamps the python CI workflow (no `_write_dockerfile` call). Departure from `scaffold_web`/`scaffold_ai_service` which both stamp Dockerfiles. Future playbooks should follow the refuse-list signal: if Docker isn't a fit for the deployment target, skip the Dockerfile call rather than stamping a placeholder.
- **Comment-string negative-assertion trap (reaffirmed 07-03; first seen 07-02 with `Astral.UV`):** When a test asserts `literal_X` is absent from a file, comments inside that file MUST NOT embed `literal_X` to discourage its use — the assertion trips on the comment. Use rephrasing ("legacy bundled-extras spelling" instead of "typer[all]") to convey intent without embedding the trigger string. Pattern applies to any "do NOT use X" comment near a test that scans for X.

### Active Todos

- [x] Plan Phase 1: Foundation (`/gsd-plan-phase 1`)
- [x] Execute Plan 01-01 (Wave 0 test infrastructure) — 15 RED-state stubs
- [x] Execute Wave 1 plans 02 (SKILL.md), 03 (install.sh), 04 (state_writer.py), 05 (bootstrap shims)
- [x] Verify Phase 1 against 5 falsifiable success criteria in ROADMAP.md (all 5 passed; 15/15 pytest GREEN; install.sh real-machine smoke OK)
- [x] Transition to Phase 2 (Pre-flight installer)
- [x] Execute Phase 4 plans 04-01..04-05
- [x] Execute Phase 4 Plan 04-06 (HEAL-05 gap closure — registry_verify wired into gsd_driver step 2)
- [ ] Re-verify Phase 4 (`/gsd-verify-phase 4`) — SC5 should now flip FAILED → VERIFIED

### Known Blockers

None currently. Research flags noted for later phases (do not block Phase 1):

- **Phase 2:** Windows-without-WSL preflight UX needs hands-on validation; admin-escalation prompt UX matters; Docker Desktop licensing communication
- **Phase 7 (hub-platform):** Direct inspection of `../professor/` structure needed before writing the playbook
- **Phase 8 (`--production-ready`):** Phase-boundary decisions (bundled vs opt-in-per-feature) is a v1.x design call

### Sub-skill Dependency Versions (to be pinned in SKILL.md frontmatter)

To be confirmed in Phase 1:

- gsd >= TBD
- brainiac >= TBD
- predator >= TBD
- code-tester >= TBD
- problem-solver >= TBD
- gsd-debug >= TBD

## Session Continuity

**Last session:** 2026-05-02T17:33:28.756Z

**Stopped At:** Completed 07-06 (E2E harness + slow marker + 07-HUMAN-UAT.md; all 6 Phase 7 plans complete)

**Where to resume:**

1. Execute Wave 1 plans in parallel (disjoint files): 01-02 (SKILL.md), 01-03 (install.sh + .gitkeep), 01-04 (state_writer.py), 01-05 (bootstrap.{sh,ps1})
2. Each Wave 1 plan flips its assigned RED stubs to GREEN — verify via `pytest scripts/tests/`
3. Run `/gsd-verify-phase 1` once all 4 Wave 1 plans complete
4. Verify against the 5 falsifiable success criteria in ROADMAP.md Phase 1
5. Transition to Phase 2 via `/gsd-transition`

**Resume file:** None

**Files of record:**

- `.planning/PROJECT.md` — vision, scope, constraints, key decisions
- `.planning/REQUIREMENTS.md` — 68 v1 requirements (all mapped)
- `.planning/ROADMAP.md` — 8 phases with falsifiable success criteria
- `.planning/research/` — STACK.md / FEATURES.md / ARCHITECTURE.md / PITFALLS.md / SUMMARY.md
- `.planning/STATE.md` — this file

---
*State file initialized at roadmap creation. Updated per phase / milestone transition.*

**Planned Phase:** 07 (Additional playbooks) — 6 plans — 2026-05-02T08:00:31.525Z
**Plan 01-01 completed:** 2026-04-30T04:24:21Z — commits bedee58 (pyproject+gitattributes), e3758de (test stubs)
**Plan 04-06 completed:** 2026-04-30T21:31:11Z — commits 7b525e1 (test RED), 298b27c (feat GREEN); HEAL-05 fully satisfied; SC5 ready for re-verification
**Plan 07-01 completed:** 2026-05-02T08:13:01Z — commits 2722929 (test RED 9 stubs), 1c8de86 (feat GREEN: PLAYBOOK_KEYWORDS + infer_app_type + _score_playbooks + _is_low_confidence; parse_paragraph wired; Electron migrated to refuse-list.md; question-bank gains "## Q: What kind of thing"); 9/9 inference tests green, 157/157 total. Wave 2 (07-02..07-05) unblocked. Decisions D-01, D-02, D-03, D-22 implemented. Requirements SCAF-02..SCAF-05 marked complete.
**Plan 07-03 completed:** 2026-05-02T08:30:53Z — commits 1728b16 (test RED 5 stubs), 9b5d6a5 (feat GREEN: scaffold_cli + _sanitize_module_name + _PLAYBOOK_DISPATCH "cli" entry; assets/cli-starter/{__main__.py.tmpl, pyproject.snippet.toml}; references/playbooks/cli.md 56 lines; stack-menu.md cli playbook defaults). 5/5 plan tests green, 171/171 total (was 166; +5). D-13/D-14 implemented. Pitfall 5 contracts verified via pyproject snippet check + subprocess argv assertion. Requirement SCAF-03 marked complete.
