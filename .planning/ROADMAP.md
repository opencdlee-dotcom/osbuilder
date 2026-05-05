# Roadmap: OSBuilder

**Defined:** 2026-04-29
**Granularity:** standard (5-8 phases) → 8 phases derived
**Total v1 requirements:** 68 (REQUIREMENTS.md header reads "65" — actual count is 68; discrepancy noted, all 68 mapped)
**Coverage:** 68/68 mapped (100%)

**Core Value:** A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.

## Phases

- [x] **Phase 1: Foundation** — Skill skeleton + state plumbing so a `/clear`'d session can resume mid-build *(complete 2026-04-29)*
- [x] **Phase 2: Pre-flight installer** — Cross-platform auto-install of Node/Python/git/gh/Docker for non-developers (completed 2026-04-30)
- [ ] **Phase 3: Intake + Stack research + Web playbook (one-playbook E2E)** — Prove the loop with deterministic scaffolder-first web builds
- [ ] **Phase 4: GSD handoff + Verify loop + Failure classifier** — Quality moat: classified retries, 3-reflection cap, falsifiable verification
- [ ] **Phase 5: Common-person UX polish** — Tutor mode, friendly errors, dev-team narration that the audience actually understands
- [ ] **Phase 6: Ship to private GitHub + scalable defaults** — Close the build → ship loop with sensible-by-default scaffold shape
- [x] **Phase 7: Additional playbooks** — AI-service, CLI, desktop (Tauri), hub-platform variants *(complete 2026-05-02)*
- [ ] **Phase 8: Skill quality / publish-bar** — Examples gallery, install one-liner, demo video, version-drift validator, `--production-ready` flag

## Phase Details

### Phase 1: Foundation
**Goal:** OSBuilder exists as an installed, resumable Claude Code skill — every other phase depends on the skill skeleton, directory layout, and state-checkpoint plumbing being real on disk.
**Depends on:** Nothing (first phase)
**Requirements:** FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05
**Success Criteria** (what must be TRUE):
  1. After install, `~/.claude/skills/osbuilder/SKILL.md` exists, has valid YAML frontmatter (`name`, `description`), and `wc -l SKILL.md` reports ≤ 200.
  2. Running `tree ~/.claude/skills/osbuilder/ -L 2` shows the four standard directories (`references/`, `scripts/`, `assets/`, `examples/`) with no nesting deeper than one level.
  3. On a machine where Python is missing, running `bash bootstrap.sh` (POSIX) or `pwsh bootstrap.ps1` (Windows) installs Python and re-execs into `state_writer.py` without manual intervention.
  4. After `scripts/state_writer.py write --goal "test"` runs, `<project-root>/.planning/osbuilder/state.md` is on disk, ≤ 20 lines, and contains all 10 named fields (goal, app_type, playbook, current_role, current_phase, phase_step, last_failure, retry_count, escalation_level, next_action).
  5. After a simulated `/clear`, re-loading SKILL.md and reading `state.md` returns the user to the same `current_role` / `current_phase` as before the clear.
**Plans:** 5 plans
Plans:
- [x] 01-01-PLAN.md — Wave 0 test infrastructure (pyproject.toml, .gitattributes, pytest stubs for FOUND-01/02/05) — completed 2026-04-29 (commits bedee58 + e3758de)
- [x] 01-02-PLAN.md — SKILL.md (≤ 200 lines, valid frontmatter, Resume Protocol) + references/README.md seed (FOUND-01, FOUND-02) — completed 2026-04-29 (commit 5c3a8d2)
- [x] 01-03-PLAN.md — install.sh (idempotent, anchored paths) + .gitkeep markers for the 4-dir layout (FOUND-03) — completed 2026-04-29 (commit cee92cb)
- [x] 01-04-PLAN.md — scripts/state_writer.py: 10-field state.md plumbing, atomic os.replace, V5/V12/V7 input validation (FOUND-05) [TDD] — completed 2026-04-29 (commit 271640c)
- [x] 01-05-PLAN.md — scripts/bootstrap.sh (POSIX) + scripts/bootstrap.ps1 (PowerShell 5.1) cross-platform Python install shims (FOUND-04) — completed 2026-04-29 (commit 99af455)

### Phase 2: Pre-flight installer (cross-platform)
**Goal:** A non-developer with a fresh machine — no Node, no Python beyond what was bootstrapped, no git, no `gh`, no Docker — runs `/osbuilder` once and ends up with all required prerequisites installed, with no manual command-line work.
**Depends on:** Phase 1
**Requirements:** PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-06, PRE-07
**Success Criteria** (what must be TRUE):
  1. On a fresh macOS / Ubuntu / Windows 11 machine missing all five tools (Node 20+, Python 3.13+, git, `gh`, Docker), running OSBuilder's preflight detects every missing tool within 10 seconds and lists them by name.
  2. The user sees a single dry-run preview ("Here's what I'll install: Node 20 via brew, gh CLI via brew, …") before any state change, and answering "yes" once installs every listed tool without further prompts.
  3. If any single install in the batch fails, the rolled-back machine is in the exact state it was in before preflight ran — `which node` / `which python3` / `which gh` / `which docker` return the same results as before.
  4. Running `/osbuilder uninstall` on a machine where preflight installed five tools removes all five (and only those five — pre-existing tools are left intact).
  5. On a Windows machine without Docker Desktop, passing `--no-docker` lets the user complete a full SQLite-only single-user CLI build to private GitHub without ever being prompted for Docker.
  6. End-to-end: a non-developer on a fresh Mac runs `/osbuilder` and the install flow completes (all required prereqs present, ready for intake) in ≤ 3 minutes including download time.
**Plans:** 4/4 plans complete
Plans:
- [x] 02-01-PLAN.md — Wave 0 test infrastructure: extend conftest.py with FakeShell + 3 fixtures, drop ≥ 15 RED stubs across test_preflight.py + test_uninstall.py (covers PRE-01..PRE-07)
- [x] 02-02-PLAN.md — scripts/preflight_check.py: detect / plan / render_preview / apply / rollback / uninstall / main with stdlib-only Python 3.13, atomic install-log, all-or-nothing rollback (PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-07) [TDD]
- [x] 02-03-PLAN.md — scripts/uninstall.py: thin wrapper around preflight_check.uninstall (PRE-06)
- [x] 02-04-PLAN.md — references/preflight/{README,macos,linux,windows}.md: per-OS install matrices, decision trees, edge cases — handoff entry point (no SKILL.md edit)

### Phase 3: Intake + Stack research + Web playbook (one-playbook E2E)
**Goal:** A user describes a web app in plain English and OSBuilder produces a scaffolded, runnable Next.js + Postgres + Tailwind project on disk — proving the full intake → research → scaffold loop end-to-end on the most-validated playbook before any other playbooks are added.
**Depends on:** Phase 2
**Requirements:** IN-01, IN-02, IN-03, IN-04, IN-05, RES-01, RES-02, RES-03, RES-04, SCAF-01, SCAF-06
**Success Criteria** (what must be TRUE):
  1. A user pastes a paragraph ("I want a website where students upload lab notebooks and I grade them") and OSBuilder produces a synthesized brief that successfully feeds `/gsd-new-project --auto` without any clarifying re-prompt loops beyond the documented question bank.
  2. A user submits a structured spec (features list + stack hints + user types) instead of a paragraph and reaches the same brief output with no functional difference.
  3. Every clarifying question presented to the user reads in plain English (no jargon: never the word "responsive", "ORM", "framework", "endpoint" appears in a question), and every question shows an "I don't know, you decide" option that resolves to the documented sensible default.
  4. For a "build me a TODO web app" intake, OSBuilder's research output is a structured stack record (libraries with verified versions, anti-recommendations, rationale) that names Next.js 16.x, Drizzle, Postgres, Tailwind 4, and pnpm — and falls back to `references/stack-menu.md` when web research times out.
  5. After research completes, `scripts/scaffold_dispatch.py` runs `pnpm create next-app@latest …` (or the verified equivalent) and produces a project where `pnpm install && pnpm dev` boots the scaffolded homepage on `localhost:3000` — with zero hand-written `package.json` / `tsconfig.json` lines committed by OSBuilder.
  6. Passing `--advanced` lets the user override any researched stack choice via the prompt; the override is logged to `state.md` and respected downstream.
  7. End-to-end: passing a paragraph describing a TODO app produces a working scaffolded project + GSD project plan within 60 seconds (excluding network fetch time for `pnpm install`).
**Plans:** 5 plans
Plans:
- [x] 03-01-PLAN.md — Wave 0 test infrastructure: 16 RED stubs across test_intake.py (IN-01..05), test_stack_researcher.py (RES-01..04), test_scaffold_dispatch.py (SCAF-01, SCAF-06); brings total collected to ≥ 46
- [x] 03-02-PLAN.md — scripts/intake_handler.py: parse_paragraph + parse_structured → derived_spec.md + state_writer.py ALLOWED_FIELDS extension (IN-01..05) [TDD]
- [x] 03-03-PLAN.md — scripts/stack_researcher.py: brainiac delegation + stack-menu fallback + advanced overrides → stack_choices in state.md (RES-01..04) [TDD]
- [x] 03-04-PLAN.md — scripts/scaffold_dispatch.py: ensure_pnpm + create-next-app + Drizzle wiring → project on disk (SCAF-01, SCAF-06) [TDD]
- [x] 03-05-PLAN.md — references/playbooks/web.md + references/stack-menu.md + references/question-bank.md: playbook spec, fallback defaults, jargon-free question bank (SCAF-01 support, RES-03 support, IN-03/IN-04 support)

### Phase 4: GSD handoff + Verify loop + Failure classifier
**Goal:** Once a project is scaffolded, OSBuilder drives GSD's per-phase loop with role delegation, classified failure handling capped at 3 reflections, and falsifiable verification on every phase — so quality is real before the UX layer wraps it.
**Depends on:** Phase 3
**Requirements:** ROLE-01, ROLE-02, ROLE-03, ROLE-04, ROLE-05, ROLE-06, ROLE-08, HEAL-01, HEAL-02, HEAL-03, HEAL-04, HEAL-05, HEAL-06, HEAL-07, VER-01, VER-02, VER-03, VER-04
**Success Criteria** (what must be TRUE):
  1. After scaffolding completes, OSBuilder invokes `/gsd-new-project --auto` exactly once with the synthesized brief, then drives `/gsd-spec-phase`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/code-tester`, `/gsd-verify-work`, `/predator`, and `/gsd-code-review` in strict sequence (single-threaded — no parallel role execution) per ROADMAP phase.
  2. Every phase produces a `VERIFICATION.md` that lists 2-5 falsifiable success criteria (observable user behaviors, never "tests pass") and `/gsd-verify-work` checks each criterion before the phase is marked done.
  3. Injecting a transient network error during `pnpm install` triggers `scripts/failure_classifier.py` to emit class `transient`, retries with exponential backoff (1s → 4s → 16s), and recovers without escalating to the user.
  4. Injecting the same validation failure 3 times in a row (e.g., a code-tester finding the LLM cannot fix) triggers escalation to `/gsd-debug` then `/problem-solver`, then on the 4th failure produces a structured handoff to the user (state, last error, what was tried, recommended next action) — and `state.md`'s `retry_count` field shows `3`.
  5. Attempting to install a hallucinated package name (e.g., `npm install @anthropic/clauded-code-helper`) is blocked by `scripts/registry_verify.py` before any network call to the registry; the verification gate runs with `--ignore-scripts` until the package is verified to exist on the public registry.
  6. After `/clear` is fired mid-build, re-invoking OSBuilder reads `state.md`'s `retry_count` and `last_failure` and resumes from the same retry budget rather than restarting the counter at zero.
  7. Every phase invokes `/predator` and `/gsd-code-review` after `/code-tester` and before the phase is marked done in `state.md`.
**Plans:** 6 plans (5 original + 1 gap-closure)
Plans:
- [x] 04-01-PLAN.md — Wave 0: extend state_writer.py ALLOWED_FIELDS (gsd_phase_count, failure_class, escalation_log) + >= 25 RED stubs across test_gsd_driver.py / test_failure_classifier.py / test_registry_verify.py; brings total collected to >= 71
- [x] 04-02-PLAN.md — scripts/gsd_driver.py: GSD phase loop state machine — emit-next, PHASE_STEP_COMMANDS dispatch (steps 0-9), VERIFICATION.md write, retry/escalation, build_install_cmd [TDD] (ROLE-01..06, ROLE-08, HEAL-06, HEAL-07, VER-01..04)
- [x] 04-03-PLAN.md — scripts/failure_classifier.py: 4-class taxonomy + priority-ordered regex + handle_transient (4x backoff) + build_escalation_handoff [TDD] (HEAL-01..04, HEAL-07)
- [x] 04-04-PLAN.md — scripts/registry_verify.py: npm/PyPI/crates.io HEAD-request gate + fail-open on network error + CLI exit codes [TDD] (HEAL-05, HEAL-06)
- [x] 04-05-PLAN.md — references/roles/qa.md: VERIFICATION.md format, falsifiability rule, forbidden patterns, >= 5 observable-behavior examples, 2-5 count rule (VER-01 support)
- [x] 04-06-PLAN.md — scripts/gsd_driver.py + tests: wire registry_verify.py into phase_step==2 handler (HEAL-05 gap closure — added _run_registry_gate + 3 integration tests) [TDD]

### Phase 5: Common-person UX polish
**Goal:** With the verify loop proven, layer the UX that makes OSBuilder usable by someone who has never written code — tutor mode, friendly errors, dev-team narration ("PM is gathering requirements... ✓"), outcome-framed questions, and beginner-mode default.
**Depends on:** Phase 4
**Requirements:** ROLE-07, ROLE-09, UX-01, UX-02, UX-03, UX-04, UX-05
**Success Criteria** (what must be TRUE):
  1. Default OSBuilder runs (no flags) print tutor-mode explanations of "what just happened in plain English" at every role transition; passing `--quiet` suppresses every tutor-mode line and only emits role banners + final outputs.
  2. During an end-to-end build, the user sees dev-team narration ("PM is gathering requirements... ✓ / Architect chose Next.js because… / Frontend dev is building the homepage…") for every phase — and never sees raw command output, raw stack traces, `ENOENT`, `EACCES`, or framework jargon in any default-mode line.
  3. Inducing each of the top 30 errors documented in the friendly-error dictionary (e.g., port-in-use, missing Docker daemon, expired `gh` token, invalid Postgres version) produces a translated message of the form "here's what broke and here's what to do" with a concrete next step the user can copy-paste.
  4. By default, the user is never asked to choose between Next.js and SvelteKit, never sees the word "Postgres" before a build starts, and never sees a deploy-target prompt; passing `--advanced` exposes stack choice, deploy targets, and other technical decisions verbatim.
  5. Tech Writer phase produces a README with plain-English copy (verified by running `humanizer` against it for AI-pattern density) that explains the dev-team metaphor and the run command in language a non-developer can follow.
  6. The friendly-error dictionary documents an explicit expansion path (file location, format, contribution guideline) so future versions can grow the dictionary from real-world failure data without code changes.
**Plans:** 5 plans
Plans:
- [x] 05-01-PLAN.md — Wave 0: test stubs (46 RED, 124 collected), state_writer ALLOWED_FIELDS extension (mode/tutor_enabled/humanizer_score/build_log_path), gsd_driver step 9→/gsd-docs-update + phase-advance shifted to step 10 (UX-01..05, ROLE-07, ROLE-09)
- [x] 05-02-PLAN.md — friendly_error.py + 30-entry dictionary + expansion README + wiring into 5 scripts (UX-02, UX-05)
- [x] 05-03-PLAN.md — narration.py + 7 role briefs + gsd_driver narration wiring (UX-01, UX-04, ROLE-09)
- [x] 05-04-PLAN.md — beginner/advanced mode gating: _mode_from_state helper in intake_handler + stack_researcher; _render_derived_spec gates stack_hints behind mode==advanced; research_stack skips brainiac in beginner mode and auto-resolves to stack-menu defaults; 8/8 mode_gating tests GREEN; full suite 97 passed (UX-03)
- [x] 05-05-PLAN.md — tech-writer step full implementation: /gsd-docs-update + humanizer integration + fallback (UX-01, ROLE-07)

### Phase 6: Ship to private GitHub + scalable defaults
**Goal:** Close the build → ship loop. Every successful build ends as a private GitHub repo with a README runbook a stranger can clone-and-run on a fresh machine — with sensible-by-default scaffold shape (env config, real DB, Dockerfile, CI) and explicit refusals of K8s/microservices in v1.
**Depends on:** Phase 5
**Requirements:** SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SCL-01, SCL-02, SCL-03, SCL-04, SCL-05, SCL-06
**Success Criteria** (what must be TRUE):
  1. After verify-loop passes, OSBuilder runs `gh repo create --private` and `git push` such that the resulting GitHub repo is visible only to the authenticated user (verified by `gh repo view --json visibility` returning `"PRIVATE"`).
  2. A second user clones the resulting repo on a fresh machine, runs the README's documented commands in order (`cd <dir> && cp .env.example .env && <install> && <run>`), and reaches a working app on `localhost` in ≤ 5 minutes — with no edits to source files required.
  3. Committing a real-looking secret (e.g., a stripe live key pattern, an OpenAI API key pattern) into a built repo's working tree is blocked by the installed gitleaks pre-commit hook before the commit lands.
  4. A built web project on disk contains: `.env.example` (committed), `.env` (gitignored), `compose.yaml` (Docker Compose v2 filename, NOT `docker-compose.yml`), `Dockerfile`, and exactly one `.github/workflows/*.yml` file with build + test on PR — no Helm chart, no k8s manifest, no service-mesh config.
  5. Asking OSBuilder to "set up Kubernetes for this app" in default mode produces a refusal with a documented explanation; passing `--production-ready` instead adds K8s/observability/Sentry/migrations/healthchecks/rate-limiting/backup as **named phases in the roadmap**, not as default code in the scaffold.
  6. If `gh auth status` reports drift / expiry before push, the user sees a friendly error with the exact remediation command (`gh auth login --git-protocol https`), not a raw `gh` stack trace.
  7. A multi-user web build receives Postgres-via-compose by default; a single-user CLI build receives SQLite by default — confirmed by reading the generated `compose.yaml` / Python config.
**Plans:** 6 plans
Plans:
- [ ] 06-01-PLAN.md — Wave 0 RED stubs (>= 16 stubs across 5 test files); state_writer.py ALLOWED_FIELDS + 4 conftest fixtures; 2 derived_spec fixture .md files (covers all 11 phase reqs at the test-infra level)
- [ ] 06-02-PLAN.md — Track A: scripts/gh_handoff.py (ship + verify) + 5 friendly-error gh-* dictionary entries + assets/gitignore-templates/{common,node,python}.gitignore + assets/gitleaks/.pre-commit-config.yaml + .gitleaks.toml (SHIP-01, SHIP-03, SHIP-04, SHIP-05)
- [ ] 06-03-PLAN.md — Track B: scaffold_dispatch.py extension (_pick_database, _write_dockerfile, _write_ci_workflow) + 4 asset templates (Dockerfiles + CI workflows) (SHIP-03, SCL-01, SCL-02, SCL-03, SCL-04)
- [ ] 06-04-PLAN.md — Track C: scripts/runbook_writer.py + assets/readme-template.md (SHIP-02)
- [ ] 06-05-PLAN.md — Track D: refusal gate in intake_handler.py + scripts/production_phase_writer.py + references/refuse-list.md (SCL-05, SCL-06)
- [ ] 06-06-PLAN.md — Wave 2 wiring: SKILL.md + gsd_driver.py refusal hook + ship-step hook (integrates SHIP-01, SHIP-02, SHIP-05, SCL-05, SCL-06)

### Phase 7: Additional playbooks
**Goal:** With web validated end-to-end, additively support AI-service (FastAPI), CLI (Typer), desktop (Tauri 2), and hub-platform (Professor-style umbrella) builds — each as its own playbook file, each able to run the full intake → scaffold → verify → ship loop.
**Depends on:** Phase 6
**Requirements:** SCAF-02, SCAF-03, SCAF-04, SCAF-05
**Success Criteria** (what must be TRUE):
  1. A user describing "I want an HTTP API that summarizes documents with an LLM" results in OSBuilder choosing the AI-service playbook and producing a FastAPI + uv + Pydantic v2 project where `uv run fastapi dev` boots a working `/docs` page with at least one routed endpoint — using `assets/fastapi-starter/` as the deterministic template (since no `create-fastapi-app` exists).
  2. A user describing "I want a command-line tool to organize my photo library" results in the CLI playbook producing a Python + Typer + Rich + SQLite project where `uv run my-cli --help` prints a Rich-formatted help screen and the tool persists state across runs in a SQLite file.
  3. A user describing "I want a desktop app that runs locally with a tray icon" results in the desktop playbook producing a Tauri 2 project (Vite + React + Rust backend) where `pnpm tauri dev` opens a native window — and OSBuilder explicitly refuses Electron with a documented rationale if the user requests it.
  4. A user describing "build me a hub like Professor Hub for X" results in the hub-platform playbook producing a top-level CLAUDE.md routing table + sub-tool subdirectories that match the structural pattern of `../professor/` (verified by direct comparison: same top-level files, same nesting depth, same routing-table format).
  5. Every playbook in this phase passes the same end-to-end clone-and-run verification used in Phase 6 (a stranger clones, runs the documented command, reaches a working app in ≤ 5 minutes).
**Plans:** 6/6 plans complete
Plans:
- [x] 07-01-PLAN.md — Intake routing + 5-way `app_type` inference (`infer_app_type` keyword-bag) + Electron refusal migration to global refuse-list.md (D-01..D-03, D-22; SCAF-02..05 routing prerequisite)
- [x] 07-02-PLAN.md — AI-service playbook: `references/playbooks/ai-service.md` + `assets/fastapi-starter/` (Pydantic v2) + `scaffold_ai_service` + uv preflight extension + Dockerfile template (SCAF-02; D-10..D-12, D-20-21)
- [x] 07-03-PLAN.md — CLI playbook: `references/playbooks/cli.md` + `assets/cli-starter/` (Typer + Rich + SQLite) + `scaffold_cli` + module-name sanitization (SCAF-03; D-13, D-14)
- [x] 07-04-PLAN.md — Desktop playbook: `references/playbooks/desktop.md` + `scaffold_desktop` + `_build_tauri_identifier` + cargo preflight + `tauri.yml.tmpl` CI workflow (SCAF-04; D-07..D-09, D-20-21)
- [x] 07-05-PLAN.md — Hub-platform playbook: `references/playbooks/hub-platform.md` + `assets/hub-template/` + vendored `professor-snapshot/` + `scaffold_hub` (pure file-stamping) + `_extract_subtools` + state_writer.subtools (SCAF-05; D-04..D-06)
- [x] 07-06-PLAN.md — Shared E2E harness: parametrized `test_e2e_playbooks.py` (5-step contract × 4 playbooks) + per-playbook timeout dict (Pitfall 8) + `07-HUMAN-UAT.md` (SCAF-02..05; D-17..D-19)

### Phase 8: Skill quality / publish-bar
**Goal:** OSBuilder is open-source publish-ready — clean install one-liner, dev-team-metaphor README, 60-second demo video, 3-5 example gallery, version-drift validator on first run, and `--production-ready` flag adding observability/migrations/Sentry/etc. as named phases (not default code).
**Depends on:** Phase 7
**Requirements:** QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. The lint script `scripts/check_skill_md_length.py` (or equivalent) reports SKILL.md line count ≤ 200 in CI on every PR; a PR that pushes SKILL.md to 201 lines fails the check.
  2. Running the published `install.sh` one-liner on a clean machine drops `~/.claude/skills/osbuilder/` in place and the next `/osbuilder` invocation succeeds — for a user who has never installed a Claude Code skill before.
  3. The README contains a section explaining the dev-team metaphor (PM / Architect / Frontend / Backend / DevOps / QA / Reviewer / Tech Writer mapped to user-facing narration) and embeds or links a 60-second demo video that shows an end-to-end paragraph → working app on private GitHub flow.
  4. `examples/` contains at least 3 (target: 5) reference apps OSBuilder built — each with screenshots, before/after spec, and the GitHub URL of the resulting private repo (or a public mirror for the gallery).
  5. On first invocation each session, `scripts/check_skill_versions.py` reads the `requires:` block from SKILL.md frontmatter and reports a friendly error with the exact upgrade command if any of GSD / brainiac / predator / code-tester / problem-solver are below their declared minimum compatible version — and refuses to proceed until the user upgrades.
  6. Passing `--production-ready` to a default web build adds the documented named phases (observability via OpenTelemetry, automated migrations via Drizzle Kit, healthcheck endpoints, secret manager integration, Sentry error tracking, rate limiting, backup strategy) to the ROADMAP — and produces no additional code in the default scaffold when the flag is absent.
**Plans:** 8 plans
Plans:
- [x] 08-01-PLAN.md — Wave 0 RED test stubs (5 new test files, 20 stubs collected) + 08-HUMAN-UAT.md scaffold + 08-URL-LOCK.md (option-personal: cdlee/osbuilder) (covers all of QUAL-01..05 at the test-infra level) — completed 2026-05-04, commits 2a67b4e + d5ab1cf + 2267e4a
- [x] 08-02-PLAN.md — SKILL.md frontmatter `requires:` block + references/version-policy.md (QUAL-05 prerequisite) — completed 2026-05-04, commits 7f18a3c + 9d3c3e7
- [x] 08-03-PLAN.md — scripts/check_skill_md_length.py standalone CI lint script (QUAL-01) — completed 2026-05-04, commit 4216da1
- [ ] 08-04-PLAN.md — scripts/check_skill_versions.py first-session validator + ~/.osbuilder/last_check.txt marker (QUAL-05)
- [ ] 08-05-PLAN.md — .github/workflows/ci.yml (lint-skill-md + test jobs, pinned @v6 actions) (QUAL-01 CI surface)
- [ ] 08-06-PLAN.md — README.md (install one-liner + dev-team metaphor + demo embed + --production-ready doc) (QUAL-02, QUAL-03, SC-6 verification)
- [ ] 08-07-PLAN.md — assets/demo/ + RECORDING-CHECKLIST.md + [HUMAN] 60-second GIF/asciinema recording (QUAL-03 demo asset)
- [ ] 08-08-PLAN.md — examples/README.md gallery index + 3 example sub-directories (web/cli/ai-service) with SPEC.md + repo-url.txt placeholders (QUAL-04)

## Phase Ordering Rationale

- **Foundation before everything** — nothing testable without skill skeleton + `state.md` working
- **Preflight before intake** — non-developers cannot run intake on a machine missing prereqs
- **One-playbook E2E (web) before more playbooks** — prove the loop on the most-validated path before multiplying surface area
- **Verify-loop before UX polish** — quality before pretty (ugly + correct beats pretty + broken)
- **Ship before extra playbooks** — close the loop with one shippable build before expanding
- **Publish bar last** — examples gallery + production-ready flag presume everything else works

## Coverage Validation

| Phase | Requirements Mapped | Count |
|-------|---------------------|-------|
| 1 - Foundation | FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05 | 5 |
| 2 - Pre-flight installer | PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-06, PRE-07 | 7 |
| 3 - Intake + Research + Web playbook | IN-01, IN-02, IN-03, IN-04, IN-05, RES-01, RES-02, RES-03, RES-04, SCAF-01, SCAF-06 | 11 |
| 4 - GSD handoff + Verify + Healing | ROLE-01, ROLE-02, ROLE-03, ROLE-04, ROLE-05, ROLE-06, ROLE-08, HEAL-01, HEAL-02, HEAL-03, HEAL-04, HEAL-05, HEAL-06, HEAL-07, VER-01, VER-02, VER-03, VER-04 | 18 |
| 5 - Common-person UX polish | ROLE-07, ROLE-09, UX-01, UX-02, UX-03, UX-04, UX-05 | 7 |
| 6 - Ship + scalable defaults | SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SCL-01, SCL-02, SCL-03, SCL-04, SCL-05, SCL-06 | 11 |
| 7 - Additional playbooks | SCAF-02, SCAF-03, SCAF-04, SCAF-05 | 4 |
| 8 - Skill quality / publish-bar | QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05 | 5 |
| **Total** | | **68** |

**Coverage:** 68/68 v1 requirements mapped (100%) — no orphans, no duplicates.

**Note on requirement count:** REQUIREMENTS.md header reads "v1 requirements: 65 total" but a hand-count of every REQ-ID yields 68 (verified). All 68 are mapped here. The `Traceability` table below has been corrected to reflect the actual 68.

**Note on ROLE allocation rationale:** The instructions suggested "ROLE-01..09 (subset)" in Phase 4. The split applied here puts the *delegation contracts* (ROLE-01..06, ROLE-08) in Phase 4 (where the verify loop and skill-to-skill plumbing live) and the *user-facing narration* concerns (ROLE-07 Tech Writer / `humanizer`, ROLE-09 dev-team narration "PM is gathering requirements... ✓") in Phase 5 alongside tutor mode, friendly errors, and beginner-mode default. Rationale: ROLE-07 and ROLE-09 are UX-shaped (plain-English README, plain-English progress lines) and belong with the rest of the common-person UX work; the verify loop in Phase 4 only needs the delegation contracts, not the narration polish.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 5/5 | Complete | 2026-04-29 |
| 2. Pre-flight installer | 4/4 | Complete | 2026-04-30 |
| 3. Intake + Research + Web playbook | 0/5 | Ready to execute (5 plans created) | - |
| 4. GSD handoff + Verify + Healing | 6/6 | Complete (incl. 04-06 HEAL-05 gap closure) | 2026-04-30 |
| 5. Common-person UX polish | 1/5 | Wave 0 RED stubs landed (124 tests collected); Wave 1 next (05-02..05-05) | - |
| 6. Ship + scalable defaults | 0/TBD | Not started | - |
| 7. Additional playbooks | 6/6 | Complete | 2026-05-02 |
| 8. Skill quality / publish-bar | 0/TBD | Not started | - |

---
*Roadmap defined: 2026-04-29*
*Last updated: 2026-04-30 after Phase 4 Plan 04-06 (HEAL-05 gap closure: registry_verify wired into gsd_driver step 2; SC5 ready for re-verification)*
