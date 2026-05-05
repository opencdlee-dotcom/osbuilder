# Phase 1: Foundation — Research

**Researched:** 2026-04-29
**Domain:** Claude Code skill authoring (orchestrator pattern) — SKILL.md skeleton, one-level-deep directory layout, cross-platform Python helper scripts, atomic state checkpoint
**Confidence:** HIGH (Anthropic best-practices doc fetched live; ground-truth inspected on real installed skills under `~/.claude/skills/`; Python availability verified locally; winget commands verified via web search)

---

## Summary

Phase 1 is the **skill skeleton + checkpoint plumbing** that every other phase depends on. Five requirements (FOUND-01..05) sum to: (a) a valid Anthropic-format `~/.claude/skills/osbuilder/` directory with a `≤200-line` `SKILL.md`, (b) the four standard sub-directories (`references/`, `scripts/`, `assets/`, `examples/`), (c) a cross-platform bootstrap shim that handles missing Python, and (d) a Python `state_writer.py` that maintains a 10-field checkpoint at `<project-root>/.planning/osbuilder/state.md` so a `/clear`'d session can resume.

There is **no novel research** in this phase — it is execution of a well-documented pattern. Anthropic's authoritative guidance (fetched today) gives exact frontmatter rules, progressive-disclosure rules, and one-level-deep references. Six existing skills under `~/.claude/skills/` give ground-truth examples of frontmatter style, body structure, and `install.sh`/`scripts/` patterns to copy.

**Primary recommendation:** Model OSBuilder's SKILL.md after **`gsd/SKILL.md` (139 lines)** — it is the closest analog (orchestrator + routing-table → references). Use **`predator/install.sh`** as the template for the bootstrap shim approach (idempotent, mkdir-p, .gitkeep markers). For `state_writer.py`, use a **single-file atomic-rename pattern** with **YAML frontmatter wrapped in a fenced markdown block** so the file is human-readable, greppable, AND machine-parseable.

---

<user_constraints>
## User Constraints (from PROJECT.md / ROADMAP.md / Phase 1 success criteria)

CONTEXT.md does not exist yet for this phase (this is research-before-discuss). Constraints below come from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, and the explicit Phase 1 success criteria.

### Locked Decisions

- **Form:** Claude Code skill at `~/.claude/skills/osbuilder/`. Never a standalone CLI/web app.
- **Helper-script language:** Python 3.13 (cross-platform). Never bash for cross-platform logic. Never Node (chicken-and-egg with preflight).
- **Architecture:** Orchestrator-with-playbooks (Anthropic Pattern 1 + 2 fused). SKILL.md ≤ 200 lines (stricter than Anthropic's 500 ceiling). Progressive disclosure to `references/`.
- **Directory layout:** Exactly four top-level sub-directories under the skill: `references/`, `scripts/`, `assets/`, `examples/`. One level deep — no `references/playbooks/sub/`. (The `roles/` and `playbooks/` folders mentioned in research/ARCHITECTURE.md are **nested under `references/`** which is the one-level-deep convention.)
- **State location:** `<project-root>/.planning/osbuilder/state.md` (NOT inside the skill's own directory — it lives with the user's built project so it commits and survives across machines).
- **State schema:** 10 named fields exactly — `goal`, `app_type`, `playbook`, `current_role`, `current_phase`, `phase_step`, `last_failure`, `retry_count`, `escalation_level`, `next_action`. ≤ 15 lines preferred, ≤ 20 lines hard limit.
- **Bootstrap shim pair:** `bootstrap.sh` (POSIX) + `bootstrap.ps1` (Windows). The shim's only job is "Python missing → install Python → re-exec the next-step Python script."
- **Privacy default (project-wide):** When OSBuilder eventually creates GitHub repos they default to `--private`. (Not Phase 1 work but locked.)
- **Composition rule:** OSBuilder never reimplements GSD/brainiac/predator/code-tester logic. Phase 1 must not introduce any duplication.

### Claude's Discretion (Phase 1)

- Exact YAML frontmatter `description` wording (must follow Anthropic's "third person, what + when, ≤1024 chars" rule but the actual sentence is yours).
- Exact body sectioning of SKILL.md (must include routing table, but the section ordering and headings are yours).
- Whether to include `argument-hint`, `version`, `user-invocable`, `allowed-tools` frontmatter fields (these are optional in Anthropic's spec; existing skills like `gsd`, `brainiac`, `predator` all include them and you should too — they're free signal).
- Atomic-write mechanism inside `state_writer.py` (write-tmp + os.replace is industry-standard; alternatives like flock are heavier).
- Whether to ship a `.gitkeep` in the empty `assets/` and `examples/` dirs (recommend yes — git-friendly, makes `tree` output match the success criterion).

### Deferred Ideas (OUT OF SCOPE FOR PHASE 1)

- Pre-flight installer for Node/git/gh/Docker → **Phase 2**.
- Intake question bank, plain-English UX, brief synthesis → **Phase 3**.
- Stack research playbooks, scaffold dispatch → **Phase 3** + **Phase 7**.
- GSD handoff, role state machine, failure classifier, retry caps → **Phase 4**.
- Friendly-error dictionary, tutor-narration, dev-team narration → **Phase 5**.
- GitHub push, runbook generator, Dockerfile templates → **Phase 6**.
- Examples gallery, `install.sh` one-liner, version-drift checker, README → **Phase 8** (skill-quality phase).
- Sub-skill version pinning in frontmatter (`requires: gsd>=...`) — punt to Phase 8 alongside `check_skill_versions.py`.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | OSBuilder installed at `~/.claude/skills/osbuilder/` with valid YAML frontmatter (`name`, `description`) | Anthropic frontmatter rules section + existing-skill examples (gsd, brainiac, predator); install-script pattern from `predator/install.sh` |
| FOUND-02 | SKILL.md ≤ 200 lines, routes via progressive disclosure to `references/` | Anthropic progressive-disclosure Patterns 1 & 2; **`gsd/SKILL.md` (139 lines)** is the closest in-ecosystem analog and the best template |
| FOUND-03 | Skill directory layout: `references/`, `scripts/`, `assets/`, `examples/` one level deep | Anthropic "Avoid deeply nested references" rule; PDF-skill structure example; existing `gsd/` directory layout |
| FOUND-04 | Bootstrap shim (`bootstrap.sh` POSIX + `bootstrap.ps1` Windows) handles missing Python | Verified install commands (brew/apt/dnf/winget); existing `predator/install.sh` and `predator/update.sh` provide the bash-script style template |
| FOUND-05 | `state_writer.py` maintains ~15-line checkpoint with 10 named fields at `<project-root>/.planning/osbuilder/state.md` | research/ARCHITECTURE.md schema (locked, 10 fields); atomic-write pattern from Python stdlib (`os.replace`); SessionStart/compact hook behavior from issue #25999 |

</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Skill discovery + initial routing (frontmatter `name`/`description` loaded by Claude Code at startup) | **SKILL.md** (markdown) | — | Anthropic spec: only frontmatter is pre-loaded; everything else loads on-demand. SKILL.md owns this entirely. |
| Progressive-disclosure body content (routing table, the body Claude reads when triggered) | **SKILL.md** (markdown) | `references/*.md` (linked, JIT-loaded) | Anthropic Pattern 1 — SKILL.md is the table of contents; `references/` is the chapters. |
| Cross-platform OS bootstrapping when Python is absent | **`scripts/bootstrap.sh`** (POSIX) + **`scripts/bootstrap.ps1`** (Windows) | — | These are the *only* file types guaranteed to run on a fresh machine without Python: `sh` is POSIX-mandatory, PowerShell is Windows-built-in. |
| State checkpoint write/read (10 named fields, atomic) | **`scripts/state_writer.py`** (Python 3.13, stdlib-only) | `<project-root>/.planning/osbuilder/state.md` (the file itself) | Determinism + testability + atomic file ops belong in code, not in Claude prompting. |
| State checkpoint **read** at session resume (after `/clear` or compaction) | **SKILL.md instructions** (told to invoke `state_writer.py read`) | — | Reading must happen before Claude reasons about resume → SKILL.md tells Claude "if state.md exists, run `python scripts/state_writer.py read` and continue from `next_action`". |
| Empty-directory placeholders for `assets/` and `examples/` | **`.gitkeep` files** | — | Phase 1 only seeds the dirs; content is filled in later phases. `.gitkeep` keeps the structure committed without forcing premature content. |
| Skill installation mechanism | **`install.sh`** (POSIX) + (optional Phase 8) `install.ps1` | — | Phase 1 needs ONLY enough install to satisfy "after install, the skill exists at `~/.claude/skills/osbuilder/`". Full `osbuilder install` one-liner is Phase 8. |

---

## Standard Stack

### Core

| Library / Format | Version | Purpose | Why Standard |
|------------------|---------|---------|--------------|
| **Anthropic SKILL.md format** | Current 2026 spec (verified live) | Skill manifest with YAML frontmatter (`name`, `description`) + markdown body | The only format Claude Code recognizes; pre-loads frontmatter, JIT-loads body. [VERIFIED: platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices fetched 2026-04-29] |
| **Python 3.13** | 3.13.x (3.13.13 stable; 3.12.6 currently installed locally — verified via `python3 --version`) | All helper scripts (`state_writer.py`, future preflight, future scaffold dispatch) | Cross-platform, stdlib-only path is feasible; preinstalled on macOS/most Linux; one-line install on Windows. [VERIFIED: local `python3 --version` returned 3.12.6 — usable; will install 3.13 via bootstrap on machines lacking it] |
| **POSIX `sh`** | n/a | `bootstrap.sh` only — the bare-minimum shim that runs without Python | Universally present on macOS/Linux/Git-Bash. Use `#!/bin/sh` (NOT `#!/usr/bin/env bash`) for the bootstrap to avoid bash-vs-sh divergence. [CITED: existing-skill convention; Anthropic does not mandate but POSIX `sh` is the lowest common denominator] |
| **PowerShell (Windows Built-in)** | 5.1 (default Win10/11) or 7+ | `bootstrap.ps1` only — Windows shim that installs Python via winget | Built into every Windows install since Windows 7; PowerShell 5.1 minimum is safe to assume. [VERIFIED: Microsoft Learn — winget install `Python.Python.3.13`] |
| **Python stdlib only** (no third-party deps) | n/a | `state_writer.py` uses only `argparse`, `pathlib`, `tempfile`, `os`, `json`, `datetime`, `sys` | Adding any pip dependency adds a preflight liability. State checkpoint is simple text-file IO — stdlib is more than enough. [VERIFIED: Python 3.x stdlib reference] |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| **`winget`** | preinstalled Win10+/11 | Windows Python installer | Inside `bootstrap.ps1`: `winget install -e --id Python.Python.3.13 --silent` [VERIFIED: dev.to/jajera and Microsoft Learn 2026] |
| **Homebrew (`brew`)** | 4.x+ | macOS Python installer | Inside `bootstrap.sh` (mac branch): `brew install python@3.13` [CITED: Homebrew formula `python@3.13`] |
| **`apt-get`** / **`dnf`** | distro-current | Linux Python installer | Inside `bootstrap.sh` (linux branch): detect via `command -v apt-get` or `command -v dnf`, then `sudo apt-get install -y python3.13 python3.13-venv` or `sudo dnf install -y python3.13` [CITED: research/STACK.md verified pkg names] |
| **`os.replace()`** (Python stdlib) | 3.3+ | Atomic file rename for state.md writes | `state_writer.py` writes to `state.md.tmp` then `os.replace(tmp, final)` — atomic on POSIX *and* Windows (unlike `os.rename`). [VERIFIED: Python docs `os.replace` — atomic on Windows since 3.3, the only stdlib option that is portable atomic-rename] |
| **`tempfile.NamedTemporaryFile`** (Python stdlib) | always | Safe tmp-file creation in target dir | Use `dir=parent_of_state_md, delete=False` so the tmp lives on the same filesystem (atomic-rename requires same FS). [VERIFIED: Python stdlib docs] |
| **`.gitkeep`** convention | n/a | Empty-dir placeholders in `assets/` and `examples/` | Industry convention; not git-special, just an empty placeholder file. [CITED: predator/install.sh creates `.gitkeep` in empty dirs] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python stdlib only for state_writer | PyYAML for state.md format | Adds dependency = preflight liability. State.md is 10 fields — hand-parse with split(":", 1) is 20 lines. **REJECTED** — keep stdlib-only. |
| `os.replace()` atomic write | `flock` + in-place write | flock is POSIX-only, not Windows. os.replace is portable. **REJECTED flock**. |
| Pure markdown `state.md` (key: value lines) | YAML frontmatter wrapped in markdown | Pure key/value lines are simplest, greppable, no parser ambiguity. YAML frontmatter is fancy but adds parser surface. **CHOSE pure markdown lines** below in "state.md format" section. |
| `bootstrap.sh` + `bootstrap.ps1` separate files | One Python file that detects OS and dispatches | Defeats the purpose — a Python file CAN'T run when Python is the missing dep. **REJECTED** — must be `sh` + `ps1`. |
| Bootstrap installs uv or pip first | Bootstrap installs ONLY Python | Phase 1 helper scripts use stdlib only; uv/pip is unnecessary at Phase 1 boundary. Phase 2+ may need uv → install it then. **CHOSE Python-only bootstrap.** |
| `install.sh` runs immediately on `git clone` | User runs `bash install.sh` after clone | One-liner curl-pipe-sh is risky; explicit invocation is the trust contract. Phase 1: ship `install.sh`, document `bash install.sh` as the install command. |

**Installation (Phase 1 only — full one-liner installer is Phase 8):**

```bash
# Manual (Phase 1 supports this):
git clone <repo> ~/.claude/skills/osbuilder
bash ~/.claude/skills/osbuilder/install.sh

# install.sh creates the dir structure and runs bootstrap.sh if Python is missing.
```

**Version verification (performed during this research, 2026-04-29):**

| Tool | Verified Source | Verified Version |
|------|-----------------|------------------|
| Python | `python3 --version` on this machine | 3.12.6 (3.13.x is available via brew/winget) |
| Anthropic skill spec | platform.claude.com fetched live | Current; frontmatter rules quoted verbatim above |
| winget Python | Microsoft Learn / DEV community | `winget install -e --id Python.Python.3.13` (working as of search 2026-04) |
| `gsd/SKILL.md` line count | local `wc -l` | 139 lines |
| `predator/SKILL.md` line count | local `wc -l` | 230 lines |
| `architect-loop/SKILL.md` line count | local `wc -l` | 272 lines |
| `brainiac/SKILL.md` line count | local `wc -l` | 499 lines (right at Anthropic ceiling) |
| `raphael/SKILL.md` line count | local `wc -l` | 1660 lines (already over) — confirms why ≤200 user constraint matters |

---

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER (Charlie)                          │
│   (1) Installs OSBuilder one-time:                               │
│       git clone <repo> ~/.claude/skills/osbuilder                │
│       bash ~/.claude/skills/osbuilder/install.sh                 │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
   ┌───────────────────────────────────────────────────────────────┐
   │             install.sh (POSIX shim, idempotent)                │
   │   - mkdir -p references/ scripts/ assets/ examples/            │
   │   - chmod +x scripts/bootstrap.sh scripts/state_writer.py      │
   │   - if ! python3 --version; then bash scripts/bootstrap.sh; fi │
   │   - touch assets/.gitkeep examples/.gitkeep                    │
   └─────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼  (only if Python missing)
   ┌───────────────────────────────────────────────────────────────┐
   │          scripts/bootstrap.sh   ·   scripts/bootstrap.ps1      │
   │   - detect OS (uname -s / $env:OS)                             │
   │   - macOS:    brew install python@3.13                         │
   │   - Linux:    apt-get / dnf detection → install python3.13     │
   │   - Windows:  winget install -e --id Python.Python.3.13        │
   │   - re-exec the calling Python script (or print "ready")       │
   └─────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼
   ┌───────────────────────────────────────────────────────────────┐
   │       ~/.claude/skills/osbuilder/   (now installed)            │
   │                                                                │
   │   SKILL.md  ←─── Claude Code pre-loads frontmatter at startup  │
   │   ├── frontmatter: name=osbuilder, description=…               │
   │   └── body (≤200 lines): routing table → references/, scripts/ │
   │                                                                │
   │   references/   ← JIT-loaded by Claude when triggered          │
   │   scripts/      ← executed (NOT loaded as context)             │
   │     ├── bootstrap.sh / bootstrap.ps1                           │
   │     └── state_writer.py                                        │
   │   assets/       ← .gitkeep only at Phase 1                     │
   │   examples/     ← .gitkeep only at Phase 1                     │
   └─────────────┬──────────────────────────────────────────────────┘
                 │
                 │  (User now runs `/osbuilder I want a website that …`)
                 │  Claude Code loads SKILL.md body, follows the routing
                 │  table, eventually invokes state_writer.py
                 ▼
   ┌───────────────────────────────────────────────────────────────┐
   │          scripts/state_writer.py   (Python 3.13, stdlib)       │
   │                                                                │
   │   Sub-commands:                                                │
   │   - init   --goal "<text>" --project-root <path>               │
   │   - write  --field <name> --value <text>                       │
   │   - read   [--field <name>]                                    │
   │   - bump   --field retry_count                                 │
   │   - reset  --field retry_count                                 │
   │   - clear-failure                                              │
   │                                                                │
   │   Atomic write:  write to tmp → os.replace() → final           │
   └─────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼
   ┌───────────────────────────────────────────────────────────────┐
   │     <project-root>/.planning/osbuilder/state.md  (≤15 lines)   │
   │                                                                │
   │   # OSBuilder State                                            │
   │   goal: …                                                      │
   │   app_type: …                                                  │
   │   playbook: …                                                  │
   │   current_role: …                                              │
   │   current_phase: …                                             │
   │   phase_step: …                                                │
   │   last_failure: …                                              │
   │   retry_count: 0                                               │
   │   escalation_level: none                                       │
   │   next_action: …                                               │
   │   updated_at: <ISO 8601 UTC>  (bookkeeping field, doesn't      │
   │                                count against the 10)           │
   └────────────────────────────────────────────────────────────────┘
                 ▲
                 │  After /clear or auto-compaction:
                 │  SKILL.md tells Claude to first run
                 │  `python scripts/state_writer.py read`
                 │  and resume from `next_action`.
                 │
                 └─── compaction-resume mechanic
```

### Recommended Project Structure

```
~/.claude/skills/osbuilder/
├── SKILL.md                          ≤ 200 lines — orchestrator + routing
├── README.md                         (Phase 8) for humans browsing GitHub
├── install.sh                        Phase 1 — POSIX installer (mkdir + chmod + bootstrap)
│
├── references/                       JIT-loaded by Claude (Phase 1: empty placeholder OK,
│   │                                 but recommend ONE seed file to demonstrate the
│   │                                 progressive-disclosure pattern is wired)
│   └── README.md                     Phase 1 seed: "What goes here" — playbooks/, roles/
│                                     filled in Phases 3-7. Optional but recommended.
│
├── scripts/                          executed (not read as context)
│   ├── bootstrap.sh                  POSIX shim — install Python if missing
│   ├── bootstrap.ps1                 Windows shim — install Python via winget
│   └── state_writer.py               Phase 1 deliverable — 10-field checkpoint
│
├── assets/                           Phase 1: .gitkeep only
│   └── .gitkeep
│
└── examples/                         Phase 1: .gitkeep only
    └── .gitkeep
```

**Phase 1 file count:** 8 files (SKILL.md, install.sh, references/README.md *optional*, scripts/{bootstrap.sh, bootstrap.ps1, state_writer.py}, assets/.gitkeep, examples/.gitkeep) = **6 mandatory + 1 recommended seed**.

### Pattern 1: Anthropic-Compliant SKILL.md (frontmatter + progressive-disclosure body)

**What:** SKILL.md begins with YAML frontmatter (≤2 required fields), followed by markdown body with a routing table that links to `references/*.md`. Frontmatter is pre-loaded by Claude Code; body is loaded only when the skill is triggered.

**When to use:** Every Claude Code skill. Non-negotiable per Anthropic spec.

**Required frontmatter rules (verbatim from Anthropic best-practices, fetched 2026-04-29):**

> `name`:
> - Maximum 64 characters
> - Must contain only lowercase letters, numbers, and hyphens
> - Cannot contain XML tags
> - Cannot contain reserved words: "anthropic", "claude"
>
> `description`:
> - Must be non-empty
> - Maximum 1024 characters
> - Cannot contain XML tags
> - Should describe what the Skill does and when to use it
>
> Always write [description] in **third person**. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems.

**Optional frontmatter fields used by existing skills (NOT required by spec — but valuable signal):**

| Field | Used by | Purpose |
|-------|---------|---------|
| `version` | brainiac, raphael, predator, code-tester, art-engine, humanizer | Track skill versioning across updates |
| `user-invocable: true` | brainiac, predator, code-tester, art-engine, raphael, darwin | Allow user to invoke directly via slash command |
| `allowed-tools` | gsd, brainiac, predator, code-tester, raphael, art-engine | Restrict tool surface for safety |
| `argument-hint` | brainiac, predator, code-tester, raphael, art-engine, darwin | Auto-completion + usage hints |
| `disable-model-invocation: true` | coordinator | Skill is for system use only, not user-facing |

**Recommendation for OSBuilder:** Include `name`, `description`, `version: 1.0.0`, `user-invocable: true`, `allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, SlashCommand`, `argument-hint`. Omit `disable-model-invocation`.

**Example (verified frontmatter from `gsd/SKILL.md`):**

```yaml
---
name: gsd
allowed-tools: Read, Write, Edit, Bash, Agent, Glob, Grep
description: >
  Spec-driven development framework — plan, execute, verify phases. Triggers on: /gsd:, new project, plan/execute/discuss phase, debug, progress.
---
```

Note: gsd uses **`description: >` block-folded YAML** which strips newlines into spaces — useful when the description has natural line breaks. It is third-person, includes both *what* (spec-driven dev framework) and *when* (triggers list).

**Example (proposed for OSBuilder):**

```yaml
---
name: osbuilder
description: >
  Builds a working full-stack app and pushes it to a private GitHub repo from a
  plain-English description. Orchestrates GSD, brainiac, predator, code-tester
  via a virtual dev-team metaphor. Triggers on: /osbuilder, build me an app,
  scaffold a project, "I want a website/CLI/desktop app that…".
version: 1.0.0
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, SlashCommand
argument-hint: "[describe-app] — e.g., /osbuilder I want a site where students upload lab notebooks"
---
```

Length check: ~410 chars in description (well under 1024 ceiling).

### Pattern 2: Routing-Table Body (the way `gsd/SKILL.md` does it)

**What:** SKILL.md body is a thin orchestrator. After frontmatter, the body has:
1. One paragraph stating the problem the skill solves
2. A **routing decision table** (Markdown table) mapping triggers/commands to `references/<file>.md`
3. Cross-cutting rules (security, refusals, escalation) — short bullet lists
4. Resume protocol pointing at `state_writer.py read`

**When to use:** Any orchestrator-style skill that juggles multiple workflows (which is OSBuilder).

**Anchor example — `gsd/SKILL.md` (139 lines total — well under our 200 budget):**

```markdown
## Command Routing

When a command is invoked, read the corresponding reference file. Each file contains the complete instructions for that command group.

| Command(s) | Reference file |
|-----------|----------------|
| `new-project`, `map-codebase` | `references/discovery.md` |
| `discuss-phase` | `references/discuss-phase.md` |
| `plan-phase` | `references/plan-phase.md` |
…
```

This pattern is exactly what OSBuilder needs. Phase 1 only requires SKILL.md to be **valid** — it does NOT require the references/*.md files to exist yet (those are filled by Phases 3–8). Phase 1's SKILL.md routing table can list TBD targets, e.g.:

```markdown
| Trigger | Reference file (filled by phase) |
|---------|----------------------------------|
| Intake (plain-English description) | `references/intake/question-bank.md` (Phase 3) |
| Stack research | `references/playbooks/web.md` (Phase 3) etc. |
| State checkpoint read | `scripts/state_writer.py read` (Phase 1 — DONE) |
```

**Trade-off:** Routing to a file that doesn't yet exist will look like a broken link if a user opens SKILL.md as plaintext, but Claude only follows links *when triggered* — so a Phase 1 SKILL.md that references future-phase files is fine as long as Phase 1 doesn't invoke them. **Mitigate** by adding a one-line note in SKILL.md: "Reference files marked (Phase N) are stubbed and will be populated in that phase."

### Pattern 3: Atomic file rewrite for `state.md`

**What:** `state_writer.py write` writes to a tempfile in the SAME directory, then calls `os.replace(tmp_path, final_path)`. `os.replace()` is atomic on POSIX *and* Windows since Python 3.3 — the only stdlib option that's portable atomic-rename.

**When to use:** Every `state.md` mutation. Never partial-write the real file.

**Why same directory:** atomic-rename only works within a single filesystem. `tempfile.gettempdir()` may be on a different FS. Use `tempfile.NamedTemporaryFile(dir=state_md_parent, delete=False)`.

**Example (Python pseudocode):**

```python
# Source: Python stdlib docs (os.replace) + tempfile docs
import os, tempfile
from pathlib import Path

def atomic_write_text(path: Path, content: str) -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX + Windows since Py 3.3
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
```

**Edge cases the script must handle:**
- Parent directory missing → `mkdir(parents=True, exist_ok=True)`.
- Write fails mid-way → cleanup `tmp` in `except`.
- Concurrent writes (two Claude turns) → `os.replace` is atomic so the file is never corrupted, but the LATER write wins. Phase 1 doesn't need locking; Phase 4 (retry counters) might.
- Mid-write `/clear` → `os.replace` is one syscall; the kernel either has done it or hasn't. The half-written `.tmp` file is orphaned but the real `state.md` is intact.

### Pattern 4: state.md format — pure markdown key:value lines (NOT YAML frontmatter)

**What:** Each of the 10 named fields is one `key: value` line. Plus a header line `# OSBuilder State` and a trailing `updated_at:` bookkeeping line. Total ≤ 15 lines.

**Why not YAML frontmatter:** YAML frontmatter requires PyYAML or a hand-parser. Pure key/value with `key, _, value = line.partition(":")` is 3 lines of stdlib code per parse and unambiguous.

**Why not JSON:** JSON is harder to read by humans (the user can edit `state.md` mid-build per the user constraint "human-readable, diffable, editable").

**Canonical Phase 1 format (≤ 15 lines):**

```markdown
# OSBuilder State

goal: <one-sentence verbatim from user intake>
app_type: <web-app | ai-service | desktop-app | cli-tool | hub-platform | unknown>
playbook: <references/playbooks/<file>.md or "unset">
current_role: <pm | architect | frontend | backend | devops | qa | reviewer | tech-writer | none>
current_phase: <integer or 0>
phase_step: <discuss | plan | execute | verify | done | none>
last_failure: <one-line summary or "none">
retry_count: <0-3>
escalation_level: <none | gsd-debug | problem-solver | user-handoff>
next_action: <one-line — what the resumed session should do first>
updated_at: <ISO 8601 UTC>
```

**Line count math:** 1 header + 1 blank + 10 fields + 1 `updated_at` = 13 lines. Fits in the ≤15 preferred / ≤20 hard cap.

**Important:** The success criterion (Phase 1 §4) says "all 10 named fields" — `updated_at` is bookkeeping, not one of the 10. Don't accidentally count it; it must NOT be omitted but must NOT be presented as one of the 10.

**Validator regex (one per field, used by `state_writer.py read --validate`):**

```python
REQUIRED_FIELDS = [
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
]
# updated_at is required but is bookkeeping (not in REQUIRED_FIELDS for the "10 named fields" gate)
```

### Pattern 5: state_writer.py CLI surface (Python 3 + argparse, stdlib only)

**What:** A single script with sub-commands. Each sub-command does one thing. All output is on stdout for piping.

**Required sub-commands for Phase 1 acceptance criterion #4:**

| Sub-command | Purpose | Phase 1 success criterion |
|-------------|---------|---------------------------|
| `init --goal <text> [--project-root <path>]` | Create initial state.md with all 10 fields stubbed (defaults: app_type=unknown, retry_count=0, escalation_level=none, …). Sets `updated_at`. | Required by criterion #4: `state_writer.py write --goal "test"` MUST produce a state.md with all 10 fields. **Recommendation: alias `write --goal X` to internally do an `init` if state.md doesn't exist.** |
| `write --field <name> --value <text>` | Update one field. Re-writes whole file atomically. Updates `updated_at`. | Used by every transition |
| `read [--field <name>]` | Print state.md to stdout (full file) or one field's value. JSON format with `--format json` flag. | Used by SKILL.md resume protocol |
| `bump --field <name>` (only valid for `retry_count`) | Increment integer. Caps at 3 (raises non-zero exit if would exceed). | Used by failure handling (Phase 4) but the plumbing belongs in Phase 1 |
| `reset --field <name>` (only `retry_count`) | Set to 0. | Used by phase-success (Phase 4) |
| `validate` | Check that all 10 fields exist + format is valid. Exit 0 on pass, non-zero with message on fail. | Recommended for Phase 1 verification |

**Default project-root resolution:** If `--project-root` is not passed, walk up from `os.getcwd()` looking for `.planning/` (GSD convention). If not found, error out with friendly message: "No `.planning/` found above `<cwd>`. Pass `--project-root <abs-path>` or run from inside a project."

**Error mode if state.md is corrupted:**
- `read` returns exit code 2 + stderr message: "state.md at `<path>` is corrupted. Missing fields: `<list>`. Run `state_writer.py init --goal "<recover>"` to reset."
- Never silently auto-fix. Never delete. The user owns their resume token.

**Example invocations the planner will need to wire up:**

```bash
# Initialize (called once per build, by intake/PM phase)
python ~/.claude/skills/osbuilder/scripts/state_writer.py init \
  --goal "A site where students upload lab notebooks" \
  --project-root /Users/charlie/projects/lab-grader

# Update a field (called every role transition)
python ~/.claude/skills/osbuilder/scripts/state_writer.py write \
  --field current_role --value backend \
  --project-root /Users/charlie/projects/lab-grader

# Read full state (called on resume)
python ~/.claude/skills/osbuilder/scripts/state_writer.py read \
  --project-root /Users/charlie/projects/lab-grader

# Read one field
python ~/.claude/skills/osbuilder/scripts/state_writer.py read \
  --field next_action --project-root /Users/charlie/projects/lab-grader

# Validate (used by Phase 1 acceptance test)
python ~/.claude/skills/osbuilder/scripts/state_writer.py validate \
  --project-root /Users/charlie/projects/lab-grader
```

### Pattern 6: Bootstrap shim (`bootstrap.sh` + `bootstrap.ps1`)

**What:** Two parallel scripts whose ONLY job is "is Python ≥3.10 installed? if not, install it via the OS-native method, then exit 0."

**Why ≥3.10 not 3.13 strictly:** Anthropic's `code-tester`/`predator` and Python projects in 2026 typically support 3.10+. Demanding 3.13 strictly would force a re-install on machines that already have 3.11/3.12 and work fine. **Recommendation:** check `python3 --version >= 3.10`; if so, accept and exit. Only install 3.13 when missing entirely.

**bootstrap.sh (POSIX) — pseudocode skeleton:**

```sh
#!/bin/sh
# Source: existing-skill convention (predator/install.sh) + research/STACK.md preflight matrix
set -eu

# 1. Already have Python ≥ 3.10?
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        echo "Python $PY_VER detected. Bootstrap not needed."
        exit 0
    fi
fi

# 2. Detect OS
OS=$(uname -s 2>/dev/null || echo unknown)

# 3. Install
case "$OS" in
    Darwin)
        if command -v brew >/dev/null 2>&1; then
            echo "Installing Python 3.13 via Homebrew…"
            brew install python@3.13
        else
            echo "ERROR: Homebrew not found. Install from https://brew.sh first."
            exit 1
        fi ;;
    Linux)
        if command -v apt-get >/dev/null 2>&1; then
            echo "Installing Python 3.13 via apt…"
            sudo apt-get update && sudo apt-get install -y python3.13 python3.13-venv
        elif command -v dnf >/dev/null 2>&1; then
            echo "Installing Python 3.13 via dnf…"
            sudo dnf install -y python3.13
        else
            echo "ERROR: Could not detect apt or dnf. Install Python 3.13 manually."
            exit 1
        fi ;;
    *)
        echo "ERROR: Unsupported OS '$OS'. Run bootstrap.ps1 on Windows or install Python 3.13 manually."
        exit 1 ;;
esac

# 4. Verify post-install
if ! python3 --version 2>/dev/null | grep -q "Python 3\.\(1[0-9]\|[2-9][0-9]\)"; then
    echo "ERROR: Python install reported success but python3 --version still fails."
    exit 1
fi

echo "Python install succeeded. OSBuilder is ready."
```

**bootstrap.ps1 (Windows) — pseudocode skeleton:**

```powershell
# Source: Microsoft Learn (winget) + research/STACK.md preflight matrix (verified 2026-04)
$ErrorActionPreference = "Stop"

# 1. Already have Python ≥ 3.10?
$existing = Get-Command python -ErrorAction SilentlyContinue
if ($existing) {
    $verLine = & python --version 2>&1
    if ($verLine -match "Python (3)\.(\d+)") {
        $minor = [int]$Matches[2]
        if ($minor -ge 10) {
            Write-Host "Python $($verLine) detected. Bootstrap not needed."
            exit 0
        }
    }
}

# 2. Install via winget (built into Windows 10+/11)
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Error "winget not found. Update Windows or install winget from the Microsoft Store."
    exit 1
}

Write-Host "Installing Python 3.13 via winget..."
& winget install -e --id Python.Python.3.13 --silent --accept-source-agreements --accept-package-agreements
if ($LASTEXITCODE -ne 0) {
    Write-Error "winget install failed (exit $LASTEXITCODE)."
    exit 1
}

# 3. Verify (note: shell PATH may need refresh — instruct user)
$verify = Get-Command python -ErrorAction SilentlyContinue
if (-not $verify) {
    Write-Warning "Python installed, but the current shell's PATH doesn't see it yet."
    Write-Warning "Close and reopen PowerShell, then re-run install.sh / install.ps1."
    exit 0  # NOT a failure — install succeeded; just need PATH refresh
}

Write-Host "Python install succeeded. OSBuilder is ready."
```

**Critical Windows gotcha (verified via web search):**
> If `python` still opens the Microsoft Store after install, go to Settings → Apps → Advanced app settings → App execution aliases and turn OFF python.exe and python3.exe (they conflict with real Python installs).

This is a **friendly-error candidate** for Phase 5 — but Phase 1's bootstrap.ps1 should at least PRINT this hint when it detects the Microsoft-Store-shim launcher (which prints "Python was not found" but `Get-Command python` returns success).

### Anti-Patterns to Avoid

- **Multi-level reference indirection** (`SKILL.md → references/index.md → references/web/index.md`) — Anthropic's docs are explicit: "Claude may partially read files when they're referenced from other referenced files." Keep one level deep. If you need sub-categories, use filename prefixes (`web-next.md`, `web-vite.md`).
- **Loading state via "Claude remembers from earlier in conversation"** — first `/clear` kills it. `state.md` is the single source of truth, written by `state_writer.py` on every transition.
- **Hand-writing YAML parser in `state_writer.py`** — pure key:value lines, parse with `partition(":")`. No PyYAML dependency.
- **Writing to a tempfile in `tempfile.gettempdir()`** — that may be on a different filesystem; `os.replace` then is non-atomic. Use `tempfile.mkstemp(dir=parent_of_state_md)`.
- **Bash for cross-platform logic in scripts/** — bash 3.2 (mac default) ≠ bash 4 (Linux) ≠ Git-Bash (Windows). The ONLY bash file in scripts/ should be `bootstrap.sh` (POSIX `sh`, not bash). All other helpers are Python.
- **Including `python` (no `python3`) in shebang lines on macOS** — `python` is Python 2 on older macOS. Always `#!/usr/bin/env python3`.
- **Putting state.md INSIDE the skill directory** (`~/.claude/skills/osbuilder/state.md`) — the success criterion explicitly says it lives at `<project-root>/.planning/osbuilder/state.md`. State is per-build, not per-skill.
- **Auto-installing Python without user confirmation** — Phase 2's preflight has a "single confirmation prompt" rule. Phase 1's bootstrap shim runs only because the user explicitly invoked `bash install.sh`, so it doesn't need a separate confirmation, but it MUST print "Installing Python 3.13 via X..." before doing it (no silent installs).
- **Asking Claude to write/parse state.md inline** — that defeats the determinism. Always shell out to `state_writer.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file rewrite | Custom write-flush-rename with locks | `os.replace(tmp, final)` from Python stdlib | Already atomic on POSIX + Windows since Python 3.3. Custom locks add Windows-vs-POSIX divergence. |
| YAML parsing for state.md | Custom YAML mini-parser | Pure markdown `key: value` per line, `str.partition(":")` | YAML's whitespace-significance is a footgun; partition is 1 line of stdlib. |
| OS detection in bootstrap | Custom uname/wmic parsing | `uname -s` in `bootstrap.sh`; PowerShell's built-in `$env:OS` / `$IsWindows` in `.ps1` | Two-shim approach already exists for this exact reason. |
| Python version detection | Parse output of `python3 --version` with regex | `python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])'` | Returns just `3.12` — easier than parsing `Python 3.12.6` |
| Cross-platform Python install | Custom multi-distro installer logic | OS-native pkg managers: `brew` / `apt-get` / `dnf` / `winget` (in priority order per OS) | Verified pkg names from research/STACK.md; users already trust these. |
| SKILL.md routing-table format | Invent a new format | Markdown table — `gsd/SKILL.md` has the ground-truth template | Existing skill ecosystem standardized on this. |
| Frontmatter spec compliance | Guess at fields | Quote Anthropic's published rules verbatim (above) | They will reject a malformed frontmatter; rules above are authoritative. |
| Empty-dir markers in git | Custom `.empty` convention | `.gitkeep` (already used by `predator/install.sh`) | De-facto standard; tooling-agnostic. |
| State checkpoint resume mechanism | Custom hook into Claude Code's compaction event | Document in SKILL.md: "Step 1 on every invocation: if `<project-root>/.planning/osbuilder/state.md` exists, run `python scripts/state_writer.py read` and resume from `next_action`" | Anthropic-recommended pattern (issue #25999); does not require Claude Code internals. SessionStart-hook approach (MemoryForge style) is OUT OF SCOPE for v1. |

**Key insight:** Phase 1 is intentionally a **plumbing** phase. There is zero novel logic to invent. Every problem listed above already has an idiomatic solution either in the Python stdlib, the existing skill ecosystem, or Anthropic's published spec. Plans should LIBERALLY copy from `gsd/SKILL.md` and `predator/install.sh` rather than re-deriving conventions.

---

## Common Pitfalls

### Pitfall 1: Frontmatter validation rejection at install
**What goes wrong:** Skill loads but Claude Code silently rejects the frontmatter. Skill is "installed" but never triggers.
**Why it happens:** Frontmatter has an XML tag in the description (Anthropic forbids), or contains the reserved word `claude`/`anthropic`, or `name` has uppercase letters.
**How to avoid:** Validate the frontmatter as part of Phase 1 acceptance. Use a regex like `^[a-z0-9-]{1,64}$` for name. Grep description for `<` and the reserved words.
**Warning signs:** `/osbuilder` does nothing. Other skills work fine. No error message.

### Pitfall 2: SKILL.md exceeds 200 lines because of routing-table bloat
**What goes wrong:** SKILL.md grows past 200 lines as more triggers/playbooks are added across phases.
**Why it happens:** Routing table tries to enumerate every command instead of grouping.
**How to avoid:** The routing table should map **categories** (intake / research / scaffold / build / verify / ship) to reference files, NOT individual commands. ~10 routing rows max. Sub-routing happens inside each reference file.
**Warning signs:** `wc -l SKILL.md` creeps up. Adding any new playbook requires a SKILL.md edit.

### Pitfall 3: state.md silently truncated to fewer than 10 fields after a partial write
**What goes wrong:** A write crashes mid-way. The file has only 5 of 10 fields. Next read fails.
**Why it happens:** Not using atomic-rename. Writing in-place, hitting an error.
**How to avoid:** **Always** use `os.replace` with a same-directory tempfile. The script must rewrite the WHOLE file every time, never patch in place.
**Warning signs:** state.md missing fields after a `/clear` mid-build. State_writer's `validate` sub-command catches this.

### Pitfall 4: `state.md` written to wrong directory
**What goes wrong:** state.md ends up at `~/.claude/skills/osbuilder/state.md` instead of `<project-root>/.planning/osbuilder/state.md`. Multiple builds clobber each other's state.
**Why it happens:** `state_writer.py` defaults to the skill's own dir or to `os.getcwd()` without finding `.planning/`.
**How to avoid:** `state_writer.py` MUST require `--project-root` OR walk up from cwd to find `.planning/`. Fail loudly if neither.
**Warning signs:** "Why does it think I'm building lab-grader when I'm in the recipe-hub project?" — wrong state.md is being read.

### Pitfall 5: `bootstrap.ps1` succeeds but Python is not on PATH in the same shell
**What goes wrong:** winget installs Python; the install.sh / install.ps1 immediately tries to run it; PATH isn't refreshed.
**Why it happens:** Windows shell does NOT auto-refresh PATH after package install. Reboot or new shell required.
**How to avoid:** After `winget install`, exit 0 with a clear message: "Python installed. Close and reopen PowerShell, then re-run install.sh." Don't try to chain into running Python in the same process.
**Warning signs:** "winget install succeeded" → "python: command not found" in the very next line of output.

### Pitfall 6: Microsoft Store python.exe alias intercepts `python`
**What goes wrong:** `python` runs but opens Microsoft Store (because the stub launcher fires).
**Why it happens:** Windows ships an "App execution alias" for `python.exe` that opens the Store. Real Python install doesn't disable it.
**How to avoid:** `bootstrap.ps1` should test that `python --version` returns actual Python output (not the store-launcher message). If launcher detected, print remediation: "Settings → Apps → Advanced app settings → App execution aliases → turn OFF python.exe and python3.exe."
**Warning signs:** `python --version` opens an app store window instead of printing a version.

### Pitfall 7: `references/` and `examples/` empty dirs disappear from git
**What goes wrong:** Phase 1 commits the directory layout, but `git ls-tree` shows only files — empty dirs vanish.
**Why it happens:** Git doesn't track directories, only files.
**How to avoid:** Add `.gitkeep` (or any zero-byte placeholder) inside every dir that should exist post-clone. `predator/install.sh` does exactly this.
**Warning signs:** `tree ~/.claude/skills/osbuilder/ -L 2` post-clone shows fewer than 4 sub-directories. Phase 1 success criterion #2 fails.

### Pitfall 8: `os.rename` used instead of `os.replace`
**What goes wrong:** State writes work on macOS/Linux but fail on Windows when state.md already exists.
**Why it happens:** `os.rename` raises `FileExistsError` on Windows if the destination exists. `os.replace` overwrites silently on both platforms.
**How to avoid:** Always `os.replace`, never `os.rename`. Hardcoded note in code review.
**Warning signs:** Test passes on macOS, fails on Windows with `[WinError 183] Cannot create a file when that file already exists`.

### Pitfall 9: Shebang/CRLF line endings on Windows breaking `bootstrap.sh`
**What goes wrong:** `bootstrap.sh` on a Windows-cloned repo (with autocrlf) has CRLF line endings; `sh` rejects it with "bad interpreter."
**Why it happens:** Git's `core.autocrlf=true` mangles `.sh` files on Windows checkout.
**How to avoid:** Add `.gitattributes` with `*.sh text eol=lf` and `*.py text eol=lf`. **This file is a Phase 1 deliverable.**
**Warning signs:** Linux/Mac CI passes; Windows-WSL test fails with "/bin/sh: bad interpreter".

### Pitfall 10: SKILL.md routing references files that don't exist (Phase 1 stub problem)
**What goes wrong:** SKILL.md lists `references/intake/question-bank.md` (Phase 3 deliverable). User opens SKILL.md in Phase 1 → broken-looking doc.
**Why it happens:** Routing table is forward-looking; only Phase 1 deliverables are real.
**How to avoid:** Add a "**Build status**" section near the top of SKILL.md listing which phases are completed. Mark unbuilt references with `(Phase N — pending)`. This is informational; Claude only follows links *when the trigger matches* and Phase 1's only triggers are install + state ops.
**Warning signs:** Reviewer flags "broken links". Mitigation: explicit phase-status note.

---

## Code Examples

Verified patterns from existing skills + Anthropic docs.

### SKILL.md frontmatter (3 verified examples from `~/.claude/skills/`)

```yaml
# Source: ~/.claude/skills/gsd/SKILL.md (139 lines total — orchestrator pattern)
---
name: gsd
allowed-tools: Read, Write, Edit, Bash, Agent, Glob, Grep
description: >
  Spec-driven development framework — plan, execute, verify phases. Triggers on: /gsd:, new project, plan/execute/discuss phase, debug, progress.
---
```

```yaml
# Source: ~/.claude/skills/brainiac/SKILL.md (research orchestrator)
---
name: brainiac
description: >
  Deep research using 10 parallel agents. Triggers on: research, deep dive, brainiac, investigate, briefing on, teach me about, learn about.
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent, WebSearch, WebFetch
argument-hint: "[mode] [depth] [topic] — mode: compare|timeline|hunch|catchup|hypothesis|fermi (optional) | depth: scan|standard|deep|auto (default: standard) | topic: any subject | flags: --lens {stakeholder}"
version: 6.0.0
---
```

```yaml
# Source: ~/.claude/skills/predator/SKILL.md (audit/extract orchestrator)
---
name: predator
description: >
  Hunt code debt, security risks, architecture violations. Extract reusable patterns. Triggers on: refactor, audit, review security, predator.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
argument-hint: "[hunt|execute|recall|assimilate|update] [path] [goal...]"
---
```

**Pattern observed across 6+ skills (gsd, brainiac, predator, code-tester, art-engine, raphael, darwin):**
- `description: >` block-folded for multi-line readability — strips to single-line at parse time
- Description always starts with **third-person verb phrase** ("Hunt code debt…", "Deep research using…", "Spec-driven development framework — …")
- Always includes "Triggers on:" comma-separated list at the end of description
- `user-invocable: true` is included on every user-facing skill
- `version: X.Y.Z` semver tracked manually

### state_writer.py atomic write (Phase 1 deliverable, verified pattern)

```python
# Source: Python stdlib (os.replace, tempfile.mkstemp, pathlib.Path)
# https://docs.python.org/3/library/os.html#os.replace
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
)

def render_state_md(fields: dict) -> str:
    lines = ["# OSBuilder State", ""]
    for key in REQUIRED_FIELDS:
        lines.append(f"{key}: {fields.get(key, '')}")
    lines.append(f"updated_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return "\n".join(lines) + "\n"

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # atomic on POSIX + Windows since Python 3.3
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise

def parse_state_md(text: str) -> dict:
    fields: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields

def validate(fields: dict) -> list:
    """Return list of missing required field names."""
    return [k for k in REQUIRED_FIELDS if k not in fields]
```

### bootstrap.sh skeleton (Phase 1 deliverable)

```sh
#!/bin/sh
# Source: existing-skill convention (predator/install.sh) + research/STACK.md
# Purpose: ensure Python ≥3.10 is installed; install if missing.
set -eu

# 1. Check existing Python
if command -v python3 >/dev/null 2>&1; then
  ver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  major=${ver%.*}
  minor=${ver#*.}
  if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
    echo "[bootstrap] Python $ver detected — OK."
    exit 0
  fi
fi

# 2. Detect OS and install
case "$(uname -s)" in
  Darwin)
    command -v brew >/dev/null || { echo "[bootstrap] Homebrew required. Install from https://brew.sh"; exit 1; }
    echo "[bootstrap] Installing Python 3.13 via Homebrew..."
    brew install python@3.13
    ;;
  Linux)
    if command -v apt-get >/dev/null; then
      echo "[bootstrap] Installing Python 3.13 via apt..."
      sudo apt-get update && sudo apt-get install -y python3.13 python3.13-venv
    elif command -v dnf >/dev/null; then
      echo "[bootstrap] Installing Python 3.13 via dnf..."
      sudo dnf install -y python3.13
    else
      echo "[bootstrap] No supported package manager. Install Python 3.13 manually."
      exit 1
    fi
    ;;
  *)
    echo "[bootstrap] Unsupported OS. On Windows, run bootstrap.ps1 instead."
    exit 1
    ;;
esac

# 3. Verify
python3 --version || { echo "[bootstrap] Install reported success but python3 missing"; exit 1; }
echo "[bootstrap] Done."
```

### install.sh skeleton (Phase 1 deliverable, idempotent)

```sh
#!/bin/sh
# Source: ~/.claude/skills/predator/install.sh (idempotent + .gitkeep pattern)
set -eu

SKILL_DIR="${HOME}/.claude/skills/osbuilder"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Idempotent dir creation
for d in references scripts assets examples; do
  mkdir -p "$SKILL_DIR/$d"
done

# .gitkeep markers for empty dirs
for d in assets examples; do
  [ -f "$SKILL_DIR/$d/.gitkeep" ] || : > "$SKILL_DIR/$d/.gitkeep"
done

# Execute permissions on scripts
chmod +x "$SKILL_DIR/scripts/bootstrap.sh" 2>/dev/null || true
chmod +x "$SKILL_DIR/scripts/state_writer.py" 2>/dev/null || true

# Run bootstrap if Python missing
if ! command -v python3 >/dev/null 2>&1; then
  echo "[install] Python missing — running bootstrap..."
  sh "$SKILL_DIR/scripts/bootstrap.sh"
fi

echo "[install] OSBuilder installed at $SKILL_DIR"
echo "[install] Try: /osbuilder help"
```

### .gitattributes (Phase 1 deliverable, prevents Pitfall 9)

```
# Source: standard cross-platform git repo convention
* text=auto

# Ensure shell scripts and Python keep LF endings on Windows checkouts
*.sh text eol=lf
*.py text eol=lf
*.ps1 text eol=crlf
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bash for cross-platform helpers | Python stdlib + tiny POSIX/PowerShell shims for the bootstrap-only case | 2024+ as Claude Code skills proliferated; Anthropic's reference skills (skill-creator) are Python-based | Phase 1 plans should NOT introduce any non-trivial bash; only `bootstrap.sh` and `install.sh` are bash. |
| Single monolithic SKILL.md | Orchestrator + `references/*.md` progressive disclosure | Anthropic's 2025 best-practices doc mandates ≤500 lines; user constraint here is ≤200 | Phase 1's SKILL.md is the **table of contents** — the reference files come later. |
| `os.rename` for file replace | `os.replace` (atomic on Windows since Py 3.3) | Python 3.3 (Sept 2012) — but many tutorials still teach `os.rename` | Important for state.md correctness on Windows. |
| Custom locking (flock) for state files | `os.replace` atomic-rename — no lock needed | Python 3.3+ | Phase 1 doesn't need any locking primitive. Phase 4 (concurrent retry counter writes) might revisit — note in research/PITFALLS.md if it matters. |
| Anthropic's `disable-model-invocation` was undocumented | Now in spec; used by `coordinator` skill for system-only skills | 2025-2026 spec updates | Not used by OSBuilder (we want user-invocation). |
| Hand-written `state.json` | Markdown `state.md` — human-readable, diffable | Echoed in Anthropic issue #25999 (MemoryForge: 4 markdown files in `.mind/`) | Confirms our markdown-with-key:value choice is industry-aligned. |
| `winget install Python` (no version pin) | `winget install -e --id Python.Python.3.13` (`-e` for exact match, `--id` for unique pkg) | 2024 winget hardening | Use the `-e --id` form to avoid alias-collision installs. |

**Deprecated/outdated:**
- **`#!/usr/bin/env bash`** in scripts that need to run on macOS — macOS ships bash 3.2 (~2007); use `#!/bin/sh` (POSIX) for the bootstrap. Phase 1's `bootstrap.sh` uses `#!/bin/sh`.
- **Chocolatey as primary Windows package manager** — winget is preinstalled on Win10+/11; Chocolatey adds an install step. Phase 1's `bootstrap.ps1` uses winget only; scoop/choco fallback is Phase 2.
- **Storing skill state in `~/.claude/skills/<name>/state.json`** — state belongs with the project the build is for. Per-project state ≠ per-skill state.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Python `os.replace` is atomic on Windows since 3.3 — sufficient for state.md mutation | Pattern 3, code examples | If wrong on some Windows edge case, state.md could be partially-written after a crash. **Risk: LOW** — well-documented stdlib behavior, used by every major Python project since 2012. |
| A2 | Pure-stdlib Python is sufficient for state_writer.py (no PyYAML, no jsonschema) | Don't Hand-Roll, Pattern 4 | If state.md format grows complex (nested data), partition()-based parsing breaks. **Risk: LOW** at Phase 1 — schema is fixed at 10 flat fields. Re-evaluate if Phase 4+ adds nesting. |
| A3 | `winget install -e --id Python.Python.3.13` is the canonical 2026 Windows command | Bootstrap shim, Pattern 6 | If winget changes the package ID or removes it, Windows install fails. **Risk: LOW-MED** — winget IDs are stable; verified via web search 2026-04-29. Pin to "if this fails, doc says try `--id Python.Python.3.13` or `--id Python.Python.3.12`." |
| A4 | macOS has Homebrew installed when bash users invoke OSBuilder | Bootstrap shim Darwin branch | If user has no brew, bootstrap.sh exits 1 with a message. Acceptable Phase 1; Phase 2 adds the "auto-install Homebrew first" handling. **Risk: known and accepted.** |
| A5 | Linux users have either apt or dnf (covers Debian/Ubuntu/Mint and Fedora/RHEL/Rocky/Alma) | Bootstrap shim Linux branch | Arch/openSUSE/Alpine users get an error message. Acceptable Phase 1; Phase 2 expands the matrix. **Risk: known and accepted (~5% of users).** |
| A6 | `~/.claude/skills/osbuilder/` is the correct install path in Claude Code 2026 | All install paths | If Claude Code changes skill discovery path, install.sh installs to the wrong place. **Risk: LOW** — verified via existing skills (gsd, predator, brainiac all live there). |
| A7 | Frontmatter rules quoted from Anthropic docs are current as of 2026-04-29 | Pattern 1 | Anthropic could change rules. Risk mitigated by fetching live docs in this research. **Risk: LOW** — fetched 2026-04-29. |
| A8 | The "10 named fields" in state.md schema are final and locked | Pattern 4 | If future phase decides to add an 11th field (e.g., `cost_so_far`), Phase 1's `validate` sub-command would reject it. **Risk: LOW** — schema locked in research/ARCHITECTURE.md and STATE.md decisions. **Mitigation:** Make `validate` check **at least** the 10 fields exist (don't reject extras). |
| A9 | `--project-root` walked from cwd looking for `.planning/` is the right default | state_writer.py CLI | If user runs from outside their project, no `.planning/` is found. Mitigated by clear error message. **Risk: LOW.** |
| A10 | Phase 1 does NOT need a `references/*.md` file to exist (only the directory) | Recommended structure | Spec ambiguity — strict reading of FOUND-02 says "routes via progressive disclosure to `references/`" which implies at least one target. **Mitigation: ship one `references/README.md` seed file describing what goes in references/ across phases.** Adds 1 file but resolves ambiguity. |
| A11 | The success-criterion test "after a simulated `/clear`, re-loading SKILL.md and reading state.md returns the user to the same `current_role`/`current_phase` as before" is testable in Phase 1 alone | Phase 1 success criterion #5 | This requires SKILL.md to actually contain a "if state.md exists, run state_writer.py read" instruction. If the routing table is too sparse, the test fails. **Mitigation:** SKILL.md MUST include a "Resume Protocol" section even if it's the only non-table content. |
| A12 | `winget install` succeeding does NOT require shell PATH refresh in the same process is FALSE | Bootstrap, Pitfall 5 | Confirmed false by experience — Windows DOES require a new shell. Phase 1's bootstrap.ps1 explicitly handles this by exiting 0 with the "reopen shell" message. **Risk: zero — handled.** |

**If this table is empty:** N/A — 12 assumptions logged.

---

## Open Questions

1. **Should Phase 1 ship a `update.sh`?**
   - What we know: `predator/` ships both `install.sh` and `update.sh`. `gsd/` ships neither.
   - What's unclear: Phase 8 explicitly owns the publish-bar `install.sh` one-liner — does Phase 1 want a parallel `update.sh`?
   - Recommendation: **Defer to Phase 8.** Phase 1 ships only a minimal `install.sh` for skeleton creation. Update mechanism is publish-bar concern.

2. **Should `references/README.md` (the seed file) exist in Phase 1?**
   - What we know: Phase 1 success criterion #1 says SKILL.md "routes via progressive disclosure to `references/`." A non-empty `references/` is the cleanest way to demonstrate the pattern is wired.
   - What's unclear: Whether a stub `references/README.md` violates "Phase 1 is just plumbing."
   - Recommendation: **Yes, ship one `references/README.md`** that explains what reference files Phases 3-7 will add. Counts as documentation, not logic.

3. **Where does the `osbuilder install` one-liner live?**
   - What we know: PROJECT.md and Phase 8 (`QUAL-02`) own this. Phase 1 only needs `bash install.sh` to work post-clone.
   - What's unclear: Does Phase 1 need a placeholder or stub?
   - Recommendation: **Phase 1 owns `install.sh` (idempotent local installer). Phase 8 owns the curl-pipe-sh one-liner.** Don't entangle.

4. **PowerShell version: 5.1 or 7+?**
   - What we know: PowerShell 5.1 is built into Windows 10/11. PowerShell 7 (cross-platform) requires install.
   - What's unclear: Does `bootstrap.ps1` use 5.1-compatible syntax to avoid an extra install step?
   - Recommendation: **Yes, write bootstrap.ps1 to be 5.1-compatible.** Use `Get-Command`, `$ErrorActionPreference`, `Write-Host/Error/Warning` (all 5.1-OK). Avoid 7-only features like `??`, `?.`.

5. **Atomic-write concurrency — does Phase 1 need locking?**
   - What we know: `os.replace` is atomic per syscall, so the FILE is never corrupt. But two near-simultaneous writes mean the LATER one wins (the earlier is silently lost).
   - What's unclear: Could two Claude turns write concurrently in Phase 1 usage?
   - Recommendation: **No locking in Phase 1.** Single-threaded is the locked architectural decision (DeepMind 2025 multi-agent failure rates documented). Phase 4's retry counter MAY revisit; flag here for the planner.

6. **Should `state_writer.py` log every transition to a journal file (`state.log`)?**
   - What we know: research/STACK.md mentions "Journaling: append a one-line entry to `state.log` on every transition for debugging."
   - What's unclear: In Phase 1 vs deferred to Phase 4 (where retry classification needs the journal)?
   - Recommendation: **Add the journal-write line in Phase 1.** It's 3 lines of code, atomic-append (no rename needed), and Phase 4+ benefits from data being there from day 1.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | state_writer.py, future scripts | ✓ | 3.12.6 (verified) | If <3.10: bootstrap.sh installs 3.13 |
| POSIX `sh` | bootstrap.sh, install.sh | ✓ | bash 3.2 / zsh / dash all OK | None — universal |
| `git` | install (clone) | ✓ (assumed; Charlie has gh ecosystem) | n/a | User error if missing |
| `brew` | macOS Python install | ✓ on macOS dev machines | n/a | bootstrap.sh exits with friendly error if missing |
| `winget` | Windows Python install | ✗ on this machine (macOS host) — verified preinstalled on Win10+/11 per Microsoft Learn | n/a | scoop fallback (Phase 2) |
| `apt-get` / `dnf` | Linux Python install | ✗ on this machine (macOS host) — assumed on Debian/Ubuntu/Fedora | n/a | Phase 2 expands distro matrix |
| Claude Code | Skill loading at all | ✓ (running this conversation) | current | None |

**Missing dependencies with no fallback (Phase 1):**
- None on the development machine.
- For users with **no Python AND no Homebrew** (mac), AND no apt/dnf (Linux): bootstrap.sh exits 1 with a friendly message. Phase 2's preflight is the formal solution.

**Missing dependencies with fallback:**
- Windows users without winget: bootstrap.ps1 exits with friendly error. Phase 2 adds scoop fallback.

**Per the Step 2.6 protocol, this phase is partly external-tool-dependent (it must INSTALL Python under specific conditions) so the audit is included rather than skipped.**

---

## Validation Architecture

**Note:** `.planning/config.json` has `workflow.nyquist_validation: true`, so this section is included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | **pytest** (Python stdlib `unittest` is also acceptable; pytest is cleaner) |
| Config file | `pyproject.toml` or `pytest.ini` — Wave 0 task creates one |
| Quick run command | `pytest scripts/tests/ -x` |
| Full suite command | `pytest scripts/tests/` |

For the bootstrap shims (`bootstrap.sh` / `bootstrap.ps1`) which are NOT Python, we use:

| Property | Value |
|----------|-------|
| Bash linter | **ShellCheck** (already noted as required tooling in research/STACK.md) |
| Quick lint | `shellcheck scripts/bootstrap.sh scripts/install.sh` |
| Manual smoke test | Run `bootstrap.sh` in a Docker container without Python — verify exit 0 + Python installed |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | Skill installed at `~/.claude/skills/osbuilder/` with valid frontmatter | smoke | `test -d ~/.claude/skills/osbuilder && head -20 ~/.claude/skills/osbuilder/SKILL.md \| grep -E '^name: osbuilder$'` | ❌ Wave 0 (write `tests/test_install.sh`) |
| FOUND-01 | Frontmatter passes Anthropic rules (name regex, description ≤1024 chars, no XML/reserved words) | unit | `pytest scripts/tests/test_skill_md.py::test_frontmatter_valid` | ❌ Wave 0 |
| FOUND-02 | SKILL.md ≤ 200 lines | smoke | `[ "$(wc -l < ~/.claude/skills/osbuilder/SKILL.md)" -le 200 ]` | ❌ Wave 0 |
| FOUND-02 | SKILL.md has at least one `references/` link in body | unit | `pytest scripts/tests/test_skill_md.py::test_has_references_link` | ❌ Wave 0 |
| FOUND-03 | Four sub-directories exist, no nesting deeper than 1 level | smoke | `find ~/.claude/skills/osbuilder/{references,scripts,assets,examples} -mindepth 2 -type d` (must return empty for nesting check) | ❌ Wave 0 |
| FOUND-04 | bootstrap.sh succeeds on a Python-less POSIX system | manual / docker | `docker run -it python-less-image bash bootstrap.sh && python3 --version` (manual smoke; CI-able later) | ❌ Wave 0 (or accept manual) |
| FOUND-04 | bootstrap.ps1 syntax-valid PowerShell 5.1 | static | `pwsh -NoProfile -Command 'Get-Command -Syntax \$null=Test-Path bootstrap.ps1; [System.Management.Automation.PSParser]::Tokenize((Get-Content bootstrap.ps1 -Raw),[ref]\$null)'` | ❌ Wave 0 |
| FOUND-05 | `state_writer.py write --goal "test"` produces state.md with all 10 fields | unit | `pytest scripts/tests/test_state_writer.py::test_init_creates_all_fields` | ❌ Wave 0 |
| FOUND-05 | state.md ≤ 20 lines | unit | `pytest scripts/tests/test_state_writer.py::test_line_count_under_20` | ❌ Wave 0 |
| FOUND-05 | Atomic write — interrupted write does not corrupt existing state.md | unit | `pytest scripts/tests/test_state_writer.py::test_atomic_replace_no_partial` | ❌ Wave 0 |
| FOUND-05 | Read after `/clear` returns same fields as last write | integration | `pytest scripts/tests/test_state_writer.py::test_round_trip` | ❌ Wave 0 |
| FOUND-05 | `validate` rejects state.md missing fields | unit | `pytest scripts/tests/test_state_writer.py::test_validate_rejects_missing` | ❌ Wave 0 |
| (Phase 1 SC #5) | After simulated `/clear`, reading state.md returns same `current_role`/`current_phase` | integration | `pytest scripts/tests/test_state_writer.py::test_resume_simulated_clear` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest scripts/tests/test_<file>.py -x` (the unit test for the file just changed)
- **Per wave merge:** `pytest scripts/tests/` + `shellcheck scripts/bootstrap.sh scripts/install.sh`
- **Phase gate:** Full pytest suite + shellcheck green + manual smoke install on a fresh machine (or VM/Docker) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `scripts/tests/__init__.py` — empty file to make tests/ a package
- [ ] `scripts/tests/test_state_writer.py` — covers FOUND-05 unit + integration tests
- [ ] `scripts/tests/test_skill_md.py` — covers FOUND-01 (frontmatter) + FOUND-02 (line count, references)
- [ ] `scripts/tests/test_install.sh` — bash smoke test for FOUND-01/03 (or absorb into pytest with subprocess)
- [ ] `pyproject.toml` (or `pytest.ini`) — pytest config; declare `pythonpath = scripts`
- [ ] `.gitattributes` — line-ending rules (prevents Pitfall 9)
- [ ] Optional: `Dockerfile.test` — Python-less Linux image for FOUND-04 bootstrap smoke test (deferrable to Phase 2 CI work)

**Framework install:** `python3 -m pip install pytest` (state_writer.py itself uses no pytest — pytest is dev-only). If user has no pip yet, bootstrap.sh handles it (Python comes with pip since 3.4+).

---

## Security Domain

**`security_enforcement`** is not explicitly set in `.planning/config.json` → treat as enabled. Apply ASVS lens.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Phase 1 has no auth surface (skill is local + filesystem-only) |
| V3 Session Management | no | No sessions; state.md is local file |
| V4 Access Control | partial | state.md is in user's home dir / project dir — relies on standard Unix file permissions. Phase 1 should `chmod 600` state.md? **Recommendation: don't chmod; let umask handle it. Note in research that state.md may contain user goals/PII.** |
| V5 Input Validation | yes | `state_writer.py write --field <name> --value <text>` — **`--value` is user-controlled and is written verbatim to state.md.** Must reject newline characters in value (which would corrupt the line-per-field format) and pre-validate `--field` is in REQUIRED_FIELDS list. |
| V6 Cryptography | no | Phase 1 stores no secrets in state.md. Goals/specs are in plaintext (acceptable). |
| V7 Error Handling | yes | All scripts must handle errors with friendly messages — never expose stack traces (Phase 5 owns the friendly-error dictionary, but Phase 1 scripts must at minimum print clean exit messages, not raw tracebacks). |
| V8 Data Protection | partial | state.md contains the user's app goal verbatim — could be sensitive (e.g., "build a system to track grade fraud"). It's stored in a project dir owned by the user, no network exposure. **Acceptable.** |
| V12 File Handling | yes | atomic file ops (handled by Pattern 3); path traversal — `--project-root` must be a resolved absolute path; reject `..` in `--field` values |
| V14 Configuration | yes | install.sh must be idempotent (verified pattern); never `rm -rf` paths; bootstrap shim must not run with root unless apt/dnf explicitly require it (it does — `sudo apt-get`) |

### Known Threat Patterns for OSBuilder Phase 1

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Newline in `--value` corrupts state.md format | Tampering | Reject `\n` and `\r` in `--value`; replace with space + warn, OR exit 2 with error. **Recommend: reject with exit 2.** |
| Field name injection (e.g., `--field "goal\nretry_count"`) | Tampering | Validate `--field` against REQUIRED_FIELDS allowlist; never interpolate user-supplied field names into the rendered output. |
| `--project-root` path traversal | Tampering | `Path(arg).resolve()` and verify it exists and is a directory. Reject paths outside HOME (optional safety). |
| Symlink attack on state.md | Tampering | `state.md` parent is `.planning/osbuilder/` — owned by user. **Risk: very low** for a local skill. Acceptable to skip for Phase 1; revisit if OSBuilder ever runs as root. |
| Bootstrap shim downloads compromised Python | Tampering | OSBuilder uses **OS-native** package managers (brew, apt, dnf, winget) — they have their own signature/integrity protocols. **Mitigation in place by delegation.** |
| Sudo prompt during bootstrap | Repudiation/UX | bootstrap.sh's apt/dnf branch uses `sudo` — print "About to run `sudo apt-get install python3.13`" before invoking, so user has a chance to abort. Phase 5's friendly-error handles bad sudo. |
| install.sh writes outside `~/.claude/skills/osbuilder/` | Tampering | All paths in install.sh anchored to `${HOME}/.claude/skills/osbuilder` — never use cwd-based paths. |
| state.md leaks via git commit (private project goal) | Information Disclosure | state.md is INSIDE the user's project's `.planning/osbuilder/` — it commits with the project. **Acceptable** because user's project is private GitHub by default (PROJECT.md decision). Phase 6 SHIP-04 owns gitleaks pre-commit; not Phase 1's job. |

**Phase 1 explicit security must-do's (planner: ensure each plan addresses these):**
1. **Validate `--field` against REQUIRED_FIELDS allowlist** in state_writer.py.
2. **Reject newline/CR in `--value`** in state_writer.py.
3. **Resolve `--project-root` to absolute path + verify directory exists** before any file IO.
4. **install.sh anchored paths only** — never use `cwd`-relative paths.
5. **Bootstrap shim prints "About to run sudo..." before sudo** invocation.

---

## Sources

### Primary (HIGH confidence)

- **[Anthropic — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)** — fetched live 2026-04-29; quoted frontmatter rules, progressive disclosure rules, scripts-vs-references rule verbatim
- **[Anthropic — Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)** — referenced from best-practices doc; confirms filesystem architecture
- **[Claude Code — Extend Claude with skills](https://code.claude.com/docs/en/skills)** — Claude Code-specific skill installation (`~/.claude/skills/<name>/`)
- **`~/.claude/skills/gsd/SKILL.md`** — direct inspection (139 lines) — closest in-ecosystem analog for OSBuilder's orchestrator pattern; routing-table format template
- **`~/.claude/skills/predator/install.sh`** — direct inspection — idempotent install pattern with `mkdir -p` + `.gitkeep` + `chmod +x`
- **`~/.claude/skills/predator/update.sh`** — direct inspection — auto-detection + backup pattern (relevant for Phase 8 follow-on, noted here)
- **`~/.claude/skills/{brainiac, predator, code-tester, art-engine, raphael, darwin, humanizer, canvas-lms, coordinator}/SKILL.md`** — frontmatter-style sample (9 skills) confirming third-person description, `triggers on:` convention, `version`/`user-invocable`/`allowed-tools`/`argument-hint` optional fields
- **Python stdlib docs (os.replace, tempfile, pathlib)** — atomic file rewrite pattern; verified `os.replace` is atomic on Windows since Py 3.3
- **[Microsoft Learn — winget Python install](https://learn.microsoft.com/en-us/windows/dev-environment/python)** — `winget install -e --id Python.Python.3.13` is the canonical 2026 command

### Secondary (MEDIUM confidence)

- **[GitHub Issue #25999 — Persistent state across context compaction](https://github.com/anthropics/claude-code/issues/25999)** — community-validated `state.md` pattern; SessionStart-hook approach (MemoryForge) is referenced for v2 awareness only
- **[DEV — Install Python on Windows via winget](https://dev.to/jajera/install-python-on-windows-via-cli-winget-3lnm)** — confirms winget command + Microsoft Store alias gotcha
- **`.planning/research/STACK.md`** (this project) — Python 3.13 + uv + winget package IDs verified earlier; cross-references back to Microsoft Learn / Homebrew formulas
- **`.planning/research/ARCHITECTURE.md`** (this project) — locks the 10-field state.md schema, the orchestrator-with-playbooks pattern, the per-build state location

### Tertiary (LOW confidence)

- **None this phase.** Every claim above traces to either Anthropic docs (HIGH), direct inspection of installed skills (HIGH), or the Python stdlib (HIGH). No web-only-search claims feed this phase's decisions.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — Anthropic spec fetched live; existing-skill ground truth inspected; Python stdlib well-documented
- Architecture (one-level-deep, frontmatter, routing-table): **HIGH** — directly from Anthropic best-practices doc + 9 verified existing-skill SKILL.md files
- state.md schema + atomic-write: **HIGH** — schema locked in research/ARCHITECTURE.md; Python `os.replace` atomic guarantee is published stdlib behavior
- Bootstrap shim cross-platform paths: **HIGH for macOS, MEDIUM-HIGH for Linux (covers ~95% via apt/dnf), MEDIUM for Windows (winget verified, but Microsoft-Store-shim collision is a known UX issue partially mitigated)** — this drove Pitfall 5 and Pitfall 6
- Pitfalls: **HIGH** — Pitfalls 1, 5, 6, 8, 9 all directly observed in the broader Claude Code / Python ecosystem and documented elsewhere
- Validation architecture: **MEDIUM-HIGH** — pytest is the obvious choice; the exact test list is one-to-one with success criteria

**Research date:** 2026-04-29
**Valid until:** 2026-05-29 (30 days — stack is stable; Anthropic skill format is the only thing that could shift, and it's been stable since 2025-Q3)
