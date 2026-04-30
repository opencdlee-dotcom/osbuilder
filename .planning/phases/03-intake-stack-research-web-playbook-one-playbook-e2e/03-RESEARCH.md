# Phase 3: Intake + Stack Research + Web Playbook (One-Playbook E2E) — Research

**Researched:** 2026-04-30
**Domain:** Plain-English app intake → structured brief → per-build stack research → deterministic scaffold (Next.js web playbook)
**Confidence:** HIGH (stack verified against npm registry + official Next.js/Drizzle docs; patterns verified against existing Phase 1/2 codebase)

---

## Summary

Phase 3 proves the full loop: user types a paragraph describing a web app and OSBuilder produces a scaffolded, runnable Next.js + Postgres + Tailwind project on disk. It introduces three new Python scripts (`intake_handler.py`, `stack_researcher.py`, `scaffold_dispatch.py`) and three new reference files (`references/playbooks/web.md`, `references/stack-menu.md`, `references/question-bank.md`).

The **intake handler** parses plain-English paragraphs and structured specs into the same structured brief format, asks a small number of outcome-framed clarifying questions (never jargon), and synthesizes a brief that feeds `/gsd-new-project --auto`. The **stack researcher** calls `/brainiac` with the derived app type as a focused query, interprets the structured result, and falls back to `references/stack-menu.md` when research times out. The **scaffold dispatcher** runs `create-next-app` in fully non-interactive mode and adds Drizzle + Postgres connection code as deterministic post-scaffold deltas — never hand-writing any file the scaffolder already produces.

The 60-second E2E target (excluding `pnpm install` download time) is achievable because research and scaffolding are driven by well-defined Python scripts with clearly bounded work. The primary risk is the gap between "paragraph in → brief out" and the exact schema that `/gsd-new-project --auto` consumes; this is mitigated by writing the brief as a self-contained markdown document that `--auto` accepts via `@` reference.

**Primary recommendation:** Build all three scripts with TDD (RED stubs first, GREEN second), keep each script under 200 lines stdlib-only, and treat the scaffold dispatcher as the integration test: `pnpm dev` booting is the phase gate, not just pytest passing.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Intake parsing (paragraph → structured brief) | OSBuilder script (`intake_handler.py`) | SKILL.md routing | The brief is a file on disk, not a conversation state; script ownership makes it testable and resumable |
| Clarifying questions + "you decide" defaults | SKILL.md (LLM-driven) | `references/question-bank.md` (loads on demand) | Questions need natural language fluency; defaults are documented in a reference file for consistency |
| Brief → `/gsd-new-project --auto` handoff | OSBuilder script (writes `derived_spec.md`) | GSD skill (reads it) | The handoff is a file exchange, not an API; this is the established GSD pattern |
| Per-build stack research | OSBuilder script (`stack_researcher.py`) | `/brainiac` skill delegation | Research invokes `/brainiac` as a subagent; script parses result into structured JSON |
| Stack-menu fallback | `references/stack-menu.md` | `stack_researcher.py` (reads on timeout) | Markdown reference loaded by the script when research times out |
| Scaffold execution | OSBuilder script (`scaffold_dispatch.py`) | OS shell (runs `pnpm create next-app`) | Deterministic subprocess call; script owns the flag set and post-scaffold Drizzle wiring |
| Post-scaffold Drizzle + Postgres wiring | `scaffold_dispatch.py` | `references/playbooks/web.md` (spec) | Small deterministic file writes (`src/lib/db.ts`, `drizzle.config.ts`, `.env.example`) |
| Web playbook specification | `references/playbooks/web.md` | `scaffold_dispatch.py` (consumer) | Reference file documents what the dispatcher must produce; no overlap |
| state.md updates (intake results, stack choices) | `state_writer.py` (existing) | `scaffold_dispatch.py` (calls it) | Reuse Phase 1/2 script; new fields: `app_type`, `playbook`, `stack_choices`, `project_path` |
| `--advanced` override logging | `state_writer.py` + `stack_researcher.py` | SKILL.md flag handling | Override captured in state.md as a `stack_overrides` field |

---

## Standard Stack

### OSBuilder Phase 3 Scripts (what OSBuilder itself is built from)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.10+ (machine has 3.12.6) | `intake_handler.py`, `stack_researcher.py`, `scaffold_dispatch.py` — subprocess, json, argparse, pathlib | Established pattern from Phase 1/2; no deps = no preflight chicken-and-egg |
| pytest | 9.0.2 (machine) / `>=8.0` (pyproject) | Test suite (`test_intake.py`, `test_stack_researcher.py`, `test_scaffold_dispatch.py`) | Existing infrastructure; all tests collected by `python3 -m pytest` |
| ruff | `>=0.6` (pyproject) | Linting | Established from Phase 1 |

### Web Playbook Stack (what the scaffolded app is built from)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `create-next-app` | 16.2.4 (latest, verified npm registry 2026-04-30) | Deterministic Next.js scaffold | Official scaffolder; produces App Router + TypeScript + Tailwind in one command |
| Next.js | 16.2.4 (bundled by `create-next-app`) | Full-stack React framework | Industry default; App Router is the Next.js 16 default |
| React | 19.2 (bundled by Next.js 16) | UI | Comes with Next 16; no separate choice |
| TypeScript | 5.x (bundled) | Type safety | `--typescript` is default in create-next-app 16 |
| Tailwind CSS | 4.2.4 (verified npm registry 2026-04-30) | Styling | `--tailwind` is default in create-next-app 16; v4 uses CSS-first config |
| pnpm | 10.33.2 (verified npm registry 2026-04-30) | Package manager | `--use-pnpm` flag available; scaffold dispatcher installs pnpm via `npm install -g pnpm` if absent |
| `drizzle-orm` | 0.45.2 (verified npm registry 2026-04-30) | Postgres ORM | Lighter than Prisma; type-safe; locked decision from STACK.md research |
| `drizzle-kit` | 0.31.10 (verified npm registry 2026-04-30) | Migrations + codegen | Required companion to drizzle-orm |
| `postgres` (postgres.js) | 3.4.9 (verified npm registry 2026-04-30) | Postgres driver for Drizzle | Recommended for serverless/edge; simpler than `pg` |
| Docker Compose v2 | OS-level | Local Postgres | `compose.yaml` (not `docker-compose.yml`); `postgres:18-alpine` pinned |

**Version verification:** All npm package versions confirmed via `npm view <pkg> version` on 2026-04-30. `create-next-app` latest is 16.2.4. [VERIFIED: npm registry]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@types/pg` | 8.x | TypeScript types for pg (if using node-postgres path) | Only if choosing node-postgres over postgres.js |
| `pg` (node-postgres) | 8.x | Alternative Postgres driver | For long-running server environments; scaffold dispatcher defaults to postgres.js |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `postgres` (postgres.js) | `pg` (node-postgres) | `pg` uses Pool; better for always-on servers. postgres.js is simpler and default for serverless. Both work with compose. |
| pnpm | npm | pnpm is faster, disk-efficient, 2026 default for TypeScript projects. `--use-pnpm` flag explicit. |
| Drizzle | Prisma | Prisma has mature migration tooling but 800KB bundle vs Drizzle's 33KB. Drizzle is the locked choice. |
| create-next-app `--yes` | explicit flags | `--yes` picks saved preferences or defaults; may pick App Router or Pages Router depending on saved prefs. Explicit flags are safer for non-interactive automation. |

**Installation (within scaffold_dispatch.py post-scaffold):**
```bash
# Post-scaffold Drizzle wiring (run in scaffolded project dir)
pnpm add drizzle-orm postgres
pnpm add -D drizzle-kit
```

---

## Architecture Patterns

### System Architecture Diagram

```
USER INPUT
  │  "I want a website where students upload lab notebooks and I grade them"
  │  (or: structured spec, or: @spec.md)
  ▼
┌─────────────────────────────────┐
│  SKILL.md — PM role             │  Detects intake form (paragraph / structured / file)
│  Loads references/question-bank │  Asks ≤5 outcome-framed questions with "you decide" defaults
│  .md on demand                  │  Detects `--advanced` flag
└──────────────┬──────────────────┘
               │  (answers collected)
               ▼
┌─────────────────────────────────┐
│  scripts/intake_handler.py      │  Merges raw input + answers into structured brief
│                                 │  Writes: <project>/.planning/osbuilder/derived_spec.md
│                                 │  Writes state.md fields: goal, app_type, playbook
│                                 │  Writes state.md field: stack_overrides (if --advanced)
└──────────────┬──────────────────┘
               │  derived_spec.md on disk
               ▼
┌─────────────────────────────────┐
│  GSD handoff                    │  OSBuilder emits: /gsd-new-project --auto @derived_spec.md
│  /gsd-new-project --auto        │  GSD writes: .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md
└──────────────┬──────────────────┘
               │  ROADMAP.md on disk
               ▼
┌─────────────────────────────────┐
│  SKILL.md — Architect role      │  Detects app_type from state.md → picks playbook
│  Loads references/playbooks/    │  web.md on demand
│  web.md on demand               │
└──────────────┬──────────────────┘
               │  app_type + playbook confirmed
               ▼
┌─────────────────────────────────┐
│  scripts/stack_researcher.py    │  Calls /brainiac with focused query
│                                 │  Parses result → structured JSON (name, version, rationale)
│                                 │  On timeout or inconclusive: reads references/stack-menu.md
│                                 │  Writes state.md field: stack_choices (JSON)
│                                 │  Respects --advanced overrides from state.md
└──────────────┬──────────────────┘
               │  stack_choices confirmed
               ▼
┌─────────────────────────────────┐
│  scripts/scaffold_dispatch.py   │  Reads playbook + stack_choices from state.md
│  [web playbook path]            │  Ensures pnpm installed (npm install -g pnpm if absent)
│                                 │  Runs: pnpm create next-app@latest <name> \
│                                 │           --typescript --tailwind --app --src-dir \
│                                 │           --eslint --use-pnpm --disable-git
│                                 │  Post-scaffold: pnpm add drizzle-orm postgres
│                                 │               pnpm add -D drizzle-kit
│                                 │  Writes: src/lib/db.ts (Drizzle + postgres.js)
│                                 │  Writes: drizzle.config.ts
│                                 │  Writes: .env.example (DATABASE_URL template)
│                                 │  Writes: compose.yaml (postgres:18-alpine)
│                                 │  Writes state.md field: project_path, current_role=devops
│                                 │  Verifies: pnpm install && pnpm dev boots on localhost:3000
└──────────────┬──────────────────┘
               │  scaffolded project on disk
               ▼
USER: working scaffolded project + GSD plan ready for Phase 4
```

### Recommended Project Structure (new files this phase adds)

```
~/.claude/skills/osbuilder/
├── references/
│   ├── playbooks/
│   │   └── web.md              ← NEW: web playbook spec (SCAF-01)
│   ├── stack-menu.md           ← NEW: fallback defaults (RES-03)
│   └── question-bank.md        ← NEW: plain-English Q bank (IN-03/IN-04)
└── scripts/
    ├── intake_handler.py        ← NEW: paragraph/spec → derived_spec.md (IN-01..05)
    ├── stack_researcher.py      ← NEW: /brainiac → structured stack JSON (RES-01..04)
    └── scaffold_dispatch.py     ← NEW: create-next-app + Drizzle wiring (SCAF-01, SCAF-06)

scripts/tests/
    ├── test_intake.py           ← NEW: tests for IN-01..05
    ├── test_stack_researcher.py ← NEW: tests for RES-01..04
    └── test_scaffold_dispatch.py← NEW: tests for SCAF-01, SCAF-06
```

### Pattern 1: Non-Interactive create-next-app

**What:** The scaffold dispatcher must run `create-next-app` without prompts, producing a deterministic output tree.

**When to use:** Every web playbook scaffold. SCAF-06 prohibits hand-writing any file the scaffolder produces.

**Critical finding:** `--yes` alone is NOT sufficient for fully non-interactive mode — it "uses saved preferences or defaults" which may include Pages Router if the machine has old saved preferences. Use **explicit flags** to guarantee App Router, TypeScript, Tailwind, and pnpm regardless of saved prefs. [VERIFIED: nextjs.org/docs/app/api-reference/cli/create-next-app]

**Verified command:**
```bash
# Source: https://nextjs.org/docs/app/api-reference/cli/create-next-app (verified 2026-04-30)
pnpm create next-app@latest my-app \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --eslint \
  --use-pnpm \
  --disable-git \
  --import-alias "@/*"
# Note: --turbopack is enabled by default in Next.js 16; no flag needed
# Note: --disable-git prevents nested git init inside the scaffold
```

**What gets produced:** TypeScript App Router project with Tailwind 4, ESLint, `src/` layout, pnpm lockfile, no nested git repo. [VERIFIED: nextjs.org docs + npm view create-next-app@16.2.4]

### Pattern 2: Post-Scaffold Drizzle Wiring (Deterministic Deltas)

**What:** After `create-next-app`, the scaffold dispatcher adds Drizzle ORM and Postgres support as a small set of deterministic file writes. These are the only files OSBuilder writes after the scaffolder; they are minimal and follow the official Drizzle getting-started pattern.

**Files written (post-scaffold):**

```typescript
// src/lib/db.ts
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

const queryClient = postgres(process.env.DATABASE_URL!);
export const db = drizzle({ client: queryClient });
```

```typescript
// drizzle.config.ts
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

```yaml
# compose.yaml (Docker Compose v2 filename — NOT docker-compose.yml)
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: myapp_secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```
# .env.example
DATABASE_URL=postgresql://myapp:myapp_secret@localhost:5432/myapp
```

**Key constraint:** `src/db/schema.ts` is NOT written by OSBuilder — it is left empty (or with a placeholder comment). GSD's execute phase will create schema files per feature. This respects the "scaffold then build" boundary.

### Pattern 3: Intake Handler — Two Input Paths, Same Output

**What:** `intake_handler.py` accepts two input forms and produces the same `derived_spec.md` output.

**Input Form 1 — Paragraph:**
```
"I want a website where students upload lab notebooks and I grade them"
```

**Input Form 2 — Structured spec (JSON or markdown):**
```json
{
  "goal": "Lab notebook grading platform",
  "features": ["file upload", "per-student grading", "feedback delivery"],
  "users": ["students", "professor"],
  "stack_hints": ["web", "file storage"]
}
```

**Output — derived_spec.md:**
```markdown
# OSBuilder Derived Spec

**Goal:** A web application where students upload lab notebooks and professors grade them.

**User types:**
- Students: upload files, view grades
- Professors: view submissions, enter grades, deliver feedback

**Core features:**
- File upload (PDF/image)
- Per-student grading workflow
- Feedback delivery

**App type:** web
**Playbook:** references/playbooks/web.md
**Stack hints:** file storage, multi-user auth

**Build with:** /gsd-new-project --auto
```

**Why this pattern matters:** `/gsd-new-project --auto` requires a document (file reference or pasted text). The derived_spec.md is that document. It bridges the OSBuilder intake world and GSD's world without modifying GSD. [VERIFIED: ~/.claude/skills/gsd-new-project/SKILL.md auto mode spec]

### Pattern 4: Question Bank — Outcome-Framed, Jargon-Free

**What:** `references/question-bank.md` provides a small set of outcome-framed questions with "I don't know, you decide" defaults. Questions are loaded by SKILL.md during PM role and asked selectively (not all questions on every build).

**Question format (from IN-03/IN-04):**
```markdown
## Q: Devices
"Should this work on phones and tablets too, or just on desktop computers?"
- Yes, phones too → [mobile-responsive scaffold flag]
- Just desktop is fine → [desktop-only scaffold, note in spec]
- I don't know, you decide → YES (mobile-responsive default)
```

**Never appears in questions:** "responsive", "ORM", "framework", "endpoint", "middleware", "hydration", "SSR", "SSG", "CDN", "schema", "migration".

**Question bank size (v1 web playbook):** 5-7 questions maximum. Each question has exactly 3 options: YES, NO, "I don't know, you decide".

### Pattern 5: Stack Researcher — Brainiac Delegation + Fallback

**What:** `stack_researcher.py` orchestrates a focused research call. It does NOT re-implement research logic — it delegates to `/brainiac` and parses the result.

**Brainiac invocation pattern (from ARCHITECTURE.md):**
```
/brainiac scan "modern stack for [app_type] app 2026"
```

**Result parsing:** The script looks for library names + versions in the brainiac output. If brainiac returns an inconclusive or empty result within a timeout, it reads `references/stack-menu.md` and returns those defaults.

**Structured output (stack_choices in state.md):**
```json
{
  "framework": {"name": "next.js", "version": "16.2.4", "source": "brainiac"},
  "orm": {"name": "drizzle-orm", "version": "0.45.2", "source": "stack-menu"},
  "database": {"name": "postgres", "version": "18-alpine", "source": "stack-menu"},
  "css": {"name": "tailwindcss", "version": "4.2.4", "source": "brainiac"},
  "package_manager": {"name": "pnpm", "version": "10.33.2", "source": "stack-menu"}
}
```

**`--advanced` override path:** If the user passes `--advanced`, SKILL.md prompts for overrides per stack component before `stack_researcher.py` runs. Overrides are stored in state.md as `stack_overrides` and merge over the research result.

### Anti-Patterns to Avoid

- **Hand-writing `package.json`:** Never. `create-next-app` produces it. Verified against SCAF-06 and the locked "scaffolder-first" rule.
- **Writing `tsconfig.json`:** Never. Created by `create-next-app`. OSBuilder must not touch it post-scaffold.
- **Using `--yes` alone for non-interactive scaffolding:** Unsafe — depends on saved machine preferences. Use explicit flags.
- **Creating `src/db/schema.ts` in the scaffold:** Out of scope for Phase 3. Schema definition is a GSD execute-phase concern.
- **Calling `/brainiac` as an inline command:** Use Task-tool subagent pattern (from ARCHITECTURE.md) for research-heavy invocations that would pollute main context.
- **Nesting `references/playbooks/web/` deeper than one level:** Anthropic one-level-deep rule. Flatten to `references/playbooks/web.md`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-stack web scaffolding | Custom `package.json` / `tsconfig.json` / Next.js config | `pnpm create next-app@latest` | 10M-token bolt.new failure mode; non-idiomatic; locked decision |
| Postgres connection pool | Custom connection code | `drizzle-orm/postgres-js` + `postgres` package | Edge cases in connection handling, connection pooling, SSL; official Drizzle pattern is 3 lines |
| Migration runner | Custom SQL file executor | `drizzle-kit push` / `drizzle-kit migrate` | Handles schema diffing, column renames, index management |
| pnpm installation check | Custom which/where logic | `npm install -g pnpm@latest` (idempotent) | Existing pattern; pnpm upgrades itself; one-liner is safer than custom detection |
| Question-answer parsing | Regex on user input | Structured choice from SKILL.md question bank | LLM is better at extracting choices from free text than regex |
| Web research | Custom web scraping | `/brainiac scan` delegation | brainiac is the established research skill; Phase 3 uses it, doesn't replace it |

**Key insight:** OSBuilder's value is orchestration, not reimplementation. Every line of custom code in `scaffold_dispatch.py` is a maintenance burden. The goal is the thinnest wrapper that calls the right tools in the right order.

---

## Common Pitfalls

### Pitfall 1: `--yes` Picks Wrong Defaults
**What goes wrong:** `pnpm create next-app@latest my-app --yes` uses saved preferences from a previous invocation on the machine. On a fresh machine with no saved preferences, defaults are TypeScript + Tailwind + App Router. On a machine where a developer previously chose Pages Router, `--yes` picks Pages Router.
**Why it happens:** `create-next-app` persists preferences to a config file on disk. `--yes` reads this cache.
**How to avoid:** Always pass explicit flags: `--typescript --tailwind --app --src-dir --eslint --use-pnpm --disable-git`. Each flag is idempotent and overrides cache.
**Warning signs:** Project has `pages/` directory instead of `app/`; `next.config.js` has `reactStrictMode` but no App Router config.
**Source:** [VERIFIED: nextjs.org/docs/app/api-reference/cli/create-next-app — "--yes" description]

### Pitfall 2: Nested Git Init Inside Scaffold
**What goes wrong:** `create-next-app` by default runs `git init` inside the scaffolded directory. If OSBuilder runs scaffold from within a git repo (the OSBuilder skill itself), this creates a nested git repo, which git treats as a submodule and confuses `gh repo create`.
**Why it happens:** `create-next-app` defaults to initializing git (useful for standalone use; harmful here).
**How to avoid:** Always pass `--disable-git` flag. The project's own git init happens later via `gh repo create --private`.
**Warning signs:** `git status` inside the project shows "On branch main" immediately after scaffold without OSBuilder having run `git init`.

### Pitfall 3: Writing Files the Scaffolder Already Produces
**What goes wrong:** `scaffold_dispatch.py` writes `.eslintrc.json`, `tsconfig.json`, or `package.json` after the scaffold runs. These conflict with what `create-next-app` produced, causing lint errors or type check failures.
**Why it happens:** Developer assumes the scaffolder didn't configure a tool; scaffolder already did.
**How to avoid:** The definitive "what `create-next-app` 16 produces" list: `package.json`, `tsconfig.json`, `.eslintrc.json` (or `eslint.config.mjs`), `next.config.ts`, `postcss.config.mjs`, `tailwind.config.ts`, `README.md`, `src/app/` directory. OSBuilder writes ONLY: `src/lib/db.ts`, `drizzle.config.ts`, `.env.example`, `compose.yaml`. Nothing else.
**Warning signs:** Post-scaffold `pnpm install` produces dependency resolution errors; `pnpm dev` fails with config conflicts.

### Pitfall 4: `/gsd-new-project --auto` Without a Document
**What goes wrong:** OSBuilder emits `/gsd-new-project --auto` without an `@` document reference. GSD errors with "Error: --auto requires an idea document."
**Why it happens:** The intake handler produces a brief in conversation, not on disk.
**How to avoid:** `intake_handler.py` MUST write `derived_spec.md` to `<project-root>/.planning/osbuilder/derived_spec.md` before OSBuilder emits the GSD command. The command becomes: `/gsd-new-project --auto @.planning/osbuilder/derived_spec.md`.
**Warning signs:** GSD refuses with the documented error message immediately after OSBuilder tries to hand off.
**Source:** [VERIFIED: ~/.claude/skills/gsd-new-project/SKILL.md — auto mode section]

### Pitfall 5: pnpm Not Installed
**What goes wrong:** `pnpm create next-app` fails with "command not found" because `pnpm` is not on PATH.
**Why it happens:** `pnpm` is not bundled with Node; it must be installed separately. The machine in this repo does not have pnpm installed (`pnpm: command not found` confirmed 2026-04-30).
**How to avoid:** `scaffold_dispatch.py` checks for `pnpm` before running scaffold. If absent, runs `npm install -g pnpm@latest` first (idempotent; pnpm upgrades itself). Log the install step to tutor-mode narration.
**Warning signs:** `subprocess.run(["pnpm", "--version"])` raises `FileNotFoundError`.

### Pitfall 6: state.md field mismatch for new fields
**What goes wrong:** Phase 3 needs to store `stack_choices`, `project_path`, and `stack_overrides` in state.md, but `state_writer.py` from Phase 1/2 only allows the 10 defined fields (ALLOWED_FIELDS allowlist). Writing new fields causes `SystemExit: unknown field`.
**Why it happens:** `state_writer.py` enforces a strict allowlist for V5 input validation. New fields were not anticipated.
**How to avoid:** Phase 3 must extend `state_writer.py`'s `REQUIRED_FIELDS` and `ALLOWED_FIELDS` to include the new Phase 3 fields. The ALLOWED_FIELDS set and REQUIRED_FIELDS tuple must both be updated. This is a planned extension, not a bug fix.
**Warning signs:** `state_writer.py write --field stack_choices` exits with "unknown field" error.

### Pitfall 7: Brainiac timeout leaves empty stack_choices
**What goes wrong:** `/brainiac scan` takes longer than expected or returns an empty/low-confidence result. `stack_researcher.py` returns empty stack_choices. Scaffold dispatcher has no stack to use.
**Why it happens:** Brainiac is a research agent that relies on web search; network latency is unbounded.
**How to avoid:** `stack_researcher.py` MUST implement a timeout (30 seconds is reasonable) and fallback: if brainiac result is empty or confidence < MEDIUM, read `references/stack-menu.md` and return those defaults. The fallback path is NOT an error path — it is a documented, tested behavior per RES-03.
**Warning signs:** `stack_choices` in state.md is empty `{}` after stack research step.

---

## Code Examples

### Verified: Non-Interactive create-next-app Command

```python
# Source: nextjs.org/docs/app/api-reference/cli/create-next-app (verified 2026-04-30)
# scripts/scaffold_dispatch.py

import subprocess
import sys
from pathlib import Path

def scaffold_web(project_name: str, project_root: Path) -> Path:
    """Run create-next-app in fully non-interactive mode."""
    cmd = [
        "pnpm", "create", "next-app@latest", project_name,
        "--typescript",
        "--tailwind",
        "--app",
        "--src-dir",
        "--eslint",
        "--use-pnpm",
        "--disable-git",
        "--import-alias", "@/*",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return project_root / project_name
```

### Verified: Drizzle + postgres.js Connection File

```typescript
// src/lib/db.ts — written post-scaffold by scaffold_dispatch.py
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

const queryClient = postgres(process.env.DATABASE_URL!);
export const db = drizzle({ client: queryClient });
```

### Verified: drizzle.config.ts

```typescript
// drizzle.config.ts — written post-scaffold by scaffold_dispatch.py
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

### Verified: Derived Spec Format for /gsd-new-project --auto

```markdown
# OSBuilder Derived Spec

**Goal:** [one sentence from intake]

**User types:**
- [type]: [what they do]

**Core features:**
- [feature 1]
- [feature 2]

**App type:** web
**Playbook:** references/playbooks/web.md
**Stack hints:** [optional, from --advanced or intake]

[Any additional context from clarifying questions]
```

This format is passed as `@.planning/osbuilder/derived_spec.md` to `/gsd-new-project --auto`.
[VERIFIED: ~/.claude/skills/gsd-new-project/SKILL.md — auto mode section requires "file reference or pasted/written text"]

### Pattern: state_writer.py Extension for Phase 3 Fields

```python
# State writer extension needed in Phase 3 (existing file: scripts/state_writer.py)
# Add these fields to REQUIRED_FIELDS and ALLOWED_FIELDS:

# New fields for Phase 3:
# - "project_path"    → absolute path to scaffolded project on disk
# - "stack_choices"   → JSON string of researched/confirmed stack
# - "stack_overrides" → JSON string of --advanced user overrides

REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
    # Phase 3 additions:
    "project_path", "stack_choices", "stack_overrides",
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `docker-compose.yml` filename | `compose.yaml` (Docker Compose v2) | Docker Compose v2 spec (stable 2023, mandatory 2026 convention) | OSBuilder must use `compose.yaml`, never `docker-compose.yml` |
| Tailwind config via `tailwind.config.js` | CSS-first config via `@theme` in global CSS | Tailwind v4.0 (Jan 2025) | No `tailwind.config.js` in scaffolded project; Tailwind 4 is what `create-next-app 16 --tailwind` installs |
| Turbopack opt-in flag | Turbopack ON by default (Next.js 16) | Next.js 16 (April 2026) | No `--turbopack` flag needed; it's the default bundler |
| Pages Router (default in Next.js ≤14) | App Router (`--app` flag, also the new default) | Next.js 13+ (stable Next.js 15+, sole default Next.js 16) | Must use `--app` flag explicitly for safety; `--yes` might not get this right |
| `prisma` ORM (2021-2024 default) | `drizzle-orm` (2025-2026 default for new projects) | Drizzle 0.3x era / Next.js 15+ era | Locked decision in STACK.md; Drizzle is lighter, faster cold-start |
| `npm` package manager | `pnpm` (disk-efficient, faster) | pnpm 8+ (2023+) becoming 2026 standard | `--use-pnpm` flag in create-next-app; pnpm must be installed first |

**Deprecated/outdated:**
- `docker-compose.yml` filename: Use `compose.yaml` only.
- `tailwind.config.js` in Next.js projects: Not generated by `create-next-app 16 --tailwind`; Tailwind v4 uses PostCSS plugin and CSS variables.
- `@next/font`: Replaced by `next/font` (built into Next.js 13+). Do not add this dep.
- Prisma as the default ORM: Drizzle is the locked v1 choice per STACK.md research.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | create-next-app, pnpm | YES | v25.7.0 | — |
| npm | pnpm install, npm view | YES | 11.10.1 | — |
| pnpm | create-next-app --use-pnpm | NO | — | `npm install -g pnpm@latest` (scaffold_dispatch.py installs if absent) |
| Python 3.10+ | intake_handler.py, stack_researcher.py, scaffold_dispatch.py | YES | 3.12.6 | — |
| pytest | test suite | YES | 9.0.2 | — |
| Docker / compose | compose.yaml for local Postgres | NOT CHECKED | — | `--no-docker` mode (SQLite; out of scope Phase 3) |
| git | disable-git flag means scaffold creates no nested repo; git needed for GSD handoff | Assumed present (Phase 2 preflight verifies it) | — | Phase 2 preflight handles |

**Missing dependencies with fallback:**
- `pnpm`: Not installed on the development machine. `scaffold_dispatch.py` must install it via `npm install -g pnpm@latest` before running the scaffold. This is deterministic and idempotent.

**Missing dependencies with no fallback (Phase 3 scope):**
- Docker: Phase 3 writes `compose.yaml` but does not run `docker compose up`. Postgres connectivity verification is out of scope for Phase 3 — that is Phase 4 (verify loop). The `pnpm dev` boot check does not require Postgres.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python3 -m pytest scripts/tests/ -x --tb=short` |
| Full suite command | `python3 -m pytest scripts/tests/ --tb=short` |
| Current test count | 30 tests collected (baseline before Phase 3) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IN-01 | Paragraph input → derived_spec.md on disk | unit | `pytest scripts/tests/test_intake.py::test_paragraph_to_derived_spec -x` | NO — Wave 0 |
| IN-02 | Structured spec input → same derived_spec.md | unit | `pytest scripts/tests/test_intake.py::test_structured_spec_to_derived_spec -x` | NO — Wave 0 |
| IN-03 | Questions use no jargon words (regex check on question-bank.md) | unit | `pytest scripts/tests/test_intake.py::test_questions_have_no_jargon -x` | NO — Wave 0 |
| IN-04 | Every question has "you decide" option that picks a default | unit | `pytest scripts/tests/test_intake.py::test_questions_have_you_decide_option -x` | NO — Wave 0 |
| IN-05 | derived_spec.md feeds /gsd-new-project --auto (format check) | unit | `pytest scripts/tests/test_intake.py::test_derived_spec_format -x` | NO — Wave 0 |
| RES-01 | stack_researcher.py calls brainiac (mock) and returns structured result | unit | `pytest scripts/tests/test_stack_researcher.py::test_calls_brainiac -x` | NO — Wave 0 |
| RES-02 | Stack research output is structured JSON with name/version/rationale fields | unit | `pytest scripts/tests/test_stack_researcher.py::test_output_is_structured -x` | NO — Wave 0 |
| RES-03 | Falls back to stack-menu.md when brainiac returns empty/timeout | unit | `pytest scripts/tests/test_stack_researcher.py::test_fallback_to_stack_menu -x` | NO — Wave 0 |
| RES-04 | --advanced overrides merge over research result | unit | `pytest scripts/tests/test_stack_researcher.py::test_advanced_override -x` | NO — Wave 0 |
| SCAF-01 | references/playbooks/web.md exists and documents the web playbook | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_web_playbook_exists -x` | NO — Wave 0 |
| SCAF-06 | scaffold_dispatch.py runs create-next-app (mocked) with correct flags | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_scaffold_cmd_flags -x` | NO — Wave 0 |
| SCAF-06 | Post-scaffold: drizzle deps installed (mocked pnpm call) | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_drizzle_deps_added -x` | NO — Wave 0 |
| SCAF-06 | Post-scaffold: src/lib/db.ts written with correct drizzle import | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_db_ts_written -x` | NO — Wave 0 |
| SCAF-06 | Post-scaffold: drizzle.config.ts written | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_drizzle_config_written -x` | NO — Wave 0 |
| SCAF-06 | Post-scaffold: .env.example written with DATABASE_URL | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_env_example_written -x` | NO — Wave 0 |
| SCAF-06 | Post-scaffold: compose.yaml written (Compose v2 filename) | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_compose_yaml_written -x` | NO — Wave 0 |

**Manual-only (not automatable in Phase 3):**
- Success criterion 5: `pnpm install && pnpm dev` boots on localhost:3000 — requires real pnpm install + running Next.js server; not a unit test. This is a human UAT step.
- Success criterion 7: 60-second E2E timer — requires measuring real wall-clock time across the full flow; documented as human UAT.

### Sampling Rate

- **Per task commit:** `python3 -m pytest scripts/tests/ -x --tb=short`
- **Per wave merge:** `python3 -m pytest scripts/tests/ --tb=short`
- **Phase gate:** Full suite green (>= 30 + Phase 3 new tests) before `/gsd-verify-phase 3`

### Wave 0 Gaps

- [ ] `scripts/tests/test_intake.py` — covers IN-01..IN-05 (5 stubs minimum)
- [ ] `scripts/tests/test_stack_researcher.py` — covers RES-01..RES-04 (4 stubs minimum)
- [ ] `scripts/tests/test_scaffold_dispatch.py` — covers SCAF-01, SCAF-06 (7 stubs minimum)
- Total new tests Wave 0 must drop: >= 16 RED stubs (brings total collected to >= 46)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (Phase 3 does not implement auth) | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | YES | Existing `_check_field_allowed` and `_check_value_safe` in `state_writer.py`; extend for new fields. Intake paragraph is user-controlled — must sanitize before writing to disk |
| V6 Cryptography | No (Phase 3 does not handle secrets at runtime) | `.env.example` contains only placeholder values, never real secrets |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in project_name (e.g., `../../../etc/passwd`) | Tampering | Validate `project_name` against `[a-zA-Z0-9_-]` only before passing to `subprocess.run`; reject `..` segments (matches existing `_check_value_safe` pattern) |
| Shell injection in pnpm command construction | Tampering | Use `subprocess.run(cmd_list, ...)` (list form, not shell=True); never interpolate user input into a shell string |
| Intake paragraph containing prompt injection targeting SKILL.md | Tampering | `intake_handler.py` treats the paragraph as data only; it writes to `derived_spec.md` which GSD reads as a document, not as instructions to execute |
| Secrets written to derived_spec.md | Info Disclosure | `intake_handler.py` must not write any API keys, passwords, or tokens; `.env.example` contains only placeholder DATABASE_URL |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `/gsd-new-project --auto` accepts `@file-path` as the idea document | Pattern 3, Pitfall 4 | If GSD requires inline text (not file ref), the handoff pattern breaks; workaround: pipe file content inline. Mitigated by reading the SKILL.md which confirms "@file or text." |
| A2 | `create-next-app 16` with explicit flags (`--typescript --tailwind --app`) produces an App Router project regardless of machine-saved preferences | Pattern 1, Pitfall 1 | If flags don't override cache, `--reset` flag also exists as a safety valve. |
| A3 | `pnpm create next-app@latest` is functionally identical to `npx create-next-app@latest --use-pnpm` | Standard Stack | If pnpm's create wrapper behaves differently, fall back to npx form with `--use-pnpm` flag. |
| A4 | brainiac's `scan` depth is fast enough for the 60-second E2E target | Pattern 5 | If brainiac scan takes >30 seconds, the timeout triggers stack-menu fallback — this is the documented behavior, not a failure. |

---

## Open Questions

1. **Does `state_writer.py` extension require bumping REQUIRED_FIELDS?**
   - What we know: `REQUIRED_FIELDS` is checked by the `validate` subcommand; if new fields are required, old state files (from Phase 1/2) will fail validation.
   - What's unclear: Should Phase 3 fields be optional (in ALLOWED_FIELDS but not REQUIRED_FIELDS)?
   - Recommendation: Add to ALLOWED_FIELDS only (not REQUIRED_FIELDS) — these are Phase 3+ fields that won't exist in early-phase state files. Validate only the original 10 as required.

2. **What is the exact `--auto` document format GSD uses to extract requirements?**
   - What we know: `gsd-new-project --auto` takes "file reference or pasted/written text in the prompt." The workflow reads questioning.md and templates/project.md.
   - What's unclear: Does GSD expect a specific markdown structure, or can any prose work?
   - Recommendation: Keep `derived_spec.md` simple prose with the header structure shown in Pattern 3. If GSD doesn't extract correctly, adjust the format — not the GSD skill.

3. **Should the E2E `pnpm dev` boot check be part of Phase 3 or Phase 4?**
   - What we know: Success criterion 5 ("pnpm install && pnpm dev boots") is a Phase 3 requirement.
   - What's unclear: Running a real Next.js dev server in tests is an integration test, not a unit test. It requires Docker for Postgres or a mock DATABASE_URL.
   - Recommendation: Phase 3 verifies the scaffold produces a bootable project via human UAT (not automated test). The automated test mocks the subprocess calls. Phase 4 adds the full verify loop including server boot.

---

## Project Constraints (from CLAUDE.md)

### From `./CLAUDE.md` (OSBuilder project instructions)

| Directive | Type | Applies to Phase 3 |
|-----------|------|--------------------|
| Python helper scripts only (stdlib where possible) | Required | All 3 new scripts must be stdlib-only |
| Single-threaded execution; no parallel agents | Required | stack_researcher.py calls brainiac sequentially |
| 3-reflection cap | Required | Not directly invoked in Phase 3 (Phase 4 concern) |
| Always use deterministic scaffolder (never hand-write package.json/tsconfig.json) | Required | scaffold_dispatch.py must use create-next-app for all scaffold files |
| State checkpoint at `<project-root>/.planning/osbuilder/state.md` | Required | intake_handler.py and scaffold_dispatch.py write state.md |
| Privacy default: private GitHub repos | Required | Phase 3 does not push to GitHub; Phase 6 concern |
| Refuse-list (K8s, microservices, etc.) | Required | web.md playbook must document refusals |
| Composition rule: fix sub-skills, never fork | Required | stack_researcher.py delegates to /brainiac, does not reimplement research |
| SKILL.md ≤ 200 lines | Required | Phase 3 must not expand SKILL.md beyond 200 lines; new content goes in references/ |
| One-level-deep references | Required | `references/playbooks/web.md`, `references/stack-menu.md`, `references/question-bank.md` — all flat |

---

## Sources

### Primary (HIGH confidence)

- `npm view create-next-app version` → 16.2.4 [VERIFIED: npm registry 2026-04-30]
- `npm view tailwindcss version` → 4.2.4 [VERIFIED: npm registry 2026-04-30]
- `npm view drizzle-orm version` → 0.45.2 [VERIFIED: npm registry 2026-04-30]
- `npm view drizzle-kit version` → 0.31.10 [VERIFIED: npm registry 2026-04-30]
- `npm view postgres version` → 3.4.9 [VERIFIED: npm registry 2026-04-30]
- `npm view pnpm version` → 10.33.2 [VERIFIED: npm registry 2026-04-30]
- `npx create-next-app@latest --help` — full flag list including `--disable-git`, `--yes`, explicit flags [VERIFIED: CLI output 2026-04-30]
- `https://nextjs.org/docs/app/api-reference/cli/create-next-app` — defaults, `--yes` behavior, App Router default [VERIFIED: WebFetch 2026-04-30]
- `https://orm.drizzle.team/docs/get-started-postgresql` — drizzle + postgres.js setup, config file format [VERIFIED: WebFetch 2026-04-30]
- `~/.claude/skills/gsd-new-project/SKILL.md` — `--auto` mode: requires idea document via `@` reference or inline text [VERIFIED: direct file read 2026-04-30]
- `.planning/research/STACK.md` — web stack decisions (Next.js 16, Drizzle, Postgres, pnpm, Tailwind 4) [VERIFIED: project research doc]
- `.planning/research/ARCHITECTURE.md` — orchestrator patterns, state.md schema, scaffold-first rule [VERIFIED: project research doc]
- `scripts/tests/conftest.py` — FakeShell, fake_which, tmp_install_log fixtures [VERIFIED: direct file read]
- `pyproject.toml` — pytest config, pythonpath=["scripts"], testpaths=["scripts/tests"] [VERIFIED: direct file read]
- `python3 -m pytest --collect-only` → 30 tests currently collected [VERIFIED: CLI output 2026-04-30]
- `scripts/state_writer.py` — ALLOWED_FIELDS, REQUIRED_FIELDS, validation logic [VERIFIED: direct file read]

### Secondary (MEDIUM confidence)

- WebSearch: "create-next-app 16 --yes defaults app router tailwind 4 non-interactive" — corroborates explicit-flags approach [MEDIUM: multiple sources agree]
- WebSearch: "drizzle-orm nextjs 16 postgres setup pnpm 2026" — corroborates postgres.js as recommended driver [MEDIUM: drizzle docs primary, posts secondary]

### Tertiary (LOW confidence)

- None — all critical claims verified via primary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack (create-next-app flags, package versions): HIGH — verified npm registry + official docs
- Architecture (intake → research → scaffold flow): HIGH — derived from verified ARCHITECTURE.md + GSD skill inspection
- Test patterns: HIGH — derived from existing Phase 1/2 test infrastructure
- Brainiac delegation pattern: MEDIUM — interface documented in ARCHITECTURE.md; actual brainiac output schema not tested in isolation
- Pitfalls: HIGH — most verified against CLI output or official docs; pitfall 3/4/6/7 are structural (derived from code inspection)

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (stable stack; Next.js 16 is current release; Drizzle 0.45.x is stable)
