# Stack Research

**Domain:** Claude Code skill orchestrating an end-to-end "describe → working app on private GitHub" pipeline (virtual dev-team metaphor)
**Researched:** 2026-04-29
**Confidence:** HIGH for OSBuilder's own stack (verified against Anthropic skills docs, Node/Python release notes); MEDIUM for the per-build defaults menu (verified against Next.js / Tauri / FastAPI release notes; per-build research happens at runtime so menu is a starting point, not a contract)

---

## Scope

This document answers **two** stack questions, in priority order:

1. **OSBuilder's own implementation stack** — what the skill itself is built from. *Heavily prioritized.*
2. **The "research-driven defaults" menu** — opinionated starting points OSBuilder picks when scaffolding the apps it builds. *Per-build research at runtime overrides these; the menu is the fallback when research is inconclusive.*

---

# Part 1 — OSBuilder's Own Stack

## Recommended Stack (the skill itself)

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Markdown SKILL.md** | n/a (Anthropic skills spec, current as of 2026) | Primary skill entrypoint with YAML frontmatter (`name`, `description`) and progressive-disclosure body | Required by Anthropic's skill format; the only thing Claude Code loads at startup is `name` + `description` from frontmatter. Body loaded on-demand. |
| **Python** | 3.13.13 (stable maintenance) or 3.14.4 (latest feature) | Helper scripts: preflight checks, scaffolder invocation, GitHub CLI wrapping, JSON state I/O | Most reliable cross-platform of the three candidates (bash/Python/Node). Stdlib (`subprocess`, `pathlib`, `shutil`, `platform`, `json`, `argparse`) covers ~90% of what the skill needs. Already required as a transitive dependency on macOS/most Linux; trivially installable on Windows. |
| **Bash** | 4+ (macOS ships 3.2 — assume `#!/usr/bin/env bash` and document the gap) | Tiny one-liners only: simple shell glue, `gh`/`git` wrappers when Python would be overkill | Acceptable for *trivial* shell glue; **not** acceptable for anything cross-platform. Windows users (even with Git Bash / WSL) hit edge cases. ShellCheck must lint every bash file in the skill. |
| **uv** | 0.5+ (Astral, 2026 stable) | Python toolchain bootstrap inside the skill's virtual environment when scripts have third-party deps | 10-100× faster than pip; one tool replaces pip + virtualenv + pyenv. Single-binary install means OSBuilder's preflight can grab it without already-installed Python. |
| **GitHub CLI (`gh`)** | 2.x (latest stable) | All GitHub operations (private repo create, push, PR open, issue file, workflow trigger) | Officially supported by GitHub; one binary on every OS; auth flow (`gh auth login`) is the only sane path for "common person" users. Alternative (raw `git` + manual token in `~/.netrc`) is not friendly. |
| **git** | 2.40+ | Source control, scaffolder output staging | Universal; assumed by `gh`. |

**Rationale for "Python over Node over bash" as helper-script language:**

- **Bash fails Windows.** Even Git Bash diverges (`readlink -f` missing, `sed -i` differs, `mktemp -d` differs, GNU vs BSD utilities). ShellCheck flags these but doesn't fix them. For a "common person" tool that *must* work on Windows, bash is a non-starter for anything beyond trivial.
- **Node would force the user to have Node installed before OSBuilder can preflight-install Node.** Chicken-and-egg. Worse, Node's child_process across platforms requires `cross-spawn` / `execa` shims that themselves are npm dependencies — adding install steps before preflight runs.
- **Python is preinstalled on macOS (since 12) and most Linux distros**, and is the most common single-line install on Windows (`winget install Python.Python.3.13`). If OSBuilder finds itself without Python, that's the *first* preflight install — and it's the only time the skill itself would need a bootstrap shim (a tiny POSIX-compliant `sh` script with PowerShell fallback for Windows that just installs Python and re-execs).

### Skill File Layout (Anthropic-recommended, current 2026)

```
~/.claude/skills/osbuilder/
├── SKILL.md                    # ≤ 200 lines (user constraint; Anthropic spec allows 500)
├── state.md                    # ~15-line checkpoint, updated per phase, survives compaction
├── references/
│   ├── playbook-web.md         # Loaded on-demand: web app build playbook
│   ├── playbook-cli.md         #   "          ": CLI app
│   ├── playbook-desktop.md     #   "          ": desktop (Tauri default)
│   ├── playbook-ai-service.md  #   "          ": AI/FastAPI service
│   ├── stack-menu.md           # The defaults from Part 2 below — referenced by Architect role
│   ├── role-pm.md              # Virtual PM role prompts/playbook
│   ├── role-architect.md       # Virtual Architect role
│   ├── role-frontend.md        # Frontend dev role
│   ├── role-backend.md         # Backend dev role
│   ├── role-devops.md          # DevOps role (Docker, CI)
│   ├── role-qa.md              # QA role (delegates to /code-tester)
│   ├── role-reviewer.md        # Reviewer role (delegates to /predator, /gsd-code-review)
│   ├── role-tech-writer.md     # Tech Writer role (README, runbook)
│   └── failure-classifier.md   # Failure types + decision table for retry/escalate
├── scripts/
│   ├── preflight.py            # Detect + install Node/Python/git/gh/Docker (Python)
│   ├── bootstrap.sh            # POSIX shell + PowerShell sibling — installs Python if missing
│   ├── bootstrap.ps1           # Windows entry — installs Python via winget then re-execs preflight.py
│   ├── scaffolder.py           # Wraps create-next-app / create-t3-app / npm create vite / cargo new
│   ├── gh_helper.py            # Thin wrapper around `gh repo create --private`, `gh repo clone`, etc.
│   ├── state_io.py             # Read/write state.md (atomic, journaled)
│   └── narrate.py              # Dev-team metaphor narration ("PM is gathering requirements... ✓")
├── assets/
│   ├── env.example.tpl         # Template for generated apps' .env.example
│   ├── gitignore.tpl           # Sensible-defaults .gitignore (overlays scaffolder output)
│   ├── ci.yml.tpl              # Single GitHub Actions workflow template
│   └── runbook.md.tpl          # Clone-and-run README template
└── tests/                      # ShellCheck + pytest for helper scripts
    ├── test_preflight.py
    ├── test_scaffolder.py
    └── test_state_io.py
```

**SKILL.md ≤ 200 lines (user constraint, stricter than Anthropic's 500-line ceiling).** Everything beyond the table-of-contents and dispatch logic lives in `references/` and is loaded on-demand. *Confidence: HIGH (Anthropic skill-creator SKILL.md as reference).*

### `state.md` Schema (for compaction-resume)

Aim for ~15 lines. Atomic write (write-tmp-then-rename). Journaling: append a one-line entry to `state.log` on every transition for debugging.

```markdown
# OSBuilder State

goal: <one-line user goal>
project_path: <abs path to generated project>
github_repo: <owner/repo or "not-yet-created">
phase: <pm | architect | frontend | backend | devops | qa | reviewer | tech-writer | done>
phase_index: <N of M>
last_action: <one line, ISO timestamp + verb>
last_failure: <none | classifier-tag + one-line message>
reflections_used: <0-3>
plans_done: <comma-separated phase IDs that completed>
plans_pending: <comma-separated phase IDs queued>
stack_chosen: <brief — e.g. "next15+drizzle+postgres-compose">
notes: <free text, ≤ 2 lines>
```

When OSBuilder resumes after `/clear` or auto-compaction:
1. Read `SKILL.md` (auto-loaded by Claude Code).
2. Read `state.md` — establishes goal, current phase, last failure.
3. Resume at `phase` with `reflections_used` carried over.

This matches Anthropic's persistent-state pattern (separate human-readable markdown files queried mid-session) — *Confidence: HIGH (matches the Anthropic Managed Agents architecture and the [Claude Code persistent-state issue](https://github.com/anthropics/claude-code/issues/25999) discussion).*

### Pre-flight Installer — Cross-Platform Compatibility Matrix

OSBuilder's preflight detects + offers to install: **Node.js, Python, git, gh CLI, Docker.** All five are needed for the "research-driven defaults menu" to work; Node + git + gh are the absolute minimum.

| Tool          | macOS (Homebrew)                  | Linux (apt / dnf)                                                | Windows (winget primary, scoop fallback)        |
|---------------|-----------------------------------|------------------------------------------------------------------|-------------------------------------------------|
| **Node.js**   | `brew install node@24`            | NodeSource repo: `curl -fsSL https://deb.nodesource.com/setup_24.x \| sudo -E bash - && sudo apt install nodejs` | `winget install OpenJS.NodeJS.LTS` (or scoop: `scoop install nodejs-lts`) |
| **Python**    | `brew install python@3.13`        | `sudo apt install python3.13 python3.13-venv` (or distro pkg)    | `winget install Python.Python.3.13`             |
| **git**       | `brew install git` (preinstalled with Xcode CLT) | `sudo apt install git` / `sudo dnf install git`               | `winget install Git.Git`                        |
| **gh CLI**    | `brew install gh`                 | `sudo apt install gh` (after adding GitHub repo) or `sudo dnf install gh` | `winget install GitHub.cli`             |
| **Docker**    | OrbStack (`brew install --cask orbstack`) **strongly preferred** over Docker Desktop on Mac (faster, smaller, same CLI) | `sudo apt install docker.io docker-compose-plugin` (or distro Docker repo) | `winget install Docker.DockerDesktop` (no good free alternative on Windows in 2026) |

**Detection order:** OSBuilder's preflight runs `which <tool>` (or `where <tool>` on Windows) → falls back to platform-specific lookup (`brew list`, `dpkg -l`, `winget list`) → then offers install with single-confirmation prompt.

**Anti-recommendations for preflight:**
- ❌ **Do NOT use Chocolatey** as primary on Windows — winget is built-in to Windows 10+/11, Chocolatey requires admin elevation and a separate install. Keep Chocolatey only as the third fallback (after winget, after scoop) for packages that exist nowhere else.
- ❌ **Do NOT use Colima** as the Docker default — its networking is buggy enough to cause silent compose failures; OrbStack is the default on Mac when it's available, raw Docker Engine on Linux, Docker Desktop on Windows.
- ❌ **Do NOT use Snap on Linux** — confinement breaks `gh auth login` in surprising ways; prefer apt/dnf/yum native packages.
- ❌ **Do NOT auto-install without confirmation** — single-confirmation prompt per tool is the trust contract.

*Confidence: HIGH for macOS/Linux paths (verified against Homebrew formulae, apt repos, Docker docs); MEDIUM for Windows (winget IDs verified against Microsoft Learn and winget.run).*

### Helper-script tooling

| Tool | Purpose | Notes |
|------|---------|-------|
| **ShellCheck** | Lint every `.sh` file in the skill on commit | Required — bash bugs are silent on Mac, fatal on Linux/Windows. Run via pre-commit or just manually before publishing. |
| **ruff** | Lint + format Python helper scripts (replaces flake8 + black) | Astral-built, same vendor as `uv`. Faster than the alternatives; one config file. |
| **pytest** | Test helper scripts | Keep tests cross-platform — use `tmp_path` fixture, never hardcode `/tmp`. |
| **pre-commit** | Run ShellCheck + ruff + pytest on git commit | One config file, reproducible across contributors. |

### Installation (for OSBuilder itself)

OSBuilder is a *skill*, not a package. Install = clone or `osbuilder install` one-liner that drops the directory into `~/.claude/skills/osbuilder/`. No npm/pip install for the skill itself.

```bash
# Suggested one-liner install (final form TBD in Phase 1):
curl -fsSL https://raw.githubusercontent.com/cdlee/osbuilder/main/install.sh | sh
# Or, manual:
git clone https://github.com/cdlee/osbuilder.git ~/.claude/skills/osbuilder
```

For the helper scripts' Python deps (if any are needed beyond stdlib):

```bash
# Inside ~/.claude/skills/osbuilder/, after install:
uv venv
uv pip install -r scripts/requirements.txt   # only if non-stdlib deps emerge
```

**Goal: keep helper scripts stdlib-only where possible.** Every dep is a preflight liability.

## Alternatives Considered (OSBuilder's own stack)

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Python helper scripts | Bash | Single-line glue (`gh auth status \|\| gh auth login`) where Python's startup overhead matters. Never for cross-platform code. |
| Python helper scripts | Node.js / TypeScript | Only if a future v2 needs heavy interop with the JS scaffolder ecosystem (`create-next-app` API mode). Not for v1 — Node is not preinstalled on a fresh "common person" machine. |
| `uv` for Python deps | `pip` | Locked-down corp environments without permission to install `uv`. Falls back gracefully — uv is `pip`-compatible. |
| `gh` CLI for GitHub | Raw `git` + PAT in `.netrc` | Never recommend for "common person" users. Acceptable only for `--advanced` mode users who already have it set up. |
| OrbStack on Mac | Docker Desktop | If user already has Docker Desktop installed, leave it — don't force migration. New installs default to OrbStack. |
| OrbStack on Mac | Colima | Almost never — Colima networking issues are well-documented and break `compose up` silently. |
| `state.md` markdown checkpoint | `state.json` | Markdown is human-readable, diffable, editable by user mid-build. JSON is faster to parse but less debuggable. The skill ecosystem already standardizes on `.md` state files. |

## What NOT to Use (OSBuilder's own stack)

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Long-running daemon / background service** | Skills must be installable as static files; cross-platform service management is a quagmire (launchd vs systemd vs Windows Services). User constraint: "no daemon." | One-shot Python scripts triggered by skill invocations. State persists in `state.md`. |
| **Bash for cross-platform logic** | Macos's bash 3.2, Linux GNU coreutils, Windows Git Bash all diverge. Silent failures eat days. | Python (stdlib only when feasible). |
| **Node.js for preflight** | Chicken-and-egg: Node is one of the things preflight installs. Cannot require Node to install Node. | Python (or POSIX `sh` + PowerShell sibling for the very first bootstrap if Python is also missing). |
| **Chocolatey as primary Windows package manager** | Requires admin elevation + separate install. winget is preinstalled on Win10+/11. | winget primary, scoop fallback, choco only as last-resort. |
| **Colima as default Docker engine on Mac** | Networking edge cases break compose silently. Not a "common person" experience. | OrbStack on Mac (free, faster, drop-in CLI). |
| **`pipx` for OSBuilder helper-script deps** | Adds another preflight tool to install. `uv` covers the same ground. | `uv` + a project-local `.venv`. |
| **Custom prompt-management system on top of skills** | Anthropic skills *are* the prompt management system in 2026. Reinventing it is the trap the skills format was built to avoid. | Use `references/` for role-specific playbooks, loaded on-demand. |
| **Hand-written `package.json` / `pyproject.toml` for the apps OSBuilder builds** | User explicit constraint + Lovable/bolt.new failure mode (10M+ tokens generating boilerplate badly). | Always use deterministic scaffolders (Part 2 below). |
| **Premature monorepo for the skill itself** | OSBuilder is one skill; nx/turborepo for one package is overhead with no benefit. | Single-folder layout per the skill spec. |

---

# Part 2 — Research-Driven Defaults Menu (for the apps OSBuilder builds)

These are the **fallback defaults** the Architect role picks when web research is inconclusive or when speed-of-decision matters more than perfection. Per-build research at runtime can override any of these.

## Default Web App: Next.js + Tailwind + Drizzle + Postgres

| Technology | Version | Purpose | Why Default |
|------------|---------|---------|-------------|
| **Next.js** | 16.2.x (latest stable Apr 2026) | Full-stack React framework, App Router, Turbopack stable | Industry default; React team officially recommends it for new projects. Turbopack is now the default bundler. |
| **React** | 19.2 (bundled with Next 16) | UI library | Comes with Next 16; nothing to choose. |
| **TypeScript** | 5.6+ | Type safety | Default in `create-next-app`; non-negotiable in 2026. |
| **Tailwind CSS** | 4.x (CSS-first config via `@theme`) | Styling | First-class `create-next-app --tailwind` support; v4 is 5-100× faster than v3. |
| **Drizzle ORM** | 0.36+ | Postgres access, type-safe queries | Lighter than Prisma (~33KB vs ~800KB), faster cold starts on serverless, better Postgres-specific features. Prisma stays as the alternative for teams that need its mature migration tooling. |
| **PostgreSQL** | 18.3 (`postgres:18-alpine` in compose, pinned) | Multi-user database | Default per user constraint ("Postgres-via-compose for multi-user web apps"). |
| **pnpm** | 10.x | Package manager | Disk-efficient, fastest installs, monorepo-ready, 2026 default for new TypeScript projects. |
| **Docker Compose** | v2 (`compose.yaml`, not `docker-compose.yml`) | Local Postgres + app | Filename per 2026 Compose spec. Pin every image tag. |

**Scaffolder command (deterministic):**
```bash
pnpm create next-app@latest my-app --typescript --tailwind --app --src-dir --turbopack --import-alias "@/*"
```

**Confidence: HIGH** (Next.js 16 release notes, Tailwind v4 release notes, Drizzle docs all verified).

## Default AI Service: FastAPI + uv + Pydantic v2

| Technology | Version | Purpose | Why Default |
|------------|---------|---------|-------------|
| **FastAPI** | 0.136.x (pin narrow: `>=0.136.1,<0.137.0`) | HTTP API for AI/ML services | Gold standard in 2026 for Python AI services; async-first; auto-docs. Still 0.x semver — pin narrow. |
| **uv** | 0.5+ | Dependency + venv management | Replaces pip + virtualenv + pyenv with one tool, 10-100× faster. |
| **Python** | 3.12 (recommended baseline) or 3.13 | Runtime | FastAPI 0.136 requires 3.10+; 3.12 is the recommended production baseline (PEP 695 generics + perf). |
| **Pydantic** | v2.x | Request/response validation | FastAPI's native validation library. |
| **Uvicorn** | 0.30+ | ASGI server | FastAPI's recommended server; for production, use behind nginx or `uvicorn --workers N`. |
| **OpenTelemetry** | latest, opt-in via `--production-ready` flag | Observability | Three-line instrumentation via `opentelemetry-instrumentation-fastapi`. |

**Scaffolder approach:** FastAPI has no `create-fastapi-app`; OSBuilder uses `uv init` then drops a hand-built starter template from `assets/fastapi-starter/`. *This is the one place where "always use a deterministic scaffolder" needs nuance — the scaffolder is OSBuilder's own template-copy, treated as deterministic.*

**Confidence: HIGH** (FastAPI release notes verified; uv adoption verified across multiple 2026 sources).

## Default Desktop App: Tauri 2.x

| Technology | Version | Purpose | Why Default |
|------------|---------|---------|-------------|
| **Tauri** | 2.x (latest stable) | Cross-platform desktop framework | 96% smaller bundles, 50% less RAM than Electron; system-WebView-based; capability permissions are SOC2/HIPAA-friendly. 2026 default unless an Electron-only plugin is required. |
| **Rust** | 1.80+ | Tauri backend | Required for Tauri. Preflight installs via `rustup`. |
| **Vite + React/Svelte/Solid** | latest | Frontend layer | Tauri is framework-agnostic; default to Vite + React for consistency with web defaults. |

**Scaffolder command:**
```bash
pnpm create tauri-app@latest
```

**Anti-recommendation: do NOT default to Electron.** Use only when the user has named an Electron-specific dep (rare). *Confidence: HIGH (verified against Tauri docs and 2026 comparison articles).*

## Default CLI App: Python + Typer

| Technology | Version | Purpose | Why Default |
|------------|---------|---------|-------------|
| **Python** | 3.13 | Runtime | Same baseline as helper scripts. |
| **Typer** | 0.13+ | CLI framework | Type-hint-driven, minimal boilerplate, built on Click (so dropdown to Click is trivial if needed). |
| **Rich** | latest | Terminal output (tables, progress, colors) | Industry standard for friendly CLI output. |
| **uv** | 0.5+ | Packaging | Same as AI service. |
| **SQLite** | bundled with Python | Storage (single-user CLIs only) | Per user constraint: SQLite for single-user; Postgres for multi-user. |

**Scaffolder approach:** `uv init my-cli --package` → drop Typer skeleton from `assets/typer-starter/`.

**Alternative menu entry: Node.js + Commander** — only when the user's broader stack is already Node and there's no Python dependency. Use Commander (35M weekly downloads, 0 deps) over oclif (heavier, scaffolding-oriented) for v1; oclif is for multi-team CLI tool-suites.

**Confidence: HIGH** (Click/Typer comparison verified; SQLite vs Postgres recommendation matches user constraint).

## Default Hub Pattern (à la Professor): umbrella `CLAUDE.md` + sub-tools

When the user request is "build me a hub like Professor Hub for X" (a named pattern in PROJECT.md):

| Component | Stack | Rationale |
|-----------|-------|-----------|
| Hub root | Top-level `CLAUDE.md` routing table + `README.md` | Matches Professor Hub structure (verified against `../professor/`). |
| Sub-tool: backend service | FastAPI + workers/queues (RQ or Celery) + Postgres | Matches `gradehub` structure. |
| Sub-tool: web frontend | Next.js | Per default web stack. |
| Sub-tool: CLI | Python + Typer | Per default CLI stack. |

**Confidence: MEDIUM** (pattern inferred from PROJECT.md description of `../professor/`; should be re-verified when Architect role consults the actual repo at runtime).

## Stack Patterns by Variant

**If the app is a web app with multi-user persistence:**
- Next.js + Drizzle + Postgres-via-compose + pnpm + Tailwind
- Because: industry default, scales to thousands of users, deploy targets are well-trodden.

**If the app is an AI/ML service (model serving, RAG, agents):**
- FastAPI + uv + Pydantic v2 + (optional) Postgres or Redis
- Because: async-first, native to the ML/Python ecosystem, OpenTelemetry-instrumentable.

**If the app is desktop:**
- Tauri 2 + Vite + React + Rust backend
- Because: 96% smaller than Electron, security-first, native-feel.

**If the app is a single-user CLI:**
- Python + Typer + Rich + (optional) SQLite
- Because: zero infra, ships as a single `uv tool install` or pipx-style binary.

**If the app is a hub-of-tools (Professor pattern):**
- Top-level `CLAUDE.md` + sub-tool folders, each picking from the menu above
- Because: matches the proven Professor Hub structure.

**If the user explicitly requests `--production-ready`:**
- Add (as named phases, not default code): observability (OpenTelemetry + Sentry), automated migrations (Drizzle Kit / Alembic), healthcheck endpoints, secret manager (env-injected via Doppler / Infisical / 1Password CLI), rate limiting, backup strategy, single GitHub Actions deploy workflow.

## Version Compatibility Notes

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Next.js 16.x | React 19.2 (bundled), Node 20 LTS+ (24.15 recommended) | Async Request APIs are required (sync access removed in v16). |
| FastAPI 0.136 | Python ≥ 3.10 (3.12 recommended) | Pin narrow `>=0.136.1,<0.137.0` because FastAPI is still 0.x. |
| Tauri 2.x | Rust 1.80+, Node 20+ | Rust toolchain is preflight-installable via `rustup`. |
| Tailwind 4.x | Next.js 15+, Vite 5+ | CSS-first config; no `tailwind.config.js`. |
| Drizzle 0.36+ | TypeScript 5.0+, Node 20+ | Postgres driver: `postgres-js` recommended for serverless, `pg` for long-running. |
| pnpm 10 | Node 20+ | Lifecycle scripts off-by-default in v10 — note in scaffolder docs. |
| Postgres 18.3 | Docker Compose v2 | Pin tag `postgres:18-alpine`, never `postgres:latest`. |

## Sources

**Anthropic Skills (HIGH confidence):**
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills) — SKILL.md format, frontmatter, progressive disclosure
- [Agent Skills overview - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — filesystem architecture, on-demand loading
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — 500-line guideline (user override: 200), scripts/ vs references/
- [anthropics/skills repo (GitHub)](https://github.com/anthropics/skills) — reference SKILL.md examples, including skill-creator
- [Equipping agents for the real world with Agent Skills (Anthropic engineering)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — design rationale
- [Persistent state across context compaction (Claude Code issue #25999)](https://github.com/anthropics/claude-code/issues/25999) — state.md pattern discussion

**Runtime versions (HIGH confidence, verified April 2026):**
- [Node.js 24.15.0 LTS release notes (April 2026)](https://nodejs.org/en/blog/release/v24.15.0) — current LTS
- [Python 3.13.13 / 3.14.4 release announcement (April 2026)](https://blog.python.org/2026/04/python-3150a8-3144-31313/) — current stable maintenance + feature
- [Status of Python versions (devguide)](https://devguide.python.org/versions/) — release schedule

**Web stack (HIGH confidence):**
- [Next.js 16 release blog](https://nextjs.org/blog/next-16) — Turbopack default, async APIs, React 19.2
- [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16) — breaking changes
- [Tailwind CSS v4.0 release blog](https://tailwindcss.com/blog/tailwindcss-v4) — CSS-first config, perf
- [Tailwind + Next.js install guide](https://tailwindcss.com/docs/guides/nextjs) — `--tailwind` flag in `create-next-app`
- [Drizzle vs Prisma 2026 (makerkit)](https://makerkit.dev/blog/tutorials/drizzle-vs-prisma) — bundle size, edge runtime
- [Postgres Docker Hub official image](https://hub.docker.com/_/postgres) — version 18.3, alpine variant

**AI service stack (HIGH confidence):**
- [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) — 0.136.x, Python baseline
- [FastAPI 2026 setup guide (zestminds)](https://www.zestminds.com/blog/fastapi-requirements-setup-guide-2025/) — production pinning advice
- [uv documentation (Astral)](https://docs.astral.sh/uv/) — pip compatibility, performance

**Desktop (HIGH confidence):**
- [Tauri vs Electron 2026 comparison (rustify)](https://rustify.rs/articles/rust-tauri-vs-electron-2026) — 96% smaller, 50% less RAM
- [Tauri vs Electron performance (gethopp)](https://www.gethopp.app/blog/tauri-vs-electron) — benchmarks
- [Best Desktop App Frameworks 2026 (pkgpulse)](https://www.pkgpulse.com/blog/best-desktop-app-frameworks-2026) — recommendation matrix

**CLI tooling (HIGH confidence):**
- [Typer official docs](https://typer.tiangolo.com/) — built on Click, type-hint-driven
- [Click vs Typer 2026 (codecut)](https://codecut.ai/comparing-python-command-line-interface-tools-argparse-click-and-typer/) — recommendation rationale
- [Commander vs oclif (grizzlypeak)](https://www.grizzlypeaksoftware.com/library/cli-framework-comparison-commander-vs-yargs-vs-oclif-utxlf9v9) — Node CLI choice

**Cross-platform installer (HIGH for macOS/Linux, MEDIUM for Windows):**
- [GitHub CLI install (winget.run)](https://winget.run/pkg/GitHub/cli) — winget package ID
- [WinGet docs (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/package-manager/winget/) — built-in to Win10+/11
- [Scoop](https://scoop.sh/) — Homebrew-style for Windows, scriptable
- [Homebrew](https://brew.sh/) — macOS/Linux primary
- [OrbStack vs Colima](https://docs.orbstack.dev/compare/colima) — networking + reliability comparison
- [Docker Desktop alternatives 2026 (fsck.sh)](https://fsck.sh/en/blog/docker-desktop-alternatives-2025/) — landscape

**Package managers (HIGH confidence):**
- [pnpm vs npm vs yarn 2026 (DEV)](https://dev.to/_d7eb1c1703182e3ce1782/npm-vs-pnpm-vs-yarn-package-manager-showdown-2026-benchmarks-2c38) — benchmarks, monorepo
- [uv vs pip (Real Python)](https://realpython.com/uv-vs-pip/) — when to use which
- [Best Python package managers 2026 (scopir)](https://scopir.com/posts/best-python-package-managers-2026/) — recommendation

**Database choice (HIGH confidence):**
- [SQLite vs Postgres for solo founder 2026](https://abhishekchaudhary.com/blog/sqlite-vs-postgres-solo-founder) — single-user CLI guidance
- [PostgreSQL vs SQLite (DataCamp)](https://www.datacamp.com/blog/sqlite-vs-postgresql-detailed-comparison) — concurrency limits

**Bash portability (HIGH confidence):**
- [ShellCheck (GitHub)](https://github.com/koalaman/shellcheck) — portability linter
- [Cross-platform Node.js (awesome list)](https://github.com/bcoe/awesome-cross-platform-nodejs) — Node-specific shims (referenced as alternative)

---
*Stack research for: Claude Code skill (OSBuilder) + per-build defaults menu*
*Researched: 2026-04-29*
*Author: research subagent (gsd-new-project Phase 6)*
