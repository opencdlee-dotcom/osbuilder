# Pitfalls Research

**Domain:** AI-driven app builder (Claude Code skill — orchestrator over GSD/brainiac/predator/code-tester ecosystem)
**Researched:** 2026-04-29
**Confidence:** HIGH (most pitfalls grounded in documented postmortems, GitHub issues, peer-reviewed studies, or official Anthropic guidance; UX failure modes flagged MEDIUM where based on category-pattern reasoning)

This document catalogs failure modes that have already destroyed competing AI app-builders, broken Claude Code skills, or burned non-developer trust. Every pitfall here is something OSBuilder must explicitly defend against in roadmap, spec, and verification — not "we'll think about it later." Severity tags drive phase prioritization: **CATASTROPHIC** must be designed against in v1; **SERIOUS** must have a guardrail by Phase 3; **MINOR** is a known-issue documented in PITFALLS for review later.

---

## Critical Pitfalls

### Pitfall 1: Vibe-Coding from Scratch (the bolt.new 10M-token spaghetti)

**Severity:** CATASTROPHIC
**What goes wrong:**
Builder generates `package.json`, framework config, routing, build pipeline, and folder layout from scratch instead of starting with a deterministic scaffolder. Result: 10M+ tokens consumed for medium apps; one auth bug fix has been documented to consume 3-5M tokens; users report 20M tokens spent on a single auth issue. Code is non-idiomatic — the AI's hallucinated "this is roughly how Next.js does it" instead of the actual `create-next-app` output. Small layout changes break unrelated parts because the project structure has no canonical reference. Once 15-20 components exist, context retention degrades and changes accumulate as duplication rather than refactoring (see Pitfall 5).

**Why it happens:**
- LLMs are trained on millions of `package.json` files and "feel" like they know how to write one
- Models optimize for "appearance of activity" — generating files looks like progress
- No reproducibility check: "if I run my own scaffolder twice, do I get the same `tsconfig.json`?" — answer is no
- Token-based pricing rewards verbose generation, not delegation

**How to avoid:**
- **Hard rule in PM/Architect role:** "If a deterministic scaffolder exists for this stack (`create-next-app`, `create-t3-app`, `npm create vite`, `cargo new`, `uv init`, `npm create tauri-app`), it MUST be the first execute step. Generated `package.json` is a verification failure."
- Maintain a **scaffolder registry** in `references/scaffolders.md`: stack → official command → flags → expected output tree
- Architect phase output names the scaffolder before any code is generated; Reviewer rejects PRs where `package.json` first-commit isn't from a recognized scaffolder
- Make this falsifiable: `git log --diff-filter=A -- package.json` should show first author = a scaffolder command, not an LLM-generated diff

**Warning signs:**
- Token burn > 100k for what should be Phase 0 (scaffold)
- Multiple iterations editing `package.json` / `tsconfig.json` / `next.config.js` before any feature code
- Build errors that "shouldn't happen on a fresh `create-next-app`" (because it isn't one)
- Reviewer flags "this folder layout doesn't match the framework's convention"

**Phase to address:**
Phase 1 (Architect/scaffold-selection) and Phase 2 (DevOps/scaffold-execution). Must be enforced by the Reviewer role at every phase boundary.

**Sources:** [Bolt.new Review 2025](https://trickle.so/blog/bolt-new-review), [Stop! Don't Use Bolt AI 2025](https://medium.com/@officewajidali/stop-dont-use-bolt-ai-2025-until-you-read-this-guide-1cd527350ddc), [Bolt token efficiency docs](https://support.bolt.new/docs/maximizing-token-efficiency)

---

### Pitfall 2: AI-Adoption Code Duplication ("4× clones, refactoring collapse")

**Severity:** CATASTROPHIC
**What goes wrong:**
GitClear's 211M-line study (Jan 2020 — Dec 2024) found code duplication grew from 8.3% in 2021 to 12.3% in 2024 (~4× growth in cloned blocks of 5+ lines, 8× growth overall). Refactoring fell from 25% to <10% of changed lines in the same window. **2024 is the first year where new duplication exceeded refactoring.** AI regenerates similar logic instead of reusing existing functions because cross-referencing eliminates the time savings. Result: an OSBuilder-built app at 5k LoC quietly contains 600+ lines of near-duplicate handlers, validators, type definitions — none of which trip "tests pass" but all of which inflate maintenance debt and break in subtly different ways under refactor.

**Why it happens:**
- LLMs default to "synthesize fresh code" rather than "search the codebase for an existing pattern"
- Tests verify behavior at the boundary, not internal duplication
- "Tests pass" is the lazy success criterion (GSD philosophy explicitly rejects this)
- No dedicated refactoring/dedup phase in most AI builders

**How to avoid:**
- **Reviewer role MUST run a duplication scan** (`jscpd`, `pylint --duplicate-code`, `cpd`, or built-in tools) at every phase boundary; threshold 5% is a hard ceiling, 3% is the target
- **Falsifiable success criteria** (GSD-style): every feature must specify "user can do X with input Y and observe Z" — duplication is irrelevant to that, but failing it = phase incomplete. Combine with the dup-scan to catch both axes.
- Architect phase produces a **shared-modules manifest** (`utils/`, `lib/`, `services/`) before feature work; subsequent phases must check the manifest before generating new code
- Cross-reference protocol: when a phase asks "do we have a function for X?", Reviewer answers from a real `grep`/`rg` over the repo, not from memory

**Warning signs:**
- `jscpd`/`pylint` reports >5% duplication
- Two files contain similar-shaped functions with different names (`validateEmail`, `checkEmailValid`)
- Reviewer notices "this looks like the validator we wrote in Phase 2"
- Build size grows faster than feature count

**Phase to address:**
Phase 2 (architect emits shared-modules manifest), Phase 4+ (Reviewer runs dup scan at every phase boundary), Phase 6 (QA verifies dup ratio before milestone close).

**Sources:** [GitClear AI Copilot Code Quality 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research), [GitClear PDF report](https://gitclear-public.s3.us-west-2.amazonaws.com/GitClear-AI-Copilot-Code-Quality-2025.pdf), [LeadDev: AI compounds tech debt](https://leaddev.com/technical-direction/how-ai-generated-code-accelerates-technical-debt)

---

### Pitfall 3: Beyond-3-Reflection Drift (Aider's empirical limit)

**Severity:** CATASTROPHIC
**What goes wrong:**
Aider's hardcoded `max_reflections = 3` in `aider/coders/base_coder.py` is empirically validated: beyond 3 self-correction passes on the same failure, the model **drifts** rather than converges — it starts proposing increasingly distant fixes, hallucinates new files, retries already-failed approaches, or "fixes" by deleting failing tests. Builders without this cap (or with naive `while not passing: try_again()` loops) burn tokens proportional to the depth of the bug rather than its complexity. Once drift starts, every reflection makes the codebase worse, not better.

**Why it happens:**
- Models don't have a true "I'm stuck" signal; they always produce plausible-looking next-step text
- Sycophancy: each reflection includes "let me try a different approach" which sounds like progress
- No outside circuit-breaker: the agent itself decides when to stop, and it doesn't want to
- Without classification, "test still failing" looks the same on attempt 1 and attempt 7

**How to avoid:**
- **Hard cap of 3 reflections per failure node** in OSBuilder's self-healing loop (matches Aider's empirically-validated limit and PROJECT.md Constraint)
- **Classify before retry** (see Pitfall 4): transient/context-overflow/tool-failure/validation-failure each have different recovery strategies; don't retry a hallucination, do retry a rate-limit
- On reflection #4, **escalate with structured handoff**: state.md snapshot + last error + attempted-fixes log + "user, here's where I'm stuck and three concrete options" — never an open-ended "I tried again, still broken"
- Reflections operate on a **delta**, not a redo: each retry must articulate "what's different about this attempt vs the last" — if it can't, that counts as no-progress and trips the cap immediately

**Warning signs:**
- Reflection counter approaches 3 (log it visibly in tutor mode)
- Same error message appearing on reflections 1, 2, 3 with different wrapping code
- Each reflection touches a different file (drift signal)
- Token spend per reflection growing instead of shrinking

**Phase to address:**
Phase 3 (self-healing loop core implementation) — non-negotiable. Phase 5 (escalation/handoff UX) for the "what to show the user when we cap out."

**Sources:** [Aider issue #1440: Only 3 reflections allowed](https://github.com/paul-gauthier/aider/issues/1440), [Aider issue #3450: max_reflections meaning](https://github.com/Aider-AI/aider/issues/3450), [Aider issue #3865: Add config for max_reflections](https://github.com/Aider-AI/aider/issues/3865)

---

### Pitfall 4: Naive Retry Loops (no failure classification)

**Severity:** CATASTROPHIC
**What goes wrong:**
Self-healing loop retries the same operation on every failure, regardless of failure type. Result: 429 rate-limit failures wait nothing then re-fail immediately; hallucinated-package failures retry the same hallucinated install command 3 times; tool-availability failures (`gh` not authed) retry until the reflection cap and then escalate uselessly. Production data: organizations running 12+ AI agents at scale achieve **94% auto-resolution** only when failures are classified before retry. Without classification, the same systems achieve <40% and burn tokens proportional to failure mode rather than fix complexity.

**Why it happens:**
- "Retry" is the easiest pattern to implement; "classify-then-retry" requires a taxonomy
- Failure-mode taxonomy is domain-specific — no library gives it to you
- LLMs don't naturally introspect "is this a tool problem or a logic problem?"

**How to avoid:**
- **Failure classifier** as first step of any retry: classify into `{transient, rate-limit, context-overflow, tool-failure, validation-failure, hallucination, missing-prerequisite, scope-creep}` (PROJECT.md spec lists 4 baseline categories — extend to at least these 8)
- **Per-class strategy table**:
  - `transient` → wait + retry (max 2)
  - `rate-limit` → wait per Retry-After header + retry (max 2)
  - `context-overflow` → invoke `/clear` + reload from `state.md` + retry once
  - `tool-failure` → diagnose missing tool, run preflight, retry if fixable, else escalate
  - `validation-failure` → re-plan, do NOT retry the same code (this is the classic "passes tests but violates intent" trap)
  - `hallucination` → never retry; flag for human, search official docs for real package
  - `missing-prerequisite` → invoke preflight installer, then retry
  - `scope-creep` → halt, return to PM with revised spec
- Every retry **must log classifier output** so tutor mode can show "retrying because: rate-limit" not just "retrying..."

**Warning signs:**
- Retry attempts on the same failure type with no per-type backoff
- Same error → same fix → same failure (definitionally a classifier miss)
- Hallucinated packages appearing in retry logs
- Tutor mode says "retrying..." with no reason

**Phase to address:**
Phase 3 (self-healing loop) — failure classifier is the keystone. Cannot be deferred.

**Sources:** [Self-Healing Agent Pattern (DEV.to)](https://dev.to/the_bookmaster/the-self-healing-agent-pattern-how-to-build-ai-systems-that-recover-from-failure-automatically-3945), [Self-Healing AI with Claude API](https://claudelab.net/en/articles/api-sdk/claude-api-self-healing-agent-production-patterns), [Self-Healing Lessons from 70+ Production Bugs](https://dev.to/_d7eb1c1703182e3ce1782/how-to-build-a-self-healing-ai-agent-system-lessons-from-70-production-bugs-2nep)

---

### Pitfall 5: Multi-Agent Cascading Errors (the MetaGPT/AutoGen trap)

**Severity:** CATASTROPHIC
**What goes wrong:**
December 2025 Google DeepMind study: unstructured multi-agent networks **amplify errors up to 17.2× compared to single-agent baselines**. In MetaGPT-style chain workflows, errors propagate sequentially (PM → Architect → Frontend → Backend, each compounding the prior's mistake). In AutoGen-style mesh workflows, broadcast contamination is near-immediate. Across six frameworks tested, cascades often saturate with 5 agents reaching 100% final infection — including settings with explicit reviewer/QA roles, because the reviewer is also infected by the upstream context. MetaGPT specifically exhibits "resource hallucinations" — agents reference non-existent files/images/classes, and execution fails downstream.

OSBuilder is exactly the architecture this study warns about: PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer. Without explicit countermeasures, OSBuilder will exhibit 17× error amplification.

**Why it happens:**
- Each agent's output becomes the next agent's input → errors don't cancel, they compound
- Reviewer role doesn't help if reviewer sees the same hallucinated context
- Resource hallucinations (referencing non-existent files) compound: Architect names a file that doesn't exist → Frontend tries to import it → Backend tries to call its API → cascade
- No agent is incentivized to push back — "the PM said this exists, must be true"

**How to avoid:**
- **Ground every agent's input in real artifacts**: each role reads from disk (`state.md`, scaffolder output, prior phase deliverables), not from in-context summaries. Each role MUST cite file paths it read.
- **Circuit breakers per agent**: token budget per role per task; if exceeded, halt and escalate (don't continue downstream)
- **Verifier independence**: Reviewer role runs in a fresh subagent with only the artifact + the spec, NOT the build conversation. Cannot inherit the cascading context.
- **Resource-existence check**: every reference to a file/class/package in any role's output must be `grep`'d/`ls`'d before downstream consumption. If it doesn't exist on disk, halt that branch.
- **Structured topology** (per the DeepMind paper): chain with mandatory disk-grounded handoffs, NOT mesh broadcast. Phases hand off through `state.md` + phase artifacts, not in-context dialogue.

**Warning signs:**
- Reviewer approves something that fails QA on basic grep
- Multiple roles reference the same non-existent file
- Token spend per role climbs across phases (compounding context)
- "Backend is implementing the API the Frontend already defined" but neither file actually exists

**Phase to address:**
Phase 1 (Architecture: define handoff format and disk-grounding rules), Phase 4 (Role implementation: verifier-as-fresh-subagent), Phase 6 (QA: cascade detector that diffs role inputs).

**Sources:** [The Multi-Agent Trap (Towards Data Science)](https://towardsdatascience.com/the-multi-agent-trap/), [Why do multi-agent LLM systems fail (2026 Guide)](https://futureagi.substack.com/p/why-do-multi-agent-llm-systems-fail), [From Spark to Fire: Modeling Error Cascades in LLM Multi-Agent](https://arxiv.org/html/2603.04474v1), [AgentMesh paper](https://arxiv.org/html/2507.19902v1)

---

### Pitfall 6: Slopsquatting / Hallucinated Package Imports

**Severity:** CATASTROPHIC (security)
**What goes wrong:**
March 2025 research: **20% of AI-generated code imports reference non-existent packages** (576k Python/JS samples examined). Open-source LLMs (CodeLlama, DeepSeek, WizardCoder, Mistral) hallucinate at higher rates than commercial; ChatGPT-4 ~5%, others much higher. Crucially, **43% of hallucinated package names recur across 10 prompts** — they are predictable. Attackers register the predictable names ("slopsquatting"). One hallucinated package (`huggingface-cli`) got 30k+ downloads in 3 months; Alibaba pasted it into a public README. Hallucinations split: 38% conflations (`express-mongoose`), 13% typo-variants, 51% pure fabrications.

OSBuilder ships apps to user-private GitHub. A slopsquatted dependency that runs `postinstall` scripts on every clone is a remote code execution vector for both Charlie and the open-source audience.

**Why it happens:**
- LLMs synthesize plausible-sounding package names from patterns (`{verb}-{noun}` conventions)
- No verification step between "model says install X" and "npm/pip install X"
- Hallucinations are repeatable, not random — same prompts produce same fake names
- Lockfile generation happens AFTER install, so a hallucinated package gets locked in

**How to avoid:**
- **Mandatory package existence check** before any `npm install` / `pip install` / `cargo add`: query the real registry API (`npm view <pkg>`, `pip index versions`, `cargo search`) and require ≥1 published version + (heuristic) >100 weekly downloads or recent activity for unfamiliar packages
- **Allowlist-first scaffolding**: only deterministic scaffolders generate the initial deps (Pitfall 1 prevention doubles as Pitfall 6 prevention)
- **Lockfile-first**: generate `package-lock.json` / `uv.lock` immediately after scaffold; subsequent additions go through `npm install --save` (which fails on non-existent), not by editing manifests directly
- **Disable lifecycle scripts during install** in OSBuilder's preflight: `npm install --ignore-scripts` until package provenance is verified (mitigates RCE-on-clone)
- **Reviewer role runs `npm audit` / `pip-audit` and a "package provenance" pass** at every dependency change

**Warning signs:**
- `npm install` for a package the LLM is "confident" about (always check)
- Package names that look like conflations (`react-router-firebase-auth`)
- New dependencies added outside scaffolder commands
- `npm WARN` about deprecated/missing during install

**Phase to address:**
Phase 2 (DevOps/dependency-policy: registry verification gate), Phase 4 (Backend/Frontend: must request deps through the gate, not by edit), Phase 7 (Security review/Watchdog).

**Sources:** [AI-hallucinated dependencies (BleepingComputer)](https://www.bleepingcomputer.com/news/security/ai-hallucinated-code-dependencies-become-new-supply-chain-risk/), [Slopsquatting research (Aikido)](https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks), [Trend Micro on Slopsquatting](https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/slopsquatting-when-ai-agents-hallucinate-malicious-packages), [Mend.io: Hallucinated Package Attack](https://www.mend.io/blog/the-hallucinated-package-attack-slopsquatting/)

---

### Pitfall 7: Auto-Compaction Destroys Mid-Build State

**Severity:** SERIOUS
**What goes wrong:**
Claude Code auto-compaction triggers at ~98% of effective context. Documented user reports: "halfway through a refactoring, in the middle of implementing a feature, right when you needed the model to maintain full context" — compaction fires and the model loses what it was doing. Worse documented cases: input + max_tokens > 200k → compaction itself fails ("175272 + 32000 > 200000"); context counter corrupted to "102%" requiring every interaction to wait through compaction. For OSBuilder building a real app, a 30-min build that compacts at minute 25 typically loses: which phase it was in, which files have been touched, what the user said in initial spec, which sub-skill was running.

**Why it happens:**
- Compaction is automatic and non-negotiable; you can't disable it
- LLM doesn't checkpoint to disk by default; everything's in conversation context
- Subagents don't inherit parent context (Pitfall 9), so a "save state to subagent" idea doesn't work
- Recovery requires *something* on disk that survives /clear AND compaction

**How to avoid:**
- **`state.md` as load-bearing checkpoint**, ~15 lines, updated at every phase boundary (PROJECT.md constraint). Required fields: goal, current phase, phases done, last failure (if any), next step, paths to in-flight artifacts
- **Phase boundaries are checkpoint boundaries** — never start a new phase without writing `state.md` + committing scaffolder/feature work to git (so a compaction-induced confusion can be reconstructed from `git log` + `state.md`)
- **Idempotent re-entry**: every phase MUST be re-runnable from `state.md` alone. If "I cleared the conversation and ran `/osbuilder continue`" doesn't work, the phase is broken.
- **Token-budget watchdog**: at 75% context, OSBuilder writes `state.md` + summarizes-to-disk; at 90%, prompts user "I'm about to compact, want to checkpoint and restart fresh?"; never wait until 98%
- **Hooks for auto-checkpoint** (per existing community patterns) — write `state.md` on every Write/Edit tool invocation, costs ~50 tokens, saves a 30-min build

**Warning signs:**
- Token use >75% with active build
- User asks "where were we?" after a compaction
- `state.md` not updated in last 3 phases
- Resume command (`/osbuilder continue`) fails or asks the user to re-explain

**Phase to address:**
Phase 1 (Architecture: state.md schema + phase-boundary checkpoint protocol), Phase 3 (self-healing: re-entry from state.md is a self-healing strategy), Phase 5 (token-budget watchdog as part of orchestration loop).

**Sources:** [Context Window & Compaction (DeepWiki)](https://deepwiki.com/anthropics/claude-code/3.3-context-window-and-compaction), [Auto-compact bug #3274](https://github.com/anthropics/claude-code/issues/3274), [Persistent state across compaction #25999](https://github.com/anthropics/claude-code/issues/25999), [Context compaction destroyed my work (DEV.to)](https://dev.to/mikeadolan/claude-code-compaction-kept-destroying-my-work-i-built-hooks-that-fixed-it-2dgp), [Auto-compact fails at 200k #48893](https://github.com/anthropics/claude-code/issues/48893)

---

### Pitfall 8: SKILL.md Description Bloat / Context Rot

**Severity:** SERIOUS
**What goes wrong:**
Two failure modes on opposite ends:
1. **Description too long/specific** → Claude Code's metadata budget is ~16k chars total across all skills. With typical 263-char descriptions, only ~42 skills fit. OSBuilder bloating its description squeezes other skills out of the discovery window. Long descriptions also make Claude *over*-trigger ("any mention of an app → use OSBuilder").
2. **Description too vague** → Claude *under*-triggers; the skill is never invoked when it should be. Anthropic's own guidance: descriptions should be "a little bit pushy" with specific trigger conditions.
3. **SKILL.md body too long** ("context rot") → instructions runs to several pages, Claude burns context loading them, agent performance degrades on long builds. PROJECT.md cap: ≤200 lines.

**Why it happens:**
- "More words = more clarity" instinct → opposite of what works for routing
- Forgetting that SKILL.md is loaded *every time* the skill is considered, not just when invoked
- Mixing reference material into SKILL.md instead of progressive-disclosure to `references/`

**How to avoid:**
- **Hard cap: SKILL.md ≤ 200 lines** (PROJECT.md constraint). Anything beyond → `references/` or `scripts/`.
- **Description ≤ 130 chars** (community-observed sweet spot for fitting many skills in budget) with the form: "[capability] when [trigger conditions]"
- **Progressive disclosure**: SKILL.md is the index; all detail (playbooks, scaffolder registry, role briefs, failure taxonomy, troubleshooting) lives in `references/{topic}.md` and is loaded only when the relevant phase runs
- **Trigger test**: write 10 prompts that should invoke OSBuilder and 10 that shouldn't; verify routing on all 20 before publish
- **Re-test after every SKILL.md edit** — a small description change can flip the trigger behavior

**Warning signs:**
- SKILL.md > 200 lines
- Description > 200 chars
- Skill invocation rate doesn't match expected trigger prompts (over/under)
- Claude loads SKILL.md and immediately needs to load 3 more `references/` files for basic operation (rot signal)

**Phase to address:**
Phase 0 (Skill scaffolding: enforce line/char caps from day 1), Phase 8 (Open-source publish: trigger-test before release).

**Sources:** [Anthropic: Equipping agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), [Anthropic skills repo: skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), [Context Rot in Claude Skills](https://www.mindstudio.ai/blog/context-rot-claude-code-skills-bloated-files), [Claude Code skill budget research gist](https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1)

---

### Pitfall 9: Subagent Context Loss / Skill Recursion

**Severity:** SERIOUS
**What goes wrong:**
- **Subagents do not inherit parent skills** — they are stateless workers. Calling `/predator` from inside OSBuilder doesn't automatically pass OSBuilder's context; predator only sees what's in the explicit invocation prompt.
- **Subagent recursion**: documented bug — when a skill's hook calls Claude recursively, endless process spawning + RAM OOM.
- **OSBuilder calls /gsd, which calls /brainiac, which calls...** — without an explicit invocation budget, this nests until context exhausts or compaction destroys the call stack.
- **Recent (Feb 2026) bug**: after 4 parallel research agents completed, Claude entered a loop of stating intent to write without executing the Write tool, repeating until context exhausted.

**Why it happens:**
- Subagents are stateless by design (good for isolation, bad for parent-context dependency)
- No built-in "max nesting depth" for skill invocations
- Hooks fire on tool calls; if hook calls Claude → infinite

**How to avoid:**
- **Explicit invocation budget**: OSBuilder MUST track depth (`OSBUILDER_DEPTH` env or in `state.md`); refuses to nest beyond depth 3 (osbuilder → gsd → brainiac → STOP)
- **Pass-through context discipline**: every subagent invocation receives a structured prompt with: goal, scoped artifact paths, expected deliverable, success criteria. Never "do whatever, you have all my context" — they don't.
- **Use `--settings` flag with `disableAllHooks: true`** for subagent invocations to prevent hook-based recursion
- **Subagents return structured artifacts to disk** (e.g. `/predator` writes report to `.planning/research/`); parent reads from disk, not from subagent's chat output. This is the same disk-grounding pattern as Pitfall 5.
- **Composition rule** (PROJECT.md constraint): if a sub-skill is missing functionality, fix the sub-skill, don't reimplement inside OSBuilder. Avoids the temptation to "just absorb GSD" which breeds the recursion-replacement anti-pattern.

**Warning signs:**
- Same skill name appearing twice in a call stack
- Subagent invocations with prompts that say "you know the project context" (you didn't pass it)
- Token spend per skill-call rising as depth grows
- Hook-driven loops (process spawning, OOM)

**Phase to address:**
Phase 1 (Architecture: invocation depth budget + structured handoff schema), Phase 4 (sub-skill orchestration: each sub-skill call wrapped with explicit context-passing protocol), Phase 5 (testing: simulate depth-4 call to verify graceful refusal).

**Sources:** [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents), [Settings pollution in subagents (Egghead)](https://egghead.io/avoid-the-dangers-of-settings-pollution-in-subagents-hooks-and-scripts~xrecv), [Infinite loop bug #27281](https://github.com/anthropics/claude-code/issues/27281), [Subagents-spawning-subagents OOM #4850](https://github.com/anthropics/claude-code/issues/4850), [Codex rescue infinite recursion #234](https://github.com/openai/codex-plugin-cc/issues/234)

---

### Pitfall 10: Deploy-Target Lock-In + Mid-Project Pricing Shifts (the v0/Lovable trust loss)

**Severity:** SERIOUS
**What goes wrong:**
- **v0 (Vercel)**: tightly coupled to Vercel infra; "Vercel lock-in" means migrating off requires DNS reconfig, env reconfig, build reconfig. May 2025 Vercel shifted v0 from unlimited prompts to credit-based without sufficient community comms — "improved transparency" felt like the opposite. Trust permanently damaged.
- **Lovable**: Cloud lock-in similar; CVE-2025-48757 (Mar 2025) — Lovable-generated apps had insufficient/missing Supabase Row Level Security policies. April 2025 Palantir engineer publicly tweeted real exposed sensitive data examples. Lovable failed to meaningfully fix in the 45-day disclosure window. November 2025: free Lovable accounts could read other users' source code, DB credentials, AI chat histories, customer data.

OSBuilder's PROJECT.md explicitly punts deploy-to-cloud-by-default to v2 — but the *clone-and-run* runbook still has lock-in risk vectors: hardcoded URLs, env templates that assume specific providers, Dockerfile assuming AWS-region-specific images.

**Why it happens:**
- "We'll add deploy targets later" → defaults silently encode one
- Cloud-vendor SDKs creep into scaffold defaults
- Pricing changes are inevitable for any hosted AI service; mitigations require user owning their stack
- Lovable RLS issue: AI builders generate plausible-looking auth without verifying actual security boundaries

**How to avoid:**
- **No-deploy-by-default rule** (PROJECT.md): v1 ships local + private GitHub; deploy is opt-in via `--production-ready` AND named-phase. Cannot bake any single deploy target into the default scaffold.
- **Vendor-neutral scaffold**: env-based config with provider-agnostic names (`DATABASE_URL`, `REDIS_URL`), not `VERCEL_*` or `SUPABASE_*` hardcoded into `next.config.js`
- **Auth/RLS verification** (Lovable lesson): if the scaffold uses Supabase/Firebase/etc., Reviewer role MUST verify RLS/security-rules policies are in place AND test "anonymous user can't read other user's row." Falsifiable check, not "auth feels added."
- **Document the migration path** in README from day one ("if you want to leave Vercel, here's what changes")
- **Self-host story**: every default scaffold must include a "run this entirely locally with `docker compose up`" path

**Warning signs:**
- Scaffold output contains a vendor name in non-replaceable positions
- Auth tested only via "user can log in" — not "non-owner can't access owner's data"
- README missing self-host instructions
- Env template requires accounts at >2 SaaS vendors before app runs

**Phase to address:**
Phase 2 (DevOps/scaffold: vendor-neutrality lint), Phase 6 (QA/Reviewer: RLS/auth boundary verification), Phase 7 (docs: migration-path section).

**Sources:** [Why I'm leaving Vercel and v0](https://medium.com/@baytbyte/why-im-sadly-leaving-vercel-and-v0-when-all-in-one-turns-into-all-for-money-368c3a976df3), [Two Days Two Hacks: Lovable disclosure](https://dev.to/jon_at_backboardio/two-days-two-hacks-the-lovable-disclosure-and-the-pattern-nobody-wants-to-talk-about-47eh), [How to migrate from Lovable Cloud to Vercel](https://nextbigwhat.com/how-to-migrate-from-lovable-cloud-to-vercel-and-take-control-of-your-stack/), [Vercel/Lovable/Copilot security crisis 2026](https://engineerscorner.in/ai-tools-security-breach-vercel-lovable-2026/), [v0 reliability community thread](https://community.vercel.com/t/is-v0-still-a-reliable-ai-solution-for-developers/28883)

---

### Pitfall 11: Validation-Failure Treated as Retry (when it should be Re-Plan)

**Severity:** SERIOUS
**What goes wrong:**
Test fails because the implementation is wrong. Naive loop: retry the implementation. Worst case: model "fixes" by deleting/weakening the test ("passes tests but violates intent"). Right response: re-plan from spec — the implementation was based on a misunderstanding, not a bug. GitClear's data on falling refactoring rates (Pitfall 2) is partly this: AI patches symptoms instead of redesigning when behavior diverges from spec.

**Why it happens:**
- "Failure → retry" is the default mental model
- Re-plan requires admitting the prior plan was wrong (sycophancy fights this)
- Tests are easier to weaken than implementations (asymmetry)
- Without a falsifiable spec, "passes tests" feels like "done"

**How to avoid:**
- **Failure classifier** (Pitfall 4) routes `validation-failure` to **re-plan path**, NOT retry path
- **Spec immutability** during retry: the spec written by PM is read-only during code-fix retries. If you need to change the spec, halt and route back to PM with a "spec needs revision" handoff.
- **Test-tampering detector**: Reviewer flags any retry that touches the test file when the test file was the failure source. Test changes require an explicit "spec changed" trigger.
- **Falsifiable success criteria** (GSD philosophy): every feature has user-observable success criteria written before implementation. Tests verify the criteria. If criteria fail, re-plan; if tests fail but criteria pass, the test is wrong (and that's a separate, narrower path).

**Warning signs:**
- Diff for a "fix" reduces test assertions / loosens matchers / adds skips
- Multiple retry cycles all touching test file
- Implementation hasn't changed but tests now pass (suspicious — verify behavior manually)
- Reviewer can't articulate what changed semantically

**Phase to address:**
Phase 3 (failure classifier + re-plan path), Phase 6 (Reviewer: test-tampering detector + falsifiable-criteria check).

**Sources:** [GitClear refactoring collapse](https://www.gitclear.com/ai_assistant_code_quality_2025_research), [Self-Healing Lessons (DEV.to)](https://dev.to/_d7eb1c1703182e3ce1782/how-to-build-a-self-healing-ai-agent-system-lessons-from-70-production-bugs-2nep), [The Evidence Against Vibe Coding (SoftwareSeni)](https://www.softwareseni.com/the-evidence-against-vibe-coding-what-research-reveals-about-ai-code-quality/)

---

### Pitfall 12: Jargon Leaks Through to Common-Person UX

**Severity:** SERIOUS
**Confidence:** MEDIUM (category-pattern reasoning + Anthropic / accessibility design heuristics)
**What goes wrong:**
Tutor-mode-on-by-default surfaces error messages from underlying tools: `ENOENT`, `EACCES`, `command not found`, `peer dep conflict`, `responsive design`, `npm WARN deprecated`, `fatal: not a git repository`. Common-person user has no schema for what these mean. They give up, file confused issues, lose trust. UX research consistently shows: a single jargon-y error in onboarding triples bounce rate vs. an equivalent plain-English error.

**Why it happens:**
- LLMs trained on dev forums; default vocab is dev jargon
- Pass-through is the lazy path: just print whatever `npm install` printed
- "Accessible" UX written by devs who can't see their own jargon
- Tutor mode mistaken for "verbose mode" (more words ≠ more accessible)

**How to avoid:**
- **Jargon dictionary** in `references/jargon-translations.md`: term → plain-English version. Every tool output passes through translation BEFORE display in beginner mode.
  - `ENOENT` → "the file/folder I need isn't there"
  - `EACCES` → "I don't have permission to do that"
  - `peer dep conflict` → "two parts of the project disagree on which version of X to use"
  - `responsive design` → never use; in questions, ask "should it work on phones too?"
- **Outcome-framed questions** (PROJECT.md constraint): never "do you need a database?" (jargon); always "do users need to save their work between visits?" (outcome)
- **Friendly-error template**: every error has 3 parts — what happened (plain), why (plain), what to try next (concrete, optional auto-fix)
- **Jargon lint pass** in QA: scan all user-facing strings against the jargon dictionary; any untranslated term is a phase failure
- **Tutor mode tone control**: explanations are "what just happened" (one sentence), not "let me teach you about npm." Patronizing-detector heuristic: if the explanation tells the user something they likely already know from the prior step, cut it.

**Warning signs:**
- Raw stack trace reaches the user
- User asks "what's a [term]?"
- "responsive design" / "deployment" / "container" appears in a user-facing question
- Beginner mode test users (non-devs) bounce on a specific error message

**Phase to address:**
Phase 0 (UX foundations: jargon dictionary scaffold), Phase 5 (tutor mode + error translation pass), Phase 8 (QA with non-developer users before publish).

**Sources:** [Beyond the Vibes guide](https://blog.tedivm.com/guides/2026/03/beyond-the-vibes-coding-assistants-and-agents/), [AI Coding Assistants for Beginners](https://www.frontendmentor.io/articles/ai-coding-assistants-for-beginners), [Google Colab Learn Mode](https://blog.google/innovation-and-ai/technology/developers-tools/colab-updates/), [Examining AI Code Assistant Impact (CHI)](https://dl.acm.org/doi/10.1145/3706599.3706670)

---

### Pitfall 13: Preflight Installer Breaks the User's System

**Severity:** SERIOUS
**Confidence:** MEDIUM (category-pattern reasoning from package-manager war stories)
**What goes wrong:**
Auto-installer guesses wrong tool (`brew install node` when user had `nvm`-managed Node, ends with two Nodes; `apt install python3` when user has `pyenv`; touching system Python on macOS, breaking other tools). User wakes up to a broken `git`, broken Homebrew, or broken Python. **One-bad-preflight kills trust permanently** for the common-person audience — they don't know how to recover.

**Why it happens:**
- "Install Node" has 8 right answers depending on environment (nvm, n, fnm, mise, brew, apt, choco, scoop, official installer, asdf)
- LLM picks the answer it saw most often in training, which may not match user's environment
- macOS system Python is load-bearing for Apple tools; touching it via brew breaks things
- Windows: PATH ordering decides which tool wins; new install can shadow existing

**How to avoid:**
- **Detect-first, install-second**: probe the system for existing version managers (`nvm`, `pyenv`, `mise`, `asdf`, `volta`); if found, route through them. Only fall back to system package manager if no manager exists.
- **Per-platform decision tree** in `references/preflight-{macos,linux,windows}.md`: dictate the right tool per platform per scenario
- **Confirmation prompt with diff preview**: "I'm about to install Node 20.x via Homebrew. This will add `/opt/homebrew/bin/node` to your PATH. Existing `node` is `/usr/local/bin/node` (v18.x). Proceed? [Y/n]" — explicit about what changes
- **Never auto-touch macOS system Python** (`/usr/bin/python3`); always install via `pyenv`/`uv`/Homebrew
- **Rollback playbook**: every install records "what I added" in `~/.osbuilder/install-log.json`; `osbuilder undo-preflight` reverses
- **Dry-run mode**: `osbuilder preflight --dry-run` shows what WOULD change, no side effects

**Warning signs:**
- Multiple Node/Python versions in PATH after preflight
- User reports "git stopped working after I ran osbuilder"
- Preflight succeeded but new app's `node` is the wrong version
- Install command run without prior detection of existing version manager

**Phase to address:**
Phase 5 (preflight installer: detection-first protocol + per-platform decision tree + rollback log + dry-run mode), Phase 8 (cross-platform validation with real users).

**Sources:** Category pattern; specific source for Windows path issue: [Tips for Cross-Platform PowerShell](https://powershell.org/2019/02/tips-for-writing-cross-platform-powershell-code/). General Tauri version-mismatch precedent: [Tauri version mismatch issue #13960](https://github.com/tauri-apps/tauri/issues/13960).

---

### Pitfall 14: Cross-Platform Path & Shell Assumptions

**Severity:** SERIOUS
**What goes wrong:**
- Path separator: Unix `/`, Windows `\`. `pkg-name@1.0.0/dist/index.js` works on macOS, fails on Windows; PowerShell may auto-replace `/` with `\` and treat `\` as escape, mangling paths
- PATH env separator: Unix `:`, Windows `;`
- Shell features: bash arrays, zsh globbing, PowerShell pipelines all differ; a "simple" install script that uses `[[ -f ... ]]` blows up in `sh`
- Line endings: `CRLF` on Windows, `LF` on Unix; scripts committed as `CRLF` fail on Linux with cryptic `bad interpreter`
- Default shell: macOS = zsh, Linux = bash, Windows = PowerShell. Cannot assume any.
- Package managers: npm vs pnpm vs yarn vs bun (per-project lockfiles incompatible); Python: pip vs pipx vs uv vs poetry; system: brew (mac) vs apt (debian) vs choco (win) vs winget vs scoop

**Why it happens:**
- Dev wrote on macOS, never tested on Windows
- Hardcoded path strings in scaffolder output
- LLM defaults to bash because most training data is bash

**How to avoid:**
- **Use language-native path APIs only**: Node `path.join()`, Python `pathlib`, Go `filepath`. Never string-concat paths.
- **Cross-platform script layer**: prefer Node-based scripts (`scripts/install.mjs`) over `.sh` for install steps — runs everywhere Node runs; package.json `scripts` use `cross-env`/`rimraf`/`shx` for shell-portable commands
- **`.gitattributes` enforces LF**: `* text=auto eol=lf` in every scaffold
- **Detect package manager**: read `packageManager` field in `package.json` (or lockfile presence: `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`); use what the project already declared
- **Test matrix**: macOS + Linux + Windows + WSL on every preflight script change (CI required)
- **Avoid bash-only constructs** in install scripts: no `[[ ]]`, no arrays, no `<()` process substitution. POSIX `sh` or Node-script.

**Warning signs:**
- Hardcoded `/` in any path string in the scaffolder template
- `.sh` scripts in install path (should be `.mjs` or `.py`)
- Scaffold doesn't include `.gitattributes` with `eol=lf`
- "Works on macOS, fails on Windows" reports from open-source users

**Phase to address:**
Phase 2 (DevOps/scaffold: cross-platform script template + .gitattributes), Phase 5 (preflight: per-platform decision trees), Phase 8 (cross-platform CI matrix before publish).

**Sources:** [Cross-platform PowerShell tips](https://powershell.org/2019/02/tips-for-writing-cross-platform-powershell-code/), [PowerShell path separator OS detection](https://rakhesh.com/powershell/powershell-path-separator-based-on-os/), [Cross-platform Node shell scripts](https://exploringjs.com/nodejs-shell-scripting/ch_creating-shell-scripts.html), [Azure Pipelines cross-platform scripting](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/cross-platform-scripting?view=azure-devops)

---

### Pitfall 15: gh CLI Auth State Drift + Token Leakage

**Severity:** SERIOUS (security-adjacent)
**What goes wrong:**
- **Auth schism**: stored auth state and what `gh` reports diverge. `GITHUB_TOKEN` env var is set → `gh auth login` is "interrupted until you unset the variable." `gh auth status` may incorrectly report `GITHUB_TOKEN` is set when it's empty. CI/CD `GITHUB_TOKEN` and dev `GH_TOKEN` collide.
- **Plain-text fallback**: if a credential store is missing/broken, `gh` falls back to writing tokens to a plain text file. User doesn't notice. File ends up tarballed, backed up, screen-shared.
- **Token in committed `.env`**: scaffold includes `.env.example`, user copies to `.env`, pastes their PAT into it, runs `git add .` (because they don't know about `.gitignore`), pushes a private PAT to a private repo — which is still bad if shared, leaked, or made public later. This has caused real-world leaks.
- **Clearing `GITHUB_TOKEN` then `gh auth login`** can leave git credentials in invalid state, requiring manual gh-as-git-credential-helper setup.

**Why it happens:**
- `gh` has 3+ auth sources (env, keychain, plain-text fallback) and they don't coordinate
- Scaffolds default to including `.env.example`, but new users don't grok the example/real-file distinction
- `git add .` is the universal "ship it" instinct for non-devs

**How to avoid:**
- **Auth-state preflight**: before any `gh` command, run `gh auth status` AND check `GH_TOKEN`/`GITHUB_TOKEN` env vars; if both/conflicting, halt with friendly resolution prompt
- **Use `gh auth login --hostname github.com --git-protocol https` flow** for fresh setups; verify with `gh api user` before proceeding
- **Verify keychain backing**: if `gh auth status` shows plain-text token storage, refuse to proceed and prompt user to fix (or auto-install keychain helper for their OS)
- **Scaffold always includes `.gitignore` with `.env`** AND a pre-commit hook (e.g. `gitleaks`) that blocks token-shaped strings
- **Pre-commit secret scan**: `gitleaks` or `trufflehog` runs in scaffold's git hooks dir; first commit of every OSBuilder-built repo includes the hook
- **PAT-handling protocol**: OSBuilder never asks the user to paste a PAT into `.env`. Always uses `gh auth` flow (browser OAuth or keychain) and reads via `gh api`, never via env-var-in-file
- **Friendly explanation of `.env` vs `.env.example`** in tutor mode at first use

**Warning signs:**
- `gh auth status` shows plain-text storage
- `git diff` reveals `GH_TOKEN=ghp_...` or `OPENAI_API_KEY=sk-...`
- Multiple `gh` auth contexts active (env + keychain + file)
- User says "I just put my key in the env file, why is git complaining?"

**Phase to address:**
Phase 5 (auth preflight + secret-scan hook in scaffold), Phase 7 (Security/Watchdog phase: full secret-leak audit before push).

**Sources:** [gh auth login GH_TOKEN issue #8347](https://github.com/cli/cli/discussions/8347), [GITHUB_TOKEN auth issue #2922](https://github.com/cli/cli/issues/2922), [gh auth status incorrectly reports #7800](https://github.com/cli/cli/issues/7800), [GitHub CLI auth confusion (Sommerfeld)](https://www.henriksommerfeld.se/github-cli-auth-confusion-using-github-token/), [GitHub CLI manual: gh auth login](https://cli.github.com/manual/gh_auth_login)

---

### Pitfall 16: Scope Creep / Premature Complexity (K8s, microservices, hosted SaaS)

**Severity:** SERIOUS
**What goes wrong:**
LLM defaults toward "best practice" code, which often means: K8s manifests, Helm charts, service mesh, microservices, message queues, multi-region everything. For a single-user lab-grader app, this is multi-week busywork producing nothing the user will ever benefit from. PROJECT.md explicitly out-of-scopes K8s/microservices/service-mesh in v1 default builds — this is a known trap.

Adjacent traps OSBuilder must refuse:
- **Building OSBuilder's own deploy target** instead of `git push` to private GitHub
- **Building a hosted multi-tenant SaaS for OSBuilder** — out of scope per PROJECT.md
- **Reimplementing GSD/brainiac/predator inside OSBuilder** — composition rule explicitly forbids
- **Building Claude Code itself or other AI-IDE substrates** — recursion, out of scope

**Why it happens:**
- LLMs trained on FAANG engineering blogs; "scalable" defaults are aspirational, not appropriate
- "More tech = more credible" instinct
- Easier to add than to defend the absence
- Open-source users may push for "support my use case" features that require absorbing dependencies

**How to avoid:**
- **Refuse-list in PM/Architect role**: K8s, Helm, service mesh, microservices, message queues, multi-region, custom auth-server, custom queue, OSBuilder-as-SaaS — auto-rejected unless `--production-ready` flag explicitly enabled AND named-phase added
- **`--production-ready` is the only escape hatch**, and it adds the items as named-phases (observability, migrations, healthchecks, secret manager, rate limiting, backups), not as default code
- **PROJECT.md "Out of Scope" section is load-bearing** — every milestone review checks it; new requests test against it before estimation
- **Composition rule enforcement** (PROJECT.md): if a sub-skill is missing functionality, fix the sub-skill, don't fork. Reviewer checks every PR for "is this duplicating GSD/brainiac/predator?"
- **"Refuse with reason" UX**: when refusing complexity, explain plainly: "I'm not adding K8s because [reason]. If you need it, run again with `--production-ready` and I'll add it as a named phase."

**Warning signs:**
- Scaffold output contains `Chart.yaml`, `kustomization.yaml`, `values.yaml`, `docker-compose.production.yml` with 8 services
- Architect proposes a microservice split for a 500-user app
- User-facing question asks about K8s without `--advanced` flag
- New code in OSBuilder duplicates an existing GSD/brainiac/predator capability

**Phase to address:**
Phase 1 (Architecture: refuse-list defined), Phase 4 (every role checks against refuse-list before producing output), milestone reviews (audit out-of-scope adherence).

**Sources:** [The Multi-Agent Trap](https://towardsdatascience.com/the-multi-agent-trap/), [Bolt.new complex project failures](https://trickle.so/blog/bolt-new-review), [Beyond the Vibes guide](https://blog.tedivm.com/guides/2026/03/beyond-the-vibes-coding-assistants-and-agents/) (premature complexity discussion)

---

### Pitfall 17: Sensible-Default Misalignment (e.g., Postgres when user wanted SQLite)

**Severity:** MINOR (recoverable, but trust-eroding)
**What goes wrong:**
PROJECT.md specifies "real database (Postgres-via-compose for multi-user web apps; SQLite only for single-user CLIs)." But "what kind of app is this?" is rarely binary. User says "personal app for my book collection" → PM picks Postgres because "web app" → user wanted SQLite-on-disk for portability and offline use. By the time they realize, scaffold is committed.

Other default misalignments to defend against:
- Tailwind by default for users who'd prefer plain CSS
- TypeScript by default for users who don't know JS yet
- Postgres when SQLite would do; SQLite when Postgres needed
- Next.js when Remix/SvelteKit would suit the project pattern

**Why it happens:**
- PM's question doesn't surface the relevant axis ("personal/local-only" vs "web for me + others")
- Default tables are coarse-grained
- "I don't know, you decide" option (PROJECT.md feature) picks the modal default, which isn't always right

**How to avoid:**
- **Outcome-framed clarifying questions** for the consequential axes:
  - "Do you want this to work without internet?" → SQLite vs Postgres
  - "Will multiple people use it at the same time?" → SQLite (no) vs Postgres (yes)
  - "Will you ever copy the whole app to a USB stick?" → SQLite (yes) vs Postgres (no)
- **Explain defaults in tutor mode at decision points**: "I'm picking Postgres because you said multiple users. If that's wrong, say 'use SQLite' and I'll switch."
- **"I don't know, you decide" defaults are documented and explainable** — never silent
- **Reversibility plan**: every default has a "to switch later, change X" note in the README, even if not currently advertised
- **"What about Y?" question after each major default**: PM proactively asks "I'm picking Postgres — does that sound right?" once, in plain English

**Warning signs:**
- User asks mid-build "wait, why Postgres?"
- Question table doesn't surface the actual axis the default depends on
- README missing "to switch DB later, change X"

**Phase to address:**
Phase 4 (PM role: outcome-framed clarification + default-explanation protocol), Phase 5 (tutor mode: explain defaults at decision points).

**Sources:** PROJECT.md constraints; [AI Coding Assistants for Beginners](https://www.frontendmentor.io/articles/ai-coding-assistants-for-beginners) (default-mismatch UX discussion)

---

### Pitfall 18: Silent Infinite Loops vs. Proper Escalation

**Severity:** SERIOUS
**What goes wrong:**
Self-healing loop hits the 3-reflection cap and... what? Bad outcomes documented:
- Silently retries beyond cap (cap not enforced)
- Caps but emits unactionable message ("I tried 3 times, can't do this. Please help.")
- Caps but loses state — user has to re-explain the entire build
- Caps and gives up with no `state.md`, no diagnostic bundle

The Feb 2026 Claude Code bug — "loop of stating intent to write without executing" — is exactly this failure mode in production: the agent never escalates, it just stalls until context exhaustion.

**Why it happens:**
- "Escalation" is harder to design than "give up"
- LLMs are reluctant to admit hard-stop ("let me try one more thing...")
- No structured handoff format → escalation is ad-hoc text the user can't act on

**How to avoid:**
- **Hard-cap enforced by external counter**, not by the LLM's self-control. Reflection counter in `state.md`; >3 → halt, no exceptions.
- **Structured handoff format** (per PROJECT.md spec): on escalation, OSBuilder produces a fixed-shape report:
  - **State**: phase, what's done, what's not
  - **Last error**: full text + source + classifier output
  - **What was tried**: list of 3 reflection attempts + diff of each
  - **Three concrete options for the user**: "(a) skip this feature for now, (b) different approach: X, (c) hand off to me with this prompt"
- **Diagnostic bundle**: escalation also writes `~/.osbuilder/handoffs/{timestamp}/` containing relevant file diffs, logs, scaffolder version, env info — the user can paste a single path into a fresh Claude session to resume
- **Stall detector**: if no tool call in N turns, treat as silent-loop and force escalation
- **Tutor mode visibility**: counter is shown ("Reflection 2 of 3 — if this doesn't work I'll hand off to you") so escalation isn't a surprise

**Warning signs:**
- Reflection counter in logs but no enforcement
- Escalation message doesn't fit the structured format
- User asked "what do I do now?" after an escalation
- No `state.md` after a failed build (can't resume)

**Phase to address:**
Phase 3 (self-healing loop + cap enforcement), Phase 5 (structured-handoff UX + diagnostic bundle), Phase 6 (QA: simulate stuck builds and verify escalation quality).

**Sources:** [Aider issue #1440](https://github.com/paul-gauthier/aider/issues/1440), [Claude Code infinite loop bug #27281](https://github.com/anthropics/claude-code/issues/27281), [Self-Healing Production Patterns (Claude Lab)](https://claudelab.net/en/articles/api-sdk/claude-api-self-healing-agent-production-patterns)

---

### Pitfall 19: Tutor Mode Becoming Patronizing or Noisy

**Severity:** MINOR (UX-eroding, not catastrophic)
**Confidence:** MEDIUM (category-pattern reasoning + Google Colab Learn Mode design constraints)
**What goes wrong:**
Tutor-mode-on-by-default explains everything. For first 3 messages, useful; by message 30, the user is skimming. Worse modes:
- **Patronizing tone**: "Great question! Let me walk you through what a folder is..." (insulting)
- **Re-explaining**: explains `git commit` after the user has seen 5 commits already
- **Walls of text**: paragraph of explanation between every step
- **Non-actionable**: "We use containerization for portability and reproducibility..." (true but irrelevant)
- **Same-explanation-repeatedly** when same step recurs (every test run gets same intro)

User ragequits, switches to `--quiet`, never trusts tutor mode again.

**Why it happens:**
- "More words = more helpful" instinct
- LLM trained to be helpful, equates verbosity with helpfulness
- No "user has already learned this" tracking
- Difficulty calibrating: novice needs full explanation, learner needs hints, returner needs nothing

**How to avoid:**
- **Tutor mode = one-line "what just happened" + optional expansion** (e.g., "(?)" or `--explain` for more)
- **Learn-once tracking**: `~/.osbuilder/learned.json` notes concepts the user has been shown; subsequent occurrences default to one-liner ("Committed your changes.") instead of full explanation
- **Tone style guide**: declarative, second-person, one sentence. "Saved your work to git." Not "Let me explain what we just did..."
- **Cut "great question" / "let me walk you through" / "the reason we do this is" wherever they appear — boilerplate openers add noise without information
- **A/B test with non-developer users** before publish; measure "user fatigue" (skim rate, --quiet adoption rate)
- **Adaptive verbosity**: Phase 1 explains more (user's first build); Phase N+ explains less (user has context)

**Warning signs:**
- Same explanation appears in same build twice
- User's session adoption of `--quiet` rises after N messages
- Tutor outputs > 3 lines for routine steps
- Beta users report "felt like a tutorial I couldn't skip"

**Phase to address:**
Phase 5 (tutor mode tone style guide + one-line default + learn-once tracking), Phase 8 (UX testing with real non-developer beta users).

**Sources:** [Google Colab Learn Mode](https://blog.google/innovation-and-ai/technology/developers-tools/colab-updates/), [Theoutpost: Colab Learn Mode](https://theoutpost.ai/news-story/google-colab-introduces-learn-mode-to-turn-gemini-into-your-personal-coding-tutor-25254/), [Beyond the Vibes](https://blog.tedivm.com/guides/2026/03/beyond-the-vibes-coding-assistants-and-agents/)

---

### Pitfall 20: Clone-Runbook Forgets Step User Needs

**Severity:** MINOR (recoverable, but breaks the "clone on any machine" promise)
**What goes wrong:**
Generated README says "run `npm install && npm run dev`" — forgets to say `cd <folder>` first, forgets that user needs `node` installed, forgets the env file copy step, assumes `gh repo clone` works (requires `gh` auth). Common-person clones, hits failure, has no recovery path. PROJECT.md core promise: "describe → working app on private GitHub → cloneable on any machine." This pitfall directly threatens the core promise.

**Why it happens:**
- Author of the runbook is an LLM that has the project loaded — it skips "obvious" steps
- "Obvious" to an LLM is not obvious to a non-developer
- Runbook tested by author, who is also the LLM (no fresh-machine validation)
- "Common-person" assumptions fail: user may not know `cd`, may not have `git` installed, may not have a terminal open

**How to avoid:**
- **Clone-runbook template** with mandatory sections (every README is generated from this):
  1. Prerequisites (what you need installed) — with auto-detect/install offer
  2. Get the code (`gh repo clone <full-name>` AND `git clone https://...`)
  3. Enter the folder (`cd <folder>`)
  4. Configure (`cp .env.example .env`, then "edit and fill in...") with explicit list of vars
  5. Install deps (one command)
  6. Run (one command)
  7. Verify (visit URL / send request) — falsifiable success check
  8. Stuck? — `~/.osbuilder/help.md` link or "rerun `osbuilder doctor`"
- **Fresh-machine validation**: in CI, spin a fresh container/VM, follow the runbook step-by-step, fail the build if any step needs human improvisation
- **`osbuilder doctor` command**: verifies prereqs are installed and env is configured; if not, offers to fix; never blocks user with cryptic shell errors
- **Tutor mode in clone-runbook**: README itself includes plain-English explanations of each step; not just commands

**Warning signs:**
- README skips `cd` after clone
- Prerequisites section missing or incomplete
- Env file step assumes user knows what to fill in
- No "verify it worked" step
- Beta user reports "I cloned it but don't know what to do next"

**Phase to address:**
Phase 7 (Tech Writer role: README generator with template), Phase 8 (CI: fresh-machine validation matrix), Phase 8 (beta-test with non-developer users on a clean machine).

**Sources:** PROJECT.md core promise + general technical-writing best practice. [AI Coding Assistants for Beginners](https://www.frontendmentor.io/articles/ai-coding-assistants-for-beginners), [Beyond the Vibes](https://blog.tedivm.com/guides/2026/03/beyond-the-vibes-coding-assistants-and-agents/)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hand-write `package.json` instead of using `create-next-app` | Don't have to learn the scaffolder's flags | 10M-token spaghetti (Pitfall 1); upgrades break; non-idiomatic structure | **Never** |
| Skip duplication scan because "tests pass" | Faster phase close | 4× duplication in 12 months (Pitfall 2); maintenance debt; cascading bug fixes | **Never** for OSBuilder; only acceptable for one-off prototypes user explicitly marks throwaway |
| Increase reflection cap above 3 | Looks like better convergence | Drift past 3 makes things worse not better (Pitfall 3); empirical Aider data | **Never** without per-failure-class re-evaluation |
| Pass-through error text from `npm`/`pip`/`git` to user | Saves jargon-translation work | Common-person bounce; trust loss (Pitfall 12) | Only in `--advanced` mode |
| Auto-install Node via Homebrew without checking for `nvm`/`mise` | Single command works on most macs | Breaks user's existing version manager (Pitfall 13); permanent trust loss | **Never** without detection-first probe |
| Hardcode `/` path separator | Faster to write than `path.join` | Windows users get cryptic errors (Pitfall 14) | **Never** in scaffolder output |
| Read `GH_TOKEN` from `.env` instead of `gh auth` | Simpler integration | Token committed risk (Pitfall 15); auth-state drift | **Never** for the user-facing flow; CI can use `GH_TOKEN` because that's its design |
| Default to Postgres for every web app | One less question to ask | Wrong for offline/portable use cases (Pitfall 17) | When `--advanced` flag set AND user explicitly chose multi-user |
| Skip `state.md` updates when "phase is short" | Saves ~50 tokens | Unrecoverable on compaction (Pitfall 7) | **Never** |
| Add K8s/Helm "for production-readiness" without `--production-ready` flag | "Looks scalable" | Premature complexity trap (Pitfall 16); weeks of busywork; user can't run it | **Never** as default; opt-in only |
| Subagent invocations with "you have my context" prompts | Less prompt engineering | Subagents are stateless (Pitfall 9); silent context loss + bad outputs | **Never** — always pass structured context explicitly |
| Trust LLM-named packages without registry check | Faster scaffolding | Slopsquatting RCE (Pitfall 6) | **Never** — registry check is mandatory |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `gh` CLI | Use `GITHUB_TOKEN` env var concurrently with `gh auth login` | Detect both, halt and resolve before any `gh` action; prefer `gh auth login` flow + keychain |
| GitHub repo creation | Assume user has scope/permissions; not handle 422 conflict | Verify `gh auth scopes` includes `repo` before create; on 422, prompt rename or use existing |
| GitHub API rate limit | Bulk operations during scaffolding hit 5k/hr or secondary limits (100 concurrent) | Throttle to <60/min; respect Retry-After headers; classify `rate-limit` and back off |
| Supabase / Firebase auth | Generate auth, skip RLS / security rules verification | Reviewer must run "non-owner can't read owner's row" test; falsifiable check (Lovable RLS lesson) |
| Docker | `docker compose up` assumes Docker Desktop running; no detection | Preflight checks `docker info`; offers install/start before any compose command |
| Node version managers | Auto-`brew install node` on a mac with `nvm` | Probe for nvm/mise/asdf/volta first; route through the existing manager |
| Python | Touch system Python on macOS via brew | Always use `pyenv`/`uv`; never `brew install python` for app dependency |
| Tauri | Mismatched JS package vs Rust crate versions | `tauri info` check + version-pin both before scaffold finalize |
| npm/pnpm/yarn/bun | Ship `package-lock.json` while project uses `pnpm-lock.yaml` | Detect lockfile or `packageManager` field; emit only the right one; commit `.npmrc` if needed |
| Pre-commit secrets | Don't ship a hook; user commits `.env` | Scaffold installs `gitleaks` or simple regex-hook in `.git/hooks/pre-commit` on init |
| Sub-skills (`/gsd`, `/brainiac`, etc.) | Invoke without explicit context; assume they "share" parent state | Pass structured prompt with: goal + scoped paths + expected deliverable + success criteria |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Token burn from vibe-coding scaffold | First phase >100k tokens; many `package.json` edits | Mandatory deterministic scaffolder (Pitfall 1) | Always — fails first build for medium app |
| Compounding reflection cycles | Per-reflection token spend grows | Hard 3-cap + per-class strategy (Pitfalls 3, 4) | Reflection #4 onward |
| Subagent context-passing failure | Sub-skill produces irrelevant or generic output | Disk-grounded handoffs + structured prompts (Pitfalls 5, 9) | Any non-trivial subagent invocation |
| Auto-compaction mid-build | Long pause; resumed agent confused about state | `state.md` checkpoint + token watchdog at 75% (Pitfall 7) | Builds >25 minutes or >150k tokens |
| Multi-agent error cascade | Reviewer approves something that fails QA on grep | Disk-grounded inputs + verifier-as-fresh-subagent (Pitfall 5) | Builds with >4 role transitions |
| Duplication-driven refactor cost | Small change touches 8 near-duplicate files | Dup scanner + shared-modules manifest (Pitfall 2) | After ~5k LoC |
| GitHub API throttling | `gh` errors or 403 mid-build | Throttle <60/min + Retry-After respect | Bulk repo/issue creation flows |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing `.env` with real secrets | Token leakage; even private repos can leak via fork/PR/tarball | `.gitignore` `.env` from scaffold; pre-commit `gitleaks` hook; `gh auth` flow not env paste |
| Slopsquatted package via hallucination | Remote code execution on `postinstall` (Pitfall 6) | Registry verification + `--ignore-scripts` until verified + lockfile-first |
| Missing RLS / security rules in generated auth (Lovable lesson) | Anonymous user reads owner's data | Reviewer's falsifiable RLS test ("non-owner can't access owner's row") |
| Plain-text `gh` token storage | Token in backup, screen-share, tarball | Detect plain-text fallback in `gh auth status`; require keychain |
| LLM hallucinates "use this Auth0 client_secret" and fills value | Pasted dummy/leaked secret in code | Secrets must come from env or keychain; never hardcoded; pre-commit scan blocks |
| `package.json` `postinstall` runs arbitrary code | Supply-chain RCE on first install | Scaffolder-only origin + `--ignore-scripts` for unverified deps |
| Open repo creation defaults | Public repo when user wanted private | Default to `--private`; user must explicitly opt into `--public` (PROJECT.md constraint) |
| OSBuilder runs unsanitized user paragraph as shell | Prompt injection → command execution | All user input goes through LLM as data, never as shell; explicit command allowlist |
| Pushing the unredacted `state.md` to GitHub | Leaks user's local file paths, env, etc. | `.gitignore` `state.md`; or sanitize before commit |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Jargon in error messages | Bounce / give up (Pitfall 12) | Translation dictionary + 3-part friendly errors |
| "Responsive design?" as a question | User doesn't know the term | "Should it work on phones?" |
| No "I don't know, you decide" option | User stalls, can't answer | Every question has explicit-default escape |
| Tutor mode walls of text (Pitfall 19) | Skim/quit/--quiet | One-line + optional expansion |
| Patronizing tone ("Great question!") | Trust erosion | Declarative second-person, no boilerplate openers |
| Re-explaining concepts user already saw | Tedious | `learned.json` tracks shown concepts |
| Silent escalation (Pitfall 18) | "Now what?" confusion | Structured handoff: state + error + tried + 3 options |
| Clone-runbook missing `cd` (Pitfall 20) | First-clone fails | Mandatory template + fresh-machine CI validation |
| Default mismatch surfaced too late (Pitfall 17) | "Wait, why Postgres?" | Explain default at decision point + reversibility note |
| `osbuilder` ran successfully but app doesn't run | "Looks done but isn't" | Falsifiable verification: "user can do X with Y and observe Z" |
| Asking too many questions upfront | Decision fatigue | Ask only consequential axes; default the rest |
| Asking too few questions | Default mismatch | The "consequential axes" set must include DB shape, multi-user, offline, scale |
| Showing raw `npm install` output during preflight | Fear / confusion | Tutor narrates ("Installing packages..."); raw output behind expand |
| `osbuilder` repo name collision on GitHub | Cryptic 422 from gh | Pre-check name; offer rename or `-2` suffix |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but commonly miss critical pieces.

- [ ] **Scaffold phase:** Often missing — `package.json` was actually generated by a real scaffolder (not LLM). Verify: `git log --diff-filter=A package.json` shows scaffolder command, not freeform LLM diff.
- [ ] **Auth:** Often missing — RLS / security rules tested for non-owner access. Verify: explicit test "anonymous user GET /api/private returns 401" passes.
- [ ] **Dependencies:** Often missing — every dep verified to exist on registry before install. Verify: `npm ls` shows no `extraneous`, no `npm WARN missing`; lockfile present.
- [ ] **Tests pass but…** — Often missing — falsifiable user-facing success criteria (not just "tests green"). Verify: spec lists "user can do X with Y and observe Z" criteria; each has a passing assertion.
- [ ] **state.md:** Often missing — checkpoint reflects actual state (not a stale copy). Verify: timestamp within last phase boundary; all required fields populated.
- [ ] **Clone-runbook:** Often missing — fresh-machine validation. Verify: CI runs `gh repo clone` + steps in a fresh container, exits 0.
- [ ] **Cross-platform:** Often missing — actually tested on Windows (not just macOS + "should work"). Verify: CI matrix includes Windows; install script ran clean.
- [ ] **Preflight installer:** Often missing — version-manager detection before brew/apt. Verify: with `nvm` installed, preflight uses nvm not brew; with `pyenv` installed, preflight uses pyenv not system Python.
- [ ] **Reflection escalation:** Often missing — structured handoff format. Verify: simulate stuck build, output matches `{state, last_error, tried, 3 options}` shape.
- [ ] **Subagent calls:** Often missing — explicit context passing. Verify: prompt audit shows scoped artifact paths + success criteria; never "you have my context."
- [ ] **`.env` security:** Often missing — `.gitignore` includes `.env`; pre-commit hook installed. Verify: try `git add .env`, expect block.
- [ ] **Tutor mode:** Often missing — one-line default; verbose only on `--explain`. Verify: routine step output ≤ 1 line in default mode.
- [ ] **Deploy target lock-in:** Often missing — vendor names not hardcoded in default scaffold. Verify: grep scaffold output for `vercel`/`supabase`/`firebase` outside of `.env.example`.
- [ ] **`--production-ready`:** Often missing — adds named phases, not default code. Verify: without flag, no `Chart.yaml` / `Dockerfile.production` / etc. With flag, those are added as separate phases.
- [ ] **Composition rule:** Often missing — sub-skill capability not absorbed into OSBuilder. Verify: any new OSBuilder file scanned for "this exists in GSD/brainiac/predator already."
- [ ] **Non-developer testable:** Often missing — non-dev beta tester ran the full flow. Verify: at least one external-user test session before publish, with success criteria from PROJECT.md core promise.

---

## Recovery Strategies

When pitfalls occur despite prevention.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Vibe-coded scaffold (Pitfall 1) | HIGH | `git stash`, run real scaffolder in `tmp/`, port code over manually, abandon original `package.json` |
| Code duplication >5% (Pitfall 2) | MEDIUM | Run `jscpd` report, manually consolidate top-3 duplicate clusters into shared module, commit refactor |
| Drift past reflection 3 (Pitfall 3) | LOW (if caught) | Hard halt, dump state.md + last-error to user, don't retry, escalate |
| Naive retry burning tokens (Pitfall 4) | LOW | Halt, classify last error, route to correct strategy, resume from checkpoint |
| Multi-agent cascade (Pitfall 5) | HIGH | Halt entire build, audit each role's input vs disk truth, re-grounding from `state.md`, restart from earliest infected phase |
| Slopsquatted package (Pitfall 6) | HIGH (security incident) | `npm uninstall <bad>`, audit lockfile + `node_modules` for postinstall side-effects, rotate any secrets accessed during install, commit clean |
| Auto-compaction destroyed state (Pitfall 7) | LOW (if state.md current) | `/clear`, run `osbuilder continue` from `state.md` |
| SKILL.md description bloat (Pitfall 8) | LOW | Trim to 130 chars, move detail to `references/`, re-test trigger |
| Subagent context loss (Pitfall 9) | LOW | Re-invoke with structured context prompt; treat prior output as discardable |
| Deploy lock-in shipped (Pitfall 10) | MEDIUM | Replace vendor-specific config with env-based; add migration-path docs; commit |
| Validation-failure retried (Pitfall 11) | LOW | Halt, route to PM for re-plan; restore tests to original; restart phase from re-plan |
| Jargon leaked (Pitfall 12) | LOW | Add term to `references/jargon-translations.md`; re-run translation pass; ship |
| Preflight broke user system (Pitfall 13) | HIGH | Read `~/.osbuilder/install-log.json`; run `osbuilder undo-preflight`; document workaround |
| Cross-platform path break (Pitfall 14) | MEDIUM | Replace string path with `path.join`; add CI matrix entry for missing platform |
| Token leaked (Pitfall 15) | HIGH (security incident) | Rotate token immediately; force-push to remove; add `.gitignore` + pre-commit hook |
| K8s shipped without `--production-ready` (Pitfall 16) | MEDIUM | Move K8s files to a branch; restore default scaffold; add Architect role checklist |
| Wrong default DB (Pitfall 17) | MEDIUM | Migration script SQLite ↔ Postgres; user-data preserved; commit |
| Silent loop / unactionable escalation (Pitfall 18) | MEDIUM | Force-stop, write `state.md` from scratch by reading repo, hand structured handoff to user |
| Tutor mode patronizing (Pitfall 19) | LOW | Tone-revise template; add to `learned.json`; ship update |
| Clone-runbook gap (Pitfall 20) | LOW | Fresh-machine test, fix README, ship update |

---

## Pitfall-to-Phase Mapping

How OSBuilder roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase(s) | Verification |
|---------|---------------------|--------------|
| 1. Vibe-coded scaffold | Phase 1 (Architecture: scaffolder registry), Phase 2 (DevOps: enforce scaffolder-first) | `git log --diff-filter=A package.json` shows scaffolder origin |
| 2. AI duplication | Phase 2 (shared-modules manifest), Phase 4+ (Reviewer: dup scan), Phase 6 (QA: dup-ratio gate) | `jscpd` reports <5% duplication at every phase boundary |
| 3. Beyond-3-reflection drift | Phase 3 (self-healing loop: hard cap) | Synthetic stuck-build test; counter enforced by external state |
| 4. Naive retry / no classification | Phase 3 (failure classifier + per-class strategy table) | Synthetic injection of each failure class; observe correct routing |
| 5. Multi-agent cascade | Phase 1 (handoff schema + disk-grounding), Phase 4 (verifier-as-fresh-subagent), Phase 6 (QA: cascade detector) | DeepMind-style infection injection; verify cascade halts at first reviewer |
| 6. Slopsquatted package | Phase 2 (DevOps: registry-verification gate), Phase 7 (Watchdog) | Fake-package injection test; install blocked |
| 7. Auto-compaction destroys state | Phase 1 (state.md schema + checkpoint protocol), Phase 5 (token watchdog at 75%) | Force `/clear` mid-build; `osbuilder continue` resumes |
| 8. SKILL.md bloat | Phase 0 (skill scaffolding: line/char caps), Phase 8 (publish: trigger-test) | SKILL.md ≤200 lines; description ≤130 chars; trigger 10/10 right |
| 9. Subagent context loss / recursion | Phase 1 (depth budget + structured handoff), Phase 4 (sub-skill orchestration), Phase 5 (depth-4 graceful refusal) | Synthetic depth-4 invocation; expect refusal with reason |
| 10. Deploy lock-in / pricing trust | Phase 2 (vendor-neutral scaffold lint), Phase 6 (RLS auth-boundary verification), Phase 7 (migration-path docs) | grep scaffold for vendor names; non-owner RLS test |
| 11. Validation-failure retried (not re-planned) | Phase 3 (classifier routes validation→re-plan), Phase 6 (test-tampering detector) | Inject failing test; verify re-plan, not retry; verify Reviewer flags weakened tests |
| 12. Jargon leaks | Phase 0 (jargon dictionary scaffold), Phase 5 (translation pass), Phase 8 (non-dev user testing) | Lint scan: 0 untranslated terms in user-facing strings |
| 13. Preflight breaks system | Phase 5 (detection-first preflight + rollback log + dry-run) | Test on macs with nvm/mise/asdf installed; verify routes through them |
| 14. Cross-platform path/shell | Phase 2 (cross-platform script template + .gitattributes), Phase 5 (per-platform decision trees), Phase 8 (CI matrix) | Cross-platform CI green on macOS+Linux+Windows+WSL |
| 15. gh CLI auth drift / token leak | Phase 5 (auth preflight + secret-scan hook), Phase 7 (Security: full leak audit) | `gh auth status` clean; `gitleaks` scan clean; `git add .env` blocked |
| 16. Scope creep / premature complexity | Phase 1 (refuse-list defined), Phase 4 (every role checks refuse-list), milestone reviews | No K8s/Helm/microservices in default scaffold; `--production-ready` adds named phases only |
| 17. Default mismatch | Phase 4 (PM outcome-framed clarification), Phase 5 (tutor explains defaults at decision points) | Question audit: each consequential axis surfaced; defaults explained inline |
| 18. Silent loop / bad escalation | Phase 3 (cap enforcement), Phase 5 (structured-handoff UX + diagnostic bundle), Phase 6 (QA: simulate stuck builds) | Stuck-build sim outputs structured handoff matching schema |
| 19. Tutor patronizing/noisy | Phase 5 (tone style guide + one-line default + learned.json), Phase 8 (non-dev UX testing) | Routine step output ≤1 line; learned-once tracking active |
| 20. Clone-runbook gaps | Phase 7 (Tech Writer: README template), Phase 8 (fresh-machine CI validation) | Fresh-container CI: clone → run → verify exits 0 with no human improv |

---

## Sources

### Documented Postmortems / Studies
- [Bolt.new Review 2025: Token Consumption Issues](https://trickle.so/blog/bolt-new-review)
- [Stop! Don't Use Bolt AI 2025 (Medium)](https://medium.com/@officewajidali/stop-dont-use-bolt-ai-2025-until-you-read-this-guide-1cd527350ddc)
- [Bolt.new Maximizing Token Efficiency](https://support.bolt.new/docs/maximizing-token-efficiency)
- [V0 vs Bolt vs Lovable Comparison 2026](https://www.nxcode.io/resources/news/v0-vs-bolt-vs-lovable-ai-app-builder-comparison-2025)
- [Why I'm Leaving Vercel and v0 (Medium)](https://medium.com/@baytbyte/why-im-sadly-leaving-vercel-and-v0-when-all-in-one-turns-into-all-for-money-368c3a976df3)
- [Two Days, Two Hacks: Lovable Disclosure (DEV.to)](https://dev.to/jon_at_backboardio/two-days-two-hacks-the-lovable-disclosure-and-the-pattern-nobody-wants-to-talk-about-47eh)
- [Vercel/Lovable/Copilot Hacked (Engineers Corner)](https://engineerscorner.in/ai-tools-security-breach-vercel-lovable-2026/)
- [Migration from Lovable Cloud to Vercel](https://nextbigwhat.com/how-to-migrate-from-lovable-cloud-to-vercel-and-take-control-of-your-stack/)
- [GitClear AI Copilot Code Quality 2025 Research](https://www.gitclear.com/ai_assistant_code_quality_2025_research)
- [GitClear PDF Report (S3)](https://gitclear-public.s3.us-west-2.amazonaws.com/GitClear-AI-Copilot-Code-Quality-2025.pdf)
- [LeadDev: AI compounds technical debt](https://leaddev.com/technical-direction/how-ai-generated-code-accelerates-technical-debt)
- [SoftwareSeni: Evidence Against Vibe Coding](https://www.softwareseni.com/the-evidence-against-vibe-coding-what-research-reveals-about-ai-code-quality/)

### Multi-Agent Failure Research
- [The Multi-Agent Trap (Towards Data Science)](https://towardsdatascience.com/the-multi-agent-trap/)
- [Why Multi-Agent LLM Systems Fail (2026 Guide)](https://futureagi.substack.com/p/why-do-multi-agent-llm-systems-fail)
- [From Spark to Fire: Modeling Error Cascades (arXiv)](https://arxiv.org/html/2603.04474v1)
- [AgentMesh paper (arXiv)](https://arxiv.org/html/2507.19902v1)
- [MetaGPT paper (OpenReview)](https://openreview.net/forum?id=VtmBAGCN7o)

### Aider Reflection Cap
- [Aider issue #1440: Only 3 reflections allowed](https://github.com/paul-gauthier/aider/issues/1440)
- [Aider issue #3450: max_reflections meaning](https://github.com/Aider-AI/aider/issues/3450)
- [Aider issue #3865: Add config for max_reflections](https://github.com/Aider-AI/aider/issues/3865)
- [Aider Advanced Model Settings](https://aider.chat/docs/config/adv-model-settings.html)

### Self-Healing AI Production Patterns
- [The Self-Healing Agent Pattern (DEV.to)](https://dev.to/the_bookmaster/the-self-healing-agent-pattern-how-to-build-ai-systems-that-recover-from-failure-automatically-3945)
- [Building Self-Healing AI Agents (Claude Lab)](https://claudelab.net/en/articles/api-sdk/claude-api-self-healing-agent-production-patterns)
- [Self-Healing Lessons from 70+ Production Bugs (DEV.to)](https://dev.to/_d7eb1c1703182e3ce1782/how-to-build-a-self-healing-ai-agent-system-lessons-from-70-production-bugs-2nep)
- [How to Build a Self-Healing AI Agent Pipeline (DEV.to)](https://dev.to/miso_clawpod/how-to-build-a-self-healing-ai-agent-pipeline-a-complete-guide-95b)

### Slopsquatting / Package Hallucination
- [AI-hallucinated dependencies (BleepingComputer)](https://www.bleepingcomputer.com/news/security/ai-hallucinated-code-dependencies-become-new-supply-chain-risk/)
- [Slopsquatting (Aikido)](https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks)
- [Slopsquatting (Trend Micro)](https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/slopsquatting-when-ai-agents-hallucinate-malicious-packages)
- [The Hallucinated Package Attack (Mend.io)](https://www.mend.io/blog/the-hallucinated-package-attack-slopsquatting/)
- [AI-Hallucinated Dependencies in PyPI/npm (Rescana)](https://www.rescana.com/post/ai-hallucinated-dependencies-in-pypi-and-npm-the-2025-slopsquatting-supply-chain-risk-explained)

### Claude Code Skill / Compaction / Subagents
- [Anthropic: Equipping agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Code skill docs](https://code.claude.com/docs/en/skills)
- [Anthropic skills repo: skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Context Rot in Claude Skills (MindStudio)](https://www.mindstudio.ai/blog/context-rot-claude-code-skills-bloated-files)
- [Skill budget research gist](https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1)
- [Context Window & Compaction (DeepWiki)](https://deepwiki.com/anthropics/claude-code/3.3-context-window-and-compaction)
- [Claude Code troubleshooting](https://code.claude.com/docs/en/troubleshooting)
- [Persistent state across compaction issue #25999](https://github.com/anthropics/claude-code/issues/25999)
- [Auto-compact bug #3274](https://github.com/anthropics/claude-code/issues/3274)
- [Auto-compact fails at 200k #48893](https://github.com/anthropics/claude-code/issues/48893)
- [Compaction destroyed my work (DEV.to)](https://dev.to/mikeadolan/claude-code-compaction-kept-destroying-my-work-i-built-hooks-that-fixed-it-2dgp)
- [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents)
- [Settings pollution in subagents (Egghead)](https://egghead.io/avoid-the-dangers-of-settings-pollution-in-subagents-hooks-and-scripts~xrecv)
- [Infinite loop bug #27281](https://github.com/anthropics/claude-code/issues/27281)
- [Subagents-spawning-subagents OOM #4850](https://github.com/anthropics/claude-code/issues/4850)
- [Codex rescue infinite recursion #234](https://github.com/openai/codex-plugin-cc/issues/234)

### gh CLI / GitHub Integration
- [gh wants GH_TOKEN even when logged in #8347](https://github.com/cli/cli/discussions/8347)
- [GITHUB_TOKEN auth issue #2922](https://github.com/cli/cli/issues/2922)
- [gh auth status incorrect GITHUB_TOKEN report #7800](https://github.com/cli/cli/issues/7800)
- [GitHub CLI auth confusion (Sommerfeld)](https://www.henriksommerfeld.se/github-cli-auth-confusion-using-github-token/)
- [GitHub CLI manual: gh auth login](https://cli.github.com/manual/gh_auth_login)
- [GitHub API rate limits (Lunar.dev)](https://www.lunar.dev/post/a-developers-guide-managing-rate-limits-for-the-github-api)
- [GitHub Apps rate limits docs](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/rate-limits-for-github-apps)
- [Do gh CLI commands use REST APIs (rate limits) #5381](https://github.com/cli/cli/discussions/5381)

### Cross-Platform / Tauri
- [Cross-platform PowerShell tips](https://powershell.org/2019/02/tips-for-writing-cross-platform-powershell-code/)
- [PowerShell path separator OS detection](https://rakhesh.com/powershell/powershell-path-separator-based-on-os/)
- [Cross-platform Node shell scripts (exploringjs)](https://exploringjs.com/nodejs-shell-scripting/ch_creating-shell-scripts.html)
- [Azure Pipelines cross-platform scripting](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/cross-platform-scripting?view=azure-devops)
- [Tauri version mismatch issue #13960](https://github.com/tauri-apps/tauri/issues/13960)
- [Tauri 2.0 docs](https://v2.tauri.app/)

### Common-Person UX / Tutor Mode
- [Beyond the Vibes: Rigorous Guide to AI Coding Assistants (tedious ramblings)](https://blog.tedivm.com/guides/2026/03/beyond-the-vibes-coding-assistants-and-agents/)
- [AI Coding Assistants for Beginners (Frontend Mentor)](https://www.frontendmentor.io/articles/ai-coding-assistants-for-beginners)
- [Google Colab Learn Mode introduction](https://blog.google/innovation-and-ai/technology/developers-tools/colab-updates/)
- [Colab Learn Mode coverage (theoutpost)](https://theoutpost.ai/news-story/google-colab-introduces-learn-mode-to-turn-gemini-into-your-personal-coding-tutor-25254/)
- [Examining AI Code Assistant Impact (CHI 2026)](https://dl.acm.org/doi/10.1145/3706599.3706670)
- [Developer Experiences with Contextualized AI (CAIN/ICSE)](https://dl.acm.org/doi/10.1145/3644815.3644949)

### Project Context
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/.planning/PROJECT.md` (constraints, decisions, out-of-scope)

---

*Pitfalls research for: AI-driven app builder Claude Code skill (OSBuilder)*
*Researched: 2026-04-29*
