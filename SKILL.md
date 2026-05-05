---
name: osbuilder
description: >
  Builds end-to-end applications from a plain-English description. Orchestrates a virtual dev team (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer) over the user's existing skill ecosystem (gsd, brainiac, predator, code-tester, problem-solver) to ship a working app to a private GitHub repo. Common-person friendly with tutor mode on by default. Triggers on. /osbuilder, build me an app, build a website, build a tool, build like Professor Hub.
allowed-tools: Read, Write, Edit, Bash, Agent, Glob, Grep, WebSearch, WebFetch
user-invocable: true
argument-hint: "[brief or @path/to/spec.md or 'build like ./reference-app']"
requires:
  gsd: 1.0.0
  brainiac: 6.0.0
  predator: 1.0.0
  code-tester: 3.1.0
  problem-solver: 3.0.0
---

# OSBuilder — Idea-to-App Orchestrator

OSBuilder turns a description into a working app on private GitHub. You describe what you want; OSBuilder runs a virtual studio (PM → Architect → Frontend → Backend → DevOps → QA → Reviewer → Tech Writer) sequentially, leveraging your existing skill ecosystem to ship the result. Designed for non-developers — plain-English questions, tutor mode on by default, friendly errors, automatic prerequisite installation.

**Quality bar:** Lovable's polish + Aider's git discipline + GSD's spec rigor + create-t3-app's deterministic scaffold.

## How It Works

| Stage | Role | Delegates to |
|-------|------|--------------|
| 1. Intake | PM | Plain-English questioning + `/gsd:spec-phase` for ambiguity scoring |
| 2. Research | Architect | `/brainiac` (web research), falls back to `references/stack-menu.md` |
| 3. Scaffold | DevOps | `scripts/scaffold_dispatch.py` — runs the right deterministic scaffolder (`create-next-app`, `create-t3-app`, `cargo new`, etc.). Never hand-writes `package.json`. |
| 4. Plan | Architect | `/gsd:new-project --auto` → `/gsd:plan-phase` per phase |
| 5. Build | Frontend / Backend / DevOps | `/gsd:execute-phase` (single-threaded — multi-agent is an explicit anti-feature) |
| 6. Verify | QA + Reviewer | `/code-tester` + `/gsd:verify-work` against falsifiable criteria; `/predator` + `/gsd:code-review` for architecture/security |
| 7. Heal | Debug-cap | `/gsd:debug` + `/problem-solver` (failure-classified, 3-reflection cap, then escalate) |
| 8. Ship | DevOps | `gh repo create --private` + clone-and-run runbook in README |

State persists in `<project-root>/.planning/osbuilder/state.md` (10-field markdown checkpoint, ~13 lines) so a `/clear`'d or context-compacted session can resume mid-build.

## Inputs

OSBuilder accepts three intake forms:

1. **Paragraph** — `/osbuilder I want a website where students upload lab notebooks and I grade them`
2. **Structured spec** — `/osbuilder @path/to/spec.md` — features list, stack hints, target users
3. **Reference app** — `/osbuilder build like ../professor for X` — extracts patterns from an existing app *(v1.x; v1 covers paragraph + spec)*

## Modes

| Flag | Effect |
|------|--------|
| (default) | Beginner mode — plain-English questioning, tutor narration on, sensible defaults always available |
| `--advanced` | Exposes stack choice, deploy targets, scaffolder selection |
| `--quiet` | Disables tutor mode (still narrates dev-team progress, just no "what just happened" explanations) |
| `--tutor` | Force tutor mode on (default) |
| `--no-docker` | SQLite-only single-user builds (for users without Docker Desktop) |
| `--production-ready` | Adds observability / CI-CD / migrations / Sentry / rate-limiting as named phases (not default) |
| `--public` | Push to a public GitHub repo (default is private) |

## Resume Protocol

OSBuilder survives `/clear` and Claude Code's auto-compaction (~98% context) by reading the session checkpoint at startup.

When invoked, OSBuilder runs:

```bash
python ~/.claude/skills/osbuilder/scripts/state_writer.py read --project-root <project-root>
```

If state.md exists with non-empty `current_role` and `current_phase`, OSBuilder resumes from that role/phase. Otherwise it starts a fresh intake.

The 10 persisted fields: `goal`, `app_type`, `playbook`, `current_role`, `current_phase`, `phase_step`, `last_failure`, `retry_count`, `escalation_level`, `next_action`. See `references/state-md-schema.md` for details.

## Architecture (One-Level-Deep)

```
~/.claude/skills/osbuilder/
├── SKILL.md                  ← this file (entry point + routing)
├── install.sh                ← idempotent installer (copies repo → install location)
├── pyproject.toml            ← test/dev tooling
├── references/               ← progressive disclosure (loaded on demand)
│   ├── README.md             ← what lives here
│   ├── playbooks/            ← per-app-type recipes (web, ai-service, cli, desktop, hub-platform)
│   ├── roles/                ← per-role briefs (pm, architect, frontend, backend, devops, qa, reviewer, tech-writer)
│   ├── preflight/            ← per-OS install matrices (macos, linux, windows)
│   ├── refuse-list.md        ← Phase 6 SCL-05 — refuse keywords + friendly opt-in copy
│   └── stack-menu.md         ← fallback stack defaults when web research is inconclusive
├── scripts/                  ← Python 3 stdlib helpers (executed, never loaded as context)
│   ├── state_writer.py       ← state.md checkpoint manager (atomic via os.replace)
│   ├── bootstrap.sh          ← POSIX Python install shim (re-execs into state_writer)
│   ├── bootstrap.ps1         ← Windows PowerShell shim (winget; two-mode for PATH-refresh gotcha)
│   ├── scaffold_dispatch.py  ← invokes the right scaffolder for the chosen playbook
│   ├── failure_classifier.py ← 4-class taxonomy: transient / context / tool / validation
│   ├── friendly_error.py     ← translates raw stack traces into "what broke + what to do"
│   ├── preflight_check.py    ← detects missing prereqs (Node, Python, git, gh, Docker)
│   ├── registry_verify.py    ← slopsquatting gate (verifies packages exist before install)
│   ├── gh_handoff.py         ← creates private GitHub repo (Phase 6 SHIP-01..05)
│   ├── runbook_writer.py     ← stamps clone-and-run README from state.md (Phase 6 SHIP-02)
│   └── production_phase_writer.py  ← --production-ready named-phase emitter (Phase 6 SCL-06)
├── assets/                   ← templates: gitignore-templates/, gitleaks/, dockerfiles/, ci-workflows/, readme-template.md
└── examples/                 ← gallery of 3-5 reference apps OSBuilder has built
```

Anti-feature: nesting deeper than one level under `~/.claude/skills/osbuilder/` (Anthropic guidance, also enforced by `find -mindepth 3 -type d` returning empty in tests).

## Hard Rules (Non-Negotiable)

1. **Always use a deterministic scaffolder** when one exists. OSBuilder never hand-writes `package.json`, `tsconfig.json`, or `pyproject.toml`. (Avoids bolt.new's documented 10M-token spaghetti failure mode.)
2. **Single-threaded execution.** The dev-team metaphor is for *narration only*. Multi-agent parallel role execution is an anti-feature (DeepMind Dec 2025: 41–86.7% failure rates, 17.2× error amplification).
3. **3-reflection cap.** Aider's empirically-validated drift limit. After 3 retries on the same failure class, escalate with a structured handoff (state, last error, what was tried).
4. **Slopsquatting gate.** Every `npm install` / `pip install` / `cargo add` runs through `scripts/registry_verify.py` first; `--ignore-scripts` until verified (Socket 2025: 20% LLM hallucination rate of package names).
5. **Refuse-list.** OSBuilder will not add Kubernetes, microservices, service-mesh, Helm, or auto-deploy in v1 default builds. These live behind `--production-ready` as opt-in named phases.
6. **Privacy by default.** GitHub repos are created **private** unless `--public` is explicitly passed.
7. **Composition over reimplementation.** If `gsd`, `brainiac`, `predator`, `code-tester`, or `problem-solver` is missing functionality, the fix lives in the sub-skill, not in OSBuilder.

## Failure Handling (Short Version)

The failure classifier (`scripts/failure_classifier.py`) sorts every error into one of four classes with a documented retry strategy:

| Class | Retry Strategy | Cap |
|-------|---------------|-----|
| `transient` | Exponential backoff (1s → 4s → 16s) | 3 |
| `context-overflow` | Compress + retry | 3 |
| `tool-failure` | Fallback path (alternate tool/command) | 3 |
| `validation-failure` | **Re-plan, NOT retry** — the model has the wrong shape | 3 |

After 3 reflections on the same failure, escalate via `/gsd:debug` then `/problem-solver`, then a structured handoff to the user. See `references/playbooks/self-healing.md` for the full classifier surface.

## Common-Person UX

- **Plain-English questioning.** OSBuilder never asks "responsive design?" — asks "Should it work on phones too?" Every question shows an "I don't know, you decide" option that resolves to the documented sensible default.
- **Tutor mode on by default.** Each stage explains what just happened in plain English. Disable with `--quiet`.
- **Friendly errors.** `scripts/friendly_error.py` maps raw failures (`ENOENT`, `EACCES`, `ModuleNotFoundError`, etc.) to "here's what broke + here's what to do." Never exposes stack traces.
- **Pre-flight installer.** First run detects missing prerequisites (Node, Python, git, `gh`, Docker) and offers auto-install with a single confirmation prompt. Cross-platform: Homebrew (macOS), apt/dnf (Linux), winget→scoop→choco (Windows).
- **Beginner mode default.** `--advanced` exposes stack/deploy/scaffolder choices for power users.

## Project Status

This skill is built phase-by-phase via GSD itself. See the OSBuilder source repo's `.planning/ROADMAP.md` for what's shipped and what's next. Phase 1 (Foundation) delivers SKILL.md, install.sh, state_writer.py, and bootstrap shims — the spine every other phase depends on.
