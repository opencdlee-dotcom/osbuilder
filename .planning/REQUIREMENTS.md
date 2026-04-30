# Requirements: OSBuilder

**Defined:** 2026-04-29
**Core Value:** A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.

## v1 Requirements

Requirements for initial release. Each maps to exactly one roadmap phase (see Traceability).

### Foundation (skill skeleton + state plumbing)

- [ ] **FOUND-01**: OSBuilder is installed as a Claude Code skill at `~/.claude/skills/osbuilder/` with valid YAML frontmatter (`name`, `description`)
- [ ] **FOUND-02**: SKILL.md is ≤ 200 lines and routes via progressive disclosure to `references/` playbooks and role briefs
- [ ] **FOUND-03**: Skill directory layout follows Anthropic's one-level-deep pattern: `references/`, `scripts/`, `assets/`, `examples/`
- [ ] **FOUND-04**: A bootstrap shim (`bootstrap.sh` for POSIX + `bootstrap.ps1` for Windows) handles the case where Python is not installed
- [ ] **FOUND-05**: A `state.md` writer (`scripts/state_writer.py`) maintains a ~15-line checkpoint at `<project-root>/.planning/osbuilder/state.md` (goal, app_type, playbook, current_role, current_phase, phase_step, last_failure, retry_count, escalation_level, next_action) so a `/clear`'d or compacted session can resume mid-build

### Pre-flight installer (the moat)

- [ ] **PRE-01**: OSBuilder detects which prerequisites are missing on first run (Node 20+, Python 3.13+, git, `gh` CLI, Docker — Docker only when needed)
- [ ] **PRE-02**: For each missing tool, OSBuilder offers auto-install with a single confirmation prompt ("To build this app I need a tool called Node.js — want me to install it for you?")
- [ ] **PRE-03**: Pre-flight installer works on macOS (Homebrew), Linux (apt/dnf with auto-detection), and Windows (winget primary → scoop fallback → choco last resort)
- [ ] **PRE-04**: Pre-flight installer is transactional — failed installs roll back, never leave the system half-broken
- [ ] **PRE-05**: Pre-flight installer offers a dry-run preview ("Here's what I'll install: …") before any state change
- [ ] **PRE-06**: Pre-flight installer has an uninstall path that cleanly removes anything OSBuilder added
- [ ] **PRE-07**: A `--no-docker` mode lets users with Docker friction (e.g., Windows individual users without Docker Desktop) build SQLite-only single-user apps

### Intake (plain-English → structured brief)

- [ ] **IN-01**: User can describe an app in a plain-English paragraph and OSBuilder takes it from there
- [ ] **IN-02**: User can submit a structured spec (features list / stack hints / users) instead of paragraph form
- [ ] **IN-03**: All clarifying questions are outcome-framed in plain English (e.g., "Should it work on phones too?" — never "responsive design?")
- [ ] **IN-04**: Every clarifying question has an "I don't know, you decide" option that picks the documented sensible default
- [ ] **IN-05**: OSBuilder synthesizes the intake into a brief that it hands off to `/gsd-new-project --auto`

### Stack research per build

- [ ] **RES-01**: For each build, OSBuilder uses `/brainiac` (or a focused web-research agent) to research the right modern stack for the described app type
- [ ] **RES-02**: Stack research output is structured (libraries with verified versions, anti-recommendations, rationale)
- [ ] **RES-03**: Stack research falls back to OSBuilder's `references/stack-menu.md` when web research is inconclusive
- [ ] **RES-04**: User can override the researched stack via `--advanced` mode

### Deterministic scaffolders (always-scaffold-first)

- [ ] **SCAF-01**: OSBuilder maintains `references/playbooks/web.md` covering create-next-app + Drizzle + Postgres-via-compose + Tailwind 4 + pnpm
- [ ] **SCAF-02**: OSBuilder maintains `references/playbooks/ai-service.md` covering FastAPI + uv + Pydantic v2 (with OSBuilder-supplied template `assets/fastapi-starter/` since no `create-fastapi-app` exists)
- [ ] **SCAF-03**: OSBuilder maintains `references/playbooks/cli.md` covering Python + Typer + Rich + SQLite for single-user CLIs
- [ ] **SCAF-04**: OSBuilder maintains `references/playbooks/desktop.md` covering Tauri 2 (refuses Electron in v1)
- [ ] **SCAF-05**: OSBuilder maintains `references/playbooks/hub-platform.md` for Professor-Hub-style umbrella workspaces (top-level CLAUDE.md routing table + sub-tool subdirectories)
- [ ] **SCAF-06**: `scripts/scaffold_dispatch.py` invokes the right deterministic scaffolder for the chosen playbook — OSBuilder never hand-writes `package.json`, `tsconfig.json`, `pyproject.toml`, etc., when a scaffolder exists

### GSD handoff + role orchestration (single-threaded)

- [ ] **ROLE-01**: OSBuilder runs `/gsd-new-project --auto` once with the synthesized brief, then drives GSD's per-phase commands sequentially (never forks GSD's logic)
- [ ] **ROLE-02**: PM role delegates to `/gsd-spec-phase` for ambiguity scoring + spec lock
- [ ] **ROLE-03**: Architect role delegates to `/gsd-plan-phase` and `/brainiac` for stack/architecture decisions
- [ ] **ROLE-04**: Frontend / Backend / DevOps roles delegate to `/gsd-execute-phase` (sequentially, NOT in parallel — multi-agent is an anti-feature)
- [ ] **ROLE-05**: QA role delegates to `/code-tester` and `/gsd-verify-work` against falsifiable success criteria
- [ ] **ROLE-06**: Reviewer role delegates to `/predator` and `/gsd-code-review` before any phase is marked done
- [ ] **ROLE-07**: Tech Writer role delegates to `/gsd-docs-update` and `/humanizer` for plain-English README and runbook
- [ ] **ROLE-08**: Debug-cap delegates to `/gsd-debug` and `/problem-solver` when the failure classifier hits the retry limit on the same failure class
- [ ] **ROLE-09**: User-facing progress is narrated at the dev-team level ("PM is gathering requirements... ✓ / Frontend dev is building the homepage...") — never raw command output

### Self-healing build loop

- [ ] **HEAL-01**: A failure classifier (`scripts/failure_classifier.py`) categorizes errors into 4 classes: transient / context-overflow / tool-failure / validation-failure
- [ ] **HEAL-02**: Each failure class has a documented retry strategy (transient → exponential backoff; context → compress + retry; tool → fallback path; validation → re-plan, NOT retry)
- [ ] **HEAL-03**: Hard cap of 3 reflections per failure (Aider's empirically-validated limit); beyond that, escalate
- [ ] **HEAL-04**: Escalation produces a structured handoff to the user: state, last error, what was tried, recommended next action
- [ ] **HEAL-05**: A registry-verification gate (`scripts/registry_verify.py`) checks every package against the public registry before any `npm install` / `pip install` / `cargo add` (slopsquatting defense)
- [ ] **HEAL-06**: Package install runs with `--ignore-scripts` until registry verification passes
- [ ] **HEAL-07**: Retry counter and last-failure persist in `state.md` so retries survive `/clear` and compaction

### Common-person UX

- [ ] **UX-01**: Tutor mode is ON by default — explains in plain English what just happened at each stage; `--quiet` disables
- [ ] **UX-02**: Friendly errors via `scripts/friendly_error.py` — never expose raw stack traces, `ENOENT`, `EACCES`, etc.; always translate to "here's what broke and here's what to do"
- [ ] **UX-03**: Beginner mode is the default; `--advanced` opt-in flag exposes stack choice, deploy targets, and other technical decisions
- [ ] **UX-04**: Per-role narration scripts in `references/roles/*.md` produce non-jargon progress messages
- [ ] **UX-05**: A starter friendly-error dictionary covers the top 30 errors observed in dogfood builds; expansion path is documented for future versions

### Verify against falsifiable criteria

- [ ] **VER-01**: Every phase has a list of falsifiable success criteria (testable outcomes, not "tests pass")
- [ ] **VER-02**: `/gsd-verify-work` is invoked at the end of every phase against those criteria
- [ ] **VER-03**: `/code-tester` runs adversarial tests on every phase before it's marked done
- [ ] **VER-04**: `/predator` reviews architecture and security on every phase before it's marked done

### Ship to private GitHub

- [ ] **SHIP-01**: OSBuilder creates a **private** GitHub repository via `gh repo create --private` after verification passes
- [ ] **SHIP-02**: OSBuilder generates a README with a clone-and-run runbook that includes: clone command, `cd` into folder, `cp .env.example .env`, install command, run command, verification step
- [ ] **SHIP-03**: A `.gitignore` template prevents `.env` files, secrets, build artifacts, and platform-specific cruft from being committed
- [ ] **SHIP-04**: A gitleaks pre-commit hook is installed in the built repo to block secret leakage
- [ ] **SHIP-05**: `gh` CLI auth state is verified before push; auth-state-drift errors get friendly remediation messages

### Scalable-by-default + production-ready upgrade path

- [ ] **SCL-01**: Default scaffold ships with env-based config (`.env.example` + `.env` in `.gitignore`)
- [ ] **SCL-02**: Default scaffold uses a real database (Postgres-via-compose for multi-user web apps; SQLite only for single-user CLIs and explicitly chosen modes)
- [ ] **SCL-03**: Default scaffold ships with a Dockerfile and `compose.yaml` (Docker Compose v2)
- [ ] **SCL-04**: Default scaffold ships with a single GitHub Actions CI workflow (build + test on PR)
- [ ] **SCL-05**: OSBuilder **refuses** to add Kubernetes / microservices / service-mesh / Helm in v1 default builds
- [ ] **SCL-06**: `--production-ready` flag adds these as **named phases** in the roadmap (not default code): observability (logs/metrics/traces), automated migrations, healthchecks, secret manager, Sentry error tracking, rate limiting, backup strategy

### Skill quality (open-source publish-ready)

- [ ] **QUAL-01**: SKILL.md is ≤ 200 lines (verified via lint script)
- [ ] **QUAL-02**: A clean `install.sh` one-liner installs OSBuilder for someone who's never used Claude Code skills
- [ ] **QUAL-03**: README explains the dev-team metaphor and links to a 60-second demo video
- [ ] **QUAL-04**: An `examples/` gallery contains 3-5 reference apps OSBuilder built (validation + onboarding)
- [ ] **QUAL-05**: First-run skill-version-drift validator (`scripts/check_skill_versions.py`) checks that GSD, brainiac, predator, code-tester, and other delegated skills meet minimum compatible versions

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Reference-app intake

- **V2-REF-01**: User can point OSBuilder at an existing reference app (e.g., `../professor/`) and say "build me one like this for X"
- **V2-REF-02**: Reference-app extraction uses Repomix-style structural analysis OR `/predator`-driven extraction (decision deferred to v1.x design phase)

### Multimodal intake

- **V2-MM-01**: User can describe an app via voice transcription
- **V2-MM-02**: User can attach a hand-drawn sketch of the UI and OSBuilder extracts component intent

### Auto-deploy

- **V2-DEP-01**: `--deploy <target>` flag deploys built app to Vercel / Fly / Railway after push
- **V2-DEP-02**: Deploy target selection is plain-English ("where should people use it?") with sensible defaults
- **V2-DEP-03**: Deploy includes domain configuration helper

### Cross-platform validation

- **V2-XPL-01**: Real-machine CI matrix runs OSBuilder builds on macOS, Ubuntu, Windows (with and without WSL)
- **V2-XPL-02**: Each playbook ships with a "verified-on-platform" badge

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Native mobile (iOS / Android) | Native toolchain surface area (Xcode signing, Android SDKs) is too large for v1; web-responsive covers most needs. |
| Pure deploy-to-cloud-by-default | Deploy targets are opinionated and risky; private GitHub is the safe v1 anchor. Opt-in via `--production-ready` and v2 deploy phase. |
| Standalone CLI / web UI / VS Code extension form | OSBuilder's leverage comes from orchestrating Claude Code skills; replicating it elsewhere defeats the point. |
| Hosted multi-tenant SaaS for OSBuilder itself | Secrets-handling, per-user isolation, and abuse risk are out of scope for a personal-tool publish. |
| Building Claude Code itself or other AI-IDE substrates | Recursion. OSBuilder runs *inside* Claude Code; not the goal. |
| Re-implementing GSD / brainiac / predator / code-tester / problem-solver | Composition rule: fix the sub-skill, never fork it into OSBuilder. Avoids divergence and duplicated maintenance. |
| Multi-agent parallel execution of dev roles | DeepMind Dec 2025: 41-86.7% failure rates, 17.2× error amplification. Dev-team is **narration only**, single-threaded execution. |
| Kubernetes / microservices / service-mesh / Helm in v1 default builds | Premature-complexity traps; available only via `--production-ready` opt-in named phases. |
| Vibe-coding `package.json` / `tsconfig.json` / `pyproject.toml` from scratch | bolt.new failure mode (10M-token spaghetti). OSBuilder always uses deterministic scaffolders. |
| Auto-deploy to Vercel without explicit consent | Lovable / v0 trust loss from pricing changes. Private GitHub is the anchor; deploy is always opt-in. |
| Chocolatey as Windows-default package manager | Documented friction; winget → scoop is the recommended path. |
| Colima as macOS-default Docker runtime | OrbStack is the 2026 default for macOS; Colima only as a fallback. |
| Electron for desktop apps | Tauri 2 is 96% smaller, 50% less RAM. v1 default is Tauri; Electron not offered. |
| Public-by-default GitHub repos | OSBuilder always creates **private** repos in v1 unless explicitly overridden via `--public`. |
| Tutor mode forced on without opt-out | Risk of patronizing or noisy UX; `--quiet` always available. |

## Traceability

Each v1 requirement maps to exactly one phase. See ROADMAP.md for full phase definitions and falsifiable success criteria.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Pending |
| FOUND-05 | Phase 1 | Pending |
| PRE-01 | Phase 2 | Pending |
| PRE-02 | Phase 2 | Pending |
| PRE-03 | Phase 2 | Pending |
| PRE-04 | Phase 2 | Pending |
| PRE-05 | Phase 2 | Pending |
| PRE-06 | Phase 2 | Pending |
| PRE-07 | Phase 2 | Pending |
| IN-01 | Phase 3 | Pending |
| IN-02 | Phase 3 | Pending |
| IN-03 | Phase 3 | Pending |
| IN-04 | Phase 3 | Pending |
| IN-05 | Phase 3 | Pending |
| RES-01 | Phase 3 | Pending |
| RES-02 | Phase 3 | Pending |
| RES-03 | Phase 3 | Pending |
| RES-04 | Phase 3 | Pending |
| SCAF-01 | Phase 3 | Pending |
| SCAF-02 | Phase 7 | Pending |
| SCAF-03 | Phase 7 | Pending |
| SCAF-04 | Phase 7 | Pending |
| SCAF-05 | Phase 7 | Pending |
| SCAF-06 | Phase 3 | Pending |
| ROLE-01 | Phase 4 | Pending |
| ROLE-02 | Phase 4 | Pending |
| ROLE-03 | Phase 4 | Pending |
| ROLE-04 | Phase 4 | Pending |
| ROLE-05 | Phase 4 | Pending |
| ROLE-06 | Phase 4 | Pending |
| ROLE-07 | Phase 5 | Pending |
| ROLE-08 | Phase 4 | Pending |
| ROLE-09 | Phase 5 | Pending |
| HEAL-01 | Phase 4 | Pending |
| HEAL-02 | Phase 4 | Pending |
| HEAL-03 | Phase 4 | Pending |
| HEAL-04 | Phase 4 | Pending |
| HEAL-05 | Phase 4 | Pending |
| HEAL-06 | Phase 4 | Pending |
| HEAL-07 | Phase 4 | Pending |
| UX-01 | Phase 5 | Pending |
| UX-02 | Phase 5 | Pending |
| UX-03 | Phase 5 | Pending |
| UX-04 | Phase 5 | Pending |
| UX-05 | Phase 5 | Pending |
| VER-01 | Phase 4 | Pending |
| VER-02 | Phase 4 | Pending |
| VER-03 | Phase 4 | Pending |
| VER-04 | Phase 4 | Pending |
| SHIP-01 | Phase 6 | Pending |
| SHIP-02 | Phase 6 | Pending |
| SHIP-03 | Phase 6 | Pending |
| SHIP-04 | Phase 6 | Pending |
| SHIP-05 | Phase 6 | Pending |
| SCL-01 | Phase 6 | Pending |
| SCL-02 | Phase 6 | Pending |
| SCL-03 | Phase 6 | Pending |
| SCL-04 | Phase 6 | Pending |
| SCL-05 | Phase 6 | Pending |
| SCL-06 | Phase 6 | Pending |
| QUAL-01 | Phase 8 | Pending |
| QUAL-02 | Phase 8 | Pending |
| QUAL-03 | Phase 8 | Pending |
| QUAL-04 | Phase 8 | Pending |
| QUAL-05 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 68 total (REQUIREMENTS.md previously stated "65 total" — that header was a counting error; hand-counting every REQ-ID across the 12 categories yields 68)
- Mapped to phases: 68 (100%)
- Unmapped: 0 ✓

**Phase distribution:**
- Phase 1 (Foundation): 5
- Phase 2 (Pre-flight): 7
- Phase 3 (Intake + Research + Web playbook): 11
- Phase 4 (GSD handoff + Verify + Healing): 18
- Phase 5 (Common-person UX polish): 7
- Phase 6 (Ship + scalable defaults): 11
- Phase 7 (Additional playbooks): 4
- Phase 8 (Skill quality / publish-bar): 5

---
*Requirements defined: 2026-04-29*
*Last updated: 2026-04-29 after roadmap creation (traceability filled, count corrected to 68)*
