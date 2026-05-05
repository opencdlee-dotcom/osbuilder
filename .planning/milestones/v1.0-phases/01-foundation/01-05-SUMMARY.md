# Plan 01-05 Summary — bootstrap shims (cross-platform Python install + re-exec)

**Status:** ✓ Complete
**Requirements covered:** FOUND-04
**Commit:** `99af455`
**Static checks:** `/bin/sh -n bootstrap.sh` clean; PowerShell tokenizer pending Windows machine

## Deliverables

| File | Platform | Purpose |
|------|----------|---------|
| `scripts/bootstrap.sh` | macOS, Linux | POSIX shell shim — installs Python 3 if missing, re-execs into state_writer.py |
| `scripts/bootstrap.ps1` | Windows 10/11 (PowerShell 5.1+) | PowerShell shim — installs Python via winget, two-mode dispatch for PATH-refresh gotcha |

## bootstrap.sh Logic

1. Detect OS via `uname -s` (Darwin / Linux / other)
2. If `python3` already on PATH, skip install
3. Else install:
   - macOS: `brew install python@3.13` (errors if Homebrew missing)
   - Linux: `sudo apt-get install python3 python3-pip` OR `sudo dnf install python3 python3-pip`
   - Other: clean error with manual-install guidance
4. Re-exec into installed `state_writer.py` (closes Phase 1 SC #3): `exec python3 "${STATE_WRITER}" "$@"`

## bootstrap.ps1 Logic (Two-Mode — BLOCKER 3 closure)

Captures `$pythonAlreadyPresent` flag BEFORE any installer runs. Uses winget
(primary on Win10+/11) to install Python 3.13 if missing.

Two-mode dispatch at end-of-script:

| Mode | Trigger | Action |
|------|---------|--------|
| Just-installed | `$JustInstalled = $true` (winget just ran) | Exit 0 with "Reopen your shell..." message — winget PATH-refresh requires new shell (Pitfall 5) |
| Existing-Python | `$pythonAlreadyPresent = $true` AND state_writer present | `& python $StateWriter @args` — re-exec in same shell |
| No state-writer | Neither + no installed state_writer.py | Exit 0 with "Bootstrap complete..." message |

## Cross-Platform Notes

- `.gitattributes` enforces LF on `*.sh`, CRLF on `*.ps1` so a Windows checkout
  doesn't break bootstrap.sh (Pitfall 9 mitigation, established in Wave 0)
- bootstrap.sh uses `set -eu` (no -o pipefail since /bin/sh dash doesn't support it)
- bootstrap.ps1 uses `$ErrorActionPreference = "Stop"` so any cmdlet failure halts execution

## Verification (grep markers)

| Check | Result |
|-------|--------|
| `grep 'exec python3 "${STATE_WRITER}" "$@"' bootstrap.sh` | ✓ |
| `grep -c 'pythonAlreadyPresent' bootstrap.ps1` | 2 |
| `grep -c 'JustInstalled' bootstrap.ps1` | 3 |
| `grep -c '& python $StateWriter @args' bootstrap.ps1` | 1 |
| `/bin/sh -n bootstrap.sh` | clean |

## Self-Check: PASSED

- [x] bootstrap.sh has correct re-exec block (`exec python3 "${STATE_WRITER}" "$@"`)
- [x] bootstrap.ps1 captures pythonAlreadyPresent before winget runs
- [x] bootstrap.ps1 has two-mode dispatch (`$JustInstalled` and existing-Python paths both present)
- [x] bootstrap.ps1 invokes installed state_writer.py via `& python $StateWriter @args`
- [x] `/bin/sh -n bootstrap.sh` parses cleanly (POSIX-portable)
- [x] No bashisms (uses `[ ... ]` not `[[ ... ]]`, no arrays)

## Manual smoke test (deferred to Phase 2 CI)

The full Python-less-machine smoke (`docker run -it python-less-image bash bootstrap.sh && python3 --version`)
is documented in `01-VALIDATION.md` row 1-03-01 as `manual+smoke` because Phase 2's
preflight installer phase will add the Docker-based CI harness for cross-platform testing.
