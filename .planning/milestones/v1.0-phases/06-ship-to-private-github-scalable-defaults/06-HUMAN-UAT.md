---
status: complete
phase: 06-ship-to-private-github-scalable-defaults
source: [06-VERIFICATION.md]
started: 2026-05-01T23:00:00Z
updated: 2026-05-01T23:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Stranger clone-and-run on fresh machine
expected: Working app reachable on localhost within 5 minutes; no edits to source files required.
test: On a second machine (or clean container), clone the repo OSBuilder just created and follow README Quick Start verbatim — `cd <dir> && cp .env.example .env && pnpm install && pnpm dev`.
why_human: Requires a fresh machine + a real GitHub repo created by a build run. Structural evidence (readme-template has all required commands + idempotency marker) verified, but the 5-minute UAT bound and "stranger" condition cannot be checked programmatically.
result: pass

### 2. Live `gh repo view --json visibility` reports PRIVATE
expected: `gh repo view --json visibility` returns `{"visibility":"PRIVATE"}` after a real ship.
test: Run `gh repo create --private` on a real project dir with a live `gh` auth session and verify with `gh repo view --json visibility`.
why_human: Requires live `gh` auth and a real GitHub account. The mocked unit tests (test_ship_runs_private_create, test_auth_drift_friendly) verify structural correctness; live verification requires an authenticated session.
result: pass

### 3. Drifted gh-auth produces friendly remediation copy
expected: Stderr contains the literal `gh auth login --git-protocol https`, no Python traceback, no raw `gh` stderr.
test: With `gh` auth expired or drifted, run OSBuilder ship-step end-to-end and inspect the user-facing message.
why_human: Requires live expired-auth state. Unit test (test_auth_drift_friendly) verifies dictionary routing; a real expired-token session is needed for true confirmation.
result: pass

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
