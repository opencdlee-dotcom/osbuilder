---
phase: 06-ship-to-private-github-scalable-defaults
plan: "05"
subsystem: intake-refusal-gate
tags: [refusal-gate, production-ready, slash-commands, tdd, scl-05, scl-06]
dependency_graph:
  requires:
    - "06-01"   # Wave 0 RED stubs + fixtures
  provides:
    - "REFUSE_KEYWORDS"
    - "check_refuse_list"
    - "production_phase_writer.emit"
    - "references/refuse-list.md"
  affects:
    - "scripts/intake_handler.py"
    - "scripts/production_phase_writer.py"
    - "references/refuse-list.md"
tech_stack:
  added: []
  patterns:
    - "Word-boundary regex for single-word keywords (\\b<kw>\\b); substring match for multi-word/hyphenated"
    - "Section parser: \\n## H2 newline-prefix search to avoid backtick-quoted references in blockquotes"
    - "Exit-code sentinel: check-refuse-list returns 2 (refused) vs 0 (clean) — callers distinguish from real errors"
key_files:
  created:
    - references/refuse-list.md
    - scripts/production_phase_writer.py
  modified:
    - scripts/intake_handler.py
    - scripts/tests/test_refusal.py
    - scripts/tests/test_production_ready.py
decisions:
  - "Newline-prefix marker search (\\n## Refusal copy) instead of plain string find to avoid false match on blockquote backtick reference on line 5 of refuse-list.md"
  - "check-refuse-list CLI exit code 2 (not 1) for refused — distinguishes 'refused, do not advance' from real errors (exit 1)"
  - "Multi-word/hyphenated keywords use direct substring; single-word uses \\b regex — matches PATTERNS.md Pitfall 10 guidance"
metrics:
  duration_seconds: 253
  completed_date: "2026-05-01T22:11:04Z"
  tasks_completed: 4
  files_changed: 5
---

# Phase 06 Plan 05: Refusal Gate + Production Phase Writer Summary

Refusal gate in `intake_handler.py` + `production_phase_writer.py` + `references/refuse-list.md` implementing SCL-05 (K8s/microservices default refusal) and SCL-06 (`--production-ready` emits 7 named ROADMAP phases to stdout).

## What Was Built

### Task 1 — references/refuse-list.md (commit 65b2ec5)
Created `references/refuse-list.md` with:
- `## Refuse keywords` H2 listing all 10 refuse keywords
- `## Refusal copy` H2 with user-facing opt-in message mentioning `--production-ready` (4 occurrences)
- `## See also` footer linking back to `intake_handler.py` and `production_phase_writer.py`

### Task 2 — intake_handler.py refusal gate (commit 2b325d6)
Extended `scripts/intake_handler.py` with:
- `REFUSE_KEYWORDS` tuple (10 entries, multi-word first)
- `REFUSE_LIST_MD` constant pointing to `references/refuse-list.md`
- `_read_state` / `_write_state_field` helpers (D-05 verbatim duplicates)
- `_load_refusal_copy`: reads `## Refusal copy` section at runtime (newline-prefix search avoids blockquote false match)
- `_matches_refuse_keyword`: word-boundary regex for single-word; substring for multi-word/hyphenated
- `check_refuse_list(project_root)`: public gate — bypasses when `production_ready=true`; writes `last_failure=refused: <kw>` + emits refusal copy to stderr on hit; returns True
- `check-refuse-list` CLI subcommand (exit 2 on refused, 0 on clean)

### Task 3 — scripts/production_phase_writer.py (commit 41c0db5)
Created `scripts/production_phase_writer.py` with:
- `NAMED_UPGRADES` tuple (7 entries: observability, migrations, healthchecks, secret-manager, sentry, rate-limiting, backups)
- `emit(project_root)`: reads state.md; if `production_ready=true`, prints 7 `/gsd-add-phase <name>` lines; otherwise zero output
- `emit` CLI subcommand with `--project-root`
- Pure stdlib; D-05 helpers duplicated verbatim

### Task 4 — Test stubs flipped GREEN (commit 903ea1c)
Flipped `test_refusal.py` and `test_production_ready.py` from `pytest.skip` to real implementations:
- V-14 `test_kubernetes_refused`: stages k8s fixture, asserts True return, `last_failure` starts with `refused:`, stderr has `production-ready`
- V-14 neg `test_clean_spec_passes`: clean fixture, asserts False return
- V-15 `test_refusal_copy_mentions_opt_in`: reads `references/refuse-list.md`, asserts `production-ready` substring
- V-16 `test_emits_seven_phases`: seeds `production_ready=true`, asserts 7 `/gsd-add-phase` lines + all NAMED_UPGRADES present
- V-17 `test_no_emit_when_default`: no `production_ready` set, asserts empty stdout

## Test Results

| Suite | Before | After |
|-------|--------|-------|
| Total passed | 138 | 143 |
| Skipped | 6 | 1 |
| Failed | 0 | 0 |
| Regressions | — | 0 |

V-14, V-15, V-16, V-17 all GREEN. `test_clean_spec_passes` also flipped (was a skip stub in the same file).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Blockquote false match in _load_refusal_copy**
- **Found during:** Task 2 (first test run)
- **Issue:** `text.find("## Refusal copy")` matched the backtick-quoted reference in the blockquote on line 5 of `refuse-list.md` (`` `## Refusal copy` ``), extracting the wrong section. Stderr showed the blockquote text instead of the refusal copy.
- **Fix:** Changed marker to `"\n## Refusal copy"` (newline-prefixed) so only the actual H2 header matches.
- **Files modified:** `scripts/intake_handler.py`
- **Commit:** 2b325d6 (fix included in same feat commit)

## Known Stubs

None — all deliverables are fully wired. `check_refuse_list` reads a real `derived_spec.md`, writes a real `last_failure` field, and loads a real `refuse-list.md`. `production_phase_writer.emit` reads real state.md. No placeholder data or hardcoded mock returns remain.

## Threat Flags

None. All new surface is:
- Read-only on `derived_spec.md` and `refuse-list.md` (no exec, no interpolation)
- Write-only on `state.md` via state_writer subprocess allowlist (field `last_failure` is in `ALLOWED_FIELDS`)
- Stdout-only for `production_phase_writer` (no file writes, no subprocess exec)

All threat mitigations from the plan's STRIDE register are implemented as designed (T-06-05-01 through T-06-05-06).

## Self-Check: PASSED
