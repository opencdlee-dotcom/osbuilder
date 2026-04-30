# Architecture Research

**Domain:** Claude Code skill that orchestrates other skills (a virtual dev studio)
**Researched:** 2026-04-29
**Confidence:** HIGH (Anthropic official docs + direct inspection of installed skill ecosystem)

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                       USER (the "common person")                      │
│        types: /osbuilder "I want a site that grades lab notebooks"   │
└──────────────────────────────────────────────┬───────────────────────┘
                                               │
┌──────────────────────────────────────────────▼───────────────────────┐
│                        OSBUILDER SKILL (this repo)                    │
│                                                                       │
│   ┌────────────────────────────────────────────────────────────────┐ │
│   │                        SKILL.md (≤ 200 lines)                   │ │
│   │  Orchestrator: routes to playbooks, manages role state machine  │ │
│   └─────┬───────────────────────────────────────────────────────┬──┘ │
│         │                                                       │     │
│   ┌─────▼──────────┐   ┌───────────────────┐   ┌───────────────▼───┐ │
│   │   references/  │   │     scripts/      │   │     examples/     │ │
│   │  (loaded JIT)  │   │  (executed JIT)   │   │  (3-5 ref apps)   │ │
│   ├────────────────┤   ├───────────────────┤   └───────────────────┘ │
│   │ playbooks/     │   │ classify_failure  │                         │
│   │ roles/         │   │ preflight_*       │                         │
│   │ preflight/     │   │ scaffold_dispatch │                         │
│   │ ux/            │   │ state_update      │                         │
│   │ failure-       │   │ os_detect         │                         │
│   │   classifier/  │   └───────┬───────────┘                         │
│   └────────────────┘           │                                     │
└────────────────────────────────┼─────────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────────┐
│                  EXISTING SKILL ECOSYSTEM (delegated)                 │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ brainiac │  │   gsd-*  │  │ predator │  │  code-   │  │ gsd-   │ │
│  │ research │  │ commands │  │  audit   │  │  tester  │  │ debug  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│  ┌──────────┐  ┌──────────────────────────────────────────────────┐  │
│  │ problem- │  │            architect-loop (Ralph)                 │  │
│  │  solver  │  │   (optional: story-by-story execution mode)       │  │
│  └──────────┘  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                    BUILT APP (the user's project)                     │
│                                                                       │
│   project-root/                                                       │
│   ├── .planning/         ← GSD's planning dir (PROJECT, REQS, ROADMAP)│
│   │   └── osbuilder/     ← OSBuilder's per-app state (state.md, etc.) │
│   ├── src/               ← scaffolded code (create-next-app etc.)     │
│   ├── .env.example                                                    │
│   ├── Dockerfile                                                      │
│   ├── .github/workflows/ci.yml                                        │
│   └── README.md          ← clone-and-run runbook                      │
│                                                                       │
│                          ↓ pushed to                                   │
│                  PRIVATE GITHUB REPO (gh CLI)                         │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **SKILL.md** | Entry point, role state machine, routing table to playbooks/roles, cross-cutting rules (privacy, refusals, escalation) | Markdown ≤ 200 lines, YAML frontmatter, links one level deep into `references/` |
| **references/playbooks/** | Per-app-type recipes (web, CLI, desktop, hub-style) — what stack, scaffolder, deps, structure | Markdown, one file per app type, ~150-300 lines each |
| **references/roles/** | Per-role briefs (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer) — what they do, which sub-skill they delegate to, handoff schema | Markdown, one file per role, ~80-150 lines each |
| **references/preflight/** | OS-specific install commands (macOS / Linux / Windows) for Node, Python, git, gh, Docker | Markdown checklists with copy-pasteable bash/PowerShell |
| **references/ux/** | Plain-English question banks, friendly error translations, tutor-mode narration templates | Markdown |
| **references/failure-classifier/** | Decision trees: transient vs context-overflow vs tool-failure vs validation-failure; what to do per class | Markdown matrix + linked Python helper |
| **scripts/** | Deterministic helpers — failure classification, OS detect, scaffolder dispatch, state.md update, preflight checks | Python 3 scripts (uses stdlib only — no install needed); bash for trivial ops |
| **examples/** | 3-5 reference apps OSBuilder has built (gallery for users + regression bench) | Sub-directories with screenshots + before/after spec |
| **State checkpoint (`state.md`)** | Resume-after-`/clear` memory: goal, phase, role, last failure, retry count | ~15 line markdown, lives in **the built app's** `.planning/osbuilder/state.md` |
| **Sub-skill ecosystem** | All actual heavy lifting (research, planning, code review, testing, debug) — OSBuilder NEVER reimplements | Existing `gsd-*`, `brainiac`, `predator`, `code-tester`, `problem-solver`, `gsd-debug` skills |

---

## Recommended Project Structure

```
~/.claude/skills/osbuilder/
├── SKILL.md                          # ≤ 200 lines — orchestrator + routing
├── README.md                         # for humans browsing GitHub
├── install.sh                        # one-liner installer
├── update.sh                         # update without losing user state
│
├── references/                       # JIT-loaded by Claude
│   ├── playbooks/                    # per-app-type recipes
│   │   ├── web-app.md                # Next.js + Postgres + Tailwind path
│   │   ├── ai-service.md             # FastAPI + Pydantic + uv path
│   │   ├── desktop-app.md            # Tauri 2 + Vite path
│   │   ├── cli-tool.md               # Python (uv) or Rust (cargo) path
│   │   ├── hub-platform.md           # Professor-Hub-style umbrella workspace
│   │   └── mobile-web.md             # responsive web (NOT native, scoped out v1)
│   │
│   ├── roles/                        # virtual dev studio role briefs
│   │   ├── pm.md                     # → /gsd-spec-phase, /gsd-discuss-phase
│   │   ├── architect.md              # → /gsd-plan-phase + /brainiac
│   │   ├── frontend.md               # → /gsd-execute-phase (UI tasks)
│   │   ├── backend.md                # → /gsd-execute-phase (API tasks)
│   │   ├── devops.md                 # → /gsd-execute-phase (CI/Docker)
│   │   ├── qa.md                     # → /code-tester + /gsd-verify-work
│   │   ├── reviewer.md               # → /predator + /gsd-code-review
│   │   └── tech-writer.md            # → /gsd-docs-update
│   │
│   ├── preflight/                    # OS-specific install paths
│   │   ├── macos.md                  # brew install ...
│   │   ├── linux.md                  # apt/dnf/pacman matrix
│   │   ├── windows.md                # winget / scoop
│   │   └── detect.md                 # how to pick the right file
│   │
│   ├── ux/                           # common-person UX
│   │   ├── question-bank.md          # plain-English Q's with "you decide" defaults
│   │   ├── friendly-errors.md        # stack trace → plain English mappings
│   │   ├── tutor-narration.md        # "what just happened" templates
│   │   └── progress-narration.md     # PM/Architect/Frontend dev-team voice
│   │
│   ├── failure-classifier/
│   │   ├── matrix.md                 # transient / context-overflow / tool / validation
│   │   ├── retry-policy.md           # 3-cap (Aider), backoff, escalation triggers
│   │   └── escalation-handoff.md     # structured handoff format when capping
│   │
│   ├── handoffs/                     # data flow between roles (schemas)
│   │   ├── pm-to-architect.md        # SPEC.md schema
│   │   ├── architect-to-builders.md  # PLAN.md schema (uses GSD's)
│   │   ├── builder-to-qa.md          # COMPLETION.md schema
│   │   └── qa-to-reviewer.md         # VERIFICATION.md schema
│   │
│   └── ship/                         # final delivery path
│       ├── github-private.md         # gh repo create --private + push
│       ├── runbook-template.md       # README clone-and-run section
│       └── env-template.md           # .env.example pattern
│
├── scripts/                          # deterministic helpers (executed, not read)
│   ├── classify_failure.py           # stdin: error text → stdout: category JSON
│   ├── os_detect.py                  # → macos|linux|windows + arch
│   ├── preflight_check.py            # which tools missing? returns JSON
│   ├── scaffold_dispatch.py          # app-type → exact scaffolder cmd
│   ├── state_update.py               # write/read state.md atomically
│   ├── retry_counter.py              # persists retry-cap state per phase
│   └── narrate.py                    # progress narration helper (dev-team voice)
│
├── templates/                        # files copied verbatim into built app
│   ├── README.runbook.md
│   ├── .env.example
│   ├── .gitignore.web
│   ├── .gitignore.python
│   ├── Dockerfile.next
│   ├── Dockerfile.fastapi
│   ├── docker-compose.postgres.yml
│   └── github-actions.ci.yml
│
└── examples/                         # gallery (3-5 reference apps)
    ├── README.md                     # index of examples
    ├── lab-notebook-grader/          # the canonical Charlie example
    ├── todo-cli/                     # smallest-possible example
    ├── recipe-hub/                   # hub-platform example
    └── ai-summarizer/                # AI service example
```

### Structure Rationale

- **`references/playbooks/`**: Each app type has very different scaffolder commands, dep lists, DB choices, and CI templates. Co-locating them as one file each (Anthropic's *Pattern 2 — domain-specific organization*) keeps token use down and lets Claude grep for "next.js" or "fastapi" without loading the whole library.
- **`references/roles/`**: Mirrors the dev-studio metaphor 1:1 — when the orchestrator says "now Architect takes over", it loads `roles/architect.md` which contains both the *narration* ("Architect is sketching the data model...") and the *delegation contract* (which sub-skill, with what input).
- **`references/handoffs/`**: Explicit schemas for the data passed between roles. Without these, role transitions become a re-prompt-from-scratch problem; with them, each handoff is a small, well-typed file commit.
- **`references/preflight/{os}.md`**: One-level-deep per Anthropic guidance. `os_detect.py` returns a string that maps to a file name — no nested references.
- **`scripts/`**: Pure-stdlib Python so OSBuilder works on a fresh machine before any preflight has run (the chicken-and-egg problem of installing Node/Docker via a tool that requires Node/Docker).
- **`templates/`**: Files copied **verbatim** — these are not for Claude to read, they're for the build pipeline to drop into the new project. Keeping them out of `references/` clarifies intent.
- **`examples/`**: Required for open-source publish-ready bar. Doubles as a regression bench — re-run OSBuilder on each example periodically and diff.

---

## Architectural Patterns

### Pattern 1: Orchestrator-with-Playbooks (Anthropic's Pattern 1 + 2 fused)

**What:** SKILL.md stays small; per-app-type recipes live in `references/playbooks/*.md`; per-role briefs live in `references/roles/*.md`. The orchestrator routes to the right playbook based on a single classification step, then walks the role state machine, loading one role brief at a time.

**When to use:** Any time SKILL.md would grow past ~200 lines because it's juggling multiple distinct workflows (web vs CLI vs desktop vs hub).

**Trade-offs:**
- Pro: SKILL.md stays scannable; new app types are additive (drop a new file in `playbooks/`); token use is bounded.
- Con: Routing logic lives in SKILL.md and must stay sharp — bad routing → wrong playbook → wasted work. Mitigation: explicit decision tree in SKILL.md with concrete triggers.

**Example (in SKILL.md):**

```markdown
## Routing Decision Tree

After PM phase produces SPEC.md, classify the app type:

| Signal in SPEC.md | App type | Playbook |
|-------------------|----------|----------|
| "users", "login", "browser", "responsive" | web-app | playbooks/web-app.md |
| "AI", "model", "completion", "embedding" + API | ai-service | playbooks/ai-service.md |
| "runs on my computer", "offline", "tray icon" | desktop-app | playbooks/desktop-app.md |
| "command line", "script", "terminal" | cli-tool | playbooks/cli-tool.md |
| "platform", "multiple tools under one umbrella" | hub-platform | playbooks/hub-platform.md |

If signals are ambiguous, ask the user one disambiguating question (see ux/question-bank.md).
```

---

### Pattern 2: Role State Machine via state.md

**What:** OSBuilder tracks current role + phase in a single file (`state.md`) inside the built app's `.planning/osbuilder/`. Every role transition is a `state_update.py` call. After `/clear` or context compaction, the resume protocol is: read state.md, load that role's brief, continue.

**When to use:** Any orchestrator that runs longer than one `/clear` cycle (which is every non-trivial OSBuilder build).

**Trade-offs:**
- Pro: Compaction-survivable; ~15 lines so it costs almost nothing to re-load; greppable; commits with the project.
- Con: Must be **atomically** updated (race-free); must be the **single source of truth** (no parallel mental state in conversation).

**`state.md` schema (~15 lines):**

```markdown
# OSBuilder State

goal: "A website where students upload lab notebooks and I grade them"
app_type: web-app
playbook: references/playbooks/web-app.md
project_root: /Users/charlie/projects/lab-grader
github_repo: charlielee/lab-grader (private)

current_role: backend
current_phase: 3  # references GSD's ROADMAP.md phase 3
phase_step: execute  # discuss | plan | execute | verify

last_action: "Backend dev finished POST /upload endpoint"
last_failure: null  # or: "code-tester found SQL injection in /search"
retry_count: 0  # caps at 3 per failure (Aider's limit)
escalation_level: none  # none | gsd-debug | problem-solver | user-handoff

next_action: "QA pass with /code-tester on src/api/upload.py"
updated_at: 2026-04-29T15:22:18Z
```

---

### Pattern 3: Skill Composition via Slash Commands (NOT Re-implementation)

**What:** OSBuilder invokes existing skills by their slash-command surface (`/gsd-spec-phase`, `/brainiac deep <topic>`, `/predator hunt`, `/code-tester [target]`, `/gsd-debug`). It treats them as black boxes — outputs only.

**When to use:** Always, for any work that an existing skill already does.

**Trade-offs:**
- Pro: Avoids the duplication failure mode (GitClear's 4× duplication finding); fixes flow back upstream.
- Con: Skill-version drift — if `/gsd-spec-phase`'s output schema changes, OSBuilder must adapt. Mitigation: pin a minimum version in SKILL.md frontmatter; check on first run; ask user to update.

**Invocation modes (when to use which):**

| Mode | Use when | How |
|------|----------|-----|
| **SlashCommand inline** | Short, deterministic step (e.g., `/gsd-progress`) | Emit the command verbatim; let Claude execute |
| **Task-tool subagent** | Long-running, context-heavy work that would bloat main context (e.g., `/code-tester` on a 50-file backend) | Spawn via `Task` tool with role brief as system prompt; receive structured return |
| **Direct skill load** | Reading a sub-skill's reference (rare — usually a smell) | Only for cross-skill consultation; prefer slash-command |

**Default rule:** prefer Task-tool subagents for QA, Reviewer, and Architect (research-heavy) phases; prefer inline SlashCommand for PM, DevOps, and Tech Writer phases.

---

### Pattern 4: Failure Classification Before Retry (Self-Healing)

**What:** When any phase fails, pipe the error through `scripts/classify_failure.py`, which returns one of `transient | context-overflow | tool-failure | validation-failure | unknown`. Per-class strategies in `references/failure-classifier/matrix.md`. Hard cap of 3 retries (Aider's empirically validated limit).

**When to use:** Every failure, no exceptions. Naive retry loops are the documented anti-pattern.

**Trade-offs:**
- Pro: ~94% auto-resolution achievable per production self-healing literature; user is only interrupted for genuinely novel failures.
- Con: Classifier must be kept current as new failure modes appear; budget for an "unknown" bucket that escalates fast.

**Failure → action matrix (concrete):**

| Class | Triggers | Action | Retry? |
|-------|----------|--------|--------|
| **transient** | network timeout, rate-limit-429, gh-cli temp failure | exponential backoff (1s, 4s, 16s) | up to 3 |
| **context-overflow** | "context length", auto-compaction fired mid-task | force-write state.md, `/clear`, resume from state.md | once, then escalate |
| **tool-failure** | scaffolder errored, npm install failed, port in use | run preflight remediator from `preflight/` | up to 3 different fixes |
| **validation-failure** | code-tester found bug, predator flagged debt, user UAT rejected | invoke `/gsd-debug` first, then `/problem-solver` | 3 cap; on hit → escalate |
| **unknown** | doesn't match any pattern | escalate immediately with structured handoff | 0 |

---

### Pattern 5: Deterministic Scaffolders First (No Hand-Written Boilerplate)

**What:** Always start a new app from a published scaffolder (`create-next-app`, `create-t3-app`, `npm create vite`, `cargo new`, `uv init`) where one exists. Hand-write nothing that the scaffolder produces. OSBuilder owns only the **deltas** (the user-specific code, env templates, CI tweaks).

**When to use:** Every new build, full stop.

**Trade-offs:**
- Pro: Saves ~10M tokens per medium app vs Bolt.new-style generation; produces idiomatic, community-blessed structure; is reproducible (same scaffolder → same skeleton).
- Con: Locked to the scaffolder's choices for the skeleton — but those are exactly the choices we want defaulted.

**Dispatch script (`scripts/scaffold_dispatch.py`):**

```python
# Pseudocode
APP_TYPE_TO_SCAFFOLD = {
  "web-app": "npx create-next-app@latest {name} --typescript --tailwind --app --use-pnpm",
  "ai-service": "uv init {name} --package && uv add fastapi pydantic uvicorn",
  "desktop-app": "npm create tauri-app@latest {name} -- --template react-ts",
  "cli-tool-py": "uv init {name}",
  "cli-tool-rust": "cargo new {name}",
  "hub-platform": "mkdir {name} && cd {name} && git init && <emit Professor-Hub structure>",
}
```

---

## Data Flow

### Build Pipeline (Intake → Ship)

```
  USER
    │ "/osbuilder I want a website where students upload lab notebooks"
    ▼
┌─────────────┐
│  INTAKE     │  SKILL.md routes; ux/question-bank.md fills gaps with plain-English Q's
│  (PM phase) │  → invokes: /gsd-new-project --auto with derived spec
└──────┬──────┘  → produces: .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md (via GSD)
       │
       ▼
┌─────────────┐
│  RESEARCH   │  Architect role: "what's the modern stack for this?"
│ (Architect) │  → invokes: /brainiac deep "<spec-derived topic>"
└──────┬──────┘  → produces: .planning/research/STACK.md, ARCHITECTURE.md, FEATURES.md
       │
       ▼
┌─────────────┐
│  SCAFFOLD   │  DevOps role: pick scaffolder via scripts/scaffold_dispatch.py
│  (DevOps)   │  → runs: create-next-app / uv init / cargo new / etc.
└──────┬──────┘  → produces: working empty project + .env.example + Dockerfile + CI yml
       │
       ▼
┌─────────────┐
│   PLAN      │  Architect role: per-phase planning
│ (Architect) │  → invokes: /gsd-plan-phase N (one per ROADMAP phase)
└──────┬──────┘  → produces: .planning/<phase>/PLAN.md (atomic XML tasks)
       │
       ▼
┌─────────────┐
│   BUILD     │  Frontend / Backend / DevOps roles execute by phase
│ (3 roles)   │  → invokes: /gsd-execute-phase N
└──────┬──────┘  → produces: src/* code + per-task git commits
       │
       ▼
┌─────────────┐
│   VERIFY    │  QA role + Reviewer role (every phase, both)
│ (QA + Rev)  │  → QA invokes: /code-tester + /gsd-verify-work
└──────┬──────┘  → Reviewer invokes: /predator + /gsd-code-review
       │           → produces: .planning/<phase>/VERIFICATION.md
       │           → on failure: classify → retry (cap 3) → /gsd-debug → /problem-solver → user
       ▼
┌─────────────┐
│    DOCS     │  Tech Writer role: README runbook + clone-and-run flow
│ (TechWrite) │  → invokes: /gsd-docs-update
└──────┬──────┘  → produces: README.md with preflight + run command
       │
       ▼
┌─────────────┐
│    SHIP     │  DevOps role: gh repo create --private; push
│  (DevOps)   │  → runs: gh repo create + git push + verify clone-fresh works
└──────┬──────┘  → produces: private GitHub repo URL returned to user
       │
       ▼
   USER: cloneable on any machine; opens README; runs the one documented command.
```

### State Storage Locations

| What | Where | Why |
|------|-------|-----|
| User's project files | `<project-root>/` (chosen by user, e.g., `~/projects/lab-grader`) | Standard project location |
| GSD planning artifacts | `<project-root>/.planning/` | GSD's own convention — OSBuilder respects it |
| OSBuilder per-build state | `<project-root>/.planning/osbuilder/state.md` | Co-located with the build it describes; commits with the project so the user owns their resume token |
| OSBuilder per-build retry counters | `<project-root>/.planning/osbuilder/retries.json` | Persists across `/clear` |
| OSBuilder per-build narration log | `<project-root>/.planning/osbuilder/narration.log` | For tutor-mode replay |
| OSBuilder skill itself | `~/.claude/skills/osbuilder/` | Standard Claude Code skill location |
| OSBuilder global config (preflight cache, etc.) | `~/.osbuilder/` | Shared across all builds; not per-project |
| Examples gallery (regression bench) | `~/.claude/skills/osbuilder/examples/` | Ships with the skill |

### Per-Phase Handoff Contracts

Every role transition writes a handoff file. Schemas (in `references/handoffs/`):

| From → To | File | Key fields |
|-----------|------|------------|
| User → PM | (verbal) | raw description string |
| PM → Architect | `.planning/PROJECT.md` + `.planning/REQUIREMENTS.md` | vision, scope, REQ-IDs |
| Architect → DevOps (Scaffold) | `state.md: app_type, playbook` | which scaffolder, which deps |
| Architect → Builder roles | `.planning/<phase>/PLAN.md` (GSD's XML schema) | atomic tasks with verify+done criteria |
| Builder → QA | git diff since `phase_start` SHA | what changed, file paths |
| QA → Reviewer | `.planning/<phase>/VERIFICATION.md` (UAT results) | pass/fail, falsifiable criteria |
| Reviewer → Tech Writer | `.planning/<phase>/SUMMARY.md` | what was built, gotchas |
| Tech Writer → DevOps (Ship) | updated README.md | runbook is correct |
| DevOps (Ship) → User | GitHub URL + clone command | the deliverable |

---

## Role-to-Skill Mapping (Complete)

This is the **delegation contract** OSBuilder enforces. Each role's brief lives in `references/roles/<role>.md` and contains: narration template, sub-skill invocation, input schema, output schema, failure handling.

| Role | Primary Skill | Support Skill(s) | When |
|------|---------------|------------------|------|
| **PM** | `/gsd-new-project --auto` (intake) → `/gsd-spec-phase` per phase | `/gsd-discuss-phase` for context | Every build, once at start; once per phase for context |
| **Architect** | `/gsd-plan-phase N` | `/brainiac deep <topic>` (stack research) | Once per phase, plus once at project start for stack research |
| **Frontend dev** | `/gsd-execute-phase N` (UI tasks only) | `/gsd-ui-phase` for UI-heavy phases | Per phase, when PLAN.md has FE tasks |
| **Backend dev** | `/gsd-execute-phase N` (API/data tasks) | — | Per phase, when PLAN.md has BE tasks |
| **DevOps** | `/gsd-execute-phase N` (CI/Docker/scripts tasks) | `scripts/scaffold_dispatch.py` (scaffold step) + `gh` CLI (ship step) | Scaffold (once, start), CI (every phase), Ship (once, end) |
| **QA** | `/code-tester [target] full normal` | `/gsd-verify-work N` | After every Builder phase, before Reviewer |
| **Reviewer** | `/predator hunt <project-root>` | `/gsd-code-review` | After QA, before phase marked done |
| **Tech Writer** | `/gsd-docs-update` | — | Before Ship; also per phase if user docs are part of the phase |
| **(Cross-cutting) Debugger** | `/gsd-debug` | `/problem-solver` | When validation-failure cap (3) hit — never first |
| **(Cross-cutting) Story Loop** *(opt-in)* | `/architect-loop run` | — | If user prefers Ralph-style story-by-story execution; opt-in via `--story-mode` |

### Subagent vs Inline Decision

```
Is this step:                            → invoke as
─────────────────────────────────────────────────────
Short (<2 min), deterministic            → SlashCommand inline
Long-running OR context-heavy            → Task-tool subagent
Reads many files                         → Task-tool subagent
Needs to write back to main context      → SlashCommand inline
Could pollute main context with noise    → Task-tool subagent
```

**Heuristic:** Reviewer (`/predator`) and QA (`/code-tester`) are *always* subagents — they read whole codebases. PM (`/gsd-spec-phase`), Tech Writer (`/gsd-docs-update`), and DevOps (`/gsd-execute-phase` for trivial CI tasks) are *usually* inline.

### Skill Version Drift Handling

**Problem:** User updates GSD; OSBuilder's expected schema breaks.

**Solution:**
1. SKILL.md frontmatter declares minimum versions: `requires: gsd>=2.0, brainiac>=6.0, predator>=1.5, code-tester>=3.1`.
2. On first invocation each session, run `scripts/check_skill_versions.py` — fast (reads frontmatter of installed skills).
3. On mismatch: friendly error + exact upgrade command. Refuse to proceed.
4. **Never silently adapt.** Better to fail loudly than to corrupt a user's project with stale assumptions.

---

## Suggested Build Order (Phase Implications for Roadmap)

The dependencies between OSBuilder's own components imply this build order. The roadmapper should map phases to these clusters.

```
Cluster A (foundation — must come first)
  1. SKILL.md skeleton + YAML frontmatter + routing decision tree
  2. scripts/os_detect.py + scripts/state_update.py (state plumbing)
  3. references/handoffs/*.md (schemas — must exist before roles use them)

Cluster B (one playbook end-to-end, prove the loop)
  4. references/playbooks/web-app.md (the most common case)
  5. references/roles/{pm,architect,devops}.md (minimum viable role set)
  6. scripts/scaffold_dispatch.py (web-app entry only at first)
  7. templates/{README.runbook.md, .env.example, github-actions.ci.yml}

Cluster C (verify-loop — quality bar)
  8. references/roles/{qa,reviewer}.md
  9. references/failure-classifier/{matrix.md, retry-policy.md}
 10. scripts/classify_failure.py + scripts/retry_counter.py

Cluster D (UX polish — common-person bar)
 11. references/ux/{question-bank.md, friendly-errors.md, tutor-narration.md}
 12. references/preflight/{macos,linux,windows,detect}.md
 13. scripts/preflight_check.py

Cluster E (ship + remaining roles)
 14. references/roles/{frontend,backend,tech-writer}.md
 15. references/ship/{github-private.md, runbook-template.md}
 16. references/failure-classifier/escalation-handoff.md (covers /problem-solver path)

Cluster F (additional playbooks — additive, low risk)
 17. references/playbooks/{ai-service,cli-tool,desktop-app,hub-platform}.md
 18. matching templates and scaffold_dispatch.py entries

Cluster G (publish bar)
 19. examples/* gallery (3-5 reference apps OSBuilder built)
 20. install.sh, update.sh, README.md (skill-level)
 21. --production-ready opt-in phases (observability, migrations, secrets)
```

**Rationale:**
- Cluster A first because nothing else can be tested without state plumbing and handoff schemas.
- Cluster B chosen as **web-app only** for the prove-the-loop phase — adding all 5 playbooks before the orchestration is debugged would multiply failure surface.
- Cluster C before Cluster D because the verify loop is the quality moat; UX polish on a broken loop is wasted.
- Cluster F is additive — each new playbook is an independent file with no cross-dependencies, so they can ship in any order or in parallel waves.

---

## State Checkpoint (`state.md`) Specification

**Location:** `<project-root>/.planning/osbuilder/state.md`
**Owner:** OSBuilder (written by `scripts/state_update.py`, read by SKILL.md on resume)
**Updated:** every role transition, every phase transition, every failure
**Size budget:** ≤ 20 lines (target ~15)

### Schema (canonical)

```markdown
# OSBuilder State

goal: <one-sentence user goal — verbatim from intake>
app_type: <web-app | ai-service | desktop-app | cli-tool | hub-platform>
playbook: references/playbooks/<file>.md
project_root: <absolute path>
github_repo: <owner/name (private)> | <none>

current_role: <pm | architect | frontend | backend | devops | qa | reviewer | tech-writer>
current_phase: <integer matching ROADMAP.md phase>
phase_step: <discuss | plan | execute | verify | done>

last_action: <one-line summary>
last_failure: <one-line summary or null>
retry_count: <0-3>
escalation_level: <none | gsd-debug | problem-solver | user-handoff>

next_action: <one-line — what the resumed session should do first>
updated_at: <ISO 8601 UTC>
```

### Resume Protocol

When SKILL.md is loaded fresh (after `/clear` or compaction):

1. Check `<project-root>/.planning/osbuilder/state.md` — exists?
2. If yes: load it → load `references/playbooks/<playbook>` → load `references/roles/<current_role>.md` → narrate "Resuming: <next_action>".
3. If no: this is a new build → run intake.

Total context cost of resume: ~15 (state) + ~200 (playbook) + ~120 (role brief) ≈ 335 lines. Cheap.

---

## Cross-Platform Strategy

### OS Detection

`scripts/os_detect.py` (pure stdlib — runs anywhere Python 3 exists):

```python
# Returns dict: {"os": "macos|linux|windows", "arch": "arm64|x64", "package_mgr": "brew|apt|dnf|pacman|winget|scoop"}
```

Output drives which `references/preflight/<os>.md` to load. **One level deep — Anthropic's no-nested-references rule.**

### Preflight Reference Layout

| File | Owns |
|------|------|
| `references/preflight/macos.md` | brew detection + install commands; `gh auth login` flow; Docker Desktop note |
| `references/preflight/linux.md` | apt/dnf/pacman matrix; user-namespace Docker note; `gh` from official repo |
| `references/preflight/windows.md` | winget primary + scoop fallback; WSL2 recommendation note; PowerShell snippets |
| `references/preflight/detect.md` | how to call `scripts/os_detect.py` and route |

### Auto-Install with One Confirmation

Per the requirement: detect missing tools → present one consolidated prompt → on yes, run all installs. Friendly errors for sudo prompts, partial failures, etc.

Friendly translation lives in `references/ux/friendly-errors.md` — common errors mapped to plain-English explanation + remediation.

---

## Failure-Classifier Architecture

### Layout

```
references/failure-classifier/
├── matrix.md            # human-readable decision tree
├── retry-policy.md      # backoff curves, caps per class
└── escalation-handoff.md # structured format when escalating to user

scripts/
├── classify_failure.py  # stdin: error blob → stdout: {"class": "...", "confidence": 0.x, "suggested_action": "..."}
└── retry_counter.py     # persists per-(phase, failure-signature) retry count to .planning/osbuilder/retries.json
```

### Why a Script (Not Embedded in SKILL.md)

- Determinism: classification is rule-based pattern matching — better as code than as Claude prompting.
- Token cost: error blobs can be huge (stack traces, build logs); piping them through a script avoids loading them into context.
- Testability: a Python script has unit tests; a markdown decision tree doesn't.

### Retry-Cap State

`<project-root>/.planning/osbuilder/retries.json`:

```json
{
  "phase_3:validation-failure:sql-injection-in-/upload": {
    "count": 2,
    "first_seen": "2026-04-29T15:18:02Z",
    "last_seen": "2026-04-29T15:21:11Z",
    "tried": ["/gsd-debug", "/problem-solver"]
  }
}
```

On 3rd hit → escalate. Counter resets when phase completes successfully.

---

## Handoff to GSD's `/gsd-new-project --auto`

OSBuilder is *not* a fork of GSD. The intake step runs `/gsd-new-project --auto`, then GSD's normal `discuss → plan → execute → verify` loop drives the rest of the build, with OSBuilder injecting role narration and sub-skill invocations between phases.

### Concrete handoff sequence

```
1. OSBuilder intake (PM role narration)
   - Runs ux/question-bank.md interactive flow
   - Produces: a derived spec string (saved to .planning/osbuilder/derived_spec.md)

2. OSBuilder → GSD handoff
   - Invokes: /gsd-new-project --auto (passes derived_spec.md via @-reference)
   - GSD writes: .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md
   - OSBuilder reads ROADMAP.md to know how many phases will be run

3. Per-phase loop (OSBuilder drives, GSD executes)
   For phase N in ROADMAP:
     - Architect role: /gsd-plan-phase N        (Task-tool subagent for research-heavy)
     - Builder roles: /gsd-execute-phase N      (inline; updates state.md per task commit)
     - QA role: /code-tester + /gsd-verify-work N
     - Reviewer role: /predator hunt + /gsd-code-review
     - On any failure: classify → retry-cap → escalate
     - Update state.md → narrate transition

4. After last phase:
   - Tech Writer: /gsd-docs-update (README runbook)
   - DevOps Ship: gh repo create --private; git push
   - Final narration: "Your app is at <github-url>; clone with: <command>"
```

**Key point:** OSBuilder does **not** call GSD's commands as if it's another agent — it emits them as user-level slash commands. The role narration and the slash command emission happen in the same turn, so the user sees "Architect is planning phase 3..." followed by `/gsd-plan-phase 3`.

---

## Scaling Considerations

This is a Claude Code skill — "scaling" means user count, not transactions. Concerns differ from a hosted service.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (Charlie) | Current architecture is fine; examples gallery doubles as regression bench |
| 10s of users (early publish) | Add `references/preflight/<os>.md` exhaustively (more package managers); add 2-3 more playbooks; expand examples gallery |
| 100s+ of users | Telemetry-friendly opt-in (anonymous failure-class counts back to a community-improvement bucket); split heavy playbooks (`hub-platform.md`) into sub-files when they grow past 300 lines; add localized question banks |

### What breaks first

1. **Skill version drift** — as GSD/brainiac/predator evolve, OSBuilder's expected schemas drift. Already addressed by version pinning + first-run check.
2. **New scaffolders** (the JS ecosystem changes flavors every ~12 months). Mitigation: `playbooks/web-app.md` is intentionally one short file — easy to swap `create-next-app` for whatever wins.
3. **Failure-classifier coverage** — new failure modes (e.g., new GitHub API errors, new npm idiosyncrasies). Mitigation: "unknown" bucket escalates fast and logs a sample for human review.

---

## Anti-Patterns

### Anti-Pattern 1: Reimplementing what sub-skills already do

**What people do:** Copy-paste GSD's planning logic into OSBuilder because "we want a slightly different output". 4× duplication, divergent maintenance, broken upgrade path.
**Why it's wrong:** The whole leverage of OSBuilder is composition. If GSD doesn't produce the right output, fix GSD; don't fork it into OSBuilder.
**Do this instead:** Open an issue against GSD. While that's pending, transform GSD's output in a small `scripts/` helper at the OSBuilder boundary — never inside OSBuilder's own logic.

### Anti-Pattern 2: Long monolithic SKILL.md

**What people do:** Cram all role briefs, playbooks, preflight commands, and UX templates into SKILL.md "for simplicity".
**Why it's wrong:** Violates Anthropic's progressive-disclosure rule (≤500 lines, target ≤200). Bloats every invocation's context.
**Do this instead:** SKILL.md = orchestrator + routing only. Everything else lives in `references/` and is loaded JIT.

### Anti-Pattern 3: Naive retry loops

**What people do:** `for i in range(10): try: do_thing(); break; except: continue`. Burns tokens, often makes things worse, never escalates.
**Why it's wrong:** Aider's empirical 3-cap exists for a reason — past 3, the model drifts instead of converging. Without classification, transient and validation failures get the same treatment.
**Do this instead:** Always classify first. Cap at 3 per failure-signature. On cap, escalate to `/gsd-debug` → `/problem-solver` → user with structured handoff.

### Anti-Pattern 4: Hand-writing boilerplate the scaffolder already produces

**What people do:** Generate `package.json`, `tsconfig.json`, `next.config.ts` from scratch via prompting. Bolt.new-style. 10M+ tokens for medium apps; non-idiomatic, divergent results.
**Why it's wrong:** Scaffolders are deterministic, free, and idiomatic. Token-waste compounds with project size.
**Do this instead:** Always start from a published scaffolder where one exists. OSBuilder owns only the deltas — the user-specific code on top of the scaffold.

### Anti-Pattern 5: Premature complexity (K8s/microservices/service-mesh in v1)

**What people do:** Default scaffolds include Helm charts, mesh sidecars, and 3-tier microservice splits "to be ready for scale".
**Why it's wrong:** Textbook premature complexity. Adds operational surface area the user can't reason about. Most apps never need it.
**Do this instead:** Default to monolith + Postgres + one Dockerfile + one CI workflow. Production-ready features are opt-in named phases via `--production-ready`.

### Anti-Pattern 6: State in the conversation, not on disk

**What people do:** Track current phase / role / retry count "in Claude's head" via conversation continuity.
**Why it's wrong:** First `/clear` or compaction kills it. User loses hours of work.
**Do this instead:** `state.md` is the single source of truth. Every transition writes to it. Conversation memory is a cache, not a store.

### Anti-Pattern 7: Multi-level reference indirection

**What people do:** `SKILL.md → references/index.md → references/web/index.md → references/web/next.md`.
**Why it's wrong:** Anthropic's docs are explicit — Claude only partially reads files reached through nested references.
**Do this instead:** Every file linked from SKILL.md, one level deep. If you need sub-categories, prefix the filename (`web-next.md`, `web-vite.md`) instead of nesting.

---

## Integration Points

### External Services (the apps OSBuilder *builds* talk to these — OSBuilder itself only uses gh CLI)

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GitHub | `gh repo create --private` + `git push` via DevOps role | gh CLI must be installed + authed (preflight) |
| GitHub Actions | drop `templates/github-actions.ci.yml` into `.github/workflows/` | Single workflow at v1; expand only on `--production-ready` |
| Docker Hub | not used by default — local Docker only at v1 | Push to a registry is opt-in `--production-ready` |
| Vercel/Fly/Railway | **out of scope v1** | Auto-deploy is explicitly excluded per PROJECT.md |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| SKILL.md ↔ playbooks | one-way file load (Claude reads on demand) | one level deep |
| Playbooks ↔ roles | playbook references roles by file path | flat — playbooks index roles, roles never index playbooks |
| Roles ↔ sub-skills | slash-command emission OR Task-tool subagent | role brief specifies which |
| OSBuilder ↔ built app | writes to `<project-root>/.planning/osbuilder/` | namespaced subdir under GSD's `.planning/` |
| OSBuilder ↔ GSD | reads/writes `.planning/{PROJECT,REQUIREMENTS,ROADMAP}.md` | uses GSD's schemas verbatim — never invent new ones |
| Scripts ↔ Claude | stdout JSON for structured returns; stderr for errors | scripts never depend on Claude's reasoning |

---

## Sources

- [Anthropic — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — HIGH confidence; canonical source for SKILL.md ≤500 lines, progressive disclosure, one-level-deep references, scripts-vs-references rule
- [Anthropic — Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — HIGH; runtime model + filesystem-based progressive disclosure
- [Claude Code Docs — Subagents](https://code.claude.com/docs/en/sub-agents) — HIGH; Task-tool delegation, isolated context windows
- [The Task Tool: Claude Code's Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2) — MEDIUM; concrete patterns for delegating long-running work
- [GitHub: anthropics/claude-code Issue #25999 — persistent state across context compaction](https://github.com/anthropics/claude-code/issues/25999) — MEDIUM; community-blessed pattern for state.md
- [Aider GitHub Issue #1440 — Only 3 reflections allowed](https://github.com/paul-gauthier/aider/issues/1440) — HIGH; canonical source for the 3-reflection cap
- [create-next-app docs](https://nextjs.org/docs/app/api-reference/cli/create-next-app), [create-t3-app](https://create.t3.gg/), [create-vite npm](https://www.npmjs.com/package/create-vite) — HIGH; deterministic scaffolders OSBuilder dispatches
- Direct inspection of `~/.claude/skills/{gsd,brainiac,predator,code-tester,architect-loop,gsd-new-project,gsd-autonomous}/SKILL.md` — HIGH; ground truth for the existing skill ecosystem OSBuilder composes over
- `.planning/PROJECT.md` (this project) — HIGH; vision, scope, key decisions

---
*Architecture research for: Claude Code orchestration skill (virtual dev studio)*
*Researched: 2026-04-29*
