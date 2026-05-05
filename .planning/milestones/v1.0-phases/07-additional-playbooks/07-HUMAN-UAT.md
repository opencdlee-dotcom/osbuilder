---
status: pending
phase: 07-additional-playbooks
source: [07-VERIFICATION.md]
started:
updated:
---

## Current Test

[pending — runner has not started]

## Tests

### 1. Stranger clone-and-run on fresh machine — ai-service
expected: Working FastAPI app reachable on `http://127.0.0.1:8000/docs` within 5 minutes of `git clone`; no edits to source files required.
test: On a second machine (or clean container) with `uv` already installed (preflight): clone the repo OSBuilder just created → `cd <dir> && uv sync && uv run fastapi dev` → open `http://127.0.0.1:8000/docs` → confirm `/`, `/health`, `/summarize` endpoints visible. Time the run from clone to /docs page.
why_human: Requires a fresh machine + a real GitHub repo created by a build run; subjective UX timing. Automated test covers the 5-step contract; human gate covers the actual stranger-clone experience.
result: <pending>

### 2. Stranger clone-and-run on fresh machine — cli
expected: `uv run <app-name> --help` prints Rich-formatted help screen within 5 minutes of clone; `<app-name> ping` writes a row to SQLite and reads it back.
test: On second machine with `uv` installed: clone → `cd <dir> && uv sync && uv run <app-name> --help` → confirm Rich-styled output → `uv run <app-name> ping` → confirm "ping #1" message + DB path → run again → confirm "ping #2" (state persisted across runs per SC-02).
why_human: Subjective Rich-formatting verification + cross-run persistence behavior; can't be deterministically automated without a real shell.
result: <pending>

### 3. Stranger clone-and-run on fresh machine — desktop
expected: `pnpm tauri dev` opens a native window with hot-reload within 5 minutes of clone (Rust toolchain install is not counted in the 5-min budget).
test: On second machine with `pnpm` AND Rust (cargo+rustc) already installed via preflight: clone → `cd <dir> && pnpm install && pnpm tauri dev` → confirm a native window opens with the default Tauri+React content. Note: cold Cargo fetch can take 60-120s on first run (Pitfall 8); count this within budget on warm cache.
why_human: OS-level GUI assertion not feasible in CI; window-opens-and-renders requires a graphical session and OS permissions (macOS Gatekeeper, Windows SmartScreen).
result: <pending>

### 4. Stranger clone-and-run on fresh machine — hub-platform
expected: A fresh human reading the top-level `CLAUDE.md` understands the hub's purpose and the role of each subfolder; routing-table format matches Professor Hub's structure.
test: On second machine: clone → `cd <dir>` → open `CLAUDE.md` → confirm it lists each sub-tool subfolder with a "TODO — describe X" purpose row → open one sub-tool's `CLAUDE.md` → confirm it's a placeholder with a clear "re-run /osbuilder" next-step instruction.
why_human: Hub-platform's success metric is comprehension by a fresh reader, not runtime behavior. UX measured by "does the routing make sense without prior context."
result: <pending>

### 5. Electron refusal produces friendly Tauri-2 rationale
expected: Submitting a spec containing "build me an Electron desktop app for X" produces a refusal pointing the user at Tauri 2 with the documented rationale (smaller binaries, less RAM); refusal copy is human-friendly (no jargon).
test: Run OSBuilder with intake "I want an Electron desktop app for note-taking" → confirm OSBuilder refuses → confirm the refusal text mentions: (a) "Electron" by name, (b) "Tauri 2" as the alternative, (c) the rationale (~10MB vs 150MB binaries, ~50% less RAM, system WebView). Verify state.md `last_failure` matches the refusal pattern.
why_human: Default-mode refusal copy is human-judged for friendliness; automated test only verifies the refuse-list.md text contains "Electron" and "Tauri" — actual UX evaluation is human.
result: <pending>

### 6. /summarize endpoint smoke (Pydantic v2 verification)
expected: After ai-service boot, POST to /summarize with valid JSON returns the summary stub (text[:200]); request validation fires on invalid input (e.g., empty text); response uses Pydantic v2 patterns (no v1 silent no-op per Pitfall 4).
test: After ai-service boot: `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":"hello world"}'` → confirm response is `{"summary":"hello world"}`. Then: `curl -X POST http://127.0.0.1:8000/summarize -H 'Content-Type: application/json' -d '{"text":""}'` → confirm 422 error (Pydantic v2 Field min_length validation fires; v1 syntax would have silently accepted).
why_human: Real HTTP smoke against a booted server requires the server to be running; automated test covers Pydantic v2 syntax via AST grep but doesn't exercise live request validation.
result: <pending>

## Notes for the human runner

- Run tests in order. Tests 1-4 are independent; test 5 doesn't require a built repo (just an intake run); test 6 requires test 1's app to be booted.
- The 5-minute budget excludes one-time toolchain install (`uv`, `pnpm`, `cargo`) — preflight handles that as a separate confirmation. The budget covers `clone → install → run → reach the documented endpoint`.
- For test 3, if the Tauri window does NOT open, capture stderr and check for: missing webkit2gtk-4.1-dev (Linux), missing MSVC (Windows — Pitfall 3), missing Xcode CLT (macOS).
- For test 5, the refusal text comes from `references/refuse-list.md`; if the rationale is missing/incomplete, file an issue against 07-01 (the migration plan).
- Mark `result: passed` / `result: failed: <description>` per row. Update `status: in-progress` while running; `status: complete` when all 6 done.
