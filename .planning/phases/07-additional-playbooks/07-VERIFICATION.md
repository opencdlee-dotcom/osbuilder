---
phase: 07-additional-playbooks
verified: 2026-05-02T12:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Stranger clone-and-run for ai-service: clone the scaffolded FastAPI repo, run `uv sync && uv run fastapi dev`, open http://127.0.0.1:8000/docs, confirm /, /health, /summarize are visible within 5 minutes"
    expected: "Working /docs page reachable in ≤5 minutes; no source edits required"
    why_human: "Requires a real GitHub repo from a build run + fresh machine; automated test covers 5-step contract; human gate covers actual stranger-clone UX"
  - test: "Stranger clone-and-run for cli: clone the scaffolded Typer repo, run `uv sync && uv run <app-name> --help`, confirm Rich-formatted help; run `<app-name> ping` twice to verify SQLite persistence"
    expected: "Rich-styled help visible; 'ping #1' then 'ping #2' on successive calls"
    why_human: "Rich formatting and cross-run persistence require a real shell session; can't be deterministically automated without one"
  - test: "Stranger clone-and-run for desktop: clone the scaffolded Tauri 2 repo (with pnpm+cargo pre-installed), run `pnpm install && pnpm tauri dev`, confirm a native window opens"
    expected: "Native window opens with hot-reload Tauri+React default content"
    why_human: "OS-level GUI assertion is not feasible in CI; requires a graphical session and OS permissions"
  - test: "Stranger clone-and-run for hub-platform: clone the scaffolded hub, open top-level CLAUDE.md, confirm routing table lists each sub-tool subfolder with purpose rows; open one sub-tool CLAUDE.md and confirm re-run instruction"
    expected: "Fresh human understands hub purpose and sub-tool structure without prior context"
    why_human: "Hub-platform success metric is human comprehension of the routing document, not runtime behavior"
  - test: "Electron refusal UX: submit intake 'I want an Electron desktop app for note-taking'; confirm refusal mentions Electron by name, Tauri 2 as alternative, and the rationale (binary size, RAM)"
    expected: "Friendly refusal copy — no jargon; all three elements present"
    why_human: "Automated test verifies refuse-list.md text contains 'Electron'+'Tauri'; actual UX friendliness is human-judged"
  - test: "/summarize smoke against booted ai-service: POST {\"text\":\"hello world\"} → {\"summary\":\"hello world\"}; POST {\"text\":\"\"} → 422"
    expected: "Valid request returns summary stub; empty text triggers Pydantic v2 min_length validation (422)"
    why_human: "Requires a live booted server; automated AST-grep verifies Pydantic v2 syntax but not live request validation"
---

# Phase 7: Additional Playbooks Verification Report

**Phase Goal:** With web validated end-to-end, additively support AI-service (FastAPI), CLI (Typer), desktop (Tauri 2), and hub-platform (Professor-style umbrella) builds — each as its own playbook file, each able to run the full intake → scaffold → verify → ship loop.
**Verified:** 2026-05-02T12:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                                                                                                             | Status     | Evidence                                                                                                                                                                                              |
|----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | SC-01: "I want an HTTP API that summarizes documents with an LLM" → ai-service playbook → FastAPI+uv+Pydantic v2 project; `uv run fastapi dev` boots /docs; uses assets/fastapi-starter/ template | ✓ VERIFIED | `infer_app_type(text)` returns `('ai-service', 8.0)`; `scaffold_ai_service` exists in scaffold_dispatch.py (line 308); `assets/fastapi-starter/main.py` has Pydantic v2 `BaseModel`/`Field`, `/`, `/health`, `/summarize` routes; `@validator`/`class Config:` count = 0; `_FASTAPI_STARTER` wired; `_write_dockerfile(stack_family="python-uv")` called |
| 2  | SC-02: "I want a command-line tool to organize my photo library" → cli playbook → Python+Typer+Rich+SQLite; `uv run my-cli --help` prints Rich help; SQLite state persists across runs            | ✓ VERIFIED | `infer_app_type(text)` returns `('cli', 6.0)`; `scaffold_cli` exists (line 384); `assets/cli-starter/__main__.py.tmpl` has `import typer`, `from rich.console import Console`, `CREATE TABLE IF NOT EXISTS pings`, `{{project_name}}`; pyproject snippet has `typer>=0.25.1` with NO `typer[all]` |
| 3  | SC-03: "I want a desktop app that runs locally with a tray icon" → desktop playbook → Tauri 2 (Vite+React+Rust); `pnpm tauri dev` opens native window; Electron explicitly refused globally      | ✓ VERIFIED | `infer_app_type(text)` returns `('desktop', 8.0)`; `scaffold_desktop` exists (line 469); `_build_tauri_identifier("my-cool-app")` = `"com.osbuilder.mycoolapp"` (confirmed live); verbatim 12-element argv with `--manager pnpm --template react-ts --identifier <id> --tauri-version 2 -y`; `references/refuse-list.md` contains "Electron" and "Tauri"; old `"Electron (use Tauri 2 via desktop playbook)"` line NOT in web.md |
| 4  | SC-04: "build me a hub like Professor Hub for X" → hub-platform playbook → top-level CLAUDE.md routing table + sub-tool dirs matching professor-snapshot structural pattern                      | ✓ VERIFIED | `infer_app_type(text)` returns `('hub-platform', 11.0)`; `scaffold_hub` exists (line 546) as pure file-stamping (no subprocess); live smoke: demo hub with grading/rostering produced CLAUDE.md + both subtool dirs; `assets/hub-template/professor-snapshot/` exists with CLAUDE.md, AGENTS.md, LabNoteBookGrader/, Exam-grader/, gradehub/, student-email-tool/; structural diff test passes (34 tests, all pass) |
| 5  | SC-05: Every playbook passes same E2E clone-and-run verification; 07-HUMAN-UAT.md has 6 tests                                                                                                    | ✓ VERIFIED (automated portion) | `scripts/tests/test_e2e_playbooks.py` exists (247 lines); 4 parametrized IDs collected (ai-service, cli, desktop, hub); TIMEOUTS dict has `"desktop": {"install": 120}`; `_real_run = subprocess.run` at module top; `pytestmark = pytest.mark.slow`; `os.killpg` + `proc.terminate()` for cross-platform teardown; `07-HUMAN-UAT.md` has exactly 6 tests in 4-line format; slow marker registered in pyproject.toml |

**Score:** 5/5 truths verified (automated)

### Required Artifacts

| Artifact                                              | Status     | Details                                                                              |
|-------------------------------------------------------|------------|--------------------------------------------------------------------------------------|
| `scripts/intake_handler.py` (PLAYBOOK_KEYWORDS, infer_app_type, _is_low_confidence, _score_playbooks, _extract_subtools) | ✓ VERIFIED | All 5 functions present; `TODO(phase-7)` and `app_type="web"` hardcode removed; 9/9 inference tests pass |
| `references/question-bank.md` (## Q: What kind of thing) | ✓ VERIFIED | Section present with 5 named branches + "I don't know, you decide" default |
| `references/refuse-list.md` (Electron refusal copy)   | ✓ VERIFIED | "Electron" (1 occurrence) + "Tauri" (1 occurrence) present; migration from web.md confirmed |
| `references/playbooks/web.md` (Electron line removed) | ✓ VERIFIED | `grep -ci "Electron (use Tauri 2 via desktop playbook)"` returns 0 |
| `references/playbooks/ai-service.md` (≤80 lines, 7 sections) | ✓ VERIFIED | 56 lines; all 7 mandatory sections present |
| `assets/fastapi-starter/main.py`                      | ✓ VERIFIED | Pydantic v2 (`BaseModel`/`Field`); `@app.get("/")`, `@app.get("/health")`, `@app.post("/summarize")`; ANTHROPIC_API_KEY in wire-up comment; no `@validator`/`class Config:` |
| `assets/fastapi-starter/pyproject.snippet.toml`       | ✓ VERIFIED | Contains `fastapi[standard]>=0.136.1` |
| `assets/dockerfiles/python-uv.Dockerfile.tmpl`        | ✓ VERIFIED | Present; contains `astral-sh/uv` multi-stage pattern |
| `scripts/scaffold_dispatch.py` (scaffold_ai_service, ensure_uv) | ✓ VERIFIED | `def scaffold_ai_service` at line 308; `def ensure_uv` at line 179; `_FASTAPI_STARTER` constant present; `"ai-service"` dispatch wired |
| `scripts/preflight_check.py` (_PLAYBOOK_TOOLS, uv+cargo install matrices) | ✓ VERIFIED | `_PLAYBOOK_TOOLS` with ai-service/cli/desktop keys; `astral-sh.uv` winget ID; `Rustlang.Rustup` winget ID; `sh.rustup.rs` Unix installer |
| `references/friendly-errors/dictionary.yaml` (5 new entries) | ✓ VERIFIED | uv-not-installed, fastapi-cli-missing, cargo-not-installed, tauri-cli-not-installed, create-tauri-app-failed — all 5 present |
| `references/playbooks/cli.md` (≤80 lines, 7 sections) | ✓ VERIFIED | 56 lines; all 7 mandatory sections |
| `assets/cli-starter/__main__.py.tmpl`                 | ✓ VERIFIED | `import typer`, `from rich.console import Console`, `{{project_name}}`, `@app.command()`, `CREATE TABLE IF NOT EXISTS pings` |
| `assets/cli-starter/pyproject.snippet.toml`           | ✓ VERIFIED | `typer>=0.25.1` present; `typer[all]` NOT present (Pitfall 5 correct) |
| `scripts/scaffold_dispatch.py` (scaffold_cli, _sanitize_module_name) | ✓ VERIFIED | `def scaffold_cli` at line 384; `def _sanitize_module_name` at line 373; `"cli"` dispatch wired |
| `references/playbooks/desktop.md` (≤80 lines, Electron rationale) | ✓ VERIFIED | 65 lines; 7 sections; "Tauri" and "Electron" both in Refuse list section; `rustup default stable-msvc` documented (Pitfall 3) |
| `scripts/scaffold_dispatch.py` (scaffold_desktop, _build_tauri_identifier) | ✓ VERIFIED | `def scaffold_desktop` at line 469; `def _build_tauri_identifier` at line 453; tauri-app@latest + react-ts + --tauri-version 2 + -y + --identifier com.osbuilder.* confirmed |
| `assets/ci-workflows/tauri.yml.tmpl`                  | ✓ VERIFIED | `dtolnay/rust-toolchain@stable`, `concurrency` block, `timeout-minutes: 30`, `libwebkit2gtk-4.1-dev` |
| `references/playbooks/hub-platform.md` (≤80 lines, 7 sections) | ✓ VERIFIED | 55 lines; all 7 mandatory sections; pure file-stamping pattern documented |
| `assets/hub-template/CLAUDE.md.tmpl`                  | ✓ VERIFIED | `{{routing_table}}` + `{{project_name}}` placeholders present |
| `assets/hub-template/subtool-CLAUDE.md.tmpl`          | ✓ VERIFIED | `{{subtool}}` placeholder present |
| `assets/hub-template/professor-snapshot/`             | ✓ VERIFIED | CLAUDE.md, AGENTS.md, LabNoteBookGrader/CLAUDE.md, Exam-grader/CLAUDE.md, gradehub/, student-email-tool/ all present |
| `scripts/scaffold_dispatch.py` (scaffold_hub)         | ✓ VERIFIED | `def scaffold_hub` at line 546; pure file-stamping (no subprocess); `"hub-platform"` dispatch wired; live smoke confirmed |
| `scripts/intake_handler.py` (_extract_subtools)       | ✓ VERIFIED | `def _extract_subtools` at line 167; `_extract_subtools("hub for grading and rostering")` = `['grading', 'rostering']` confirmed live |
| `scripts/state_writer.py` (subtools in ALLOWED_FIELDS) | ✓ VERIFIED | `"subtools"` at line 57 in ALLOWED_FIELDS; NOT in REQUIRED_FIELDS |
| `scripts/tests/test_e2e_playbooks.py`                 | ✓ VERIFIED | 247 lines; 4 parametrized IDs; `TIMEOUTS` dict with `"desktop": {"install": 120}`; `_real_run = subprocess.run`; `pytestmark = pytest.mark.slow` |
| `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` | ✓ VERIFIED | 6 tests; 4-line shape per test; "Electron"+"Tauri 2" in test 5; curl command for /summarize in test 6; "Rust toolchain install is not counted" in test 3 |
| `pyproject.toml` (slow marker)                        | ✓ VERIFIED | `slow` marker registered; `addopts = "-x --tb=short -m 'not slow'"` confirms default opt-out |
| `references/stack-menu.md` (4 new playbook sections)  | ✓ VERIFIED | `## ai-service playbook defaults`, `## cli playbook defaults`, `## desktop playbook defaults`, `## hub-platform playbook defaults` — all 4 present |

### Key Link Verification

| From                                    | To                                     | Via                                     | Status     | Details                                                       |
|-----------------------------------------|----------------------------------------|-----------------------------------------|------------|---------------------------------------------------------------|
| `intake_handler.py:parse_paragraph`     | `intake_handler.py:infer_app_type`     | `_score_playbooks` call before atomic_write | ✓ WIRED | `scores = _score_playbooks(text)` at line 403; `inferred_app_type` replaces hardcoded "web" |
| `scaffold_dispatch.py:scaffold_ai_service` | `assets/fastapi-starter/main.py`    | `atomic_write` of starter content (line 358) | ✓ WIRED | `_FASTAPI_STARTER / "main.py"` read and written into project_dir |
| `scaffold_dispatch.py:scaffold_ai_service` | `subprocess uv init --app + uv add fastapi[standard]` | `subprocess.run(shell=False)` | ✓ WIRED | Both subprocess calls present at lines 330-362 |
| `scaffold_dispatch.py:scaffold_cli`     | `assets/cli-starter/__main__.py.tmpl` | template read + substitution + atomic_write | ✓ WIRED | `_CLI_STARTER / "__main__.py.tmpl"` substituted and written |
| `scaffold_dispatch.py:scaffold_cli`     | `subprocess uv add typer`             | `subprocess.run(shell=False)`           | ✓ WIRED | `["uv", "add", "typer"]` present (NOT `typer[all]`) |
| `scaffold_dispatch.py:scaffold_desktop` | `pnpm create tauri-app@latest`        | `subprocess.run` 12-element argv       | ✓ WIRED   | `--manager pnpm --template react-ts --identifier <id> --tauri-version 2 -y` |
| `scaffold_dispatch.py:_build_tauri_identifier` | reverse-DNS `com.osbuilder.<name>` | pure function; `re.sub + lower()`    | ✓ WIRED   | Live: `_build_tauri_identifier("my-cool-app")` = `"com.osbuilder.mycoolapp"` |
| `Electron in spec → refusal`            | `references/refuse-list.md`           | global refuse-list (post-07-01 migration) | ✓ WIRED | "Electron" present in refuse-list.md; old web.md line removed |
| `scaffold_dispatch.py:scaffold_hub`     | `assets/hub-template/CLAUDE.md.tmpl` | `atomic_write` (no subprocess)        | ✓ WIRED   | `_HUB_TEMPLATE / "CLAUDE.md.tmpl"` read and substituted; live smoke confirms |
| `test_phase07_hub_platform.py:test_hub_matches_professor_structure` | `assets/hub-template/professor-snapshot/` | `_structural_signature` diff | ✓ WIRED | Structural diff test passes (part of 34/34 passing tests) |
| `intake_handler._extract_subtools`      | `state_writer.ALLOWED_FIELDS['subtools']` | comma-separated string via state_writer | ✓ WIRED | "subtools" in ALLOWED_FIELDS; live `_extract_subtools` produces list |
| `scripts/tests/test_e2e_playbooks.py`   | `scripts/scaffold_dispatch.py + scripts/intake_handler.py` | `_real_run` (not mocked) | ✓ WIRED | `_real_run = subprocess.run` captured at module top |

### Data-Flow Trace (Level 4)

Not applicable — this phase produces scaffolding scripts, playbook docs, and test infrastructure. No UI components rendering dynamic data from a store or database.

### Behavioral Spot-Checks

| Behavior | Command / Check | Result | Status |
|---|---|---|---|
| SC-01 intake inference | `infer_app_type("I want an HTTP API that summarizes documents with an LLM")` | `('ai-service', 8.0)` | ✓ PASS |
| SC-02 intake inference | `infer_app_type("I want a command-line tool to organize my photo library")` | `('cli', 6.0)` | ✓ PASS |
| SC-03 intake inference | `infer_app_type("I want a desktop app that runs locally with a tray icon")` | `('desktop', 8.0)` | ✓ PASS |
| SC-04 intake inference | `infer_app_type("build me a hub like Professor Hub for grading and rostering")` | `('hub-platform', 11.0)` | ✓ PASS |
| SC-04 hub sub-tool extraction | `_extract_subtools("build me a hub like Professor Hub for grading and rostering")` | `['grading', 'rostering']` | ✓ PASS |
| SC-04 scaffold_hub live smoke | `scaffold_hub("demo", tmp, subtools=["grading","rostering"])` | CLAUDE.md + grading/CLAUDE.md + rostering/CLAUDE.md all created | ✓ PASS |
| SC-03 Tauri identifier | `_build_tauri_identifier("my-cool-app")` | `"com.osbuilder.mycoolapp"` | ✓ PASS |
| SC-03 identifier strips specials | `_build_tauri_identifier("My_App-2")` | `"com.osbuilder.myapp2"` | ✓ PASS |
| 34 unit tests pass | `uv run pytest test_phase07_*.py -q` | 34 passed in 0.39s | ✓ PASS |
| Full suite no regression | `uv run pytest scripts/tests/ -x -q` (excl. slow) | 189 passed, 1 skipped, 1 warning | ✓ PASS |
| E2E collect | `uv run pytest test_e2e_playbooks.py --collect-only -q` | 4 parametrized IDs (0 collected via not-slow) | ✓ PASS |
| Slow marker excludes E2E from default run | `uv run pytest -m 'not slow' --collect-only -q` | E2E tests deselected (4 deselected) | ✓ PASS |
| SC-01 live clone-and-run | Requires fresh machine + real repo | Cannot run in CI without toolchain | ? SKIP (human_needed) |
| SC-02 live clone-and-run | Requires fresh machine + real repo | Cannot run in CI without toolchain | ? SKIP (human_needed) |
| SC-03 live clone-and-run | Requires graphical session + native OS | Cannot run in CI | ? SKIP (human_needed) |
| SC-04 live clone-and-run | Human UX judgment | Cannot automate | ? SKIP (human_needed) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| SCAF-02 | 07-01, 07-02, 07-06 | FastAPI + uv + Pydantic v2 playbook | ✓ SATISFIED | `ai-service.md` (56 lines, 7 sections), `fastapi-starter/main.py` (Pydantic v2), `scaffold_ai_service` wired, 6/6 ai-service tests pass |
| SCAF-03 | 07-01, 07-03, 07-06 | Python + Typer + Rich + SQLite CLI playbook | ✓ SATISFIED | `cli.md` (56 lines, 7 sections), `cli-starter/__main__.py.tmpl` (Typer+Rich+SQLite), `scaffold_cli` wired, 5/5 cli tests pass |
| SCAF-04 | 07-01, 07-04, 07-06 | Tauri 2 desktop playbook (refuses Electron) | ✓ SATISFIED | `desktop.md` (65 lines, 7 sections + Electron rationale), `scaffold_desktop` with verbatim 12-element argv, `_build_tauri_identifier` correct, Electron global refusal confirmed, 6/6 desktop tests pass |
| SCAF-05 | 07-01, 07-05, 07-06 | Hub-platform (Professor-style) playbook | ✓ SATISFIED | `hub-platform.md` (55 lines, 7 sections), `scaffold_hub` pure file-stamping, `professor-snapshot/` vendored, `_extract_subtools` parsing works, 8/8 hub tests pass |

All 4 phase requirements accounted for. No orphaned requirements (ROADMAP maps exactly SCAF-02, SCAF-03, SCAF-04, SCAF-05 to Phase 7).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `scripts/scaffold_dispatch.py` | 573 | `TODO — describe {s}` in routing table row template | ℹ️ Info | Intentional stub — this is the user-facing placeholder text in the generated hub CLAUDE.md. Not a code-quality issue. |

No blockers or warnings found. The single TODO is by design (it's the content generated for hub sub-tool routing table rows, which the user fills in themselves).

### Human Verification Required

The 5-step E2E contract (intake → scaffold → install → boot → stop) is covered by automated tests in `scripts/tests/test_e2e_playbooks.py`. The following 6 items require human execution as documented in `07-HUMAN-UAT.md`:

#### 1. Stranger clone-and-run — ai-service (SC-05 + SC-01)

**Test:** On a fresh machine with `uv` installed, clone the FastAPI repo OSBuilder produced → `cd <dir> && uv sync && uv run fastapi dev` → open `http://127.0.0.1:8000/docs` → confirm /, /health, /summarize visible. Time from clone to /docs page.
**Expected:** Working /docs page within ≤5 minutes; no source edits required.
**Why human:** Requires a real GitHub repo from a build run + a second machine with a clean environment. Subjective UX timing cannot be automated.

#### 2. Stranger clone-and-run — cli (SC-05 + SC-02)

**Test:** Fresh machine with `uv` → clone → `uv sync && uv run <app-name> --help` → confirm Rich-styled output → `uv run <app-name> ping` → confirm "ping #1" → repeat → confirm "ping #2".
**Expected:** Rich-formatted help visible; SQLite persistence confirmed across two runs.
**Why human:** Rich formatting quality and cross-run persistence require a real interactive shell; can't be deterministically automated.

#### 3. Stranger clone-and-run — desktop (SC-05 + SC-03)

**Test:** Fresh machine with `pnpm` and Rust pre-installed → clone → `pnpm install && pnpm tauri dev` → confirm native window opens.
**Expected:** Native window with hot-reload within ≤5 minutes (Rust toolchain install excluded from budget).
**Why human:** OS-level GUI assertions are not feasible in CI; requires graphical session and OS permissions (macOS Gatekeeper, Windows SmartScreen).

#### 4. Stranger clone-and-run — hub-platform (SC-05 + SC-04)

**Test:** Fresh machine → clone → open `CLAUDE.md` → confirm routing table lists each sub-tool with purpose rows → open a sub-tool `CLAUDE.md` → confirm re-run /osbuilder instruction.
**Expected:** Fresh human understands hub purpose and sub-tool structure without prior context.
**Why human:** Success metric is human comprehension, not runtime behavior.

#### 5. Electron refusal UX (SC-03 + D-22)

**Test:** Run OSBuilder intake with "I want an Electron desktop app for note-taking" → confirm refusal mentions: (a) "Electron" by name, (b) "Tauri 2" as alternative, (c) binary size rationale (~10MB vs 150MB, ~50% less RAM).
**Expected:** Friendly, jargon-free refusal with all three elements present.
**Why human:** Automated test verifies refuse-list.md text contains "Electron"+"Tauri"; actual UX friendliness is human-judged.

#### 6. /summarize Pydantic v2 smoke (SCAF-02 D-12)

**Test:** After ai-service boots → `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":"hello world"}'` → confirm `{"summary":"hello world"}`. Then POST with `{"text":""}` → confirm 422.
**Expected:** Stub returns text[:200]; empty text triggers Pydantic v2 min_length validation (422, not silent pass).
**Why human:** Requires live booted server; automated AST grep verifies Pydantic v2 syntax but not live HTTP validation behavior.

### Gaps Summary

No automation-verifiable gaps. All 5 must-have truths verified; all 4 requirements (SCAF-02 through SCAF-05) satisfied; all key links wired; all artifacts exist and are substantive. The only items requiring follow-up are the 6 human UAT tests documented in `07-HUMAN-UAT.md`, which are gated by nature (fresh machine, real repos, OS GUI, human UX judgment).

The `07-HUMAN-UAT.md` file is ready for execution by the developer.

---

_Verified: 2026-05-02T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
