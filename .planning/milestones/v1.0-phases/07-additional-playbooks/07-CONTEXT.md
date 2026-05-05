# Phase 7: Additional playbooks - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Add 4 new playbooks — `ai-service` (FastAPI + uv + Pydantic v2), `cli` (Python + Typer + Rich + SQLite), `desktop` (Tauri 2), `hub-platform` (Professor-style umbrella) — each with a `references/playbooks/<type>.md` spec, scaffold-dispatch routing, intake `app_type` inference, and an end-to-end clone-and-run loop matching Phase 6's web playbook. Web playbook is unchanged; this phase is purely additive.

**Out of scope (future phases):** runtime sub-tool generation inside hub-platform builds, deployment integrations beyond the existing private-GitHub ship-step, additional language ecosystems (Go, Ruby, etc.).

</domain>

<decisions>
## Implementation Decisions

### Routing — intake `app_type` inference

- **D-01:** Replace the hardcoded `app_type="web"` in `scripts/intake_handler.py:264` with keyword-scored inference across all 5 playbooks (web / ai-service / cli / desktop / hub-platform).
- **D-02:** When inference confidence is low or 2+ playbooks score similarly, fall back to a plain-English question via `references/question-bank.md` (e.g., "Sounds like an HTTP API or a desktop app — which fits?"). Never silently coin-flip; always preserve the "I don't know, you decide" option per IN-04.
- **D-03:** The TODO comment at `scripts/intake_handler.py:263-265` is the deletion target — the new inference function replaces the placeholder hardcode.

### Hub-platform shape (SC-04)

- **D-04:** Hub-platform playbook produces a top-level `CLAUDE.md` routing table + N empty sub-tool subdirectories named from intake (e.g., `grader/`, `roster/`). Each sub-tool gets its own placeholder `CLAUDE.md`. User re-runs `/osbuilder` per sub-tool to fill them in a later session.
- **D-05:** Structural verification: file/dir layout must match `professor/` at the top level (same nesting depth, same routing-table format) — diff-checked against a vendored snapshot in tests, NOT a live filesystem dependency on `professor/`.
- **D-06:** Sub-tool count and names come from intake parsing (e.g., "build me a hub like Professor Hub for grading and rostering" → `grading/`, `rostering/`). If unresolvable, ask via question-bank.

### Desktop scaffolding (SC-03)

- **D-07:** Desktop playbook uses `pnpm create tauri-app@latest <name> --template react-ts --manager pnpm --identifier <reverse-dns>` — non-interactive, pinned flags, mirroring the create-next-app pattern from Phase 3 web playbook.
- **D-08:** Tauri owns template drift (same risk model accepted for create-next-app). Pin `create-tauri-app` to a verified version in the playbook .md so version drift is visible in git diffs.
- **D-09:** Electron refusal stays at the intake refusal gate (already in `references/refuse-list.md`); desktop playbook documents the Tauri-not-Electron rationale inline per SC-03.

### AI-service scaffold contents (SC-01)

- **D-10:** `assets/fastapi-starter/` ships: routed `/` (hello), `/health` (200 OK), automatic `/docs` from FastAPI, **plus a stub `/summarize` POST endpoint** that calls a placeholder `summarize(text)` function returning `{"summary": text[:200]}`. Matches SC-01's "summarizes documents with an LLM" example so the AI shape is visible immediately, no API key required to boot.
- **D-11:** No real Claude API call in the starter — the stub function carries a comment pointing to where the user wires in a real LLM call. Avoids the "needs an API key to demo" friction.
- **D-12:** Pydantic v2 models for request/response on `/summarize` (`SummarizeRequest`, `SummarizeResponse`) — establishes the v2 patterns required by SCAF-02.

### CLI playbook scaffold (SC-02)

- **D-13:** CLI playbook uses `uv init --app <name>` + post-scaffold writes for `pyproject.toml` Typer/Rich/SQLite deps. SQLite path is `~/.<app-name>/state.db`; `_pick_database` already routes non-web to SQLite so no change needed there.
- **D-14:** Starter command: `<app-name> --help` (Rich-formatted) and one example sub-command (`<app-name> ping`) that writes a row to SQLite and reads it back, proving SC-02's "persists state across runs."

### Plan slicing

- **D-15:** Phase 7 = **6 plans**:
  - `07-01` — Intake routing + inference (single source of truth before playbooks land)
  - `07-02` — AI-service playbook (`ai-service.md` + `assets/fastapi-starter/` + scaffold dispatch + tests)
  - `07-03` — CLI playbook (`cli.md` + post-scaffold writes + tests)
  - `07-04` — Desktop playbook (`desktop.md` + create-tauri-app dispatch + tests)
  - `07-05` — Hub-platform playbook (`hub-platform.md` + structural template + sub-tool stubs + tests)
  - `07-06` — Shared E2E harness (parametrized stranger-clone test across all 4 playbooks)
- **D-16:** Plans 07-02..07-05 are wave-parallelizable once 07-01 lands. 07-06 depends on all four.

### Verification (SC-05)

- **D-17:** One parametrized E2E test file `scripts/tests/test_e2e_playbooks.py` runs the 5-step contract (intake → scaffold → install → boot → stop) parametrized over `[ai-service, cli, desktop, hub]`. Single source of truth for the contract.
- **D-18:** Each parametrized case has a hard timeout (~30s scaffold + ~60s install + ~30s boot = ~2min per case, ~8min total). Failures gate the phase per SC-05's ≤5-min stranger-clone requirement.
- **D-19:** Manual stranger-clone UAT remains in `07-HUMAN-UAT.md` per Phase 6 precedent — automated test covers the contract, human gate covers the experience.

### Preflight extensions

- **D-20:** Extend `scripts/preflight_check.py` with auto-install (single confirmation, same as Node/Docker) for: `cargo`/`rustc` via `curl https://sh.rustup.rs -sSf | sh -s -- -y` (Rust, needed for Tauri); `uv` via `curl -LsSf https://astral.sh/uv/install.sh | sh` (needed for FastAPI + CLI playbooks).
- **D-21:** Both installers respect the Phase 2 cross-platform contract — Windows uses the official PowerShell installers (`winget install Astral.UV`, `winget install Rustlang.Rustup` or fallback `Invoke-WebRequest` to the official .ps1 scripts).

### Refusal/scope guardrails

- **D-22:** Migrate Electron refusal from `references/playbooks/web.md` to global `references/refuse-list.md` (currently scoped to web; now covers all builds). Hub-platform refuses inline-scaffolding all sub-tools at once (per D-04).
- **D-23:** No new refuse keywords for Phase 7 beyond Electron migration — existing kubernetes/microservices/helm/service-mesh keywords still apply universally.

### Claude's Discretion

- Inference scoring algorithm details (weighted keyword counts vs. simple bag-of-words) — planner picks; D-02's "ask if unsure" is the safety net.
- Exact wording of the playbook-fallback question in `question-bank.md` — should match the existing outcome-framed style (no jargon).
- Whether to vendor a `professor/` snapshot inside `.planning/codebase/snapshots/` or `assets/hub-template/` for D-05 diff-checking — planner picks based on what fits the test harness cleanest.
- Line ordering inside each new playbook .md — keep web.md's section order (What it produces / Scaffold command / Post-scaffold files / Refuse list / Stack pinned versions) for consistency.

### Folded Todos

None — no pending todos matched Phase 7 scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 7 scope sources
- `.planning/ROADMAP.md` §"Phase 7: Additional playbooks" — 5 success criteria (SC-01..SC-05) and SCAF-02..SCAF-05 mapping
- `.planning/REQUIREMENTS.md` lines 63-66 — SCAF-02..SCAF-05 acceptance text
- `.planning/PROJECT.md` §"Active" — common-person UX rules and "refuses" list (Electron migration source)

### Web playbook precedent (template for the 4 new playbooks)
- `references/playbooks/web.md` — section-by-section template; new playbooks must mirror this shape (77 lines)
- `references/stack-menu.md` — fallback defaults format; each new playbook adds a "## <type> playbook defaults" table here
- `scripts/scaffold_dispatch.py` — `scaffold_web()`, `_pick_database()`, `_write_dockerfile()`, `_write_ci_workflow()` — extension pattern for new `scaffold_ai_service()`, `scaffold_cli()`, `scaffold_desktop()`, `scaffold_hub()` functions

### Intake routing surface (D-01..D-03)
- `scripts/intake_handler.py:227-272` — `parse_paragraph()` and `parse_structured()`; `app_type="web"` hardcode at line 264 with TODO(phase-7)
- `references/question-bank.md` — outcome-framed question patterns; new "what kind of thing" question follows existing IN-03/IN-04 style

### Refusal + scope guardrails
- `scripts/intake_handler.py:54-65` — `REFUSE_KEYWORDS` tuple; D-22 expands by moving Electron from web.md to refuse-list.md (no new keywords)
- `references/refuse-list.md` — refusal copy; D-22 migration target
- `scripts/production_phase_writer.py` — `NAMED_UPGRADES` tuple; reused as-is (no per-playbook overrides)

### Verification (SC-05, D-17..D-19)
- `.planning/phases/06-ship-to-private-github-scalable-defaults/06-04-PLAN.md` — Phase 6 stranger-clone runbook pattern (precedent for what "clone-and-run in ≤5 min" means)
- `scripts/tests/conftest.py` — fixture patterns for parametrized E2E tests; `mock_gh_subprocess` and `mock_git_subprocess` reusable
- `assets/ci-workflows/node.yml.tmpl`, `assets/ci-workflows/python.yml.tmpl` — CI templates each playbook inherits

### Preflight (D-20..D-21)
- `scripts/preflight_check.py` — Node/Python/git/gh/Docker detection + auto-install pattern; Rust + uv extensions follow same shape
- `scripts/bootstrap.sh`, `scripts/bootstrap.ps1` — cross-platform installer entry points (Phase 2)

### External (verify versions at research time)
- Tauri 2 docs (`tauri.app/start/create-project/`) — `create-tauri-app` flags and template names
- FastAPI docs (`fastapi.tiangolo.com/`) — `fastapi dev` runner + Pydantic v2 patterns
- Typer docs (`typer.tiangolo.com/`) — `Typer()` + Rich integration
- uv docs (`docs.astral.sh/uv/`) — `uv init --app` and Windows installer
- Rustup install script (`https://sh.rustup.rs`) and Windows alternative

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/scaffold_dispatch.py:scaffold_web()` — copy-paste-and-adapt template for the 4 new scaffold functions; same signature `(project_name, project_root) -> Path`
- `scripts/scaffold_dispatch.py:_pick_database()` — already routes non-web to SQLite; no change needed for cli/ai-service/hub
- `scripts/scaffold_dispatch.py:atomic_write()`, `_validate_project_name()` — reuse as-is
- `scripts/intake_handler.py:parse_paragraph()` / `parse_structured()` — extend with inference function; `app_type` field already plumbed through
- `scripts/runbook_writer.py` — README template substitution is playbook-agnostic; works for all 4 with stack-specific quickstart command pulled from each `<type>.md`'s "Scaffold command" section
- `scripts/gh_handoff.py` — repo creation is playbook-agnostic; reused unchanged
- `references/playbooks/web.md` — section-by-section template (What it produces / Scaffold command / Post-scaffold / Refuse list / Stack)

### Established Patterns
- Playbook .md files are loaded on-demand by the Architect role — NOT pulled into SKILL.md (200-line cap from QUAL-01); each new playbook stays under ~80 lines like `web.md`
- Pinned versions in playbook .md with "verified <date>" stamps — researcher must verify and stamp
- `--playbook` argparse flag in `scripts/scaffold_dispatch.py` already accepts arbitrary string; new values plug in via routing dict
- Test files use `pytest.skip("Wave 1 target")` for Wave 0 RED stubs (Phase 1 pattern); E2E test 07-06 follows this Wave 0/1 split
- Friendly errors via `friendly_error.translate()` + `dictionary.yaml` entries — each new playbook adds its tool-specific entries (e.g., `tauri-not-installed`, `uv-not-installed`)

### Integration Points
- `scripts/gsd_driver.py` — phase_step state machine is playbook-agnostic; ship-step (Phase 6) wraps any playbook output
- `references/question-bank.md` — new "what-kind-of-thing" question lands here per D-02
- `assets/ci-workflows/` — `python.yml.tmpl` already exists (used by current web/python builds); ai-service and cli playbooks reuse it. Desktop needs new `tauri.yml.tmpl` (Rust + Node combo). Hub doesn't need CI by default (it's a workspace, not an app).
- `assets/dockerfiles/` — python.Dockerfile.tmpl reusable for ai-service; cli doesn't ship a Dockerfile (it's a local CLI); desktop ships build artifacts not a container; hub doesn't ship a Dockerfile
- `scripts/preflight_check.py` — single extension point for Rust + uv detection (D-20)

</code_context>

<specifics>
## Specific Ideas

- SC-04 explicitly compares to `professor/` — diff-based structural verification is the contract, not feature parity. Vendor a snapshot at planning time so the test isn't filesystem-coupled.
- SC-01 names a concrete example ("summarizes documents with an LLM") — the `/summarize` stub endpoint (D-10) lifts that example verbatim so a user pasting SC-01's exact spec sees the right shape immediately.
- SC-03 explicitly requires that OSBuilder "refuses Electron with a documented rationale if the user requests it." Current refusal is in `web.md` — must move to global `refuse-list.md` (D-22).
- The "stranger clones, runs the documented command, reaches a working app in ≤5 min" gate is the same human contract as Phase 6 — `07-HUMAN-UAT.md` follows `06-HUMAN-UAT.md`'s shape.

</specifics>

<deferred>
## Deferred Ideas

- **Real Claude API wiring in fastapi-starter** — D-11 ships the stub. A future phase or `--with-llm-key` flag could write a working `summarize()` that calls the Anthropic SDK. Not in Phase 7 scope.
- **Sub-tool autoscaffolding for hub-platform** — D-04 ships empty stubs. Letting the hub playbook automatically run `/osbuilder` for each named sub-tool is a Phase 8+ orchestration question.
- **Additional language ecosystems** (Go, Ruby, Java, Elixir) — out of v1 milestone per PROJECT.md scope.
- **Deployment beyond private GitHub** (Vercel/Fly/Railway integrations) — Phase 6 ship-step is the v1 contract.
- **Per-playbook --advanced overrides for stack components** (e.g., swap FastAPI for Litestar) — current `--advanced` flag covers component-level overrides; per-playbook menu extension is deferred.

</deferred>

---

*Phase: 07-additional-playbooks*
*Context gathered: 2026-05-01*
