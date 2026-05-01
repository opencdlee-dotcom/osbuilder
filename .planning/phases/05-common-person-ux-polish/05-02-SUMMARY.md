---
phase: 05-common-person-ux-polish
plan: "02"
subsystem: friendly-error-translator
tags:
  - friendly-error
  - translator
  - dictionary
  - graceful-degrade
  - tdd-green
requirements:
  - UX-02
  - UX-05
dependency-graph:
  requires:
    - scripts/tests/test_friendly_error.py (11 RED stubs from Plan 05-01)
    - scripts/failure_classifier.py (module shape analog)
  provides:
    - scripts/friendly_error.py (translate, load_dictionary, FriendlyMessage)
    - references/friendly-errors/dictionary.yaml (30 entries × 9 fields)
    - references/friendly-errors/README.md (5 H2 sections)
    - import-guard wiring in 5 scripts (preflight_check, scaffold_dispatch, stack_researcher, intake_handler, gsd_driver)
  affects:
    - All future Phase 5 + Phase 6+ scripts that surface raw subprocess errors — they can now route through `_fe.translate` for plain-English output
tech-stack:
  added: []
  patterns:
    - hand-rolled YAML subset parser (no third-party YAML dep)
    - first-match dictionary precedence (ORDER MATTERS — copied from failure_classifier)
    - graceful-degrade import guard (`try: import friendly_error as _fe / except ImportError: _fe = None`)
    - traceback / Node-stack-frame strip in generic fallback
    - `_safe_format` ctx interpolation (catches KeyError, returns original template)
key-files:
  created:
    - scripts/friendly_error.py
    - references/friendly-errors/dictionary.yaml
    - references/friendly-errors/README.md
    - .planning/phases/05-common-person-ux-polish/05-02-SUMMARY.md
  modified:
    - scripts/tests/test_friendly_error.py (11 RED stubs flipped to GREEN)
    - scripts/preflight_check.py (import guard + 2 wiring sites)
    - scripts/scaffold_dispatch.py (import guard + 4 wiring sites)
    - scripts/stack_researcher.py (import guard only)
    - scripts/intake_handler.py (import guard only)
    - scripts/gsd_driver.py (import guard + 3 wiring sites)
decisions:
  - "Hand-rolled YAML subset parser keeps friendly_error.py self-contained — no PyYAML dependency. Parser handles inline scalars, nested block sequences (1 level for schema_fields), `~` → None, comments. Multi-line block scalars (`|`, `>`) are NOT implemented; the dictionary doesn't need them, and adding them would require additional tests."
  - "format_version gate is fail-fast SystemExit (T-05-02-02 mitigation). Module-init load suppresses both FileNotFoundError and SystemExit so the module is always importable; translate() falls back to the generic translator when the dictionary is empty."
  - "scaffold_dispatch.py has 4 wiring sites, not 3 as the plan listed — the second pnpm-add warning (drizzle-kit) was wrapped for consistency since both warnings surface the same class of error."
  - "stack_researcher.py and intake_handler.py have import-guard ONLY, per plan instructions — their existing sys.stderr.write calls are either generic argparse error paths (`OSBuilder: error — {e}`) or input-validation paths that emit fixed text rather than raw subprocess output. Wrapping them was out of scope."
  - "test_dictionary_format_version_checked uses tmp_path with a tiny `format_version: \"9.9\"` document — sufficient to exercise the format-version gate without bumping the live dictionary's count check."
metrics:
  duration: ~12 minutes (single agent, sequential)
  tasks: 2
  files: 9 (4 created, 5 modified)
  completed: 2026-04-30
---

# Phase 5 Plan 02: Friendly-Error Translator Summary

**One-liner:** Translates raw subprocess and exception output into plain-English `FriendlyMessage` objects via a 30-entry YAML dictionary plus a generic-fallback path that strips Python tracebacks and Node stack frames; wired into 5 OSBuilder scripts with a graceful-degrade import guard.

## Outcome

After this plan, every raw subprocess error in OSBuilder's 5 main user-facing scripts (preflight_check, scaffold_dispatch, stack_researcher, intake_handler, gsd_driver) gets translated to a plain-English FriendlyMessage before reaching stderr — no stack traces, no errno codes, no Python module names. The translator is `scripts/friendly_error.py`, a pure-stdlib module with a hand-rolled YAML subset parser; the dictionary lives at `references/friendly-errors/dictionary.yaml` with a `format_version: "1.0"` gate that fails fast on tampered/drifted files. All 11 RED stubs from Plan 05-01 flip GREEN; full test suite is 89 passed, 35 skipped (other Wave 1 stubs), 0 failed, 0 errored.

## Tasks Executed

| Task | Description | Files | Commit |
|---|---|---|---|
| 1 | friendly_error.py + dictionary.yaml + README.md (TDD: tests pass after impl) | scripts/friendly_error.py, references/friendly-errors/dictionary.yaml, references/friendly-errors/README.md, scripts/tests/test_friendly_error.py | be6fc11 |
| 2 | Wire `_fe.translate` into 5 error-path scripts | scripts/preflight_check.py, scripts/scaffold_dispatch.py, scripts/stack_researcher.py, scripts/intake_handler.py, scripts/gsd_driver.py | 5d78bbe |

### Module surface (Task 1)

| Symbol | Type | Purpose |
|---|---|---|
| `FriendlyMessage` | dataclass | 5 fields: title, what_broke, what_to_do, copy_paste, severity |
| `Severity` | Literal type | "info" \| "warn" \| "error" \| "fatal" |
| `translate(raw, ctx)` | function | First-match dictionary lookup → entry message OR generic fallback |
| `load_dictionary(path)` | function | Parse + validate YAML; raises SystemExit on format-version drift or <30 entries |
| `_parse_yaml_subset(raw)` | private | Hand-rolled parser (~70 lines) — inline scalars, nested lists, `~`, comments |
| `_strip_tracebacks(text)` | private | Removes Python `Traceback (most recent...)` blocks + Node `at fn (file:line)` frames |
| `_generic_translator(text, ctx)` | private | Last-line fallback when no dictionary entry matches |
| `_build_message(entry, ctx)` | private | Format dictionary entry with `_safe_format` ctx interpolation |
| `_safe_format(template, ctx)` | private | `template.format(**ctx)` with KeyError/IndexError/ValueError → original template |
| CLI shim | `__main__` | Reads stdin, prints rendered translation to stdout |

### Dictionary inventory (30 entries)

| Category | Entries |
|---|---|
| registry | slopsquat-blocked, npm-404, pypi-404 |
| preflight | pnpm-not-found, npm-not-found, python-not-found, node-version-old |
| gh-auth | gh-not-found, gh-token-conflict, gh-token-expired |
| docker | docker-not-installed, docker-daemon-not-running, pg-conn-refused, pg-auth-fail |
| runtime | port-in-use, module-not-found-py, module-not-found-js, next-build-fail |
| scaffold | tailwind-bad-class, humanizer-missing, gsd-skill-missing |
| filesystem | eacces-generic, path-traversal-rejected, state-md-missing, enoent-generic |
| network | network-econnreset, network-timeout, dns-resolve-fail |
| git | git-not-a-repo, git-merge-conflict |

ORDER: most-specific entries first. `slopsquat-blocked` precedes `npm-404` and `pypi-404`; `pnpm-not-found` precedes `npm-not-found`; `port-in-use` (regex `EADDRINUSE`) precedes `enoent-generic` (substring `ENOENT`).

### Wiring sites (Task 2)

| Script | Sites | Type |
|---|---|---|
| scripts/preflight_check.py | 2 | apply() FileNotFoundError + install exit nonzero |
| scripts/scaffold_dispatch.py | 4 | pnpm-not-found, create-next-app exit, drizzle-orm pnpm-add warning, drizzle-kit pnpm-add warning |
| scripts/gsd_driver.py | 3 | unknown phase_step, no state.md (×2 — emit_next + status), CalledProcessError in _cmd_status |
| scripts/stack_researcher.py | 0 | import guard only — existing stderr writes are argparse / generic main exception |
| scripts/intake_handler.py | 0 | import guard only — existing stderr writes are input validation, not raw subprocess output |

## Verification

| Check | Expected | Result |
|---|---|---|
| `load_dictionary()` entry count | ≥ 30 | **30** |
| Each entry has 9 required fields | yes | yes (verified across all 30 entries) |
| `translate("EADDRINUSE...")` title | ≠ "Something went wrong" | **"The port is already taken"** |
| `translate(traceback...)` what_broke | no "Traceback", no `File "` | **clean** ("RuntimeError: boom") |
| `translate("pnpm: command not found")` title | ≠ "Something went wrong" | **"pnpm isn't installed yet"** |
| README has 5 H2 sections | yes | yes |
| All 5 scripts have `import friendly_error as _fe` | yes | yes (5/5) |
| All 5 modules import cleanly | yes | yes (`python3 -c "import preflight_check; import scaffold_dispatch; ..."` exits 0) |
| Full test suite | no regressions | **89 passed, 35 skipped, 0 failed** |
| test_friendly_error.py: 11 stubs GREEN | 11 pass | **11 pass** |
| Phase 4 tests still green | 78 passed | **78 passed** (unchanged) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] Wrapped 4th scaffold_dispatch.py warning site for consistency**

- **Found during:** Task 2
- **Issue:** The plan listed 3 wiring sites in scaffold_dispatch.py — pnpm-not-found, create-next-app exit, and the drizzle-orm pnpm-add warning. There is also a drizzle-kit pnpm-add warning ~10 lines later that surfaces the same class of error to the user.
- **Fix:** Wrapped both pnpm-add warnings (drizzle-orm AND drizzle-kit) with the same translation pattern. Both surface raw subprocess exit codes and would have shown a hybrid output (one wrapped, one not) to the user — inconsistent UX.
- **Files modified:** scripts/scaffold_dispatch.py
- **Commit:** 5d78bbe

**2. [Rule 2 — Missing critical functionality] Wrapped second `no state.md` site in gsd_driver.py for consistency**

- **Found during:** Task 2
- **Issue:** The plan listed `_cmd_emit_next` and `_cmd_status` as separate sites for the missing-state.md error. Both surface the identical `no state.md at {path}` message; wrapping only one would mean different UX depending on which subcommand the user ran.
- **Fix:** Wrapped both sites with identical translation pattern.
- **Files modified:** scripts/gsd_driver.py
- **Commit:** 5d78bbe

The plan called for "5 sites" total in gsd_driver.py (3 listed); after wrapping both state-md-missing sites and the CalledProcessError site, there are 4 wiring sites. The unknown-phase_step site was wrapped per plan.

### Out of Scope (deferred / not done)

- **stack_researcher.py and intake_handler.py wrapping:** Per plan instructions ("if no error sites beyond graceful-degrade paths, add the import guard only"). Their existing stderr writes are argparse error paths (`OSBuilder: --advanced-overrides is not valid JSON`), generic main exception handlers, or input-validation paths emitting fixed text — none surface raw subprocess output. Future plans can wrap these if user-facing UX justifies it.
- **CLI subprocess invocation tests:** test_friendly_error.py asserts module behavior + wiring presence (grep for `_fe.translate`). End-to-end "wired site emits a translated message" tests are out of scope; the wiring is structurally verified by `test_error_paths_wrapped_in_known_sites` and the import guards are verified by `test_import_guard_in_all_five_scripts`.

## Threat Model Compliance

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-05-02-01 (Information Disclosure — traceback in fallback) | `_strip_tracebacks` removes Python `Traceback ...` blocks + indented `File "..."` frames + Node `at fn (file:line)` frames | mitigated; verified by `test_generic_fallback_strips_traceback` and `test_friendly_message_no_raw_stack_frames` |
| T-05-02-02 (Tampering — dictionary format_version drift) | `load_dictionary` raises SystemExit on `format_version != "1.0"` or fewer than 30 entries | mitigated; verified by `test_dictionary_format_version_checked` |
| T-05-02-03 (Tampering — copy_paste interpolation) | `_safe_format` catches KeyError/IndexError/ValueError; copy_paste is rendered as plain text only, never auto-executed | mitigated; copy_paste output is sent to stderr as text |
| T-05-02-04 (DoS — YAML parser on malformed file) | `_parse_yaml_subset` is non-recursive; bounded by file size (small data file, ~330 lines); exception → SystemExit with clear message | mitigated; module-init load also catches FileNotFoundError + SystemExit |
| T-05-02-05 (Information Disclosure — build.log path in fallback) | what_to_do says "Check the debug log at .planning/osbuilder/build.log" — relative, project-local; no secret leakage | accepted as designed |

No new threat surface introduced.

## Threat Flags

None — the 5 scripts wired in this plan already had the relevant trust boundaries (subprocess invocation, file paths, state.md write) reviewed in their original phases. This plan only adds an output-translation layer on the user-facing edge.

## Self-Check

- All 4 created files exist:
  - scripts/friendly_error.py ✓ FOUND
  - references/friendly-errors/dictionary.yaml ✓ FOUND
  - references/friendly-errors/README.md ✓ FOUND
  - .planning/phases/05-common-person-ux-polish/05-02-SUMMARY.md ✓ FOUND (this file)
- Commit be6fc11 exists ✓ FOUND
- Commit 5d78bbe exists ✓ FOUND
- All 5 scripts contain `import friendly_error as _fe`: ✓ 5/5 FOUND
- 30 dictionary entries with 9 fields each: ✓ verified
- 11 of 11 test_friendly_error.py tests pass: ✓ PASS
- 78 Phase 4 tests still green (no regressions): ✓ PASS
- README has all 5 H2 sections: ✓ PASS

## Self-Check: PASSED

## Next

Phase 5 Wave 1 plans 03 (narration), 04 (tutor mode + mode gating), 05 (tech writer) flip the remaining 35 RED stubs to GREEN. None of those plans depend on friendly_error.py changes — they can run independently.
