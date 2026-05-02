---
status: issues_found
phase: 06-ship-to-private-github-scalable-defaults
depth: standard
files_reviewed: 28
diff_base: f75c85f1b67b22819eb2084e0cf58a431b7fd0b1
findings:
  critical: 0
  warning: 14
  info: 20
  total: 34
---

# Phase 6 Code Review

Standard-depth review of 28 files changed during Phase 6 (ship-to-private-github + scalable defaults). No critical issues. 14 warnings (mostly defensive-programming, validation, and asymmetric error-handling). 20 info-level observations (consistency, dead code, future-phase TODOs).

## Critical Issues

None. No SQL injection, command injection, hardcoded production secrets, or auth bypass vectors found. Subprocess calls are uniformly `shell=False` with list-form `argv`. Token redaction (`_TOKEN_RE`) is applied before any stderr write in `gh_handoff._friendly`. Path-traversal validation is consistent across `_resolve_project_root` helpers and `state_writer._check_value_safe`.

---

## Warnings

### WR-01: `_friendly` token-redaction regex misses `github_pat_*` fine-grained tokens

- **File:** scripts/gh_handoff.py:31
- **Issue:** `_TOKEN_RE = re.compile(r"gh[ps]_[A-Za-z0-9_]{20,}")` redacts classic `ghp_` (PAT) and `ghs_` (server) tokens but not GitHub fine-grained PATs (`github_pat_*`). T-06-02-03 cites secret-redaction in `gh` stderr — partial mitigation only.
- **Fix:** `_TOKEN_RE = re.compile(r"(?:gh[opsu]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{22,})")` (also covers `gho_` OAuth and `ghu_` user-to-server).

### WR-02: empty `repo_url` from `gh repo view` silently persisted to state.md

- **File:** scripts/gh_handoff.py:236-244
- **Issue:** Step 5 only validates `visibility`. A malformed `gh repo view` response with `sshUrl=""` writes `repo_url=""`, breaking downstream `git clone {{repo_url}}` substitution in the runbook.
- **Fix:** Validate `ssh_url.startswith(("git@", "https://", "ssh://"))` before `_write_state_field("repo_url", ...)`.

### WR-03: `runbook_writer.write_readme` placeholder canary fires on benign user input

- **File:** scripts/runbook_writer.py:168-172
- **Issue:** The "leftover `{{`" canary throws `SystemExit` for any `{{` post-substitution. A user goal containing `{{` (e.g. Jinja-like syntax) crashes the runbook step.
- **Fix:** Check only the known-placeholder set: `leftover = [p for p in known_placeholders if p in composed]`.

### WR-04: refuse-keyword priority ordering is undocumented

- **File:** scripts/intake_handler.py:113-129
- **Issue:** Loop returns first keyword in tuple order, not first-occurring in spec. So a spec with both `helm` and `kubernetes` always reports `kubernetes`. Intentional ("most-severe-first") but undocumented.
- **Fix:** Add a comment explaining the ordering invariant at line 38.

### WR-05: `gsd_driver` ship-step uses `basename(project_path)` rather than the full path

- **File:** scripts/gsd_driver.py:525-535
- **Issue:** When `project_path` is `/absolute/somewhere/myapp` and `project_root` is unrelated, ship operates on `project_root / "myapp"` (an empty/missing dir). gh repo create then runs against a different directory than scaffold did.
- **Fix:** Assert `Path(project_path).parent == project_root` before invoking child scripts, or pass the absolute path directly.

### WR-06: `_compose_gitignore` idempotency marker is substring-matched

- **File:** scripts/gh_handoff.py:112-117
- **Issue:** `if _GITIGNORE_MARKER in existing` — a hand-edited `.gitignore` that quotes the marker text in a comment skips a needed rewrite. Low risk because writes are atomic.
- **Fix (optional):** Anchor with `existing.startswith(_GITIGNORE_MARKER)`.

### WR-07: `gh repo create --source=<absolute path>` runs without explicit `cwd`

- **File:** scripts/gh_handoff.py:208-221
- **Issue:** `cwd=str(project_dir)` is omitted on this single call while every surrounding `git` invocation pins it. Defensive symmetry would prevent silent breakage if `gh`'s `--source` semantics change.
- **Fix:** Add `cwd=str(project_dir)` to the `gh repo create` invocation.

### WR-08: `_humanizer_present` swallows all parse errors and fails open

- **File:** scripts/gsd_driver.py:295-297
- **Issue:** Bare `except Exception: pass` then `return True` — even a `PermissionError` reading `humanizer/SKILL.md` is treated as "present, version unparseable." Per design (fail-open), but at minimum should emit a tutor-line so the user sees the unverifiable state.
- **Fix:** `_emit("tech-writer", "version-check", "fail", detail=...)` before `return True`.

### WR-09: `_load_refusal_copy` marker is brittle to leading-newline assumptions

- **File:** scripts/intake_handler.py:101-110
- **Issue:** `text.find("\n## Refusal copy")` returns `-1` if the H2 is the very first line of the file (no preceding newline). Today's `references/refuse-list.md` is safe (5 prior H2s) but the regression is silent.
- **Fix:** Match `(?:^|\n)## Refusal copy` via `re.search`, or lock the H1+blank prefix with a test.

### WR-10: `parse_paragraph` always sets `app_type="web"` regardless of paragraph content

- **File:** scripts/intake_handler.py:245-259
- **Issue:** A paragraph saying "Build me a CLI to rename files" produces `app_type=web` and triggers `create-next-app`. Asymmetric with `parse_structured`, which respects an explicit `app_type`. v1 ships only the web playbook so this is latent; will surface in Phase 7.
- **Fix:** Add a `# TODO(phase-7): infer app_type from text` comment, or simple keyword-match inference.

### WR-11: `production_phase_writer.emit` does not de-duplicate against existing ROADMAP phases

- **File:** scripts/production_phase_writer.py:68-78
- **Issue:** Always prints all 7 `/gsd-add-phase` lines when `production_ready=true`. Re-running on a project that already added some upgrades will emit duplicate phase requests, depending on `gsd-add-phase`'s own idempotency.
- **Fix:** Read `.planning/ROADMAP.md` and skip already-present upgrade names, or document the single-shot invariant.

### WR-12: `scaffold_dispatch._cmd_scaffold` swallows `state.md` write failure

- **File:** scripts/scaffold_dispatch.py:283-291
- **Issue:** `except (OSError, subprocess.CalledProcessError): pass` after the subprocess that records `project_path`. If state.md is read-only or the field allowlist rejects the value, downstream ship/runbook see empty `project_path` and fail with a confusing error.
- **Fix:** Emit a stderr warning so the user sees the silent persistence failure.

### WR-13: `runbook_writer._derive_commands` generic fallback writes a broken README

- **File:** scripts/runbook_writer.py:113-119 + scripts/runbook_writer.py:168-172
- **Issue:** When playbook is unrecognized, returns `{"install_command": "see README", ...}`. The post-substitution README has a Quick Start that says `cp .env.example .env && see README && see README` — runs but does nothing useful, and the canary doesn't catch it (no `{{`).
- **Fix:** Refuse to write a runbook with no commands — raise `SystemExit` for unknown playbooks.

### WR-14: `gsd_driver._build_escalation_output` ignores its `state` parameter

- **File:** scripts/gsd_driver.py:183-189
- **Issue:** Function signature is `def _build_escalation_output(state: dict) -> str` but body returns a constant. Either remove the parameter or mark it reserved.
- **Fix:** `def _build_escalation_output(state: dict) -> str:  # noqa: ARG001 — reserved`.

---

## Info

### IN-01: `gh_handoff.ship` does not detect post-`--push` divergence
scripts/gh_handoff.py:208-221 — If `gh repo create --push` creates the repo but the push portion fails (network drop, hook reject), `gh repo view` still reports `visibility=PRIVATE`. Detect via `git log origin/main..HEAD` after the call.

### IN-02: `_run_tech_writer_step` writes optimistic `humanizer_score=0`
scripts/gsd_driver.py:374-380 — Documented design (Plan 05-05 deviation), but a reader between optimistic write and actual humanizer execution sees `0`. Add a tutor-line caveat.

### IN-03: `REFUSE_KEYWORDS` and `references/refuse-list.md` keyword list duplicated
scripts/intake_handler.py:38-49 + references/refuse-list.md:21-30 — No test enforces the mirror. Add `test_refuse_list_synced()`.

### IN-04: `--public` flag emits no warning to user
scripts/gh_handoff.py:300-302 — Hard Rule #6 says private-by-default; the public path should warn before creating a publicly-readable repo.

### IN-05: `playbook` lookup is `lower()`-cased but state.md values are not normalized at write time
scripts/runbook_writer.py:91 — Defensive but inconsistent. Add a state.md integrity test that enforces canonical case.

### IN-06: marker constants duplicated across modules with no cross-check
scripts/gh_handoff.py:28 + scripts/runbook_writer.py:33 — D-05 policy (no cross-imports) is acceptable; consider a `references/markers.md` index for maintainers.

### IN-07: Public/private API confusion calling `_narration._init_build_log` from outside its module
scripts/gsd_driver.py:256, 239 — Promote to a public name in `narration.py` or document the dependency.

### IN-08: Inline YAML frontmatter parsing is fragile
scripts/gsd_driver.py:281-294 — Use `re.search(r'^version:\s*["\']?([\d.]+)["\']?', text, re.MULTILINE)` to avoid the line-by-line parser.

### IN-09: `_cmd_verify` uses raw `sys.stderr.write` instead of `_friendly`
scripts/gh_handoff.py:282-283 — Inconsistent with the rest of the module's friendly_error routing.

### IN-10: `python-uv.Dockerfile.tmpl` `CMD` assumes a top-level `app` package
assets/dockerfiles/python-uv.Dockerfile.tmpl:19 — Currently dormant (only node-pnpm path is wired); will need parameterization in Phase 7.

### IN-11: README "How OSBuilder built this" placeholder section has no completion test
assets/readme-template.md:59-67 — Soft contract that `/gsd-docs-update` replaces this section. Add a verification test.

### IN-12: `.gitleaks.toml` allowlist regex uses unnecessary lazy quantifier
assets/gitleaks/.gitleaks.toml:11-14 — `(.*?)\.env\.example$` ≡ `.*\.env\.example$` against an end-anchor.

### IN-13: `test_gitleaks_blocks_real_secret` writes a Stripe-shaped string in source
scripts/tests/test_scaffold_extensions.py:102 — If OSBuilder itself is gitleaks-scanned, the test file may be flagged. Confirm `scripts/tests/` is allowlisted.

### IN-14: ship-step pass-through ignores `production_phase_writer` returncode
scripts/gsd_driver.py:567-569 — Trusts the docstring contract that pp always exits 0; either assert or strengthen the docstring.

### IN-15: `_validate_project_name` defined but never called in `intake_handler`
scripts/intake_handler.py:174-181 — Dead code (verbatim duplicate of the `scaffold_dispatch` version). Wire it in or delete.

### IN-16: `_SECRET_PATTERNS` misses common AI service token shapes
scripts/intake_handler.py:34 — Add `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `sk-`, `Bearer `. gitleaks at commit time is the real backstop, but defense-in-depth helps.

### IN-17: state.md round-trip with `:` in values needs a test
scripts/state_writer.py:115-124 — `partition(":")` splits on the first colon only. `repo_url=git@github.com:user/foo.git` round-trips correctly, but lacks a regression test.

### IN-18: two `friendly-errors` entries match the same `gh: command not found` pattern
references/friendly-errors/dictionary.yaml:90-108 — `gh-not-installed` (Phase 6) and `gh-not-found` (prior). First-match-wins makes this functional but creates maintenance debt.

### IN-19: `node.yml.tmpl` missing `concurrency:` group
assets/ci-workflows/node.yml.tmpl — Standard practice for `pull_request` workflows; adds quality-of-life for downstream apps.

### IN-20: `references/refuse-list.md` "See also" links to OSBuilder-internal paths
references/refuse-list.md:54-59 — Links `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` are 404s for installed-skill users at `~/.claude/skills/osbuilder/`. Strip or wrap in a maintainers-only block at install time.

---

## Summary

- **Files reviewed:** 28
- **Critical:** 0
- **Warning:** 14
- **Info:** 20
- **Total:** 34

**Highest-priority fixes (recommended for Phase 6 close):**
1. WR-01 (token redaction misses `github_pat_*`) — 1-line regex fix.
2. WR-02 (empty `repo_url` silently persisted) — adds 3 lines of validation.
3. WR-05 (`project_path` / `project_root` divergence) — adds 1 invariant check in `gsd_driver`.
4. WR-13 (generic fallback writes broken README) — refuse on unknown playbook.

**Lower-priority but worth tracking:** WR-04 (refuse-list ordering doc), WR-08 (humanizer-version exception logging), WR-11 (production_phase_writer dedup), WR-14 (`_build_escalation_output` dead parameter).

Phase 6 implementation is solid: subprocess invocations are uniformly safe, idempotency is well-designed (gitignore marker, runbook marker, `git remote get-url origin` check, README marker), and the refusal gate cleanly separates the gate (exit code 2 sentinel) from the orchestrator. Asset templates carry source attribution and verification dates.
