---
status: pending
phase: 08-skill-quality-publish-bar
source: [08-VERIFICATION.md, 08-URL-LOCK.md]
started:
updated:
---

## Current Test

[pending — runner has not started]

## Tests

### 1. Install one-liner end-to-end on a fresh container (QUAL-02 SC-2)
expected: `curl -fsSL https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh | sh` on a clean Docker `ubuntu:latest` lands `~/.claude/skills/osbuilder/SKILL.md` and `/osbuilder` succeeds in a Claude Code session that has never installed an OSBuilder skill before.
test: `docker run --rm -it ubuntu:latest bash -c 'apt-get update && apt-get install -y curl python3 && curl -fsSL https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh | sh && cat ~/.claude/skills/osbuilder/SKILL.md | head -5'`
why_human: Requires the published public-repo URL to be live + a fresh container with no prior Claude Code skill state. Cannot automate without provisioning a clean VM.
result: <pending>

### 2. 60-second demo records an unedited end-to-end build (QUAL-03 SC-3)
expected: Demo (assets/demo/osbuilder-demo.gif and the .cast source) shows paragraph → derived_spec → scaffold → verify → private GitHub URL with no cuts hiding friction (Pitfall 6). Total runtime ≤ 60 seconds; no secrets visible (gh token, .env, ssh key).
test: Play back assets/demo/osbuilder-demo.gif. Confirm: (a) every phase visible at the same speed it ran, (b) no cut "voice-over saying what's about to happen", (c) final frame shows a real GitHub repo URL (private or public mirror), (d) no on-screen secrets.
why_human: Subjective UX honesty check — humans judge whether the demo is faithful to the real experience.
result: <pending>

### 3. README dev-team metaphor reads as plain English to a non-developer (QUAL-03)
expected: Non-developer reader can describe what each of the 8 roles does after reading the README's "How OSBuilder Works" section once, without re-reading.
test: Hand README.md to a non-developer; ask them to summarize what "Architect" and "QA" do in their own words; check answer matches the documented narration.
why_human: Common-person UX metric is comprehension by a fresh reader, not keyword presence (the latter is automated in test_readme.py).
result: <pending>

### 4. Examples gallery apps were actually built by OSBuilder (QUAL-04 SC-4)
expected: Each example in `examples/` reflects a real OSBuilder build: SPEC.md original paragraph traces back to a real run; screenshots match the running app; repo-url.txt resolves to a real (private or public-mirror) GitHub repo.
test: For each `examples/<name>/`: open SPEC.md → re-run OSBuilder against the documented paragraph → confirm the inferred playbook matches → open repo-url.txt → confirm the URL is reachable (or NOT_PUBLISHED placeholder is documented in `examples/README.md`).
why_human: Each example must be a real build, not aspirational filler. Subjective verification.
result: <pending>

### 5. Version-drift validator real-world first-session UX (QUAL-05 SC-5)
expected: On a developer's machine where one of (gsd, brainiac, predator, code-tester, problem-solver) is below the minimum declared in SKILL.md `requires:`, first `/osbuilder` invocation that session prints a friendly upgrade message and refuses to proceed (or, for missing-version sub-skills like gsd/predator on 2026-05-02, warns and proceeds — per Pitfall 2 policy).
test: `rm -f ~/.osbuilder/last_check.txt`; manually downgrade a sub-skill (e.g., `cd ~/.claude/skills/brainiac && git checkout v5.0.0`); run `/osbuilder`; confirm the friendly error appears with the exact upgrade command. Restore the sub-skill afterwards.
why_human: Real-world first-session entry path requires a Claude Code session, not just a unit test (which covers the validator logic in isolation).
result: <pending>

## Notes for the human runner

- Run tests in any order; tests 1-5 are independent.
- Test 1 (clean-machine one-liner) requires `08-URL-LOCK.md` to have a real URL (not `<TBD>`). If the URL was deferred at the 08-01 Task 0 checkpoint, mark this row `result: BLOCKED — URL not locked` and document the unblocker.
- Test 2 (demo): if any secrets are visible, redo the recording in a clean shell with throwaway gh login.
- Mark `result: passed` / `result: failed: <description>` per row. Update `status: in-progress` while running; `status: complete` when all 5 done.
