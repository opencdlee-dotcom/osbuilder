# OSBuilder

## What This Is

OSBuilder is a Claude Code skill that turns a description ("I want a website where students upload lab notebooks and I can grade them") into a working application — full-stack frontend + backend, pushed to a private GitHub repo, runnable on any machine. It's modeled on a small dev studio: a virtual PM, Architect, Frontend dev, Backend dev, DevOps, QA, Reviewer, and Tech Writer collaborate through Claude's existing skill ecosystem (`gsd`, `brainiac`, `predator`, `code-tester`, `problem-solver`, `gsd:debug`) to deliver, verify, and ship the app. Designed so a non-developer ("the common person") can drive the whole process by answering plain-English questions.

## Core Value

**A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.**

If anything else fails, this single promise must hold: *describe → working app on private GitHub → cloneable on any machine.*

## Requirements

### Validated

- [x] User can describe an app in plain English (paragraph or structured spec) and get a `derived_spec.md` handoff document — Validated in Phase 3 (IN-01, IN-02): `parse_paragraph()` and `parse_structured()` both write the `/gsd-new-project --auto` format
- [x] OSBuilder web-researches the right modern stack for the described app — Validated in Phase 3 (RES-01..RES-04): `stack_researcher.py` calls brainiac subprocess, returns structured JSON per component with fallback to `stack-menu.md` defaults and `--advanced` override support
- [x] OSBuilder always starts from a deterministic scaffolder — Validated in Phase 3 (SCAF-01, SCAF-06): `scaffold_web()` runs `pnpm create next-app@latest` with pinned flags; never hand-writes `package.json`
- [x] All questioning uses plain-English, outcome-framed options — Validated in Phase 3 (IN-03): `question-bank.md` passes jargon gate (no "responsive", "ORM", "framework", etc.)
- [x] Every question has an "I don't know, you decide" option — Validated in Phase 3 (IN-04): all 6 question sections in `question-bank.md` include this option

### Active

#### Core build pipeline

- [ ] User can describe an app by pointing at a reference app like `professor/` and OSBuilder takes it from there
- [ ] OSBuilder web-researches the right modern stack for the described app (no fixed default — Next.js for web, FastAPI for AI services, Tauri for desktop, etc.) ← _research validated; full GSD handoff pending Phase 4_
- [ ] OSBuilder hands off to GSD's spec → plan → execute → verify loop for actual implementation (does not reimplement what GSD already does)
- [ ] OSBuilder produces a working local app the user can run with one documented command after clone
- [ ] OSBuilder pushes the result to a **private GitHub repo** with a clone-and-run runbook in the README
- [ ] OSBuilder generates an explicit clone-on-another-machine flow that just works (env templates, install scripts, friendly preflight checks)

#### Whole-dev-team orchestration

- [ ] OSBuilder runs a virtual studio with named roles (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer), each backed by an existing skill or dedicated phase
- [ ] User-facing progress is narrated at the dev-team level ("PM is gathering requirements... ✓ / Frontend dev is building the homepage..."), not raw command output
- [ ] Every phase has a code reviewer pass (`/predator`, `/gsd-code-review`) before being marked done
- [ ] Every phase has a QA pass (`/code-tester`, `/gsd-verify-work`) with falsifiable success criteria — not "tests pass"

#### Common-person UX

- [ ] All questioning uses plain-English, outcome-framed options (e.g., "Should it work on phones too?" — never "responsive design?")
- [ ] Every question has a "I don't know, you decide" option that picks the right default
- [ ] Beginner mode is the default; `--advanced` opt-in flag exposes stack choice, deploy targets, and other technical decisions
- [ ] **Tutor mode is ON by default** — explains in plain English what just happened at each stage; `--quiet` disables
- [ ] Friendly errors with concrete next steps — never expose raw stack traces; always translate to "here's what broke and how to fix it"
- [ ] **Pre-flight installer**: detects missing prerequisites (Node, Python, git, `gh` CLI, Docker) and offers auto-install with a single confirmation prompt; works on macOS, Linux, Windows

#### Self-healing build loop

- [ ] OSBuilder classifies failures before retrying (transient / context-overflow / tool-failure / validation-failure) — no naive retry loops
- [ ] Hard cap of 3 reflections per failure (Aider's documented limit); beyond that, escalate to the user with a structured handoff (state, last error, what was tried)
- [ ] When stuck, OSBuilder delegates to `/gsd:debug` and `/problem-solver` before giving up
- [ ] OSBuilder maintains a `state.md` checkpoint (~15 lines: goal / phase / plans done / last failure) so a `/clear`'d or context-compacted session can resume mid-build

#### Scalable-by-default + production-ready upgrade path

- [ ] Default scaffold ships with: env-based config (`.env.example` + `.gitignore`'d `.env`), real database (Postgres-via-compose for multi-user web apps; SQLite only for single-user CLIs), Dockerfile, single GitHub Actions CI workflow
- [ ] **Refuses** to add Kubernetes / microservices / service-mesh / Helm in v1 unless the spec explicitly requires multi-region or multi-team — these are textbook premature-complexity traps
- [ ] `--production-ready` flag adds observability (logs/metrics/traces), automated migrations, healthchecks, secret manager, error tracking (Sentry), rate limiting, and backup strategy as **named phases** in the roadmap, not as default code

#### Skill quality (open-source publish-ready)

- [ ] SKILL.md ≤ 200 lines (progressive disclosure to `references/` for playbooks and deep details)
- [ ] Includes a clean install flow (`/osbuilder install` or one-liner) suitable for someone who's never used Claude Code skills before
- [ ] Has a generic-enough UX that someone other than Charlie can use it productively without reading source
- [ ] Ships with a README that explains the dev-team metaphor and links to a 60-second demo video
- [ ] Has a small example gallery (3–5 reference apps OSBuilder has built) under `examples/`

### Out of Scope

- **Pure deploy-to-cloud-by-default** — `/osbuilder` builds local + pushes to private GitHub, but does NOT auto-deploy to Vercel/Fly/Railway in v1. *Reason:* deploy targets are opinionated and risky; user opt-in via `--production-ready` and a separate deploy phase keeps trust intact.
- **Mobile native apps (iOS/Android)** — v1 covers web (responsive), CLI, desktop (Tauri/Electron), and services. Native mobile is a v2 scope decision. *Reason:* native mobile toolchains (Xcode signing, Android SDKs) need their own preflight + UX surface area; punting until web is solid.
- **A non-Claude Code form (standalone CLI, web UI, VS Code extension)** — OSBuilder is a Claude Code skill, period. *Reason:* the orchestration over existing skills (gsd, brainiac, predator, etc.) only works inside Claude Code; replicating it elsewhere defeats the leverage.
- **Public/multi-tenant cloud SaaS for OSBuilder itself** — OSBuilder is a tool the user installs locally; there's no hosted version. *Reason:* security, secrets-handling, and per-user isolation are out of scope for a v1 personal-tool publish.
- **Building Claude Code itself or other AI-IDE substrates** — OSBuilder runs *inside* Claude Code; it doesn't build new IDEs. *Reason:* recursion. Not the goal.
- **Re-implementing GSD, brainiac, predator, etc.** — OSBuilder orchestrates these. If functionality is missing in a sub-skill, fix the sub-skill, don't fork it into OSBuilder. *Reason:* avoid divergence and duplicated maintenance.
- **Human-in-the-loop required at every step** — OSBuilder defaults to autonomous (auto-fix on failure, auto-approve on plans) for the user's flow. Beginner mode is friendly, not chatty. *Reason:* user explicitly chose auto-fix-then-report and YOLO-style execution as their default mode.

## Context

**The user (Charlie) is the primary builder and the first audience.** Charlie already maintains a deep ecosystem of Claude Code skills under `~/.claude/skills/` (GSD framework, brainiac, raphael, predator, code-tester, problem-solver, architect-loop, kdp-publisher, canvas-lms, and many domain skills). OSBuilder is the **bootstrap layer** sitting on top of that ecosystem — its job is to take an idea and route it through the right combination of those skills to produce a shipping app.

**Inspiration: Professor Hub** (`../professor/`). Professor Hub is an umbrella workspace with a top-level `CLAUDE.md` routing table and several sub-tools (`gradehub` — Python backend with workers/queues/orchestrator/canvas-client; `LabNoteBookGrader`, `Exam grader`, `student-email-tool`). It demonstrates the kind of structure OSBuilder should be able to generate: a hub with proper FE/BE plumbing, real backend architecture, and skill-mapped workflows. OSBuilder should be able to take "build me a hub like Professor Hub for X" as a reference-style input and replicate the pattern.

**Audience expansion: "the common person."** Charlie is the first user but the explicit goal is open-source publish — OSBuilder should be usable by someone who has never written a line of code. That means plain-English questioning, outcome-framed options, friendly errors, automatic preflight installation of prerequisites, and tutor-mode-ON-by-default. This constraint shapes nearly every UX decision in the skill.

**State of the art (2026 research, see `.planning/research/`):**

- Lovable.dev / bolt.new / v0.dev show the high-water mark for "describe → deployable app" but burn 10M+ tokens for medium apps when they generate boilerplate from scratch instead of using deterministic scaffolders
- Aider's hard-cap of 3 reflection iterations is empirically validated — beyond that the model drifts instead of converging
- Anthropic's official Claude Code skill guidance: orchestrator > monolith, SKILL.md ≤ 200 lines, progressive disclosure, `state.md` for compaction survival
- GitClear's 211M-line study found 4× rise in code duplication post-AI-adoption — verification against falsifiable criteria (not "tests pass") is the differentiator that prevents this in OSBuilder-built apps
- Production self-healing pattern: classify failure type before retrying; ~94% auto-resolution achievable when paired with explicit success criteria

**Quality bar (the explicit aspiration):**
*Lovable's polish + Aider's git discipline + GSD's spec rigor + create-t3-app's deterministic scaffold,* wired as an orchestrator skill that delegates rather than reimplements.

## Constraints

- **Form**: Claude Code skill at `~/.claude/skills/osbuilder/` — never a standalone CLI or web app. — Decided in initial questioning; the orchestration leverage only works inside Claude Code.
- **Tech stack (for OSBuilder itself)**: Markdown SKILL.md + bash/Python helper scripts in `references/` and `scripts/` as needed. No long-running server, no daemon. — Skills must be installable as static files; no infrastructure.
- **Tech stack (for apps OSBuilder builds)**: Selected per-build via web research; biased toward modern defaults (Next.js + Postgres + Tailwind for web, FastAPI for AI services, Tauri for desktop). — User explicitly chose research-per-build over a fixed stack.
- **Default app shape**: Sensible-patterns scaffold (env config, real DB, Dockerfile, single CI workflow). Production-ready features are opt-in phases. — User chose "both: scalable patterns + opt-in production-ready upgrade path."
- **Failure handling**: Auto-fix mode is the default; classify failures before retrying; cap at 3 reflections; escalate with structured handoff. — User explicitly chose auto-fix-then-report; reflection cap matches Aider's empirically-validated limit.
- **Cross-platform support**: macOS, Linux, Windows for both OSBuilder itself and the preflight installer it runs. — Open-source publish target requires it.
- **Privacy**: Apps default to **private** GitHub repos; OSBuilder never publishes anything publicly without an explicit opt-in. — User specified private repos; matches "common person" trust expectations.
- **Composition rule**: If a sub-skill (gsd, brainiac, predator, etc.) is missing functionality OSBuilder needs, the fix lives in the sub-skill, not in OSBuilder. — Avoids divergence and maintenance debt.
- **No native mobile in v1**: iOS/Android native (Xcode/Swift, Android SDK/Kotlin) is excluded from v1. — Toolchain surface area is too large for the first ship; web-responsive covers most user needs.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build OSBuilder as a Claude Code skill (not CLI, not web app) | Standalone CLI would have to re-implement Claude's reasoning to do "anything end-to-end"; skill leverages existing toolbelt + skills ecosystem | — Pending |
| Always start from deterministic scaffolder (create-next-app etc.) when one exists; never hand-write boilerplate | Bolt.new / vibe-coding mode burns 10M+ tokens generating package.json from scratch and produces messy code; deterministic scaffolders are free, reproducible, idiomatic | Validated in Phase 3 (SCAF-01, SCAF-06): `pnpm create next-app@latest` with pinned flags |
| Orchestrator pattern over monolith — delegate to existing skills (gsd, brainiac, predator, code-tester, problem-solver, gsd:debug) | Anthropic's official skill guidance + 211M-line study shows duplication is the failure mode; composition is the way out | — Pending |
| Research per build (not fixed stack) | User explicit choice; matches modern best practice that picks Next.js/FastAPI/Tauri based on what's being built | Validated in Phase 3 (RES-01..RES-04): brainiac subprocess + fallback menu |
| Auto-fix mode default with 3-reflection cap, then escalate with structured handoff | Matches Aider's empirically-validated limit; production self-healing pattern requires failure classification before retry | — Pending |
| Tutor mode ON by default, `--quiet` opt-out | Audience is "common person"; explanation builds trust and teaches; power users can disable | — Pending |
| Auto-install prerequisites with single confirmation prompt | "Common person" can't be expected to know how to install Node/Docker/gh; confirmation keeps trust without blocking flow | — Pending |
| Whole-dev-team metaphor for progress narration (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer) | Non-technical users intuitively understand "QA found a bug" better than "test failed retrying"; also makes phase ownership explicit | — Pending |
| Deliverable = working local app + private GitHub repo (NOT auto-deploy to cloud) | User explicit choice; deploy targets are opinionated and risky; private GitHub is the safe v1 anchor | — Pending |
| Refuse K8s/microservices/service-mesh in v1 default builds | Premature-complexity traps; opt-in via `--production-ready` flag as named phases | — Pending |
| `state.md` checkpoint (~15 lines) updated per phase for compaction survival | Auto-compaction fires at ~98% of context; long builds need resume; matches Anthropic's recommended pattern | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-30 — Phase 3 complete: intake → stack research → scaffold loop validated*
