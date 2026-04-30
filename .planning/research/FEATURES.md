# Feature Research

**Domain:** AI-driven app builder skill (Claude Code orchestrator on top of an existing skill ecosystem)
**Researched:** 2026-04-29
**Confidence:** HIGH (Lovable / Bolt / v0 / Aider / Claude Code patterns directly verified; OpenHands / MetaGPT / AutoGen verified at framework-feature level)

---

## Executive Framing

The 2025-2026 AI app-builder market splits into three archetypes, and OSBuilder must position deliberately against each:

1. **Hosted "describe → deployable" tools** (Lovable, Bolt.new, v0) — strong on polish + one-click deploy, weak on long-horizon architecture, prone to 10M-token boilerplate burns, lock you into their stack and runtime.
2. **Terminal pair-programmers** (Aider, Cursor, Claude Code itself) — strong on git discipline, repo context, and self-healing within a session; weak on greenfield "scaffold from idea" intake and on common-person UX.
3. **Multi-agent dev-team frameworks** (MetaGPT, AutoGen, OpenHands, GPT Engineer / Lovable's predecessor) — strong on the role metaphor, weak on reliability — empirical 41-86.7% failure rates on multi-agent systems and 17.2x error amplification vs single-agent baselines.

**OSBuilder's lane:** orchestrator skill that **delegates** to existing skills (gsd, brainiac, predator, code-tester, problem-solver, gsd:debug) using the dev-team metaphor as a UX layer — not as a multi-agent reliability gamble. The whole-team narration is for *the user*; under the hood it's a single Claude Code session driving deterministic phases through one orchestrator.

This avoids the multi-agent error-cascade trap, gets the bolt/lovable polish via deterministic scaffolds (eliminating the 10M-token boilerplate burn), and gets Aider's git discipline by leaning on GSD's existing phase loop.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these = OSBuilder feels like a toy or a half-finished tool. Note: "common person" expectation level is the bar, not "Hacker News expectation level."

| Feature | Why Expected | Complexity | Notes / Source |
|---------|--------------|------------|----------------|
| **Plain-English intake** ("describe what you want") | Every comparable tool (Lovable, Bolt, v0, GPT Engineer, RapidNative) leads with chat-style intake; non-developers cannot use form-based or YAML intake | LOW | Map paragraph → structured spec via existing `gsd-new-project` flow. Already partially solved by GSD. |
| **Generates a working full-stack app** (not just UI) | v0's no-backend limitation is the single most-cited weakness; non-developers don't know to wire a backend separately | HIGH | Mitigated by deterministic scaffolders (`create-t3-app`, `create-next-app`, FastAPI templates) — frees Claude from generating boilerplate. |
| **Code lives in a real git repo** (not vendor sandbox) | Bolt's WebContainer and v0's hosted env are common complaints — users want to own their code; Lovable added GitHub export for exactly this reason | MEDIUM | Private GitHub push via `gh` CLI; clone-and-run runbook in README. Aligns with PROJECT.md core value. |
| **Auto-commits with sensible messages** | Aider's defining feature; Cursor 2.0 added it; users no longer accept "AI made changes I can't audit" | LOW | Conventional Commits format; weak-model commit-message generation pattern from Aider. |
| **One-command run after clone** | Universal expectation post-create-next-app; "I cloned it and it doesn't work" is the highest-frequency tooling failure | MEDIUM | `npm run dev` / `make dev` / `docker compose up` with documented prerequisite list in README. |
| **Auto-fix on failure (linter + test)** | Aider, Cursor, Lovable, Bolt all do this; running tests and not fixing failures is now a regression | MEDIUM | Wire to `code-tester` + `gsd:debug`. Cap at 3 reflections (Aider's empirical limit) — beyond that, drift > convergence. |
| **Secrets in `.env`, never committed** | Lovable security incident exposed 170 production apps with auth flaws; this is now a compliance baseline expectation | LOW | `.env.example` + `.gitignore`'d `.env` template ships with every scaffold. |
| **Error messages translated to actionable next steps** | "Common person" cannot read stack traces; every modern dev tool now has friendly errors (npm, Docker, Vercel) | MEDIUM | Friendly-error layer over child process output. Map common errors to fixes. Tied to tutor mode. |
| **Live progress indication during long builds** | Bolt ~30s, Lovable ~60s with plan-first UX — users tolerate slow only if they see what's happening | LOW | Dev-team-metaphor narration ("Architect is choosing the stack..." "Backend dev wired the database..."). |
| **README with setup instructions** | Every scaffolder generates one; non-developer specifically needs it because they will hand the repo to someone else | LOW | Generated as part of Tech Writer phase. |
| **Failure recovery without losing work** | Cursor 2.0 background agents, Claude Code session resume, Aider git rollback — context loss is the #1 trust-breaker | MEDIUM | `state.md` checkpoint pattern (~15 lines) per phase; survives `/clear` and auto-compaction. |

---

### Differentiators (Competitive Advantage)

These are where OSBuilder competes — features that align with the stated quality bar: *Lovable's polish + Aider's git discipline + GSD's spec rigor + create-t3-app's deterministic scaffold.*

| Feature | Value Proposition | Complexity | Notes / Citation |
|---------|-------------------|------------|------------------|
| **Deterministic scaffolder-first** (never hand-write `package.json`) | Eliminates the 10M-token boilerplate burn that founders complain about with Bolt; produces idiomatic, reproducible, maintained code; sidesteps the "vibe-coded auth has 40-45% vulnerability rate" finding | LOW | `create-t3-app`, `create-next-app`, `npm create vite`, `cargo new`, `poetry new`, FastAPI cookiecutter. **Highest-leverage differentiator** because every other tool gets this wrong. |
| **Reference-app intake** (point at a real repo: "build me a hub like `professor/`") | No competing tool does this well; closest is Repomix-as-context, but no AI app builder ingests "build LIKE this" pattern; matches PROJECT.md's Professor Hub use case | HIGH | Use Repomix or `gh repo clone` + structural analysis; extract patterns (top-level CLAUDE.md, FE/BE boundary, queue/worker shape). Pairs with `predator` for repo extraction. |
| **Whole-dev-team progress narration** ("PM is gathering requirements ✓ / Architect chose Next.js because... / Frontend dev is building the homepage...") | Transforms opaque AI output into a story non-developers can follow; teaches them what dev work looks like; turns waiting time into trust-building | MEDIUM | Narration layer; dev-team roles map to existing skills (PM=`gsd-new-project`, Architect=`brainiac`+`gsd-roadmap`, Frontend/Backend=`architect-loop`, QA=`code-tester`, Reviewer=`predator`/`gsd-code-review`, Tech Writer=README phase). |
| **Tutor mode ON by default** (explains in plain English what just happened at each stage) | Lovable has interactive tutorial outputs but no tool teaches the user *while building their app*; this is OSBuilder's audience-defining feature | MEDIUM | Per-phase 1-2 sentence "what just happened in plain English" output; `--quiet` opt-out; ties directly into progress narration. **Depends on progress narration.** |
| **Failure-classification before retry** (transient / context-overflow / tool-failure / validation-failure → different handling) | Aider naively retries 3x on edit-format errors and stops; production self-healing patterns require classify-first; ~94% auto-resolution achievable when paired with falsifiable success criteria | MEDIUM | Maps to PROJECT.md "self-healing build loop" requirement. Classifier is a small prompt → category → routing decision. |
| **Falsifiable success criteria per phase** (not "tests pass" but "user can sign up, log in, and see their dashboard at /dashboard") | GitClear's 211M-line study found 4× rise in code duplication post-AI; verification against falsifiable criteria is the prevention | MEDIUM | `gsd-verify-work` already does this. OSBuilder enforces it as a hard gate per phase. |
| **Pre-flight installer** (auto-detects + offers to install Node, Python, git, `gh`, Docker; cross-platform) | No AI app builder does this — they all assume prerequisites exist; non-developers crash here | HIGH | Per-OS detection scripts; one-line install via `brew`/`apt`/`winget`/`scoop`/`nvm`/`pyenv`; single confirmation prompt. **OSBuilder-specific moat for "common person" audience.** |
| **Outcome-framed questioning with "you decide" defaults** ("Should it work on phones?" not "responsive design?"; every question has "I don't know, you decide") | Lovable's Chat Mode is the closest; Bolt and v0 dump technical questions; matches PROJECT.md UX requirements | LOW | Question-bank pattern with default-picker fallback; ties to beginner mode. |
| **`state.md` compaction-survival checkpoint** (~15 lines: goal / phase / plans done / last failure) | Auto-compaction fires at ~98% context; long builds need resume; competing tools either don't survive or lose progress detail | LOW | Updated per phase; OpenClaw and Anthropic's own `12 Production AI Agent Primitives` validate this pattern. |
| **Hard 3-reflection cap with structured escalation** (state, last error, what was tried) | Aider's empirically-validated limit; beyond 3, models drift instead of converging; the escalation handoff is what makes it usable | LOW | Cap is mechanical; the value is the *structured handoff* format ("here's what we tried, here's what failed, here's where I'm stuck"). |
| **Sensible-by-default app shape** (env config + real DB + Dockerfile + single CI workflow); refuses K8s/microservices/service-mesh in v1 | Bolt and Lovable will happily over-engineer; "premature complexity" is a recognized failure mode in the post-mortems | MEDIUM | Hard refusal in default mode with clear explanation; `--production-ready` opens the door to observability/Sentry/secrets-manager **as named phases**, not as default code. |
| **Composes existing skills, doesn't reimplement** (gsd, brainiac, predator, code-tester, problem-solver, gsd:debug) | Anthropic's official skill guidance: orchestrator > monolith; OSBuilder has unique leverage here because Charlie's ecosystem already exists | MEDIUM | SKILL.md ≤ 200 lines; progressive disclosure to `references/`; the orchestration is the product. |
| **Auto-fix-then-report mode** (no chatty step-by-step approval — autonomous within phase, reports outcomes) | User explicitly chose this; aligns with "auto mode" in modern Claude Code; differentiates from approval-heavy frameworks like MetaGPT | LOW | Default behavior; phase boundaries are the natural pause points. |
| **Private-by-default GitHub repo** (never publishes anything publicly without explicit opt-in) | Lovable defaults to public-shareable; Bolt's WebContainer leaks deployments (the "hidden Netlify deployment nobody asked for" complaint); private-by-default is a trust signal for non-developers | LOW | `gh repo create --private`; explicit `--public` flag required to override. |
| **3-5 example gallery + dev-team metaphor in README** | Lovable, Bolt, GPT Engineer all lead with examples; the metaphor + examples reduce cognitive load for first-time users | LOW | Examples directory + 60-second demo video link; aligns with PROJECT.md skill-quality requirements. |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that look obvious but hurt OSBuilder's positioning. The "why we won't" matters as much as "what we will."

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Vibe-coding-from-scratch** (generating `package.json`, `tsconfig`, framework boilerplate token-by-token) | Looks impressive in demos; Bolt and Lovable do it | Founders report 10M-token burns on medium apps; produces non-idiomatic code that drifts from framework conventions; 40-45% vulnerability rate in vibe-coded code; can't be maintained by next AI session | **Always-scaffold-first**. If a deterministic scaffolder exists, run it. Customization happens *after* the scaffold, never before. |
| **Auto-deploy to Vercel/Fly/Railway by default** | Lovable/Bolt/v0 all have one-click deploy; "more polished" feel | Deploy targets are opinionated and risky; environment secrets, billing, domain ownership all become OSBuilder's problem; private-deploy != private repo | **Private GitHub repo + explicit `--production-ready` deploy phase** (named, opt-in, with user confirmation per target). Already in PROJECT.md Out of Scope. |
| **Multi-agent system with parallel agents** (PM, Architect, Frontend etc. as actual separate agent processes) | Looks like the dev-team metaphor; MetaGPT and AutoGen do it | Empirical 41-86.7% failure rates; 17.2x error amplification vs single-agent; star-topology hub-corruption causes total system failure; AutoGen has documented premature-termination bugs in cycle tracking | **Single orchestrator + named phases with role-flavored narration.** Dev-team is a UX metaphor, not an architecture. The reliability comes from sequential phases with verification gates. |
| **Building Claude Code itself / new IDE substrate** | "Why not make it standalone so anyone can use it?" | OSBuilder's leverage is the existing skill ecosystem (gsd, brainiac, predator, etc.); replicating the orchestration outside Claude Code defeats the whole premise; recursion trap | **Stay a Claude Code skill.** Already in PROJECT.md Out of Scope. |
| **Hosted multi-tenant SaaS version of OSBuilder** | Distribution play; what Lovable/Bolt do | Security, secrets-handling, per-user isolation are out of scope for v1; non-trivial infra; competes with the open-source-publish goal | **Local install only**, open-source skill at `~/.claude/skills/osbuilder/`. |
| **Native mobile (iOS/Android) builds** | Users will ask; v0 and Lovable hint at it | Xcode signing, Android SDK, App Store review processes — each its own preflight + UX surface; v1 cannot absorb this | **v1 = web (responsive) + CLI + desktop (Tauri/Electron) + services.** Native mobile = v2 scope decision. |
| **Generic "any language any framework" support** | Sounds powerful | The deterministic-scaffolder advantage requires deep per-stack knowledge; generic = mediocre everywhere | **Curated stack list with deep support** (Next.js, FastAPI, Tauri, T3, Vite, Cargo) and "research adds new ones as needed via brainiac" rather than claiming universal support. |
| **Human-in-the-loop approval at every step** | "Safer feeling"; what enterprise-y AI app builders advertise | User explicitly chose autonomous-with-escalation; chatty approval breaks flow for the common-person audience; phase boundaries are sufficient checkpoints | **Auto-fix-then-report mode** with phase-boundary review; structured escalation only when the 3-reflection cap is hit. |
| **Building inside Bolt-style WebContainer / browser sandbox** | Looks slick; zero local setup | The whole point of OSBuilder is real local repo + clone-and-run-on-any-machine; sandbox approach undermines the core value | **Local filesystem + real git + real `gh` CLI**, with preflight installer to make local setup painless. |
| **AI-generated authentication from scratch** | Every app needs auth | Lovable security incident proved this exposes apps; auth has token rotation, rate limiting, RBAC, session handling that LLMs reliably get wrong | **Use scaffold-bundled auth** (NextAuth/Auth.js for T3, FastAPI-Users for FastAPI, Supabase Auth for full-stack) — never roll auth from prompts. |
| **Forking/owning gsd, brainiac, predator code** | "Easier to ship if everything's in one place" | Divergence and duplicated maintenance; PROJECT.md composition rule; killed Lovable's GPT Engineer ancestor's velocity | **If a sub-skill is missing functionality, fix the sub-skill.** OSBuilder only contains orchestration code. |
| **Real-time multi-user collaboration on a build** | Lovable advertises it; "modern feeling" | Common-person audience builds alone; collaboration is a v2+ concern; complicates state.md / git semantics enormously | **Single-user builds with private GitHub repos.** Collaboration is what GitHub already provides post-build. |
| **A "fix everything" super-prompt** that bypasses the phase loop | "Just make it work" — what users will ask for at frustration moments | Naive retry loops; produces drift; what the 3-reflection cap exists to prevent | **Structured escalation with `gsd:debug` + `problem-solver`** when phases legitimately fail; not a magic fix-all. |
| **Visual drag-drop builder UI** | What no-code tools have; "more accessible" | OSBuilder is a Claude Code skill — there is no GUI surface; building one is the standalone-CLI / IDE-substrate trap | **Plain-English questioning + tutor mode + dev-team narration in chat.** That's the UI. |

---

## Feature Dependencies

```
Plain-English intake
    └──feeds──> Outcome-framed questioning
                      └──feeds──> Spec (gsd-new-project)
                                       └──feeds──> Roadmap (gsd-roadmap + brainiac research)
                                                        └──feeds──> Architect: stack selection (research-driven)
                                                                          └──requires──> Deterministic scaffolder catalog
                                                                                              └──feeds──> Sensible-by-default app shape
                                                                                                                └──feeds──> Phase loop (architect-loop)
                                                                                                                                  └──gated by──> Falsifiable success criteria + Reviewer pass + QA pass
                                                                                                                                                       └──recovers via──> Failure classification + 3-reflection cap + structured escalation

Reference-app intake (alternative path)
    └──requires──> Repomix or gh repo clone + structural analysis
                          └──feeds──> Spec (with patterns extracted)
                                            └──merges into──> Roadmap

Tutor mode
    └──requires──> Whole-dev-team progress narration (the events are what tutor mode explains)
                          └──requires──> Phase boundaries with named owners

Pre-flight installer
    └──independent of build pipeline──> Runs before any phase starts
                                                    └──requires──> Cross-platform detection scripts
                                                                          └──enables──> Common-person UX guarantee

state.md checkpoint
    └──updated by──> Every phase transition
                          └──enables──> Resume after /clear or auto-compaction

GitHub push
    └──requires──> gh CLI (covered by preflight)
                          └──requires──> Private-by-default flag
                                                └──enables──> Clone-and-run runbook

Auto-fix-then-report mode
    └──conflicts with──> Human-in-the-loop approval at every step (anti-feature)
    └──enabled by──> Failure classification + 3-reflection cap (without these, autonomy is dangerous)

Whole-dev-team narration (UX layer)
    └──conflicts with──> Multi-agent parallel execution (anti-feature)
    └──implementation──> Single orchestrator with role-flavored output, NOT separate agents
```

### Dependency Notes

- **Tutor mode requires progress narration:** tutor mode's content is "explain what just happened" — the events being explained are produced by the dev-team narration. Build narration first, layer tutor mode on top.
- **Auto-fix mode requires failure classification:** Aider's "naive 3-retry then stop" loses too much work; failure classification is what makes autonomy safe.
- **Reference-app intake requires extraction tooling:** Repomix or `predator`-style structural extraction; this is the higher-complexity intake path and should be v1.x not strict v1.
- **Deterministic scaffolder catalog is a foundation requirement:** every other build feature assumes "we never hand-write boilerplate"; without this, the entire value prop collapses into bolt-style token burn.
- **`state.md` is independent but ubiquitous:** every phase writes it; doesn't depend on anything else, but everything else depends on it surviving compaction.
- **Pre-flight installer is independent of the build pipeline** — it runs once at install time + on each new project, doesn't gate on anything else, and is the **most common-person-critical** feature for first-run trust.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate "describe → working app on private GitHub → cloneable on any machine" for a non-developer.

- [ ] **Plain-English intake** (paragraph + structured spec) — without this there is no product
- [ ] **Outcome-framed questioning with "you decide" defaults** — common-person UX baseline
- [ ] **Stack research per build** (brainiac-driven) — PROJECT.md explicit requirement
- [ ] **Deterministic scaffolder-first** for top stacks (Next.js, T3, FastAPI, Tauri, Vite, Cargo) — eliminates token burn
- [ ] **Hand-off to GSD's spec → plan → execute → verify loop** — orchestrator pattern; doesn't reimplement
- [ ] **Sensible-by-default scaffold** (env, real DB, Dockerfile, one CI workflow) — production-ready opt-in only
- [ ] **Whole-dev-team progress narration** with named roles — the differentiating UX
- [ ] **Tutor mode ON by default** — common-person audience requirement
- [ ] **Friendly errors** with concrete next steps — common-person trust requirement
- [ ] **Pre-flight installer** for Node, Python, git, `gh`, Docker (macOS + Linux + Windows) — first-run trust
- [ ] **Auto-fix-then-report with failure classification + 3-reflection cap + structured escalation** — self-healing without drift
- [ ] **Private GitHub repo push** with clone-and-run runbook in README — core deliverable
- [ ] **`state.md` compaction-survival checkpoint** — long-build viability
- [ ] **`--advanced` flag** for stack choice + technical decisions — power-user opt-in
- [ ] **`--quiet` flag** for tutor mode opt-out — power-user opt-in
- [ ] **SKILL.md ≤ 200 lines + progressive disclosure to `references/`** — Anthropic skill guidance
- [ ] **3-5 example gallery + 60s demo video** — discoverability + first-impression

### Add After Validation (v1.x)

Features to add once core is working and "common person" feedback is in.

- [ ] **Reference-app intake** ("build me a hub like `professor/`") — high-value but high-complexity intake path; ship v1 with paragraph + spec, add reference-pointer once those are stable
- [ ] **`--production-ready` flag with named phases** for observability, Sentry, secrets-manager, healthchecks, rate-limiting, backup — opt-in production upgrade
- [ ] **Multi-language polish** — v1 is English-first; localized question banks come after validation
- [ ] **Voice intake** — multimodal input (RapidNative, Plivo) is a 2026 trend but not a v1 requirement; chat works
- [ ] **Sketch / image intake** — Google Stitch / RapidNative do this; v1.x add via Claude's vision once paragraph intake is solid
- [ ] **Skill version pinning** — once gsd / brainiac / predator have multiple stable versions, OSBuilder pins for reproducibility
- [ ] **Build replay from `state.md`** — given a state file, re-run the build deterministically; valuable for debugging Charlie-side, becomes a feature later

### Future Consideration (v2+)

- [ ] **Native mobile builds (iOS/Android)** — toolchain surface area too large for v1; Out of Scope per PROJECT.md
- [ ] **Cloud-deploy phase as named opt-in** (Vercel/Fly/Railway with explicit confirmation per target) — beyond `--production-ready` flag; full deploy automation
- [ ] **Multi-user / team-collab builds** — single-user is the v1 audience
- [ ] **Visual progress dashboard** — chat narration is the v1 UI; a real dashboard requires non-Claude-Code surface area, which is Out of Scope
- [ ] **Hosted SaaS version** — Out of Scope per PROJECT.md
- [ ] **Public marketplace of OSBuilder-generated apps** — distribution play; not before v1 validates

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Plain-English intake | HIGH | LOW (GSD already does this) | P1 |
| Deterministic scaffolder-first | HIGH | LOW (it's just `npx create-...`) | P1 |
| Hand-off to GSD phase loop | HIGH | LOW (orchestrator wiring) | P1 |
| Whole-dev-team progress narration | HIGH | MEDIUM (narration layer + role mapping) | P1 |
| Tutor mode (default ON) | HIGH | MEDIUM (depends on narration) | P1 |
| Friendly error translation | HIGH | MEDIUM (error map + fallback) | P1 |
| Pre-flight installer | HIGH | HIGH (cross-platform, multi-tool detection) | P1 |
| Failure classification + 3-reflection cap | HIGH | MEDIUM (classifier prompt + routing) | P1 |
| Private GitHub repo push | HIGH | LOW (`gh repo create --private`) | P1 |
| `state.md` checkpoint | HIGH | LOW (15-line markdown writer) | P1 |
| Outcome-framed questioning | HIGH | LOW (question-bank pattern) | P1 |
| Falsifiable success criteria per phase | HIGH | LOW (gsd-verify-work already does it) | P1 |
| Sensible-by-default scaffold shape | HIGH | LOW (template choices) | P1 |
| Refuses K8s/microservices in default mode | MEDIUM | LOW (just say no) | P1 |
| Auto-commits with sensible messages | MEDIUM | LOW (Aider pattern; weak-model commit msg) | P1 |
| `--advanced` and `--quiet` flags | MEDIUM | LOW (flag handling) | P1 |
| 3-5 example gallery + demo video | MEDIUM | MEDIUM (build the examples) | P1 |
| Reference-app intake | HIGH | HIGH (Repomix + structural analysis + pattern matching) | P2 |
| `--production-ready` named phases | MEDIUM | MEDIUM (phase definitions + per-feature templates) | P2 |
| Build replay from state.md | LOW | MEDIUM | P3 |
| Voice intake | LOW | MEDIUM (Claude voice + Whisper) | P3 |
| Sketch/image intake | MEDIUM | MEDIUM (Claude vision) | P3 |
| Native mobile | HIGH (eventual) | HIGH (toolchain) | P3 (v2) |
| Cloud auto-deploy | MEDIUM | HIGH (per-target trust + secrets) | P3 (v2) |

**Priority key:**
- P1: Must have for v1 launch (validates the core promise)
- P2: Should have, add post-v1 once core is validated
- P3: Defer until product-market fit / explicitly requested by users

---

## Competitor Feature Analysis

| Feature | Lovable.dev | Bolt.new | v0.dev | Cursor | Aider | OpenHands | MetaGPT | GPT Engineer | Claude Code | **OSBuilder** |
|---------|-------------|----------|--------|--------|-------|-----------|---------|--------------|-------------|---------------|
| Intake | Chat (Plan-first) | Chat (one-shot) | Component spec / Figma | IDE prompt | CLI prompt | CLI / GUI | YAML / spec | Chat + sketch | Chat | **Chat + spec + reference-app (v1.x)** |
| Stack selection | Fixed (React + Supabase) | User-picked, browser-sandboxed | Fixed (React + Tailwind) | User picks | User picks | User picks | Configurable | Fixed (React + shadcn) | User picks | **Research-per-build (brainiac)** |
| Scaffolder-first? | No (vibe-codes) | No (vibe-codes) | No (component-only) | N/A (edits existing) | N/A | No | No | No | N/A | **Yes (deterministic always)** |
| Build orchestration | Single chat thread | Single chat thread | Single chat thread | Composer agent | Reflection loop | Multi-agent | Multi-agent (PM+Arch+Eng+QA) | Multi-agent (predecessor of Lovable) | Sub-agents + skills | **Single orchestrator + dev-team narration** |
| Self-healing | Auto-fix on lint/test | Auto-fix on error | Manual | Background agents | 3-reflection cap | Multi-agent retry | Multi-agent retry | Multi-agent retry | Hooks + skills | **Classify-then-route + 3-reflection cap + escalate** |
| Failure escalation | None (user re-prompts) | None | None | None | Stops at 3 | Cascade-prone | Cascade-prone | Cascade-prone | Manual | **Structured handoff (state, error, attempts) → user** |
| Common-person UX | Strong (Plan + Chat Mode) | Medium | Weak (developer-targeted) | Weak | None (CLI) | Weak | Weak | Medium | None | **Strong (tutor + outcome-framed + dev-team narration)** |
| Plain-English errors | Partial | Partial | Partial | None | None | None | None | Partial | None | **Yes (mapped + tutor explains)** |
| Pre-flight installer | N/A (hosted) | N/A (hosted) | N/A (hosted) | None | None | Manual | Manual | Manual | None | **Yes (Node/Python/git/gh/Docker, cross-OS)** |
| Output | Hosted Lovable URL + GitHub export | WebContainer + GitHub export | Component code + GitHub | Local IDE | Local repo | Local repo | Local repo | Local repo + GitHub + deploy | Local repo | **Local repo + private GitHub (default)** |
| Auto-deploy | One-click (Lovable / Vercel) | One-click (Netlify visible by default) | Vercel | None | None | None | None | One-click | None | **No (opt-in via `--production-ready` only)** |
| Git discipline | GitHub export | GitHub export | GitHub export | Manual | **Auto-commit per change** | Auto | Auto | GitHub | Manual | **Auto-commit per phase (Aider pattern)** |
| Compaction survival | N/A (short builds) | N/A | N/A | Background agents | Session-bound | Session-bound | Session-bound | Session-bound | Hooks + memory | **`state.md` per phase + auto-resume** |
| Reflection cap | None visible | None visible | None visible | None | **3 (empirical)** | None visible | None visible | None | None | **3 + classified escalation** |
| Scaffold shape | Supabase + React | User chooses | React + Tailwind only | N/A | N/A | User chooses | User chooses | React + shadcn + Vite | N/A | **Sensible defaults + opt-in production-ready** |
| Refuses K8s/microservices in default? | N/A | No (will build it) | N/A | No | No | No | No | No | No | **Yes (explicit refusal in v1)** |
| Reference-app intake | No | No | No | Limited (file context) | Repo as context | Repo as context | No | No | Repo as context | **Yes — "build like X" pattern (v1.x)** |

**Key takeaways from competitor matrix:**
- **No competitor combines deterministic scaffolding + dev-team UX + Aider-grade git discipline + GSD spec rigor.** OSBuilder's positioning is the union, not any one of these.
- **Pre-flight installer is OSBuilder's strongest moat** — every hosted tool sidesteps it (because their environment is fixed); every CLI tool ignores it (because their audience is developers). OSBuilder's "common person" audience makes this table-stakes for *its* market while being unique in the broader space.
- **Multi-agent dev teams (MetaGPT, OpenHands, AutoGen, GPT Engineer's predecessor pattern) are the wrong abstraction at the implementation layer** — empirical reliability data shows error cascades, premature termination, hub-corruption topologies. Use the metaphor as UX, not as architecture.
- **Aider's reflection cap is empirically validated** — anything past 3 is drift, not convergence. OSBuilder adopts the cap and adds the structured-escalation handoff Aider lacks.

---

## Mapping to OSBuilder's Dev-Team Roles

The whole-dev-team metaphor is a **UX narration layer**, not an agent topology. Here's how each role maps to existing skills + the user-facing narration pattern:

| Role | Maps to (existing skill) | User-facing narration | Phase output |
|------|--------------------------|------------------------|--------------|
| **PM (Product Manager)** | `gsd-new-project` | "PM is gathering requirements..." → "PM understood: a grading hub for student lab notebooks." | `.planning/PROJECT.md` |
| **Architect** | `brainiac` (research) + `gsd-roadmap` (planning) | "Architect is researching the right stack..." → "Architect chose Next.js + Postgres because..." | `.planning/ROADMAP.md` + STACK decision |
| **Frontend Dev** | `architect-loop` (run mode, scoped to FE phase) | "Frontend dev is building the homepage..." → "Frontend dev shipped homepage + nav." | Frontend code + commit |
| **Backend Dev** | `architect-loop` (run mode, scoped to BE phase) | "Backend dev is wiring the database..." → "Backend dev shipped auth + user table." | Backend code + commit |
| **DevOps** | `architect-loop` (scoped to infra phase) | "DevOps is setting up CI..." → "DevOps wired Dockerfile + GitHub Actions." | Dockerfile, `.github/workflows/`, commit |
| **QA** | `code-tester` + `gsd-verify-work` | "QA is testing the signup flow..." → "QA verified: signup works end-to-end." | Test results + falsifiable verification |
| **Reviewer** | `predator` (hunt) + `gsd-code-review` | "Reviewer is checking the auth code..." → "Reviewer flagged: missing rate limiting on `/login`." | Review report; gates phase completion |
| **Tech Writer** | Final phase (README + clone-and-run runbook) | "Tech Writer is writing the setup guide..." → "Tech Writer shipped README + runbook." | README, runbook, env templates |
| **(Escalator, when stuck)** | `gsd:debug` + `problem-solver` | "We're stuck on database migration — let me dig in..." → structured handoff if still failing | `state.md` updated with failure detail; user prompted with options |

**Implementation rule:** No role runs as a parallel agent. The orchestrator (OSBuilder skill) calls the underlying skill in sequence, swaps the narration label, and produces the phase output. The metaphor lives in *output formatting*, not in *execution topology*. This sidesteps the documented multi-agent failure modes (17.2x error amplification, 41-86.7% failure rates).

---

## Sources

**Comparison products (verified directly):**
- [Lovable vs Bolt vs v0: AI App Builder Comparison](https://lovable.dev/guides/lovable-vs-bolt-vs-v0)
- [V0 vs Bolt.new vs Lovable 2026 (NxCode)](https://www.nxcode.io/resources/news/v0-vs-bolt-vs-lovable-ai-app-builder-comparison-2025)
- [Best AI App Builders in 2026: Top 6 Tools Compared (Lovable)](https://lovable.dev/guides/best-ai-app-builders)
- [Lovable vs Bolt vs v0: What Your Code Looks Like (TECHSY)](https://techsy.io/en/blog/lovable-vs-bolt-vs-v0)
- [Best AI Code Editors in 2026 (MindStudio)](https://www.mindstudio.ai/blog/best-ai-code-editors)
- [Bolt.new Review 2026: Limits of the AI App Builder](https://uxmagic.ai/blog/bolt-new-review-2026-ai-app-builder-limits)
- [Vibe Coding Pitfalls — 7 Ways Your AI Built App Breaks After Launch](https://www.clixlogix.com/vibe-coding-pitfalls-7-ways-your-ai-built-app-breaks-after-launch/)
- [Cursor 2.0 announcement](https://cursor.com/blog/2-0)
- [Cursor 3.0 announcement](https://cursor.com/blog/cursor-3)
- [GPT Engineer / Lovable's predecessor (GitHub)](https://github.com/AntonOsika/gpt-engineer)
- [GPT Engineer App](https://gptengineer.app/)
- [OpenHands](https://openhands.dev/)
- [MetaGPT (GitHub)](https://github.com/FoundationAgents/MetaGPT)
- [v0 by Vercel](https://v0.app/)
- [Buildra (one-click GitHub + Vercel pattern)](https://buildra.dev/)
- [RapidNative — multimodal intake reference](https://www.rapidnative.com/blogs/best-ai-app-builder)
- [Top 8 Open-Source Coding Agents in 2026](https://www.opensourceaireview.com/blog/top-8-open-source-coding-agents-in-2026)

**Aider git discipline + reflection cap:**
- [Aider Linting and Testing Documentation](https://aider.chat/docs/usage/lint-test.html)
- [Aider Git Integration Documentation](https://aider.chat/docs/git.html)
- [Aider Issue #1440 — "Only 3 reflections allowed, stopping"](https://github.com/paul-gauthier/aider/issues/1440)
- [Aider Options Reference](https://aider.chat/docs/config/options.html)

**Multi-agent failure data (anti-feature justification):**
- [Why Do Multi-Agent LLM Systems Fail? (arxiv 2503.13657)](https://arxiv.org/pdf/2503.13657)
- [The Multi-Agent Trap (Towards Data Science)](https://towardsdatascience.com/the-multi-agent-trap/)
- [The Multi-Agent Reckoning (April 2026)](https://medium.com/@Micheal-Lanham/the-multi-agent-reckoning-two-papers-that-challenge-everything-you-assumed-7a8834b49b8d)
- [Multi-Agent System Reliability — Failure Patterns (Maxim)](https://www.getmaxim.ai/articles/multi-agent-system-reliability-failure-patterns-root-causes-and-production-validation-strategies/)
- [Dissecting Bug Triggers in Modern Agentic Frameworks (arxiv)](https://arxiv.org/html/2604.08906)
- [9 Critical Failure Patterns of Coding Agents (Columbia DAPLab)](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html)

**Self-healing + failure classification patterns:**
- [Mastering Retry Logic Agents — 2025 Best Practices (Sparkco)](https://sparkco.ai/blog/mastering-retry-logic-agents-a-deep-dive-into-2025-best-practices)
- [Error Recovery and Fallback Strategies in AI Agent Development (GoCodeo)](https://www.gocodeo.com/post/error-recovery-and-fallback-strategies-in-ai-agent-development)
- [LLM Error Handling and Fallback Strategies for Production](https://www.buildmvpfast.com/blog/building-with-unreliable-ai-error-handling-fallback-strategies-2026)
- [Why AI-Generated Code Fails — 7 Smart Fixes](https://www.progressiverobot.com/2026/04/25/ai-generated-code-fails-fixes/)

**Claude Code skill orchestration patterns:**
- [Extend Claude with skills (official Claude Code docs)](https://code.claude.com/docs/en/skills)
- [Agent Skills (Claude API docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Code: Hooks, Subagents, and Skills — Complete Guide (ofox.ai 2026)](https://ofox.ai/blog/claude-code-hooks-subagents-skills-complete-guide-2026/)
- [Multi-agent orchestration for Claude Code in 2026 (Shipyard)](https://shipyard.build/blog/claude-code-multi-agent/)
- [Beyond One-Shot Prompts — 5 Claude Code Workflow Patterns (MindStudio)](https://www.mindstudio.ai/blog/claude-code-agentic-workflow-patterns)
- [gstack: virtual dev team for Claude Code](https://aibuilderhub.dev/en/blog/gstack-claude-code-workflow)
- [Claude Skills Comprehensive Guide 2026 (Anandbg)](https://anandbg.com/blog/claude-skills-comprehensive-guide-2026)

**Compaction survival / state.md pattern:**
- [Persistent state across context compaction (claude-code issue #25999)](https://github.com/anthropics/claude-code/issues/25999)
- [Context Compaction Research — Claude Code, Codex CLI, OpenCode, Amp](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f)
- [Surviving Context Compaction (OpenClaw)](https://openclaw-hub.com/blog/surviving-context-compaction)
- [12 Production AI Agent Primitives Every Builder Should Know](https://www.mindstudio.ai/blog/12-production-ai-agent-primitives-claude-code-leak)
- [Context Window & Compaction (DeepWiki claude-code)](https://deepwiki.com/anthropics/claude-code/3.3-session-and-conversation-management)

**Reference-app intake / Repomix:**
- [Repomix — Pack your codebase into AI-friendly formats](https://repomix.com/)
- [Repomix on GitHub](https://github.com/yamadashy/repomix)
- [How to write a good spec for AI agents (Addy Osmani)](https://addyosmani.com/blog/good-spec/)

**Deterministic scaffolders:**
- [Create T3 App](https://create.t3.gg/)
- [create-t3-app on GitHub](https://github.com/t3-oss/create-t3-app)

**AI-generated code quality data:**
- [A Survey of Bugs in AI-Generated Code (arxiv 2512.05239)](https://arxiv.org/html/2512.05239v1)
- [How far can we push AI autonomy in code generation? (Martin Fowler)](https://martinfowler.com/articles/pushing-ai-autonomy.html)

---

*Feature research for: AI-driven app builder skill (OSBuilder, Claude Code orchestrator)*
*Researched: 2026-04-29*
*Confidence: HIGH on competitor feature analysis and Aider/Lovable/Bolt/v0 patterns; HIGH on multi-agent failure data (multiple peer-reviewed and industry sources); HIGH on Claude Code skill orchestration patterns (official docs + verified guides). MEDIUM-HIGH on `state.md` pattern (multiple credible sources, no single canonical spec yet).*
