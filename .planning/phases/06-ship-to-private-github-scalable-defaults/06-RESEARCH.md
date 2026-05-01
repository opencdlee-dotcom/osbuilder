# Phase 6: Ship to private GitHub + scalable defaults — Research

**Researched:** 2026-05-01
**Domain:** Build → ship loop closure for OSBuilder (a Claude Code skill, written in bash + Python 3.13 stdlib + Markdown). Phase 6 wraps the verified scaffold from Phases 1–5 with: (a) private-GitHub repo creation via `gh`, (b) generated-app shape policy (`.env.example` / `.env` / `compose.yaml` / `Dockerfile` / one CI workflow), (c) gitleaks pre-commit defense, (d) refusal mechanics for K8s/microservices/Helm in default mode, (e) `gh auth status` drift remediation, and (f) database default rule (Postgres-via-compose for multi-user web; SQLite for single-user CLI).
**Confidence:** HIGH for codebase-internal decisions (`scaffold_dispatch.py` already writes `.env.example` + `compose.yaml`; `gsd_driver.py` PHASE_STEP_COMMANDS extension pattern; `state_writer.py` ALLOWED_FIELDS pattern — all verified by direct file read). HIGH for external tool versions (`gh` 2.90.0 verified locally, gitleaks v8.30.1 verified via GitHub releases API on 2026-05-01, Docker Compose `compose.yaml` priority order verified via official docs). MEDIUM for the README "stranger reaches working app in ≤ 5 min" criterion — requires manual UAT; deterministic test harness only verifies file presence + content patterns.

---

<user_constraints>
## User Constraints (from project context — no separate CONTEXT.md exists)

> Phase 6 has not been through a separate `/gsd-discuss-phase`; the constraints below are extracted verbatim from CLAUDE.md (project), PROJECT.md (Key Decisions), REQUIREMENTS.md (SHIP-01..05, SCL-01..06), ROADMAP.md (Phase 6 success criteria), and STATE.md (locked decisions).

### Locked Decisions

1. **Form:** OSBuilder is a Claude Code skill at `~/.claude/skills/osbuilder/`. Phase 6 work edits SKILL.md + adds Python 3.13 stdlib scripts under `scripts/` + adds Markdown templates under `references/` and `assets/`. **No new Python deps** (locked since Phase 1 — the project explicitly forbids them; stdlib-only).
2. **Privacy default:** `gh repo create --private` is the ONLY default. `--public` flag opt-in is required for public repos. Verified by `gh repo view --json visibility` returning `"PRIVATE"`.
3. **Compose v2 canonical filename:** `compose.yaml` (NOT `docker-compose.yml`). Per Docker Compose Specification: when multiple compose files coexist, `compose.yaml` is the preferred canonical name. `version:` key is OBSOLETE in Compose v2 — must be removed from any template. [VERIFIED: docs.docker.com/compose/intro/compose-application-model]
4. **Database default rule:** Multi-user web → Postgres via `compose.yaml`; single-user CLI → SQLite (file path under `~/.local/share/<app>/` or platform-equivalent). Detected from `state.md` field `app_type` (already in REQUIRED_FIELDS) cross-referenced with `playbook` (web vs cli).
5. **Refuse-list (v1 default):** K8s, microservices, service-mesh, Helm, Electron, native mobile, auto-deploy. Refusal lives at the Architect role boundary in the GSD phase loop (not after-the-fact; before any planning). The refusal text is friendly + names a `--production-ready` opt-in path.
6. **`--production-ready` flag semantics:** Adds K8s / observability / Sentry / migrations / healthchecks / rate-limiting / backup as **named ROADMAP phases** (not as scaffold code). Implementation: appends rows to the LLM-driven `/gsd-add-phase` invocation; produces `.planning/ROADMAP.md` entries, NOT files in the user app.
7. **Pinned Postgres image:** `postgres:18-alpine` (already in `scripts/scaffold_dispatch.py` line 58). Never `postgres:latest`.
8. **gh CLI version:** `gh` 2.90.0 verified on dev machine; minimum compatible declared in SKILL.md frontmatter to be set during Phase 6 (currently TBD per STATE.md).
9. **gitleaks version:** v8.30.1 (latest stable as of 2026-03-21) — pinned in `.pre-commit-config.yaml` for built repos. [VERIFIED: api.github.com/repos/gitleaks/gitleaks/releases/latest]
10. **Cross-platform support:** macOS / Linux / Windows. Bash scripts must be portable (POSIX-safe sed/grep/find or Python 3 stdlib). Windows-without-Docker handled via `--no-docker` flag (already shipped in Phase 2).
11. **State checkpoint extension:** Phase 6 adds new ALLOWED_FIELDS to `state_writer.py` following the Phase 3/4/5 additive pattern. New fields: `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`. NEVER added to REQUIRED_FIELDS — additive only.
12. **Composition rule:** OSBuilder NEVER hand-writes `package.json` / `tsconfig.json` / `Dockerfile`-internal-stages-from-scratch when a deterministic source exists. Dockerfile templates live under `assets/dockerfiles/` and are stamped post-scaffold the same way Phase 3 stamps `.env.example` and `compose.yaml`.
13. **Verification methodology:** Falsifiable, observable user behaviors per VER-01..04 (Phase 4). Phase 6 tests use a `tmp_path` "fake built app" tree + bash scripts that assert file presence + content patterns, plus a manual-UAT row for the "stranger reaches working app in ≤ 5 min" criterion that cannot be deterministically automated.

### Claude's Discretion

- **Plan count:** Estimated 5–6 plans (Wave 0 RED stubs + 4–5 Wave 1 plans by file ownership). Final count is the planner's call.
- **README runbook template structure:** Must include: title, one-line summary, Quick Start (cd / cp .env.example / install / run), Requirements, Configuration, Development, Tests sections. Section ordering and exact heading text are open.
- **Refusal copy text:** Must name `--production-ready` and explain *why* in one sentence (not just "no"). Exact wording is open. Recommend: 2–3 sentences max.
- **`assets/dockerfiles/` granularity:** Per-stack family (Node-pnpm, Python-uv, Python-pip) vs per-playbook (web, ai-service, cli). Recommend per-stack family — fewer files, more reuse, since Phase 7 adds more playbooks. Final call is the planner's.
- **CI workflow filename:** `ci.yml` recommended (community convention); `pull-request.yml` or `test.yml` also acceptable. Planner picks.
- **Where in the GSD phase loop the ship step lives:** Recommend new `phase_step == 11` (after Phase 5's `phase_step == 10` advance) for the FINAL phase only — NOT every phase. Triggered by `current_phase == gsd_phase_count + 1` (i.e., all phases done) or by an explicit `/osbuilder ship` command. Final call is the planner's.
- **Pre-commit framework vs raw git hook:** Recommend the `pre-commit` framework (industry standard, declarative `.pre-commit-config.yaml`, supports update workflow) over raw git hook (one-shot bash, hard to update, easier to forget). Final call is the planner's; rationale documented below.

### Deferred Ideas (OUT OF SCOPE)

- **Auto-deploy** (Vercel / Fly / Railway) — explicitly v2-DEP-01..03; never in v1.
- **Public repos by default** — locked private-by-default; `--public` is the only override.
- **Renovate / Dependabot config** — quality-of-life, not v1.
- **Branch protection / required reviewers / signed commits** — v2 (no API support gap; just scope).
- **Per-stack CI matrices** (Node 18/20/22 × Linux/macOS/Windows) — v1 ships ONE CI workflow per built repo (SCL-04 explicitly says "exactly one"); matrix expansion is opt-in via `--production-ready`.
- **Helm chart / k8s manifest / service-mesh config** — refused list (SCL-05); `--production-ready` adds them as ROADMAP phases, not files.
- **Automated `compose up` smoke test in CI** — out of scope (CI runtime cost + flake risk); README says how to run locally instead.
- **GitHub Pages / Vercel deploy preview hooks** — auto-deploy adjacent; v2.
- **Multi-platform Docker buildx images (`linux/amd64,linux/arm64`)** — v2 (single-platform `docker build` covers v1 dev-on-machine).
- **Renaming the existing `scripts/` shape** — additive only (per STATE.md "additive ALLOWED_FIELDS" rule).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SHIP-01 | OSBuilder creates a **private** GitHub repository via `gh repo create --private` after verification passes | New `scripts/gh_handoff.py` (referenced in SKILL.md line 87 as planned but not yet on disk); invokes `gh repo create --private --source=. --remote=origin --push`; verifies with `gh repo view --json visibility,nameWithOwner,sshUrl` returning `"PRIVATE"` |
| SHIP-02 | OSBuilder generates a README with a clone-and-run runbook | New `scripts/runbook_writer.py` + `assets/runbook-templates/<playbook>.md`; consumes `state.md` `playbook`, `project_path`, `stack_choices` to fill in stack-specific commands |
| SHIP-03 | `.gitignore` template prevents `.env`, secrets, build artifacts, platform cruft from being committed | New `assets/gitignore-templates/{node,python,desktop,common}.gitignore`; merged at scaffold time by `gh_handoff.py` (or extended `scaffold_dispatch.py`); composition rule: union of {common, language-specific} |
| SHIP-04 | A gitleaks pre-commit hook is installed in the built repo | New `assets/pre-commit-config.yaml.tmpl` pinned to `gitleaks` rev v8.30.1; new `assets/gitleaks.toml` (permissive starter with allowlist documentation); README runbook adds `pre-commit install` setup step (hooks not auto-installed on clone — this is the documented gotcha) |
| SHIP-05 | `gh` CLI auth state verified before push; auth-state-drift errors get friendly remediation | `gh_handoff.py` runs `gh auth status` (exit 0 = OK; exit 1 = drift); on drift, friendly_error.translate() emits "## GitHub login expired" with copy-paste `gh auth login --git-protocol https`; new dictionary entries added to `references/friendly-errors/dictionary.yaml` (Phase 5 baseline is 30 entries; Phase 6 grows to ~33–34) |
| SCL-01 | Default scaffold ships with env-based config (`.env.example` + `.env` in `.gitignore`) | `.env.example` already written by `scaffold_dispatch.py` line 126; Phase 6 extends to ALL playbooks (currently web only); `.gitignore` template MUST contain `.env` and `.env.*` (allowing `.env.example` via negative match `!.env.example`) |
| SCL-02 | Real database defaults: Postgres-via-compose for multi-user web; SQLite for single-user CLI | `state.md` field `app_type` already exists; Phase 6 adds a small dispatcher in `gh_handoff.py` (or `scaffold_dispatch.py`) that picks compose.yaml-with-postgres for `playbook=web` and SQLite-path config for `playbook=cli`; postgres pin is `postgres:18-alpine` (already in scaffold_dispatch.py line 58) |
| SCL-03 | Default scaffold ships with Dockerfile + `compose.yaml` (Compose v2) | `compose.yaml` already shipped (web playbook); new `assets/dockerfiles/{node-pnpm,python-uv}.Dockerfile` multi-stage templates; `.dockerfile` files copied + stamped post-scaffold; NO `version:` key (Compose v2 obsolete) |
| SCL-04 | ONE `.github/workflows/*.yml` with build + test on PR | New `assets/ci-workflows/{node,python}.yml.tmpl`; uses `actions/checkout@v6`, `actions/setup-node@v4`, `pnpm/action-setup@v4`; minimal — Ubuntu only, single Node version (20); `pnpm install && pnpm test` (or stack equivalent) |
| SCL-05 | OSBuilder refuses K8s / microservices / service-mesh / Helm in v1 default builds | Refusal lives at the Architect role in `gsd_driver.py` _role_for_step path (or new pre-planning gate); new `references/refuse-list.md` documenting the refusal text + the friendly explanation; refusal short-circuits before any planning happens; tested by passing a refusal-trigger spec and asserting state.md `last_failure` matches a documented refusal pattern |
| SCL-06 | `--production-ready` flag adds named ROADMAP phases (not scaffold code) | Flag plumbs through SKILL.md → state.md (new ALLOWED_FIELD `production_ready`) → `gh_handoff.py` (or new `scripts/production_phase_writer.py`) which emits `/gsd-add-phase` slash commands for each named upgrade (observability, migrations, healthchecks, secret manager, Sentry, rate limiting, backup); test: with flag, ROADMAP.md gains ≥7 new phase rows; without flag, ROADMAP.md is unchanged |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Private GitHub repo creation | `scripts/gh_handoff.py` (NEW) | `gh` CLI subprocess (external) | Script wraps `gh repo create --private --source=. --remote=origin --push`; verifies via `gh repo view --json visibility` |
| `gh auth status` preflight | `scripts/gh_handoff.py` (NEW) | `friendly_error.translate()` + `references/friendly-errors/dictionary.yaml` | Drift detection lives in gh_handoff; friendly-error dictionary translates raw `gh` errors to user-facing copy |
| README runbook generation | `scripts/runbook_writer.py` (NEW) | `assets/runbook-templates/<playbook>.md`; `state.md` reads | LLM-free templated stamping (placeholders filled from state.md); deterministic and testable |
| `.gitignore` composition | `scripts/gh_handoff.py` (NEW) — calls helper `_compose_gitignore()` | `assets/gitignore-templates/{common,node,python,desktop}.gitignore` | Union semantics: common + per-language; deterministic write at the same point Phase 3 stamps `.env.example` |
| gitleaks `.pre-commit-config.yaml` | `scripts/gh_handoff.py` (NEW) — calls helper `_install_gitleaks_hook()` | `assets/pre-commit-config.yaml.tmpl`, `assets/gitleaks.toml` | Stamp at same point as `.gitignore`; runbook tells user to run `pre-commit install` (hook activation is opt-in by design) |
| Dockerfile generation | `scripts/scaffold_dispatch.py` (EXTEND) — new `_write_dockerfile()` | `assets/dockerfiles/{node-pnpm,python-uv}.Dockerfile.tmpl` | Lives next to existing `_DB_TS` / `_COMPOSE_YAML` constants — same composition pattern |
| `compose.yaml` generation | `scripts/scaffold_dispatch.py` (existing line 55) | — | Already shipped in Phase 3; Phase 6 confirms NO `version:` key and pinned `postgres:18-alpine` |
| GitHub Actions CI workflow | `scripts/scaffold_dispatch.py` (EXTEND) — new `_write_ci_workflow()` | `assets/ci-workflows/{node,python}.yml.tmpl` | Stamp at same point as Dockerfile |
| Database choice (Postgres vs SQLite) | `scripts/scaffold_dispatch.py` — extend with `_pick_database()` reading state.md | `state.md` `playbook` + `app_type` fields | Pure function: web → postgres-compose; cli → sqlite-path; deterministic + testable |
| K8s/microservices refusal | `scripts/gsd_driver.py` (EXTEND PHASE_STEP_COMMANDS branching) | `references/refuse-list.md` (NEW) | Architect role intercepts; emits structured refusal via `friendly_error.translate()` + writes `last_failure` |
| `--production-ready` named-phase emission | `scripts/production_phase_writer.py` (NEW, optional — could fold into gh_handoff.py) | `/gsd-add-phase` slash command per named feature | Iterates a hardcoded list of 7 named features; emits one `/gsd-add-phase <name>` per feature ONLY when `state.md` `production_ready=true` |
| State checkpoint extension | `scripts/state_writer.py` (EXTEND ALLOWED_FIELDS) | — | Add `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`, `production_ready` to ALLOWED_FIELDS — Phase 3/4/5 additive pattern |
| Friendly-error dictionary expansion | `references/friendly-errors/dictionary.yaml` (EDIT) | — | Add 3–4 entries: `gh-auth-expired`, `gh-repo-name-collision`, `gh-not-installed`, `gitleaks-blocked-secret` |

---

## Summary

Phase 6 closes OSBuilder's loop: every successful build ends as a private GitHub repo with a runnable README, real config (env-based + DB), Docker artifacts, and one CI workflow — with gitleaks blocking secret leaks at commit time, and a documented refusal of K8s / microservices / Helm in default mode that points to `--production-ready` for opt-in.

The implementation lives entirely inside the OSBuilder skill (Python 3.13 stdlib + Markdown templates + bash where unavoidable). It does NOT alter the user's app code path beyond stamping new files at the existing scaffold-dispatch boundary; it does NOT add new third-party Python deps; it does NOT spawn long-running services. Phase 6 reuses every Phase-1..5 mechanism: `state_writer.py` ALLOWED_FIELDS extension, `friendly_error.translate()` routing, `gsd_driver.py` PHASE_STEP_COMMANDS dispatch, and the `assets/` template stamping pattern from `scaffold_dispatch.py`.

The work splits into four tracks that map cleanly to plans:

**Track A — `gh_handoff.py` (new, ~250 lines).** Wraps `gh auth status` preflight, `gh repo create --private --source=. --remote=origin --push`, and `gh repo view --json visibility` verification. Handles the four documented `gh` failure modes (not authenticated, expired token, name collision, network failure) by routing through `friendly_error.translate()`. Writes `repo_url` + `repo_visibility` + `gh_auth_status` to state.md. Idempotent: re-running on an already-pushed dir is a no-op (detects via `git remote -v`). Lives next to existing `gsd_driver.py` style (subprocess.run with shell=False, pure stdlib).

**Track B — Built-app scaffold extensions (`assets/` + `scaffold_dispatch.py` extension).** Adds Dockerfile templates per stack family (Node-pnpm, Python-uv), a CI workflow per stack family, a `.gitignore` template per stack family + common, and a gitleaks `.pre-commit-config.yaml` template. All stamped at the same boundary where Phase 3's `.env.example` and `compose.yaml` are already stamped. Composition pattern: `_DB_TS` / `_COMPOSE_YAML` Python constants → templates promoted to `assets/` files because they're now bigger and more numerous; `scaffold_dispatch.py` learns to read them. The Postgres-vs-SQLite decision becomes a pure function reading `state.md` `playbook` + `app_type`.

**Track C — README runbook generator (`runbook_writer.py` + templates).** Stamps a per-playbook README with placeholders filled from `state.md` (project name, stack choices, run commands). The README contains: title, summary, Quick Start (clone-and-run in ≤ 5 commands), Requirements, Configuration, Development, Tests, and a "How OSBuilder built this" section (Phase 5 baseline; Phase 6 extends to also reference the dev-team metaphor of who-built-what for the user's app). LLM-free generation — deterministic templated stamping. The "stranger reaches working app in ≤ 5 min" criterion is verified by manual UAT (cannot be deterministically automated; documented as a manual-only test row in Validation Architecture).

**Track D — Refusal mechanics + `--production-ready` flag (`gsd_driver.py` extension + `production_phase_writer.py`).** A new gate at the Architect role boundary inspects derived spec / state.md for refuse-list keywords ("kubernetes", "k8s", "microservices", "helm", "service mesh"); on hit, emits a structured refusal via `friendly_error.translate()` and writes `last_failure` with `refused: <topic>`. The `--production-ready` flag plumbs through SKILL.md → state.md `production_ready=true` → `production_phase_writer.py` which emits `/gsd-add-phase observability`, `/gsd-add-phase migrations`, etc. (7 named phases) — appending to the active ROADMAP, not generating scaffold code.

**Wave 0** (test infrastructure) drops ~12–18 RED stubs across `test_gh_handoff.py`, `test_runbook_writer.py`, `test_scaffold_extensions.py`, `test_refusal.py`, and `test_production_ready.py`. **Wave 1** (parallel-safe) implements the four tracks. **Wave 2** wires everything into `gsd_driver.py` PHASE_STEP_COMMANDS as the new step 11 (final-phase ship step) and adds friendly-error dictionary entries.

**Primary recommendation:** Build Wave 0 first (test infrastructure + state_writer.py ALLOWED_FIELDS extension). Then Wave 1 splits into 4 plans that can be implemented in parallel by file ownership (gh_handoff.py owns Track A, scaffold_dispatch.py-extension + assets/ own Track B, runbook_writer.py owns Track C, gsd_driver.py-extension + production_phase_writer.py own Track D). Wave 2 is the integration plan.

---

## Standard Stack

### Phase 6 New Code (OSBuilder itself)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.13 | All new modules — `gh_handoff.py`, `runbook_writer.py`, `production_phase_writer.py`, scaffold_dispatch.py extensions | No new deps allowed (locked); stdlib has every primitive needed (`subprocess.run`, `pathlib.Path`, `re`, `json`, `argparse`) |
| `subprocess.run(shell=False)` | built-in | All `gh` and `git` invocations; never `shell=True` (Phase 3/4 security pattern) | Established project pattern; no shell injection surface |
| `pathlib.Path` | built-in | All filesystem paths in new modules | Existing project convention (state_writer.py, gsd_driver.py, scaffold_dispatch.py) |
| `re` | built-in | gitignore composition (de-dup); refusal-pattern matching | Stdlib regex; first-match semantics |
| `json` | built-in | `gh repo view --json visibility,nameWithOwner,sshUrl` parsing | Stdlib; matches Phase 4 registry_verify pattern |
| `pytest` | 9.0.2 (existing) | Test suite extension: `test_gh_handoff.py`, `test_runbook_writer.py`, `test_scaffold_extensions.py`, `test_refusal.py`, `test_production_ready.py` | Existing infrastructure |

### Phase 6 New Templates (in `assets/` — for built apps)

| File | Source | Purpose |
|------|--------|---------|
| `assets/gitignore-templates/common.gitignore` | Hand-curated; based on github.com/github/gitignore | Lines for `.env`, `.env.*`, `!.env.example`, `*.log`, `.DS_Store`, `Thumbs.db`, `desktop.ini`, `.vscode/`, `.idea/`, OS cruft, IDE cruft |
| `assets/gitignore-templates/node.gitignore` | Hand-curated; based on github.com/github/gitignore/blob/main/Node.gitignore | `node_modules/`, `dist/`, `build/`, `.next/`, `.turbo/`, `coverage/`, `*.tsbuildinfo` |
| `assets/gitignore-templates/python.gitignore` | Hand-curated; based on github.com/github/gitignore/blob/main/Python.gitignore | `__pycache__/`, `*.pyc`, `*.egg-info/`, `.venv/`, `venv/`, `.pytest_cache/`, `.mypy_cache/`, `dist/`, `build/`, `*.egg` |
| `assets/dockerfiles/node-pnpm.Dockerfile.tmpl` | Multi-stage Node 20-alpine | Standard build/run separation; uses `corepack` for pnpm |
| `assets/dockerfiles/python-uv.Dockerfile.tmpl` | Multi-stage `python:3.13-slim` | Standard build/run separation; uses `uv` (already established for AI-service playbook) |
| `assets/ci-workflows/node.yml.tmpl` | actions/checkout@v6, actions/setup-node@v4, pnpm/action-setup@v4 | Single-stack PR test workflow |
| `assets/ci-workflows/python.yml.tmpl` | actions/checkout@v6, actions/setup-python@v6, astral-sh/setup-uv@v6 | Single-stack PR test workflow |
| `assets/runbook-templates/web.md` | Markdown with `{{project_name}}` / `{{run_command}}` placeholders | LLM-free deterministic stamping |
| `assets/runbook-templates/cli.md` | Markdown with `{{project_name}}` / `{{install_command}}` placeholders | (Phase 7 will add ai-service, desktop, hub-platform) |
| `assets/pre-commit-config.yaml.tmpl` | gitleaks rev v8.30.1 | Pinned; used by all built repos |
| `assets/gitleaks.toml.tmpl` | Permissive starter | Allows `.env.example` placeholders; documents how to allowlist false positives |
| `references/refuse-list.md` | New | The text OSBuilder emits when refusing K8s/microservices/Helm; cross-referenced by `gsd_driver.py` |

### External Tool Dependencies (verified locally on dev machine 2026-05-01)

| Tool | Version | Source | Required For |
|------|---------|--------|--------------|
| `gh` (GitHub CLI) | 2.90.0 | `/opt/homebrew/bin/gh` | SHIP-01, SHIP-05 |
| `git` | 2.50.1 (Apple Git-155) | `/usr/bin/git` | SHIP-01 |
| `gitleaks` | 8.30.1 | `/opt/homebrew/bin/gitleaks` | SHIP-04 (binary mode); also pinned in pre-commit-config |
| `pre-commit` (Python framework) | NOT installed locally | NOT REQUIRED at OSBuilder runtime; required IN BUILT REPO at user time | SHIP-04 (framework mode) |
| Docker / Compose v2 | NOT VERIFIED in this session (assumed present from Phase 2 preflight) | Phase 2 `preflight_check.py` | SCL-02 (Postgres compose), SCL-03 |

[VERIFIED: `gh --version` → 2.90.0 (2026-04-16); `gitleaks version` → 8.30.1; `git --version` → 2.50.1 — all from local Bash on 2026-05-01]

### Documentation-Lookup Verification

- **`gh repo create` flags** verified via `gh repo create --help` on dev machine 2026-05-01: `--private`, `--source string`, `--push`, `--remote string`, `--add-readme`, `--gitignore string`, `--license string` are all current. [VERIFIED: gh 2.90.0 local help output]
- **`compose.yaml` priority** verified via docs.docker.com/compose/intro/compose-application-model: Compose looks for `compose.yaml` (preferred), `compose.yml`, `docker-compose.yaml`, `docker-compose.yml` in priority order. [VERIFIED: docs.docker.com 2026-05-01]
- **`compose.yaml` `version:` key obsolete** confirmed by docker/docs Issue #13933 + Compose Specification (the `version:` field has been deprecated since 2023; modern Compose ignores it with a warning). [VERIFIED: docs.docker.com/reference/compose-file]
- **gitleaks pre-commit hook** repo: `https://github.com/gitleaks/gitleaks` with `.pre-commit-hooks.yaml` exposing hook id `gitleaks`. Latest stable rev `v8.30.1` (published 2026-03-21). [VERIFIED: api.github.com/repos/gitleaks/gitleaks/releases/latest 2026-05-01]
- **GitHub Actions versions** verified via current release tags: `actions/checkout@v6`, `actions/setup-node@v4`, `pnpm/action-setup@v4` (search results 2026-05-01). [CITED: github.com/actions/setup-node, github.com/pnpm/action-setup]
- **Postgres image pin** `postgres:18-alpine` already used in `scripts/scaffold_dispatch.py` line 58 — Phase 6 keeps this pin. [VERIFIED: direct file read 2026-05-01]

### Alternatives Considered

| Instead of | Could Use | Tradeoff | Recommendation |
|------------|-----------|----------|----------------|
| `pre-commit` framework + `.pre-commit-config.yaml` | Raw git hook (`.git/hooks/pre-commit` shell script) | Raw hook is simpler (no framework) but harder to update, easy to forget on clone, no version pinning | **Use pre-commit framework** — industry standard; declarative; supports update; gitleaks ships official `.pre-commit-hooks.yaml` upstream |
| `gh repo create --source=. --push` (single command) | Manual `git init` + `git remote add` + `gh repo create` + `git push` | Single command is atomic; manual flow is more debuggable but easier to leave half-done | **Use `--source=. --push`** — atomic, reduces failure surface, supported since `gh` 2.0 |
| `compose.yaml` (Compose v2 canonical) | `docker-compose.yml` (Compose v1 legacy) | Both work; v1 filename is widely recognized but Compose Specification names v2 canonical | **Use `compose.yaml`** — matches SCL-03 success criterion verbatim; future-proof |
| Multi-stage Dockerfile | Single-stage Dockerfile | Multi-stage gives smaller runtime image but more complex to read | **Multi-stage** — modern best practice; runtime image excludes build deps |
| `actions/setup-node@v4` + `pnpm/action-setup@v4` | `actions/setup-node@v4` with `cache: 'pnpm'` only | Both work; `pnpm/action-setup` must precede `setup-node` so the `cache: 'pnpm'` works | **Use both, in that order** — per pnpm docs: pnpm setup must precede Node setup for cache to engage |
| Per-stack-family Dockerfile templates | Per-playbook Dockerfile templates | Per-stack-family = fewer files, more reuse; per-playbook = more specific | **Per-stack-family** — Phase 7 adds more playbooks but stack families stay small (Node-pnpm covers web, hub; Python-uv covers ai-service, cli) |
| Templated README runbook with placeholders | LLM-generated README via `/gsd-docs-update` | Phase 5 Plan 05-05 already wires `/gsd-docs-update` for the "How OSBuilder built this" section; runbook is deterministic content (clone, install, run) | **Templated runbook for the deterministic Quick Start section; LLM-augmented for the dev-team-metaphor section** — composition is the pattern |
| Refusal at the Architect role | Refusal at SKILL.md user-input parsing | Earlier refusal = less wasted work; but state.md is the single source of truth | **Architect-role refusal in `gsd_driver.py`** — uses the existing failure_classifier + state.md mechanisms; matches Phase 4 escalation pattern |

### Installation (no new packages)

All work uses Python 3.13 stdlib + existing pytest + new Markdown templates + new bash scripts. No `pip install`. No `npm install` for OSBuilder itself. Built apps (the user's generated repos) install their own deps per their stack — that's separate.

### Version verification

```bash
python3 --version     # ≥ 3.13 (preflight installer ensures)
gh --version          # ≥ 2.0 (--source=. --push requires)
git --version         # any modern version
gitleaks version      # ≥ 8.0 (pinned to v8.30.1 in pre-commit-config.tmpl)
docker compose version  # v2 (compose.yaml canonical filename support)
```

---

## Architecture Patterns

### System Architecture Diagram

```
PHASE 5 OUTPUT
  │  state.md fields populated:
  │    goal, app_type, playbook, current_phase, phase_step,
  │    project_path, stack_choices, mode, tutor_enabled,
  │    humanizer_score, build_log_path
  │  /gsd-verify-work passed → phase_step=10 → phase advanced
  │  README.md exists in project_path (humanizer-checked)
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/gsd_driver.py — Phase loop state machine (EXTENDED)    │
│                                                                  │
│  emit_next_command():                                            │
│    if current_phase > gsd_phase_count:  ← all phases done       │
│      goto SHIP STEP                                             │
│                                                                  │
│  PHASE_STEP_COMMANDS new entry:                                  │
│    11: ship-step → handled in-line by _run_ship_step()          │
│                                                                  │
│  Plus: Architect-role refusal gate (NEW)                        │
│    Inspects derived_spec.md / spec for refuse-list keywords     │
│    On hit: emit refusal + last_failure="refused: <topic>"       │
└──────────────┬─────────────────────────────────────┬─────────────┘
               │                                     │
               │ ship-step                           │ refusal-gate
               ▼                                     ▼
┌─────────────────────────────────────────┐  ┌────────────────────────┐
│  scripts/gh_handoff.py (NEW)            │  │  references/refuse-    │
│                                         │  │  list.md (NEW)         │
│  Public API:                            │  │                        │
│    ship(project_dir, project_root)      │  │  Refusal pattern list  │
│      → preflight gh auth                │  │    + friendly copy     │
│      → write .gitignore (composed)      │  │                        │
│      → write .pre-commit-config.yaml    │  │  Cross-referenced by   │
│      → write Dockerfile (per stack)     │  │  gsd_driver.py refusal │
│      → write CI workflow                │  │  gate                  │
│      → git init + commit + branch=main  │  │                        │
│      → gh repo create --private \       │  └────────────────────────┘
│              --source=. --remote=origin\│
│              --push                     │  ┌────────────────────────┐
│      → gh repo view --json visibility   │  │  scripts/runbook_      │
│      → write state.md repo_url + viz    │  │  writer.py (NEW)       │
│                                         │  │                        │
│  Failure modes (each via friendly_error)│  │  Public API:           │
│    1. gh not installed                  │  │    write_readme(state) │
│    2. gh auth not authenticated         │  │      → reads playbook  │
│    3. gh auth token expired             │  │      → reads stack     │
│    4. repo name collision (HTTP 422)    │  │      → loads template  │
│    5. network failure                   │  │      → fills placeholdr│
│                                         │  │      → atomic_write    │
│  Persists to state.md:                  │  │                        │
│    repo_visibility=PRIVATE              │  │  Templates from:       │
│    repo_url=git@github.com:user/x.git   │  │    assets/runbook-     │
│    gh_auth_status=ok                    │  │    templates/<pb>.md   │
│    pre_commit_installed=true            │  └────────────────────────┘
└─────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/scaffold_dispatch.py (EXTENDED — Phase 6 additions)    │
│                                                                  │
│  Existing: write_drizzle_files() writes 4 files post-scaffold:  │
│    db.ts, drizzle.config.ts, .env.example, compose.yaml         │
│                                                                  │
│  NEW Phase 6:                                                    │
│    _write_dockerfile(project_dir, stack_family)                  │
│      → reads assets/dockerfiles/<family>.Dockerfile.tmpl        │
│      → atomic_write to project_dir/Dockerfile                   │
│                                                                  │
│    _write_ci_workflow(project_dir, stack_family)                │
│      → reads assets/ci-workflows/<family>.yml.tmpl              │
│      → atomic_write to project_dir/.github/workflows/ci.yml     │
│                                                                  │
│    _pick_database(playbook, app_type) → "postgres" | "sqlite"   │
│      → web → postgres (compose.yaml stamped)                    │
│      → cli → sqlite (path config in app)                        │
│      → ai-service → postgres (multi-user expected)              │
│                                                                  │
│  All called at the SAME boundary as write_drizzle_files() —     │
│  no new dispatch points in scaffold_web().                      │
└──────────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/production_phase_writer.py (NEW, optional)             │
│                                                                  │
│  Reads state.md production_ready field.                          │
│  If true: emits 7 /gsd-add-phase slash commands:                │
│    1. observability (logs/metrics/traces via OpenTelemetry)     │
│    2. automated migrations (Drizzle Kit / Alembic)              │
│    3. healthcheck endpoints                                      │
│    4. secret manager integration                                 │
│    5. Sentry error tracking                                      │
│    6. rate limiting                                              │
│    7. backup strategy                                            │
│                                                                  │
│  Each command appends a row to .planning/ROADMAP.md             │
│  (handled by /gsd-add-phase, not by this script).               │
│                                                                  │
│  CRITICAL: writes ROADMAP rows, NEVER touches user app code.    │
└──────────────────────────────────────────────────────────────────┘
               │
               ▼
            BUILT REPO ON DISK + PRIVATE GITHUB MIRROR
              .gitignore, .env.example (.env gitignored)
              Dockerfile, compose.yaml (or no compose for CLI/SQLite)
              .github/workflows/ci.yml
              .pre-commit-config.yaml + .gitleaks.toml (hooks NOT yet
                installed; runbook says `pre-commit install`)
              README.md (Quick Start + How OSBuilder built this)
              git remote origin = git@github.com:<user>/<repo>.git
              gh repo view --json visibility → "PRIVATE"
```

### Recommended Project Structure (OSBuilder skill — additions only)

```
~/.claude/skills/osbuilder/
├── SKILL.md                         (existing — line 87 already references gh_handoff.py)
├── scripts/
│   ├── gh_handoff.py                (NEW — Track A; ~250 lines)
│   ├── runbook_writer.py            (NEW — Track C; ~150 lines)
│   ├── production_phase_writer.py   (NEW — Track D; ~80 lines)
│   ├── scaffold_dispatch.py         (EXTEND — _write_dockerfile, _write_ci_workflow, _pick_database)
│   ├── gsd_driver.py                (EXTEND — refusal gate; new step 11; _run_ship_step)
│   ├── state_writer.py              (EXTEND — ALLOWED_FIELDS adds 5 fields)
│   └── tests/
│       ├── test_gh_handoff.py       (NEW)
│       ├── test_runbook_writer.py   (NEW)
│       ├── test_scaffold_extensions.py  (NEW)
│       ├── test_refusal.py          (NEW)
│       └── test_production_ready.py (NEW)
├── assets/
│   ├── gitignore-templates/
│   │   ├── common.gitignore         (NEW)
│   │   ├── node.gitignore           (NEW)
│   │   ├── python.gitignore         (NEW)
│   │   └── desktop.gitignore        (NEW — Tauri/Electron pattern; Phase 7 may extend)
│   ├── dockerfiles/
│   │   ├── node-pnpm.Dockerfile.tmpl    (NEW — multi-stage)
│   │   └── python-uv.Dockerfile.tmpl    (NEW — multi-stage)
│   ├── ci-workflows/
│   │   ├── node.yml.tmpl            (NEW)
│   │   └── python.yml.tmpl          (NEW)
│   ├── runbook-templates/
│   │   ├── web.md                   (NEW)
│   │   └── cli.md                   (NEW; Phase 7 adds others)
│   ├── pre-commit-config.yaml.tmpl  (NEW)
│   └── gitleaks.toml.tmpl           (NEW — permissive starter)
└── references/
    ├── refuse-list.md               (NEW — refusal copy + reasons)
    └── friendly-errors/
        └── dictionary.yaml          (EDIT — add 4 entries)
```

### Pattern 1: gh_handoff.ship() — atomic create + push

**What:** Single function that takes a built project on disk and ends with it pushed to a private GitHub repo, with state.md fields written.
**When to use:** Final step of every successful OSBuilder build (gsd_driver.py phase_step == 11, only when current_phase > gsd_phase_count).
**Example:**

```python
# scripts/gh_handoff.py — Track A core
# Source: gh CLI 2.90.0 docs (gh repo create --help, verified 2026-05-01)
import subprocess
import sys
from pathlib import Path
import json

def ship(project_dir: Path, project_root: Path, *, private: bool = True) -> int:
    """SHIP-01..05: full ship pipeline. Returns 0 on success, 1 on failure.

    Idempotent: if `git remote get-url origin` already returns a github URL,
    the function exits 0 without re-creating the repo.
    """
    # 1. SHIP-05 — preflight: gh auth status
    auth = subprocess.run(["gh", "auth", "status"], shell=False, capture_output=True, text=True)
    if auth.returncode != 0:
        # Friendly-error route — NEW dictionary entry "gh-auth-expired" or "gh-auth-not-logged-in"
        _emit_friendly_error("gh-auth-status-failed", auth.stderr)
        return 1

    # 2. SHIP-03 + SHIP-04 — stamp .gitignore + .pre-commit-config.yaml + .gitleaks.toml
    _compose_gitignore(project_dir)
    _install_gitleaks_hook(project_dir)

    # 3. git init + commit + branch=main (gh default branch from user account)
    if not (project_dir / ".git").is_dir():
        subprocess.run(["git", "init", "-b", "main"], cwd=str(project_dir), check=True, shell=False)
    subprocess.run(["git", "add", "-A"], cwd=str(project_dir), check=True, shell=False)
    # First commit only if there are changes; idempotent on re-run
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(project_dir),
        capture_output=True, text=True, check=True, shell=False,
    )
    if status.stdout.strip():
        subprocess.run(
            ["git", "commit", "-m", "chore: initial scaffold by OSBuilder"],
            cwd=str(project_dir), check=True, shell=False,
        )

    # 4. SHIP-01 — gh repo create (idempotent: skip if remote exists)
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(project_dir), capture_output=True, text=True, shell=False,
    )
    if remote.returncode != 0:
        visibility_flag = "--private" if private else "--public"
        result = subprocess.run(
            ["gh", "repo", "create",
             "--source=" + str(project_dir),
             "--remote=origin",
             "--push",
             visibility_flag],
            shell=False, capture_output=True, text=True,
        )
        if result.returncode != 0:
            _emit_friendly_error("gh-repo-create-failed", result.stderr)
            return 1

    # 5. Verify visibility
    view = subprocess.run(
        ["gh", "repo", "view", "--json", "visibility,nameWithOwner,sshUrl"],
        cwd=str(project_dir), capture_output=True, text=True, shell=False,
    )
    if view.returncode != 0:
        _emit_friendly_error("gh-repo-view-failed", view.stderr)
        return 1
    repo_info = json.loads(view.stdout)
    if repo_info.get("visibility") not in ("PRIVATE", "PUBLIC"):
        _emit_friendly_error("gh-repo-visibility-unknown", view.stdout)
        return 1

    # 6. Persist to state.md (via state_writer.py subprocess — same pattern as
    #    gsd_driver.py _write_field)
    _write_state_field(project_root, "repo_visibility", repo_info["visibility"])
    _write_state_field(project_root, "repo_url", repo_info["sshUrl"])
    _write_state_field(project_root, "gh_auth_status", "ok")
    return 0
```

### Pattern 2: gitleaks pre-commit config

**What:** A `.pre-commit-config.yaml` pinned to gitleaks v8.30.1 + a permissive starter `.gitleaks.toml`.
**When to use:** Stamped into every built repo by `gh_handoff._install_gitleaks_hook()`.
**Example:**

```yaml
# assets/pre-commit-config.yaml.tmpl
# Source: github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml (verified 2026-05-01)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

```toml
# assets/gitleaks.toml.tmpl
# Permissive starter — extend with [[allowlist]] entries as false positives surface.
# Source: github.com/gitleaks/gitleaks#configuration (verified 2026-05-01)
title = "OSBuilder default gitleaks config"

# Use upstream defaults (no [extend.path] override).
# Project-specific allowlist:
[allowlist]
description = "Files that legitimately contain pattern-matching strings"
paths = [
    '''(.*?)\.env\.example$''',
    '''README\.md$''',
    '''docs/.*\.md$''',
]
```

**README runbook reminder:** Hooks are NOT auto-installed on clone. The runbook MUST include:

```bash
# After clone, before first commit:
pip install pre-commit  # or: brew install pre-commit
pre-commit install      # registers .git/hooks/pre-commit
```

### Pattern 3: compose.yaml (already shipped — Phase 6 confirms shape)

```yaml
# assets/compose-templates/web.yaml — already in scripts/scaffold_dispatch.py line 55
# NO `version:` key (Compose v2 obsolete)
# Source: docs.docker.com/compose/intro/compose-application-model (verified 2026-05-01)
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

### Pattern 4: GitHub Actions CI (Node-pnpm)

```yaml
# assets/ci-workflows/node.yml.tmpl
# Source: github.com/pnpm/action-setup README, github.com/actions/setup-node (verified 2026-05-01)
name: Test on PR

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: pnpm/action-setup@v4
        with:
          version: 10

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm test
```

CRITICAL ORDER NOTE: `pnpm/action-setup` MUST precede `actions/setup-node` so the `cache: 'pnpm'` directive engages. Reversed order silently breaks caching. [VERIFIED: pnpm/action-setup README]

### Pattern 5: Multi-stage Dockerfile (Node-pnpm)

```dockerfile
# assets/dockerfiles/node-pnpm.Dockerfile.tmpl
# Source: docs.docker.com/build/building/multi-stage (verified 2026-05-01)

# ---- builder ----
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.33.2 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# ---- runtime ----
FROM node:20-alpine AS runtime
WORKDIR /app
RUN corepack enable
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["pnpm", "start"]
```

### Pattern 6: Refusal mechanics

**What:** When user spec contains refuse-list keywords, the Architect role short-circuits planning with a structured refusal.
**When to use:** Architect step (`phase_step == 1` /gsd-plan-phase boundary) reads `derived_spec.md` for keywords; on hit, refuses before any plan is written.
**Example:**

```python
# scripts/gsd_driver.py — Phase 6 extension
REFUSE_KEYWORDS = (
    "kubernetes", "k8s", "helm", "service mesh",
    "service-mesh", "microservice", "microservices",
    "istio", "linkerd", "consul",
)

def _check_refuse_list(project_root: Path, state: dict) -> bool:
    """SCL-05: refusal gate. Returns True if request is refused.

    Reads derived_spec.md (LLM intake output) and last_failure to detect refuse
    triggers. On hit: writes last_failure='refused: <topic>', emits friendly
    refusal, returns True (caller must NOT advance phase_step).

    The refusal copy is sourced from references/refuse-list.md verbatim.
    """
    # Skip if production_ready=true (the flag bypasses refusal)
    if state.get("production_ready", "false") == "true":
        return False
    spec_path = project_root / ".planning" / "osbuilder" / "derived_spec.md"
    if not spec_path.exists():
        return False
    spec = spec_path.read_text(encoding="utf-8").lower()
    for kw in REFUSE_KEYWORDS:
        if kw in spec:
            _write_field(project_root, "last_failure", f"refused: {kw}")
            _emit("architect", "refusal", "fail", detail=f"detected '{kw}' in spec")
            sys.stderr.write(_load_refusal_copy(kw))
            return True
    return False
```

### Anti-Patterns to Avoid

- **`shell=True` in subprocess.run.** Forbidden by Phase 4's locked decision (T-04-02-03). Always pass list[str] form.
- **Embedding `version:` in `compose.yaml`.** Compose v2 deprecated this key in 2023; modern Compose ignores it with a warning.
- **`gh repo create` without `--private` in default mode.** Even with `--public` flag absent, omitting `--private` lets `gh` use account default which may be public. Always pass the explicit visibility flag.
- **`actions/setup-node@v4` before `pnpm/action-setup@v4`.** Order matters; reversed silently breaks pnpm cache.
- **Auto-installing pre-commit hooks during scaffold.** Hooks live in user's `.git/hooks/` (not in the cloned repo); auto-installing during scaffold doesn't help users who clone later. Documented in README; user runs `pre-commit install` themselves.
- **`postgres:latest` in compose.yaml.** Locked decision: use `postgres:18-alpine`. Latest tag drift is a Phase 6 anti-pattern.
- **Hand-writing the `Dockerfile` in Python f-strings.** Use template files in `assets/dockerfiles/` with placeholder substitution; same pattern as `_DB_TS` etc but promoted to files because templates are bigger and used per-stack-family.
- **Using `--clone` with `gh repo create`.** Creates duplicate copy of repo; user already has the working tree. Use `--source=. --push` instead.
- **Refusing K8s after planning has produced files.** Refuse before any planning; don't waste cycles writing then deleting.
- **Newline-injection in `state_writer.write --value`.** state_writer.py rejects newlines and `..` already (line 64-69 _check_value_safe). Phase 6 must respect this — repo URLs are safe by construction (gh outputs single-line JSON), but any user-input-derived value MUST round-trip through state_writer's existing validation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secret-pattern detection | A regex of stripe / openai / aws keys | `gitleaks` | 100+ patterns maintained upstream; supports custom rules; pre-commit integration is one config file |
| `git remote add` + `git push` orchestration | Hand-rolled `subprocess.run(["git", ...])` chains | `gh repo create --source=. --push` | Atomic; handles edge cases (already-init'd, name collision); supported since gh 2.0 |
| Pre-commit hook framework | Custom `.git/hooks/pre-commit` shell script | `pre-commit` framework + `.pre-commit-config.yaml` | Industry standard; declarative; supports update workflow; gitleaks ships official upstream config |
| Postgres container management | Manual `docker run` commands in README | `compose.yaml` + `docker compose up -d` | Reproducible; handles networking + volumes + restart policy; one command |
| Multi-stage Dockerfile | Single-stage with `RUN cleanup` after build | Multi-stage `FROM ... AS builder` then `FROM ... AS runtime` | Smaller runtime image; build deps excluded from production layer |
| GitHub Actions caching for pnpm | Manual `actions/cache@v4` with hash keys | `actions/setup-node@v4` with `cache: 'pnpm'` | Built-in; respects pnpm-lock.yaml; pnpm setup must precede |
| `.gitignore` content | Per-project hand-curated lists | github.com/github/gitignore canonical templates (vendored as `assets/gitignore-templates/`) | Maintained upstream; covers OS / IDE / language cruft we'd miss |
| README structure | Free-form generation | Templated runbook with placeholders + LLM augmentation for the dev-team-metaphor section | Deterministic Quick Start (which is most of the SHIP-02 success criterion) + LLM polish for the explanation section |
| Refusal-text generation | LLM each time | Static `references/refuse-list.md` referenced by gsd_driver.py | Deterministic; testable; cheap (no LLM call) |
| Postgres-vs-SQLite choice logic | Hand-rolled per playbook | A 5-line `_pick_database(playbook, app_type)` pure function | Deterministic; testable; rule lives in one place |

**Key insight:** Phase 6 is mostly composition of EXISTING tools (`gh`, `git`, `gitleaks`, Compose v2, GitHub Actions, pre-commit framework). The OSBuilder code is glue: it wraps these tools, stamps templates that point to them, and translates their failure modes through `friendly_error.translate()`. The refusal mechanics are the only piece without an obvious upstream — and even there, the refusal *text* lives in a Markdown reference file, not in code.

---

## Common Pitfalls

### Pitfall 1: `gh auth status` returns 0 even when token is for a different account
**What goes wrong:** `gh auth status` exits 0 if any token is configured. Pushing to a repo created under that account silently uses the configured account, even if the user expected a different account.
**Why it happens:** `gh` doesn't know which account the user "intended."
**How to avoid:** Capture `gh auth status` stdout and parse the active account; show it in tutor-mode output before `gh repo create` runs ("OSBuilder will create this repo under account `octocat` — proceed? [Y/n]"). For v1 default mode, the locked decision is "use whatever account `gh auth status` says is active" — non-interactive.
**Warning signs:** User says "I have two GitHub accounts" — flag for documentation.

### Pitfall 2: Pre-commit hooks not auto-installed on clone
**What goes wrong:** User clones the OSBuilder-built repo, makes a commit, and a real secret gets committed because `.git/hooks/pre-commit` doesn't exist on the cloned machine.
**Why it happens:** Git hooks live in `.git/hooks/`, which is NOT under version control by design. Even though `.pre-commit-config.yaml` is in the repo, no hook is installed until the user runs `pre-commit install`.
**How to avoid:** README runbook must include `pre-commit install` as a Quick Start step. Recommend: include a `make setup` or `bash scripts/setup.sh` one-liner in the built repo that runs `pre-commit install` (and any other clone-time setup).
**Warning signs:** A built repo's README skips the `pre-commit install` line; a built repo passes a sample-secret commit on a fresh clone.

### Pitfall 3: `compose.yaml` `version:` key triggers warning on modern Compose
**What goes wrong:** Older templates include `version: '3.8'` at the top of compose.yaml; Compose v2 ignores it and prints a deprecation warning to user output, eroding trust.
**Why it happens:** Tutorials and Stack Overflow answers from 2019–2022 still include the version key.
**How to avoid:** All Phase 6 compose.yaml templates MUST omit `version:`. Test by `grep -E "^version:" compose.yaml` returning empty.
**Warning signs:** Build output contains `WARN[0000] /path/compose.yaml: the attribute 'version' is obsolete` — this is the explicit failure mode.

### Pitfall 4: `gh repo create` name collision
**What goes wrong:** A repo with that name already exists on the user's account; `gh repo create` exits non-zero with `HTTP 422: name already exists on this account`.
**Why it happens:** OSBuilder uses the project directory name; if the user has built a same-named repo before, collision.
**How to avoid:** On HTTP 422, friendly-error catches and offers: (a) suggest `<name>-2`, (b) prompt user for new name, (c) push to existing repo via `git remote add origin git@github.com:user/<existing>.git`. Default mode picks (a). Friendly-error dictionary entry `gh-repo-name-collision`.
**Warning signs:** `gh repo create` exit 1 with stderr containing `already exists on this account`.

### Pitfall 5: macOS vs Linux `sed` / `grep` portability
**What goes wrong:** BSD sed (macOS default) and GNU sed (Linux) have different `-i` flag semantics. A script that works on macOS dev machine breaks on the user's Linux clone OR vice versa.
**Why it happens:** Different POSIX implementations.
**How to avoid:** Phase 6 uses Python 3.13 stdlib for any string-mutation logic — NOT shell sed/grep. Bash scripts in built repos (e.g., setup.sh) use only POSIX-portable constructs OR explicitly require `bash` 4+ in shebang.
**Warning signs:** A script with `sed -i '' ...` (macOS BSD pattern) running on Linux fails with `unrecognized option`.

### Pitfall 6: gitleaks blocks `.env.example` placeholder values
**What goes wrong:** A real-looking placeholder (`DATABASE_URL=postgresql://user:password@localhost/db`) in `.env.example` triggers gitleaks; commit blocked.
**Why it happens:** gitleaks's default rules match anything that looks like a credential.
**How to avoid:** `.gitleaks.toml.tmpl` has `[allowlist] paths = ['''(.*?)\.env\.example$''']`. Test with the existing `_ENV_EXAMPLE` content (`DATABASE_URL=postgresql://myapp:myapp@localhost:5432/myapp`) — must not be blocked.
**Warning signs:** First commit on a fresh clone fails with gitleaks rule hit on `.env.example`.

### Pitfall 7: `state_writer.write --value` rejects values with newlines or `..`
**What goes wrong:** A `gh repo view --json sshUrl` output that somehow contains a newline (shouldn't happen, but defensively) crashes when written to state.md.
**Why it happens:** state_writer.py line 64-69 enforces `_check_value_safe`.
**How to avoid:** Sanitize before write — `value.strip().replace("\n", " ").replace("..", "[parent]")` or fail loudly. Use the existing `_write_field` helper from gsd_driver.py which already treats failures appropriately.
**Warning signs:** `OSBuilder: --value cannot contain newline characters.` SystemExit during ship step.

### Pitfall 8: Default branch name is `master` on the user's machine
**What goes wrong:** `git init` defaults to `main` on git ≥ 2.28, but older installations or git configured with `init.defaultBranch=master` produce a `master` branch. `gh repo view` then shows the user a default-branch mismatch with GitHub's account default of `main`.
**Why it happens:** Git config drift.
**How to avoid:** Always use `git init -b main` explicitly. Test: `git symbolic-ref HEAD` returns `refs/heads/main`.
**Warning signs:** `gh` UI shows two branches (`main` + `master`) after first push.

### Pitfall 9: `--source=.` requires the working tree to have NO uncommitted changes
**What goes wrong:** `gh repo create --source=. --push` fails if `.git/` exists but staging is dirty, or if there's no initial commit.
**Why it happens:** `gh` invokes `git push` internally; needs a clean state.
**How to avoid:** `gh_handoff.ship()` runs `git add -A` + `git commit` BEFORE `gh repo create`. Idempotent: only commits if `git status --porcelain` shows changes.
**Warning signs:** `gh repo create` exit 1 with `nothing to commit` or `working tree dirty`.

### Pitfall 10: Refusal regex matches false positives in spec
**What goes wrong:** User says "I want a simple service" — the word "service" matches "service-mesh"? "I want users to scale up" — substring "scale" matches "k8s" via fuzzy?
**Why it happens:** Loose substring matching.
**How to avoid:** Use word-boundary regex (`\bkubernetes\b`, `\bk8s\b`, etc.) and a focused keyword list. Test against a curated set of true-positive AND false-positive specs.
**Warning signs:** A simple TODO web app spec triggers refusal.

### Pitfall 11: gh CLI version skew on user's machine
**What goes wrong:** `gh repo create --source=.` requires gh ≥ 2.0 (released 2021). Older installs (< 2.0) lack the flag.
**Why it happens:** Phase 2 preflight may not enforce a minimum gh version.
**How to avoid:** Phase 6 ship step parses `gh --version`; on < 2.0, friendly-error with upgrade command (`brew upgrade gh` / `winget upgrade GitHub.cli`).
**Warning signs:** `gh repo create: unknown flag --source` from older gh.

---

## Runtime State Inventory

> N/A for Phase 6 — this is a greenfield additive phase. No rename, refactor, migration, or string-replacement is involved. Phase 6 only adds new files and extends existing scripts additively (per the locked Phase 3/4/5 ALLOWED_FIELDS pattern).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Phase 6 reads `state.md` (additively writes new ALLOWED_FIELDS) and writes new files in user app dirs | None |
| Live service config | None — built repos are static files; no live service backed by Phase 6 logic | None |
| OS-registered state | None — pre-commit hooks live in user's `.git/hooks/`, registered ONLY when user runs `pre-commit install` (not during scaffold) | None at OSBuilder level |
| Secrets/env vars | None — Phase 6 doesn't introduce new env var names; it uses `gh` and `git` which read existing `~/.config/gh/hosts.yml` etc. | None |
| Build artifacts | None — `pyproject.toml` already exists from Phase 1; no new compiled artifacts | None |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gh` (GitHub CLI) | SHIP-01, SHIP-05 | YES (dev machine) | 2.90.0 | None — Phase 2 preflight ensures install; manual fallback is "git push to user-created repo URL" but this defeats UX |
| `git` | SHIP-01 | YES | 2.50.1 (Apple Git-155) | None — Phase 2 preflight ensures |
| `gitleaks` | SHIP-04 (binary; framework mode pulls binary itself) | YES | 8.30.1 | If absent and `pre-commit` framework cannot fetch (offline), document fallback in README |
| `pre-commit` | SHIP-04 | NOT installed locally — required IN BUILT REPO at user time | — | Built repo's README runbook says `pip install pre-commit` or `brew install pre-commit` |
| Docker / Compose v2 | SCL-02, SCL-03 | NOT verified in this session — assumed by Phase 2 | — | `--no-docker` flag (already in Phase 2) → SQLite-only single-user CLI; refuses multi-user-web build with friendly-error |
| Python 3.13 | All Phase 6 scripts | YES (dev machine 3.12.6 reported in Phase 5; preflight installer ensures 3.13+ on user machine) | — | None — preflight installer handles |
| Network access to `github.com` | SHIP-01 (push), SHIP-04 (pre-commit fetch gitleaks binary on first run) | YES at dev time | — | Friendly-error on offline; document "you can re-run /osbuilder ship later" |

**Missing dependencies with no fallback:**
- None at the OSBuilder development side. `gh`, `git`, `gitleaks`, `Docker` are all preflight-installer responsibilities.

**Missing dependencies with fallback:**
- `pre-commit` (the Python framework) at user-clone time → README runbook installs it.
- Docker → `--no-docker` flag forces SQLite-only single-user CLI playbook.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (Python 3.13 stdlib + pytest only — no new deps; matches Phase 4/5) |
| Config file | `pyproject.toml` (existing — Phase 1) |
| Quick run command | `python3 -m pytest scripts/tests/ -x --tb=short -q` |
| Full suite command | `python3 -m pytest scripts/tests/ --tb=short -q` |
| Estimated runtime | ~15 seconds (quick, all phases) — Phase 6 adds ~12–18 tests on top of Phase 5's 127 |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SHIP-01 | `gh repo create --private` invoked with `--source=. --push`; `gh repo view --json visibility` returns `"PRIVATE"` | unit (mock subprocess); integration (smoke against test repo, deleted after) | `pytest scripts/tests/test_gh_handoff.py::test_ship_runs_private_create -x` | ❌ Wave 0 |
| SHIP-01 | Failure modes: gh-not-installed, gh-not-authenticated, gh-token-expired, repo-name-collision, network-failure — each routes through `friendly_error.translate()` | unit | `pytest scripts/tests/test_gh_handoff.py::test_failure_modes_friendly -x` | ❌ Wave 0 |
| SHIP-02 | `runbook_writer.write_readme()` produces a README containing: title, summary, Quick Start (`cd`, `cp .env.example .env`, install, run, verify), Requirements, Configuration, Development, Tests sections | unit (assert section presence + placeholder substitution) | `pytest scripts/tests/test_runbook_writer.py -x` | ❌ Wave 0 |
| SHIP-02 | Stranger-clone-and-run completes in ≤ 5 minutes | **manual UAT** (cannot deterministically automate; documented under Manual-Only Verifications below) | n/a | n/a |
| SHIP-03 | `.gitignore` written to project_dir contains: `.env`, `.env.*`, `!.env.example`, `*.log`, `.DS_Store`, `node_modules/` (or `__pycache__/` per stack), `.vscode/`, `.idea/` | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_gitignore_composition -x` | ❌ Wave 0 |
| SHIP-04 | `.pre-commit-config.yaml` written to project_dir is pinned to `gitleaks` rev `v8.30.1`; `.gitleaks.toml` allows `.env.example` paths | unit (file content match) | `pytest scripts/tests/test_scaffold_extensions.py::test_gitleaks_config -x` | ❌ Wave 0 |
| SHIP-04 | Real-looking secret commit blocked: writing `STRIPE_KEY=sk_live_AAAAAAAAAAAAAAAAAAAAAAAA` to a non-allowlisted file then `git commit` exits non-zero (WHEN gitleaks hook is installed) | integration (uses tmp git repo + installs hook + commits secret + asserts non-zero exit) | `pytest scripts/tests/test_scaffold_extensions.py::test_gitleaks_blocks_real_secret -x` (gated on `command -v pre-commit && command -v gitleaks`; skipif marker) | ❌ Wave 0 |
| SHIP-05 | `gh auth status` failure → friendly-error message with `gh auth login --git-protocol https` copy-paste | unit (mock subprocess returns exit 1 + canned stderr; assert friendly-error fields) | `pytest scripts/tests/test_gh_handoff.py::test_auth_drift_friendly -x` | ❌ Wave 0 |
| SCL-01 | Generated project contains `.env.example` (committed) and `.env` is matched by `.gitignore` | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_env_example_committed -x` | ❌ Wave 0 (existing `.env.example` write is Phase 3; test asserts it remains AND `.env` is gitignored) |
| SCL-02 | `_pick_database("web", "multi-user")` returns "postgres"; `_pick_database("cli", "single-user")` returns "sqlite" | unit (pure function) | `pytest scripts/tests/test_scaffold_extensions.py::test_pick_database -x` | ❌ Wave 0 |
| SCL-02 | Web build → `compose.yaml` exists with `postgres:18-alpine` and NO `version:` key; CLI build → no `compose.yaml`, app config has SQLite path | unit (file presence + content) | `pytest scripts/tests/test_scaffold_extensions.py::test_db_default_per_playbook -x` | ❌ Wave 0 |
| SCL-03 | Generated project contains `Dockerfile` (multi-stage) AND `compose.yaml` (without `version:` key) | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_docker_artifacts -x` | ❌ Wave 0 |
| SCL-04 | Generated project contains EXACTLY ONE `.github/workflows/*.yml` file with `actions/checkout@v6`, `actions/setup-node@v4` (or `setup-python@v6`), and `pull_request:` trigger | unit | `pytest scripts/tests/test_scaffold_extensions.py::test_one_ci_workflow -x` | ❌ Wave 0 |
| SCL-05 | A spec containing "kubernetes" → refusal: state.md `last_failure` matches `^refused: kubernetes`; no `.planning/PROJECT.md` is written | unit (mock derived_spec.md; call _check_refuse_list; assert state.md write + early return) | `pytest scripts/tests/test_refusal.py::test_kubernetes_refused -x` | ❌ Wave 0 |
| SCL-05 | Refusal copy contains the word "production-ready" (the opt-in path) | unit (load `references/refuse-list.md`; grep) | `pytest scripts/tests/test_refusal.py::test_refusal_copy_mentions_opt_in -x` | ❌ Wave 0 |
| SCL-06 | `state.md production_ready=true` → `production_phase_writer.py` emits 7 `/gsd-add-phase <name>` slash commands to stdout | unit (capture stdout; assert lines) | `pytest scripts/tests/test_production_ready.py::test_emits_seven_phases -x` | ❌ Wave 0 |
| SCL-06 | `state.md production_ready=false` (default) → `production_phase_writer.py` emits zero slash commands; ROADMAP.md unchanged | unit | `pytest scripts/tests/test_production_ready.py::test_no_emit_when_default -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest scripts/tests/ -x --tb=short -q` (≤ 15s)
- **Per wave merge:** `python3 -m pytest scripts/tests/ --tb=short -q` (full suite, all phases)
- **Phase gate:** Full suite green before `/gsd-verify-work` runs the 7 falsifiable success criteria from ROADMAP

### Wave 0 Gaps

- [ ] `scripts/tests/test_gh_handoff.py` — RED stubs for SHIP-01, SHIP-05; uses `subprocess` mock fixtures (capture command list; canned stdout/stderr/returncode)
- [ ] `scripts/tests/test_runbook_writer.py` — RED stubs for SHIP-02 (section presence + placeholder substitution against fake state.md)
- [ ] `scripts/tests/test_scaffold_extensions.py` — RED stubs for SHIP-03, SHIP-04, SCL-01..04 (file presence + content patterns against tmp_path "fake built app" tree)
- [ ] `scripts/tests/test_refusal.py` — RED stubs for SCL-05 (refusal gate behavior)
- [ ] `scripts/tests/test_production_ready.py` — RED stubs for SCL-06 (slash-command emission count)
- [ ] `scripts/tests/conftest.py` — extend with shared fixtures: `fake_built_app` (tmp_path tree), `fake_state_md` factory, `mock_gh_subprocess` (parameterized canned responses for the 5 failure modes), `mock_git_subprocess` (clean tree / dirty tree / no-init scenarios)
- [ ] `scripts/tests/fixtures/derived_spec_with_k8s.md` — refusal-test fixture
- [ ] `scripts/tests/fixtures/derived_spec_clean.md` — refusal-test negative fixture
- [ ] `state_writer.py` ALLOWED_FIELDS extension: add `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`, `production_ready` (additive — NOT in REQUIRED_FIELDS, matches Phase 3/4/5 pattern)

### Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stranger clones the resulting repo on a fresh machine and reaches a working app on `localhost` in ≤ 5 min via README | SHIP-02 success criterion #2 | "Stranger" + "fresh machine" + "5 min" cannot be deterministically automated in pytest; this is a UAT row | After E2E build, on a SECOND machine (or `docker run -it ubuntu` clean container with prerequisites): `gh repo clone <user/repo>; cd <repo>; cat README.md; <follow runbook verbatim>; verify localhost shows working homepage`. Time the run. |
| End-to-end refusal of "set up Kubernetes for this app" produces a friendly explanation pointing to `--production-ready` | SHIP-success-criterion #5 (ROADMAP) | Default-mode refusal copy is human-judged for friendliness | Submit a spec containing "build me a TODO app with Kubernetes orchestration"; verify state.md `last_failure` matches refusal pattern; verify `references/refuse-list.md`-sourced copy is shown to user; verify offering `--production-ready` is explicit |
| `--production-ready` adds K8s as a NAMED PHASE in `.planning/ROADMAP.md`, not as scaffold code | SCL-06 | Inspecting "named phase row" in ROADMAP.md is a content judgment, not a deterministic regex (could automate but content quality is human-judged) | Submit same Kubernetes spec with `--production-ready`; verify `.planning/ROADMAP.md` gains rows for: observability, migrations, healthchecks, secret manager, Sentry, rate limiting, backup; verify NO k8s manifest / Helm chart files appear in user's project_path |

### Test Harness Strategy (the pattern for SHIP-04 integration)

For SHIP-04 ("real secret blocked by hook") — the only test that needs real subprocess + real gitleaks + real pre-commit — use this pattern:

```python
# scripts/tests/test_scaffold_extensions.py
import subprocess
import shutil
import pytest

@pytest.fixture
def fake_built_repo(tmp_path):
    """Create a tmp git repo with .pre-commit-config.yaml + .gitleaks.toml installed."""
    repo = tmp_path / "fake-built-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, shell=False)
    # Stamp the templates (mirror what gh_handoff.py would do)
    (repo / ".pre-commit-config.yaml").write_text(...)  # gitleaks rev v8.30.1
    (repo / ".gitleaks.toml").write_text(...)  # permissive starter
    return repo

@pytest.mark.skipif(
    shutil.which("pre-commit") is None or shutil.which("gitleaks") is None,
    reason="needs pre-commit and gitleaks installed locally",
)
def test_gitleaks_blocks_real_secret(fake_built_repo):
    """SHIP-04: gitleaks pre-commit hook blocks a real-looking secret."""
    subprocess.run(["pre-commit", "install"], cwd=fake_built_repo, check=True, shell=False)
    secret_file = fake_built_repo / "config.py"
    secret_file.write_text('STRIPE_KEY = "sk_live_AAAAAAAAAAAAAAAAAAAAAAAA"\n')
    subprocess.run(["git", "add", "config.py"], cwd=fake_built_repo, check=True, shell=False)
    result = subprocess.run(
        ["git", "commit", "-m", "secret"],
        cwd=fake_built_repo, capture_output=True, text=True, shell=False,
    )
    assert result.returncode != 0, f"gitleaks should block; got returncode {result.returncode}"
    assert "gitleaks" in (result.stdout + result.stderr).lower()
```

For SHIP-01 (`gh repo create --private`) — choose ONE of:

**Option A (recommended for v1):** Mock `subprocess.run` for `gh ...` calls; assert command list contains `--private`. Real-network test left for manual UAT. Fast, deterministic, no GitHub state pollution.

**Option B:** Live test against a known-disposable test repo name (e.g., `osbuilder-ship-test-<timestamp>`); delete after via `gh repo delete -y`. Real but slow + requires authenticated dev environment + risks rate-limit + can leave orphans on flaky network. Not recommended for the per-task tight loop; acceptable for nightly UAT.

Recommendation: Option A in `test_gh_handoff.py`; Option B as an opt-in `pytest -m live_gh` marker that's skipped by default and only run by Charlie on demand.

---

## Code Examples

Verified patterns from official sources:

### Stamp `.gitignore` with composition

```python
# scripts/gh_handoff.py — Track A internal helper
# Source: github.com/github/gitignore (verified 2026-05-01)
ASSETS = Path(__file__).resolve().parent.parent / "assets" / "gitignore-templates"

def _compose_gitignore(project_dir: Path, stack_family: str = "node") -> None:
    """Compose .gitignore from common + stack-family templates.

    Idempotent: if .gitignore already exists, prepends new content + a separator
    rather than overwriting (preserves user customization).
    """
    common = (ASSETS / "common.gitignore").read_text(encoding="utf-8")
    lang = (ASSETS / f"{stack_family}.gitignore").read_text(encoding="utf-8")
    composed = (
        "# OSBuilder default — common\n"
        + common.strip() + "\n\n"
        + f"# OSBuilder default — {stack_family}\n"
        + lang.strip() + "\n"
    )
    target = project_dir / ".gitignore"
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if "# OSBuilder default" in existing:
            return  # already stamped (idempotent)
        composed = composed + "\n# --- existing .gitignore ---\n" + existing
    atomic_write(target, composed)
```

### `.env.example` allowlist negative match

```gitignore
# assets/gitignore-templates/common.gitignore — relevant excerpt
# Source: github.com/github/gitignore (curated)
.env
.env.*
!.env.example
!.env.sample
```

The negative match (`!`) ensures `.env.example` IS committed even though `.env.*` matches it.

### `gh repo create` invocation

```python
# Source: gh CLI 2.90.0 docs (verified via local `gh repo create --help` 2026-05-01)
subprocess.run(
    [
        "gh", "repo", "create",
        "--source=" + str(project_dir),
        "--remote=origin",
        "--push",
        "--private",  # or "--public" if state.md says so
    ],
    shell=False,
    capture_output=True,
    text=True,
)
```

### `gh repo view --json` verification

```python
# Source: gh CLI 2.90.0 (verified 2026-05-01)
view = subprocess.run(
    ["gh", "repo", "view", "--json", "visibility,nameWithOwner,sshUrl"],
    cwd=str(project_dir),
    capture_output=True, text=True, shell=False, check=True,
)
info = json.loads(view.stdout)
# info == {"visibility": "PRIVATE", "nameWithOwner": "octocat/myapp", "sshUrl": "git@github.com:octocat/myapp.git"}
assert info["visibility"] == "PRIVATE"
```

### gh auth status preflight + drift remediation

```python
# Source: cli/cli/issues/8846 + gh-pat docs (verified 2026-05-01)
auth = subprocess.run(
    ["gh", "auth", "status"],
    capture_output=True, text=True, shell=False,
)
if auth.returncode != 0:
    # friendly_error dictionary entry "gh-auth-status-failed":
    #   what_broke: "GitHub CLI is not authenticated (or your token has expired)."
    #   what_to_do: "Run the command below to log in again. If you set GITHUB_TOKEN, unset it first."
    #   copy_paste: "gh auth login --git-protocol https"
    msg = friendly_error.translate("gh auth status failed: " + auth.stderr, ctx={"tool": "gh"})
    sys.stderr.write(format_friendly_error(msg))
    return 1
```

### Pure-function database choice

```python
# scripts/scaffold_dispatch.py — new helper
def _pick_database(playbook: str, app_type: str) -> str:
    """SCL-02: deterministic database default rule.

    web, ai-service, hub-platform → postgres (multi-user expected)
    cli → sqlite (single-user)
    desktop → sqlite (single-user, local-only by default)
    """
    if playbook in ("web", "ai-service", "hub-platform"):
        return "postgres"
    if playbook in ("cli", "desktop"):
        return "sqlite"
    # Unknown playbook — default to sqlite (safer; doesn't require Docker)
    return "sqlite"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `docker-compose.yml` (Compose v1) | `compose.yaml` (Compose v2 canonical) | Compose Specification published 2020; v1 EOL'd June 2023 | OSBuilder uses `compose.yaml` per Phase 6 SCL-03 (verbatim) |
| `version: '3.8'` at top of compose file | Omit `version:` (obsolete in v2; ignored with warning) | Deprecation began 2023 | OSBuilder templates omit; warning would erode trust |
| Manual `git remote add` + `git push` after `gh repo create` | Single `gh repo create --source=. --push` | gh CLI ≥ 2.0 (2021) | Atomic; one failure surface; OSBuilder uses |
| Raw `.git/hooks/pre-commit` shell script | `pre-commit` framework with `.pre-commit-config.yaml` | Industry shift ~2018–2020 | Declarative; supports update; gitleaks ships official upstream config |
| Single-stage Dockerfile | Multi-stage Dockerfile (`FROM ... AS builder`) | Multi-stage stable since Docker 17.05 (2017) | Smaller runtime image; build deps excluded |
| `actions/checkout@v3` | `actions/checkout@v6` | v6 released 2024–2025 timeframe | Latest stable; OSBuilder uses |
| `actions/setup-node@v3` | `actions/setup-node@v4` | v4 released 2024 | Built-in pnpm cache support |
| `npm install -g pnpm` in CI | `pnpm/action-setup@v4` (with order-before-setup-node) | Action stabilized 2023+ | Cache works; OSBuilder uses |
| `git init` (default branch follows config) | `git init -b main` (explicit) | git ≥ 2.28 (2020) | Avoids master/main drift |
| Personal access tokens with no expiration | Tokens with expiration; `gh auth status` reports drift; `gh auth refresh` | GitHub deprecated unscoped/long PATs progressively | Phase 6 friendly-error copy points at `gh auth login --git-protocol https` to refresh |

**Deprecated/outdated:**
- `docker-compose` (the v1 separate Python tool) — replaced by `docker compose` (built into Docker CLI as plugin)
- `version:` key in compose files — obsolete
- `chmod +x .git/hooks/pre-commit` raw scripts — superseded by `pre-commit` framework
- `actions/cache@v4` for node_modules — superseded by `setup-node@v4`'s built-in cache

---

## Project Constraints (from CLAUDE.md)

> CLAUDE.md is short in this repo (the file ends mid-section "Core Technologi"). The actionable directives are inferable from PROJECT.md + STATE.md + the existing codebase shape.

- **Stack-for-OSBuilder-itself:** Python 3.13 stdlib + Markdown + bash where unavoidable. No third-party Python deps.
- **Stack-for-built-apps:** Per-build research (Phase 3 already proven for web playbook); fallback to `references/stack-menu.md`.
- **Defaults are research-driven, not fixed.** Phase 6's job is to provide the SHAPE (env config, Dockerfile, CI, real DB, gitleaks) — the SPECIFIC values come from the per-build stack research run in Phase 3 (currently web only; Phase 7 adds others).
- **Privacy by default.** All ship-step code paths use `--private` unless `state.md` flag explicitly says otherwise.
- **Never hand-roll.** Phase 6 reaches for `gh`, `git`, `gitleaks`, `pre-commit`, Compose v2, GitHub Actions — all upstream-maintained.
- **Single-threaded execution.** Ship step is one final phase; runs after every per-phase verify-loop has passed; no parallelism.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 6 ship step lives at `phase_step == 11` (after Phase 5's step 10 advance) and only runs once when `current_phase > gsd_phase_count` | Architecture Patterns / Discretion | If wrong, ship runs every phase (wasteful + creates nested repos); planner needs to confirm or pick differently |
| A2 | The `--production-ready` flag emits via `/gsd-add-phase` slash commands rather than direct ROADMAP.md edits | Architecture Patterns | If wrong (e.g., `/gsd-add-phase` doesn't exist or has different contract), production_phase_writer.py needs different downstream — could fall back to direct ROADMAP append |
| A3 | The user's `gh` is authenticated under the account they want repos under (no multi-account disambiguation in v1) | Pitfalls #1 | If user has multiple accounts and v1 picks the wrong one, repos go to wrong place; recommend tutor-mode prompt before push as a v1.x enhancement |
| A4 | gitleaks v8.30.1 will remain stable through Phase 6 ship; no breaking pre-commit-hook contract change | Standard Stack | If gitleaks ships breaking change, pin update; low-risk (semver) |
| A5 | The per-stack-family Dockerfile granularity (Node-pnpm, Python-uv) covers Phases 6 + 7 needs | Standard Stack / Discretion | If Phase 7 adds a playbook that needs a third stack family (e.g., Rust for Tauri 2 sidecar), add at that point — additive |
| A6 | "Stranger clones in ≤ 5 min" is verifiable only by manual UAT, not by pytest | Validation Architecture | If reviewer wants automation, deterministic "clone + run + tail logs + grep success pattern" inside a Docker test container is possible but adds complexity + flakiness; flagged as Open Question 1 below |
| A7 | The refusal gate runs at the Architect role boundary (phase_step == 1 / `/gsd-plan-phase`) | Architecture Patterns | If refusal needs to run earlier (during PM/spec phase) to prevent any spec.md write, planner can move; refusal earlier is strictly safer |
| A8 | A `tmp_path`-based "fake built app" tree is sufficient for testing file-stamping behavior; full `gh repo create` over real network is opt-in only | Validation Architecture | Standard practice; matches Phase 4's approach for `registry_verify` |
| A9 | The `refuse-list` keyword regex uses word-boundary matches and a curated list (not LLM-driven detection) | Architecture Patterns | If user spec uses synonyms ("orchestration platform" instead of "kubernetes"), false negative; v1.x can add LLM-augmented detection if needed |
| A10 | The `--no-docker` flag (Phase 2) plus `playbook == cli` adequately handles "user without Docker wants to build" — no compose.yaml in CLI builds | Standard Stack | Already shipped in Phase 2 (PRE-07); Phase 6 just respects the flag — no risk |

---

## Open Questions

1. **Should the "stranger clones in ≤ 5 min" criterion be automated via Docker container UAT?**
   - What we know: It is currently classified as manual UAT in the validation table. A `docker run --rm -it ubuntu:24.04 bash -c "apt install -y git node-pnpm; gh repo clone <test-repo>; cd <repo>; <runbook commands>; <verify localhost>"` script could automate.
   - What's unclear: Does the planner / verifier want this as a deterministic test, or is manual UAT acceptable for v1? Adds CI complexity but adds confidence.
   - Recommendation: **Manual UAT for v1.** Document in 06-VALIDATION.md as a manual row. If Phase 8 demands deterministic test (likely for QUAL-04 examples gallery), revisit.

2. **Does the refusal gate need a bypass mechanism for power users who explicitly want K8s WITHOUT `--production-ready`?**
   - What we know: SCL-05 says refuse in default mode. SCL-06 says `--production-ready` adds K8s as a named phase, NOT as scaffold code.
   - What's unclear: What if a power user passes `--production-ready` AND wants K8s manifests in the actual scaffold (not just as a roadmap phase)? Project decisions explicitly punt this to v1.x design.
   - Recommendation: **No bypass in v1.** `--production-ready` adds K8s as a phase row only; if the user runs that phase later, the phase itself can scaffold k8s artifacts.

3. **Should `gh_handoff.py` ship-step idempotency cover the case where the remote exists but has DIVERGENT history?**
   - What we know: Idempotency check is via `git remote get-url origin`. If it exists, ship() returns early.
   - What's unclear: If the remote is `origin = git@github.com:user/<repo>.git` but the local working tree has uncommitted changes ahead of remote, what should ship() do?
   - Recommendation: **Detect via `git status --porcelain` + `git log origin/main..HEAD --oneline` — on divergence, friendly-error: "Your local repo has changes not yet pushed. Run `git push` manually or contact maintainer."** No auto-merge; safer.

4. **Should `assets/runbook-templates/web.md` be a single template with playbook-conditional sections, or per-playbook files?**
   - What we know: Per-playbook files (one per of: web, cli; later ai-service, desktop, hub-platform).
   - What's unclear: Maintainability tradeoff: single-file with `{{#if playbook == 'web'}}` Mustache-style is more compact but adds a templating engine choice (no new deps locked → would need stdlib `string.Template` or hand-rolled).
   - Recommendation: **Per-playbook files.** Avoids adding a templating mini-language; stdlib `str.replace()` covers placeholder substitution.

5. **What's the friendly-error dictionary's category for the new entries?**
   - What we know: Phase 5 dictionary has 9 categories: `preflight | gh-auth | registry | runtime | docker | filesystem | network | git | scaffold`.
   - What's unclear: New entries `gh-repo-name-collision` is `gh-auth` (same family) or new category `gh-repo`?
   - Recommendation: **Reuse `gh-auth` category for all `gh ...` errors except `gitleaks-blocked-secret` which goes in new category `secrets-defense` — adds 1 category, justifiable because it's a different threat surface.**

---

## Sources

### Primary (HIGH confidence)

- **Local file reads (verified 2026-05-01):**
  - `scripts/state_writer.py` — ALLOWED_FIELDS pattern, REQUIRED_FIELDS, `_check_value_safe`
  - `scripts/gsd_driver.py` — PHASE_STEP_COMMANDS, `_role_for_step`, `_run_tech_writer_step`, `_emit` narration helper, `_run_registry_gate`
  - `scripts/scaffold_dispatch.py` — existing `compose.yaml` constant (line 55, no `version:`), `.env.example` constant (line 52), `write_drizzle_files` boundary (line 122), Postgres pin `postgres:18-alpine` (line 58)
  - `SKILL.md` — `gh_handoff.py` planned but not yet on disk (line 87), refuse-list (line 100)
  - `references/playbooks/web.md` — refuse list (line 51-58)
  - `references/stack-menu.md` — current pinned versions
  - `.planning/REQUIREMENTS.md` — SHIP-01..05, SCL-01..06 verbatim
  - `.planning/ROADMAP.md` — Phase 6 success criteria verbatim
  - `.planning/STATE.md` — locked decisions through Phase 5
  - Phase 5's `05-RESEARCH.md`, `05-VALIDATION.md` — research/validation format precedent
  - Phase 4's `04-RESEARCH.md` — research format precedent
- **`gh repo create --help`** (gh 2.90.0 local, 2026-05-01) — confirmed `--private`, `--source string`, `--push`, `--remote string` flags
- **`gitleaks version`** (8.30.1 local, 2026-05-01) — verifies binary install
- **`api.github.com/repos/gitleaks/gitleaks/releases/latest`** (2026-05-01) — confirms `v8.30.1` published 2026-03-21
- **docs.docker.com/compose/intro/compose-application-model** — Compose canonical filename priority order (verified via WebSearch 2026-05-01)
- **docs.docker.com/reference/compose-file** — Compose v2 spec; `version:` key obsolete
- **github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml** — official pre-commit hook id `gitleaks`
- **github.com/actions/setup-node** — `setup-node@v4` with `cache: 'pnpm'` directive
- **github.com/pnpm/action-setup** — `action-setup@v4` precede setup-node order rule

### Secondary (MEDIUM confidence)

- **github.com/github/gitignore** — canonical gitignore templates (curated, vendored into `assets/gitignore-templates/`)
- **github.com/cli/cli/issues/8846** — gh auth token renewal flow (informs friendly-error copy)
- **medium.com/@ketanpradhan/secure-your-git-repository-with-gitleaks-and-pre-commit-hooks** — pre-commit + gitleaks integration tutorial (cross-reference; not authoritative on its own)
- **dev.to/igadii/building-efficient-nodejs-workflows-in-github-actions** — pnpm + Node CI workflow pattern
- **pnpm.io/continuous-integration** — official pnpm CI guidance

### Tertiary (LOW confidence — flagged for validation during execution)

- **The exact Dockerfile contents for Python-uv** (assets/dockerfiles/python-uv.Dockerfile.tmpl) — based on uv's documented multi-stage pattern but not directly verified against Phase 7's eventual ai-service playbook needs. Wave 1 plan should verify against `astral-sh/uv` README before stamping.
- **`docker compose version` reports v2 on the dev machine** — assumed from Phase 2 preflight; not re-verified in this research session.

---

## Metadata

**Confidence breakdown:**
- Standard stack (gh, gitleaks, Compose v2, GH Actions): HIGH — all verified locally + via WebSearch + via official GitHub release tag
- Architecture patterns (file boundaries, dispatch points): HIGH — derived from direct file read of Phase 4/5 codebase
- Pitfalls: HIGH for codebase-internal (state_writer rejection rules, default branch); MEDIUM for external (gh name collision behavior, pre-commit framework upgrade flow) — verified against issue threads
- Validation architecture: HIGH — full per-task map; one row (SHIP-02 #2 stranger-clone) flagged manual-UAT explicitly
- Refusal mechanics: MEDIUM — no upstream pattern; design is original; protected by deterministic regex + curated keyword list

**Research date:** 2026-05-01
**Valid until:** 2026-06-01 (30 days for stable; gh CLI / gitleaks / Compose v2 are mature, slow-moving)
