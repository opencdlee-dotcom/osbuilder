---
status: partial
phase: 05-common-person-ux-polish
source: [05-VERIFICATION.md]
started: 2026-05-01T07:45:00Z
updated: 2026-05-01T07:45:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. End-to-end build narration in default mode
expected: Running OSBuilder against a sample paragraph emits dev-team banners ([PM], [ARCHITECT], [FRONTEND], [BACKEND], [DEVOPS], [QA], [REVIEWER], [TECH-WRITER]) for every phase, with '> In plain English: ...' tutor lines after each successful step, and zero raw subprocess output / stack traces / errno codes / framework jargon visible to the user.
result: [pending]

### 2. Top-30 errors translate to friendly messages
expected: Inducing a representative sample of dictionary errors at runtime (pnpm absent, state.md unwritable, port-in-use, etc.) produces FriendlyMessage output of the form "here's what broke and here's what to do" with a working copy_paste_command — not a stack trace or errno code.
result: [pending]

### 3. Generated README plain-English quality (humanizer audit)
expected: Running an actual /gsd-docs-update + /humanizer @README.md cycle on a built project yields a README that contains "## How OSBuilder built this" naming all 8 roles, reads naturally to a non-developer, and humanizer reports zero 'critical' AI-pattern findings.
result: [pending]

### 4. --advanced flag exposes stack choices
expected: Running the same intake paragraph in --advanced mode shows technology names (Next.js, Postgres, Drizzle, etc.) in derived_spec.md and surfaces deploy-target prompts, while default mode hides them. Mode is set via state.md mode=advanced; flag wiring is a future entry-point CLI.
result: [pending]

### 5. Friendly-error dictionary expansion path is followable
expected: A new contributor reads references/friendly-errors/README.md and successfully adds a 31st entry to dictionary.yaml — the format-version gate accepts the new entry, ORDER-MATTERS guidance is clear, tests pass without code changes.
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
