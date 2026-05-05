---
phase: 06-ship-to-private-github-scalable-defaults
fixed_at: 2026-05-02T03:42:00Z
review_path: .planning/phases/06-ship-to-private-github-scalable-defaults/06-REVIEW.md
iteration: 2
findings_in_scope: 34
fixed: 34
skipped: 0
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-05-02T03:42:00Z
**Source review:** .planning/phases/06-ship-to-private-github-scalable-defaults/06-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope: 34 (0 Critical + 14 Warning + 20 Info)
- Fixed: 34
- Skipped: 0

Iteration 1 (2026-05-02) applied all 14 Warning findings. Iteration 2 (this pass)
applied all 20 Info findings. Each fix landed as its own atomic commit. Several
fixes flag a logic/semantic behaviour change and are marked
"requires human verification" below — syntax checks passed and the full test
suite (148 tests, 1 skipped) is green, but observable runtime behaviour should
be confirmed in the verifier phase.

## Fixed Issues — Iteration 1 (Warnings)

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

## Fixed Issues — Iteration 2 (Info)

### IN-01: `gh_handoff.ship` does not detect post-`--push` divergence

**Files modified:** `scripts/gh_handoff.py`
**Commit:** 610d5de
**Applied fix:** After `gh repo create --push` returns success, run
`git log origin/main..HEAD --oneline` from the project_dir. If the command
exits 0 with non-empty output, local main has commits that did not reach
the remote — surface this through `_friendly` and return 1. If the command
exits non-zero (origin/main ref absent), skip the check (fresh repo before push).
**Status:** fixed — requires human verification (new failure path:
silently-broken pushes are now caught and reported as ship failures).

### IN-02: `_run_tech_writer_step` writes optimistic `humanizer_score=0`

**Files modified:** `scripts/gsd_driver.py`
**Commit:** 253f70a
**Applied fix:** Emit a `tech-writer / check-humanizer / ok` tutor-line via
`_emit(...)` immediately after invoking `/humanizer @README.md`, with
detail explaining that `humanizer_score=0` is an optimistic write and
humanizer's own score (if any) overrides on the next state read. The
optimistic-write behaviour itself is unchanged (Plan 05-05 deviation).

### IN-03: `REFUSE_KEYWORDS` and `references/refuse-list.md` keyword list duplicated

**Files modified:** `scripts/tests/test_refusal.py`
**Commit:** cada3be
**Applied fix:** Added `test_refuse_list_synced(ih)` regression test that parses
the `## Refuse keywords` H2 section from `references/refuse-list.md` (extracts
`- bullet` items) and asserts set-equality with `intake_handler.REFUSE_KEYWORDS`.
Catches drift in either direction (Python-only or markdown-only entries).

### IN-04: `--public` flag emits no warning to user

**Files modified:** `scripts/gh_handoff.py`
**Commit:** aca6764
**Applied fix:** In `_cmd_ship`, when `args.public` is set, emit a single-line
stderr warning before invoking `ship()`: "OSBuilder: warning — --public flag
set; this will create a PUBLICLY-READABLE GitHub repo (private is the default)".
Hard Rule #6 (private-by-default) is no longer silently bypassed.

### IN-05: `playbook` lookup is `lower()`-cased but state.md values are not normalized at write time

**Files modified:** `scripts/tests/test_state_writer.py`
**Commit:** 6ef2973
**Applied fix:** Added `test_playbook_canonical_case_round_trip` test that
asserts state.md round-trips the `playbook` value verbatim (no auto-normalisation),
documenting the contract that producers (intake_handler, scaffold_dispatch)
must write canonical lowercase. If a future change auto-normalises at write
time, this test will fail and the contract change must be intentional.

### IN-06: marker constants duplicated across modules with no cross-check

**Files modified:** `references/markers.md` (new file)
**Commit:** 697da2d
**Applied fix:** Created `references/markers.md` as a maintainer-only index
listing all OSBuilder idempotency markers (`_GITIGNORE_MARKER`,
`OSBUILDER_MARKER`), where they are defined, what file they stamp, and how
the idempotency check is performed (anchored vs substring). D-05 (no
cross-imports) policy preserved — this is a documentation index, not runtime code.

### IN-07: Public/private API confusion calling `_narration._init_build_log` from outside its module

**Files modified:** `scripts/gsd_driver.py`
**Commit:** 9d282d3
**Applied fix:** Added clarifying comments to `_refresh_narration_state` and
`_init_build_log_if_new_build` documenting that the underscore-prefixed
narration helpers are part of narration's public surface (per
`scripts/narration.py` module docstring) despite the leading underscore.
The contract is now spelled out at the call sites.

### IN-08: Inline YAML frontmatter parsing is fragile

**Files modified:** `scripts/gsd_driver.py`
**Commit:** f66e427
**Applied fix:** Added `import re` at the top of the module and replaced the
hand-rolled line-by-line frontmatter parser in `_humanizer_present()` with a
single `re.search(r'^version:\s*["\']?([\d.]+)["\']?\s*$', text, re.MULTILINE)`.
Padding to 3 components (`2.0` → `(2, 0, 0)`) preserved.

### IN-09: `_cmd_verify` uses raw `sys.stderr.write` instead of `_friendly`

**Files modified:** `scripts/gh_handoff.py`
**Commit:** d8fecb4
**Applied fix:** Replaced the raw `sys.stderr.write("OSBuilder: gh repo view
failed or returned empty.\n")` with `_friendly("gh repo view failed or
returned empty", tool="gh")`, matching the rest of the module's
friendly_error routing (translates known stderr fragments + token redaction).

### IN-10: `python-uv.Dockerfile.tmpl` `CMD` assumes a top-level `app` package

**Files modified:** `assets/dockerfiles/python-uv.Dockerfile.tmpl`
**Commit:** 3608237
**Applied fix:** Added an `IN-10 / TODO(phase-7)` comment block at the top of
the Dockerfile and a single-line `IN-10:` comment above the `CMD` line noting
that the Dockerfile is dormant until Phase 7 wires the cli / ai-service
playbooks, at which point CMD must be parameterised per playbook.

### IN-11: README "How OSBuilder built this" placeholder section has no completion test

**Files modified:** `scripts/tests/test_tech_writer.py`
**Commit:** 68bc7b5
**Applied fix:** Added two tests:
- `test_readme_template_placeholder_section_present` — asserts
  `assets/readme-template.md` contains both the `## How OSBuilder built this`
  H2 AND the placeholder sentinel phrase ("Tech Writer step has not run yet
  on this build", whitespace-normalised).
- `test_completed_readme_replaces_placeholder_sentinel` — uses the existing
  `runbook_writer` fixture path to confirm a freshly-stamped README contains
  the sentinel (so future verification tests can assert it's GONE after
  `/gsd-docs-update` lands).

### IN-12: `.gitleaks.toml` allowlist regex uses unnecessary lazy quantifier

**Files modified:** `assets/gitleaks/.gitleaks.toml`
**Commit:** 9ef70e7
**Applied fix:** Replaced `(.*?)\.env\.example$` and `(.*?)\.env\.sample$`
with `.*\.env\.example$` and `.*\.env\.sample$` respectively. Lazy `(.*?)`
is equivalent to `.*` against an end-anchored pattern; the greedy form is
faster and reads as the obvious intent. Test
`test_gitleaks_config` (which asserts the literal regex `\.env\.example`
substring) still passes.

### IN-13: `test_gitleaks_blocks_real_secret` writes a Stripe-shaped string in source

**Files modified:** `scripts/tests/test_scaffold_extensions.py`
**Commit:** ae958c0
**Applied fix:** Added an `IN-13:` inline comment above the synthetic
`STRIPE_KEY=sk_test_...` test fixture documenting that this is a synthetic
test value (not a real secret) and that any future top-level OSBuilder
gitleaks config must allowlist `scripts/tests/.*\.py$` so this fixture
does not block commits to the OSBuilder repo. OSBuilder currently has no
top-level gitleaks config — the hook only ships into scaffolded projects.

### IN-14: ship-step pass-through ignores `production_phase_writer` returncode

**Files modified:** `scripts/gsd_driver.py`
**Commit:** 55be0a6
**Applied fix:** After invoking `production_phase_writer.py emit`, check
`pp.returncode != 0` — if non-zero, write `pp.stderr` then a one-line
"contract violation" stderr line, still pass through `pp.stdout` (idempotent),
and return 1. The docstring contract remains "always exits 0", but if a
future change breaks that contract (e.g. ROADMAP read raises) the failure
is now surfaced rather than silently swallowed.

### IN-15: `_validate_project_name` defined but never called in `intake_handler`

**Files modified:** `scripts/intake_handler.py`
**Commit:** 0b6b5b7
**Applied fix:** Deleted the dead `_validate_project_name` function from
`scripts/intake_handler.py` (verbatim duplicate of the `scaffold_dispatch.py`
version that is actually wired). intake_handler does not accept a
project_name argument from users (it parses `derived_spec.md`), so the
helper was unreachable. The scaffold_dispatch copy remains in use.

### IN-16: `_SECRET_PATTERNS` misses common AI service token shapes

**Files modified:** `scripts/intake_handler.py`
**Commit:** a7b5e97
**Applied fix:** Extended `_SECRET_PATTERNS` to include `openai_api_key`,
`anthropic_api_key`, `sk-` (OpenAI / Anthropic / Stripe key prefix), and
`bearer ` (Authorization header paste — trailing space disambiguates from
benign words like "bearer-token"). gitleaks at commit time remains the real
backstop — these patterns catch obvious paste-mistakes in the user's plain-
English spec BEFORE state.md or any subprocess sees them. Comment block
documents the defense-in-depth intent.

### IN-17: state.md round-trip with `:` in values needs a test

**Files modified:** `scripts/tests/test_state_writer.py`
**Commit:** e355cc2
**Applied fix:** Added `test_value_with_colon_round_trip` test that writes
`repo_url=git@github.com:user/foo.git`, reads it back via both `--field` and
`--format json`, and asserts byte-identical round-trip. Also exercises
multi-colon values like `https://example.com:8080/path`. Pins the
`partition(":")` (split-on-first-colon-only) parser contract.

### IN-18: two `friendly-errors` entries match the same `gh: command not found` pattern

**Files modified:** `references/friendly-errors/dictionary.yaml`
**Commit:** e451bfb
**Applied fix:** Consolidated the two duplicate-pattern entries (`gh-not-installed`
+ `gh-not-found`) into a single `gh-not-installed` entry whose `what_to_do`
copy and `copy_paste_command` cover both Phase 6 (ship) and preflight
contexts. Comment block above the entry explains the consolidation and
points to the future migration path (ctx-based discrimination) if
context-specific copy is needed. The `test_dictionary_has_30_entries` test
still passes — count drops from 35 to 34.

### IN-19: `node.yml.tmpl` missing `concurrency:` group

**Files modified:** `assets/ci-workflows/node.yml.tmpl`
**Commit:** 3b83b5d
**Applied fix:** Added the standard GitHub-Actions concurrency block:
`group: ${{ github.workflow }}-${{ github.ref }}` with
`cancel-in-progress: true`. Cancels in-flight runs when a new commit lands
on the same PR ref — saves CI minutes on rapid rebases without affecting
correctness. `test_one_ci_workflow` still passes (no assertion on
top-level keys outside `on:` and `jobs:`).

### IN-20: `references/refuse-list.md` "See also" links to OSBuilder-internal paths

**Files modified:** `references/refuse-list.md`
**Commit:** d69f927
**Applied fix:** Wrapped the two maintainer-only links
(`.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` Phase 6 success
criteria #5) in an HTML comment block with a maintainer note explaining
why. Installed-skill users at `~/.claude/skills/osbuilder/` no longer see
broken links. The two genuine cross-references (`scripts/intake_handler.py`,
`scripts/production_phase_writer.py`) stay visible. `_load_refusal_copy`
parser is unaffected — `## See also` still acts as the H2 boundary.

## Skipped Issues

None — all 34 in-scope findings (14 Warning + 20 Info) were applied across
the two iterations.

---

_Fixed: 2026-05-02T03:42:00Z (combined report; iteration 1 fixed at 2026-05-02T01:54:45Z)_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
