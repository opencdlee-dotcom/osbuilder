# Phase 7: Additional playbooks - Research

**Researched:** 2026-05-01
**Domain:** Cross-stack scaffolding (FastAPI / Typer / Tauri 2 / hub-platform) + intake routing + parametrized E2E
**Confidence:** HIGH for external tool versions (verified against PyPI / npm / GitHub releases on 2026-05-01) and create-tauri-app CLI signature (verified by running `--help` locally); HIGH for OSBuilder codebase patterns (read directly); HIGH for professor/ structural inventory (read directly); MEDIUM for inference-algorithm choice (multiple valid approaches; recommendation given but not measured against real intake corpus).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Routing — intake `app_type` inference**

- **D-01:** Replace the hardcoded `app_type="web"` in `scripts/intake_handler.py:264` with keyword-scored inference across all 5 playbooks (web / ai-service / cli / desktop / hub-platform).
- **D-02:** When inference confidence is low or 2+ playbooks score similarly, fall back to a plain-English question via `references/question-bank.md` (e.g., "Sounds like an HTTP API or a desktop app — which fits?"). Never silently coin-flip; always preserve the "I don't know, you decide" option per IN-04.
- **D-03:** The TODO comment at `scripts/intake_handler.py:263-265` is the deletion target — the new inference function replaces the placeholder hardcode.

**Hub-platform shape (SC-04)**

- **D-04:** Hub-platform playbook produces a top-level `CLAUDE.md` routing table + N empty sub-tool subdirectories named from intake (e.g., `grader/`, `roster/`). Each sub-tool gets its own placeholder `CLAUDE.md`. User re-runs `/osbuilder` per sub-tool to fill them in a later session.
- **D-05:** Structural verification: file/dir layout must match `professor/` at the top level (same nesting depth, same routing-table format) — diff-checked against a vendored snapshot in tests, NOT a live filesystem dependency on `professor/`.
- **D-06:** Sub-tool count and names come from intake parsing (e.g., "build me a hub like Professor Hub for grading and rostering" → `grading/`, `rostering/`). If unresolvable, ask via question-bank.

**Desktop scaffolding (SC-03)**

- **D-07:** Desktop playbook uses `pnpm create tauri-app@latest <name> --template react-ts --manager pnpm --identifier <reverse-dns>` — non-interactive, pinned flags, mirroring the create-next-app pattern from Phase 3 web playbook.
- **D-08:** Tauri owns template drift (same risk model accepted for create-next-app). Pin `create-tauri-app` to a verified version in the playbook .md so version drift is visible in git diffs.
- **D-09:** Electron refusal stays at the intake refusal gate (already in `references/refuse-list.md`); desktop playbook documents the Tauri-not-Electron rationale inline per SC-03.

**AI-service scaffold contents (SC-01)**

- **D-10:** `assets/fastapi-starter/` ships: routed `/` (hello), `/health` (200 OK), automatic `/docs` from FastAPI, **plus a stub `/summarize` POST endpoint** that calls a placeholder `summarize(text)` function returning `{"summary": text[:200]}`.
- **D-11:** No real Claude API call in the starter — the stub function carries a comment pointing to where the user wires in a real LLM call.
- **D-12:** Pydantic v2 models for request/response on `/summarize` (`SummarizeRequest`, `SummarizeResponse`).

**CLI playbook scaffold (SC-02)**

- **D-13:** CLI playbook uses `uv init --app <name>` + post-scaffold writes for `pyproject.toml` Typer/Rich/SQLite deps. SQLite path is `~/.<app-name>/state.db`; `_pick_database` already routes non-web to SQLite so no change needed there.
- **D-14:** Starter command: `<app-name> --help` (Rich-formatted) and one example sub-command (`<app-name> ping`) that writes a row to SQLite and reads it back.

**Plan slicing**

- **D-15:** Phase 7 = **6 plans**:
  - `07-01` — Intake routing + inference (single source of truth before playbooks land)
  - `07-02` — AI-service playbook (`ai-service.md` + `assets/fastapi-starter/` + scaffold dispatch + tests)
  - `07-03` — CLI playbook (`cli.md` + post-scaffold writes + tests)
  - `07-04` — Desktop playbook (`desktop.md` + create-tauri-app dispatch + tests)
  - `07-05` — Hub-platform playbook (`hub-platform.md` + structural template + sub-tool stubs + tests)
  - `07-06` — Shared E2E harness (parametrized stranger-clone test across all 4 playbooks)
- **D-16:** Plans 07-02..07-05 are wave-parallelizable once 07-01 lands. 07-06 depends on all four.

**Verification (SC-05)**

- **D-17:** One parametrized E2E test file `scripts/tests/test_e2e_playbooks.py` runs the 5-step contract (intake → scaffold → install → boot → stop) parametrized over `[ai-service, cli, desktop, hub]`.
- **D-18:** Each parametrized case has a hard timeout (~30s scaffold + ~60s install + ~30s boot = ~2min per case, ~8min total).
- **D-19:** Manual stranger-clone UAT remains in `07-HUMAN-UAT.md` per Phase 6 precedent.

**Preflight extensions**

- **D-20:** Extend `scripts/preflight_check.py` with auto-install (single confirmation, same as Node/Docker) for: `cargo`/`rustc` via `curl https://sh.rustup.rs -sSf | sh -s -- -y`; `uv` via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **D-21:** Both installers respect the Phase 2 cross-platform contract — Windows uses the official PowerShell installers (`winget install astral-sh.uv`, `winget install -e --id Rustlang.Rustup`).

> **Research correction:** CONTEXT.md D-21 wrote `winget install Astral.UV`. The actual winget package ID is `astral-sh.uv` (lowercase, hyphenated namespace) — verified against the live winget-pkgs manifest at `manifests/a/astral-sh/uv/0.11.8/astral-sh.uv.installer.yaml`. Plans MUST use `astral-sh.uv` not `Astral.UV`. The Rustup ID `Rustlang.Rustup` in D-21 is correct.

**Refusal/scope guardrails**

- **D-22:** Migrate Electron refusal from `references/playbooks/web.md` to global `references/refuse-list.md` (currently scoped to web; now covers all builds). Hub-platform refuses inline-scaffolding all sub-tools at once (per D-04).
- **D-23:** No new refuse keywords for Phase 7 beyond Electron migration — existing kubernetes/microservices/helm/service-mesh keywords still apply universally.

### Claude's Discretion

- Inference scoring algorithm details (weighted keyword counts vs. simple bag-of-words) — planner picks; D-02's "ask if unsure" is the safety net.
- Exact wording of the playbook-fallback question in `question-bank.md` — should match the existing outcome-framed style (no jargon).
- Whether to vendor a `professor/` snapshot inside `.planning/codebase/snapshots/` or `assets/hub-template/` for D-05 diff-checking — planner picks based on what fits the test harness cleanest.
- Line ordering inside each new playbook .md — keep web.md's section order (What it produces / Scaffold command / Post-scaffold files / Refuse list / Stack pinned versions) for consistency.

### Deferred Ideas (OUT OF SCOPE)

- Real Claude API wiring in fastapi-starter (D-11 ships the stub).
- Sub-tool autoscaffolding for hub-platform builds (D-04 ships empty stubs).
- Additional language ecosystems (Go, Ruby, Java, Elixir).
- Deployment beyond private GitHub.
- Per-playbook --advanced overrides for stack components.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCAF-02 | OSBuilder maintains `references/playbooks/ai-service.md` covering FastAPI + uv + Pydantic v2 (with OSBuilder-supplied template `assets/fastapi-starter/`) | §1 (FastAPI/uv versions + commands), §2 (Pydantic v2 patterns), §10 (07-02 plan notes) |
| SCAF-03 | OSBuilder maintains `references/playbooks/cli.md` covering Python + Typer + Rich + SQLite for single-user CLIs | §3 (Typer 0.25.1 / Rich 15 / SQLite stdlib), §10 (07-03 plan notes) |
| SCAF-04 | OSBuilder maintains `references/playbooks/desktop.md` covering Tauri 2 (refuses Electron in v1) | §4 (create-tauri-app verified flags + prereqs), §10 (07-04 plan notes) |
| SCAF-05 | OSBuilder maintains `references/playbooks/hub-platform.md` for Professor-Hub-style umbrella workspaces (top-level CLAUDE.md routing table + sub-tool subdirectories) | §5 (live professor/ structural inventory), §10 (07-05 plan notes) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

CLAUDE.md is the OSBuilder Stack Research doc — it does not impose hard coding directives. Project-level constraints come from `.planning/STATE.md` and prior phase patterns:

- **Pure stdlib:** All `scripts/*.py` files use Python stdlib only (no third-party deps) — verified against `intake_handler.py`, `scaffold_dispatch.py`, `preflight_check.py`. Phase 7 MUST follow.
- **`atomic_write` pattern:** Every file write goes through `atomic_write` (tmp + `os.replace`). Duplicate the helper into each new module — DO NOT introduce a shared utils module (Phase 1 D-05 lock).
- **`_validate_project_name`:** Reuse from `scaffold_dispatch.py:148-155` for any new scaffold function (path traversal + shell-unsafe char rejection).
- **Friendly errors:** Each new playbook adds `dictionary.yaml` entries; raw stack traces / `ENOENT` / `EACCES` MUST be translated via `friendly_error.translate()`.
- **Lazy fixture import for not-yet-implemented modules:** Per the STATE.md "Test collection pattern" — never use `pytest.importorskip` at module top; use a `sw`-style fixture so individual test names always appear in `--collect-only`.
- **SKILL.md ≤ 200 lines (QUAL-01):** Playbooks load on-demand. New `references/playbooks/*.md` files MUST stay self-contained ≤ 80 lines each (web.md is 77).
- **`_real_run` capture pattern:** Any test that monkeypatches `subprocess.run` MUST capture `_real_run = subprocess.run` BEFORE the patch (recursion-safe pattern from Phase 4 STATE.md, evidenced in `test_gh_handoff.py:27`).
- **Argv-token script-path matching:** Predicates that classify subprocess calls match by argv token (`c.endswith("script.py")`) not loose `" ".join(cmd)` substring scan.

---

## Summary

Phase 7 adds 4 new playbooks to the existing web-only scaffold pipeline, plus replaces the hardcoded `app_type="web"` with a 5-way keyword-inference router that falls back to a plain-English question. The tools are well-documented and stable as of 2026-05-01:

- **FastAPI 0.136.1** + **uv 0.11.8** ships a `fastapi[standard]` extra that auto-installs `fastapi dev` (CLI command). `uv init --app` + `uv add 'fastapi[standard]'` + `uv run fastapi dev` is the canonical 3-step path. Pydantic v2.13.3 is a transitive dep, no separate add needed.
- **Typer 0.25.1** now declares `rich >= 13.8.0` as a HARD dependency (no longer optional) — installing typer brings rich automatically.
- **create-tauri-app 4.6.2** (current latest is 4.7.0 per GitHub release `create-tauri-app-js-v4.7.0` from 2026-01-06; npm registry shows 4.6.2 as published — pin to 4.6.2 since that is what `npx create-tauri-app@latest` resolves to today). All four CONTEXT-named flags are real: `--manager`, `--template`, `--identifier`, plus `-y` for non-interactive defaults and `--tauri-version 2` to lock the major.
- **Hub-platform** structure verified by reading `../professor/` directly: top-level `CLAUDE.md` routing-table + per-subtool subdirectories (e.g., `LabNoteBookGrader/`, `Exam grader/`) each with their own `CLAUDE.md`. AGENTS.md exists alongside CLAUDE.md but is optional.

**Primary recommendation:** Implement plan 07-01 (inference) first using a **weighted keyword-bag** algorithm (each playbook owns ~5-8 high-signal keywords, score = sum of matched weights, fall back to question if `top_score < 2.0` OR `top_score - 2nd_score < 1.0`). Plans 07-02..07-05 then run in parallel via the established Wave 1 model — each adds ONE scaffold function, ONE playbook .md, ONE friendly-error dictionary entry, and ONE Wave 0 test stub. 07-06 lands the parametrized E2E harness last.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 5-way `app_type` inference | `intake_handler.py` (Python module) | `references/question-bank.md` (fallback question) | `intake_handler.parse_paragraph` already owns paragraph→spec mapping; inference belongs there. Question-bank is data, not logic. |
| ai-service scaffold (FastAPI starter copy) | `scaffold_dispatch.py:scaffold_ai_service` | `assets/fastapi-starter/` (vendored template files) | `scaffold_dispatch` is the only scaffold dispatcher; new function follows `scaffold_web` shape exactly. |
| CLI scaffold (uv init + post-scaffold writes) | `scaffold_dispatch.py:scaffold_cli` | `assets/cli-starter/` (Typer + SQLite snippet templates) | Same reason. |
| Desktop scaffold (create-tauri-app subprocess) | `scaffold_dispatch.py:scaffold_desktop` | None — Tauri owns template drift | Mirrors `scaffold_web`'s create-next-app pattern. |
| Hub-platform scaffold (write CLAUDE.md + N stub dirs) | `scaffold_dispatch.py:scaffold_hub` | `assets/hub-template/CLAUDE.md.tmpl` + `subtool-CLAUDE.md.tmpl` | Hub is pure file-stamping; no external scaffolder exists. |
| Rust toolchain detection + auto-install | `preflight_check.py` (extend `REQUIRED_TOOLS_DESKTOP` slice) | `bootstrap.sh` / `bootstrap.ps1` are unchanged (those are for Python only) | Preflight already owns multi-tool detection + atomic install-log + rollback. |
| uv detection + auto-install | `preflight_check.py` (extend table) | None | Same. |
| Friendly error translation for new tools | `references/friendly-errors/dictionary.yaml` | `friendly_error.translate()` (read-only consumer) | Dictionary is data; translator is generic. |
| Parametrized E2E harness | `scripts/tests/test_e2e_playbooks.py` (new file) | `scripts/tests/conftest.py` (extend with `playbook_case` fixture if needed) | Mirrors Phase 6's per-feature test files. |
| Manual UAT contract | `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` | n/a | Mirrors `06-HUMAN-UAT.md` exactly. |

---

## Standard Stack

### Core (per playbook)

| Playbook | Library | Version | Purpose | Why Standard | Source |
|----------|---------|---------|---------|--------------|--------|
| ai-service | fastapi | 0.136.1 | HTTP API framework | tiangolo/fastapi is canonical; `[standard]` extra ships `fastapi dev` CLI runner | [VERIFIED: PyPI 2026-04-23] |
| ai-service | pydantic | 2.13.3 | Request/response models | Transitive dep of fastapi[standard]; v2 is the locked decision per D-12 | [VERIFIED: PyPI 2026-04-20] |
| ai-service | uvicorn | 0.46.0 | ASGI server | Transitive dep of fastapi[standard]; powers `fastapi dev` | [VERIFIED: PyPI 2026-04 latest] |
| ai-service | uv | 0.11.8 | Python project + package manager | Astral's all-in-one replacement for pip+pipx+poetry+venv | [VERIFIED: PyPI 2026-04-27] |
| cli | typer | 0.25.1 | CLI framework (Click + type-hint sugar) | `fastapi/typer` is canonical for type-hint CLIs; ships rich-formatted help | [VERIFIED: PyPI 2026-04-30] |
| cli | rich | 15.0.0 | Terminal styling + tables | NOW a hard dep of typer ≥0.25 (was optional pre-0.17); installed automatically | [VERIFIED: PyPI 2026-04-12 + typer pyproject.toml `rich >=13.8.0`] |
| cli | uv | 0.11.8 | (same as ai-service) | (same) | (same) |
| cli | sqlite3 | stdlib | Embedded persistence | Python stdlib; zero deps; D-13 locks `~/.<app-name>/state.db` | [VERIFIED: Python 3.13 stdlib] |
| desktop | create-tauri-app | 4.6.2 | Scaffolder | Official Tauri scaffolder; supports non-interactive flags (verified via `--help`) | [VERIFIED: npm 2026-05-01 (latest 4.7.0 per GH releases 2026-01-06; pinning to 4.6.2 = `pnpm create tauri-app@latest` resolved value)] |
| desktop | tauri (Rust crate) | 2.x | Runtime | `--tauri-version 2` flag pins to v2; create-tauri-app installs the matching CLI | [VERIFIED: tauri.app v2 docs] |
| desktop | @tauri-apps/cli | 2.11.0 | Tauri JS dev/build CLI | Installed by create-tauri-app into the scaffolded project | [VERIFIED: npm 2026-05-01] |
| desktop | rustup-toolchain | stable | Rust compiler | Required by Tauri build; preflight auto-installs via sh.rustup.rs | [VERIFIED: rustup.rs] |
| hub-platform | none | n/a | Pure file-stamping | Hub is structural — no external scaffolder | [VERIFIED: codebase] |

### Supporting (referenced by playbooks but not directly installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | (auto via fastapi[standard]) | Form data parsing | Implicit; only if user adds form endpoints |
| starlette | (auto via fastapi) | ASGI framework | Implicit; FastAPI is built on it |
| webkit2gtk-4.1 (system) | (Ubuntu 22.04+) | WebView for Tauri Linux | Required only for Linux desktop builds |
| MSVC Build Tools (system) | latest | C++ compiler for Rust on Windows | Required only for Windows desktop builds |
| Xcode CLT (system) | latest | Tools for Rust on macOS | Required only for macOS desktop builds |

### Alternatives Considered

| Instead of | Could Use | Tradeoff | Decision |
|------------|-----------|----------|----------|
| FastAPI | Litestar / Flask / Django REST | Litestar is faster but less canonical; Flask is older without async-first; DRF is heavyweight | FastAPI wins on docs, type-hints, ecosystem; D-10 locked |
| Typer | Click directly / argparse | Click is more bare; argparse is stdlib but ugly help; `rich-click` is a Click variant | Typer wins on type-hint ergonomics + free Rich help; D-13 locked |
| Tauri 2 | Electron | Electron 40-100% larger binaries, 2x RAM. v1 OSBuilder explicitly refuses Electron | Tauri locked; Electron refused via D-22 |
| uv | poetry / pdm / pip+venv | poetry is slower (2-10x); pdm is niche; pip+venv lacks lockfile by default | uv wins on speed + single-binary install + fastapi-tutorial uses it; D-13 locked |
| sqlite3 stdlib | sqlite-utils / sqlmodel / aiosqlite | sqlite-utils is a CLI tool for ad-hoc; SQLModel pulls Pydantic+SQLAlchemy (out of scope for v1 starter); aiosqlite is async (overkill for sync CLI) | stdlib `sqlite3` is zero-dep + sufficient for the `ping` example |
| Hub vendored snapshot | Live `../professor/` filesystem dependency | Live dependency couples test runs to the maintainer's machine layout — fails on stranger checkout | Vendor at `assets/hub-template/professor-snapshot/` (recommended location below) |

**Installation (per playbook, after preflight has installed Rust + uv):**

```bash
# ai-service
uv init --app <project-name>
cd <project-name>
uv add 'fastapi[standard]'
# (optional, for /summarize stub) — pydantic is transitive but pinning shows intent:
# uv add pydantic

# cli
uv init --app <project-name>
cd <project-name>
uv add typer  # rich >=13.8.0 is automatic

# desktop (Rust must already be installed via preflight)
pnpm create tauri-app@latest <project-name> \
  --manager pnpm \
  --template react-ts \
  --identifier <reverse-dns-id> \
  --tauri-version 2 \
  -y

# hub-platform — no external scaffolder; OSBuilder writes files directly
```

**Version verification log (pre-locked into playbook .md):**

```bash
$ npm view create-tauri-app version
4.6.2

$ npm view @tauri-apps/cli version
2.11.0

$ curl -s https://pypi.org/pypi/fastapi/json | jq -r '.info.version'
0.136.1   # released 2026-04-23

$ curl -s https://pypi.org/pypi/uv/json | jq -r '.info.version'
0.11.8    # released 2026-04-27

$ curl -s https://pypi.org/pypi/typer/json | jq -r '.info.version'
0.25.1    # released 2026-04-30

$ curl -s https://pypi.org/pypi/rich/json | jq -r '.info.version'
15.0.0    # released 2026-04-12

$ curl -s https://pypi.org/pypi/pydantic/json | jq -r '.info.version'
2.13.3    # released 2026-04-20

$ curl -s https://pypi.org/pypi/uvicorn/json | jq -r '.info.version'
0.46.0
```

---

## Architecture Patterns

### System Architecture Diagram

```
                  ┌──────────────────────────────────────────┐
                  │  User: "I want a CLI to organize photos" │
                  └─────────────────┬────────────────────────┘
                                    │
                                    ▼
        ┌──────────────────────────────────────────────────────────┐
        │ scripts/intake_handler.py                                 │
        │   parse_paragraph(text)                                   │
        │     → infer_app_type(text)  ◄── NEW (07-01)              │
        │       ├── score=keyword_bag(text, PLAYBOOK_KEYWORDS)      │
        │       ├── if confident → return "cli"                    │
        │       └── else → ask question-bank.md "What kind…?"      │
        │     → derived_spec.md (with app_type=cli)                 │
        └─────────────────┬────────────────────────────────────────┘
                          │
                          ▼  (state.md: app_type=cli, playbook=cli)
        ┌──────────────────────────────────────────────────────────┐
        │ scripts/scaffold_dispatch.py                              │
        │   --playbook cli  →  scaffold_cli(name, root)            │
        │       │                                                   │
        │       ├── _validate_project_name(name)                   │
        │       ├── ensure_uv()  ◄── NEW (or guarded by preflight) │
        │       ├── subprocess.run(["uv", "init", "--app", name])  │
        │       ├── atomic_write(pyproject.toml additions)         │
        │       ├── atomic_write(src/<name>/__main__.py from tmpl) │
        │       ├── _write_dockerfile (skipped — CLIs don't ship)  │
        │       └── _write_ci_workflow(stack_family="python")      │
        └─────────────────┬────────────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────────────────────────┐
        │ Per-playbook 5-step contract (E2E test 07-06):            │
        │   1. intake → derived_spec.md (app_type correct)         │
        │   2. scaffold → project_dir on disk                       │
        │   3. install → uv sync / pnpm install (timeout 60s)      │
        │   4. boot → uv run fastapi dev / pnpm tauri dev / ...   │
        │   5. stop → SIGTERM, verify exit                         │
        └──────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────────────────────────┐
        │ scripts/preflight_check.py (extended for desktop+ai)     │
        │   detect()/plan() now scopes by playbook (D-20):         │
        │     base tools: node, python3, git, gh, docker           │
        │     +cli tools: uv  ◄── NEW                              │
        │     +ai tools:  uv  ◄── NEW                              │
        │     +desktop:   uv (no), rustup ◄── NEW                  │
        │   Auto-install via:                                       │
        │     curl -LsSf https://astral.sh/uv/install.sh | sh       │
        │     curl --proto '=https' https://sh.rustup.rs -sSf | sh  │
        │   Windows: winget install astral-sh.uv                    │
        │            winget install -e --id Rustlang.Rustup         │
        └──────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (after Phase 7 lands)

```
OSBuilder/
├── references/
│   ├── playbooks/
│   │   ├── web.md           # Phase 3 (unchanged)
│   │   ├── ai-service.md    # NEW — 07-02
│   │   ├── cli.md           # NEW — 07-03
│   │   ├── desktop.md       # NEW — 07-04
│   │   └── hub-platform.md  # NEW — 07-05
│   ├── question-bank.md     # +1 question (playbook fallback) — 07-01
│   ├── refuse-list.md       # +Electron migration (D-22) — 07-04
│   ├── stack-menu.md        # +4 default tables (one per new playbook)
│   └── friendly-errors/
│       └── dictionary.yaml  # +5 entries: tauri-not-installed, uv-not-installed,
│                            #              cargo-not-installed, fastapi-not-installed,
│                            #              create-tauri-app-failed
├── assets/
│   ├── fastapi-starter/         # NEW — 07-02
│   │   ├── main.py              # /, /health, /summarize stub
│   │   └── pyproject.snippet.toml  # deps to add post-uv-init
│   ├── cli-starter/             # NEW — 07-03
│   │   ├── __main__.py.tmpl     # Typer app + ping subcommand
│   │   └── pyproject.snippet.toml
│   ├── hub-template/            # NEW — 07-05
│   │   ├── CLAUDE.md.tmpl       # routing table {{subtools}} placeholder
│   │   ├── subtool-CLAUDE.md.tmpl  # per-subtool placeholder
│   │   └── professor-snapshot/  # vendored diff target (~10 files)
│   │       ├── CLAUDE.md
│   │       ├── AGENTS.md
│   │       └── ... (top-level only, no .git, no .planning, no .venv)
│   └── ci-workflows/
│       └── tauri.yml.tmpl       # NEW — Rust+Node combined CI (07-04)
├── scripts/
│   ├── intake_handler.py        # MODIFIED: + infer_app_type, PLAYBOOK_KEYWORDS const
│   ├── scaffold_dispatch.py     # MODIFIED: + scaffold_ai_service / _cli / _desktop / _hub
│   ├── preflight_check.py       # MODIFIED: + uv + rustup detection + install actions
│   └── tests/
│       ├── test_intake.py       # MODIFIED: +5 inference test cases (07-01)
│       ├── test_scaffold_dispatch.py  # MODIFIED: + per-playbook scaffold tests
│       ├── test_preflight.py    # MODIFIED: +rust/uv detect+plan tests
│       └── test_e2e_playbooks.py  # NEW — parametrized [ai-service, cli, desktop, hub] (07-06)
└── .planning/phases/07-additional-playbooks/
    ├── 07-CONTEXT.md       (exists)
    ├── 07-RESEARCH.md      (this file)
    ├── 07-01-PLAN.md       through 07-06-PLAN.md
    ├── 07-VERIFICATION.md
    ├── 07-VALIDATION.md
    └── 07-HUMAN-UAT.md     (mirrors 06-HUMAN-UAT.md)
```

### Pattern 1: Subprocess scaffold dispatch (mirror `scaffold_web`)

**What:** Each new `scaffold_X` function follows the established 4-step shape from `scaffold_web` (lines 184-274 of `scaffold_dispatch.py`):

1. `_validate_project_name(name)` — security gate.
2. `ensure_TOOL()` — install missing scaffold dep if needed (mirrors `ensure_pnpm`).
3. `subprocess.run([scaffolder_cmd...], cwd=project_root, check=True, shell=False, capture_output=True, text=True)` wrapped in try/except for `FileNotFoundError`/`OSError` (translates via `friendly_error`) and `subprocess.CalledProcessError`.
4. Post-scaffold `atomic_write` calls for the 1-3 files OSBuilder owns (template files, env example, etc.).

**When to use:** All four new scaffold functions. NOT for `scaffold_hub` — that's pure file-stamping (Pattern 4).

**Example (canonical structure for `scaffold_ai_service`):**

```python
# Source: scripts/scaffold_dispatch.py:scaffold_web (verified 2026-05-01)
_FASTAPI_STARTER = ASSETS / "fastapi-starter"

def scaffold_ai_service(project_name: str, project_root: Path) -> Path:
    _validate_project_name(project_name)
    ensure_uv()  # NEW helper — mirrors ensure_pnpm
    cmd = ["uv", "init", "--app", project_name]
    try:
        subprocess.run(cmd, cwd=str(project_root), check=True,
                       capture_output=True, text=True, shell=False)
    except (FileNotFoundError, OSError) as e:
        _emit_friendly("uv-not-installed", e)
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        _emit_friendly_from_stderr(e)
        raise SystemExit(1)
    project_dir = project_root / project_name
    # Post-scaffold writes: copy starter main.py + add fastapi[standard] dep
    atomic_write(project_dir / "main.py",
                 (_FASTAPI_STARTER / "main.py").read_text(encoding="utf-8"))
    subprocess.run(["uv", "add", "fastapi[standard]"], cwd=str(project_dir),
                   shell=False, check=False)
    _write_dockerfile(project_dir, stack_family="python-uv")
    _write_ci_workflow(project_dir, stack_family="python")
    return project_dir
```

### Pattern 2: Keyword-bag inference with confidence threshold

**What:** A pure function `infer_app_type(text: str) -> tuple[str, float]` that returns `(playbook_name, confidence_score)`. The caller in `parse_paragraph` checks confidence and either commits or asks the question-bank fallback.

**When to use:** Only inside `parse_paragraph`. `parse_structured` already respects an explicit `app_type` key — leave it untouched.

**Algorithm (recommended — Claude's Discretion per CONTEXT.md):**

```python
# PLAYBOOK_KEYWORDS: weighted keyword bag per playbook.
# Weights are integers — higher = stronger signal.
# Source-of-truth lives here in intake_handler.py; tests pin specific
# weights so changes surface in code review.
PLAYBOOK_KEYWORDS = {
    "web": {
        "website": 3, "web app": 3, "browser": 2, "homepage": 3,
        "landing page": 3, "frontend": 2, "html": 1, "todo app": 2,
        "blog": 2, "marketplace": 2, "saas": 2,
    },
    "ai-service": {
        "api": 2, "http api": 3, "endpoint": 2, "rest": 2,
        "summarize": 3, "llm": 3, "openai": 2, "anthropic": 2,
        "fastapi": 3, "service": 1, "microservice": 0,  # 0 because refuse-list catches it
        "embeddings": 2, "rag": 3, "agent": 2,
    },
    "cli": {
        "cli": 3, "command line": 3, "command-line": 3, "terminal": 2,
        "script": 2, "tool": 1, "automation": 2, "organize": 2,
        "batch": 2, "convert": 2, "rename": 2,
    },
    "desktop": {
        "desktop app": 3, "desktop": 2, "tray icon": 3, "system tray": 3,
        "native window": 3, "windows app": 2, "macos app": 2, "linux app": 2,
        "tauri": 3, "electron": 0,  # 0 because refuse-list catches it
        "menu bar": 3, "offline app": 2,
    },
    "hub-platform": {
        "hub": 3, "platform": 2, "umbrella": 3, "workspace": 2,
        "professor hub": 4, "like professor": 4, "multiple tools": 3,
        "monorepo": 2, "suite": 2, "router": 1,
    },
}

def infer_app_type(text: str) -> tuple[str, float]:
    """Return (best_playbook, top_score) given a paragraph.

    Pure function: no I/O, deterministic.

    Confidence rules (D-02):
    - Caller treats top_score < 2.0 as "low confidence — ask question"
    - Caller treats (top_score - second_score) < 1.0 as "tied — ask question"
    """
    lower = text.lower()
    scores: dict[str, float] = {pb: 0.0 for pb in PLAYBOOK_KEYWORDS}
    for pb, kws in PLAYBOOK_KEYWORDS.items():
        for kw, w in kws.items():
            # Use word-boundary match for single-word keywords; substring for multi-word
            if " " in kw or "-" in kw:
                if kw in lower:
                    scores[pb] += w
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                    scores[pb] += w
    best = max(scores, key=scores.get)
    return best, scores[best]


def _is_low_confidence(scores: dict[str, float]) -> bool:
    """Helper for parse_paragraph: True if no clear winner."""
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[0] < 2.0:
        return True
    if sorted_scores[0] - sorted_scores[1] < 1.0:
        return True
    return False
```

**Test coverage required:**
- 5 positive cases (one per playbook) where score is decisive.
- 2 ambiguous cases that should trigger question-bank fallback.
- 1 empty/garbage paragraph → fallback.
- 1 paragraph that hits a refuse-keyword (microservices) — refuse-list takes precedence over inference.

### Pattern 3: Hub-platform structural diff against vendored snapshot (D-05)

**What:** A test that walks the vendored `assets/hub-template/professor-snapshot/` directory tree and asserts that `scaffold_hub(name, root)` produces a tree with the same nesting depth (1 level of subdirs) and same file kinds (top-level CLAUDE.md + per-subtool CLAUDE.md).

**When to use:** Only in `test_scaffold_dispatch.py::test_hub_matches_professor_structure`. Real `professor/` is NEVER read at test time.

**Example (test stub for Wave 0 / Wave 1 GREEN):**

```python
# scripts/tests/test_scaffold_dispatch.py
SNAPSHOT = REPO_ROOT / "assets" / "hub-template" / "professor-snapshot"

def _structural_signature(root: Path) -> set[tuple[str, str]]:
    """Return {(relpath, kind), ...} where kind ∈ {'dir', 'file'}.
    Walks one level deep only — top level + immediate subdirs (each treated as opaque).
    """
    sig = set()
    for entry in root.iterdir():
        if entry.name.startswith(".") or entry.name == "node_modules":
            continue
        if entry.is_dir():
            sig.add((entry.name, "dir"))
            # If subdir contains CLAUDE.md, that's the per-subtool routing pattern
            if (entry / "CLAUDE.md").exists():
                sig.add((f"{entry.name}/CLAUDE.md", "file"))
        elif entry.is_file():
            sig.add((entry.name, "file"))
    return sig

def test_hub_matches_professor_structure(tmp_project_root):
    snapshot_sig = _structural_signature(SNAPSHOT)
    # Build a hub with the same subtool names as the snapshot
    subtools = sorted(name for name, kind in snapshot_sig if kind == "dir")
    project_dir = scaffold_hub(
        "test-hub", tmp_project_root,
        subtools=subtools,
    )
    built_sig = _structural_signature(project_dir)
    # Top-level CLAUDE.md must exist in both
    assert ("CLAUDE.md", "file") in built_sig
    # Every subdir from snapshot must exist as a subdir in built
    snapshot_dirs = {n for n, k in snapshot_sig if k == "dir"}
    built_dirs = {n for n, k in built_sig if k == "dir"}
    assert snapshot_dirs.issubset(built_dirs), \
        f"Missing subtool dirs: {snapshot_dirs - built_dirs}"
    # Every subdir must contain its own CLAUDE.md
    for sub in snapshot_dirs:
        assert (project_dir / sub / "CLAUDE.md").exists()
```

### Pattern 4: Pure file-stamping for hub-platform (no subprocess)

`scaffold_hub` is the ODD ONE OUT — it does NOT shell out to a scaffolder. It writes files directly:

```python
def scaffold_hub(project_name: str, project_root: Path, *, subtools: list[str]) -> Path:
    _validate_project_name(project_name)
    for sub in subtools:
        _validate_project_name(sub)  # subtool names go on disk too
    project_dir = project_root / project_name
    project_dir.mkdir(parents=True, exist_ok=False)
    # Top-level CLAUDE.md — substitute {{routing_table}} with N rows
    template = (ASSETS / "hub-template" / "CLAUDE.md.tmpl").read_text(encoding="utf-8")
    rows = "\n".join(
        f"| `{s}/` | TODO — describe {s} | n/a |" for s in subtools
    )
    rendered = template.replace("{{routing_table}}", rows).replace(
        "{{project_name}}", project_name
    )
    atomic_write(project_dir / "CLAUDE.md", rendered)
    # Per-subtool placeholder dirs + CLAUDE.md
    sub_template = (ASSETS / "hub-template" / "subtool-CLAUDE.md.tmpl").read_text(encoding="utf-8")
    for s in subtools:
        atomic_write(project_dir / s / "CLAUDE.md",
                     sub_template.replace("{{subtool}}", s))
    return project_dir
```

### Anti-Patterns to Avoid

- **Hand-writing `pyproject.toml` / `Cargo.toml` / `package.json`:** Rule from PROJECT.md "Out of Scope" — every playbook MUST use the upstream scaffolder + post-scaffold writes only. `uv init` writes pyproject.toml; we add deps via `uv add`. `create-tauri-app` writes Cargo.toml; we leave it alone.
- **Asking 5+ questions during inference:** The plain-English fallback (per D-02) asks ONE clarifying question with an "I don't know, you decide" branch. Multi-turn dialog goes against the common-person UX principle (UX-04 + IN-04).
- **Sharing scaffold helper code via a new utils module:** STATE.md "Recursion-safe monkeypatch (added 04-06)" + the established D-05 dup-pattern locks the rule: `atomic_write` and `_validate_project_name` MUST be duplicated, NOT imported from a shared module. Phase 7 follows.
- **Live `../professor/` filesystem dep in tests:** Snapshot at `assets/hub-template/professor-snapshot/` per D-05. Even on the maintainer's machine the test reads the snapshot, never the real path.
- **Pulling Pydantic v1 patterns:** `from pydantic import BaseModel` works on v2; v1 features like `@validator` (replaced by `@field_validator`) and `class Config` (replaced by `model_config = ConfigDict(...)`) are deprecated. Stub MUST use v2-native syntax.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FastAPI app skeleton | Hand-written `main.py` with manual ASGI mounting | `assets/fastapi-starter/main.py` (vendored, tested) | Tiangolo's pattern is one-import; deviation invites hydration bugs |
| FastAPI dev server | `uv run uvicorn main:app --reload` | `uv run fastapi dev` | `fastapi dev` adds nicer banner + auto-port-find + identical reload semantics; preferred per official docs |
| Tauri scaffold | Bespoke Vite+React+Cargo skeleton | `pnpm create tauri-app@latest ... --tauri-version 2 -y` | Tauri team owns template currency; rolling our own = stale Cargo.toml + missed v2 breaking changes |
| Typer help formatting | Manual ANSI escape codes / argparse formatter | Typer's built-in Rich integration (since 0.17 lazy, hard-dep since `rich >=13.8.0` in 0.25) | Typer auto-detects Rich; no config needed |
| SQLite path resolution | Hardcoded `./state.db` | `Path.home() / f".{app_name}" / "state.db"` (D-13) | XDG-friendly, doesn't pollute cwd, avoids permission issues in CI |
| Hub routing table | LLM-generated CLAUDE.md per build | Template-stamped from `assets/hub-template/CLAUDE.md.tmpl` with `{{routing_table}}` substitution | Determinism + idempotency requirement of D-04 |
| Rust toolchain install | Custom rustup script | `curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf \| sh -s -- -y` | Official; security-reviewed; `-y` makes non-interactive |
| uv install | Custom pip install | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | Official; faster than pip-installing uv |
| Cross-platform process spawning for tests | Manual subprocess management | `subprocess.run(..., timeout=N)` with try/except `subprocess.TimeoutExpired` | Stdlib; ENV already has timeout=5 precedent in `preflight_check._probe_version` |

**Key insight:** Phase 7 is mostly **plumbing existing tools together**. The only NEW assets are: 4 playbook .md docs (~50-80 lines each), 2 vendored starter dirs (`fastapi-starter/`, `cli-starter/`), 1 hub template tree, and 1 CI workflow template. All scripted logic is "copy `scaffold_web` shape, swap subprocess command."

## Runtime State Inventory

> Phase 7 is **purely additive** — no rename, refactor, or migration. This section is included for completeness but every category is "None — phase is greenfield additive."

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — phase only adds new files; no record/key/collection changes | none |
| Live service config | None — no external services touched (no n8n, Datadog, etc.) | none |
| OS-registered state | None — no Task Scheduler / launchd / systemd registrations created | none |
| Secrets/env vars | None new. The fastapi-starter `/summarize` stub is API-key-FREE per D-11 — comment-only pointer to `ANTHROPIC_API_KEY` for the user to wire later | none |
| Build artifacts | None — phase doesn't rename any installed-package egg-info / Cargo target | none |

**One adjacent note:** D-22 migrates the **Electron refusal copy** from `references/playbooks/web.md` to `references/refuse-list.md`. This is not runtime state — it's a **doc move**. The `REFUSE_KEYWORDS` tuple in `intake_handler.py:57` is unchanged (Electron is not currently a keyword and won't become one in Phase 7 per D-23; the refusal triggers via the playbook .md text content, not a hard-coded keyword). Plan 07-04 owns the migration.

---

## Common Pitfalls

### Pitfall 1: `pnpm create tauri-app` flag passing differs from npm

**What goes wrong:** `pnpm create tauri-app@latest <name> --template react-ts` — pnpm forwards `--template` to the scaffolder cleanly. **But** `npm create tauri-app@latest <name> -- --template react-ts` requires the `--` separator. CONTEXT.md D-07 specifies pnpm; if a user has only npm installed (preflight didn't auto-install pnpm), the same command fails confusingly.

**Why it happens:** npm's create-* dispatcher swallows flags before `--`; pnpm doesn't. This is documented in pnpm's CLI semantics but not on the Tauri docs page.

**How to avoid:** `scaffold_desktop` MUST call `ensure_pnpm()` (already exists, see line 161-168 of `scaffold_dispatch.py`) BEFORE invoking `create-tauri-app`. Same pattern as `scaffold_web`. If the user is on npm-only, pnpm gets installed first. **NEVER fall back to npm with `--`** — the install process for `@tauri-apps/cli` deviates and tests break.

**Warning signs:** Test failure with `error: unknown flag: --template`.

### Pitfall 2: `fastapi[standard]` extra is what installs `fastapi dev`

**What goes wrong:** `uv add fastapi` installs FastAPI but does NOT install the `fastapi` CLI command (the `fastapi dev` runner). Running `uv run fastapi dev` returns "command not found."

**Why it happens:** `fastapi-cli` is a separate optional package, included only via the `[standard]` extra: `fastapi[standard]` pulls in `fastapi-cli`, `httptools`, `uvicorn[standard]`, `email-validator`, etc.

**How to avoid:** ALWAYS write `uv add 'fastapi[standard]'` (single quotes prevent shell glob misinterpretation). Test the boot step in 07-06 by running `uv run fastapi dev --port <ephemeral>` and assert HTTP 200 on `/health`.

**Warning signs:** `uv run fastapi dev` says "command not found" or "module not found"; `/docs` returns 404.

### Pitfall 3: Rust toolchain on Windows requires MSVC default host

**What goes wrong:** A user runs `winget install Rustlang.Rustup`, then `pnpm tauri dev` fails with linker errors about missing `link.exe`.

**Why it happens:** Default rustup-init on Windows asks the user to choose a host triple (gnu vs msvc). When run via `winget` non-interactively, it picks `gnu` by default on some platforms — but Tauri requires `msvc` to link with the Microsoft C++ Build Tools.

**How to avoid:** After install, run `rustup default stable-msvc` as part of the auto-install flow on Windows. Document in `references/preflight/windows.md`. The Linux/macOS `sh.rustup.rs` path is not affected — it auto-picks the right toolchain.

**Warning signs:** "linker `link.exe` not found" / "error: Microsoft Visual C++ 14.0 or greater is required."

### Pitfall 4: Pydantic v2 imports look the same but `@validator` is gone

**What goes wrong:** A user copies a v1 example into the fastapi-starter (or AI helps them) and uses `@validator("field")`. v2 ignores the decorator silently — validation never runs.

**Why it happens:** v2 renamed it `@field_validator` (and `@root_validator` → `@model_validator`). v1 decorators are not raised; pydantic v2 silently no-ops them under the v1-compatibility shim that was removed in 2.x.

**How to avoid:** The `assets/fastapi-starter/main.py` MUST use v2-native syntax: `from pydantic import BaseModel, Field, field_validator` and `model_config = ConfigDict(...)` instead of `class Config`. Add a comment block citing `https://docs.pydantic.dev/latest/migration/`. Test that the model serialize/deserialize round-trips.

**Warning signs:** Validation errors don't fire on bad input; the field accepts anything.

### Pitfall 5: Typer `app = typer.Typer()` requires no `--rich-help-panel` but Rich must be importable

**What goes wrong:** A user installs typer in a minimal env and the help output has no colors. They assume Typer is broken.

**Why it happens:** Pre-0.17 typer made Rich an optional extra (`typer[all]`); 0.17+ made it lazy-loaded; 0.25.1 (current) hard-pinned `rich >=13.8.0` in `dependencies`. `uv add typer` therefore installs rich automatically — the pre-0.17 confusion is a stale internet artifact.

**How to avoid:** Pin `typer >=0.25.1` in `pyproject.toml` snippet. Tests assert that `uv pip list` shows both `typer` and `rich` after `uv sync`. Document in `cli.md` that no separate `rich` add is needed.

**Warning signs:** "Rich is not installed" stderr from typer; help output is plain ASCII.

### Pitfall 6: `uv init --app` writes a `requires-python = ">=3.X"` based on the local Python

**What goes wrong:** uv writes `requires-python = ">=3.13"` (or whatever the local active Python is) in pyproject.toml. A stranger cloning on Python 3.12 can't `uv sync`.

**Why it happens:** uv reads `python --version` (or `.python-version`) when initializing. Phase 1 preflight installs 3.13 — so OSBuilder builds always pin to 3.13. That's fine for OSBuilder — but the runbook clone-and-run gate on a stranger's machine relies on the stranger ALSO having 3.13.

**How to avoid:** Document in `runbook_writer` README: "Requires Python 3.13+" surfaces explicitly. Phase 6's runbook template already has a Requirements section — extend it for the ai-service / cli playbooks. The uv error message on version mismatch IS friendly already (no `friendly_error` translation needed).

**Warning signs:** Stranger gets `python: required >=3.13.0` from uv on first sync.

### Pitfall 7: `create-tauri-app` `--identifier` MUST be reverse-DNS

**What goes wrong:** A user (or OSBuilder building from intake) passes `--identifier my-app` and create-tauri-app silently accepts it. Later, `tauri build` fails with `Bundle identifier my-app is not valid` because macOS code-signing requires reverse-DNS (`com.example.myapp`).

**Why it happens:** create-tauri-app validates identifier loosely; Tauri's bundler is stricter.

**How to avoid:** `scaffold_desktop` MUST construct the identifier deterministically: `"com.osbuilder." + project_name.replace("-", "")`. Document the convention in `desktop.md`. Add a test that `_build_identifier("my-cool-app") == "com.osbuilder.mycoolapp"`.

**Warning signs:** Late `tauri build` failure (not caught at scaffold time).

### Pitfall 8: Subprocess `timeout` on long installs vs scaffold

**What goes wrong:** The E2E parametrized test (07-06) sets a 60-second timeout on `uv sync` / `pnpm install`. On slow networks (CI cold-starts), `pnpm install` for the Tauri scaffold (downloads ~200MB of node_modules + Rust crate fetches) routinely exceeds 60s.

**Why it happens:** Tauri's first build pulls full Rust dep graph (regex, serde, tokio, tauri-runtime, ~200 crates). With cold CI cargo cache, this is slow.

**How to avoid:** D-18 already specifies ~60s install timeout — keep that for ai-service/cli (FastAPI + Typer install in <30s on cold cache). For desktop, allow 120s install timeout, OR mock the cargo fetch via `CARGO_NET_OFFLINE=1` after a one-time priming step. Document the divergence in `test_e2e_playbooks.py`'s parametrize ID. Recommended: per-playbook timeout dict, not a single global.

**Warning signs:** `subprocess.TimeoutExpired` on the desktop case but not the others.

---

## Code Examples

### Example 1: `assets/fastapi-starter/main.py` (D-10, D-11, D-12)

```python
# assets/fastapi-starter/main.py — verified Pydantic v2 + FastAPI 0.136.1 patterns
# Source: https://fastapi.tiangolo.com/fastapi-cli/ (verified 2026-05-01)
# Source: https://docs.pydantic.dev/latest/concepts/models/ (Pydantic v2 BaseModel)
"""OSBuilder FastAPI starter (ai-service playbook)."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="OSBuilder AI Service Starter",
    version="0.1.0",
)


class SummarizeRequest(BaseModel):
    """Pydantic v2 model — uses Field(...) for declarative defaults + constraints."""
    text: str = Field(..., min_length=1, max_length=100_000,
                       description="Input text to summarize.")


class SummarizeResponse(BaseModel):
    summary: str


def summarize(text: str) -> str:
    """Stub — returns first 200 chars.

    TO WIRE A REAL LLM: replace this body with a call to your provider.
    Example (after `uv add anthropic`):

        from anthropic import Anthropic
        client = Anthropic()  # reads ANTHROPIC_API_KEY from env
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": f"Summarize: {text}"}],
        )
        return msg.content[0].text
    """
    return text[:200]


@app.get("/")
def read_root():
    return {"message": "Hello from OSBuilder AI Service"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def post_summarize(req: SummarizeRequest):
    return SummarizeResponse(summary=summarize(req.text))
```

### Example 2: `assets/cli-starter/__main__.py.tmpl` (D-13, D-14)

```python
# assets/cli-starter/__main__.py.tmpl — verified Typer 0.25.1 + Rich auto-loaded
# Source: https://typer.tiangolo.com/tutorial/ (verified 2026-05-01)
# Source: https://typer.tiangolo.com/tutorial/commands/help/ (Rich help panel)
"""OSBuilder CLI starter — replace {{project_name}} with the user's app name."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import typer
from rich.console import Console

APP_NAME = "{{project_name}}"
DB_PATH = Path.home() / f".{APP_NAME}" / "state.db"

app = typer.Typer(
    name=APP_NAME,
    help="OSBuilder CLI starter — type --help for commands.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pings ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "ts TEXT NOT NULL)"
    )
    return conn


@app.command()
def ping():
    """Write a row to SQLite and read it back — proves persistence works."""
    conn = _init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute("INSERT INTO pings (ts) VALUES (?)", (ts,))
    conn.commit()
    cur = conn.execute("SELECT COUNT(*) FROM pings")
    count = cur.fetchone()[0]
    conn.close()
    console.print(f"[green]ping #{count}[/green] at [cyan]{ts}[/cyan]")
    console.print(f"DB: [dim]{DB_PATH}[/dim]")


if __name__ == "__main__":
    app()
```

`pyproject.toml` snippet to be added by `scaffold_cli` post-`uv init`:

```toml
[project.scripts]
{{project_name}} = "{{project_name}}.__main__:app"

[project]
dependencies = [
    "typer>=0.25.1",
]
```

### Example 3: `assets/hub-template/CLAUDE.md.tmpl` (D-04, D-05)

```markdown
# {{project_name}} Hub

This is the central workspace for all related tools. Open this folder whenever you need to access any of the tools below.

## Tools in This Hub

| Folder | Purpose | Key Skill |
|--------|---------|-----------|
{{routing_table}}

## Adding New Tools

Drop new tools as subfolders here and update this table. Re-run `/osbuilder` from inside a subfolder to scaffold its implementation.

## Notes For LLM Agents

- Use the nearest subproject `CLAUDE.md`; this file is only a router for the hub.
- Folder names are exact and case-sensitive.
- Keep secrets out of source files.
```

`{{routing_table}}` is replaced with N rows of `| \`<sub>/\` | TODO — describe <sub> | n/a |` by `scaffold_hub`.

### Example 4: Parametrized E2E test (D-17, D-18)

```python
# scripts/tests/test_e2e_playbooks.py — Phase 7 Plan 07-06
# Mirrors test_gh_handoff.py monkeypatch + _real_run capture pattern
"""E2E parametrized test: intake → scaffold → install → boot → stop per playbook."""
from __future__ import annotations
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAFFOLD = REPO_ROOT / "scripts" / "scaffold_dispatch.py"
INTAKE   = REPO_ROOT / "scripts" / "intake_handler.py"

# Per-playbook timeouts (Pitfall 8 — desktop needs more for cold Cargo fetches)
TIMEOUTS = {
    "ai-service": {"install": 60, "boot": 30},
    "cli":         {"install": 30, "boot": 15},
    "desktop":     {"install": 120, "boot": 60},
    "hub":         {"install": 5,  "boot": 5},  # hub doesn't install or boot
}

PLAYBOOK_BOOT_CMD = {
    "ai-service": ["uv", "run", "fastapi", "dev", "--port", "0"],
    "cli":         None,  # CLI "boot" = `<name> --help`; not a long-running daemon
    "desktop":     ["pnpm", "tauri", "dev"],
    "hub":         None,  # hub has no boot
}

# pytest.mark.skipif for tools that aren't installed locally — preflight should
# normally guarantee them but CI without preflight needs the skip
def _has(tool: str) -> bool:
    return shutil.which(tool) is not None


@pytest.mark.parametrize("playbook,intake_text", [
    ("ai-service", "I want an HTTP API that summarizes documents with an LLM"),
    ("cli",         "I want a command-line tool to organize my photo library"),
    ("desktop",     "I want a desktop app that runs locally with a tray icon"),
    ("hub",         "build me a hub like Professor Hub for grading and rostering"),
])
def test_e2e_playbook(tmp_project_root, playbook, intake_text):
    """5-step contract per CONTEXT D-17."""
    if playbook == "ai-service" and not _has("uv"):
        pytest.skip("uv not installed — preflight required")
    if playbook == "desktop" and not (_has("pnpm") and _has("cargo")):
        pytest.skip("pnpm + cargo not installed — preflight required")

    # 1. intake
    proc = subprocess.run(
        [sys.executable, str(INTAKE), "parse", "--input", intake_text,
         "--project-root", str(tmp_project_root)],
        check=True, capture_output=True, text=True, timeout=10,
    )
    spec = (tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md").read_text()
    expected_app_type = {
        "ai-service": "ai-service", "cli": "cli",
        "desktop": "desktop", "hub": "hub-platform",
    }[playbook]
    assert f"**App type:** {expected_app_type}" in spec

    # 2. scaffold
    project_name = f"{playbook.replace('-', '_')}_smoke"
    proc = subprocess.run(
        [sys.executable, str(SCAFFOLD), "scaffold",
         "--project-name", project_name,
         "--project-root", str(tmp_project_root),
         "--playbook", expected_app_type],
        check=True, capture_output=True, text=True, timeout=60,
    )
    project_dir = tmp_project_root / project_name
    assert project_dir.exists()

    # 3. install (skip for hub — no install)
    if playbook != "hub":
        install_cmd = {
            "ai-service": ["uv", "sync"],
            "cli":         ["uv", "sync"],
            "desktop":     ["pnpm", "install"],
        }[playbook]
        subprocess.run(install_cmd, cwd=str(project_dir), check=True,
                        capture_output=True, text=True,
                        timeout=TIMEOUTS[playbook]["install"])

    # 4. boot (only ai-service and desktop have a daemon)
    boot_cmd = PLAYBOOK_BOOT_CMD[playbook]
    if boot_cmd is not None:
        with subprocess.Popen(
            boot_cmd, cwd=str(project_dir),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        ) as proc:
            try:
                # Wait for "Application startup complete" or similar; or just sleep
                time.sleep(min(TIMEOUTS[playbook]["boot"], 8))
                # 5. stop (SIGTERM)
                if os.name != "nt":
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                pytest.fail(f"{playbook} boot did not stop cleanly")
    elif playbook == "cli":
        # CLI "boot" = `<name> --help` returns 0 with Rich-formatted output
        result = subprocess.run(
            ["uv", "run", project_name, "--help"],
            cwd=str(project_dir), capture_output=True, text=True,
            timeout=TIMEOUTS["cli"]["boot"], check=True,
        )
        assert "Usage:" in result.stdout or "Commands" in result.stdout
```

### Example 5: Friendly-error dictionary additions (D-22 reference)

```yaml
# Append to references/friendly-errors/dictionary.yaml — 5 new entries

- id: uv-not-installed
  match_pattern: "uv: command not found"
  category: preflight
  title: "uv (Python package manager) isn't installed yet"
  what_broke: "OSBuilder needs the 'uv' command to scaffold Python projects (FastAPI / CLI playbooks)."
  what_to_do: "Run preflight to auto-install uv, or install it manually."
  copy_paste_command: "python3 scripts/preflight_check.py install"
  phase_seen: "preflight, 7"
  expansion_note: "Phase 7 ai-service + cli playbooks"

- id: cargo-not-installed
  match_pattern: "cargo: command not found"
  category: preflight
  title: "Rust isn't installed yet"
  what_broke: "OSBuilder needs the Rust toolchain (cargo + rustc) to scaffold desktop apps with Tauri."
  what_to_do: "Run preflight to auto-install Rust via rustup, or install it manually."
  copy_paste_command: "python3 scripts/preflight_check.py install"
  phase_seen: "preflight, 7"
  expansion_note: "Phase 7 desktop playbook"

- id: tauri-cli-not-installed
  match_pattern: "tauri: command not found"
  category: preflight
  title: "Tauri CLI isn't installed yet in this project"
  what_broke: "The 'tauri' command is provided by @tauri-apps/cli and lives in the project's node_modules."
  what_to_do: "Run pnpm install in the project directory to install the local Tauri CLI."
  copy_paste_command: "pnpm install"
  phase_seen: "7"
  expansion_note: "Phase 7 desktop playbook"

- id: create-tauri-app-failed
  match_pattern: "create-tauri-app.*exit"
  pattern_type: regex
  category: scaffold
  title: "create-tauri-app couldn't finish scaffolding"
  what_broke: "The Tauri scaffolder exited with an error before it finished. Common causes: pnpm not installed, network problem, or invalid identifier."
  what_to_do: "Run preflight to ensure pnpm and Rust are installed, then retry."
  copy_paste_command: "python3 scripts/preflight_check.py install"
  phase_seen: "7"
  expansion_note: "Phase 7 desktop playbook"

- id: fastapi-cli-missing
  match_pattern: "Error: No module named 'fastapi.cli'"
  category: scaffold
  title: "fastapi dev command isn't available"
  what_broke: "The fastapi CLI runner needs the 'standard' extra: fastapi[standard]."
  what_to_do: "Re-add fastapi with the standard extra in your project's pyproject.toml."
  copy_paste_command: "uv add 'fastapi[standard]'"
  phase_seen: "7"
  expansion_note: "Phase 7 ai-service playbook (Pitfall 2)"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `uvicorn main:app --reload` | `fastapi dev` | FastAPI 0.111+ shipped `fastapi-cli` (April 2026) | Friendlier banner, auto-reload identical, prefer for dev |
| `pip install poetry && poetry install` | `uv sync` (reads pyproject.toml directly) | uv 0.1+ (2025) | 10-100x faster; one binary; lockfile auto-created |
| `typer[all]` extras for Rich | `typer` (rich is hard dep) | typer 0.25.0 (2026-04) | One less extras-decision; rich always installed |
| Pydantic v1 `@validator`, `class Config` | Pydantic v2 `@field_validator`, `model_config = ConfigDict()` | Pydantic 2.0 (2023) | v1 syntax silently no-ops in v2 — Pitfall 4 |
| `npx create-tauri-app@latest` (interactive) | `pnpm create tauri-app@latest <name> --manager pnpm --template react-ts --identifier <id> -y` (non-interactive) | create-tauri-app 4.x flag set stable | Reproducible scaffolds across CI machines |
| Hand-rolled hub `CLAUDE.md` per build | Template-stamped from `assets/hub-template/CLAUDE.md.tmpl` | Phase 7 design (D-04) | Determinism + idempotency |

**Deprecated/outdated:**
- `pydantic.BaseSettings` → moved to `pydantic-settings` package in v2.
- Tauri 1 (`tauri-apps/tauri-cli` v1.x) — Tauri 2 is the locked decision. `--tauri-version 1` is still supported by create-tauri-app for legacy users.
- Typer's `typer-cli` (a separate tool, NOT typer itself) — was a way to run typer apps without writing main entry. Not used here; we ship a proper `[project.scripts]` entry.

---

## Assumptions Log

> Claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The recommended weighted-keyword scores (e.g., `"hub" = 3`, `"professor hub" = 4`) are good defaults | §Pattern 2 (Inference) | If real intake distribution disagrees, more "ask the question" fallbacks fire than expected. Self-correcting because the fallback IS user-friendly per IN-04. |
| A2 | Per-playbook E2E timeouts (`ai-service:60s install, desktop:120s install`) are correct for typical CI | §Code Example 4, Pitfall 8 | Flaky tests on slow networks. Mitigation: timeouts are per-playbook dict, not global — easy to tune later. |
| A3 | Tauri's identifier convention `com.osbuilder.<sanitized-name>` is sufficient for non-published apps (no real signing) | §Pitfall 7 | If users later publish to Mac App Store, they'll need to override; not a v1 concern. |
| A4 | `assets/hub-template/professor-snapshot/` is the right vendor location vs `.planning/codebase/snapshots/professor/` | §Recommended structure | Only matters for test discoverability — `assets/` is git-tracked and ships with the skill, so test-time access is guaranteed. CONTEXT.md leaves this to Claude's discretion. **Recommendation: `assets/hub-template/professor-snapshot/`** because `.planning/` is doc-only and not shipped with the installed skill. |
| A5 | The 5-step E2E contract (intake → scaffold → install → boot → stop) is the right shape — not a 4-step (no install) or 6-step (with verify) | §Pattern 1, Example 4 | If "stop" is hard to detect cleanly cross-platform, may need to drop step 5 to "send SIGTERM, accept any exit." Risk is medium — Windows lacks `os.killpg`. |
| A6 | Subprocess timeouts via `subprocess.run(timeout=N)` work cross-platform on Windows for `pnpm install` | §Code Example 4 | Windows + WSL has known `subprocess.TimeoutExpired` quirks with shell=False. Phase 6 already exercises this on `git push` so risk is LOW. |
| A7 | `scaffold_hub` should NOT shell out to a scaffolder — pure file-stamping is correct | §Pattern 4 | Only hub deviates from the subprocess pattern. If consistency turns out to matter more, an empty subprocess wrapper could be added later. Low risk. |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **Does `create-tauri-app -y` (yes-flag) skip ALL prompts, or are there optional prompts post-`--y`?**
   - What we know: `-y, --yes Skip prompts and use defaults where applicable` (verified `--help` 2026-05-01).
   - What's unclear: The "where applicable" phrasing suggests some prompts may not have defaults.
   - Recommendation: 07-04 should run `pnpm create tauri-app@latest test-tauri --manager pnpm --template react-ts --identifier com.osbuilder.testtauri --tauri-version 2 -y` once during plan authoring and verify zero prompts. If a prompt fires, document the missing flag.

2. **Should `scaffold_desktop` add a `tauri.conf.json` post-scaffold edit (e.g., to set window title from intake)?**
   - What we know: D-07/D-08 say "pin flags, accept Tauri's template drift" — implies NO post-scaffold edits for now.
   - What's unclear: Will users complain about the default window title `tauri-app`?
   - Recommendation: 07-04 ships v1 unchanged. Add `tauri.conf.json` post-scaffold edit as a Phase 8 polish item if dogfood feedback demands.

3. **Does `uv sync` succeed without network when `uv.lock` is present and all deps are cached?**
   - What we know: `uv sync --frozen` is the offline-friendly mode.
   - What's unclear: Whether 07-06 E2E test should pass `--frozen` (faster but tighter coupling) or plain `sync` (slower but matches stranger-clone).
   - Recommendation: Use plain `uv sync` in 07-06 to match the stranger-clone runbook — that's the actual contract being tested. Document the trade in `test_e2e_playbooks.py` docstring.

4. **Should the inference function use a config file (TOML/YAML) for `PLAYBOOK_KEYWORDS` or hardcode it as a Python dict?**
   - What we know: Existing patterns (`REFUSE_KEYWORDS` tuple in `intake_handler.py:57`) hardcode in Python.
   - What's unclear: Is keyword tuning likely to be a non-coding contributor task?
   - Recommendation: Hardcode in Python for v1 (matches `REFUSE_KEYWORDS`). Move to a config file in v2 if + when external contribution becomes a real pattern.

5. **For hub-platform, what counts as a "subtool name" if the user says "Professor Hub for grading, exam grading, and student emails"?**
   - What we know: D-06 says sub-tool names come from intake parsing. Question-bank fallback if unresolvable.
   - What's unclear: Is "exam grading" two tools or one? Naming convention (`exam-grading/` vs `exam_grading/` vs `Exam grader/`)?
   - Recommendation: Plan 07-05 should specify a `_extract_subtools(text) -> list[str]` helper that returns kebab-case names. Add a question-bank entry: "I see <N> tools in your description — should they be named [a, b, c]? [yes / let me rename / I don't know, you decide]". CONTEXT.md says this is OK to ask.

6. **Should preflight install Rust/uv lazily (only when a desktop/python playbook is selected) or eagerly (always)?**
   - What we know: D-20 says "auto-install with single confirmation, same model as Node/Docker." Existing preflight installs all 5 tools eagerly.
   - What's unclear: Does it match the spirit of D-20 to install Rust on a user's machine when they're just building a web app?
   - Recommendation: **Lazy** — extend `plan()` to accept a `playbook` arg (default "all") and return only relevant actions. The "ask once, install once" principle is preserved per playbook. Document in `references/preflight/README.md`.

---

## Environment Availability

| Dependency | Required By | Available (this machine) | Version | Fallback |
|------------|------------|---------|---------|----------|
| `npm` | desktop scaffold (for npx and as pnpm bootstrap) | ✓ | (verified — `npm view` calls succeeded) | — |
| `pnpm` | desktop scaffold | ? | (preflight installs via `npm i -g pnpm`) | `ensure_pnpm()` already handles |
| `python3` ≥ 3.13 | all Python playbooks + scripts | ✓ | (Phase 1 preflight already verifies) | — |
| `uv` | ai-service + cli scaffolds | ? | (preflight will install via D-20) | None — blocking for ai-service/cli |
| `cargo`/`rustc` | desktop builds | ? | (preflight will install via D-20) | None — blocking for desktop |
| `gh` CLI | shared with phase 6 | ✓ | (Phase 2 preflight) | — |
| `git` | shared | ✓ | (Phase 2 preflight) | — |
| Xcode CLT (macOS) / `build-essential` (Linux) / MSVC (Windows) | desktop on each OS | varies | (Tauri 2 prereq — preflight should detect) | Document install in `references/preflight/<os>.md` |
| `webkit2gtk-4.1-dev` (Linux only) | desktop on Linux | varies | (Ubuntu 22.04+ has it; Ubuntu 20.04 needs `-4.0`) | Document v22.04+ as min Linux |
| `pre-commit` + `gitleaks` | shared with phase 6 (CI workflow only) | n/a — only used in built repos | n/a | — |

**Missing dependencies with no fallback:**
- `uv` (blocks ai-service + cli scaffolds) — **but** D-20 mandates auto-install, so this is solved at the preflight layer before scaffold runs.
- `cargo`/`rustc` (blocks desktop) — same: D-20 solves it.

**Missing dependencies with fallback:**
- `pnpm` (blocks desktop scaffold AND web scaffold) — `ensure_pnpm()` already exists in `scaffold_dispatch.py:161-168`. Reused for `scaffold_desktop`.

---

## Validation Architecture

> `nyquist_validation: true` in `.planning/config.json` — this section is REQUIRED.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (Python 3.13 stdlib + pytest only — no new deps; matches Phases 1-6) |
| Config file | `pyproject.toml` (existing — Phase 1) |
| Quick run command | `python3 -m pytest scripts/tests/ -x --tb=short -q` |
| Full suite command | `python3 -m pytest scripts/tests/ --tb=short -q` |
| Estimated runtime | ~25 seconds (quick, all phases). Phase 7 adds ~16 unit tests + 4 parametrized E2E cases (~10s mocked + ~8min real-tool) |
| E2E suite (slow) | `python3 -m pytest scripts/tests/test_e2e_playbooks.py -v` (gated by `@pytest.mark.skipif` per tool availability; ~8min wall clock when all tools present) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAF-02 | `references/playbooks/ai-service.md` exists with required sections | unit (file content) | `pytest scripts/tests/test_scaffold_dispatch.py::test_ai_service_playbook_md_present -x` | ❌ Wave 0 |
| SCAF-02 | `assets/fastapi-starter/main.py` ships, has `/`, `/health`, `/summarize`, Pydantic v2 BaseModel | unit (AST grep) | `pytest scripts/tests/test_scaffold_dispatch.py::test_fastapi_starter_endpoints -x` | ❌ Wave 0 |
| SCAF-02 | `scaffold_ai_service(name, root)` calls `uv init --app`, writes main.py, runs `uv add 'fastapi[standard]'` | unit (mocked subprocess) | `pytest scripts/tests/test_scaffold_dispatch.py::test_scaffold_ai_service_subprocess_calls -x` | ❌ Wave 0 |
| SCAF-02 | E2E: `uv run fastapi dev` boots and `/docs` returns 200 | parametrized E2E | `pytest scripts/tests/test_e2e_playbooks.py::test_e2e_playbook[ai-service-...] -x` | ❌ Wave 0 |
| SCAF-03 | `references/playbooks/cli.md` exists with required sections | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_cli_playbook_md_present -x` | ❌ Wave 0 |
| SCAF-03 | `assets/cli-starter/__main__.py.tmpl` ships with Typer + ping subcommand | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_cli_starter_typer_app -x` | ❌ Wave 0 |
| SCAF-03 | `scaffold_cli(name, root)` runs `uv init --app`, adds typer dep, writes __main__.py | unit (mocked subprocess) | `pytest scripts/tests/test_scaffold_dispatch.py::test_scaffold_cli_subprocess_calls -x` | ❌ Wave 0 |
| SCAF-03 | E2E: `uv run <name> --help` prints Rich-formatted help, `<name> ping` writes to SQLite | parametrized E2E | `pytest scripts/tests/test_e2e_playbooks.py::test_e2e_playbook[cli-...] -x` | ❌ Wave 0 |
| SCAF-04 | `references/playbooks/desktop.md` exists with required sections + Electron rationale | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_desktop_playbook_md_present -x` | ❌ Wave 0 |
| SCAF-04 | `scaffold_desktop(name, root)` runs `pnpm create tauri-app@latest` with verified flags | unit (mocked subprocess) | `pytest scripts/tests/test_scaffold_dispatch.py::test_scaffold_desktop_subprocess_calls -x` | ❌ Wave 0 |
| SCAF-04 | identifier follows `com.osbuilder.<sanitized>` pattern | unit (pure function) | `pytest scripts/tests/test_scaffold_dispatch.py::test_desktop_identifier_format -x` | ❌ Wave 0 |
| SCAF-04 | Electron in spec → refused via global refuse-list (NOT new keyword — D-22) | unit | `pytest scripts/tests/test_refusal.py::test_electron_refused_globally -x` | ❌ Wave 0 |
| SCAF-04 | E2E: `pnpm tauri dev` opens window (boot signal — process up + readable stdout) | parametrized E2E | `pytest scripts/tests/test_e2e_playbooks.py::test_e2e_playbook[desktop-...] -x` | ❌ Wave 0 |
| SCAF-05 | `references/playbooks/hub-platform.md` exists with required sections | unit | `pytest scripts/tests/test_scaffold_dispatch.py::test_hub_playbook_md_present -x` | ❌ Wave 0 |
| SCAF-05 | `assets/hub-template/professor-snapshot/` vendored | unit (file presence) | `pytest scripts/tests/test_scaffold_dispatch.py::test_hub_snapshot_vendored -x` | ❌ Wave 0 |
| SCAF-05 | `scaffold_hub(name, root, subtools=[...])` produces matching structural signature | unit (structural diff) | `pytest scripts/tests/test_scaffold_dispatch.py::test_hub_matches_professor_structure -x` | ❌ Wave 0 |
| SCAF-05 | Top-level CLAUDE.md has routing-table with one row per subtool | unit (markdown parse) | `pytest scripts/tests/test_scaffold_dispatch.py::test_hub_routing_table -x` | ❌ Wave 0 |
| SCAF-05 | E2E: scaffold completes in <10s (no install/boot to test for hub) | parametrized E2E | `pytest scripts/tests/test_e2e_playbooks.py::test_e2e_playbook[hub-...] -x` | ❌ Wave 0 |
| (Cross) | `infer_app_type(text)` returns correct playbook for 5 sample paragraphs | unit | `pytest scripts/tests/test_intake.py::test_infer_app_type_per_playbook -x` | ❌ Wave 0 |
| (Cross) | Low-confidence paragraph triggers question-bank fallback | unit | `pytest scripts/tests/test_intake.py::test_inference_low_confidence_asks -x` | ❌ Wave 0 |
| (Cross) | Refuse keyword takes precedence over inference | unit | `pytest scripts/tests/test_intake.py::test_refuse_beats_inference -x` | ❌ Wave 0 |
| (Cross) | preflight detects + plans uv install action | unit | `pytest scripts/tests/test_preflight.py::test_uv_detection_and_plan -x` | ❌ Wave 0 |
| (Cross) | preflight detects + plans rustup install action | unit | `pytest scripts/tests/test_preflight.py::test_rustup_detection_and_plan -x` | ❌ Wave 0 |
| (Cross) | preflight winget IDs are exact strings: `astral-sh.uv` and `Rustlang.Rustup` | unit | `pytest scripts/tests/test_preflight.py::test_winget_ids_exact -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest scripts/tests/ -x --tb=short -q` (~25s; excludes E2E by default)
- **Per wave merge:** Full suite green AND `pytest scripts/tests/test_e2e_playbooks.py -v` (E2E with skip-if-missing-tools)
- **Phase gate:** Full suite green + manual UAT in 07-HUMAN-UAT.md complete before `/gsd-verify-work`

### Wave 0 Gaps

The planner MUST schedule a Wave 0 plan (07-01 OR a dedicated 07-00) that lands the following RED stubs and shared fixtures BEFORE any Wave 1 implementation:

- [ ] `scripts/tests/test_e2e_playbooks.py` — RED stubs for the 4-case parametrized E2E (07-06 lands GREEN)
- [ ] `scripts/tests/test_intake.py` — extend with 3 inference test stubs (test_infer_app_type_per_playbook, test_inference_low_confidence_asks, test_refuse_beats_inference)
- [ ] `scripts/tests/test_scaffold_dispatch.py` — extend with ~12 stubs (3 per playbook: md presence, scaffold subprocess shape, post-scaffold writes)
- [ ] `scripts/tests/test_preflight.py` — extend with 3 stubs (uv detection, rustup detection, winget ID exact)
- [ ] `scripts/tests/test_refusal.py` — extend with 1 stub (test_electron_refused_globally — covers D-22)
- [ ] `scripts/tests/conftest.py` — extend with: `playbook_case` parametrize fixture (4 cases), `mock_uv_subprocess` (programmable canned responses), `mock_create_tauri_app_subprocess`
- [ ] Framework install: none required (pytest 9.0.2 already in pyproject.toml)
- [ ] `scripts/state_writer.py` — extend `ALLOWED_FIELDS` with: `subtools` (comma-separated list for hub-platform builds — additive, NOT in REQUIRED_FIELDS, matches Phase 6 pattern)
- [ ] `assets/hub-template/professor-snapshot/` — vendor the snapshot (~10 files copied from `../professor/` top-level minus `.git`, `.planning`, `.venv`, etc.)

*(If no gaps: "None — existing test infrastructure covers all phase requirements" — Phase 7 has gaps, listed above.)*

### Manual-Only Verifications (07-HUMAN-UAT.md content)

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stranger clones the resulting ai-service repo on a fresh machine and reaches `/docs` in ≤5 min | SCAF-02 + SC-05 | "Stranger" + "fresh machine" + "5 min" can't be deterministically automated | After E2E build, on a SECOND machine: `gh repo clone <user/repo>; cd <repo>; <follow README runbook>; verify /docs page renders`. Time the run. |
| Same for cli, desktop, hub-platform | SCAF-03/04/05 + SC-05 | (same) | (same, per playbook) |
| Refusal of "build me an Electron app" produces friendly explanation pointing to Tauri rationale | SC-03, D-22 | Default-mode refusal copy is human-judged for friendliness | Submit "build me an Electron desktop app for X"; verify state.md `last_failure` matches refusal pattern; verify copy mentions Tauri 2 alternative. |
| `/summarize` POST endpoint stub responds correctly with valid Pydantic v2 request | SCAF-02 (D-12 verification) | Real HTTP smoke against booted server | After ai-service boot: `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":"hello world"}'` returns `{"summary":"hello world"}`. |

---

## Per-Plan Implementation Notes

### 07-01: Intake routing + inference

**Goal:** Replace hardcoded `app_type="web"` at `intake_handler.py:264` with `infer_app_type` + question-bank fallback.

**Files:**
- `scripts/intake_handler.py` — ADD `PLAYBOOK_KEYWORDS` const + `infer_app_type` function + caller wiring in `parse_paragraph`. Modify the docstring at line 263-265 to remove the TODO(phase-7) marker.
- `references/question-bank.md` — APPEND new "Q: What kind of thing" outcome-framed question (mirroring IN-03/IN-04 style). The 5 named branches: web / API / CLI / desktop / hub-platform; "I don't know, you decide" → web (safest default — broadest reach).
- `scripts/tests/test_intake.py` — ADD 3 test stubs (per Validation map).

**Gotchas:**
- `parse_structured` MUST stay untouched — it respects an explicit `app_type` key already.
- Refuse-keyword check (`check_refuse_list`) runs AFTER spec is written; inference happens BEFORE, so the order is intake-text → infer → write spec → refuse-check. If refuse fires, the spec already has app_type set — that's fine; refusal short-circuits before scaffolding anyway.
- Test paragraphs MUST be plain English; using exact playbook names like "build me an ai-service" is a degenerate input, NOT a real intake — sample paragraphs in tests should mirror SC-01..SC-04 wording.

**Wave-parallelizable with:** Nothing — this is Wave 1 single. 07-02..07-05 unblock once this is GREEN.

### 07-02: AI-service playbook (SCAF-02)

**Goal:** Add FastAPI + uv + Pydantic v2 scaffold path.

**Files:**
- `references/playbooks/ai-service.md` — NEW (~70 lines, mirroring web.md). Pinned versions: fastapi 0.136.1, uv 0.11.8, pydantic 2.13.3.
- `assets/fastapi-starter/main.py` — NEW (Example 1 above).
- `assets/fastapi-starter/pyproject.snippet.toml` — NEW (deps to add post-`uv init`).
- `scripts/scaffold_dispatch.py` — ADD `scaffold_ai_service` (~50 lines, mirroring `scaffold_web` shape). ADD `ensure_uv` helper (mirrors `ensure_pnpm`).
- `references/friendly-errors/dictionary.yaml` — APPEND `uv-not-installed`, `fastapi-cli-missing` entries.
- `references/stack-menu.md` — APPEND `## ai-service playbook defaults` table.
- `scripts/tests/test_scaffold_dispatch.py` — ADD 4 stubs.

**Gotchas:**
- Pitfall 2 — `uv add 'fastapi[standard]'` (single quotes mandatory).
- Pitfall 4 — Pydantic v2 syntax in main.py (no `@validator`, no `class Config`).
- `_pick_database("ai-service", at)` returns `"postgres"` (line 89 of scaffold_dispatch.py) — already correct, no change needed.
- `_write_dockerfile(project_dir, stack_family="python-uv")` — but `python-uv.Dockerfile.tmpl` doesn't exist yet in `assets/dockerfiles/`. Plan 07-02 ships it OR documents the no-op behavior (current `_write_dockerfile` silently no-ops on missing template — line 102-103).
- The Dockerfile question matters for SHIP-03 — Phase 6 ships Dockerfile for web; AI-service should ship one too (it's a deployable service). RECOMMEND: 07-02 ships `assets/dockerfiles/python-uv.Dockerfile.tmpl`.

**Wave-parallelizable with:** 07-03, 07-04, 07-05 (all touch disjoint files except `scaffold_dispatch.py` and `dictionary.yaml` — these need atomic-merge discipline, see Wave Coordination below).

### 07-03: CLI playbook (SCAF-03)

**Goal:** Add Python + Typer + Rich + SQLite scaffold path.

**Files:**
- `references/playbooks/cli.md` — NEW (~70 lines).
- `assets/cli-starter/__main__.py.tmpl` — NEW (Example 2 above).
- `assets/cli-starter/pyproject.snippet.toml` — NEW (typer dep).
- `scripts/scaffold_dispatch.py` — ADD `scaffold_cli` (~40 lines).
- `references/stack-menu.md` — APPEND `## cli playbook defaults` table.
- `scripts/tests/test_scaffold_dispatch.py` — ADD 4 stubs.

**Gotchas:**
- Pitfall 5 — Document that typer 0.25.1 hard-deps rich; no separate add needed.
- `{{project_name}}` template substitution — typer's `[project.scripts]` entry points need a Python-import-safe name. Sanitize: replace `-` with `_` in the Python module path, but keep `-` in the script name (`uv run my-cli` works, file is `my_cli/__main__.py`).
- `Path.home() / f".{APP_NAME}" / "state.db"` — sanitize APP_NAME identically (no `-`).
- No Dockerfile, no compose.yaml (CLI doesn't ship as a container per `_pick_database` already routes "cli" → "sqlite").
- `_write_ci_workflow(stack_family="python")` — already exists from Phase 6.

**Wave-parallelizable with:** 07-02, 07-04, 07-05.

### 07-04: Desktop playbook (SCAF-04)

**Goal:** Add Tauri 2 + create-tauri-app scaffold path + migrate Electron refusal.

**Files:**
- `references/playbooks/desktop.md` — NEW (~80 lines, with Tauri-not-Electron section per D-09).
- `scripts/scaffold_dispatch.py` — ADD `scaffold_desktop` (~50 lines). ADD `_build_tauri_identifier(name)` helper.
- `references/refuse-list.md` — MIGRATE Electron refusal copy from web.md per D-22 (web.md gets a one-line cross-reference).
- `references/playbooks/web.md` — REMOVE the "Electron (use Tauri 2 via desktop playbook)" line from the refuse list section per D-22.
- `references/friendly-errors/dictionary.yaml` — APPEND `cargo-not-installed`, `tauri-cli-not-installed`, `create-tauri-app-failed`.
- `references/stack-menu.md` — APPEND `## desktop playbook defaults` table.
- `assets/ci-workflows/tauri.yml.tmpl` — NEW (Rust + Node combined CI; similar to existing python.yml.tmpl).
- `scripts/tests/test_scaffold_dispatch.py` — ADD 4 stubs.
- `scripts/tests/test_refusal.py` — ADD `test_electron_refused_globally` stub.

**Gotchas:**
- Verified flag set per `npx create-tauri-app --help` 2026-05-01: `--manager pnpm`, `--template react-ts`, `--identifier <id>`, `--tauri-version 2`, `-y` for non-interactive.
- Pitfall 1 — `ensure_pnpm()` BEFORE create-tauri-app; never fall back to `npm create ... -- --template`.
- Pitfall 3 — Document Windows MSVC default in `references/preflight/windows.md`. Auto-run `rustup default stable-msvc` post-install on Windows.
- Pitfall 7 — Identifier MUST be reverse-DNS. Helper: `_build_tauri_identifier(name) -> str`.
- Pitfall 8 — E2E timeout for desktop install is 120s (vs 60s for others).
- D-09 — Web playbook STILL needs to mention Tauri rationale, just via cross-reference to refuse-list.md, not inline copy.

**Wave-parallelizable with:** 07-02, 07-03, 07-05.

### 07-05: Hub-platform playbook (SCAF-05)

**Goal:** Add umbrella-workspace scaffold path matching professor/ structure.

**Files:**
- `references/playbooks/hub-platform.md` — NEW (~70 lines).
- `assets/hub-template/CLAUDE.md.tmpl` — NEW (Example 3 above).
- `assets/hub-template/subtool-CLAUDE.md.tmpl` — NEW (~10 lines, placeholder per subtool).
- `assets/hub-template/professor-snapshot/` — NEW directory containing copied top-level files from `../professor/` (CLAUDE.md, AGENTS.md, .mcp.json, top-level subdir LISTING — but we vendor empty subdirs OR a minimal subdir each containing a CLAUDE.md to mirror the per-subtool routing pattern). Recommended minimum vendor:
  ```
  assets/hub-template/professor-snapshot/
  ├── CLAUDE.md         (verbatim copy)
  ├── AGENTS.md         (verbatim copy)
  ├── LabNoteBookGrader/
  │   └── CLAUDE.md     (verbatim copy from professor/LabNoteBookGrader/CLAUDE.md if present, else stub)
  ├── Exam grader/
  │   └── CLAUDE.md     (same)
  ├── gradehub/
  │   └── (empty placeholder if no CLAUDE.md exists in real professor)
  └── student-email-tool/   (NOTE: real professor has this as a SYMLINK — vendor as empty placeholder)
  ```
- `scripts/scaffold_dispatch.py` — ADD `scaffold_hub` (~40 lines, pure file-stamping per Pattern 4).
- `scripts/intake_handler.py` — ADD `_extract_subtools(text)` helper to parse subtool list from intake.
- `scripts/state_writer.py` — EXTEND `ALLOWED_FIELDS` with `subtools` (comma-separated string).
- `references/stack-menu.md` — APPEND `## hub-platform playbook defaults` table (mostly N/A — no real stack).
- `scripts/tests/test_scaffold_dispatch.py` — ADD 5 stubs.

**Gotchas:**
- Hub does NOT shell out — pure file-stamping (Pattern 4). No subprocess test mocking needed.
- `_extract_subtools` should handle plurals: "for grading and rostering" → `["grading", "rostering"]`. Use simple regex `\b(\w+ing|\w+s)\b` — or better, ask via question-bank when count is ambiguous.
- The vendored snapshot is a TEST FIXTURE, not a runtime artifact. Document this in `assets/hub-template/README.md`.
- `professor/student-email-tool` is a symlink in real professor — vendor as empty placeholder dir to keep the snapshot self-contained.
- No Dockerfile, no CI workflow, no compose.yaml — hub is a workspace, not an app.

**Wave-parallelizable with:** 07-02, 07-03, 07-04.

### 07-06: Shared E2E harness (SC-05)

**Goal:** Single parametrized test exercising the 5-step contract across all 4 new playbooks.

**Files:**
- `scripts/tests/test_e2e_playbooks.py` — NEW (~250 lines; Example 4 above).
- `scripts/tests/conftest.py` — EXTEND with `playbook_case` fixture if needed (probably not — parametrize is sufficient).
- `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` — NEW (mirrors 06-HUMAN-UAT.md format with 4 playbook UAT rows + 1 Electron-refusal row).

**Gotchas:**
- The test MUST gracefully skip when prerequisites are missing (use `@pytest.mark.skipif(not _has(...))` per playbook). Real CI without preflight should still run the file (it'll just skip).
- D-18 timeout total is ~8min for all 4 cases. Mark the file with `@pytest.mark.slow` (declare in pyproject.toml under `[tool.pytest.ini_options].markers`) so a quick `pytest -m 'not slow'` skips it.
- Pitfall 8 — per-playbook timeout dict, not global.
- Hub case has no install/boot — assertion is just "scaffold succeeded + structural diff against snapshot."
- Cross-platform `os.killpg` is POSIX-only. Windows path uses `proc.terminate()` directly. Document the divergence inline in the test.

**Depends on:** 07-01 (inference) + 07-02..07-05 (each scaffold function exists and is GREEN).

**Wave-parallelizable with:** Nothing — runs in its own wave.

### Wave Coordination Notes

`scaffold_dispatch.py` and `references/friendly-errors/dictionary.yaml` are touched by ALL of 07-02..07-05. Avoid merge conflicts by:

- **Option A (recommended):** Plan 07-02..07-05 each opens a separate atomic block in `scaffold_dispatch.py` (e.g., one `def scaffold_ai_service` def each). Add a section divider comment block per playbook so diffs don't overlap. The dictionary.yaml is APPEND-only — same approach (one section divider per playbook).
- **Option B:** Serialize the 4 plans (07-02 → 07-03 → 07-04 → 07-05). Loses parallelism but is conflict-free.

Pattern A is the established Wave 1 pattern from Phase 6 (`scaffold_extensions.py` extension across 4 plans). Recommend A.

---

## Open Questions / Risks

(see "Open Questions" section above)

**Top risks for the planner to track:**

1. **create-tauri-app `-y` flag may not skip 100% of prompts** (Open Q1). Mitigation: 07-04 plan should include a one-time real-tool smoke during plan authoring.
2. **uv on Windows winget is `astral-sh.uv` not `Astral.UV`** (CONTEXT.md D-21 typo). Already corrected in this RESEARCH.md; planner should put the correct ID into preflight install action.
3. **Pydantic v1 → v2 migration silent failures** (Pitfall 4). The fastapi-starter MUST be tested for v2-native syntax in unit tests.
4. **Desktop E2E install timeout flakiness** (Pitfall 8). Per-playbook timeout dict, not global.
5. **Hub-platform vendored snapshot drift from real professor/** — research-time snapshot is point-in-time. If `../professor/` evolves, the snapshot doesn't auto-update. ACCEPTED: snapshot is a STRUCTURAL contract, not a content contract. Plan 07-05 should document the vendoring date + update procedure.

---

## Sources

### Primary (HIGH confidence)

- **Live `npx create-tauri-app --help`** (`npx --yes create-tauri-app@4.6.2 --help`, run 2026-05-01) — verified the exact flag set: `--manager [cargo, pnpm, yarn, npm, deno, bun, dotnet]`, `--template [vanilla, vanilla-ts, vue, vue-ts, svelte, svelte-ts, react, react-ts, solid, solid-ts, yew, leptos, sycamore, angular, preact, preact-ts, blazor, dioxus]`, `--identifier`, `-y/--yes`, `-f/--force`, `--tauri-version [1|2]`.
- **PyPI registry** (verified 2026-05-01) — fastapi 0.136.1, uv 0.11.8, typer 0.25.1, rich 15.0.0, pydantic 2.13.3, uvicorn 0.46.0.
- **npm registry** (verified 2026-05-01) — create-tauri-app 4.6.2, @tauri-apps/cli 2.11.0, create-next-app 16.2.4.
- **Typer 0.25.1 pyproject.toml** (`pypi.org/pypi/typer/json` requires_dist) — confirms `rich >=13.8.0` is a HARD dependency.
- **winget-pkgs manifest** `manifests/a/astral-sh/uv/0.11.8/astral-sh.uv.installer.yaml` — confirms package ID is `astral-sh.uv` (NOT `Astral.UV`).
- **OSBuilder codebase** (read directly):
  - `scripts/scaffold_dispatch.py` (332 lines) — patterns 1, 4
  - `scripts/intake_handler.py` (376 lines) — pattern 2
  - `scripts/preflight_check.py` (623 lines) — D-20 extension shape
  - `scripts/tests/conftest.py` (253 lines) — fixture catalog
  - `references/playbooks/web.md` (77 lines) — playbook .md template
  - `references/refuse-list.md` (67 lines) — D-22 migration target
  - `references/question-bank.md` (66 lines) — D-02 fallback target
  - `references/stack-menu.md` (43 lines) — per-playbook table format
  - `references/friendly-errors/dictionary.yaml` — 30 entries verified, 5 new entries documented
  - `assets/ci-workflows/python.yml.tmpl` (16 lines) — reused by ai-service + cli
  - `.planning/phases/06-ship-to-private-github-scalable-defaults/06-HUMAN-UAT.md` — UAT format precedent
  - `.planning/phases/06-ship-to-private-github-scalable-defaults/06-VALIDATION.md` — validation arch precedent
- **`../professor/` filesystem** (read directly 2026-05-01) — verified hub structure: top-level `CLAUDE.md` (29 lines, routing-table to LabNoteBookGrader/, Exam grader/, gradehub/, student-email-tool/ as symlink) + `AGENTS.md` (29 lines).
- **Tauri 2 official docs** (`v2.tauri.app/start/prerequisites/`) — system prerequisites verified.
- **rustup install URL** `https://sh.rustup.rs` — `HTTP/2 200`, content-length 29250, last-modified 2026-03-12 (verified curl HEAD).
- **uv install URL** `https://astral.sh/uv/install.sh` — redirects to `releases.astral.sh/installers/uv/latest/uv-installer.sh` (verified curl HEAD).

### Secondary (MEDIUM confidence)

- **Tauri create-project docs** (`v2.tauri.app/start/create-project/`) — flags partly documented; cross-verified with live `--help`.
- **uv FastAPI integration guide** (`docs.astral.sh/uv/guides/integration/fastapi/`) — documents `uv add fastapi --extra standard` and `uv run fastapi dev`.
- **FastAPI CLI docs** (`fastapi.tiangolo.com/fastapi-cli/`) — Pydantic v2 minimal example verified.
- **Typer Rich integration deepwiki** (`deepwiki.com/fastapi/typer/3-rich-integration`) — confirmed lazy-loaded since 0.17 + hard-dep since 0.25 (`>=13.8.0`).

### Tertiary (LOW confidence — flagged for validation)

- **Pitfall 7 (`com.osbuilder.<sanitized>` identifier convention)** — convention chosen by this research, NOT verified against the Mac App Store rules at scale. Planner should accept; risk is non-publication v1 apps don't care.
- **Inference-algorithm weights** (`PLAYBOOK_KEYWORDS`) — chosen by this research; not measured against a real intake corpus. The fallback question is the safety net; weights can tune over time.

---

## Metadata

**Confidence breakdown:**
- Standard stack (versions): HIGH — every version verified against live registry on 2026-05-01.
- create-tauri-app CLI flags: HIGH — verified by running `--help` locally.
- Architecture patterns: HIGH — direct extraction from existing codebase patterns.
- Pitfalls: HIGH — extracted from official docs + verified against version pins.
- Inference algorithm: MEDIUM — recommended weights are a starting point; D-02 fallback question is the safety net.
- Hub-platform snapshot: HIGH — read real `../professor/` directly; snapshot vendor-location is Claude's discretion (recommended `assets/hub-template/professor-snapshot/`).
- E2E timeouts: MEDIUM — informed estimate; Pitfall 8 documents the desktop divergence.
- winget IDs: HIGH — `astral-sh.uv` verified against live winget-pkgs manifest; CONTEXT.md D-21 typo flagged.

**Research date:** 2026-05-01
**Valid until:** 2026-06-01 (30 days for stable libraries; FastAPI / uv / typer have monthly release cadence — re-verify versions before committing playbook .md files).
