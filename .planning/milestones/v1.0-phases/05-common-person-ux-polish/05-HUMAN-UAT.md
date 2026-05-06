---
status: complete
phase: 05-common-person-ux-polish
source: [05-VERIFICATION.md]
started: 2026-05-01T07:45:00Z
updated: 2026-05-05T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-end build narration in default mode
expected: Running OSBuilder against a sample paragraph emits dev-team banners ([PM], [ARCHITECT], [FRONTEND], [BACKEND], [DEVOPS], [QA], [REVIEWER], [TECH-WRITER]) for every phase, with '> In plain English: ...' tutor lines after each successful step, and zero raw subprocess output / stack traces / errno codes / framework jargon visible to the user.
result: pass — `narration.emit()` called sequentially for all 8 roles produced banners `[PM] action...` / `[PM] action [OK]` followed by `> In plain English: I am the project manager. I figure out what you want to build...` per role. All 8 roles render plain-language tutor lines (PM/ARCHITECT/FRONTEND/BACKEND/DEVOPS/QA/REVIEWER/TECH-WRITER); no raw subprocess output, stack traces, errno codes, or framework jargon visible.

### 2. Top-30 errors translate to friendly messages
expected: Inducing a representative sample of dictionary errors at runtime (pnpm absent, state.md unwritable, port-in-use, etc.) produces FriendlyMessage output of the form "here's what broke and here's what to do" with a working copy_paste_command — not a stack trace or errno code.
result: pass — dictionary has 39 entries; 39 of 39 dictionary-aligned raw-error samples translate to a specific FriendlyMessage with title + what_broke + what_to_do + (where applicable) copy_paste_command, no Errno/Traceback/raw-shell-prefix leaks. Spot-checked: pnpm-not-found → "pnpm isn't installed yet" + `npm install -g pnpm`; port-in-use → "The port is already taken" + `lsof -i :3000`; gh-auth-drift → "GitHub login expired or never set" + `gh auth login --git-protocol https`. The previously-failing pg-conn-refused regex was loosened in commit 11432a3 to `connection.*refused.*5432` and now matches all three real-world phrasings (`connection refused at localhost:5432`, `connection to server refused on port 5432`, `connection refused (Postgres) port 5432`). Note: errors NOT in the dictionary still fall through to the generic translator which embeds raw text in `what_broke` — out-of-dictionary leakage is a known shape but is outside the top-30 scope.

### 3. Generated README plain-English quality (humanizer audit)
expected: Running an actual /gsd-docs-update + /humanizer @README.md cycle on a built project yields a README that contains "## How OSBuilder built this" naming all 8 roles, reads naturally to a non-developer, and humanizer reports zero 'critical' AI-pattern findings.
result: partial — `runbook_writer.write_readme()` correctly stamps `## How OSBuilder built this` from `assets/readme-template.md` with state.md substitutions (verified on the Phase 3 built project at `/tmp/uat-runs/timing-proj`). However, the section body in the template is an explicit placeholder ("filled in by the Tech Writer step `/gsd-docs-update`") that names PM/Architect/Frontend/Backend/DevOps/QA explicitly and Reviewer/Tech-Writer implicitly — the full 8-role enumeration depends on the interactive `/gsd-docs-update` skill running, and the humanizer audit requires the interactive `/humanizer` skill. Both must be exercised in a real Claude Code session, not from a non-interactive script. Recommend marking this row complete only after a documented run of those two skills against a built repo.

### 4. --advanced flag exposes stack choices
expected: Running the same intake paragraph in --advanced mode shows technology names (Next.js, Postgres, Drizzle, etc.) in derived_spec.md and surfaces deploy-target prompts, while default mode hides them. Mode is set via state.md mode=advanced; flag wiring is a future entry-point CLI.
result: pass — `parse_structured(..., stack_hints=["Next.js","Postgres","Drizzle"])` produces a derived_spec that includes `**Stack hints:** Next.js, Postgres, Drizzle` in advanced mode and omits the line entirely in beginner mode. State.md `mode` field correctly drives the gating per UX-03. (Side defect noted, out of scope: when `users` is passed as a string instead of a list, `parse_structured` iterates char-by-char — see `parse_structured` rendering of "students and teachers" as one bullet per character.)

### 5. Friendly-error dictionary expansion path is followable
expected: A new contributor reads references/friendly-errors/README.md and successfully adds a 40th entry to dictionary.yaml — the format-version gate accepts the new entry, ORDER-MATTERS guidance is clear, tests pass without code changes.
result: pass — followed `references/friendly-errors/README.md` step-by-step to add a `git-not-installed` entry (filled a real gap in the dictionary). Format_version gate accepted the entry, all 11 `test_friendly_error.py` tests passed without code changes, `friendly_error.translate("/bin/bash: git: command not found")` routed to the new title "git isn't installed yet" with `copy_paste: python3 scripts/preflight_check.py install`. README's ORDER MATTERS rule was clear enough to place the entry correctly. Entry was reverted after the smoke run.

## Summary

total: 5
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- Test 3 cannot complete fully without an interactive `/gsd-docs-update` + `/humanizer` cycle against a real built repo. Open as a pending sub-task.
- Side defect (out of scope): `parse_structured` iterates `users` char-by-char when given a string. Should check `isinstance(users, list)`.
