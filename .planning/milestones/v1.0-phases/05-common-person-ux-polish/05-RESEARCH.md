# Phase 5: Common-person UX polish — Research

**Researched:** 2026-04-30
**Domain:** UX shell for an LLM-orchestrator skill — narration, error translation, jargon gating, plain-English documentation
**Confidence:** HIGH for codebase-internal decisions (gsd_driver dispatch points, state_writer extension pattern, friendly-error sources from PITFALLS.md/SUMMARY.md verified by direct file read); MEDIUM for humanizer interface (skill exists at `~/.claude/skills/humanizer/` but exposes only an LLM-driven slash command — `--check` / `--rewrite` flags are NOT in its current contract; this is the most consequential research finding)

---

## Summary

Phase 5 wraps the verified build engine from Phases 1–4 in a UX layer a non-developer can drive. The work is scope-bounded by SPEC.md (locked, ambiguity 0.19): 8 requirements → 7 new files + 4 module-level extensions across the existing codebase. There are no algorithmic unknowns, but there are five architectural decisions the planner must lock and one humanizer-contract gap that needs explicit treatment.

The phase splits into five tracks. Each is independent enough that Wave 1 plans can run in parallel after Wave 0 lays the test scaffold:

**Track A — Narration substrate (`scripts/narration.py` + role briefs):** A single-process Python module that renders role banners, parses subprocess output line-buffered into summaries, and pipes the raw text into a debug log. Loads 8 role briefs at module import (qa.md exists; the other 7 are new). Wired into `gsd_driver.py` at every PHASE_STEP_COMMANDS dispatch boundary (steps 0, 1, 3, 4, 5, 6, 8, plus the new `tech-writer` step) and at every existing `subprocess.run` call site in the 5 listed scripts.

**Track B — Friendly-error layer (`scripts/friendly_error.py` + dictionary + README):** A pure-translation module that converts raw error strings/exceptions into a 5-field FriendlyMessage struct. The dictionary is 30 entries with 8 fields each. Phase 5's hardest format question is YAML-vs-Markdown: stdlib has no YAML parser and the project rule forbids new deps. Recommendation locked below.

**Track C — Tutor mode rendering + `--quiet` plumbing:** Tutor lines emitted by `narration.py` after every `status="ok"` event, sourced from per-role brief data. Forbidden-jargon scan runs at test time (capture stdout, grep against the 6-token list). `--quiet` flag plumbs from OSBuilder entry → `state_writer.py` `mode`-adjacent field → narration.py module init.

**Track D — Beginner/advanced mode gating:** A new `mode` field in state.md's ALLOWED_FIELDS, written by entry-point flag parsing, read by `intake_handler.py`'s question-bank surface and by `stack_researcher.py`/`scaffold_dispatch.py` as a default-resolution gate. Beginner mode auto-resolves stack from `references/stack-menu.md` and deploy target from documented refuse-list defaults; advanced mode surfaces those choices as prompts.

**Track E — Tech Writer phase + humanizer integration:** A new `tech-writer` step (step 8.5 — between `/gsd-verify-work` at step 8 and the phase-advance at step 9) emits `/gsd-docs-update --target=README.md` then `/humanizer @README.md`. The humanizer skill's actual contract is an LLM-driven slash command, NOT a `--check`/`--rewrite` CLI; this is the largest deviation from SPEC and is documented as Open Question 1 with three resolution paths.

**Primary recommendation:** Build Wave 0 first (test infrastructure + state_writer.py ALLOWED_FIELDS extension). Then Wave 1 splits cleanly into 5 plans that can be implemented in parallel by file ownership. Tech Writer + humanizer integration goes in its own plan because it depends on the humanizer-contract resolution (Open Question 1) being answered before code is written.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Role banner rendering (`[PM] ... ✓`) | `scripts/narration.py` | per-role briefs (data) | Single module owns the print/format contract; briefs are data templates |
| Tutor-mode "what happened" line | `scripts/narration.py` | per-role briefs (template strings) | Same module emits banner + tutor line; data driven by role brief |
| Subprocess output capture | `scripts/narration.py` | `gsd_driver.py`, `preflight_check.py`, `scaffold_dispatch.py`, `stack_researcher.py`, `intake_handler.py` | narration owns the capture wrapper; existing scripts adopt it |
| Debug log file write | `scripts/narration.py` | filesystem (`.planning/osbuilder/build.log`) | append-mode; rotation per-build (overwrite on new `state_writer init`) |
| Error string → FriendlyMessage | `scripts/friendly_error.py` | dictionary file (data) | Pure function; loads dictionary at module import |
| Friendly-error dictionary | `references/friendly-errors/dictionary.{yaml\|md}` | `friendly_error.py` (consumer) | Data file; format choice locked below |
| Friendly-error expansion contract | `references/friendly-errors/README.md` | dictionary file | Documentation only |
| `--quiet` / `--advanced` flag plumbing | OSBuilder entry point (SKILL.md → user-invocable invocation) | `state.md` `mode` field via `state_writer.py` | Flags written to state at session start; read by every prompt site |
| Beginner-mode question gating | `scripts/intake_handler.py` (existing) | `state.md` `mode` field, `references/question-bank.md` | Existing intake reads `mode` field; beginner gates technical questions |
| Default-mode stack auto-resolution | `scripts/stack_researcher.py` (existing) | `references/stack-menu.md`, `state.md` `mode` field | Beginner mode skips advanced-only prompts; falls back to stack-menu defaults |
| Tech Writer step dispatch | `scripts/gsd_driver.py` (existing) | PHASE_STEP_COMMANDS extension | New step value 8 (or 8.5) emits `/gsd-docs-update` then `/humanizer` |
| README humanizer score persistence | `scripts/state_writer.py` (existing) | ALLOWED_FIELDS extension | New `humanizer_score` field |
| 7 new role briefs (PM, Architect, Frontend, Backend, DevOps, Reviewer, Tech Writer) | `references/roles/{role}.md` | `narration.py` (consumer) | Markdown files with structured sections; loaded on demand |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UX-01 | Tutor mode ON by default; `--quiet` disables | narration.py emits tutor line after every status="ok"; --quiet suppresses lines starting with `> `; state.md `mode` field gates rendering |
| UX-02 | `friendly_error.py` translates raw failures — never expose stack traces, ENOENT, EACCES | friendly_error.translate() at every subprocess-error path in the 5 listed scripts; raw text → debug log; dictionary loaded at module import |
| UX-03 | Beginner mode default; `--advanced` exposes stack/deploy/scaffolder choices | `mode` field in state.md (`beginner`/`advanced`); intake_handler/question-bank gates jargon-bearing prompts; stack_researcher auto-resolves in beginner mode |
| UX-04 | Per-role narration scripts produce non-jargon progress messages | 7 new briefs in references/roles/; banner template + tutor template + per-step copy + failure copy; loaded on-demand by narration.py |
| UX-05 | Top-30 friendly-error dictionary; documented expansion path | references/friendly-errors/dictionary.{yaml\|md} with 30 entries × 8 fields; README documents format-version + contribution criteria |
| ROLE-07 | Tech Writer delegates to /gsd-docs-update and /humanizer | gsd_driver.py PHASE_STEP_COMMANDS gains tech-writer step; emits /gsd-docs-update then /humanizer; humanizer_score → state.md |
| ROLE-09 | User-facing progress narrated at dev-team level — never raw command output | narration.emit() at every dispatch boundary; subprocess output captured; raw text routed to .planning/osbuilder/build.log |
</phase_requirements>

---

<user_constraints>
## User Constraints (from SPEC.md — treated as locked decisions)

### Locked Decisions

1. **Module surface:** `scripts/friendly_error.py` exposes `translate(raw, ctx) -> FriendlyMessage` returning `{title, what_broke, what_to_do, copy_paste, severity}`. Every error path in `gsd_driver.py`, `preflight_check.py`, `scaffold_dispatch.py`, `stack_researcher.py`, `intake_handler.py` routes through it.
2. **Dictionary entries:** Exactly 30 entries with 8 fields each: `id`, `match_pattern`, `category`, `title`, `what_broke`, `what_to_do`, `copy_paste_command`, `phase_seen`, `expansion_note`. (SPEC says 8 fields; the field list above is 9 — see Open Question 4.)
3. **Dictionary categories:** `preflight | gh-auth | registry | runtime | docker | filesystem | network | git | scaffold` (9 enumerated categories).
4. **Forbidden jargon (6 tokens):** `framework`, `endpoint`, `responsive`, `ORM`, `dependency injection`, `transpiler`. Forbidden in default-mode tutor lines, role banners, and friendly-error messages. Allowed in `--advanced` mode and in role briefs' "advanced copy" sections.
5. **Tutor line prefix:** `> ` by default. Planner may pick a different unique grep-able prefix (Assumption #4 in SPEC).
6. **`--quiet` semantics:** Suppresses tutor lines; keeps role banners and final outputs.
7. **`--advanced` semantics:** Exposes stack choice, deploy target, and scaffolder selection as prompts; default mode resolves them silently to documented defaults.
8. **Tech Writer step:** New step value in `gsd_driver.py`'s PHASE_STEP_COMMANDS that invokes `/gsd-docs-update --target=README.md` then `/humanizer --check README.md`; produces `humanizer_score` in state.md; retry once with `/humanizer --rewrite README.md` then fail if still flagged.
9. **Humanizer fallback:** If humanizer skill is missing or version-drifted, friendly-error + warning to state.md + non-humanizer-gated README.
10. **`mode` field in state.md:** String enum `beginner | advanced`; ALLOWED_FIELDS extension following Phase 4 pattern.
11. **Format choice:** YAML preferred over JSON for dictionary; Markdown table is the documented fallback if YAML loading would require non-stdlib deps.
12. **Localization:** English-first; non-English deferred to v2.
13. **No new Python deps.** Phase 5 stays on Python 3.13 stdlib.

### Claude's Discretion

- Tutor-line prefix character (default `> ` per SPEC; planner may change).
- Friendly-error dictionary file format (YAML default per SPEC; Markdown table fallback documented).
- Per-role brief file structure (4 sections required; section ordering and exact heading text are open).
- Subprocess capture mechanism (threading vs asyncio vs select — recommended below).
- Build.log rotation policy (per-build vs per-phase vs append-forever — recommended below).
- Tech Writer step number in PHASE_STEP_COMMANDS (between current step 8 and step 9 phase-advance).

### Deferred Ideas (OUT OF SCOPE)

- `gh repo create --private` / push / runbook generation — Phase 6.
- `.env.example` / `compose.yaml` / `Dockerfile` / `.github/workflows/*.yml` scaffold defaults — Phase 6.
- Friendly-error dictionary entries 31+ — expansion-path concern (the contribution contract documented in this phase governs them).
- Voice intake or multimodal narration — v2.
- Localization to non-English — v2.
- K8s / observability / Sentry / rate-limiting narration copy — Phase 8 (`--production-ready`).
- Runtime humanizer rewrite suggestions inside the live tutor stream — humanizer runs only against the final README.
- Changes to the Phase 4 failure classifier or registry gate — Phase 5 only consumes their outputs.
</user_constraints>

---

## Standard Stack

### Phase 5 New Code

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.13 | All new modules — `narration.py`, `friendly_error.py` | No new deps allowed (locked); stdlib has every primitive needed |
| `subprocess.Popen` + `select.select` (POSIX) / `subprocess.run` capture (Windows fallback) | built-in | Line-buffered subprocess output capture | Standard pattern for streaming subprocess output without deadlock; matches the existing project pattern in `preflight_check.py` and `scaffold_dispatch.py` |
| `pathlib.Path` | built-in | All filesystem paths in narration.py / friendly_error.py | Existing project convention (state_writer.py, gsd_driver.py) |
| `re` | built-in | Friendly-error match-pattern matching; jargon-scan tests | Stdlib regex; first-match precedence ordering |
| `json` | built-in | If JSON dictionary chosen; humanizer_score parsing | Stdlib; no comments / multi-line strings (this is the YAML-vs-JSON tradeoff) |
| `pytest` | 9.0.2 (existing) | Test suite extension: `test_narration.py`, `test_friendly_error.py`, `test_tutor_mode.py`, `test_mode_gating.py`, `test_tech_writer.py` | Existing infrastructure |

### Per-build Stack (no change — this phase doesn't pick stacks)

[VERIFIED: existing stack-menu.md is unchanged in scope.] Phase 5 does not introduce new stack choices for built apps. It reads `references/stack-menu.md` defaults and propagates them through `mode=beginner`.

### Documentation-Lookup Verification

- Python 3.13 `subprocess` docs verified via stdlib reference: `subprocess.Popen` accepts `stdout=subprocess.PIPE`, `stderr=subprocess.PIPE`, `bufsize=1` (line-buffered), `text=True` (decoded). [VERIFIED: Python 3.13 stdlib docs, accessed 2026-04-30]
- `select.select` works on POSIX file descriptors but NOT on Windows pipes; for Windows compatibility a small thread-per-stream pattern is the documented stdlib solution. [VERIFIED: Python 3.13 docs — `select.select` "Note: On Windows, only sockets are supported"]
- `urllib.request` HEAD pattern from Phase 4 carries forward unchanged; not relevant to Phase 5.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stdlib YAML subset parser | `pyyaml` (third-party) | Banned by project rule "no new Python deps" |
| YAML dictionary | JSON dictionary | Stdlib supports JSON natively but no comments / no multi-line strings — readability suffers for 30-entry hand-edited file |
| YAML dictionary | Markdown table | Stdlib supports str.split / re — works but harder to validate schema; more vulnerable to formatting drift |
| `subprocess.run(capture_output=True)` then post-print | `subprocess.Popen` line-buffered streaming | `run` blocks until subprocess exits — long-running commands look frozen to the user. Streaming is correct for narration. |
| `select.select` (POSIX-only) | thread-per-stream | `select` is simpler for POSIX but breaks on Windows. Thread pattern is portable. **Recommendation: thread-per-stream for Windows compatibility per Phase 2's cross-platform mandate.** |
| Re-implementing humanizer logic in Python | Delegating to `/humanizer` slash command | SPEC explicitly forbids embedding humanizer; "Phase 5 does not embed humanizer logic; it only invokes it." |

**Installation:** No new packages. All work is stdlib + new Python files + new Markdown files.

**Version verification:**
```bash
python3 --version    # ≥ 3.13 (current 3.12.6 on dev machine; preflight installer ensures 3.13+)
python3 -c "import select, subprocess, pathlib, re, json; print('all stdlib OK')"
python3 -m pytest --version    # 9.0.2 [VERIFIED: 04-RESEARCH.md baseline]
```

---

## Architecture Patterns

### System Architecture Diagram

```
PHASE 4 OUTPUT
  │  state.md (current_phase, current_role, retry_count, etc.)
  │  failure_classifier.py + registry_verify.py + gsd_driver.py running
  │  raw subprocess output reaches user; no friendly errors; no narration
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  OSBuilder ENTRY POINT (SKILL.md user-invocable)                 │
│  Parses flags: --quiet, --advanced, --tutor, --no-docker, etc.  │
│  Writes mode={beginner|advanced} to state.md                     │
│  Writes tutor_enabled={true|false} (or just relies on mode)      │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/gsd_driver.py — Phase loop state machine (existing)     │
│  EXTENDED IN PHASE 5:                                            │
│  - Calls narration.emit(role, action, "start", detail) BEFORE   │
│    every PHASE_STEP_COMMANDS dispatch                            │
│  - Calls narration.emit(role, action, "ok", detail) AFTER each  │
│    successful dispatch                                           │
│  - Calls narration.emit(role, action, "fail", detail) AFTER any │
│    failure (which itself routes through friendly_error.translate)│
│  - PHASE_STEP_COMMANDS gains a new entry:                        │
│      8.5 (or new step ID): "tech-writer" → /gsd-docs-update     │
│           + /humanizer with retry logic (see Track E)            │
└──────────────┬─────────────────────────────────────┬─────────────┘
               │                                     │
               ▼                                     ▼
┌─────────────────────────────────────────┐  ┌────────────────────────┐
│  scripts/narration.py (NEW)             │  │  scripts/friendly_     │
│                                         │  │  error.py (NEW)        │
│  Public API:                            │  │                        │
│    emit(role, action, status, detail)   │  │  Public API:           │
│    capture_subprocess(cmd, role, action)│  │    translate(raw, ctx) │
│      → wraps subprocess.Popen with      │  │      → FriendlyMessage │
│        line-buffered stdout/stderr      │  │    load_dictionary()   │
│        capture; user sees summary;      │  │      → list[Entry]     │
│        raw text appended to build.log   │  │                        │
│                                         │  │  Internal:             │
│  Loads at import:                       │  │    _DICTIONARY = ... at│
│    role briefs from references/roles/   │  │      module import     │
│      *.md (8 files: qa.md + 7 new)     │  │    _ensure_format_     │
│    forbidden-jargon list (6 tokens)     │  │      version() check   │
│                                         │  │    _generic_translator │
│  Reads at every emit:                   │  │      (fallback when no │
│    state.md `mode` field                │  │       dict entry hits) │
│    state.md `tutor_enabled` (derived    │  │                        │
│      from --quiet flag)                 │  │  Reads at import:      │
│                                         │  │    references/friendly-│
│  Output paths:                          │  │      errors/dictionary │
│    stdout (banners + tutor lines)       │  │      .{yaml|md}        │
│    .planning/osbuilder/build.log (raw)  │  │                        │
│                                         │  └──────────────┬─────────┘
└──────────────┬──────────────────────────┘                 │
               │                                            │
               │  every existing subprocess.run call site    │
               │  in the 5 listed scripts wraps through      │
               │  narration.capture_subprocess(...)          │
               │  AND every error path calls                 │
               │  friendly_error.translate(raw, ctx) before  │
               │  emitting fail-status narration             │
               │                                            │
               ▼                                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  references/                                                     │
│  ├── roles/                                                      │
│  │   ├── qa.md                          (existing — Phase 4)    │
│  │   ├── pm.md                          (NEW)                   │
│  │   ├── architect.md                   (NEW)                   │
│  │   ├── frontend.md                    (NEW)                   │
│  │   ├── backend.md                     (NEW)                   │
│  │   ├── devops.md                      (NEW)                   │
│  │   ├── reviewer.md                    (NEW)                   │
│  │   └── tech-writer.md                 (NEW)                   │
│  └── friendly-errors/                                            │
│      ├── dictionary.{yaml|md}           (NEW — 30 entries)      │
│      └── README.md                      (NEW — expansion path)  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼  Tech Writer step (new in PHASE_STEP_COMMANDS)
┌──────────────────────────────────────────────────────────────────┐
│  TECH WRITER STEP                                                │
│  emit /gsd-docs-update --target=README.md                        │
│  emit /humanizer @README.md (or whatever the actual contract is) │
│  parse humanizer output → humanizer_score                        │
│  state_writer.py write --field humanizer_score --value <score>   │
│  if score >= 1 critical issue:                                   │
│    retry once: emit /humanizer --rewrite @README.md              │
│    re-parse score                                                │
│    if still >= 1 critical: emit failure narration; halt phase    │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
                          Phase 6 (ship)
```

### Recommended Project Structure (new files this phase adds)

```
~/.claude/skills/osbuilder/
├── scripts/
│   ├── narration.py             ← NEW: role banners + subprocess capture (~200 lines)
│   ├── friendly_error.py        ← NEW: error translation module (~150 lines)
│   ├── tests/
│   │   ├── test_narration.py    ← NEW: ~15 stubs (UX-04, ROLE-09, banner emission, capture)
│   │   ├── test_friendly_error.py ← NEW: ~10 stubs (UX-02, UX-05, dictionary load, translate)
│   │   ├── test_tutor_mode.py   ← NEW: ~8 stubs (UX-01, jargon scan, --quiet plumbing)
│   │   ├── test_mode_gating.py  ← NEW: ~6 stubs (UX-03, beginner default, advanced opt-in)
│   │   └── test_tech_writer.py  ← NEW: ~5 stubs (ROLE-07, humanizer integration, fallback)
│   └── (existing scripts: state_writer.py, gsd_driver.py, etc. — extended, not replaced)
├── references/
│   ├── roles/
│   │   ├── qa.md                ← EXISTING
│   │   ├── pm.md                ← NEW (50-200 lines)
│   │   ├── architect.md         ← NEW (50-200 lines)
│   │   ├── frontend.md          ← NEW (50-200 lines)
│   │   ├── backend.md           ← NEW (50-200 lines)
│   │   ├── devops.md            ← NEW (50-200 lines)
│   │   ├── reviewer.md          ← NEW (50-200 lines)
│   │   └── tech-writer.md       ← NEW (50-200 lines)
│   └── friendly-errors/
│       ├── dictionary.yaml      ← NEW (~250 lines, 30 entries × 8 fields)
│       │ (or dictionary.md fallback if YAML loading is rejected)
│       └── README.md            ← NEW (~80 lines, expansion contract + format-version)
└── .planning/osbuilder/
    └── build.log                ← NEW (per-build runtime artifact, NOT committed)
```

### Pattern 1: Subprocess Output Capture — Thread-per-Stream (Cross-Platform)

**What:** narration.py wraps every existing `subprocess.run(...)` call site so user-facing output is a friendly summary while raw text flows to the debug log. Uses `subprocess.Popen` with `stdout=PIPE, stderr=PIPE, bufsize=1, text=True` (line-buffered). Two background threads drain stdout and stderr line-by-line; the main thread polls thread state and emits user-facing summaries.

**Critical constraint:** `select.select` on POSIX is the natural choice but **fails on Windows pipes**. Phase 2's cross-platform mandate (Homebrew + apt + winget) means narration must work on Windows too. **Thread-per-stream is the recommended pattern** — slightly more code than `select`, but portable. [VERIFIED: Python 3.13 docs explicitly state `select.select` does not work on Windows pipes; thread-per-stream is the canonical stdlib pattern]

```python
# scripts/narration.py — capture_subprocess pattern
# Source: [CITED: Python 3.13 subprocess docs; pattern is canonical]
import subprocess
import threading
from pathlib import Path
from typing import Iterable

def _drain_stream(stream, lines: list[str], log_handle) -> None:
    """Drain a stream line-by-line; tee to lines list and log file."""
    for line in iter(stream.readline, ""):
        lines.append(line.rstrip("\n"))
        log_handle.write(line)
        log_handle.flush()
    stream.close()


def capture_subprocess(
    cmd: list[str],
    role: str,
    action: str,
    *,
    log_path: Path,
    cwd: Path | None = None,
    timeout: float | None = None,
) -> tuple[int, list[str], list[str]]:
    """Run cmd; emit role banner; capture stdout+stderr line-buffered.

    Returns: (returncode, stdout_lines, stderr_lines)
    Raw output is also appended to log_path (for debug-log routing).
    """
    emit(role, action, "start", detail=" ".join(cmd[:2]))  # "start" banner

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n# {_now_iso()} {role} {action}: {' '.join(cmd)}\n")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
            shell=False,
            cwd=str(cwd) if cwd else None,
        )
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        t_out = threading.Thread(target=_drain_stream, args=(proc.stdout, stdout_lines, log))
        t_err = threading.Thread(target=_drain_stream, args=(proc.stderr, stderr_lines, log))
        t_out.start(); t_err.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        t_out.join(); t_err.join()

    if proc.returncode == 0:
        emit(role, action, "ok", detail=None)
    else:
        # Translation happens at the call site, not here, because friendly_error
        # needs the structured raw error string + ctx
        raw_error = "\n".join(stderr_lines[-20:])  # last 20 stderr lines = signal
        # caller invokes friendly_error.translate(raw_error, ctx) and re-emits
        emit(role, action, "fail", detail="(see debug log)")
    return proc.returncode, stdout_lines, stderr_lines
```

**Why threads over `select`:** Phase 2's preflight matrix supports Windows (winget primary). Windows `select.select` only handles sockets, not pipes. Thread-per-stream is ~10 extra lines and works everywhere. [VERIFIED: Python 3.13 `select` docs.]

**Why `bufsize=1` + `text=True`:** Line-buffering ensures the drain thread sees output as it's produced (not as a single 64KB block at EOF). `text=True` decodes bytes → str at the boundary.

**Why deque-style "last 20 stderr lines":** Stack traces are often dozens of frames; the signal (e.g., `EACCES`, `ENOENT`, `pnpm install failed: ECONNRESET`) is in the last few lines. Truncating to 20 keeps the friendly-error context manageable for translation.

### Pattern 2: Role Banner + Tutor Line Emission

**What:** `narration.emit(role, action, status, detail)` is the single output gate. Reads `mode` and tutor-enabled state from state.md (cached at module import) and renders one of three layouts.

```python
# scripts/narration.py — emit pattern
# Source: [VERIFIED: pattern derived from existing state_writer.py module structure]
from typing import Literal

Status = Literal["start", "ok", "fail"]

# Module-init: load role briefs once
_ROLE_BRIEFS: dict[str, dict] = {}  # role → {banner, tutor, copy_per_step, failure_copy}

def _load_briefs() -> None:
    """Load 8 role briefs from references/roles/*.md at module import."""
    for role_file in (REPO_ROOT / "references" / "roles").glob("*.md"):
        role = role_file.stem  # "pm", "architect", ...
        _ROLE_BRIEFS[role] = _parse_brief_markdown(role_file.read_text())


# Module-init: snapshot mode + quiet from state.md
_TUTOR_ENABLED: bool = True  # default
_MODE: str = "beginner"      # default

def _refresh_state(project_root: Path) -> None:
    """Refresh _TUTOR_ENABLED and _MODE from state.md.

    Called by the entry point at session start; cached for the session.
    """
    global _TUTOR_ENABLED, _MODE
    state = _read_state(project_root)
    _MODE = state.get("mode", "beginner")
    quiet = state.get("tutor_enabled", "true").lower()
    _TUTOR_ENABLED = quiet in ("true", "1", "yes")


def emit(role: str, action: str, status: Status, detail: str | None = None) -> None:
    """Render one role-banner line; if status="ok" and tutor enabled, also tutor line."""
    brief = _ROLE_BRIEFS.get(role)
    if brief is None:
        # graceful degrade: print plain banner without brief lookup
        symbol = {"start": "...", "ok": "✓", "fail": "✗"}[status]
        suffix = f" — {detail}" if detail else ""
        print(f"[{role.upper()}] {action}{symbol}{suffix}")
        return

    # Banner: "[PM] Gathering requirements... ✓"
    template = brief["banner_template"][status]
    print(template.format(action=action, detail=detail or ""))

    # Tutor line: "> In plain English: I asked you about your app and wrote down what you said."
    if status == "ok" and _TUTOR_ENABLED and _MODE == "beginner":
        tutor_template = brief.get("tutor_per_step", {}).get(action, brief["tutor_template"])
        line = "> " + tutor_template.format(action=action, detail=detail or "")
        # Forbidden-jargon check at runtime is documented; test-time scan is the gate
        print(line)
```

**Forbidden-jargon scan: test-time, not runtime.** Runtime scan would raise on every emit if a brief was edited badly; test-time scan is the better gate. The test suite captures stdout from a full E2E run and greps for the 6 tokens against the captured stream — see Validation Architecture below.

**`> ` prefix:** SPEC default. Plain ASCII; works in any terminal (no color/Rich dependency, which would add a dep). Grep-able: `grep '^> ' build-output.txt` extracts every tutor line.

### Pattern 3: Per-Role Brief Format

**What:** Each `references/roles/{role}.md` has 4 documented sections that `narration.py` parses. Loaded on import.

```markdown
# OSBuilder PM Role — Narration Brief

## Banner Templates

start: [PM] {action}...
ok: [PM] {action} ✓
fail: [PM] {action} ✗ {detail}

## Tutor Template (default)

> In plain English: {action} — that's the part where I figure out what you want.

## Per-Step Copy

intake-paragraph:
  banner: Reading your description
  tutor: I read what you wrote and pulled out the key things you said you wanted.

intake-structured:
  banner: Reading your spec
  tutor: I read your spec and pulled out the features and stack hints.

spec-lock:
  banner: Locking the spec
  tutor: I made sure the description is clear enough to build from. If anything was fuzzy, I asked you about it.

## Failure Copy

intake-paragraph: PM hit a snag while reading your description. Details below.
intake-structured: PM couldn't read your spec file. Details below.
spec-lock: PM thinks the description still has too many open questions. Details below.
```

**Parser pattern** (`_parse_brief_markdown` in narration.py): walks H2 sections, splits H3-style "key: value" or indented `key:\n  field: value` entries. Stdlib only — `re.split(r"^## ", content, flags=re.MULTILINE)` followed by line-by-line parsing.

**Why this format over YAML frontmatter + body:** The 8-field-per-role-brief surface is small enough that pure-Markdown sections are readable for hand-editing AND parseable with stdlib regex. YAML frontmatter would tempt a `pyyaml` dep.

### Pattern 4: Friendly-Error Module — Pure Translator + First-Match Dictionary

**What:** `friendly_error.translate(raw, ctx)` is a pure function. Loads dictionary at module import; iterates entries in dictionary order; returns the first match, or falls back to a generic translator that strips Python tracebacks and Node stack frames.

```python
# scripts/friendly_error.py — translate pattern
# Source: [VERIFIED: dictionary-first pattern; first-match precedence; pure function]
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

Severity = Literal["info", "warn", "error", "fatal"]

@dataclass
class FriendlyMessage:
    title: str
    what_broke: str
    what_to_do: str
    copy_paste: str | None
    severity: Severity


_DICTIONARY: list[dict] = []  # loaded at module import

def load_dictionary() -> list[dict]:
    """Load and validate the friendly-error dictionary at module import.

    Format-version field check: rejects malformed dictionaries with a clear error.
    """
    global _DICTIONARY
    path = REPO_ROOT / "references" / "friendly-errors" / "dictionary.yaml"
    # If YAML is the locked format, parse with the hand-rolled subset parser
    # (see Locked Decision below). If Markdown table is fallback, parse with
    # split('|') row-by-row.
    raw = path.read_text(encoding="utf-8")
    entries = _parse_yaml_subset(raw)  # or _parse_markdown_table
    if entries[0].get("format_version") != "1.0":
        raise SystemExit(
            "OSBuilder: friendly-errors dictionary format-version mismatch. "
            f"Expected 1.0, got {entries[0].get('format_version')}"
        )
    _DICTIONARY = entries[1:]  # first entry is metadata
    return _DICTIONARY


def translate(raw_error: str | Exception, ctx: dict | None = None) -> FriendlyMessage:
    """Translate a raw error into a FriendlyMessage.

    First-match precedence: iterate dictionary; return first entry whose
    match_pattern matches raw_error (regex if `pattern_type=regex`, else substring).
    Falls back to _generic_translator if no entry matches.
    """
    text = str(raw_error)
    for entry in _DICTIONARY:
        pattern = entry["match_pattern"]
        is_regex = entry.get("pattern_type", "substring") == "regex"
        if is_regex:
            if re.search(pattern, text):
                return _build_message(entry, ctx)
        elif pattern in text:
            return _build_message(entry, ctx)
    return _generic_translator(text, ctx)


def _generic_translator(text: str, ctx: dict | None) -> FriendlyMessage:
    """Fallback when no dictionary entry matches.

    Strip Python tracebacks and Node stack frames; surface the last meaningful line.
    """
    cleaned = _strip_tracebacks(text)
    last_line = (cleaned.strip().splitlines() or ["unknown error"])[-1]
    return FriendlyMessage(
        title="Something went wrong",
        what_broke=last_line[:200],  # truncated
        what_to_do="Check the debug log at .planning/osbuilder/build.log for details.",
        copy_paste=None,
        severity="error",
    )


def _strip_tracebacks(text: str) -> str:
    """Remove Python Traceback blocks and Node stack frames."""
    lines = text.splitlines()
    out = []
    in_tb = False
    for line in lines:
        if line.startswith("Traceback (most recent"):
            in_tb = True
            continue
        if in_tb and (line.startswith(" ") or line.startswith("\t")):
            continue
        if re.match(r"^\s+at .+\(.+:\d+\)$", line):  # Node stack
            continue
        if re.match(r'^\s+File ".*", line \d+,', line):  # Python frame
            continue
        in_tb = False
        out.append(line)
    return "\n".join(out)
```

**First-match precedence:** Dictionary order matters. **More specific patterns must come BEFORE generic ones.** Example: a specific "ENOENT: pnpm" entry must precede a generic "ENOENT" entry. The dictionary is hand-curated with this in mind, and the README documents the rule.

**Why pure function:** Testable in isolation (no state.md read, no subprocess). Caller passes `ctx` if it wants to interpolate (e.g., `{project_path}` in the copy_paste command).

**Why dictionary-first then generic-fallback:** 30 entries is curated for high-frequency failures. The generic fallback prevents an unmatched error from leaking a stack trace; it's a safety net, not a primary path.

### Pattern 5: Mode Gating in Question Bank + Stack Researcher

**What:** Beginner mode (default) auto-resolves stack/deploy/scaffolder choices to documented defaults. Advanced mode exposes them as prompts. The gate is the `mode` field in state.md, written at entry-point flag parse time, read by every prompt site.

**Existing call sites that must check `mode`:**

1. **`scripts/intake_handler.py`** — Currently reads paragraph/structured spec but doesn't gate question-bank questions by mode. Phase 5 must extend it to skip jargon-bearing questions in beginner mode (Q: Devices, Q: Users are jargon-free already; Q: External access maps to "API" jargon; Q: File uploads is neutral; Q: Privacy is neutral).
2. **`scripts/stack_researcher.py`** — Currently invokes `/brainiac` for stack research; falls back to stack-menu.md. Phase 5 must add: in beginner mode, skip the brainiac surface entirely if the playbook is "web" (default → use stack-menu); in advanced mode, prompt the user to confirm/override each stack choice.
3. **`scripts/scaffold_dispatch.py`** — Currently dispatches to `pnpm create next-app` etc. Phase 5 must skip "are you sure?" prompts in beginner mode; expose them in advanced mode.

**Default-mode auto-resolution table:**

| Decision | Beginner default | Source |
|----------|------------------|--------|
| Web stack framework | next.js 16.2.4 | `references/stack-menu.md` row 1 |
| ORM | drizzle-orm 0.45.2 | `references/stack-menu.md` row 2 |
| Database | postgres 18-alpine (multi-user) OR sqlite (single-user) | `references/stack-menu.md` + `Q: Users` answer |
| CSS | tailwindcss 4.2.4 | `references/stack-menu.md` |
| Package manager | pnpm 10.33.2 | `references/stack-menu.md` |
| Deploy target | none (local + private GitHub only) | SPEC.md "Out of Scope: deploy targets are Phase 6" |
| Scaffolder | `pnpm create next-app@latest` for web playbook | `references/playbooks/web.md` |

**The acceptance test** for UX-03 grep'd against the prompt stream uses these forbidden tokens in default mode: `Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind`. The auto-resolution table picks Next.js + Drizzle + Postgres + Tailwind without ever naming them in a prompt.

### Pattern 6: Tech Writer Step + Humanizer Integration

**What:** A new step value in `gsd_driver.py`'s PHASE_STEP_COMMANDS dict. Slot it between the current step 8 (`/gsd-verify-work`) and the existing in-line step 9 (phase advance). Recommendation: rename step 8 → 9, add tech-writer at step 8 (or insert at 8.5 by remapping).

**Sequence:**

1. Driver's emit-next reaches new step → emit `/gsd-docs-update --target=README.md`.
2. On re-entry (after `/gsd-docs-update` completes), emit `/humanizer @README.md` — see Open Question 1 for actual contract.
3. On re-entry (after `/humanizer` completes), parse humanizer output → derive `humanizer_score` (number of critical issues found).
4. Write `humanizer_score` to state.md via `state_writer.py`.
5. If `humanizer_score >= 1`:
   - First retry: emit `/humanizer --rewrite @README.md` (or whatever the actual rewrite invocation is — see Open Question 1).
   - Re-parse score on re-entry.
   - If still `>= 1`: emit failure narration via `friendly_error.translate("humanizer flagged README", ctx={...})`; halt phase.
6. If `humanizer_score == 0`: advance to step 9 (phase done).

**Humanizer fallback (locked in SPEC):** If `~/.claude/skills/humanizer/SKILL.md` is missing or its frontmatter `version` doesn't meet a minimum:
- Emit friendly-error: "humanizer skill missing or version-drifted; README ships without an AI-pattern check."
- Write `humanizer_score=skipped` (or `null`) to state.md.
- Continue to step 9 (phase advance).
- Surface in the build summary so the user knows the README is non-humanizer-gated.

**Detection mechanism:** Read `~/.claude/skills/humanizer/SKILL.md`; parse YAML frontmatter for `name: humanizer` and `version: <x.y.z>`. Minimum version pinned in OSBuilder's SKILL.md frontmatter `requires:` block (TBD in Phase 8 per QUAL-05; for Phase 5, accept `>= 2.0.0`). [VERIFIED: humanizer SKILL.md frontmatter shows `version: 2.2.0` 2026-04-30]

### Anti-Patterns to Avoid

- **Calling `subprocess.run` without narration wrapper:** Every existing `subprocess.run` call site in the 5 listed scripts must be migrated to `narration.capture_subprocess`. A grep for `subprocess.run\(` after Phase 5 ships should find zero hits in those scripts (other than internal helpers in narration.py / friendly_error.py themselves).
- **Reading state.md inside `emit()` on every call:** State should be cached at module init (or refreshed once per session), not re-read per emission. ~hundreds of emits per build; ~hundreds of subprocess reads of state.md is wasteful and creates a race window.
- **Adding `pyyaml` to fix YAML parsing:** Banned by project rule. Either hand-roll a YAML subset parser (see Open Question 2) or fall back to Markdown table.
- **Embedding humanizer logic in Python:** SPEC explicitly forbids this. The humanizer is a slash-command skill; OSBuilder invokes it.
- **Tutor lines in `--quiet` mode:** Test must verify zero `> `-prefix lines in `--quiet` output.
- **Forbidden jargon in tutor lines:** Test must grep captured output against the 6-token list.
- **Per-emit jargon scan at runtime:** Slow; raises on every emit if a brief is bad. Use test-time scan of captured output.
- **Single-file 30-entry dictionary without entry IDs:** Without unique `id` per entry, the README's "criteria for inclusion" can't reference specific entries. Every entry must have a stable `id` (e.g., `port-in-use`, `gh-token-expired`).
- **Renaming PHASE_STEP_COMMANDS keys to integers other than the current 0–9:** Existing tests pin those values. Add tech-writer as step 8 and shift the verify-work to a non-conflicting position (or insert as step 8.5 by remapping the dict).
- **Forgetting to extend ALLOWED_FIELDS:** New fields `mode`, `humanizer_score`, `tutor_enabled` (and any others) must be added to `state_writer.py`'s ALLOWED_FIELDS in Wave 0 — same pattern as Phase 4. State writes to unknown fields fail; `gsd_driver.py` would silently drop them.
- **Per-build vs per-phase build.log:** Pick one. Recommendation: append-mode for the lifetime of one build; `state_writer init` truncates it. New build = fresh log. Per-phase rotation is harder to debug across phases.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Subprocess streaming | Custom polling/select loop with corner cases | `subprocess.Popen` with `bufsize=1, text=True` + thread-per-stream drain | Stdlib pattern; works on Windows; no edge cases |
| Stack-trace stripping | LLM-based summarization, ML model | Regex strip on `^\s+at .+\(.+:\d+\)$` (Node) and `^\s+File ".*", line` (Python) | Stack frames have deterministic shapes; regex is faster, predictable, testable |
| Forbidden-jargon scan | Per-emit runtime check | Test-time grep against captured E2E output | Test-time = single check covers all paths; runtime check is a maintenance burden |
| Markdown-table parsing | Custom Markdown parser | `str.split("|")` row-by-row; strip per cell | Markdown tables have a fixed shape; stdlib `str.split` suffices |
| YAML parsing | `pyyaml` dependency | Hand-rolled subset parser (only the keys we use) OR Markdown-table fallback | Project rule: no new deps; hand-rolling is a 50-line subset (see Open Question 2) |
| State persistence | New schema file or in-memory dict | Existing `state_writer.py` ALLOWED_FIELDS extension | Phase 4 pattern; survives `/clear` for free |
| Role-brief loading | Per-emit file read | Module-init load into `_ROLE_BRIEFS` dict | Briefs change rarely; load once per session |
| Humanizer logic | Reimplementing humanizer's pattern detection in Python | Delegate to `/humanizer` slash command | Composition rule; SPEC forbids embedding |
| Build.log rotation | Custom log rotation library | Append for one build; truncate on `state_writer init` | Aligns with state.md lifecycle; one build = one log |

**Key insight:** Phase 5 is wrapping work, not algorithmic work. Every line of custom logic is a maintenance surface. Stdlib + dictionary-as-data + test-time-scans is the operating mode.

---

## State Machine + State.md Field Extensions for Phase 5

`state_writer.py`'s ALLOWED_FIELDS must be extended in Wave 0. Add to ALLOWED_FIELDS (NOT to REQUIRED_FIELDS — same pattern as Phase 3 and Phase 4):

```python
# scripts/state_writer.py — extend ALLOWED_FIELDS for Phase 5
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    # Phase 3 (existing)
    "project_path",
    "stack_choices",
    "stack_overrides",
    # Phase 4 (existing)
    "gsd_phase_count",
    "failure_class",
    "escalation_log",
    # Phase 5 additions:
    "mode",              # "beginner" | "advanced"
    "tutor_enabled",     # "true" | "false" — set to "false" by --quiet
    "humanizer_score",   # int (count of critical issues) | "skipped" | "0"
    "build_log_path",    # absolute path to .planning/osbuilder/build.log for this build
}
```

[VERIFIED: state_writer.py lines 36-44 show the existing pattern; new fields slot in cleanly.]

---

## 30-Entry Friendly-Error Dictionary Seed List

Below is the seed list. Each entry will become a row in `dictionary.yaml` (or table row in `dictionary.md`) with the 8 fields locked in SPEC. Source attribution: P# = PITFALLS.md pitfall number; SUM = SUMMARY.md; PRE/4 = Phase 1-4 SUMMARYs and dogfood failures; STD = standard ecosystem failure mode.

| # | id | match_pattern | category | title | what_to_do (hint) | Source |
|---|----|----|------|-----|-----|---|
| 1 | `port-in-use` | `EADDRINUSE` (regex) | runtime | The port is already taken | Stop the other thing using port 3000 (or pick a different port). | STD |
| 2 | `pnpm-not-found` | `pnpm: command not found` | preflight | pnpm isn't installed yet | Run `npm install -g pnpm` or let OSBuilder install it. | PRE |
| 3 | `npm-not-found` | `npm: command not found` | preflight | npm isn't installed yet (Node missing) | Run preflight: `python3 scripts/preflight_check.py install`. | PRE |
| 4 | `python-not-found` | `python3: command not found` | preflight | Python isn't installed yet | Run the bootstrap shim: `bash scripts/bootstrap.sh`. | P13 |
| 5 | `node-version-old` | `node version .* < 20` (regex) | preflight | Your Node is too old | Run preflight: `python3 scripts/preflight_check.py install` to upgrade. | PRE |
| 6 | `gh-not-found` | `gh: command not found` | gh-auth | The GitHub CLI isn't installed yet | Run preflight: `python3 scripts/preflight_check.py install`. | P15 |
| 7 | `gh-token-expired` | `HTTP 401` AND `gh` (regex pattern_type=regex) | gh-auth | Your GitHub login has expired | Run `gh auth login --git-protocol https` and follow the prompts. | P15 |
| 8 | `gh-token-conflict` | `GITHUB_TOKEN.*set.*interrupted` (regex) | gh-auth | Two GitHub tokens are fighting | Unset the env var: `unset GITHUB_TOKEN`, then run `gh auth login`. | P15 |
| 9 | `docker-daemon-not-running` | `Cannot connect to the Docker daemon` | docker | Docker isn't running yet | Start Docker Desktop (or OrbStack on Mac) and try again. | STD |
| 10 | `docker-not-installed` | `docker: command not found` | docker | Docker isn't installed | Install Docker Desktop or OrbStack, or use `--no-docker` for SQLite-only. | PRE |
| 11 | `enoent-generic` | `ENOENT` | filesystem | The file or folder I need isn't there | Check the path; if it should exist, re-run scaffold or check `state.md`. | P12 |
| 12 | `eacces-generic` | `EACCES` | filesystem | I don't have permission to do that | Try running with the right permissions, or pick a folder you own. | P12 |
| 13 | `git-not-a-repo` | `fatal: not a git repository` | git | This isn't a git folder yet | Run `git init` in the project folder, then try again. | P15 |
| 14 | `git-merge-conflict` | `Merge conflict in` | git | Two changes disagree | Open the conflicting file; pick which version to keep; commit. | STD |
| 15 | `module-not-found-py` | `ModuleNotFoundError` | runtime | A Python piece is missing | Run `pip install -e .` from the project folder. | STD |
| 16 | `module-not-found-js` | `Cannot find module` | runtime | A Node piece is missing | Run `pnpm install` from the project folder. | STD |
| 17 | `npm-404` | `npm ERR! 404` | registry | That package name isn't on npm | The name is likely a typo or hallucinated — OSBuilder blocked it. | P6 |
| 18 | `pypi-404` | `No matching distribution found` | registry | That Python package isn't on PyPI | The name is likely wrong — OSBuilder blocked it. | P6 |
| 19 | `slopsquat-blocked` | `slopsquatting gate blocked` | registry | OSBuilder blocked a suspicious package | A package name OSBuilder couldn't verify was rejected for safety. | P6, PRE |
| 20 | `network-econnreset` | `ECONNRESET` | network | Network connection dropped | Wait a moment and OSBuilder will retry. (Already handled by the retry loop.) | P3, 4 |
| 21 | `network-timeout` | `ETIMEDOUT` | network | Network is slow | Check your connection; OSBuilder will retry. | 4 |
| 22 | `dns-resolve-fail` | `EAI_AGAIN` | network | Couldn't reach the internet | Check your connection. | 4 |
| 23 | `next-build-fail` | `next build failed` | runtime | The Next.js build hit an error | Run `pnpm build` to see the details, or check `build.log`. | STD |
| 24 | `tailwind-bad-class` | `Cannot apply unknown utility class` | scaffold | A Tailwind class name is wrong | Edit the file mentioned and fix the class name; check spelling. | STD |
| 25 | `pg-conn-refused` | `connection refused.*5432` (regex) | docker | Postgres isn't running yet | Run `docker compose up -d postgres` from the project folder. | STD |
| 26 | `pg-auth-fail` | `password authentication failed` | docker | Postgres password mismatch | Check `.env` against `compose.yaml`; usually `cp .env.example .env`. | STD |
| 27 | `path-traversal-rejected` | `cannot contain '..'` | filesystem | OSBuilder blocked a risky path | A path with `..` was rejected for safety; use absolute paths. | PRE |
| 28 | `state-md-missing` | `no state.md at` | filesystem | OSBuilder lost track of where it was | Run `state_writer.py init` or restart the build. | 4 |
| 29 | `humanizer-missing` | `humanizer.*not found.*~/.claude/skills` (regex) | scaffold | The humanizer skill isn't installed | README will ship without the AI-pattern check; install humanizer to enable. | (this phase) |
| 30 | `gsd-skill-missing` | `gsd-.*: command not found` (regex) | scaffold | A GSD skill is missing | Install the missing GSD skill in `~/.claude/skills/`. | P9, 4 |

**Dictionary file size estimate:** ~250 lines for YAML (8 fields × 30 entries × ~1 line each + metadata + comments). ~80 lines for Markdown table fallback (1 row per entry, fewer comments).

**Pattern-type mix:** ~12 regex entries (where multi-token patterns matter) + ~18 substring entries. First-match precedence ordering: most-specific first (e.g., `slopsquat-blocked` before `npm-404`), generic last.

**Coverage rationale:**
- 5 entries from PITFALLS.md (P3, P6, P9, P12, P13, P15) — known dogfood failures.
- 4 entries from Phase 1-4 SUMMARYs — failures hit during real OSBuilder development (`state-md-missing`, `path-traversal-rejected`, `slopsquat-blocked`, `network-econnreset`).
- ~21 entries from STD ecosystem failures (Node, Python, Postgres, Docker, Git, npm, pnpm) — high-frequency real-world failures the project will hit on first dogfood builds.

---

## Per-Role Coverage Map

`gsd_driver.py`'s PHASE_STEP_COMMANDS maps to these roles. Each role owns the user-facing narration for its dispatched commands. The 8 roles are:

| # | Role | Owns Steps | Phase Step → Role Mapping | Brief File |
|---|------|-----------|---------------------------|------------|
| 1 | PM | Initial spec + intake | step 0 (`/gsd-spec-phase`) + intake_handler.py paragraph/structured calls | `references/roles/pm.md` (NEW) |
| 2 | Architect | Plan + stack research | step 1 (`/gsd-plan-phase`) + stack_researcher.py brainiac call | `references/roles/architect.md` (NEW) |
| 3 | Frontend | UI execute | part of step 3 (`/gsd-execute-phase`) — when the phase touches UI files | `references/roles/frontend.md` (NEW) |
| 4 | Backend | API/DB execute | part of step 3 (`/gsd-execute-phase`) — when the phase touches API/DB | `references/roles/backend.md` (NEW) |
| 5 | DevOps | Scaffold + install + registry gate | step 2 (`registry_verify` + install) + scaffold_dispatch.py invocations | `references/roles/devops.md` (NEW) |
| 6 | QA | Test + verify | step 4 (`/code-tester`) + step 8 (`/gsd-verify-work`) | `references/roles/qa.md` (EXISTING) |
| 7 | Reviewer | Review | step 5 (`/predator`) + step 6 (`/gsd-code-review`) | `references/roles/reviewer.md` (NEW) |
| 8 | Tech Writer | Docs + humanizer | new step (between 8 and 9): `/gsd-docs-update` + `/humanizer` | `references/roles/tech-writer.md` (NEW) |

**Frontend vs Backend split during step 3:** `/gsd-execute-phase` is a single skill invocation. The Frontend/Backend split is **narration-only** — `gsd_driver.py` could pick `frontend` or `backend` as the active role based on the phase's spec (e.g., "build the homepage" → Frontend; "build the API" → Backend). Heuristic: read the GSD phase title (post-`/gsd-spec-phase` output); if it contains `UI`, `frontend`, `homepage`, `screen`, `page` → role=frontend; if it contains `API`, `backend`, `database`, `endpoint`, `model` → role=backend; default → role=devops.

**Per-phase-step copy structure** (each role brief):

```yaml
# example: references/roles/pm.md
banner_template:
  start: "[PM] {action}..."
  ok: "[PM] {action} ✓"
  fail: "[PM] {action} ✗ ({detail})"

tutor_template: "In plain English: {action}."

per_step:
  intake-paragraph:
    banner: "Reading your description"
    tutor: "I read what you wrote and pulled out the things you said you wanted."
  intake-structured:
    banner: "Reading your spec"
    tutor: "I read your spec file and listed the features."
  spec-lock:
    banner: "Locking the spec"
    tutor: "I made sure the description is clear enough to build from."

failure_copy:
  intake-paragraph: "PM had trouble reading your description. Details below."
  intake-structured: "PM couldn't read your spec file. Details below."
  spec-lock: "PM thinks the description still has too many open questions."
```

**File-size target per brief:** 50–200 lines per SPEC. Realistic estimate: 80–120 lines. 7 new briefs × ~100 lines each = ~700 lines of new role-brief Markdown.

---

## Common Pitfalls

### Pitfall 1: Subprocess Pipe Deadlock

**What goes wrong:** A long-running subprocess writes >64KB to stderr; the parent doesn't drain it until after `proc.wait()` returns; the subprocess blocks on the full pipe; deadlock.
**Why it happens:** Default OS pipe buffer is ~64KB. If both stdout and stderr fill, both block. Reading one isn't enough.
**How to avoid:** Drain stdout AND stderr concurrently — that's why thread-per-stream is the canonical pattern. Both threads call `iter(stream.readline, "")` until EOF.
**Warning signs:** A subprocess hangs indefinitely when run through narration but works fine standalone.

### Pitfall 2: `select.select` on Windows Pipes

**What goes wrong:** Phase 5 deploys to Windows users (per Phase 2). `select.select` is the POSIX-natural choice for multiplexing pipe reads, but it doesn't work on Windows pipes — it raises or silently fails.
**Why it happens:** Windows IO model differs; pipes are file handles, not selectable objects.
**How to avoid:** Use threads-per-stream (Pattern 1). Slightly more code, but portable. **Locked decision.**
**Warning signs:** Tests pass on macOS/Linux; fail mysteriously on Windows.

### Pitfall 3: Terminal Capability Variation (Color, ✓ vs `[OK]`)

**What goes wrong:** Tutor mode emits `✓` glyph; Windows cmd.exe (legacy) doesn't render Unicode well; output shows `?` or boxes.
**Why it happens:** Unicode support varies across terminals; Windows Terminal handles it, cmd.exe sometimes doesn't.
**How to avoid:** SPEC's acceptance test explicitly checks for `✓` in output. Recommendation: use plain ASCII `[OK]` / `[FAIL]` / `...` as the safe default; allow Unicode glyph as an optional render mode (gated by env var or terminal-capability detection). **Open Question 3.**
**Warning signs:** Windows users see boxes/`?`s instead of `✓`/`✗`.

### Pitfall 4: Humanizer Contract Mismatch

**What goes wrong:** SPEC assumes humanizer exposes `--check` and `--rewrite` flags. The actual humanizer skill at `~/.claude/skills/humanizer/SKILL.md` is an LLM-driven slash command with NO `--check` or `--rewrite` flag in its frontmatter or body. Invoking `/humanizer --check README.md` won't behave as SPEC predicts; it will run the humanizer's normal flow.
**Why it happens:** SPEC was written from forward-references in OSBuilder's SKILL.md; humanizer's actual surface differs.
**How to avoid:** **Open Question 1 below.** Three resolution paths:
  1. **Adapt to actual contract:** Invoke `/humanizer @README.md` (no flags) and parse the rendered output for severity tokens; treat any "critical" mention as failure. This is the closest to existing humanizer behavior.
  2. **Extend humanizer:** Add `--check` and `--rewrite` flags to humanizer's SKILL.md. Cross-skill change; expand Phase 5 scope.
  3. **Use humanizer as-is for `--check` only:** Humanizer's natural output already enumerates issues; the "Final rewrite" section IS a rewrite. Don't issue separate calls. Run humanizer once, get both diagnosis and rewrite in one pass; if rewrite still has critical patterns by re-grep, fail.
  **Recommendation:** Option 3 (use as-is). Run `/humanizer @README.md` once; humanizer outputs a draft → audit → final rewrite. Accept the final-rewrite output. Score = count of "critical" patterns in the audit step. If audit reports zero critical issues against the final, pass. Cleanest fit with existing humanizer contract.
**Warning signs:** Tech-writer-step tests pass with mocks but fail against the real humanizer skill.

### Pitfall 5: State.md Read on Every emit() Call

**What goes wrong:** `narration.emit` is called dozens of times per build. If each call subprocess-runs `state_writer.py read --field mode`, total time is hundreds of subprocess spawns + reads. Slow. Also creates a race window where an emit during a state write reads stale data.
**Why it happens:** "Source of truth = state.md" is the project mantra, applied too literally.
**How to avoid:** Cache state at module init OR refresh once per session via `_refresh_state(project_root)` called from the entry point. Within one Python invocation of OSBuilder, mode/tutor_enabled don't change.
**Warning signs:** Build takes noticeably longer than Phase 4 baseline (which had no narration).

### Pitfall 6: Forbidden Jargon Slipping Through Role Briefs

**What goes wrong:** A new role brief contains the word "framework" in a tutor template; nobody catches it; default-mode acceptance test fails 3 weeks after the brief shipped.
**Why it happens:** The 6 forbidden tokens are easy to use accidentally ("This is the testing framework that..." in a Tech Writer brief).
**How to avoid:** Two layers:
  1. Lint at file-write time (CI / pre-commit): grep every `references/roles/*.md` against the 6 tokens; fail commit if any hit (excluding documented "advanced copy" sections).
  2. Runtime test: capture E2E output, grep for tokens (test_tutor_mode.py).
**Warning signs:** Beta tester reports a tutor line containing "framework"; or the runtime test fails with a specific captured line.

### Pitfall 7: PHASE_STEP_COMMANDS Renumbering Breaks Phase 4 Tests

**What goes wrong:** Adding `tech-writer` step requires changing PHASE_STEP_COMMANDS; if existing keys (0–9) are renumbered, Phase 4's tests break (they pin step values).
**Why it happens:** `PHASE_STEP_COMMANDS = {0: "/gsd-spec-phase", 1: "/gsd-plan-phase", ...}` is a dict. Inserting a new step "between" 8 and 9 means renumbering 9 → 10.
**How to avoid:** Add tech-writer at step 9 (current "advance" step); shift the advance to step 10. OR pick a non-integer-conflicting key like `8.5` (won't work because `phase_step` is stored as string-of-int in state.md). OR introduce step "9" for tech-writer and rename the advance to "10". Recommendation: add the new step at value `9`, shift the existing in-line advance to `10`. Update Phase 4 tests in Wave 0.
**Warning signs:** Phase 4 tests fail after Phase 5 changes land.

### Pitfall 8: Build.log Path Cross-OS Drift

**What goes wrong:** narration.py hardcodes `.planning/osbuilder/build.log` but the path uses Unix `/`; on Windows the actual file ends up at a confusing location, or path-traversal rejection in `state_writer._check_value_safe` blocks writing the path to state.md (because the path contains a `..` segment relative to project root in some cases).
**Why it happens:** Cross-platform path bugs (P14 in PITFALLS).
**How to avoid:** Use `pathlib.Path(project_root) / ".planning" / "osbuilder" / "build.log"` — never string concat. Resolve to absolute before writing to state.md.
**Warning signs:** Windows users report build.log is in C:\ root instead of project folder.

---

## Code Examples

### Example 1: Friendly-Error Translate Pattern

```python
# scripts/friendly_error.py
# Source: [VERIFIED: pattern derived from existing project patterns + SPEC requirement 1]
from dataclasses import dataclass
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
DICTIONARY_PATH = REPO_ROOT / "references" / "friendly-errors" / "dictionary.yaml"


@dataclass
class FriendlyMessage:
    title: str
    what_broke: str
    what_to_do: str
    copy_paste: str | None
    severity: str  # "info" | "warn" | "error" | "fatal"


_DICTIONARY: list[dict] = []


def load_dictionary(path: Path = DICTIONARY_PATH) -> list[dict]:
    """Load + validate dictionary; check format-version field."""
    global _DICTIONARY
    raw = path.read_text(encoding="utf-8")
    parsed = _parse_yaml_subset(raw)  # 50-line hand-rolled parser; see Open Question 2
    if not parsed or parsed[0].get("format_version") != "1.0":
        raise SystemExit(
            "OSBuilder: friendly-errors dictionary format-version mismatch. "
            "Expected 1.0; got " + str(parsed[0].get("format_version") if parsed else None)
        )
    _DICTIONARY = parsed[1:]  # first record is metadata
    if len(_DICTIONARY) < 30:
        raise SystemExit(
            f"OSBuilder: dictionary has {len(_DICTIONARY)} entries; expected >= 30."
        )
    return _DICTIONARY


def translate(raw_error: str | Exception, ctx: dict | None = None) -> FriendlyMessage:
    """Pure translator. First-match precedence over dictionary; generic fallback."""
    text = str(raw_error)
    ctx = ctx or {}
    for entry in _DICTIONARY:
        pattern = entry["match_pattern"]
        is_regex = entry.get("pattern_type", "substring") == "regex"
        if (is_regex and re.search(pattern, text)) or (not is_regex and pattern in text):
            return _build_message(entry, ctx)
    return _generic_translator(text, ctx)


def _build_message(entry: dict, ctx: dict) -> FriendlyMessage:
    """Format dictionary entry with ctx interpolation (e.g., {project_path})."""
    return FriendlyMessage(
        title=entry["title"].format(**ctx),
        what_broke=entry["what_broke"].format(**ctx),
        what_to_do=entry["what_to_do"].format(**ctx),
        copy_paste=(entry.get("copy_paste_command") or "").format(**ctx) or None,
        severity=entry.get("severity", "error"),
    )


def _generic_translator(text: str, ctx: dict) -> FriendlyMessage:
    """Fallback: strip stack traces; surface last meaningful line."""
    cleaned = _strip_tracebacks(text)
    last = (cleaned.strip().splitlines() or ["unknown error"])[-1][:200]
    return FriendlyMessage(
        title="Something went wrong",
        what_broke=last,
        what_to_do="Check the debug log at .planning/osbuilder/build.log.",
        copy_paste=None,
        severity="error",
    )


def _strip_tracebacks(text: str) -> str:
    """Remove Python tracebacks and Node stack frames."""
    lines = text.splitlines()
    out = []
    in_py_tb = False
    for line in lines:
        if line.startswith("Traceback (most recent"):
            in_py_tb = True
            continue
        if in_py_tb:
            if line.startswith(" ") or line.startswith("\t") or "File \"" in line:
                continue
            in_py_tb = False
        if re.match(r"^\s+at .+\(.+:\d+\)$", line):  # Node stack frame
            continue
        out.append(line)
    return "\n".join(out)


# Module-init: load dictionary
try:
    load_dictionary()
except (FileNotFoundError, SystemExit):
    # Allow import even if dictionary is missing/malformed; raise on first translate()
    pass


if __name__ == "__main__":
    import sys
    msg = translate(sys.stdin.read())
    print(f"## {msg.title}\n\n{msg.what_broke}\n\n**What to do:** {msg.what_to_do}")
    if msg.copy_paste:
        print(f"\n```\n{msg.copy_paste}\n```")
```

### Example 2: Subprocess Capture in narration.py (Excerpt)

See Pattern 1 above for the full `capture_subprocess` implementation. Test pattern:

```python
# scripts/tests/test_narration.py
import subprocess
from pathlib import Path
import pytest


@pytest.fixture
def nrt():
    import importlib
    try:
        return importlib.import_module("narration")
    except ImportError:
        pytest.skip("narration module not yet created (Wave 1 target)")


def test_capture_subprocess_writes_log(nrt, tmp_path, capsys):
    """ROLE-09: raw subprocess output goes to build.log; user sees role banner."""
    log_path = tmp_path / "build.log"
    rc, out, err = nrt.capture_subprocess(
        ["echo", "hello world"], role="devops", action="probe",
        log_path=log_path,
    )
    assert rc == 0
    captured = capsys.readouterr()
    # User sees role banner only — never raw "hello world"
    assert "[DEVOPS]" in captured.out or "[devops]" in captured.out.lower()
    assert "hello world" not in captured.out
    # build.log contains raw output
    assert "hello world" in log_path.read_text()


def test_no_raw_stack_in_default_mode(nrt, tmp_path, capsys):
    """ROLE-09 acceptance: zero raw stack frames in default-mode output."""
    log_path = tmp_path / "build.log"
    rc, _, _ = nrt.capture_subprocess(
        ["python3", "-c", "import sys; raise RuntimeError('boom')"],
        role="qa", action="run-tests",
        log_path=log_path,
    )
    assert rc != 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out
    assert 'File "' not in captured.out
    assert "RuntimeError" not in captured.out  # raw error not in user output
```

### Example 3: Mode-Gating Test

```python
# scripts/tests/test_mode_gating.py
import pytest


def test_beginner_mode_no_jargon_in_prompts(intake, tmp_project_root, writer, capsys):
    """UX-03: default-mode build for TODO web app produces zero jargon prompts."""
    writer("init", "--goal", "TODO web app", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    intake.parse_paragraph("I want a TODO web app", project_root=tmp_project_root)
    captured = capsys.readouterr()
    forbidden = ["Next.js", "SvelteKit", "Postgres", "SQLite", "Vercel",
                 "Fly.io", "Railway", "Drizzle", "Tailwind"]
    for token in forbidden:
        assert token not in captured.out, f"Beginner mode leaked '{token}' in prompt"


def test_advanced_mode_exposes_stack(intake, tmp_project_root, writer, capsys):
    """UX-03: --advanced mode exposes >= 3 technology names."""
    writer("init", "--goal", "TODO web app", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "advanced",
           project_root=tmp_project_root)
    intake.parse_paragraph("I want a TODO web app", project_root=tmp_project_root)
    captured = capsys.readouterr()
    technical = ["Next.js", "Postgres", "Drizzle", "Tailwind", "pnpm"]
    hits = sum(1 for t in technical if t in captured.out)
    assert hits >= 3, f"Advanced mode exposed only {hits} technical terms; need >= 3"
```

---

## Runtime State Inventory

Phase 5 does not rename or refactor existing strings. It extends configurations and adds new files. Checklist:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | state.md ALLOWED_FIELDS lacks `mode`, `tutor_enabled`, `humanizer_score`, `build_log_path` | Code edit — extend ALLOWED_FIELDS in `state_writer.py` (Wave 0 task) |
| Stored data | `.planning/osbuilder/build.log` does not exist; new artifact | Code edit — `narration.py` creates on first emit |
| Live service config | None — no external services in Phase 5 | None |
| OS-registered state | None — no OS-level registrations | None |
| Secrets/env vars | None — no new env vars; SPEC explicitly forbids new dependencies, no API keys needed | None |
| Build artifacts | None — no new packages installed into the OSBuilder skill itself | None |

**Nothing found in OS-registered or secrets categories** — verified by reading the SPEC (no service tokens), the existing scripts (no env-var reads beyond what already exists), and the humanizer skill's frontmatter (no env-var requirements).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 stdlib | narration.py, friendly_error.py | YES | 3.12.6 (preflight upgrades to 3.13+) | — |
| `subprocess.Popen`, `threading`, `pathlib`, `re`, `json` | narration.py, friendly_error.py | YES (stdlib) | built-in | — |
| pytest | test suite | YES | 9.0.2 | — |
| `~/.claude/skills/humanizer/SKILL.md` | tech-writer step (ROLE-07) | YES | 2.2.0 | friendly-error + skip humanizer gate; non-humanizer-gated README; warning to state.md (per SPEC fallback) |
| `~/.claude/skills/gsd-docs-update/SKILL.md` | tech-writer step (ROLE-07) | YES | (no version frontmatter) | friendly-error + halt phase if missing |
| Existing `state_writer.py` ALLOWED_FIELDS extension pattern | mode/humanizer_score persistence | YES | (Phase 3 + 4 pattern) | — |
| Existing `gsd_driver.py` PHASE_STEP_COMMANDS dispatch | tech-writer step insertion | YES | (Phase 4 driver) | — |
| Existing `references/roles/qa.md` | template for new 7 briefs | YES | (Phase 4) | — |
| Existing `references/stack-menu.md` | beginner-mode default resolution | YES | (Phase 3) | — |
| Existing `references/question-bank.md` | mode-gated prompts | YES | (Phase 3) | — |

[VERIFIED: `ls ~/.claude/skills/humanizer/` shows SKILL.md exists; `~/.claude/skills/humanizer/SKILL.md` frontmatter shows `version: 2.2.0`. `ls ~/.claude/skills/gsd-docs-update/` shows SKILL.md exists; no version field in frontmatter. 2026-04-30]

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:**
- humanizer skill (if not installed at session time): friendly-error fallback path is locked in SPEC.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python3 -m pytest scripts/tests/ -x --tb=short` |
| Full suite command | `python3 -m pytest scripts/tests/ --tb=short` |
| Current test count | 78 tests collected (after Phase 4 — see STATE.md) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-01 | tutor mode emits `>` prefix lines on status="ok" by default | unit | `pytest scripts/tests/test_tutor_mode.py::test_tutor_line_emitted_default -x` | NO — Wave 0 |
| UX-01 | `--quiet` flag → `tutor_enabled=false` in state.md → zero `>` lines | unit | `pytest scripts/tests/test_tutor_mode.py::test_quiet_suppresses_tutor -x` | NO — Wave 0 |
| UX-01 | `--quiet` keeps role banners visible | unit | `pytest scripts/tests/test_tutor_mode.py::test_quiet_keeps_banners -x` | NO — Wave 0 |
| UX-02 | `friendly_error.translate(raw)` returns FriendlyMessage struct | unit | `pytest scripts/tests/test_friendly_error.py::test_translate_returns_struct -x` | NO — Wave 0 |
| UX-02 | dictionary entry matches → uses entry copy | unit | `pytest scripts/tests/test_friendly_error.py::test_dictionary_match -x` | NO — Wave 0 |
| UX-02 | unknown error → generic fallback (no traceback in output) | unit | `pytest scripts/tests/test_friendly_error.py::test_generic_fallback_strips_traceback -x` | NO — Wave 0 |
| UX-02 | every error path in 5 listed scripts wraps via translate() | integration | `pytest scripts/tests/test_friendly_error.py::test_all_error_paths_wrapped -x` | NO — Wave 0 |
| UX-03 | beginner-mode prompts contain zero jargon tokens | unit | `pytest scripts/tests/test_mode_gating.py::test_beginner_no_jargon -x` | NO — Wave 0 |
| UX-03 | advanced-mode prompts expose >= 3 jargon tokens | unit | `pytest scripts/tests/test_mode_gating.py::test_advanced_exposes_stack -x` | NO — Wave 0 |
| UX-03 | mode field in ALLOWED_FIELDS; persisted across reads | unit | `pytest scripts/tests/test_state_writer.py::test_mode_field_allowed -x` | EXISTS (extend) |
| UX-04 | 8 role brief files exist in references/roles/ | unit | `pytest scripts/tests/test_narration.py::test_eight_role_briefs -x` | NO — Wave 0 |
| UX-04 | each new brief has 4 documented sections | unit | `pytest scripts/tests/test_narration.py::test_brief_has_required_sections -x` | NO — Wave 0 |
| UX-04 | role banners contain no forbidden jargon | unit | `pytest scripts/tests/test_tutor_mode.py::test_no_jargon_in_banners -x` | NO — Wave 0 |
| UX-05 | dictionary file has >= 30 entries | unit | `pytest scripts/tests/test_friendly_error.py::test_dictionary_has_30_entries -x` | NO — Wave 0 |
| UX-05 | each entry has all 8 documented fields | unit | `pytest scripts/tests/test_friendly_error.py::test_dictionary_schema -x` | NO — Wave 0 |
| UX-05 | dictionary README has 5 documented sections | unit | `pytest scripts/tests/test_friendly_error.py::test_dictionary_readme -x` | NO — Wave 0 |
| UX-05 | adding a new entry to dictionary is data-only (no code change) | manual | (acceptance: edit dictionary, re-run suite, no code regression) | manual |
| ROLE-07 | gsd_driver.py PHASE_STEP_COMMANDS includes tech-writer step | unit | `pytest scripts/tests/test_tech_writer.py::test_phase_step_includes_tech_writer -x` | NO — Wave 0 |
| ROLE-07 | tech-writer step emits `/gsd-docs-update --target=README.md` | unit | `pytest scripts/tests/test_tech_writer.py::test_emits_gsd_docs_update -x` | NO — Wave 0 |
| ROLE-07 | tech-writer step emits humanizer invocation after gsd-docs-update | unit | `pytest scripts/tests/test_tech_writer.py::test_emits_humanizer -x` | NO — Wave 0 |
| ROLE-07 | humanizer_score persisted to state.md | unit | `pytest scripts/tests/test_tech_writer.py::test_humanizer_score_persisted -x` | NO — Wave 0 |
| ROLE-07 | humanizer >= 1 critical → retry once with rewrite | unit | `pytest scripts/tests/test_tech_writer.py::test_humanizer_retry_once -x` | NO — Wave 0 |
| ROLE-07 | humanizer missing → friendly-error fallback; non-humanizer README | unit | `pytest scripts/tests/test_tech_writer.py::test_humanizer_missing_fallback -x` | NO — Wave 0 |
| ROLE-09 | narration.emit() called at every PHASE_STEP_COMMANDS dispatch | integration | `pytest scripts/tests/test_narration.py::test_emit_at_every_dispatch -x` | NO — Wave 0 |
| ROLE-09 | E2E build prints role banners for all 8 dev-team roles | integration | `pytest scripts/tests/test_narration.py::test_eight_banners_in_e2e -x` | NO — Wave 0 |
| ROLE-09 | E2E build output: zero `^\s+at .+\(.+:\d+\)$` (Node stack) | integration | `pytest scripts/tests/test_narration.py::test_no_node_stack_frames -x` | NO — Wave 0 |
| ROLE-09 | E2E build output: zero `Traceback \(most recent` | integration | `pytest scripts/tests/test_narration.py::test_no_python_tracebacks -x` | NO — Wave 0 |
| ROLE-09 | raw stderr from subprocess goes to build.log, not stdout | unit | `pytest scripts/tests/test_narration.py::test_raw_stderr_to_log -x` | NO — Wave 0 |

**Manual-only (not automatable in Phase 5):**
- Tutor-mode tone calibration: subjective judgment ("does the tutor copy feel patronizing?"). Tested via Charlie's eye + dogfood beta users.
- README readability for non-developers: humanizer's `--check` is the closest automation; final readability is human UAT.
- E2E TODO web-app build with all 8 role banners: requires live Claude Code session; the integration test mocks the gsd_driver entry but real-world drift between mocks and live behavior is human UAT.

### Sampling Rate

- **Per task commit:** `python3 -m pytest scripts/tests/ -x --tb=short`
- **Per wave merge:** `python3 -m pytest scripts/tests/ --tb=short`
- **Phase gate:** Full suite green (>= 78 + Phase 5 new tests = >= 122) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `scripts/tests/test_narration.py` — covers ROLE-09, UX-04, banner emission, capture, log routing (minimum 15 stubs)
- [ ] `scripts/tests/test_friendly_error.py` — covers UX-02, UX-05, dictionary load, translate, generic fallback (minimum 10 stubs)
- [ ] `scripts/tests/test_tutor_mode.py` — covers UX-01, jargon scan, --quiet plumbing (minimum 8 stubs)
- [ ] `scripts/tests/test_mode_gating.py` — covers UX-03, beginner default, advanced opt-in (minimum 6 stubs)
- [ ] `scripts/tests/test_tech_writer.py` — covers ROLE-07, humanizer integration, fallback (minimum 5 stubs)
- [ ] `scripts/state_writer.py` ALLOWED_FIELDS extension — `mode`, `tutor_enabled`, `humanizer_score`, `build_log_path` (Wave 0, code change required before any Phase 5 module writes state)

**Total new RED stubs Wave 0 must drop:** >= 44 (brings collected total to >= 122 tests).

### Falsifiable Test Assertions per Requirement

| Req | Falsifiable Assertion |
|-----|----------------------|
| UX-01 | After `--quiet` is set, capturing stdout from a full `gsd_driver emit-next` cycle produces zero lines starting with `> `. |
| UX-02 | After inducing each of 30 dictionary errors, captured stdout contains ZERO lines matching `Traceback`, `npm ERR!`, `pnpm ERR_`, `^\s+at .+\(.+:\d+\)$`, `^\s+File "`. |
| UX-03 | A beginner-mode TODO-web-app intake produces stdout containing ZERO of: `Next.js`, `SvelteKit`, `Postgres`, `SQLite`, `Vercel`, `Fly.io`, `Railway`, `Drizzle`, `Tailwind`. |
| UX-04 | `find references/roles -name "*.md" \| wc -l` returns 8. Each new brief contains "## Banner Templates", "## Tutor Template", "## Per-Step Copy", "## Failure Copy" headings. |
| UX-05 | `wc -l references/friendly-errors/dictionary.{yaml\|md}` shows file is non-trivial; counting via parser shows >= 30 entries; each entry has all 8 fields. |
| ROLE-07 | After tech-writer step completes, `state.md` contains a `humanizer_score:` line with a numeric or "skipped" value. |
| ROLE-09 | `gsd_driver` E2E run captures stdout matching `\[(PM\|ARCHITECT\|FRONTEND\|BACKEND\|DEVOPS\|QA\|REVIEWER\|TECH-WRITER)\]` for each of the 8 roles at least once. |

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (Phase 5 does not implement auth — humanizer is a local skill, not network) | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | YES | `friendly_error.translate()` receives raw error strings from subprocess output — must not eval, exec, or interpolate any content into shell commands. State writes via `_check_value_safe` (rejects `\n`, `..`). Dictionary file loaded with strict format-version check; rejects malformed input. |
| V6 Cryptography | No | — |
| V7 Error Handling | YES | This phase's primary surface. Friendly-error layer must NOT leak path details, secrets, or internal stack frames to user-facing output. Raw errors → debug log only (not committed; gitignored). |
| V11 Output Encoding | YES | Tutor lines and role banners use plain text only (no HTML, no shell escapes). Dictionary entries' `copy_paste_command` field is shown as a code block — must not be auto-executed. |
| V14 Configuration | YES | Dictionary `format_version` field gates loading; mismatched version → fail fast with clear error (not silent skip). |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via subprocess output | Tampering | `narration.capture_subprocess` treats output as data only; never passes raw output to an LLM as instruction; raw output goes to log file (read by humans, not Claude) |
| Path traversal in build.log path | Tampering | `state_writer.py._check_value_safe` rejects `..`; `build_log_path` written via state_writer, validated |
| Secret leakage in build.log | Information disclosure | build.log is at `.planning/osbuilder/build.log`; Phase 6 will gitignore the entire `.planning/osbuilder/` directory (already convention); document that build.log may contain raw env / token output and should not be committed |
| Shell injection via friendly-error `copy_paste_command` interpolation | Tampering | ctx values that flow into `copy_paste_command` come from state_writer (which enforces `_check_value_safe`); FriendlyMessage is shown as plain text — never auto-executed |
| Dictionary tampering (format-version downgrade attack) | Tampering | Hard format-version check at load; reject anything other than `1.0` for v1 |
| Humanizer skill version drift / tampering | Tampering | Read humanizer SKILL.md frontmatter at session start; pin minimum version; on mismatch → friendly-error fallback path |
| Resource exhaustion via subprocess that produces gigabytes of output | DoS | build.log appended in real-time (no in-memory buffer); stream is drained line-by-line; if subprocess won't exit, narration's timeout kills it (default 300s per subprocess) |

---

## Project Constraints (from CLAUDE.md)

| Directive | Type | Applies to Phase 5 |
|-----------|------|--------------------|
| Python 3.13 stdlib only (no new deps) | Required | narration.py, friendly_error.py — all stdlib; YAML parser (if chosen) is hand-rolled subset; humanizer is delegated, not embedded |
| Single-threaded execution; dev-team is narration-only | Required | narration.py renders banners as the GSD loop runs sequentially; no parallel execution |
| 3-reflection cap (Aider's empirically-validated limit) | Required | Tech-writer step's humanizer retry is 1 retry max (locked in SPEC); not subject to the 3-reflection rule because humanizer fail is a different class |
| State checkpoint at `<project-root>/.planning/osbuilder/state.md` | Required | mode, tutor_enabled, humanizer_score, build_log_path all persist; survive `/clear` |
| Composition rule: fix sub-skills, never fork | Required | Humanizer is delegated via `/humanizer` slash command, not embedded; if humanizer needs a `--check` flag, fix humanizer (Open Question 1) |
| SKILL.md ≤ 200 lines | Required | Phase 5 adds NO content to SKILL.md (forward references already documented); all new copy lives in `references/roles/` and `references/friendly-errors/` |
| One-level-deep references | Required | `references/friendly-errors/` is one level (allowed — same depth as `references/playbooks/`); `references/roles/` flat |
| Refuse-list: no K8s/microservices/etc. in default builds | Required | Phase 5 doesn't add scaffold defaults; refuse-list is enforced in narration copy (no K8s in tutor lines) |
| No raw subprocess output to user in default mode | Required (locked in SPEC) | narration.capture_subprocess routes raw output to build.log; user sees role banners + friendly summaries only |
| 6 forbidden jargon tokens in tutor lines | Required (locked in SPEC) | Test-time grep against captured output; pre-commit lint on role briefs |
| State.md ALLOWED_FIELDS extension pattern (Phase 4 precedent) | Required | Wave 0 task: extend ALLOWED_FIELDS with `mode`, `tutor_enabled`, `humanizer_score`, `build_log_path` |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `subprocess.run(capture_output=True)` (post-print) | `subprocess.Popen` line-buffered + thread-per-stream drain | n/a (always was Popen) | User sees output as it happens, not in a frozen-then-dump pattern |
| `select.select` for stream multiplexing | thread-per-stream | n/a (Windows compatibility forced this) | Portable across POSIX + Windows |
| Per-emit state.md re-read | Module-init cache + session refresh | n/a | Reduces ~hundreds of subprocess spawns per build to 1 |
| LLM-based error summarization | Dictionary + first-match precedence + generic fallback | n/a | Deterministic, testable, fast; no token cost; no LLM dependency at error time |

**Deprecated/outdated:**
- "More words = more helpful" tutor copy — Phase 5 explicitly avoids this (P19: tutor patronizing). One-line tutor explanations only.
- Multi-agent narration with parallel execution — DeepMind Dec 2025 study shows 41-86.7% failure rates; OSBuilder's narration is single-threaded only (P5).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | YAML subset is parseable in ~50 lines of stdlib (no `pyyaml`) | Track B (dictionary format) | If YAML subset is too restrictive, fall back to Markdown table — both formats are documented |
| A2 | Thread-per-stream subprocess capture works correctly on Windows for line-buffered output | Pattern 1 | If Windows pipes have buffering surprises (e.g., subprocess buffers stderr until exit), narration appears frozen on Windows. Mitigation: integration test on Windows + flush-only-on-emit fallback |
| A3 | The humanizer skill at `~/.claude/skills/humanizer/SKILL.md` will continue to expose its current LLM-driven invocation pattern (no `--check`/`--rewrite` flags) | Track E | If humanizer adds those flags before Phase 5 ships, the simpler "Option 1" resolution to Open Question 1 becomes available; if humanizer changes its output schema, parsing breaks. Mitigation: pin humanizer version in SKILL.md frontmatter `requires:` block (Phase 8 task) |
| A4 | `mode` field in state.md as a string enum is sufficient for v1 (per SPEC Assumption #3) | Track D | If finer-grained gating is needed (per-question-bank section), upgrade to a richer mode object in Phase 8 polish |
| A5 | `> ` prefix is acceptable as the tutor-line marker (SPEC Assumption #4) | Pattern 2 | If the prefix conflicts with shell prompts in copy-paste, change to `[hint] ` — both are equally grep-able |
| A6 | Inserting new step value in PHASE_STEP_COMMANDS at position 9 (shifting existing 9 → 10) is the cleanest dispatch model | Pitfall 7 | Phase 4 tests pin step values; renumbering requires Wave 0 test updates |
| A7 | "Critical AI-pattern issue" maps to humanizer's existing severity taxonomy (per SPEC Assumption #2) | Track E | Humanizer SKILL.md does NOT have an explicit severity taxonomy — it has 24 patterns with no "critical" tag. This is the source of Open Question 1 |
| A8 | Per-role brief size 50–200 lines (locked in SPEC) is enough to cover banner + tutor + per-step copy + failure copy for the typical 3–5 actions per role | Pattern 3 | If a role has many actions (e.g., DevOps owns 6+ steps), 200 lines may be tight; mitigation: allow brief to grow to 300 with planner sign-off |

---

## Open Questions

> SPEC.md ambiguity score is 0.19 — these are the residual gaps that survived the SPEC interview. Each has a recommended resolution; the planner should confirm or override.

### 1. Humanizer Contract Mismatch (HIGH-IMPACT)

- **What we know:** SPEC requires `/humanizer --check README.md` (returns score) and `/humanizer --rewrite README.md` (rewrites). The humanizer skill at `~/.claude/skills/humanizer/SKILL.md` (verified version 2.2.0) is an LLM-driven slash command with no `--check`/`--rewrite` flags. Its natural workflow already produces a "draft → audit → final rewrite" cycle in one invocation.
- **What's unclear:** How to map SPEC's two-call retry pattern onto humanizer's actual one-call pattern.
- **Recommendation (Option 3):** Invoke `/humanizer @README.md` once. The natural humanizer output already produces a "Final rewrite". Score = number of "What makes the below so obviously AI generated?" bullet points humanizer reports against the final. If score >= 1, accept the final-rewrite output as the README and re-run humanizer once on the new version; if still >= 1, flag for human review (per SPEC fallback path) but don't fail the phase outright. **This is the cleanest fit with humanizer's existing contract; doesn't require modifying humanizer; satisfies SPEC's "retry once" requirement at a slight semantic shift.**
- **Alternate:** Extend humanizer to expose `--check` and `--rewrite` flags in a separate cross-skill change. Expands Phase 5 scope; adds a new locked dependency.

### 2. YAML Parser Scope for Dictionary

- **What we know:** Project rule forbids `pyyaml`. SPEC defaults to YAML for the dictionary; Markdown table is the documented fallback.
- **What's unclear:** Is hand-rolling a YAML subset parser worth the 50-line maintenance cost, or is Markdown table just as good?
- **Recommendation:** **Markdown table.** Reasoning: (a) Markdown table is just as readable and editable as YAML; (b) no parser to maintain; (c) `str.split("|")` row-by-row is one line of stdlib; (d) easier to lint with grep; (e) eliminates the YAML-version-edge-case maintenance surface. The "YAML preferred" in SPEC is a soft preference; Markdown fallback is explicitly approved.
- **Alternate:** YAML subset parser. Useful if dictionary entries grow multi-line bodies (e.g., long `what_to_do` with embedded code samples). Markdown table can also support this via inline ``` ``` ```` ``` ``` ` `` ` backtick code blocks per cell.

### 3. Unicode Glyph vs ASCII for Banner Status

- **What we know:** SPEC's acceptance test references `✓` / `✗` glyphs.
- **What's unclear:** Windows cmd.exe (legacy) doesn't reliably render Unicode; `[OK]` / `[FAIL]` ASCII is safer.
- **Recommendation:** Use Unicode `✓` / `✗` as the default; provide an env var `OSBUILDER_ASCII_ONLY=1` that falls back to `[OK]`/`[FAIL]`/`...`. Modern Windows Terminal renders Unicode fine; only legacy cmd.exe is an issue, and the env var is the user's escape hatch.
- **Alternate:** ASCII-always. Loses some visual polish but is bulletproof.

### 4. Field Count: 8 or 9?

- **What we know:** SPEC requirement 2 says "each entry has fields `id`, `match_pattern`, `category`, `title`, `what_broke`, `what_to_do`, `copy_paste_command`, `phase_seen`, `expansion_note`." That's 9 fields. SPEC requirement 2 ALSO says "each with all 8 documented fields" in the acceptance criterion. Discrepancy.
- **What's unclear:** Is the count 8 or 9?
- **Recommendation:** **9 fields** (the enumerated list is authoritative). Update the acceptance check to "8 documented fields" → "9 documented fields" in PLAN.md. Add an optional 10th field `pattern_type` (substring | regex; default substring) — implementation-required, not user-required, so doesn't break the count. The pattern_type field is an implementation detail of the parser, not a user-facing schema field.
- **Alternate:** Drop one of the 9 (likely `expansion_note`) to satisfy the "8 fields" count. Loses an expansion-tracking field that the README's contribution criteria reference.

### 5. PHASE_STEP_COMMANDS Insertion Point for tech-writer

- **What we know:** Existing steps 0–9 are pinned by Phase 4 tests. Tech-writer goes "after QA + Reviewer, before Phase 6 ship handoff."
- **What's unclear:** Insert at step 9 (shift advance to 10), or insert as step 9.5 (string key, not int)?
- **Recommendation:** Insert at step 9; rename existing in-line phase-advance step to step 10. Update Phase 4 tests in Wave 0 to expect step 10 for advance. This is the cleanest integer-keyed pattern; preserves type consistency.
- **Alternate:** Use string keys throughout (e.g., `"spec-phase"`, `"plan-phase"`, `"tech-writer"`). Larger diff to Phase 4 code; not recommended.

### 6. Build.log Rotation Policy

- **What we know:** SPEC says raw output routes to `.planning/osbuilder/build.log`. Doesn't specify rotation.
- **What's unclear:** Append forever? Truncate per build? Per phase?
- **Recommendation:** Truncate per build (i.e., on `state_writer init`, also truncate build.log). One build = one log; resume-after-`/clear` continues appending to the existing log. New build = fresh log. Rotation across builds is unnecessary because each build's log is bounded.
- **Alternate:** Append-with-timestamp markers. Useful for debugging recurring builds but log grows unbounded.

### 7. Forbidden-Jargon Lint Surface

- **What we know:** SPEC forbids 6 tokens in default-mode tutor lines + role banners + friendly-error messages. They may appear in `--advanced` mode and in role briefs' "advanced copy" sections.
- **What's unclear:** "Advanced copy" sections — do role briefs need explicit advanced-copy sections, or is the advanced-mode UI built elsewhere?
- **Recommendation:** Phase 5 v1 doesn't include explicit "advanced copy" sections in role briefs. `--advanced` mode in v1 simply allows technical question text to appear (sourced from `references/question-bank.md` advanced sections, future addition). The role briefs themselves stay jargon-free. If a brief needs technical vocabulary later, add an `## Advanced Copy` section then; the lint rule excludes that section from the jargon scan.
- **Alternate:** Add `## Advanced Copy` placeholder sections to all 7 new briefs in Phase 5 (empty for now). Lower-cost forward compatibility.

---

## Files to Create / Modify with Size Estimates

### New Files (Wave 1+)

| File | Estimated Lines | Owns |
|------|----------------|------|
| `scripts/narration.py` | 200–250 | role-banner emission, subprocess capture, brief loading, log writes |
| `scripts/friendly_error.py` | 150–180 | translate(), dictionary load, generic fallback, traceback stripping |
| `scripts/tests/test_narration.py` | 200 (15 stubs + helpers) | UX-04, ROLE-09 tests |
| `scripts/tests/test_friendly_error.py` | 180 (10 stubs + helpers) | UX-02, UX-05 tests |
| `scripts/tests/test_tutor_mode.py` | 120 (8 stubs) | UX-01 tests |
| `scripts/tests/test_mode_gating.py` | 100 (6 stubs) | UX-03 tests |
| `scripts/tests/test_tech_writer.py` | 100 (5 stubs) | ROLE-07 tests |
| `references/roles/pm.md` | 80–120 | PM banner + tutor + per-step + failure copy |
| `references/roles/architect.md` | 80–120 | Architect copy |
| `references/roles/frontend.md` | 80–120 | Frontend copy |
| `references/roles/backend.md` | 80–120 | Backend copy |
| `references/roles/devops.md` | 80–120 | DevOps copy |
| `references/roles/reviewer.md` | 80–120 | Reviewer copy |
| `references/roles/tech-writer.md` | 80–120 | Tech Writer copy |
| `references/friendly-errors/dictionary.md` (preferred per Open Question 2) | ~80 (30 rows + headers) | 30 entry table |
| `references/friendly-errors/README.md` | ~80 | format-version + schema + contribution criteria + 5 documented sections |

**Subtotal new code:** ~600 lines Python; ~200 lines tests-helpers; ~700 lines role briefs; ~160 lines friendly-error data + docs; ~700 lines test stub bodies. **Phase 5 total: ~2,400 lines new content.**

### Modified Files (Wave 0)

| File | Modification | Estimated Diff |
|------|--------------|---------------|
| `scripts/state_writer.py` | Extend ALLOWED_FIELDS with 4 new fields (`mode`, `tutor_enabled`, `humanizer_score`, `build_log_path`) | +5 lines |
| `scripts/gsd_driver.py` | (Wave 1) Add `narration.emit()` calls at every PHASE_STEP_COMMANDS dispatch boundary; add tech-writer step; renumber phase-advance to 10 | +30–50 lines |
| `scripts/preflight_check.py` | (Wave 1) Wrap subprocess.run calls with `narration.capture_subprocess()`; route errors through `friendly_error.translate()` | +20–30 lines (mostly mechanical) |
| `scripts/scaffold_dispatch.py` | (Wave 1) Same subprocess wrapping + friendly-error routing | +20–30 lines |
| `scripts/stack_researcher.py` | (Wave 1) Same subprocess wrapping + friendly-error routing + mode-gating in research surface | +30–40 lines |
| `scripts/intake_handler.py` | (Wave 1) Same subprocess wrapping + friendly-error routing + mode-gating in question-bank surface | +30–40 lines |

**Subtotal modifications:** ~150–200 lines diff across 6 existing files.

### Wave 0 Order (must complete before Wave 1)

1. Extend `state_writer.py` ALLOWED_FIELDS (single commit — atomic).
2. Drop ~44 RED test stubs across 5 new test files.
3. Confirm baseline: `python3 -m pytest --collect-only` shows >= 122 tests.

### Wave 1 Order (parallelizable plans)

| Plan ID | Owns | Files Touched | Disjoint From |
|---------|------|---------------|---------------|
| 05-01 | Wave 0 (state extension + RED stubs) | state_writer.py, all 5 new test files | — (must run first) |
| 05-02 | narration.py + role briefs (7 new) + ROLE-09 wiring in gsd_driver.py | narration.py, references/roles/{pm,architect,frontend,backend,devops,reviewer,tech-writer}.md, gsd_driver.py emit-call insertions | 05-03 (different files), 05-04 |
| 05-03 | friendly_error.py + dictionary + README + UX-02 wiring in 5 listed scripts | friendly_error.py, dictionary.md, friendly-errors/README.md, error-path edits in preflight/scaffold/stack/intake/gsd_driver | 05-02 (modifies same scripts but different lines) |
| 05-04 | Mode-gating: --quiet + --advanced flag plumbing + intake/stack-researcher mode reads | intake_handler.py mode read, stack_researcher.py mode read, OSBuilder entry-point flag parse (SKILL.md or new entry script) | 05-02, 05-03 |
| 05-05 | Tech Writer + humanizer integration | gsd_driver.py PHASE_STEP_COMMANDS extension, tech-writer step handler, humanizer detection | 05-02 (same gsd_driver.py file but different sections) |

**Plans 05-02 and 05-03 both modify the 5 listed scripts.** Recommendation: a coordination subtask in plan 05-02 lands the narration call sites first (creates the wrap surface), then plan 05-03 inserts the friendly_error.translate() calls inside those wraps. Sequential within a single plan or two sequential commits in the same plan.

**Plans 05-02 and 05-05 both modify gsd_driver.py.** They touch different sections (emit calls vs PHASE_STEP_COMMANDS dict) but both are in the same file. Sequence them: 05-02 first, then 05-05.

---

## Sources

### Primary (HIGH confidence)

- `.planning/phases/05-common-person-ux-polish/05-SPEC.md` — locked design contract (8 reqs, 16 acceptance, 4 assumptions) [VERIFIED: direct file read 2026-04-30]
- `.planning/REQUIREMENTS.md` — UX-01..05, ROLE-07, ROLE-09 requirement text [VERIFIED: direct file read]
- `.planning/ROADMAP.md` — Phase 5 entry + dependencies + success criteria [VERIFIED: direct file read]
- `.planning/STATE.md` — Phase 4 complete; baseline test count = 78 [VERIFIED: direct file read]
- `.planning/phases/04-gsd-handoff-verify-loop-failure-classifier/04-RESEARCH.md` — pattern reference (state machine, registry, failure classifier) [VERIFIED: direct file read]
- `.planning/phases/04-gsd-handoff-verify-loop-failure-classifier/04-VALIDATION.md` — Nyquist validation template [VERIFIED: direct file read]
- `.planning/research/PITFALLS.md` — 20 pitfalls; P12 (jargon leaks), P19 (tutor patronizing), P15 (gh auth) feed the dictionary seed [VERIFIED: direct file read]
- `.planning/research/SUMMARY.md` — recommended stack, architecture, "common person UX" risk profile [VERIFIED: direct file read]
- `SKILL.md` — forward references for tutor mode, --quiet, --advanced, friendly errors [VERIFIED: direct file read]
- `scripts/gsd_driver.py` — PHASE_STEP_COMMANDS dict, _read_state, _bump_field, escalation logic [VERIFIED: direct file read]
- `scripts/state_writer.py` — ALLOWED_FIELDS extension pattern; _check_value_safe; atomic_write [VERIFIED: direct file read]
- `scripts/intake_handler.py` — existing intake surface; needs mode-gating extension [VERIFIED: direct file read first 100 lines]
- `scripts/preflight_check.py` — existing subprocess.run patterns to wrap [VERIFIED: direct file read first 80 lines]
- `references/roles/qa.md` — template for new 7 briefs (4-section structure, 91 lines) [VERIFIED: direct file read]
- `references/question-bank.md` — existing 6-question intake surface; mode-gate target [VERIFIED: direct file read]
- `references/stack-menu.md` — beginner-mode default-resolution source [VERIFIED: direct file read]
- `~/.claude/skills/humanizer/SKILL.md` — actual contract: LLM-driven slash command, version 2.2.0, no --check/--rewrite flags [VERIFIED: direct file read 2026-04-30 — this is the source of Open Question 1]
- `~/.claude/skills/gsd-docs-update/SKILL.md` — slash command for docs generation; --force / --verify-only flags exist [VERIFIED: direct file read]
- Python 3.13 stdlib documentation: `subprocess.Popen` (bufsize, text mode), `select.select` (POSIX-only on pipes), `threading.Thread` patterns [CITED: docs.python.org]

### Secondary (MEDIUM confidence)

- Subprocess line-buffered streaming patterns — canonical thread-per-stream pattern documented across multiple Python guides; pattern is stable [CITED: Python docs]
- Markdown table format for editable data files — common open-source convention; no specific source [ASSUMED]
- Friendly-error dictionary first-match precedence — derived from logging-rule and IDS-rule conventions [ASSUMED]

### Tertiary (LOW confidence)

- Unicode glyph rendering on legacy Windows cmd.exe — historical issue; modern Windows Terminal handles fine; recommendation is defensive [ASSUMED]
- 50-line YAML-subset parser feasibility — derived from observation that the 8 fields are simple strings; no nested structures [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- Standard stack (Python stdlib + existing test infrastructure): HIGH — all primitives verified
- Architecture patterns (narration, friendly-error, mode gating): HIGH — patterns derived from existing project conventions
- Dictionary seed list (30 entries): HIGH — sourced from PITFALLS.md (verified) + Phase 1-4 SUMMARYs (verified) + STD ecosystem failures (well-known)
- Per-role brief structure: HIGH — qa.md provides verified template
- Subprocess capture pattern: MEDIUM — pattern is canonical but Windows behavior needs integration test
- Tech Writer + humanizer integration: MEDIUM — humanizer's actual contract differs from SPEC; Open Question 1 requires planner resolution
- PHASE_STEP_COMMANDS extension: HIGH — gsd_driver.py code read verifies dict structure; insertion point clear
- Validation Architecture: HIGH — falsifiable assertions per requirement; test stub counts derived from acceptance criteria
- Common-person UX tone: MEDIUM — testable via grep but final judgment is subjective (UAT)

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (humanizer skill version may shift; otherwise stable for 30+ days; Python stdlib + GSD skill interfaces are stable for 6+ months)

---

## RESEARCH COMPLETE
