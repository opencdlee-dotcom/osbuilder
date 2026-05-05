---
phase: 08-skill-quality-publish-bar
plan: 02
subsystem: skill-frontmatter-and-version-policy-doc
tags: [wave-2, qual-05, requires-block, version-policy]
requires:
  - .planning/phases/08-skill-quality-publish-bar/08-RESEARCH.md
  - .planning/phases/08-skill-quality-publish-bar/08-PATTERNS.md
  - .planning/phases/08-skill-quality-publish-bar/08-01-SUMMARY.md
provides:
  - "SKILL.md frontmatter `requires:` block — declares minimums for 5 sub-skills (gsd, brainiac, predator, code-tester, problem-solver)"
  - "references/version-policy.md — OSBuilder-local convention doc (78 lines): format + 4-row behavior table + Anthropic-future-proofing disclaimer + See also footer"
affects:
  - "08-03 (scripts/check_skill_versions.py) — reads requires: block as source of truth via extended _read_frontmatter() parser"
  - "scripts/tests/test_check_skill_versions.py RED stubs (3 of 4) — depend on requires: block being parseable + version-policy.md cross-link"
tech-stack:
  added: []
  patterns:
    - "Custom frontmatter convention with disclaimer (`requires:` block — non-Anthropic-standard, namespaced if conflict materializes per Pitfall 7)"
    - "Maintainer-only reference doc shape (refuse-list.md/markers.md analog: cross-reference header + policy table + See also footer)"
key-files:
  created:
    - references/version-policy.md
  modified:
    - SKILL.md
decisions:
  - "Used `requires:` (short-and-clear) over `osbuilder-requires:` (forward-compatible) — RESEARCH.md Q5 RESOLVED in favor of intuitiveness; migration documented in version-policy.md if Anthropic ever standardizes a conflicting `requires:` field"
  - "Pinned versions: gsd 1.0.0, brainiac 6.0.0, predator 1.0.0, code-tester 3.1.0, problem-solver 3.0.0 — brainiac/code-tester/problem-solver match installed reality (verified 2026-05-02); gsd/predator are baseline for future versions that DO declare a version (currently no `version:` field, validator will warn-not-block per Pitfall 2)"
  - "Per-user-global marker location locked at `~/.osbuilder/last_check.txt` (RESEARCH.md Q6 RESOLVED) — documented in version-policy.md `## Resetting the marker` and `## Why per-user-global, not per-project` sections"
metrics:
  duration: ~3min
  completed: 2026-05-04
  tasks: 2
  files: 2
---

# Phase 08 Plan 02: SKILL.md `requires:` block + version-policy.md Summary

QUAL-05 prerequisite landed: SKILL.md frontmatter now declares minimum versions for all 5 sub-skills via a 6-line `requires:` block (data-driven source of truth for the 08-03 validator), and `references/version-policy.md` documents the OSBuilder-local convention with format spec, 4-row behavior table, and Anthropic-future-proofing disclaimer.

## Final SKILL.md Line Count

- **Before:** 130 lines
- **After:** 136 lines (+6 for the `requires:` block)
- **QUAL-01 invariant:** preserved — 136 ≤ 200 (64 lines headroom remaining)

## requires: Block Contents (Verbatim)

```yaml
requires:
  gsd: 1.0.0
  brainiac: 6.0.0
  predator: 1.0.0
  code-tester: 3.1.0
  problem-solver: 3.0.0
```

Indentation is exactly 2 spaces — matches the extended `_read_frontmatter()` parser pattern documented in 08-PATTERNS.md (08-03 will land that parser).

## Version Pinning Rationale (verified 2026-05-02)

| Sub-skill | Pinned minimum | Installed version | Notes |
|-----------|---------------|-------------------|-------|
| brainiac | 6.0.0 | 6.0.0 | matches installed reality |
| code-tester | 3.1.0 | 3.1.0 | matches installed reality |
| problem-solver | 3.0.0 | 3.0.0 | matches installed reality |
| gsd | 1.0.0 | (no version field) | baseline for future versions; validator warns-not-blocks per Pitfall 2 |
| predator | 1.0.0 | (no version field) | baseline for future versions; validator warns-not-blocks per Pitfall 2 |

## references/version-policy.md Stats

- **Path:** `references/version-policy.md`
- **Lines:** 78 (≥ 30 threshold)
- **Sections:** 6 H2 headings — Format, Behavior on first invocation, Resetting the marker, Why per-user-global not per-project, Updating the minimums, See also
- **Behavior table:** 4 rows (meet / below-minimum / version-absent / not-installed) + header
- **Cross-references:** 3 mentions of `scripts/check_skill_versions.py` (1 in cross-reference header + 1 inline in behavior section + 1 in See also footer)

## test_skill_md.py — Confirmed GREEN

```
scripts/tests/test_skill_md.py ...                                       [100%]
============================== 3 passed in 0.01s ===============================
```

The pre-existing hand-rolled `_read_frontmatter()` parser at `scripts/tests/test_skill_md.py:15-40` does NOT explode on the new `requires:` block — its line-startswith-space heuristic treats the indented sub-keys as continuation of the empty-valued `requires:` parent, leaving `name`/`description`/`allowed-tools`/etc. untouched. T-08-04 mitigation confirmed.

## Full pytest Suite — Confirmed GREEN

```
========== 189 passed, 21 skipped, 4 deselected, 1 warning in 11.26s ===========
```

Identical to 08-01's post-Wave-0 baseline (189/21/4). No regression. The 21 skipped includes the 20 Phase-8 RED stubs (waiting on 08-03..08-08 to flip) plus the 1 pre-existing skip from prior phases.

## Acceptance Gate Re-Run

| Gate | Result |
|------|--------|
| `wc -l SKILL.md` between 131 and 140 | PASS (136) |
| `wc -l SKILL.md` ≤ 200 | PASS (136 ≤ 200) |
| `grep -c "^requires:" SKILL.md` == 1 | PASS (1) |
| `grep -E "^  (gsd\|brainiac\|predator\|code-tester\|problem-solver): [0-9.]+$" SKILL.md` returns 5 | PASS (5) |
| `grep -c "^---$" SKILL.md` == 2 | PASS (2) |
| `uv run pytest scripts/tests/test_skill_md.py -x` GREEN | PASS (3 passed) |
| `references/version-policy.md` exists | PASS |
| `wc -l references/version-policy.md` ≥ 30 | PASS (78) |
| `# OSBuilder Version Policy` heading present | PASS |
| `## Format` section with yaml fenced block | PASS |
| `## Behavior on first invocation` section with 4-row table | PASS (4 data rows + 1 header = 5 `^| ` lines) |
| `## See also` footer present | PASS |
| `scripts/check_skill_versions.py` cross-link present | PASS (3 references) |

## Threat Mitigation Re-confirmation

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-08-04 (parser breaks on requires: block) | mitigate | CONFIRMED — test_skill_md.py 3/3 GREEN; existing hand-parser handles indented sub-keys as parent-key continuation without exploding |
| T-08-05 (shell metacharacters in version strings) | mitigate | CONFIRMED — pinned values are dotted-integer literals matching `[0-9.]{1,16}`; the 08-03 validator will re-apply the regex allowlist |
| T-08-06 (future Anthropic spec conflict) | accept | CONFIRMED — disclaimer landed in version-policy.md (lines 7-12); migration path to `osbuilder-requires:` documented in Pitfall 7 reference |

## Downstream Unblocked

- **08-03** (`scripts/check_skill_versions.py`) — `requires:` block now exists in SKILL.md; validator can parse it via the extended `_read_frontmatter()` pattern from 08-PATTERNS.md lines 132-165. `references/version-policy.md` cross-referenced in script docstring per plan frontmatter `key_links`.
- **scripts/tests/test_check_skill_versions.py** RED stubs — 3 of 4 stubs (test_all_meet_minimum / test_blocks_on_drift / test_warns_on_missing_version) now have a SKILL.md frontmatter to seed against; the 4th (test_first_session_marker) was independent.

## Deviations from Plan

None — plan executed exactly as written (verbatim content per 08-PATTERNS.md template, 5-version pinning per Task 1 action block, Pitfall 1 mitigation respected with body content untouched).

## Authentication Gates

None encountered — all changes are local file edits.

## Self-Check: PASSED

- File `SKILL.md` (modified, 136 lines) — FOUND
- File `references/version-policy.md` (new, 78 lines) — FOUND
- Commit `7f18a3c` (feat(08-02): add requires: block to SKILL.md frontmatter) — FOUND
- Commit `9d3c3e7` (docs(08-02): create references/version-policy.md) — FOUND
