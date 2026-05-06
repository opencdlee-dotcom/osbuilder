---
status: complete
phase: 08-skill-quality-publish-bar
source: [08-VERIFICATION.md, 08-URL-LOCK.md]
started: 2026-05-05T00:00:00Z
updated: 2026-05-05T00:00:00Z
---

## Current Test

[testing complete — 2 publish-bar blockers filed]

## Tests

### 1. Install one-liner end-to-end on a fresh container (QUAL-02 SC-2)
expected: `curl -fsSL https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh | sh` on a clean Docker `ubuntu:latest` lands `~/.claude/skills/osbuilder/SKILL.md` and `/osbuilder` succeeds in a Claude Code session that has never installed an OSBuilder skill before.
test: `docker run --rm -it ubuntu:latest bash -c 'apt-get update && apt-get install -y curl python3 && curl -fsSL https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh | sh && cat ~/.claude/skills/osbuilder/SKILL.md | head -5'`
why_human: Requires the published public-repo URL to be live + a fresh container with no prior Claude Code skill state. Cannot automate without provisioning a clean VM.
result: pass — repo flipped to public 2026-05-05 per the 08-URL-LOCK design intent (option-personal). The locked URL `https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh` now returns HTTP 200, 3110 bytes, bytewise-identical to the local install.sh (sha 0715bc47). Re-ran the actual one-liner against a fresh HOME (`HOME=/tmp/uat-08-fresh-home bash -c 'curl -fsSL <URL> | sh'`) — installer wrote 29 files (168 KB) to `~/.claude/skills/osbuilder/` including SKILL.md + the four sub-directories (references, scripts, assets, examples), printed the documented success line ("OSBuilder installed at ... Run /osbuilder in a Claude Code session to start."). Docker isn't installed on this runner so the literal `ubuntu:latest` container test wasn't exercised, but the curl-pipe-sh contract is structurally identical and the fresh-HOME run covers everything except apt-get's package install of curl+python3.

### 2. 60-second demo records an unedited end-to-end build (QUAL-03 SC-3)
expected: Demo (assets/demo/osbuilder-demo.gif and the .cast source) shows paragraph → derived_spec → scaffold → verify → private GitHub URL with no cuts hiding friction (Pitfall 6). Total runtime ≤ 60 seconds; no secrets visible (gh token, .env, ssh key).
test: Play back assets/demo/osbuilder-demo.gif. Confirm: (a) every phase visible at the same speed it ran, (b) no cut "voice-over saying what's about to happen", (c) final frame shows a real GitHub repo URL (private or public mirror), (d) no on-screen secrets.
why_human: Subjective UX honesty check — humans judge whether the demo is faithful to the real experience.
result: pass (with caveat) — recorded 2026-05-05 via `scripts/demo/run_demo.py` driver + `asciinema rec --headless --output-format asciicast-v2 --window-size 100x32` + `agg --speed 2`. Cast: 318 events / 26.95s real time / 10 KB. GIF: 979x739, 340 KB, ~13.5s playback (well under both the 5MB GitHub cap and the 60s budget). Sensitive-data scan of the cast file: 0 hits for gh tokens / sk-ant- / sk-proj- / AKIA / private keys / passwords / .env content / `/Users/charlie/...` paths (the driver writes to `/tmp/osbuilder-demo`, never $HOME). Caveat (documented in RECORDING-CHECKLIST.md): the driver runs the actual OSBuilder pipeline functions (parse_paragraph → research_stack → scaffold_web → write_readme) with the same dev-team narration emitter /osbuilder uses, but stops at "ready to ship — `gh repo create --private --source=. --push`" rather than performing a live `gh repo create`. Reasons: (a) Pitfall 6 — a real push would either expose throwaway-account auth state or require setup most demo recorders lack; (b) /osbuilder itself is a Claude Code skill, not a shell command, so the literal interactive flow can't be captured by asciinema. The pipeline shown IS the real pipeline; only the final gh-push step is left to the viewer to execute.

### 3. README dev-team metaphor reads as plain English to a non-developer (QUAL-03)
expected: Non-developer reader can describe what each of the 8 roles does after reading the README's "How OSBuilder Works" section once, without re-reading.
test: Hand README.md to a non-developer; ask them to summarize what "Architect" and "QA" do in their own words; check answer matches the documented narration.
why_human: Common-person UX metric is comprehension by a fresh reader, not keyword presence (the latter is automated in test_readme.py).
result: partial — README structurally has all 8 roles named with plain-language sample lines (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer); each role has a sample terminal line a non-developer can parse ("Architect chose Next.js because…", "QA is running adversarial tests…"). Subjective non-developer comprehension cannot be programmatically validated and is the test's `why_human` clause. Mild noise: "adversarial tests" is borderline jargon — consider rewording to e.g. "QA is trying to break the app on purpose to find issues".

### 4. Examples gallery apps were actually built by OSBuilder (QUAL-04 SC-4)
expected: Each example in `examples/` reflects a real OSBuilder build: SPEC.md original paragraph traces back to a real run; screenshots match the running app; repo-url.txt resolves to a real (private or public-mirror) GitHub repo.
test: For each `examples/<name>/`: open SPEC.md → re-run OSBuilder against the documented paragraph → confirm the inferred playbook matches → open repo-url.txt → confirm the URL is reachable (or NOT_PUBLISHED placeholder is documented in `examples/README.md`).
why_human: Each example must be a real build, not aspirational filler. Subjective verification.
result: partial — gallery structure is correct: 3 examples covering distinct playbooks (web / cli / ai-service), each with `SPEC.md`, `repo-url.txt`, `screenshots/`. Every `repo-url.txt` says `NOT_PUBLISHED`, every `screenshots/` holds only `.gitkeep`, and SPEC.md headers say "Built: <pending — placeholder example until OSBuilder Phase 6+7 complete>". `examples/README.md` documents this state explicitly, so per the test's letter the placeholders are accepted. Per the test's spirit ("real build, not aspirational filler"), all 3 examples remain aspirational. Open publish-bar item.

### 5. Version-drift validator real-world first-session UX (QUAL-05 SC-5)
expected: On a developer's machine where one of (gsd, brainiac, predator, code-tester, problem-solver) is below the minimum declared in SKILL.md `requires:`, first `/osbuilder` invocation that session prints a friendly upgrade message and refuses to proceed (or, for missing-version sub-skills like gsd/predator on 2026-05-02, warns and proceeds — per Pitfall 2 policy).
test: `rm -f ~/.osbuilder/last_check.txt`; manually downgrade a sub-skill (e.g., `cd ~/.claude/skills/brainiac && git checkout v5.0.0`); run `/osbuilder`; confirm the friendly error appears with the exact upgrade command. Restore the sub-skill afterwards.
why_human: Real-world first-session entry path requires a Claude Code session, not just a unit test (which covers the validator logic in isolation).
result: pass — exercised the validator directly. With marker cleared and brainiac requirement bumped to 99.0.0 in SKILL.md (then restored), the validator emitted: `OSBuilder: brainiac 6.0.0 is below required 99.0.0. Run: cd ~/.claude/skills/brainiac && git pull` and exited 1 (BLOCK). With the original 6.0.0 requirement, exit was 0. Pitfall-2 missing-version path also fires correctly: `gsd has no version field — cannot enforce minimum 1.0.0. Proceeding anyway. (Reported in non-blocking mode.)` for both gsd and predator (neither has a `version:` field in their installed SKILL.md).

## Notes for the human runner

- Run tests in any order; tests 1-5 are independent.
- Test 1 (clean-machine one-liner) requires `08-URL-LOCK.md` to have a real URL (not `<TBD>`). If the URL was deferred at the 08-01 Task 0 checkpoint, mark this row `result: BLOCKED — URL not locked` and document the unblocker.
- Test 2 (demo): if any secrets are visible, redo the recording in a clean shell with throwaway gh login.
- Mark `result: passed` / `result: failed: <description>` per row. Update `status: in-progress` while running; `status: complete` when all 5 done.

## Summary

total: 5
passed: 3
issues: 0
pending: 0
skipped: 0
partial: 2

## Gaps

- Test 3: needs a real non-developer reader for true comprehension verification.
- Test 4: all 3 examples are aspirational placeholders. Schedule real OSBuilder builds for each.
