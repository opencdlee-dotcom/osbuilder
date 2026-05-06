# OSBuilder

## What This Is

OSBuilder is a Claude Code skill that turns a description ("I want a website where students upload lab notebooks and I can grade them") into a working application — full-stack frontend + backend, pushed to a private GitHub repo, runnable on any machine. It's modeled on a small dev studio: a virtual PM, Architect, Frontend dev, Backend dev, DevOps, QA, Reviewer, and Tech Writer collaborate through Claude's existing skill ecosystem (`gsd`, `brainiac`, `predator`, `code-tester`, `problem-solver`, `gsd:debug`) to deliver, verify, and ship the app. Designed so a non-developer ("the common person") can drive the whole process by answering plain-English questions.

## Core Value

**A non-developer describes what they want, and OSBuilder delivers a working, scalable, version-controlled app — without ever touching a command line manually or learning a framework.**

If anything else fails, this single promise must hold: *describe → working app on private GitHub → cloneable on any machine.*

## Requirements

### Validated

- [x] User can describe an app in plain English (paragraph or structured spec) and get a `derived_spec.md` handoff document — v1.0 (IN-01, IN-02): `parse_paragraph()` and `parse_structured()` both write the `/gsd-new-project --auto` format
- [x] OSBuilder web-researches the right modern stack for the described app — v1.0 (RES-01..RES-04): `stack_researcher.py` calls brainiac subprocess, returns structured JSON per component with fallback to `stack-menu.md` defaults and `--advanced` override support
- [x] OSBuilder always starts from a deterministic scaffolder — v1.0 (SCAF-01..SCAF-06): `scaffold_web/ai_service/cli/desktop/hub` all run vendored or upstream scaffolders; never hand-write `package.json`
- [x] All questioning uses plain-English, outcome-framed options — v1.0 (IN-03): `question-bank.md` passes jargon gate
- [x] Every question has an "I don't know, you decide" option — v1.0 (IN-04): all 6 question sections include this option
- [x] OSBuilder is installed as a Claude Code skill at `~/.claude/skills/osbuilder/` with valid YAML frontmatter — v1.0 (FOUND-01..05): SKILL.md 136/200 lines; 4-directory layout; bootstrap.sh + bootstrap.ps1; state_writer 10-field checkpoint
- [x] Pre-flight installer detects missing prerequisites and offers auto-install with single confirmation, works on macOS/Linux/Windows — v1.0 (PRE-01..07): 595-line `preflight_check.py` with transactional rollback, version-manager refusal, `--no-docker` mode
- [x] OSBuilder hands off to GSD's spec → plan → execute → verify loop with classified failure handling capped at 3 reflections — v1.0 (ROLE-01..09, HEAL-01..07, VER-01..04): 678-line `gsd_driver.py`; 4-class failure taxonomy; slopsquatting gate
- [x] OSBuilder runs a virtual studio with 8 named roles narrating progress — v1.0 (UX-01..05, ROLE-07, ROLE-09): 8 role briefs drive `[ROLE]` banner + `> In plain English` tutor lines; beginner mode hides tech jargon by default
- [x] Friendly errors with concrete next steps — never raw stack traces — v1.0 (UX-02, UX-05): 39-entry dictionary with `format_version: "1.0"` gate; 5 scripts wire `_fe.translate`
- [x] OSBuilder pushes the result to a private GitHub repo with a clone-and-run README runbook — v1.0 (SHIP-01..05): `gh repo create --private`; `runbook_writer.py` substitutes from template; gitleaks pre-commit hook v8.30.1
- [x] Default scaffold ships env config + real DB + Dockerfile + single CI workflow; refuses K8s/microservices/Helm in v1 — v1.0 (SCL-01..06): `compose.yaml` Postgres for multi-user web; SQLite for CLI; refuse-list with word-boundary regex; `--production-ready` adds 7 named upgrades
- [x] 4 playbooks (web, ai-service, cli, desktop) + hub-platform — v1.0 (SCAF-02..05): per-playbook scaffold mirrors `scaffold_web` shape; Electron globally refused
- [x] SKILL.md ≤ 200 lines, install one-liner, README dev-team metaphor, examples gallery, version-drift validator — v1.0 (QUAL-01..05): all 5 satisfied; demo binary deferred (waiver in 08-VERIFICATION.md)

### Active

(empty — next milestone requirements live in `.planning/REQUIREMENTS.md` after `/gsd-new-milestone`)

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

**Current state (post-v1.0):**

- Codebase: 124 deliverable files; 10,704 LOC pure-stdlib Python (incl. tests); 1,609 LOC reference Markdown.
- Tech stack: Python 3.13 helpers + Markdown SKILL.md/references + bash/PowerShell bootstrap shims.
- Test surface: 207 passed / 3 skipped (3 skips intentional and documented).
- Sub-skill minimums declared in SKILL.md `requires:` block: gsd ≥ 1.0.0, brainiac ≥ 6.0.0, predator ≥ 1.0.0, code-tester ≥ 3.1.0, problem-solver ≥ 3.0.0.
- Publish status: skill is publish-ready as a static install (`install.sh` one-liner from a GitHub repo). The 60-second demo recording is deferred per user choice; RECORDING-CHECKLIST.md is the unblock path. Live UAT across 5 phases is by-design pending and tracked in STATE.md `## Deferred Items`.

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
| Build OSBuilder as a Claude Code skill (not CLI, not web app) | Standalone CLI would have to re-implement Claude's reasoning to do "anything end-to-end"; skill leverages existing toolbelt + skills ecosystem | ✓ Good — v1.0: skill at `~/.claude/skills/osbuilder/`; SKILL.md 136/200 lines; install one-liner working |
| Always start from deterministic scaffolder when one exists; never hand-write boilerplate | Bolt.new / vibe-coding mode burns 10M+ tokens generating package.json from scratch; deterministic scaffolders are free, reproducible, idiomatic | ✓ Good — v1.0 (SCAF-01..06): web/ai-service/cli/desktop/hub all use vendored or upstream scaffolders |
| Orchestrator pattern over monolith — delegate to existing skills | Anthropic's official skill guidance + 211M-line study shows duplication is the failure mode; composition is the way out | ✓ Good — v1.0: gsd_driver delegates 7 slash commands per phase (spec/plan/execute/code-tester/verify-work/predator/code-review); no functionality duplicated |
| Research per build (not fixed stack) | Matches modern best practice that picks Next.js/FastAPI/Tauri based on what's being built | ✓ Good — v1.0 (RES-01..04): brainiac subprocess + stack-menu.md fallback; advanced overrides logged to state.md |
| Auto-fix mode default with 3-reflection cap, then escalate with structured handoff | Matches Aider's empirically-validated limit; production self-healing pattern requires failure classification before retry | ✓ Good — v1.0 (HEAL-01..07): 4-class failure_classifier; 1s→4s→16s exponential backoff; escalation to /gsd-debug then /problem-solver after 3rd retry |
| Tutor mode ON by default, `--quiet` opt-out | Audience is "common person"; explanation builds trust and teaches; power users can disable | ✓ Good — v1.0 (UX-01): `_TUTOR_ENABLED=True` default; `> In plain English: ...` after every successful step in beginner mode |
| Auto-install prerequisites with single confirmation prompt | "Common person" can't be expected to install Node/Docker/gh; confirmation keeps trust without blocking flow | ✓ Good — v1.0 (PRE-01..07): single dry-run preview + single y/n confirmation; transactional rollback on any failure |
| Whole-dev-team metaphor for progress narration (8 named roles) | Non-technical users intuitively understand "QA found a bug" better than "test failed retrying"; makes phase ownership explicit | ✓ Good — v1.0 (UX-04, ROLE-09): 8 role briefs drive `[ROLE]` banners; jargon-grep test enforces zero hits for forbidden tech tokens at runtime |
| Deliverable = working local app + private GitHub repo (NOT auto-deploy to cloud) | Deploy targets are opinionated and risky; private GitHub is the safe v1 anchor | ✓ Good — v1.0 (SHIP-01): `gh repo create --private` verified; auto-deploy explicitly out of scope |
| Refuse K8s/microservices/service-mesh in v1 default builds | Premature-complexity traps; opt-in via `--production-ready` flag as named phases | ✓ Good — v1.0 (SCL-05, SCL-06): word-boundary regex catches "kubernetes" but not "k8sFooBar"; `--production-ready` emits 7 `/gsd-add-phase` lines verbatim |
| `state.md` checkpoint (~15 lines) updated per phase for compaction survival | Auto-compaction fires at ~98% of context; long builds need resume; matches Anthropic's recommended pattern | ✓ Good — v1.0 (FOUND-05): 10-field schema; atomic os.replace writes; ALLOWED_FIELDS extended cleanly across 5 phases without breaking REQUIRED_FIELDS |
| Single-threaded execution; dev-team metaphor is narration only, never parallel agents | DeepMind Dec 2025 documented 41-86.7% multi-agent failure rates; orchestrator-with-playbooks beats actor-based competition | ✓ Good — v1.0 enforced throughout; `gsd_driver` has zero `asyncio`/`threading` for orchestration; `narration.capture_subprocess` is the only thread use (stream capture, not concurrent agents) |
| Pure-stdlib Python 3.13 for helper scripts (no third-party deps) | Cross-platform; bash fails Windows; Node has chicken-and-egg with preflight; minimizes user install friction | ✓ Good — v1.0: every script (preflight_check, state_writer, friendly_error, narration, gsd_driver, scaffold_dispatch, intake_handler, stack_researcher, gh_handoff, runbook_writer, registry_verify, failure_classifier, production_phase_writer, check_skill_md_length, check_skill_versions) is pure stdlib |

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
*Last updated: 2026-05-05 after v1.0 milestone shipped (Publish-Ready)*
