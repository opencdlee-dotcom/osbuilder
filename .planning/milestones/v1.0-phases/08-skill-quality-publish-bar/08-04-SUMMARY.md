---
phase: 08-skill-quality-publish-bar
plan: 04
subsystem: skill-quality
tags: [QUAL-05, version-drift, validator, frontmatter, semver, marker, stdlib]
requires:
  - SKILL.md `requires:` block (08-02)
  - references/version-policy.md (08-02)
  - scripts/tests/test_check_skill_versions.py (08-01 RED stubs)
provides:
  - QUAL-05 first-session sub-skill version-drift validator
affects:
  - SKILL.md frontmatter (consumer of validator output)
  - ~/.osbuilder/last_check.txt (per-user-global session marker)
  - ~/.claude/skills/<name>/SKILL.md (read-only consumer of installed `version:`)
tech-stack:
  added: []
  patterns:
    - Hand-rolled stdlib YAML frontmatter parser (extends test_skill_md.py:_read_frontmatter for nested-block)
    - Stdlib semver tuple compare (`tuple[int, ...]` from MAJOR.MINOR.PATCH)
    - V5 input-validation regex allowlist (`^[0-9.]{1,16}$`) for fail-safe rejection of malformed/poisoned version strings
    - Per-user-global marker pattern at ~/.osbuilder/ (NOT per-project) for cross-project session throttle
    - Subcommand+main argparse shape mirroring production_phase_writer.py
key-files:
  created:
    - scripts/check_skill_versions.py
  modified: []
decisions:
  - Warn-not-block on missing `version:` field (Pitfall 2; gsd & predator currently field-less; docs/upstream-fix per composition rule)
  - Marker file is ~/.osbuilder/last_check.txt (per-user-global; reset via `rm -f`)
  - Malformed version string => (0,0,0) fail-safe ("older than anything") not exception (V5 + T-08-10/T-08-11 mitigation)
  - parse_version supports leading `v` prefix (e.g., `v6.0.0`) but only dotted-int alphabet
metrics:
  duration: ~12 min
  completed: 2026-05-05T03:55:00Z
  pytest-baseline: 196 passed / 14 skipped
  pytest-after: 200 passed / 10 skipped (+4 RED→GREEN flips, no regressions)
  script-lines: 216
---

# Phase 8 Plan 04: scripts/check_skill_versions.py (QUAL-05) Summary

QUAL-05 sub-skill version-drift validator landed: pure-stdlib CLI (`check`
subcommand) reads OSBuilder's SKILL.md `requires:` block, enumerates declared
sub-skills, reads each installed `version:` from `~/.claude/skills/<name>/SKILL.md`,
and runs the 4-mode behavior matrix (pass / BLOCK on drift / WARN on missing
version / BLOCK on missing skill dir) against `references/version-policy.md`.
Marker file at `~/.osbuilder/last_check.txt` throttles re-runs to once per
session; `--force` overrides.

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement scripts/check_skill_versions.py (TDD) | fa6f60b | scripts/check_skill_versions.py |

The 4 Wave 0 RED stubs in `scripts/tests/test_check_skill_versions.py` (landed
in 08-01) flipped from `SKIPPED` to `PASSED` once the module became importable —
no test churn, the test contract was correct as written.

## Acceptance Gates (all PASS)

| Gate | Result |
|------|--------|
| File exists & executable bit set | OK (`-rwxr-xr-x` 100755) |
| Shebang `#!/usr/bin/env python3` on line 1 | OK |
| `from __future__ import annotations` present | OK |
| Module-level constants `REPO_ROOT`, `SKILL_MD`, `SKILLS_DIR`, `MARKER`, `_VERSION_RE` | OK (5/5) |
| Public exports `check_versions`, `is_first_session`, `record_check_complete`, `parse_version`, `main` | OK (5/5) |
| Pure stdlib (no yaml/requests/packaging/semver imports) | OK (`grep -cE` = 0) |
| 4 Wave 0 tests pass | OK (`uv run pytest scripts/tests/test_check_skill_versions.py -x` = 4 passed) |
| parse_version edge cases | OK — `parse_version('1.2.3') < parse_version('1.10.0')`; `parse_version('') == (0,0,0)`; `parse_version('v6.0.0') == (6,0,0)`; `parse_version('1.0.0; rm -rf /') == (0,0,0)` |
| Real-world dry-run output documented | OK (case-b — see below) |
| Full pytest no regressions | OK (200 passed / 10 skipped — was 196/14; +4 net passes, -4 net skips, exactly the RED→GREEN delta) |

## Real-World Dry-Run

Command: `rm -f ~/.osbuilder/last_check.txt && python3 scripts/check_skill_versions.py check --force`

Stderr output:
```
OSBuilder: ⚠️  gsd has no version field — cannot enforce minimum 1.0.0. Proceeding anyway. (Reported in non-blocking mode.)
OSBuilder: ⚠️  predator has no version field — cannot enforce minimum 1.0.0. Proceeding anyway. (Reported in non-blocking mode.)
```

Exit code: `0` — case (b) from the acceptance criteria (warn lines for `gsd` &
`predator` with no version field; brainiac/code-tester/problem-solver pass
silently; overall exit 0). Marker file `~/.osbuilder/last_check.txt` was
created (3 bytes — `"ok\n"`).

### Per-sub-skill mode breakdown (verified against installed SKILL.md files)

| Sub-skill | Installed version | Declared minimum | Mode |
|-----------|-------------------|------------------|------|
| gsd | (no `version:` field) | 1.0.0 | WARN — non-blocking |
| brainiac | 6.0.0 | 6.0.0 | full-version — pass silently |
| predator | (no `version:` field) | 1.0.0 | WARN — non-blocking |
| code-tester | 3.1.0 | 3.1.0 | full-version — pass silently |
| problem-solver | 3.0.0 | 3.0.0 | full-version — pass silently |

This matches the prediction in 08-RESEARCH.md Pitfall 2 (gsd & predator are
field-less today; composition rule says fix the sub-skill upstream rather than
fork into OSBuilder; the warn-and-proceed posture keeps OSBuilder usable while
the upstream fix lands).

## Pytest Delta

- **Before plan:** 196 passed / 14 skipped (baseline at end of 08-08 / 08-07).
- **After plan:** 200 passed / 10 skipped.
- **Net:** +4 passes, -4 skips (exactly the 4 Wave 0 RED→GREEN flips).
- **Regressions:** 0.

The 4 flipped tests:
1. `test_all_meet_minimum` — fake fixture seeds gsd=1.0.0 & brainiac=6.0.0 vs
   matching minimums → `check_versions()` returns 0.
2. `test_blocks_on_drift` — fake fixture seeds brainiac=5.0.0 vs 6.0.0 minimum
   → `check_versions()` returns 1 + stderr contains `brainiac` and `5.0.0`.
3. `test_warns_on_missing_version` — fake fixture seeds gsd with no `version:`
   field → `check_versions()` returns 0 + stderr contains `gsd` and the warn
   glyph `⚠️` plus the substring `no version field`.
4. `test_first_session_marker` — `is_first_session()` toggles True → False after
   `record_check_complete()`.

## Threat-Model Coverage (T-08-10 .. T-08-14)

| Threat ID | Disposition | Implementation |
|-----------|-------------|----------------|
| T-08-10 (Tampering: version `1.0.0; rm -rf /`) | mitigate | `parse_version` applies `_VERSION_RE = ^[0-9.]{1,16}$` allowlist; non-matching → (0,0,0) fail-safe (looks "older than anything", causes BLOCK rather than execution) |
| T-08-11 (Tampering: requires: shell metachars) | mitigate | Same `_VERSION_RE` applied to every minimum-version string from SKILL.md before tuple compare |
| T-08-12 (Info disclosure: leaks ~/.claude/skills/ structure) | accept | Stderr names sub-skills already user-declared in SKILL.md `requires:`; no surprising disclosure |
| T-08-13 (Tampering: marker poisoning skips checks) | accept | Marker presence can ONLY block re-runs, never block initial run; documented mitigation `rm -f ~/.osbuilder/last_check.txt` lives in references/version-policy.md |
| T-08-14 (DoS: malformed frontmatter infinite loop) | mitigate | Parser bounded by file content length; `re.DOTALL` on simple `^---\n...\n---\n` pattern has no backtracking risk |

All threat dispositions implemented or accepted with documented rationale.

## Deviations from Plan

### Auto-fixed Issues / Soft Deviations

**1. [Soft Rule 1 — Soft target overshoot] Script line count 216 vs target 100-180**
- **Found during:** Acceptance criteria check
- **Issue:** Plan acceptance criterion sets a 100-180-line soft target ("pattern target ~150"); must_haves frontmatter sets `min_lines: 120`. Implemented script is 216 lines.
- **Why exceeded:** The plan's `<action>` block prescribes the script source verbatim — that source itself is ~220 lines including required docstrings (module docstring with 4-row behavior matrix, function docstrings for parse_version / _read_frontmatter / _read_installed_version / is_first_session / record_check_complete / check_versions / _cmd_check / main), four section dividers, friendly-error multi-line stderr writes, and the V5 allowlist mitigation comments. One pass of compaction (removed section dividers and one extra blank-line block) dropped 9 lines from 225 → 216.
- **Disposition:** Acceptable. The `min_lines: 120` floor is well exceeded; behavior is identical to plan; further compaction would lose either docstrings (disallowed by plan), threat-mitigation comments (disallowed by threat model), or the friendly-stderr-on-multiple-lines pattern (disallowed by Pitfall 2 / friendly-error.py convention). The 100-180 target was a soft estimate in the plan; the verbatim-source instruction takes precedence per the plan's own "Full file content (target ~150 lines, pure stdlib)" note (a target, not a cap).
- **Files modified:** scripts/check_skill_versions.py
- **Commit:** fa6f60b

No other deviations. The 4-test contract (08-01 Wave 0 RED stubs) matched the
implementation exactly with zero churn — the stubs predicted the exact
fixture-monkeypatch surface (`SKILL_MD`, `SKILLS_DIR`, `MARKER` module-level
constants) and the exact public-API export list (`check_versions`,
`is_first_session`, `record_check_complete`, `parse_version`, `main`).

## Authentication Gates

None — pure local file I/O, no network, no auth surface.

## Self-Check: PASSED

- File `scripts/check_skill_versions.py` exists: FOUND (216 lines, mode 100755)
- Commit `fa6f60b`: FOUND (`git log --oneline | grep fa6f60b` confirmed)
- 4 target tests pass: FOUND (`uv run pytest scripts/tests/test_check_skill_versions.py -x` = 4 passed)
- Full pytest: 200 passed / 10 skipped (+4 vs 196 baseline)
- Real-world dry-run output: case (b), exit 0, marker file created at ~/.osbuilder/last_check.txt

## QUAL-05 Success Criterion Coverage

> "First-invocation each session ... reads `requires:` from SKILL.md frontmatter
> and reports a friendly error with the exact upgrade command if any of
> GSD/brainiac/predator/code-tester/problem-solver are below their declared
> minimum compatible version"

- ✓ Reads `requires:` from SKILL.md frontmatter (via `_read_frontmatter` nested-block parser)
- ✓ Friendly error includes the **exact** upgrade command:
  `cd ~/.claude/skills/<name> && git pull` (and the install path:
  `cd ~/.claude/skills && git clone <repo-url> <name>` for missing dirs)
- ✓ All 5 sub-skills enumerated (gsd, brainiac, predator, code-tester, problem-solver)
- ✓ First-invocation gating via marker (`is_first_session()` + `record_check_complete()`)
- ✓ Pitfall 2 covered: missing `version:` field warns and proceeds (non-blocking)
- ✓ Pitfall 7 mitigated: `references/version-policy.md` (08-02) cross-references
  the validator and documents `requires:` as an OSBuilder-local convention with
  Anthropic-future-proofing notes
