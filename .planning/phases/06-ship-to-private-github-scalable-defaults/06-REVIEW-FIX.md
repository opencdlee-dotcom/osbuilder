---
phase: 06-ship-to-private-github-scalable-defaults
fixed_at: 2026-05-02T01:54:45Z
review_path: .planning/phases/06-ship-to-private-github-scalable-defaults/06-REVIEW.md
iteration: 1
findings_in_scope: 14
fixed: 14
skipped: 0
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-05-02T01:54:45Z
**Source review:** .planning/phases/06-ship-to-private-github-scalable-defaults/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 14 (all Warning; 0 Critical; 20 Info skipped per scope policy)
- Fixed: 14
- Skipped: 0

All Critical+Warning findings from the Phase 6 standard-depth review were applied.
Each fix landed as its own atomic commit. Several fixes flag a logic/semantic
behaviour change and are marked "requires human verification" below — syntax checks
passed, but observable runtime behaviour should be confirmed in the verifier phase.

## Fixed Issues

### WR-01: `_friendly` token-redaction regex misses `github_pat_*` fine-grained tokens

**Files modified:** `scripts/gh_handoff.py`
**Commit:** 6364161
**Applied fix:** Replaced `_TOKEN_RE` with a unified pattern covering classic
`ghp_` (PAT), `ghs_` (server), `gho_` (OAuth), `ghu_` (user-to-server), `ghr_`
(refresh) and `github_pat_*` (fine-grained PAT) tokens. Comment block above the
regex documents each prefix.

### WR-02: empty `repo_url` from `gh repo view` silently persisted to state.md

**Files modified:** `scripts/gh_handoff.py`
**Commit:** 652f8b8
**Applied fix:** After `gh repo view` returns, validate that the sanitised
`ssh_url` starts with one of `git@`, `https://`, or `ssh://`. If not, route the
raw value through `_friendly` and return 1 instead of writing an empty/malformed
`repo_url` to `state.md`. Also flips persistence to use the already-sanitised
local variable.
**Status:** fixed — requires human verification (semantic behaviour change in
the ship pipeline; the new `return 1` path interrupts the previous silent-write
behaviour).

### WR-03: `runbook_writer.write_readme` placeholder canary fires on benign user input

**Files modified:** `scripts/runbook_writer.py`
**Commit:** ed3e563
**Applied fix:** Replaced the bare `"{{" in composed` substring check with a
known-placeholder set check (the keys of the local `subs` dict). User goals
containing `{{` (Jinja-like syntax in a project description) no longer trip
the canary, but unsubstituted OSBuilder placeholders still raise `SystemExit`
with a clear message naming the offending placeholders.

### WR-04: refuse-keyword priority ordering is undocumented

**Files modified:** `scripts/intake_handler.py`
**Commit:** 00be75c
**Applied fix:** Added a multi-line comment block above `REFUSE_KEYWORDS`
explaining the "first-in-tuple wins" matching invariant and the "broader/more
severe terms above narrower ones" ordering rule, with the helm/kubernetes case
called out as the canonical example.

### WR-05: `gsd_driver` ship-step uses `basename(project_path)` rather than the full path

**Files modified:** `scripts/gsd_driver.py`
**Commit:** 17a3717
**Applied fix:** Resolved `project_dir` and asserted that
`project_dir.parent.resolve() == project_root.resolve()` before invoking the
runbook/ship/production-phase child scripts. If `project_path` lives outside
`project_root` the ship step now writes a clear stderr message and returns 1
rather than silently shipping a different directory than scaffold built.
**Status:** fixed — requires human verification (semantic behaviour change:
previously-silent path divergence is now a hard failure).

### WR-06: `_compose_gitignore` idempotency marker is substring-matched

**Files modified:** `scripts/gh_handoff.py`
**Commit:** 282729d
**Applied fix:** Switched `_GITIGNORE_MARKER in existing` to
`existing.startswith(_GITIGNORE_MARKER)`. Comment above the check explains the
hand-edited-comment edge case the anchor protects against.

### WR-07: `gh repo create --source=<absolute path>` runs without explicit `cwd`

**Files modified:** `scripts/gh_handoff.py`
**Commit:** 2d89d56
**Applied fix:** Added `cwd=str(project_dir)` to the `gh repo create`
subprocess invocation, matching the surrounding git invocations. Comment block
explains the defensive-symmetry rationale.

### WR-08: `_humanizer_present` swallows all parse errors and fails open

**Files modified:** `scripts/gsd_driver.py`
**Commit:** 899e09e
**Applied fix:** Capture the original exception in a local `parse_error`
variable and emit a `tech-writer / version-check / fail` tutor-line via
`_emit(...)` before returning the documented fail-open `True`. The behaviour
remains fail-open per design — only the user-visible signalling improves.

### WR-09: `_load_refusal_copy` marker is brittle to leading-newline assumptions

**Files modified:** `scripts/intake_handler.py`
**Commit:** 4d9cfc9
**Applied fix:** Replaced `text.find("\n## Refusal copy")` with
`re.search(r"(?:^|\n)## Refusal copy", text)`. The H2 is now matched whether it
is the very first line of the file or preceded by other content. Inline
backtick references inside blockquotes are still excluded because they are not
at column 0.

### WR-10: `parse_paragraph` always sets `app_type="web"` regardless of paragraph content

**Files modified:** `scripts/intake_handler.py`
**Commit:** e907b88
**Applied fix:** Added a `WR-10 / TODO(phase-7)` block to the `parse_paragraph`
docstring noting that v1 always sets `app_type="web"` because only the web
playbook ships, and that Phase 7 should infer `app_type` from text once the
cli / ai-service / desktop / hub-platform playbooks land.

### WR-11: `production_phase_writer.emit` does not de-duplicate against existing ROADMAP phases

**Files modified:** `scripts/production_phase_writer.py`
**Commit:** ffbb309
**Applied fix:** Added `_existing_roadmap_phases(project_root)` helper that
reads `.planning/ROADMAP.md` (if present) and returns the set of `NAMED_UPGRADES`
already mentioned (lower-cased substring match). `emit()` now skips upgrades in
that set. Falls back to emitting all 7 if the roadmap is missing/unreadable;
gsd-add-phase's own idempotency remains the backstop.
**Status:** fixed — requires human verification (substring-based dedupe could
miss when gsd-add-phase normalises titles in unexpected ways).

### WR-12: `scaffold_dispatch._cmd_scaffold` swallows `state.md` write failure

**Files modified:** `scripts/scaffold_dispatch.py`
**Commit:** 2f4a1ca
**Applied fix:** Caught the exception type instead of bare `pass`. Now writes a
`OSBuilder: warning — failed to record project_path in state.md (...)` line to
stderr including the exception type and message, and notes that downstream
ship/runbook may need `--project-path` supplied manually. Behaviour remains
non-fatal (no exit code change) per the existing contract.

### WR-13: `runbook_writer._derive_commands` generic fallback writes a broken README

**Files modified:** `scripts/runbook_writer.py`
**Commit:** 1d0a180
**Applied fix:** Replaced the `"see README"` placeholder fallback with
`raise SystemExit(...)`. Unknown playbooks now fail with a clear message
naming the offending value and listing the supported set
(`web`, `cli`, `ai-service`). Confirmed no existing tests depend on the prior
fallback strings.
**Status:** fixed — requires human verification (semantic behaviour change:
previously-silent broken README is now a hard failure that aborts the ship
pipeline at the runbook step).

### WR-14: `gsd_driver._build_escalation_output` ignores its `state` parameter

**Files modified:** `scripts/gsd_driver.py`
**Commit:** f701fd3
**Applied fix:** Added `# noqa: ARG001 — reserved` to the function signature
and a docstring paragraph explaining that the parameter is intentionally kept
for future branching on retry context (e.g. `last_failure` category) without
a caller-side signature change.

## Skipped Issues

None — all 14 in-scope warnings were applied.

---

_Fixed: 2026-05-02T01:54:45Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
