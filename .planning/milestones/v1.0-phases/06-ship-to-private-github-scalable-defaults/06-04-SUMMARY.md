---
phase: 06-ship-to-private-github-scalable-defaults
plan: 04
subsystem: documentation
tags: [readme, runbook, markdown, template, ship, tdd]

# Dependency graph
requires:
  - phase: 06-01
    provides: "Wave 0 RED stubs: test_runbook_writer.py stub + fake_built_app/fake_state_md fixtures in conftest.py"
  - phase: 06-02
    provides: "gh_handoff.py ships repo_url to state.md — read by write_readme()"
provides:
  - "scripts/runbook_writer.py: write_readme(project_dir, project_root) -> Path; CLI write subcommand"
  - "assets/readme-template.md: 66-line Markdown template with 7 {{placeholder}} slots and 5 required H2 sections"
  - "V-03 GREEN: test_runbook_writes_quickstart passes (was skip)"
affects:
  - "06-06 (Wave 2 wiring): gh_handoff.py will call write_readme() after repo push"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Idempotency via HTML comment marker (<!-- OSBuilder runbook -->) — skip rewrite if marker present"
    - "str.replace() placeholder substitution over str.format() — avoids KeyError on Markdown curly braces"
    - "Post-substitution sanity check: raise SystemExit if '{{' remains in composed content"
    - "D-05 duplication: atomic_write + _resolve_project_root verbatim-copied into runbook_writer.py"

key-files:
  created:
    - scripts/runbook_writer.py
    - assets/readme-template.md
  modified:
    - scripts/tests/test_runbook_writer.py

key-decisions:
  - "Template uses 7 close-set placeholders (project_name, stack_summary, install_command, run_command, test_command, repo_url, playbook); any unknown placeholder in template raises SystemExit loudly"
  - "Idempotency marker is the literal HTML comment '<!-- OSBuilder runbook -->' embedded near top of template; second write_readme() call on same README returns without rewriting"
  - "Quick Start section unconditionally includes 'pre-commit install' line regardless of playbook (Pitfall 2 mitigation)"
  - "_derive_commands() is a pure function mapping playbook string to command dict — web/cli/ai-service branches; generic fallback for unknown playbooks"

patterns-established:
  - "Runbook stamping is deterministic composition — no LLM calls; the 'How OSBuilder built this' section is a placeholder filled by Phase 5 /gsd-docs-update"

requirements-completed:
  - SHIP-02

# Metrics
duration: 2min
completed: 2026-05-01
---

# Phase 6 Plan 04: Runbook Writer Summary

**Deterministic README stamping via `assets/readme-template.md` + `scripts/runbook_writer.py` — V-03 GREEN, 138 passed 6 skipped, zero regressions**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-01T22:02:02Z
- **Completed:** 2026-05-01T22:04:27Z
- **Tasks:** 1 (GREEN implementation — RED stub existed from 06-01)
- **Files modified:** 3

## Accomplishments

- `scripts/runbook_writer.py` provides `write_readme(project_dir, project_root) -> Path`: reads state.md JSON via state_writer subprocess, loads template, substitutes 7 placeholders with `str.replace()`, atomic-writes README.md; idempotent (returns without rewriting if marker present)
- `assets/readme-template.md`: 66-line template with all 5 required H2 sections (Quick Start, Requirements, Configuration, Development, Tests), `<!-- OSBuilder runbook -->` idempotency marker, `cp .env.example .env` and `pre-commit install` Pitfall-2 lines
- `test_runbook_writer.py::test_runbook_writes_quickstart` flipped from skip to GREEN (V-03); full suite 138 passed 6 skipped

## Task Commits

1. **GREEN: runbook_writer.py + readme-template.md + V-03** - `6e29bd8` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `scripts/runbook_writer.py` - write_readme(), _derive_commands(), _read_state(), atomic_write(), _resolve_project_root(), CLI write subcommand, OSBUILDER_MARKER constant
- `assets/readme-template.md` - 66-line Markdown template with 7 {{placeholder}} slots, 5 H2 sections, idempotency marker
- `scripts/tests/test_runbook_writer.py` - Full GREEN implementation (was stub with pytest.skip)

## Decisions Made

- Used `str.replace()` not `str.format()` for placeholder substitution — Markdown bodies contain `{}` characters that trip `str.format()` with KeyError
- Post-substitution check (`"{{" in composed`) raises `SystemExit` loudly on any unsubstituted placeholder — catches template typos at write time, not discovery time
- Idempotency check reads existing README before loading template — avoids template I/O on re-runs

## Deviations from Plan

None — plan executed exactly as written. Implementation follows the plan's `<implementation>` section verbatim.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `write_readme()` is ready to be called by `gh_handoff.py` in Plan 06-06 (Wave 2 wiring)
- V-03 satisfied; remaining V-IDs in this phase: V-14/15 (refusal — 06-05), V-16/17 (production phases — 06-05), V-07 (gitleaks integration — env-gated)

## Self-Check

- [x] `scripts/runbook_writer.py` exists
- [x] `assets/readme-template.md` exists (66 lines)
- [x] `scripts/tests/test_runbook_writer.py` updated (GREEN)
- [x] Commit `6e29bd8` exists

## Self-Check: PASSED

---
*Phase: 06-ship-to-private-github-scalable-defaults*
*Completed: 2026-05-01*
