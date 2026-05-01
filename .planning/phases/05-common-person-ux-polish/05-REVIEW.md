---
phase: 05-common-person-ux-polish
reviewed: 2026-04-30T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - references/friendly-errors/dictionary.yaml
  - scripts/friendly_error.py
  - scripts/gsd_driver.py
  - scripts/intake_handler.py
  - scripts/narration.py
  - scripts/preflight_check.py
  - scripts/scaffold_dispatch.py
  - scripts/stack_researcher.py
  - scripts/state_writer.py
  - scripts/tests/test_friendly_error.py
  - scripts/tests/test_mode_gating.py
  - scripts/tests/test_narration.py
  - scripts/tests/test_stack_researcher.py
  - scripts/tests/test_tech_writer.py
  - scripts/tests/test_tutor_mode.py
findings:
  critical: 0
  warning: 5
  info: 8
  total: 13
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-04-30T00:00:00Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Phase 5 lands four major capabilities — friendly-error translation, narration banners, mode gating (beginner/advanced), and the tech-writer sub-state machine. The implementation is broadly defensive: `shell=False` everywhere, allowlisted state fields, atomic writes, and graceful-degrade import guards. No critical security issues were found.

Five warnings worth flagging:

1. **Subprocess capture log-handle lifecycle** — the `_drain_stream` threads receive a file handle that is closed by the surrounding `with log_path.open(...)` block as soon as `capture_subprocess` exits its `with` body. If a thread is still running at that moment (e.g., kill/timeout race), it will write to a closed handle and raise `ValueError`. The surrounding bare `except Exception` in `_drain_stream`'s `finally` only protects `stream.close()`, not the loop body.
2. **Tech-writer sub-step state-machine race** — `_run_tech_writer_step` writes `tech_writer_sub_step` and bumps `phase_step` non-atomically across two separate subprocess calls. A `/clear` or crash between the writes leaves state inconsistent (sub_step reset but phase_step not yet bumped, or vice versa). The "defensive reset" branch covers tampering but not interrupted writes.
3. **Hand-rolled YAML parser swallows malformed entries silently** — multiple branches `continue` on malformed input (line 134 `if pending_list_key is None: continue`, line 156 silent overwrite on duplicate keys). Combined with the `try/except` around `load_dictionary()` at module init, a malformed dictionary produces an empty `_DICTIONARY` and EVERY error falls through to the generic translator. There is no way for the user to learn the dictionary is broken.
4. **Tutor-line tokens may leak technology jargon** — `FORBIDDEN_JARGON` in `narration.py` (6 entries: framework, endpoint, responsive, ORM, dependency injection, transpiler) is a subset of `_FORBIDDEN_JARGON` in `test_mode_gating.py` (9 entries: Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind). Worse, the constant is **defined but not used** anywhere in `narration.py`. There is no runtime check that role-brief tutor templates conform; the test suite is the only gate.
5. **Brainiac subprocess call hardcodes `python3`** — `stack_researcher._call_brainiac` invokes `["python3", "-m", "brainiac", ...]` rather than `[sys.executable, "-m", "brainiac", ...]`. On Windows where `python3` is not on PATH (only `python`), this fails before the existing `OSError` catch — not a security bug but a Phase 2 cross-platform regression.

Eight info items cover style/maintenance issues (severity field defaulted but never set, `_safe_format` duplicated across two modules, unused `_validate_project_name` in intake_handler, etc.).

## Warnings

### WR-01: Race on file-handle close in capture_subprocess

**File:** `scripts/narration.py:307-333`
**Issue:** `_drain_stream` threads write to the log handle inside `for line in iter(stream.readline, ""):`. The handle is closed automatically by the `with log_path.open("a", ...) as log:` context manager once `capture_subprocess` exits the `with` block. Because `t_out.join()` and `t_err.join()` are called *inside* the `with` block, normal flow is safe — but if `proc.kill()` is followed by a slow stream drain, or if `subprocess.TimeoutExpired` fires and the threads have not yet exited their read loop after `proc.wait()` returns, the threads can still race against the `with` block exit. There is no `try/except` around `log_handle.write(line)` inside `_drain_stream`, only around `stream.close()` in `finally`.

The current code path appears safe in practice (the join is inside the with-block, and `proc.kill()` should close the pipes which exits `iter(stream.readline, "")`), but the invariant is non-obvious and one refactor away from breaking.

**Fix:** Either move the `t_out.join()`/`t_err.join()` outside the `with log_path.open(...)` block (so threads finish before the file is closed), or wrap the write in a try/except in `_drain_stream`:
```python
def _drain_stream(stream, lines: list[str], log_handle) -> None:
    try:
        for line in iter(stream.readline, ""):
            lines.append(line.rstrip("\n"))
            try:
                log_handle.write(line)
                log_handle.flush()
            except (ValueError, OSError):
                # log handle closed or broken — keep draining stream
                pass
    finally:
        try:
            stream.close()
        except Exception:
            pass
```

### WR-02: Non-atomic two-write update in tech-writer sub-state machine

**File:** `scripts/gsd_driver.py:354-380`
**Issue:** `_run_tech_writer_step` performs two or three separate `state_writer write/bump` subprocess calls per sub-step:

- Sub-step A (line 354): `_write_field("tech_writer_sub_step", "awaiting-humanizer")` only.
- Sub-step B humanizer-absent (lines 366-368): three writes — `humanizer_score=skipped`, `tech_writer_sub_step=""`, `bump phase_step`.
- Sub-step B humanizer-present (lines 377-379): three writes — `humanizer_score=0`, `tech_writer_sub_step=""`, `bump phase_step`.

Each `_write_field` is its own subprocess call that reads, mutates, and atomically rewrites `state.md`. If the build is interrupted (Ctrl-C, `/clear`, OOM kill) between writes, state.md will be in a partial state. Most concerning: if interruption happens between `tech_writer_sub_step=""` and `bump phase_step`, the next `emit_next_command` will see `phase_step==9` AND `sub_step==""`, which re-emits `/gsd-docs-update` — duplicate work, possibly duplicate humanizer invocation. The "Unknown sub_step" branch (lines 384-389) does NOT cover this case (sub_step IS empty).

**Fix:** Either extend `state_writer` to support batched multi-field writes (`write --field a=1 --field b=2`), or order the writes so that interruption is recoverable: set `humanizer_score` first (idempotent re-set is fine), then bump `phase_step` to 10 (which moves the FSM forward), and only then reset `sub_step`. The "stuck at step 9 with sub_step empty" branch already re-emits `/gsd-docs-update` cleanly; the failure mode to avoid is the inverse (sub_step set but phase_step not advanced after success).

### WR-03: Malformed dictionary silently degrades to generic-only translation

**File:** `scripts/friendly_error.py:81-162, 314-317`
**Issue:** `_parse_yaml_subset` silently `continue`s on multiple malformed-input shapes:
- Line 134: nested list item with no `key:` line preceding → silently dropped.
- Line 156: an entry with a duplicate key silently overwrites the prior value.
- Line 142: a `key: value` line outside any record → silently dropped.

The module-init guard (lines 314-317) catches `FileNotFoundError` AND `SystemExit` and silently swallows both. Combined: if the dictionary is corrupt, `_DICTIONARY` stays `[]`, every error skips the dictionary loop (line 287's `for entry in _DICTIONARY: ...` over empty list), and falls through to `_generic_translator`. The user sees "Something went wrong" for ENOENT, EADDRINUSE, etc. — all the carefully-curated copy is silently bypassed.

There is no warning printed, no health check, no test that would catch a half-deployed dictionary.

**Fix:** At minimum, at module load when `SystemExit` is caught from `load_dictionary()`, write a warning to `sys.stderr` once:
```python
try:
    load_dictionary()
except FileNotFoundError:
    pass  # dictionary not yet shipped — fine pre-Phase 5
except SystemExit as e:
    sys.stderr.write(
        f"OSBuilder warning: friendly-errors dictionary failed to load "
        f"({e}). Falling back to generic error translation.\n"
    )
```
Better: add a `validate` subcommand that runs the parser strictly (raise on duplicate keys, raise on stray lines) for CI and a pre-commit hook.

### WR-04: FORBIDDEN_JARGON list is defined but never enforced; tutor-line content is unchecked

**File:** `scripts/narration.py:38-41`
**Issue:** `FORBIDDEN_JARGON = frozenset([...])` is declared at module level (lines 38-41) but never referenced anywhere else in `narration.py`. It is also a strict subset of the test fixture `_FORBIDDEN_JARGON` in `test_mode_gating.py` (which adds Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind).

This means:
1. The jargon constant is dead code (Info-level, see IN-01) AND
2. There is no runtime gate preventing a future role-brief edit from adding "Next.js" to a tutor template — the only gate is a test that emits all 8 banners and grep-checks the output.

The brief parser (`_parse_brief_markdown`) loads tutor templates from `references/roles/*.md` files. If anyone edits a role brief and adds "Next.js framework" to the tutor template, the test catches it on `pytest`, but a slipped commit reaches the user.

**Fix:** Either (a) remove the unused constant (and rely on tests), or (b) actually wire it up: in `emit()`, after rendering the tutor line, check `_MODE == "beginner"` and skip the print if any forbidden token is present (with a warning to stderr in dev mode). Recommend (b) as defense-in-depth.

### WR-05: stack_researcher hardcodes "python3" for brainiac subprocess (Windows regression)

**File:** `scripts/stack_researcher.py:101-117`
**Issue:** `_call_brainiac` uses `["python3", "-m", "brainiac", query]`. Every other subprocess call in this codebase uses `[sys.executable, ...]` (verify with `grep -n 'sys.executable' scripts/*.py`). On Windows, `python3` may not be on PATH — only `python` is. `preflight_check.py:236` already accounts for this for the detection probe, but `stack_researcher` does not.

Result: in advanced mode on Windows, brainiac always fails with `FileNotFoundError`, which is silently caught (line 116) and falls through to stack-menu defaults. The user gets the fallback experience with no indication that brainiac was attempted-and-failed for a fixable reason.

**Fix:**
```python
result = subprocess.run(
    [sys.executable, "-m", "brainiac", "scan", query],
    shell=False, capture_output=True, text=True,
    timeout=30, check=False,
)
```

## Info

### IN-01: Unused module-level constant FORBIDDEN_JARGON

**File:** `scripts/narration.py:38-41`
**Issue:** The constant is declared but never referenced inside the module. See WR-04 for the security-relevant context.
**Fix:** Either wire into `emit()` (preferred) or delete.

### IN-02: severity field defaulted but never set in dictionary

**File:** `scripts/friendly_error.py:223-226` and `references/friendly-errors/dictionary.yaml:8-17`
**Issue:** `_build_message` reads `entry.get("severity", "error")` and validates against the `Severity` literal, but the dictionary's `schema_fields` declaration (lines 8-17 of dictionary.yaml) does NOT include `severity`. None of the 30 entries set severity. So every translated message gets `severity="error"`, even items that should be `info` (e.g., `humanizer-missing` is documented as a non-fatal degrade) or `warn` (e.g., `network-econnreset` is a transient retry).
**Fix:** Either add `severity` to the schema and set it per entry, or remove the field from `_build_message` and document that severity is always "error" in v1.

### IN-03: _safe_format duplicated across two modules

**File:** `scripts/friendly_error.py:194-205`, `scripts/narration.py:191-196`
**Issue:** Two near-identical `_safe_format(template, ctx_or_kwargs)` implementations exist. Both catch the same exception trio. The narration version uses `**ctx` keyword args; the friendly_error version takes a dict. Behavior identical — diverging fix risk.
**Fix:** Extract to a shared `scripts/_safe_format.py` (or re-export from one module) and import.

### IN-04: _validate_project_name in intake_handler is defined but never called

**File:** `scripts/intake_handler.py:54-61`
**Issue:** `_validate_project_name` exists (with V5 + T-3-01 docstring) but no call site in this file references it. `scaffold_dispatch.py` has its own copy that IS used. Dead code in intake_handler.
**Fix:** Delete the unused copy, or add a call site if there's a code path that should validate (none obvious in the current file — `parse_paragraph`/`parse_structured` only read `goal`).

### IN-05: Comments on YAML lines not stripped (parser limitation)

**File:** `scripts/friendly_error.py:81-162`
**Issue:** The hand-rolled parser strips lines that start with `#` but does NOT strip inline comments. A line like `id: example  # inline comment` produces value `"example  # inline comment"`. The current dictionary has no inline comments so this is latent.
**Fix:** Document the limitation explicitly in the parser docstring (lines 44-57), or strip inline `#` comments in `_strip_quotes` for unquoted values. Alternative: switch to PyYAML once a dependency is acceptable.

### IN-06: _build_escalation_output ignores its `state` argument

**File:** `scripts/gsd_driver.py:183-189`
**Issue:** Function takes `state: dict` but never uses it; always returns the same hardcoded string `"/gsd-debug\n/problem-solver"`. Either the parameter is leftover from a refactor or a future enhancement.
**Fix:** Either drop the unused parameter (`def _build_escalation_output() -> str:`) or use it to enrich the escalation prompt (e.g., interpolate `last_failure`).

### IN-07: Magic number `_ESCALATION_THRESHOLD = 3` lacks a sourced rationale

**File:** `scripts/gsd_driver.py:64`
**Issue:** The constant has no comment pointing to its origin. SPEC may justify "three strikes" but the code does not reference it.
**Fix:** One-line comment: `# T-04-02-05: three retries trigger /gsd-debug + /problem-solver escalation`

### IN-08: gsd_driver._humanizer_present() reads SKILL.md fully then iterates

**File:** `scripts/gsd_driver.py:279-297`
**Issue:** The function reads the full file, splits on lines, and tracks `in_front` to identify YAML frontmatter. The text content of SKILL.md may be large; only the first ~10 lines are needed. Minor inefficiency, not a bug.
**Fix:** Add an early break once the closing `---` is encountered:
```python
if line.strip() == "---":
    if in_front:
        break  # closed frontmatter — version not found
    in_front = True
    continue
```

---

## Out of Scope (informational)

- **Performance:** v1 review scope excludes performance issues. The repeated `subprocess.run([sys.executable, str(STATE_WRITER), ...])` pattern (every state field read/write spawns a new Python process) is correctness-correct but wasteful. Out of scope for v1.
- **Test coverage:** Tests are well-scoped and use real subprocess calls (excellent for behavior validation). I did not flag test files for issues since they are test code; reliability looks good (proper fixtures, lazy imports, capsys).
- **Mode-gating defense-in-depth verdict:** I traced the beginner-mode error path. `friendly_error.translate()` returns dictionary entries verbatim; the dictionary copy is hand-curated and contains no jargon. The generic-fallback emits last 200 chars of cleaned error — this CAN leak jargon if the upstream tool prints "Next.js build error" to stderr. Test `test_friendly_message_no_raw_stack_frames` covers stack frames but not jargon tokens. Worth adding a beginner-mode test that pipes a Next.js error string and asserts no `_FORBIDDEN_JARGON` token reaches user output.
- **Path traversal verdict:** All `_resolve_project_root` implementations correctly reject `..`. `state_writer._check_value_safe` rejects `\n`, `\r`, and `..` in values. `_validate_project_name` enforces `[a-zA-Z0-9_-]+`. No subprocess uses `shell=True`. Phase 4 path-traversal mitigations carried forward correctly into Phase 5.
- **Graceful-degrade import guards verdict:** The `try: import friendly_error / except ImportError` pattern in 5 scripts is consistent. The pattern correctly distinguishes "module not yet shipped" (ImportError) from "module shipped but broken" (would raise on import — currently caught by the same handler in friendly_error.py's own SystemExit-suppressing try/except). See WR-03 for the visibility gap this creates.

---

_Reviewed: 2026-04-30T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
