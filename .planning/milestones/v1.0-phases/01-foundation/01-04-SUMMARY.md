# Plan 01-04 Summary — state_writer.py (TDD: RED → GREEN)

**Status:** ✓ Complete
**Requirements covered:** FOUND-05
**Commit:** `271640c`
**Tests:** `pytest scripts/tests/test_state_writer.py` — 8/8 GREEN

## Deliverable

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/state_writer.py` | OSBuilder's state.md checkpoint manager | 287 |

## TDD Gate Sequence

- **RED state** was already established by Wave 0 (Plan 01) — 8 tests collected and failing because `state_writer.py` did not exist (lazy `sw` fixture skipped them).
- **GREEN commit:** `271640c — feat(01-04): implement state_writer.py — 10-field state.md plumbing`. After this commit landed, all 8 tests turn GREEN.

## Schema (locked, 10 named fields)

`goal`, `app_type`, `playbook`, `current_role`, `current_phase`, `phase_step`,
`last_failure`, `retry_count`, `escalation_level`, `next_action` — plus an
`updated_at` ISO-8601 timestamp bookkeeping field.

state.md format: pure markdown `key: value` lines (NOT YAML, NOT JSON). Output
is 13 lines (well under the 20-line hard cap).

state.md location: `<project-root>/.planning/osbuilder/state.md`.

## CLI Surface

| Command | Purpose |
|---------|---------|
| `init --goal "..." [--app-type X] [--playbook Y]` | Create state.md with all 10 fields populated |
| `write --field NAME --value "..."` | Set one field's value |
| `read [--field NAME] [--format json]` | Print fields (plain or JSON) |
| `bump --field NAME` | Increment a counter (retry_count, escalation_level, phase_step) |
| `validate` | Exit non-zero if any of the 10 required fields is missing |

`--project-root PATH` is accepted **before or after** the subcommand (pre-parse
extraction strips it from argv before argparse sees it).

## Security (T-1-V5 / V12 / V7 mitigations)

- **V5 newline reject:** `--value` containing `\n` or `\r` rejected with friendly error
- **V5 allowlist:** `--field` must be in the 10-field allowlist; unknown fields rejected
- **V5 ordering (defense in depth):** `_check_field_allowed` runs BEFORE `_check_value_safe`
  — cheap allowlist check fails fast on hostile field names without examining payload
- **V12 path traversal:** `--value` containing `..` rejected; `--project-root` rejects
  `..` segments and resolves to absolute Path
- **V7 friendly errors:** all top-level errors caught and printed to stderr as
  `OSBuilder: ...` messages — never expose Python stack traces

## Atomic Write (Pattern 3)

`atomic_write(path, content)` uses `os.replace()` — atomic on POSIX + Windows
since Python 3.3. Tmp file is `.{stem}.{pid}.tmp` in the same directory as
the target so `os.replace` stays cross-device-safe and the cleanup test can
match `glob(".state.*.tmp")`.

`render_state_md()` and `atomic_write()` are module-level callables so the
in-process monkeypatch test (test_atomic_replace_no_partial) can monkeypatch
the rendering step and assert the original file is byte-identical after a
simulated mid-write crash.

## Pure Stdlib

No third-party dependencies. argparse + datetime + json + os + pathlib + sys.

## Self-Check: PASSED

- [x] `pytest scripts/tests/test_state_writer.py` 8/8 GREEN
- [x] `state_writer.py init --goal "test" --project-root /tmp/x` creates 13-line state.md with all 10 fields
- [x] `state_writer.py write --field goal --value $'a\nb'` rejects newline (exit 1, friendly error)
- [x] `state_writer.py write --field bogus --value ok` rejects unknown field
- [x] `state_writer.py write --field playbook --value ../../../etc/passwd` rejects `..`
- [x] `state_writer.py read --field current_role` round-trips correctly
- [x] `state_writer.py read --format json` returns parseable JSON with all 10 fields
- [x] `state_writer.py validate` exits non-zero when fields are missing
