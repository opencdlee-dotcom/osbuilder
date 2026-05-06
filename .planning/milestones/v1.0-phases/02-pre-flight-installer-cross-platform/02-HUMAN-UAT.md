---
status: blocked
phase: 02-pre-flight-installer-cross-platform
source: [02-VERIFICATION.md]
started: 2026-04-30T15:07:30Z
updated: 2026-05-05T00:00:00Z
---

## Current Test

[testing complete — both scenarios require hardware not available to the runner]

## Tests

### 1. Fresh-Mac End-to-End Smoke Test (SC #6)
expected: On a fresh macOS machine (real network, real Homebrew), `python3 scripts/preflight_check.py install` detects all missing tools, shows dry-run preview, installs everything with a single y/n confirmation, and completes in ≤ 3 minutes total. All five tools (Node 20+, Python 3.13+, git, gh, Docker) should be present after the run.
result: blocked — runner machine is not fresh and is configured `no_docker: true` in `~/.osbuilder/preflight-config.json`. Partial evidence: `python3 scripts/preflight_check.py check` reports node 25.7.0 / python 3.13.13 / git 2.50.1 / gh 2.90.0 all present and version_ok=True; `python3 scripts/preflight_check.py install --dry-run` returns "Nothing to install" in <1s. Cannot exercise the missing-tool install path without uninstalling tools on the user's working machine. Needs a real fresh macOS box.

### 2. Windows --no-docker Flow (SC #5)
expected: On a real Windows 11 machine, `python3 scripts/preflight_check.py install --no-docker` completes the full install flow without any Docker prompt, winget PATH refresh works (tools usable after reopening shell), and the SQLite-only path is unblocked.
result: blocked — no Windows 11 hardware available to the runner (platform is darwin/macOS).

## Summary

total: 2
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 2

## Gaps

- Both tests require hardware the runner does not have. Re-run by a human on (a) a fresh macOS machine and (b) a real Windows 11 machine with winget.
