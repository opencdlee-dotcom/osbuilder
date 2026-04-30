---
phase: 02-pre-flight-installer-cross-platform
plan: 04
subsystem: docs
tags: [reference-docs, preflight, macos, linux, windows, progressive-disclosure, homebrew, apt, dnf, winget]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "references/README.md (parent directory seeded), SKILL.md (locked at ≤200 lines, D-13)"
  - phase: 02-pre-flight-installer-cross-platform-plan-02
    provides: "scripts/preflight_check.py with _MACOS_INSTALL/_APT_INSTALL/_DNF_INSTALL/_WINGET_INSTALL tables (source-of-truth package IDs)"
provides:
  - "references/preflight/README.md — D-13 handoff entry point for /osbuilder preflight (71 lines)"
  - "references/preflight/macos.md — Homebrew install matrix + OrbStack default + system-Python pitfall + transitive-deps caveat (94 lines)"
  - "references/preflight/linux.md — apt + dnf decision tree + ID_LIKE detection + sudo UX + unsupported-distro refusal (114 lines)"
  - "references/preflight/windows.md — winget primary + scoop fallback + PATH-refresh + Docker Desktop license + nvm-windows APPDATA caveat + choco anti-recommendation (128 lines)"
affects: [phase-3-web-playbook, phase-5-common-person-ux, gsd-verify-phase-2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Progressive-disclosure documentation: per-OS reference files loaded on-demand by Architect role, not pre-loaded in SKILL.md"
    - "Doc-code lockstep: package IDs in reference docs must match _MACOS_INSTALL/_APT_INSTALL/_DNF_INSTALL/_WINGET_INSTALL tables in preflight_check.py; enforced post-hoc by /gsd-verify-phase"

key-files:
  created:
    - references/preflight/README.md
    - references/preflight/macos.md
    - references/preflight/linux.md
    - references/preflight/windows.md
  modified: []

key-decisions:
  - "D-13 honored: NO SKILL.md edit — references/preflight/README.md serves as the handoff entry point (SKILL.md remains 127 lines / 9666 bytes)"
  - "D-09 documented: Linux v1 = apt + dnf only; other distros refuse with 'PR welcome' message in linux.md"
  - "D-10 documented: Windows = winget primary, scoop fallback; choco explicitly anti-recommended in windows.md"
  - "D-11 intent documented: OrbStack is preferred macOS Docker runtime per docs.orbstack.dev; code has known inconsistency (package_id='docker' not 'orbstack') tracked for v2"
  - "W-03 lockstep: docs and code both derive from Apr-2026-verified IDs in 02-RESEARCH.md; cross-script enforcement deferred to /gsd-verify-phase (depends_on=[] parallelism preserved)"

patterns-established:
  - "Reference docs use verbatim package IDs from research (never invented) — enables mechanical cross-check at verify time"
  - "Per-OS pitfall cross-references: linux.md documents Pitfall 5 + 14; windows.md documents Pitfall 3 + 4; macos.md documents Pitfall 2 + 6"

requirements-completed: [PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-06, PRE-07]

# Metrics
duration: 8min
completed: 2026-04-30
---

# Phase 02 Plan 04: Pre-flight Reference Documentation Summary

**Four per-OS reference docs under references/preflight/ documenting brew/apt/dnf/winget install matrices, version-manager refusal flow, and platform-specific gotchas for scripts/preflight_check.py**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-30T07:17:12Z
- **Completed:** 2026-04-30T07:25:00Z
- **Tasks:** 2
- **Files modified:** 4 created, 0 modified

## Accomplishments

- Created `references/preflight/README.md` (71 lines) as the D-13 handoff entry point — documents what preflight does, how it works, per-OS links, bootstrap handoff flow, and --no-docker mode (PRE-07)
- Created `references/preflight/macos.md` (94 lines) with Homebrew install matrix (5 tools), OrbStack as default Docker runtime (D-11), system-Python pitfall (Pitfall 2), transitive-deps caveat (Pitfall 6), version-manager refusal flow (Pitfall 13)
- Created `references/preflight/linux.md` (114 lines) with apt + dnf decision tree, ID_LIKE detection rationale, supported/unsupported distro tables, sudo prompt UX (Pitfall 5), cross-platform shell discipline (Pitfall 14), unsupported-distro refusal flow (D-09)
- Created `references/preflight/windows.md` (128 lines) with winget primary + scoop fallback (D-10), PATH-refresh two-mode pattern cross-referencing bootstrap.ps1:39-44 (Pitfall 3), Docker Desktop license note (Pitfall 4), nvm-windows APPDATA caveat, choco anti-recommendation (W-06)
- All 4 doc-grep gates from 02-VALIDATION.md lines 58-61 pass (4/4)
- SKILL.md byte-equivalent before/after (127 lines / 9666 bytes)
- All 30 tests GREEN

## Package-ID Alignment Verification

### macOS (brew) — 5/5
| Tool | Doc ID | Code `_MACOS_INSTALL` |
|---|---|---|
| Node 20+ | `node@20` | `node@20` |
| Python 3.13+ | `python@3.13` | `python@3.13` |
| git | `git` | `git` |
| gh | `gh` | `gh` |
| Docker | `orbstack` (intent) / `docker` (code) | `docker` (known inconsistency — see D-11 note) |

### Linux apt-get — 5/5
| Tool | Doc ID | Code `_APT_INSTALL` |
|---|---|---|
| Node 20+ | `nodejs` | `nodejs` |
| Python 3.13+ | `python3.13 python3.13-venv` | `python3.13 python3.13-venv` |
| git | `git` | `git` |
| gh | `gh` | `gh` |
| Docker | `docker.io docker-compose-plugin` | `docker.io docker-compose-plugin` |

### Linux dnf — 5/5
| Tool | Doc ID | Code `_DNF_INSTALL` |
|---|---|---|
| Node 20+ | `nodejs:20/common` | `nodejs:20/common` |
| Python 3.13+ | `python3.13` | `python3.13` |
| git | `git` | `git` |
| gh | `gh` | `gh` |
| Docker | `docker docker-compose-plugin` | `docker docker-compose-plugin` |

### Windows winget — 5/5
| Tool | Doc ID | Code `_WINGET_INSTALL` |
|---|---|---|
| Node 20+ | `OpenJS.NodeJS.LTS` | `OpenJS.NodeJS.LTS` |
| Python 3.13+ | `Python.Python.3.13` | `Python.Python.3.13` |
| git | `Git.Git` | `Git.Git` |
| gh | `GitHub.cli` | `GitHub.cli` |
| Docker | `Docker.DockerDesktop` | `Docker.DockerDesktop` |

## Task Commits

Each task was committed atomically:

1. **Task 1: README.md + macos.md** - `51899ec` (docs)
2. **Task 2: linux.md + windows.md** - `95cbe46` (docs)

**Plan metadata:** (final docs commit — see below)

## Files Created/Modified

- `references/preflight/README.md` — D-13 handoff entry point; links all per-OS files; documents preflight flow, PRE-01..07 requirements, --no-docker mode
- `references/preflight/macos.md` — Homebrew install matrix (5 tools), OrbStack default (D-11), system-Python pitfall (Pitfall 2), transitive-deps caveat (Pitfall 6)
- `references/preflight/linux.md` — apt + dnf install matrices (5 tools each), ID_LIKE detection, sudo UX (Pitfall 5), cross-platform shell discipline (Pitfall 14), unsupported-distro refusal (D-09)
- `references/preflight/windows.md` — winget install matrix (5 tools), scoop fallback (D-10), PATH-refresh two-mode pattern (Pitfall 3), Docker Desktop license (Pitfall 4), nvm-windows APPDATA, choco anti-recommendation (W-06)

## Decisions Made

- D-13 honored: did NOT edit SKILL.md (byte-equivalent confirmed)
- D-11 intent documented accurately: OrbStack is the preferred macOS Docker runtime (from RESEARCH.md and docs.orbstack.dev), even though the code's `_MACOS_INSTALL["docker"]` package_id remains `"docker"` due to a test-stub constraint predating the D-11 lock. The inconsistency is documented inline in macos.md as a known v1 gap tracked for v2.
- W-03 lockstep: cross-script package-ID verification (docs vs. code) is the responsibility of /gsd-verify-phase, not this plan — both derive from the same Apr-2026-verified IDs in 02-RESEARCH.md

## Deviations from Plan

None — plan executed exactly as written. The only editorial addition was the "Code note (D-11)" callout in macos.md to accurately document the known code inconsistency between the OrbStack intent (D-11) and the actual `_MACOS_INSTALL["docker"]` package_id. This improves doc accuracy without changing any behavior.

## Known Stubs

None. All four files contain substantive content derived from verified package IDs.

## Issues Encountered

None. The files were created from verbatim content provided in the plan, verified against `scripts/preflight_check.py`'s install tables.

## W-03 Lockstep Note

Cross-script package-ID verification (docs package IDs vs. `scripts/preflight_check.py` install table entries) is enforced post-hoc by `/gsd-verify-phase`, not at plan-level. This plan and Plan 02-02 both derive from the same Apr-2026-verified IDs in `02-RESEARCH.md` / `STACK.md`, so they cannot drift if executed independently.

## User Setup Required

None — documentation only, no external service configuration required.

## Next Phase Readiness

- All four preflight reference docs are in place under `references/preflight/`
- D-13 handoff loop closed: `/osbuilder` can load `references/preflight/README.md` for the high-level narrative, then load the matching per-OS file for execution details
- Phase 2 Wave 1 complete: Plan 02-01 (test stubs), 02-02 (preflight_check.py), 02-03 (uninstall.py), 02-04 (reference docs) all shipped
- Ready for `/gsd-verify-phase 2` to run all 4 doc-grep gates + 30 unit tests

---
*Phase: 02-pre-flight-installer-cross-platform*
*Completed: 2026-04-30*
