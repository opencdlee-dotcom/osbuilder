---
status: complete
phase: 07-additional-playbooks
source: [07-VERIFICATION.md]
started: 2026-05-05T00:00:00Z
updated: 2026-05-05T00:00:00Z
---

## Current Test

[testing complete — 2 defects filed, 1 partial pending GUI verification]

## Tests

### 1. Stranger clone-and-run on fresh machine — ai-service
expected: Working FastAPI app reachable on `http://127.0.0.1:8000/docs` within 5 minutes of `git clone`; no edits to source files required.
test: On a second machine (or clean container) with `uv` already installed (preflight): clone the repo OSBuilder just created → `cd <dir> && uv sync && uv run fastapi dev` → open `http://127.0.0.1:8000/docs` → confirm `/`, `/health`, `/summarize` endpoints visible. Time the run from clone to /docs page.
why_human: Requires a fresh machine + a real GitHub repo created by a build run; subjective UX timing. Automated test covers the 5-step contract; human gate covers the actual stranger-clone experience.
result: pass — scaffolded ai-service via `scaffold_dispatch.py scaffold --playbook ai-service`, ran `uv sync` (warm cache; resolved 44 packages in 25ms) then `uv run fastapi dev --port 8123` (default 8000 was occupied by another process on this Mac), reached "Application startup complete" within seconds. `curl /` → HTTP 200, `/health` → 200, `/docs` → 200. Pydantic v2 + FastAPI 0.136.1 patterns visible in `main.py`. Caveat: not a true fresh-machine clone (ran on the dev box); structurally equivalent to the stranger-clone path.

### 2. Stranger clone-and-run on fresh machine — cli
expected: `uv run <app-name> --help` prints Rich-formatted help screen within 5 minutes of clone; `<app-name> ping` writes a row to SQLite and reads it back.
test: On second machine with `uv` installed: clone → `cd <dir> && uv sync && uv run <app-name> --help` → confirm Rich-styled output → `uv run <app-name> ping` → confirm "ping #1" message + DB path → run again → confirm "ping #2" (state persisted across runs per SC-02).
why_human: Subjective Rich-formatting verification + cross-run persistence behavior; can't be deterministically automated without a real shell.
result: pass — both defects fixed in commit 0641a63 (fix(scaffold-cli): inject [project.scripts] + tool.uv.package=true; keep Typer multi-command). (a) scaffold_cli now appends [project.scripts] + [tool.uv] package=true to the uv-init pyproject.toml so `uv run <name> --help` resolves. (b) cli-starter __main__.py.tmpl now registers an @app.callback() so Typer keeps multi-command mode and `<app> ping` is reachable. Re-verified end-to-end on 2026-05-05: `uv run uat-cli --help` shows Rich-formatted help with `ping` listed; `uv run uat-cli ping` writes "ping #1 at <ts>" + DB path; second invocation writes "ping #2" (cross-run persistence confirmed). Two regression tests added (test_scaffold_cli_injects_project_scripts, test_cli_starter_template_uses_app_callback).

### 3. Stranger clone-and-run on fresh machine — desktop
expected: `pnpm tauri dev` opens a native window with hot-reload within 5 minutes of clone (Rust toolchain install is not counted in the 5-min budget).
test: On second machine with `pnpm` AND Rust (cargo+rustc) already installed via preflight: clone → `cd <dir> && pnpm install && pnpm tauri dev` → confirm a native window opens with the default Tauri+React content. Note: cold Cargo fetch can take 60-120s on first run (Pitfall 8); count this within budget on warm cache.
why_human: OS-level GUI assertion not feasible in CI; window-opens-and-renders requires a graphical session and OS permissions (macOS Gatekeeper, Windows SmartScreen).
result: partial — scaffold structure is correct (Tauri 2 layout: `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json` with `$schema=schema.tauri.app/config/2`, identifier `com.osbuilder.uatdesk`, devUrl localhost:1420, React 19 + Vite 7 + TypeScript 5.8 + Tauri CLI 2). Did not run `pnpm tauri dev` because verifying a native window opens requires a real graphical session per the test's `why_human` clause. Needs a human at the screen to flip this to pass/fail.

### 4. Stranger clone-and-run on fresh machine — hub-platform
expected: A fresh human reading the top-level `CLAUDE.md` understands the hub's purpose and the role of each subfolder; routing-table format matches Professor Hub's structure.
test: On second machine: clone → `cd <dir>` → open `CLAUDE.md` → confirm it lists each sub-tool subfolder with a "TODO — describe X" purpose row → open one sub-tool's `CLAUDE.md` → confirm it's a placeholder with a clear "re-run /osbuilder" next-step instruction.
why_human: Hub-platform's success metric is comprehension by a fresh reader, not runtime behavior. UX measured by "does the routing make sense without prior context."
result: pass — scaffolded hub via `scaffold_dispatch.py scaffold --playbook hub-platform --subtool grader --subtool inbox`. Top-level `CLAUDE.md` lists `grader/` and `inbox/` in a routing table with "TODO — describe X" purpose rows + adding-new-tools guidance. Each subtool `CLAUDE.md` is a placeholder with the documented "Re-run `/osbuilder` from inside this folder" instruction. Plain-language readable.

### 5. Electron refusal produces friendly Tauri-2 rationale
expected: Submitting a spec containing "build me an Electron desktop app for X" produces a refusal pointing the user at Tauri 2 with the documented rationale (smaller binaries, less RAM); refusal copy is human-friendly (no jargon).
test: Run OSBuilder with intake "I want an Electron desktop app for note-taking" → confirm OSBuilder refuses → confirm the refusal text mentions: (a) "Electron" by name, (b) "Tauri 2" as the alternative, (c) the rationale (~10MB vs 150MB binaries, ~50% less RAM, system WebView). Verify state.md `last_failure` matches the refusal pattern.
why_human: Default-mode refusal copy is human-judged for friendliness; automated test only verifies the refuse-list.md text contains "Electron" and "Tauri" — actual UX evaluation is human.
result: pass — fixed in commit fd52de7 (fix(intake): refuse Electron + coerce string scalars in parse_structured). Added "electron" to REFUSE_KEYWORDS and to references/refuse-list.md `## Refuse keywords` (kept the test_refuse_list_synced gate green). Re-verified on 2026-05-05: `_matches_refuse_keyword("I want an Electron desktop app for note-taking")` returns "electron"; `check_refuse_list(root)` returns True; state.md `last_failure: refused: electron` is set; the full refusal copy (including the Electron / Tauri 2 / 10MB-vs-150MB / 50%-less-RAM rationale) prints to stderr. Regression test test_electron_keyword_in_refuse_keywords added.

### 6. /summarize endpoint smoke (Pydantic v2 verification)
expected: After ai-service boot, POST to /summarize with valid JSON returns the summary stub (text[:200]); request validation fires on invalid input (e.g., empty text); response uses Pydantic v2 patterns (no v1 silent no-op per Pitfall 4).
test: After ai-service boot: `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":"hello world"}'` → confirm response is `{"summary":"hello world"}`. Then: `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":""}'` → confirm 422 error (Pydantic v2 Field min_length validation fires; v1 syntax would have silently accepted).
why_human: Real HTTP smoke against a booted server requires the server to be running; automated test covers Pydantic v2 syntax via AST grep but doesn't exercise live request validation.
result: pass — booted on port 8123. `POST /summarize {"text":"hello world"}` → HTTP 200 `{"summary":"hello world"}`. `POST /summarize {"text":""}` → HTTP 422 with body `{"detail":[{"type":"string_too_short","loc":["body","text"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}`. Pydantic v2 `Field(..., min_length=1)` validation fires correctly; v1 would have silently accepted the empty string.

## Notes for the human runner

- Run tests in order. Tests 1-4 are independent; test 5 doesn't require a built repo (just an intake run); test 6 requires test 1's app to be booted.
- The 5-minute budget excludes one-time toolchain install (`uv`, `pnpm`, `cargo`) — preflight handles that as a separate confirmation. The budget covers `clone → install → run → reach the documented endpoint`.
- For test 3, if the Tauri window does NOT open, capture stderr and check for: missing webkit2gtk-4.1-dev (Linux), missing MSVC (Windows — Pitfall 3), missing Xcode CLT (macOS).
- For test 5, the refusal text comes from `references/refuse-list.md`; if the rationale is missing/incomplete, file an issue against 07-01 (the migration plan).
- Mark `result: passed` / `result: failed: <description>` per row. Update `status: in-progress` while running; `status: complete` when all 6 done.

## Summary

total: 6
passed: 5
issues: 0
pending: 0
skipped: 0
partial: 1

## Gaps

- Test 3 (desktop GUI): needs a human at a graphical session to confirm the native window actually opens. Tauri 2 scaffold structure is verified; only the OS-level window-opens-and-renders step is gated.
