# Project Research Summary

**Project:** OSBuilder
**Domain:** AI-driven app-builder skill (Claude Code orchestrator)
**Researched:** 2026-04-29
**Confidence:** HIGH

## Executive Summary

OSBuilder occupies a positioning no competitor currently owns: **deterministic-scaffolder-first + Aider-grade git discipline + GSD spec rigor + Lovable-grade UX polish**, wired as a *single-threaded* orchestrator skill that delegates to Charlie's existing skill ecosystem (`gsd`, `brainiac`, `predator`, `code-tester`, `problem-solver`, `gsd-debug`) instead of reimplementing any of it. The "common person" audience constraint (non-developers, tutor-mode-on-by-default) plus the pre-flight installer is the strongest moat — no competitor in 2026 (Lovable, bolt.new, v0, Cursor, Aider, OpenHands) handles end-to-end "I have nothing installed → working app on private GitHub" without expecting a developer-grade environment.

The recommended approach is the **orchestrator-with-playbooks** pattern from Anthropic's official skill guidance: SKILL.md ≤ 200 lines holds only the role state machine + routing; per-app-type recipes (web / AI-service / desktop / CLI / hub-platform) live in `references/playbooks/*.md`; per-role briefs (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer) live in `references/roles/*.md`; helpers live in `scripts/` (Python 3.13 — bash fails on Windows, Node has the chicken-and-egg preflight problem). State persists in `<project-root>/.planning/osbuilder/state.md` (~15 lines) so a `/clear`-d or compaction-killed session can resume mid-build.

The dominant risks are well-documented: bolt.new's 10M-token spaghetti from skipping deterministic scaffolders (mitigation: always-scaffold-first, refuse to hand-write `package.json`), Aider's empirically-validated 3-reflection drift (mitigation: hard-cap retries with classified failure types and structured escalation), GitClear's 4× duplication finding from AI adoption (mitigation: every phase verifies against falsifiable criteria via `/code-tester` + `/gsd-verify-work`), and slopsquatting (20% LLM hallucination rate of package names per Socket 2025 — mitigation: registry-verification gate before any `npm install`/`pip install`, with `--ignore-scripts` until verified). **Multi-agent execution is an explicit anti-feature** — Google DeepMind's Dec 2025 study documented 41-86.7% failure rates and 17.2× error amplification in multi-agent systems vs single-agent baselines; the dev-team metaphor in OSBuilder is for *narration only*, never for parallel execution.

## Key Findings

### Recommended Stack

OSBuilder itself is built as a Claude Code skill: markdown SKILL.md + YAML frontmatter (`name`, `description`) following Anthropic's progressive-disclosure pattern, with helper scripts in Python 3.13 (preinstalled on macOS + most Linux, single `winget install` on Windows, no chicken-and-egg with the preflight installer it implements). The cross-platform preflight matrix uses `winget` (primary on Win10+/11) → `scoop` (fallback) → `choco` (last resort) on Windows; Homebrew on macOS; apt/dnf on Linux. **OrbStack is the Mac Docker default; Docker Desktop is the only viable Windows option in 2026** (no good free alternative, has licensing friction for orgs >250 employees — flag for FAQ + `--no-docker` mode for SQLite-only single-user builds).

**Core technologies (OSBuilder itself):**
- **Markdown SKILL.md + YAML frontmatter**: skill format — Anthropic's official pattern, ≤200 lines, progressive disclosure to references/
- **Python 3.13** (helpers): cross-platform reliability — bash fails Windows, Node has chicken-and-egg
- **Bootstrap shim** (POSIX `sh` + PowerShell `bootstrap.ps1`): handles the rare case where Python itself is missing
- **uv** (Astral): replaces pip + virtualenv + pyenv — 10-100× faster, single binary, pip-compatible
- **state.md markdown checkpoint** (~15 lines): compaction-resume per Anthropic Managed Agents pattern + Claude Code issue #25999
- **Failure-classifier as standalone Python script** (not embedded in SKILL.md): keeps error blobs out of context, enables unit testing, deterministic 4-class taxonomy

**Per-build defaults menu (verified Apr 2026 versions):**
- **Web apps:** Next.js 16.2.x + React 19.2 + Tailwind 4 + Drizzle ORM + Postgres 18-alpine + pnpm 10
- **AI services:** FastAPI 0.136.x + uv + Pydantic v2 + Python 3.12 baseline (no `create-fastapi-app` exists; OSBuilder ships its own template under `assets/fastapi-starter/`)
- **Desktop:** Tauri 2 (96% smaller bundle, 50% less RAM than Electron — non-negotiable in 2026)
- **CLI (single-user):** Python + Typer + Rich + SQLite
- **Hub-platform (Professor-Hub-style):** custom playbook — top-level CLAUDE.md routing table + sub-tool subdirectories (deeper research needed when this playbook is built)
- **Compose:** Docker Compose v2 with `compose.yaml` (NOT `docker-compose.yml`)

### Expected Features

Research identified **11 table stakes / 15 differentiators / 14 anti-features** across the 2025-2026 AI app-builder landscape (Lovable, bolt.new, v0, Cursor, Aider, OpenHands, GPT Engineer, MetaGPT, AutoGen, Claude Code).

**Must have (table stakes):**
- Plain-English intake (paragraph form) + structured-spec form + reference-app pointer ("build like `professor/`")
- Web research per build for stack selection (no fixed default beyond the menu above)
- Always-deterministic-scaffolder-first (`create-next-app`, `create-t3-app`, `npm create vite`, `cargo new`, etc. — never hand-write `package.json`)
- Per-phase atomic git commits (Aider pattern); `git init` in built repo on day 1
- Working local app the user can run with one documented command after clone
- Push to **private** GitHub repo with clone-and-run runbook in README
- Tutor mode ON by default (explains what just happened in plain English); `--quiet` opt-out
- Friendly errors with concrete next steps (never expose `ENOENT` / stack traces)
- Pre-flight installer with single-confirmation auto-install (Node, Python, git, gh CLI, Docker as needed)
- Outcome-framed questions ("Should it work on phones too?" — never "responsive design?")
- Beginner mode default; `--advanced` opt-in flag exposes stack choice / deploy targets

**Should have (competitive differentiators):**
- Whole-dev-team narration ("PM is gathering requirements... ✓ / Frontend dev is building the homepage..." — narration *only*, single-threaded execution)
- Self-healing build loop with classified failures (transient / context-overflow / tool-failure / validation-failure) and 3-reflection cap
- `state.md` checkpoint for compaction-resume mid-build
- Falsifiable-criteria verification per phase (every phase verified via `/code-tester` + `/gsd-verify-work` against testable success criteria, not "tests pass")
- Per-role skill delegation (PM → `/gsd-spec-phase`, Architect → `/gsd-plan-phase` + `/brainiac`, FE/BE/DevOps → `/gsd-execute-phase`, QA → `/code-tester` + `/gsd-verify-work`, Reviewer → `/predator` + `/gsd-code-review`, Tech Writer → `/gsd-docs-update`, Debug-cap → `/gsd-debug` + `/problem-solver`)
- Slopsquatting registry-verification gate before any package install
- `gh` CLI auth handling with structured error mapping
- 60-second demo video + 3-5 example gallery in `examples/`
- Reference-app intake (Repomix-style structural extraction) — v1.x after paragraph + spec validate
- Cross-platform real-machine preflight testing (macOS + Linux + Windows + WSL)
- `--production-ready` flag adds observability / Sentry / migrations / healthchecks / rate-limiting / backup as **named phases** (not default code)

**Defer (v2+):**
- Voice / sketch intake (multimodal — RapidNative, Google Stitch patterns; trend confirmed but timing TBD)
- Auto-deploy to Vercel / Fly / Railway (deliberately *not* default — opt-in via `--production-ready` + separate deploy phase)
- Native mobile (iOS/Android — toolchain surface area too large for v1)
- Hosted multi-tenant SaaS for OSBuilder itself (out of scope; secrets/isolation cost too high for personal-tool publish)

### Architecture Approach

OSBuilder uses the **orchestrator-with-playbooks** pattern (Anthropic Pattern 1+2 fused): a thin SKILL.md routing layer + role state machine + per-app-type playbooks + per-role briefs + helper scripts, all under `~/.claude/skills/osbuilder/` with one level of nesting maximum. The build pipeline is **strictly single-threaded**: Intake (PM) → Research (Architect + brainiac) → Scaffold (DevOps + scaffolder dispatch) → Plan (Architect per phase) → Build (FE / BE / DevOps per phase) → Verify (QA + Reviewer every phase) → Docs (Tech Writer) → Ship (DevOps via `gh repo create --private`). State lives in the *built app's* `.planning/osbuilder/state.md`, namespaced under GSD's existing `.planning/` directory. GSD handoff is **intake-only**: OSBuilder runs `/gsd-new-project --auto` once with a synthesized brief, then drives GSD's per-phase commands by emitting slash commands narrated through the role layer — never forks GSD's logic.

**Major components:**
1. **SKILL.md** — entry point, role state machine, routing logic (≤ 200 lines)
2. **`references/playbooks/`** — per-app-type recipes (web.md, ai-service.md, desktop.md, cli.md, hub-platform.md)
3. **`references/roles/`** — per-role briefs (pm.md, architect.md, frontend.md, backend.md, devops.md, qa.md, reviewer.md, tech-writer.md)
4. **`references/preflight/`** — per-OS install matrices (macos.md, linux.md, windows.md)
5. **`scripts/`** — Python helpers: `failure_classifier.py`, `state_writer.py`, `scaffold_dispatch.py`, `preflight_check.py`, `friendly_error.py`, `registry_verify.py`, `gh_handoff.py`, `bootstrap.sh` + `bootstrap.ps1`
6. **`assets/`** — templates for things without a third-party scaffolder (e.g., `fastapi-starter/`)
7. **`examples/`** — gallery of 3-5 reference apps OSBuilder built (validation + onboarding)
8. **`<project-root>/.planning/osbuilder/state.md`** — ~15-line live checkpoint for compaction-resume

### Critical Pitfalls

Top 5 from `PITFALLS.md` (full list of 20 with severity tags + warning signs + prevention strategy + phase mapping in source doc):

1. **bolt.new 10M-token spaghetti (CATASTROPHIC)** — vibe-coding `package.json` from scratch instead of using a deterministic scaffolder produces unmaintainable code at 10× the token cost. *Mitigation:* always-scaffold-first; OSBuilder refuses to write boilerplate the LLM doesn't need to write.
2. **Aider's 3-reflection drift (SERIOUS)** — beyond 3 retries on the same failure, the model drifts away from the goal instead of converging. *Mitigation:* hard-cap retries per failure class; structured escalation (state + last error + attempts) when cap is hit.
3. **Slopsquatting (CATASTROPHIC)** — LLMs hallucinate package names ~20% of the time (Socket 2025 study); 43% of those hallucinations recur, making them attractive squat targets. *Mitigation:* registry-verification gate before any `npm install` / `pip install`; `--ignore-scripts` until verified; gitleaks pre-commit hook.
4. **Auto-compaction destroys mid-build state (SERIOUS)** — Claude Code auto-compaction at ~98% context wipes mid-build progress. *Mitigation:* `state.md` checkpoint updated per phase + per-step; first-run-after-compaction skill code reads it back as the entry point.
5. **Multi-agent error cascade (CATASTROPHIC if attempted)** — DeepMind Dec 2025: 41-86.7% failure rates + 17.2× error amplification in multi-agent systems vs single-agent. MetaGPT/AutoGen-style "PM + Architect + Engineer + QA as separate concurrent agents" is documented to fail. *Mitigation:* dev-team metaphor is **strictly narration**; OSBuilder runs single-threaded, adopting role personas sequentially.

Honorable mentions covered in PITFALLS.md: GitClear 4× duplication (validate against falsifiable criteria), Lovable RLS CVE-2025-48757 + v0 Vercel pricing trust loss (private GitHub default + opt-in deploy), preflight system breakage (transactional install + dry-run preview + uninstall path), `.env` leakage (gitleaks pre-commit + `.gitignore` template), jargon leak (friendly-error dictionary + tutor-mode tone calibration), refuse-list (no K8s/microservices/SaaS in v1).

## Implications for Roadmap

Based on research, the suggested phase structure follows the **7-cluster build order** from ARCHITECTURE.md, refined for granularity = standard:

### Phase 1: Foundation — Skill skeleton + state plumbing
**Rationale:** Nothing else is testable without the skill installed and `state.md` working. This is the spine.
**Delivers:** `~/.claude/skills/osbuilder/SKILL.md` (≤200 lines) + directory layout + `scripts/state_writer.py` + bootstrap shims (POSIX + PowerShell) + skeleton `references/` and `scripts/` files
**Addresses:** "OSBuilder is a Claude Code skill at `~/.claude/skills/osbuilder/`" requirement; SKILL.md quality gate
**Avoids:** SKILL.md description bloat (Pitfall 8); subagent context loss (Pitfall 9 — by establishing the orchestrator pattern)
**Research flag:** No — well-documented Anthropic patterns

### Phase 2: Pre-flight installer (cross-platform)
**Rationale:** Highest-risk phase per STACK.md; must be solid before anything else can run reliably for non-developers. Strongest moat per FEATURES.md.
**Delivers:** `scripts/preflight_check.py` + `references/preflight/{macos,linux,windows}.md` + auto-install with single confirmation + dry-run preview + transactional install (rollback on failure) + uninstall path + cross-platform real-machine testing harness
**Uses:** Homebrew (macOS), apt/dnf (Linux), winget→scoop→choco (Windows); installs Node, Python, git, gh CLI, Docker (with `--no-docker` mode for SQLite-only)
**Addresses:** "Pre-flight installer" requirement; "Common-person UX" requirements
**Avoids:** Preflight system breakage (Pitfall 13)
**Research flag:** YES — Windows-without-WSL preflight UX needs hands-on validation; admin escalation prompt UX matters; Docker Desktop licensing communication

### Phase 3: Intake + Research + Scaffolder dispatch (one playbook E2E: web)
**Rationale:** Proves the loop end-to-end with one playbook before adding complexity. Web is the most-validated path.
**Delivers:** `references/playbooks/web.md` + `scripts/scaffold_dispatch.py` + intake question bank (paragraph + structured spec — reference-app deferred to v1.x) + `/brainiac` integration for stack research + outcome-framed question library + sensible-default-on-skip mechanic
**Uses:** create-next-app + Drizzle + Postgres-via-compose + Tailwind 4 + pnpm
**Addresses:** Plain-English intake; web-research per build; always-scaffold-first
**Avoids:** bolt.new 10M-token spaghetti (Pitfall 1); GitClear 4× duplication (Pitfall 2 — by deferring code generation to scaffolder + GSD)
**Research flag:** No — paths are well-documented

### Phase 4: GSD handoff + Verify loop + Failure classifier
**Rationale:** Verify-loop is the quality moat; must precede UX polish so quality is real before it's pretty. Failure classifier needs phase-level retry context.
**Delivers:** `/gsd-new-project --auto` invocation pattern + role-to-skill delegation (PM/Architect/QA/Reviewer initially) + `scripts/failure_classifier.py` (4 classes) + retry counter in `state.md` + 3-reflection cap + structured-escalation handoff schema + `scripts/registry_verify.py` (slopsquatting gate)
**Uses:** `/gsd-spec-phase`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/code-tester`, `/gsd-verify-work`, `/predator`, `/gsd-code-review`, `/gsd-debug`, `/problem-solver`
**Addresses:** Self-healing build loop requirements; falsifiable-criteria verification
**Avoids:** Aider's 3-reflection drift (Pitfall 3); naive retry burning tokens (Pitfall 11); validation-failure misclassified (Pitfall 11); slopsquatting (Pitfall 6); auto-compaction destroying state (Pitfall 7)
**Research flag:** No — Aider/DeepMind patterns are well-cited

### Phase 5: Common-person UX polish (tutor + friendly errors + dev-team narration)
**Rationale:** Verify-loop is now real; the UX polish wraps it for the "common person" audience. Order matters: ugly + correct beats pretty + broken.
**Delivers:** `references/roles/*.md` (all 8 roles wired with narration scripts) + `scripts/friendly_error.py` (error→next-step dictionary) + tutor-mode-on-by-default + `--quiet` opt-out + `--advanced` mode flag + outcome-framed-question library polish + Beginner-mode default
**Addresses:** All "Common-person UX" requirements; whole-dev-team narration
**Avoids:** Jargon leak (Pitfall 12); tutor patronizing/noisy (Pitfall 19); progress-narration confusion
**Research flag:** MEDIUM — friendly-error dictionary expands with real-world failure data from v1; tutor tone calibration needs Charlie's eye

### Phase 6: GitHub push + clone-and-run runbook
**Rationale:** Closes the build → ship loop; the explicit deliverable per Core Value.
**Delivers:** `scripts/gh_handoff.py` + `gh repo create --private` + README generator with clone-and-run runbook (includes `cd`, `cp .env.example .env`, install command, run command, verification step) + `.env` leakage guard (gitleaks pre-commit hook + `.gitignore` template) + auth-state-drift handling
**Addresses:** "Push to private GitHub" + "Clone-and-run runbook" requirements
**Avoids:** `.env` token leakage (Pitfall 15); clone-runbook missing `cd` (Pitfall 20); gh auth schism (Pitfall 15)
**Research flag:** No — gh CLI is well-documented

### Phase 7: Additional playbooks (AI-service, CLI, desktop, hub-platform)
**Rationale:** Once the web playbook proves the loop, additional playbooks are additive + low-risk + can ship in parallel waves. Hub-platform (Professor-Hub-style) gets its own deeper research because it's structurally distinct.
**Delivers:** `references/playbooks/{ai-service,cli,desktop,hub-platform}.md` + `assets/fastapi-starter/` template + Tauri 2 scaffolder integration + Typer CLI scaffolder pattern + hub-platform multi-tool umbrella pattern
**Uses:** FastAPI + uv + Pydantic v2; Tauri 2; Typer + Rich + SQLite; CLAUDE.md routing-table pattern (inspired by `../professor/`)
**Addresses:** "Anything end-to-end" scope expansion
**Avoids:** Hub-platform structural drift (needs its own research)
**Research flag:** YES for hub-platform — Professor-Hub structural inspection deserves its own phase-level research; FastAPI no-scaffolder template needs care

### Phase 8: Skill quality + Publish bar
**Rationale:** Open-source publish-ready is an explicit v1 requirement; this is the "polish + ship" phase.
**Delivers:** Examples gallery (3-5 reference apps under `examples/`) + 60-second demo video + README explaining dev-team metaphor + `install.sh` one-liner + skill-version-drift first-run validator + `--production-ready` flag implementation (observability/Sentry/migrations/healthchecks/rate-limiting/backup/secret-manager as named phases — not default code)
**Addresses:** All "Skill quality (open-source publish-ready)" requirements
**Avoids:** Skill version drift breakage; premature complexity (Pitfall 16 — by gating these as opt-in phases)
**Research flag:** YES for `--production-ready` — phase boundaries (which features bundle vs opt-in-per-feature) is a v1.x design call that benefits from phase-level research

### Phase Ordering Rationale

- **Foundation before everything** — nothing testable without skill + state plumbing
- **Preflight before intake** — non-developers can't run intake if their machine doesn't have the prereqs
- **One-playbook-E2E before more playbooks** — prove the loop before adding surface area
- **Verify-loop before UX polish** — quality before pretty (ugly + correct beats pretty + broken)
- **Ship before extra playbooks** — close the loop with one shippable build before expanding
- **Publish bar last** — examples gallery + production-ready flag presume everything else works

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Preflight installer):** Windows-without-WSL UX, admin-escalation prompts, Docker Desktop licensing communication, `--no-docker` SQLite-only flow
- **Phase 7 (Hub-platform playbook):** Direct inspection of `../professor/` structure; Repomix vs predator-driven extraction tradeoffs (also relevant for v1.x reference-app intake)
- **Phase 8 (`--production-ready` flag):** Phase-boundary decisions (observability + Sentry + healthchecks + rate-limiting + backup + secret-manager + automated migrations) — bundled vs opt-in-per-feature

Phases with standard patterns (skip phase research):
- **Phase 1 (Foundation):** Anthropic skill format is well-documented
- **Phase 3 (Intake + Web playbook):** create-next-app + Drizzle + Postgres patterns are well-known
- **Phase 4 (GSD handoff + Verify):** GSD's own surface is the user's existing toolchain
- **Phase 6 (GitHub push):** gh CLI is well-documented

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | OSBuilder helper-language verified across multiple sources; per-build defaults verified against Apr 2026 release notes |
| Features | HIGH | Multi-source competitor analysis; multi-agent failure data peer-reviewed (DeepMind + arxiv); Aider 3-cap canonical |
| Architecture | HIGH | Anthropic official docs + direct inspection of installed skill ecosystem; matches existing GSD patterns |
| Pitfalls | HIGH | Pulled from real postmortems and peer-reviewed studies; only the UX pitfalls are MEDIUM (need real-world validation) |

**Overall confidence:** HIGH

### Gaps to Address

- **Windows-without-WSL preflight UX** — needs hands-on validation in Phase 2; admin escalation prompts can derail "common person" UX. Plan: spike Windows VM + real user test before Phase 2 ships.
- **Friendly-error dictionary completeness** — v1 ships with a starter dictionary; expansion happens via real-world failure data from the first 3-5 example builds. Plan: instrument failure classifier to log unmatched errors → expand dictionary phase-over-phase.
- **Tutor-mode tone calibration** — risk of becoming patronizing or noisy; subjective. Plan: Charlie reviews tutor copy in Phase 5; opt-out always available.
- **Hub-platform playbook structural details** — deserves direct inspection of `../professor/` before its playbook is written. Plan: Phase 7 dedicates first plan to structural extraction research.
- **Skill-version-drift policy** — no formal Claude Code skill-dependency mechanism in 2026; OSBuilder ships its own first-run validator. Plan: Phase 8 includes `scripts/check_skill_versions.py`.
- **`--production-ready` phase boundaries** — bundled vs per-feature opt-in is a v1.x design call. Plan: Phase 8 first plan researches the boundary; conservative default = each feature is its own opt-in phase.

## Sources

### Primary (HIGH confidence)
- [Anthropic — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic — Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Anthropic — Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Code Subagents docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code issue #25999 — persistent state across context compaction](https://github.com/anthropics/claude-code/issues/25999)
- [Aider issue #1440 — 3-reflection limit](https://github.com/paul-gauthier/aider/issues/1440)
- [Google DeepMind multi-agent failure study (Dec 2025)](https://arxiv.org/abs/2503.13657)
- [GitClear 211M-line AI duplication study](https://www.gitclear.com/coding_on_copilot_data_shows_ais_downward_pressure_on_code_quality)
- [Socket 2025 — Slopsquatting hallucination rates](https://socket.dev/blog/slopsquatting)
- [Lovable RLS CVE-2025-48757](https://nvd.nist.gov/vuln/detail/CVE-2025-48757)
- [Next.js 16 release notes](https://nextjs.org/blog/next-16)
- [Tailwind v4 release](https://tailwindcss.com/blog/tailwindcss-v4)
- [Tauri 2 vs Electron benchmarks](https://rustify.rs/articles/rust-tauri-vs-electron-2026)
- [uv (Astral) docs](https://docs.astral.sh/uv/)

### Secondary (MEDIUM confidence)
- Anthropic skills repo examples (community pattern validation)
- pnpm vs npm vs yarn 2026 benchmarks (DEV community)
- Docker Desktop alternatives (fsck.sh 2026)
- Best Python package managers 2026 (scopir)
- Drizzle vs Prisma 2026 (makerkit)

### Tertiary (LOW confidence)
- Multimodal intake (voice/sketch) 2026 trends — confirmed direction, specific implementation TBD for v1.x
- Hub-platform structural pattern — inferred from PROJECT.md; should be re-verified at Phase 7 against `../professor/`

---
*Research completed: 2026-04-29*
*Ready for roadmap: yes*
