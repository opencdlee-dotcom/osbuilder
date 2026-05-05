---
phase: 04-gsd-handoff-verify-loop-failure-classifier
reviewed: 2026-04-30T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - scripts/gsd_driver.py
  - scripts/failure_classifier.py
  - scripts/registry_verify.py
  - scripts/state_writer.py
  - scripts/tests/test_gsd_driver.py
  - scripts/tests/test_failure_classifier.py
  - scripts/tests/test_registry_verify.py
  - references/roles/qa.md
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-30T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Phase 04 introduces four files: the GSD phase-loop state machine (`gsd_driver.py`), an error
classifier with backoff (`failure_classifier.py`), a package registry gate (`registry_verify.py`),
and a QA role reference doc (`qa.md`). The `state_writer.py` ALLOWED_FIELDS extension is clean.

Security posture is strong: no `shell=True`, no subprocess string interpolation, no `eval`, and
`_check_value_safe` blocks newlines and `..` in all state writes. The threat-model mitigations
documented in the plan are correctly implemented with one critical exception: the initial-state
branch in `gsd_driver.py` bumps `phase_step` instead of advancing `current_phase`, causing every
subsequent `emit-next` call to re-emit `/gsd-new-project --auto` indefinitely. This is a logic
bug that breaks the state machine at its entry point.

Two secondary concerns: `handle_transient` performs a blocking `time.sleep()` inside a module
that declares itself "pure function — no file I/O, no subprocess calls" — the sleep is an
undocumented side-effect that makes unit testing fragile. The unknown-error fallback in `classify`
returns `class: "transient"` with `strategy: "escalate"`, which is a semantically inconsistent
combination that will confuse any caller branching on `class`.

`references/roles/qa.md` is documentation source — reviewed for correctness; no code defects found.

---

## Critical Issues

### CR-01: `current_phase=0` branch never advances `current_phase` — state machine infinite loop

**File:** `scripts/gsd_driver.py:212-215`

**Issue:** When `current_phase == 0`, `emit_next_command` emits `/gsd-new-project --auto` and
bumps `phase_step`, but never writes `current_phase` forward. Every subsequent `emit-next`
invocation reads `current_phase=0` again and re-emits `/gsd-new-project --auto`. The state
machine is stuck at the entry point forever — the pipeline cannot progress past bootstrapping.

The comment says _"initial state (current_phase=0): emit /gsd-new-project --auto"_ implying this
is a one-shot bootstrap, but there is no mechanism to leave that state.

**Fix:** After emitting the bootstrap command, write `current_phase` to `1` so the next call
dispatches by `phase_step` instead of re-entering the bootstrap branch:

```python
if current_phase == 0:
    print("/gsd-new-project --auto")
    _write_field(project_root, "current_phase", "1")
    _write_field(project_root, "phase_step", "0")
    return 0
```

This mirrors exactly how `phase_step == 9` (line 229-232) handles phase advancement —
reset `phase_step` to 0 and write the new `current_phase`.

---

## Warnings

### WR-01: `handle_transient` performs a blocking `time.sleep()` inside a declared "pure" module

**File:** `scripts/failure_classifier.py:167`

**Issue:** The module docstring declares _"Pure function — no file I/O, no subprocess calls."_
`handle_transient` calls `time.sleep(wait)` as a side-effect before returning. This is not pure.
Consequences:

1. `test_transient_econnreset` (test line 23) calls `fc.classify("pnpm install failed: ECONNRESET")`
   without monkeypatching `time.sleep`, so it actually sleeps 1 second every test run. This is a
   latent test-speed defect today and a real slowdown if any CI retry loop triggers it.
2. The `classify()` → `handle_transient()` call chain means a caller invoking `classify()` gets
   a sleep side-effect with no warning in `classify()`'s own docstring.

**Fix (option A — preferred):** Remove the sleep from `handle_transient`; return the `backoff_seconds`
value and let the caller decide whether to sleep. This keeps the function pure and makes the
test suite instant:

```python
def handle_transient(error: str, retry_count: int = 0) -> dict:
    if retry_count >= 3:
        return {"class": "transient", "strategy": "escalate",
                "retry_ok": False, "backoff_seconds": None}
    wait = BACKOFF_SECONDS.get(retry_count, 16)
    # Caller is responsible for sleeping backoff_seconds before retry
    return {"class": "transient", "strategy": "backoff",
            "retry_ok": True, "backoff_seconds": wait}
```

**Fix (option B — minimal):** Keep the sleep but rename the function to `handle_transient_with_sleep`
and remove the "pure function" claim from the module docstring. Also update `test_transient_econnreset`
to monkeypatch `time.sleep`.

---

### WR-02: Unknown-error fallback returns semantically inconsistent `class: "transient"` + `strategy: "escalate"`

**File:** `scripts/failure_classifier.py:132-138`

**Issue:** The fallback branch (no pattern matched) returns:

```python
return {
    "class": "transient",
    "strategy": "escalate",
    "retry_ok": False,
    "backoff_seconds": None,
}
```

`class: "transient"` signals a network/retry-able error. `strategy: "escalate"` signals no more
retries. A caller that branches on `class == "transient"` and then applies transient backoff logic
will be misdirected. The `next_action_map` in `build_escalation_handoff` (line 200) keys on
`failure_class`; an unknown error maps to the `"transient"` bucket and gets the network advice
("Check network connectivity") rather than the correct generic advice.

**Fix:** Use a dedicated `"unknown"` class for the fallback:

```python
# Unknown error — escalate immediately, no retry
return {
    "class": "unknown",
    "strategy": "escalate",
    "retry_ok": False,
    "backoff_seconds": None,
}
```

Add `"unknown"` to the `next_action_map` in `build_escalation_handoff`:

```python
"unknown": "Review the error above manually, then run `/osbuilder resume`",
```

Update `classify()`'s return-type docstring to include `"unknown"` as a valid class.

---

### WR-03: `build_escalation_handoff` uses deprecated `datetime.utcnow()`

**File:** `scripts/failure_classifier.py:196`

**Issue:** `_dt.datetime.utcnow()` is deprecated since Python 3.12 and will be removed in a future
release. The rest of the codebase (e.g. `state_writer.py:84`, `gsd_driver.py:133`) correctly uses
`datetime.now(timezone.utc)`.

**Fix:**

```python
ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
```

Or keep the format consistent with gsd_driver.py:

```python
ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

---

### WR-04: `phase_step == 2` registry gate is a no-op — the verification is never run

**File:** `scripts/gsd_driver.py:218-221`

**Issue:** The code comment says _"Registry verify gate — no slash command; advance step"_ but the
actual registry verification subprocess call (`REGISTRY_VERIFY`) is never invoked. The constant
`REGISTRY_VERIFY` (line 27) is defined but never used. Step 2 simply bumps `phase_step` without
performing any check.

This means the slopsquatting defense (the main security goal of `registry_verify.py`) is wired up
in isolation but is never called from the state machine that was designed to invoke it.

Whether this is intentional (the registry gate is called by the slash command handler, not the
driver) or an oversight is not clear from the code. If the gate is supposed to be enforced here,
it is absent. If it is enforced elsewhere, `REGISTRY_VERIFY` should be removed from this file to
avoid misleading readers.

**Fix (if gate belongs here):** Call the verifier at step 2 before advancing:

```python
if phase_step == 2:
    # Registry verify gate: called by the execute phase; no stdout slash command
    # The actual check is performed by the execute phase slash command itself.
    _bump_field(project_root, "phase_step")
    return 0
```

Or, if the gate IS supposed to run here, invoke it:

```python
if phase_step == 2:
    # Verify registry before proceeding to execute phase
    pkg = state.get("pending_package", "")
    eco = state.get("pending_ecosystem", "")
    if pkg and eco:
        result = subprocess.run(
            [sys.executable, str(REGISTRY_VERIFY), "--pkg", pkg, "--ecosystem", eco],
            shell=False,
        )
        if result.returncode != 0:
            sys.stderr.write("OSBuilder: registry verify failed — install blocked.\n")
            return 1
    _bump_field(project_root, "phase_step")
    return 0
```

At minimum, remove the unused `REGISTRY_VERIFY` import constant if the gate is not called here,
to prevent future confusion.

---

## Info

### IN-01: `test_transient_econnreset` will sleep 1 second on every test run

**File:** `scripts/tests/test_failure_classifier.py:23-26`

**Issue:** `test_transient_econnreset` calls `fc.classify("pnpm install failed: ECONNRESET")`
without monkeypatching `time.sleep`. As confirmed above (WR-01), `classify` → `handle_transient`
calls `time.sleep(1)`. The test suite will be 1 second slower on every run. If this test is
called repeatedly in a retry loop, the latency compounds.

**Fix:** Add a monkeypatch for `time.sleep` in this test:

```python
def test_transient_econnreset(fc, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    result = fc.classify("pnpm install failed: ECONNRESET")
    assert result["class"] == "transient"
    assert result["strategy"] == "backoff"
```

---

### IN-02: `VERIFICATION.md` template always generates identical generic criteria regardless of phase content

**File:** `scripts/gsd_driver.py:134-157`

**Issue:** `_write_verification_md` writes a static template with two fixed criteria ("Application
loads without errors", "Primary user workflow completes end-to-end") regardless of what the phase
actually built. `qa.md` explicitly states criteria must be _"LLM-generated per phase based on what
was actually planned and built — not drawn from a static bank."_

The static template satisfies the `test_criteria_not_tests_pass` test and the count rule (2
criteria), but violates the falsifiability contract: "Primary user workflow completes end-to-end"
is vague — `qa.md` lists _"The feature works correctly"_ as a forbidden pattern.

This is a design-level gap, not a runtime bug. The function should be a placeholder that delegates
to the QA role at runtime, or the template should at minimum include the phase number in criteria
text to indicate specificity is expected.

**Fix:** Mark the current implementation as a scaffold/stub in the docstring, and note that the
`/gsd-verify-work` skill should generate phase-specific criteria from `qa.md`. Alternatively, include
a `TODO` comment making this explicit:

```python
# TODO(QA): Replace static template with LLM-generated criteria from qa.md
# per-phase, using the actual spec and plan as context. Static criteria here
# are a conformance scaffold only.
```

---

### IN-03: `_resolve_project_root` `".."` check is a substring match, not a path segment match

**File:** `scripts/gsd_driver.py:58`, `scripts/state_writer.py:74`

**Issue:** Both files check `if ".." in arg:` to block path traversal. This is a substring match.
A legitimate directory name containing `..` in its text (e.g. `"/home/user/projects/repo..backup"`)
would be rejected, and a crafted path like `"foo/...bar"` would pass the check because `...` does
not contain `..` — wait, it does: `"..."` contains `".."`. The substring check is slightly overly
broad but not dangerously permissive. The main risk is false positives, not bypasses.

The check is consistent across both files (copied verbatim per comment). No security bypass exists
given `Path(arg).resolve()` is called immediately after, normalizing the path. Low severity.

**Fix (optional hardening):** Use path-segment-level check to avoid false positives:

```python
p = Path(arg)
if any(part == ".." for part in p.parts):
    raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
return p.resolve()
```

---

_Reviewed: 2026-04-30T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
