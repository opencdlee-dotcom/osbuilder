# Project State: OSBuilder

**Last Updated:** 2026-04-29 (after roadmap creation)

## Project Reference

**Core Value:** A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.

**Current Focus:** Foundation — establish the skill skeleton, directory layout, and `state.md` plumbing so every subsequent phase has a resumable spine to build on.

## Current Position

- **Milestone:** v1 (initial open-source publish-ready release)
- **Phase:** 1 — Foundation
- **Plan:** Not yet planned (run `/gsd-plan-phase 1` next)
- **Status:** Roadmap created; awaiting Phase 1 planning
- **Progress:** [□□□□□□□□] 0/8 phases complete

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases planned | 0 / 8 |
| Phases completed | 0 / 8 |
| Plans executed | 0 |
| v1 requirements mapped | 68 / 68 (100%) |
| v1 requirements completed | 0 / 68 |

## Accumulated Context

### Key Decisions Locked In (from PROJECT.md + research)

- **Form:** Claude Code skill at `~/.claude/skills/osbuilder/` — never a standalone CLI/web app
- **Helper-script language:** Python 3.13 (cross-platform; bash fails Windows; Node has chicken-and-egg with preflight)
- **Architecture:** Orchestrator-with-playbooks (Anthropic Pattern 1 + 2 fused); SKILL.md ≤ 200 lines; progressive disclosure to `references/`
- **Execution model:** Strictly single-threaded; dev-team metaphor is **narration only**, never parallel agents (DeepMind Dec 2025 documented 41-86.7% multi-agent failure rates)
- **Reflection cap:** Hard 3 per failure (Aider's empirically-validated limit); structured escalation beyond
- **Scaffolder rule:** Always-deterministic-scaffolder-first; never hand-write `package.json` / `tsconfig.json` / `pyproject.toml`
- **State checkpoint:** `<project-root>/.planning/osbuilder/state.md` (~15 lines) for compaction-resume
- **Privacy default:** Private GitHub repos via `gh repo create --private`; explicit `--public` required to override
- **Refuse-list (v1 default):** K8s, microservices, service-mesh, Helm, Electron, native mobile, auto-deploy, public repos by default
- **Composition rule:** If a sub-skill (gsd, brainiac, predator, code-tester, problem-solver, gsd-debug) is missing functionality, fix the sub-skill — never fork it into OSBuilder

### Active Todos

- [ ] Plan Phase 1: Foundation (`/gsd-plan-phase 1`)
- [ ] Execute Phase 1 plans (per plan)
- [ ] Verify Phase 1 against falsifiable success criteria
- [ ] Transition to Phase 2

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

**Last session:** Initialization (PROJECT.md → REQUIREMENTS.md → research/ → ROADMAP.md)

**Where to resume:**
1. Run `/gsd-plan-phase 1` to plan Foundation phase
2. The plan will decompose Phase 1 success criteria into atomic plans
3. Execute plans via `/gsd-execute-phase 1`
4. Verify against the 5 success criteria documented in ROADMAP.md Phase 1

**Files of record:**
- `.planning/PROJECT.md` — vision, scope, constraints, key decisions
- `.planning/REQUIREMENTS.md` — 68 v1 requirements (all mapped)
- `.planning/ROADMAP.md` — 8 phases with falsifiable success criteria
- `.planning/research/` — STACK.md / FEATURES.md / ARCHITECTURE.md / PITFALLS.md / SUMMARY.md
- `.planning/STATE.md` — this file

---
*State file initialized at roadmap creation. Updated per phase / milestone transition.*
