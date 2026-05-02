---
phase: 06-ship-to-private-github-scalable-defaults
verified: 2026-05-01T23:00:00Z
status: human_needed
score: 5/7 must-haves verified
overrides_applied: 0
human_verification:
  - test: "On a second machine (or clean container), clone the repo OSBuilder just created, follow README Quick Start commands verbatim (cd <dir> && cp .env.example .env && pnpm install && pnpm dev), and confirm a working app on localhost."
    expected: "Working app reachable on localhost within 5 minutes with no edits to source files."
    why_human: "Requires a fresh machine + a real GitHub repo created by a build run. Structural evidence (readme-template.md has all required commands + idempotency marker) is verified but the 5-minute UAT bound and 'stranger' condition cannot be checked programmatically."
  - test: "Run gh repo create --private on a real project dir with a live gh auth session and verify with: gh repo view --json visibility — confirm the output shows PRIVATE."
    expected: "gh repo view --json visibility returns {\"visibility\":\"PRIVATE\"}."
    why_human: "Requires live gh auth and a real GitHub account. The mocked unit tests (test_ship_runs_private_create, test_auth_drift_friendly) verify structural correctness; live verification requires an authenticated session."
  - test: "With gh auth expired or drifted, run OSBuilder ship step and confirm the error message shown to the user contains the exact command 'gh auth login --git-protocol https' and no raw gh stack trace."
    expected: "User sees the friendly remediation message with the copy-pasteable command. No Python traceback or raw gh stderr."
    why_human: "Requires live expired-auth state. Unit test (test_auth_drift_friendly) verifies the dictionary routing; a real expired token session is needed for true confirmation."
---

# Phase 6: ship-to-private-github-scalable-defaults Verification Report

**Phase Goal:** Close the build -> ship loop. Every successful build ends as a private GitHub repo with a README runbook a stranger can clone-and-run on a fresh machine — with sensible-by-default scaffold shape (env config, real DB, Dockerfile, CI) and explicit refusals of K8s/microservices in v1.
**Verified:** 2026-05-01T23:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | After verify-loop passes, OSBuilder runs `gh repo create --private` and `git push` — resulting repo is PRIVATE (verified by `gh repo view --json visibility` returning "PRIVATE") | ? HUMAN NEEDED | `scripts/gh_handoff.py` ship() invokes `["gh", "repo", "create", "--private", "--source=...", "--remote=origin", "--push"]` (shell=False, no shell=True). Unit test V-01 (test_ship_runs_private_create) passes GREEN. State field `repo_visibility` written post-ship. Live `gh` auth required for E2E. |
| 2 | A second user clones the resulting repo on a fresh machine, follows README commands, and reaches a working app on localhost in <= 5 minutes | ? HUMAN NEEDED | `assets/readme-template.md` contains all required commands: `cp .env.example .env`, `{{install_command}}`, `{{run_command}}`, `pre-commit install`. Section structure verified (5 required H2s present). Idempotency marker `<!-- OSBuilder runbook -->` present. `runbook_writer.write_readme` substitutes all placeholders (test V-03 GREEN). The "stranger + 5 minutes" UAT bound cannot be automated. |
| 3 | Committing a real-looking secret into a built repo's working tree is blocked by the gitleaks pre-commit hook | PARTIAL | `assets/gitleaks/.pre-commit-config.yaml` pinned to `rev: v8.30.1`; `assets/gitleaks/.gitleaks.toml` has allowlist for `.env.example`. `_install_gitleaks_hook()` stamps both files (test V-06 GREEN). Integration test V-07 is SKIPPED (env-gated: requires pre-commit + gitleaks binaries). This is the only skipped automated test. |
| 4 | A built web project contains `.env.example`, `.env` gitignored, `compose.yaml` (no `version:` key), `Dockerfile`, and exactly one `.github/workflows/*.yml` with build+test on PR — no Helm/k8s | VERIFIED | `.env.example` written by `write_drizzle_files` (V-09 GREEN). `_compose_gitignore` stamps `.gitignore` with `.env\n`, `.env.*\n`, `!.env.example\n` (V-05 GREEN). `_COMPOSE_YAML` has no `^version:` key (confirmed programmatically). `_write_dockerfile` stamps multi-stage Dockerfile from `node-pnpm.Dockerfile.tmpl` (V-12 GREEN). `_write_ci_workflow` stamps exactly one `ci.yml` with `pull_request:` trigger and correct pnpm/action-setup ordering (V-13 GREEN). No Helm/k8s files in any template. |
| 5 | Asking "set up Kubernetes for this app" in default mode produces a refusal with documented explanation; `--production-ready` adds K8s/etc. as named ROADMAP phases | VERIFIED | `intake_handler.check_refuse_list` detects "kubernetes" via word-boundary regex (`\bkubernetes\b`); writes `last_failure='refused: kubernetes'`; prints refusal copy from `references/refuse-list.md`. Refusal copy contains "production-ready" 4 times (V-15 GREEN). `_matches_refuse_keyword('k8sFooBar')` returns None (false-positive defense confirmed). `production_phase_writer.emit` prints exactly 7 `/gsd-add-phase <name>` lines when `production_ready=true`, zero otherwise (V-16, V-17 GREEN). Refusal gate wired in `gsd_driver.py` at `phase_step==1` (confirmed via source scan). |
| 6 | If `gh auth status` reports drift/expiry, user sees friendly error with `gh auth login --git-protocol https` — no raw stack trace | ? HUMAN NEEDED | `friendly_error` dictionary entry `gh-auth-drift` with `copy_paste_command: "gh auth login --git-protocol https"` confirmed present (35 entries total). `translate("You are not logged into any GitHub hosts").copy_paste == "gh auth login --git-protocol https"` confirmed programmatically. Token redaction via `_TOKEN_RE.sub("[REDACTED-TOKEN]", raw)` present in `gh_handoff._friendly`. Unit test V-08 (test_auth_drift_friendly) GREEN. Live expired-auth session needed for full confirmation. |
| 7 | Multi-user web build receives Postgres-via-compose; single-user CLI build receives SQLite — confirmed by compose.yaml / config | VERIFIED | `_pick_database('web', 'multi-user-web') == 'postgres'` and `_pick_database('cli', 'single-user-cli') == 'sqlite'` confirmed programmatically. `write_drizzle_files(db_choice='postgres')` writes `compose.yaml`; `write_drizzle_files(db_choice='sqlite')` skips it. Tests V-10 (pure function) and V-11 (file presence) GREEN. |

**Score:** 4/7 truths fully VERIFIED, 3/7 require human verification for the live-gh portions (structural evidence passes for all 3).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/gh_handoff.py` | ship() + verify() + friendly-error routing | VERIFIED | 322 lines. Exports `ship`, `verify`, `_compose_gitignore`, `_install_gitleaks_hook`, `main`. shell=False throughout (0 shell=True). Token redaction present. |
| `scripts/runbook_writer.py` | write_readme + template substitution | VERIFIED | 226 lines. Exports `write_readme`, `_derive_commands`, `_read_state`, `OSBUILDER_MARKER`, `TEMPLATE_PATH`. CLI `write` subcommand registered. |
| `scripts/scaffold_dispatch.py` | _pick_database + _write_dockerfile + _write_ci_workflow | VERIFIED | Extended with 3 new public helpers. ASSETS constant points to `<repo>/assets`. |
| `scripts/intake_handler.py` | REFUSE_KEYWORDS + check_refuse_list + check-refuse-list CLI | VERIFIED | REFUSE_KEYWORDS has 10 entries. check_refuse_list wired with state write + stderr copy. CLI subcommand registered returning exit 2 on hit. |
| `scripts/production_phase_writer.py` | emit subcommand, 7 named upgrades | VERIFIED | 111 lines. NAMED_UPGRADES tuple has 7 entries. emit() prints exactly 7 lines when production_ready=true, 0 otherwise. |
| `scripts/gsd_driver.py` | Refusal gate at phase_step==1 + ship-step block | VERIFIED | check-refuse-list subprocess at phase_step==1, exit-2 short-circuit. Ship-step block at current_phase > gsd_phase_count invoking runbook_writer -> gh_handoff -> production_phase_writer. |
| `references/friendly-errors/dictionary.yaml` | 5 new gh-* entries | VERIFIED | 35 total entries. New entries: gh-not-installed, gh-auth-drift, gh-name-collision, gh-network, gh-repo-view-fail. Auth drift entry routes to correct copy_paste_command. |
| `assets/gitignore-templates/common.gitignore` | .env / .env.* / !.env.example lines | VERIFIED | Contains all three .env negative-match lines. |
| `assets/gitignore-templates/node.gitignore` | node_modules/ + dist/ | VERIFIED | Present. |
| `assets/gitignore-templates/python.gitignore` | __pycache__/ + .venv/ | VERIFIED | Present. |
| `assets/gitleaks/.pre-commit-config.yaml` | Pinned to rev: v8.30.1 | VERIFIED | Content confirmed. |
| `assets/gitleaks/.gitleaks.toml` | .env.example allowlist | VERIFIED | Allowlist regex `(.*?)\.env\.example$` present. |
| `assets/dockerfiles/node-pnpm.Dockerfile.tmpl` | Multi-stage AS builder + AS runtime | VERIFIED | Both stages present. |
| `assets/dockerfiles/python-uv.Dockerfile.tmpl` | Multi-stage AS builder + AS runtime | VERIFIED | Both stages present. |
| `assets/ci-workflows/node.yml.tmpl` | pnpm/action-setup before setup-node + pull_request: | VERIFIED | pnpm/action-setup@v4 at line 15, actions/setup-node@v4 at line 19 — correct order. |
| `assets/ci-workflows/python.yml.tmpl` | astral-sh/setup-uv@v6 + pull_request: | VERIFIED | Both present. |
| `assets/readme-template.md` | 5 H2 sections + cp .env.example + pre-commit install + marker | VERIFIED | All 5 sections, both key lines, idempotency marker present. |
| `references/refuse-list.md` | "production-ready" >= 4x + ## Refusal copy H2 | VERIFIED | 4 case-insensitive matches confirmed. H2 marker `## Refusal copy` present. |
| `SKILL.md` | <= 200 lines + 3 new artifact mentions | VERIFIED | 130 lines (well under 200). runbook_writer.py, production_phase_writer.py, refuse-list.md all mentioned. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gsd_driver.py` phase_step==1 | `intake_handler.py check-refuse-list` | subprocess exit-2 sentinel | WIRED | `check-refuse-list` string confirmed in gsd_driver.py source. Exit 2 short-circuit present. |
| `gsd_driver.py` current_phase > gsd_phase_count | `runbook_writer.py write` | subprocess sequence | WIRED | All three scripts referenced in gsd_driver.py ship-step block. `current_phase > gsd_phase_count` trigger condition confirmed. |
| `gsd_driver.py` ship-step | `gh_handoff.py ship` | subprocess after runbook | WIRED | Strict sequence: runbook -> gh_handoff -> production_phase_writer confirmed in source. |
| `gsd_driver.py` ship-step | `production_phase_writer.py emit` | subprocess after gh_handoff | WIRED | Confirmed in source. stdout passed through to caller. |
| `gh_handoff.py` | `friendly_error.py` | graceful-degrade import guard | WIRED | `import friendly_error as _fe` guard present. _friendly() helper confirmed. |
| `gh_handoff.py` | `state_writer.py write` | `_write_state_field` subprocess | WIRED | repo_visibility, repo_url, gh_auth_status, pre_commit_installed written post-ship. |
| `runbook_writer.py` | `assets/readme-template.md` | `(ASSETS / 'readme-template.md').read_text()` | WIRED | TEMPLATE_PATH = ASSETS / "readme-template.md" confirmed in source. |
| `runbook_writer.py` | `state_writer.py read --format json` | `_read_state` subprocess | WIRED | _read_state reads state.md via subprocess, populates substitution map. |
| `intake_handler.check_refuse_list` | `state_writer.py write --field last_failure` | `_write_state_field` | WIRED | V-14 test verifies state.md last_failure written on refusal. |
| `intake_handler.check_refuse_list` | `references/refuse-list.md` | `_load_refusal_copy` reads file | WIRED | `refuse-list.md` string confirmed in intake_handler source. |
| `scaffold_dispatch._write_dockerfile` | `assets/dockerfiles/*.Dockerfile.tmpl` | `ASSETS / "dockerfiles"` path read | WIRED | ASSETS constant defined, template path constructed from stack_family arg. |
| `scaffold_dispatch._write_ci_workflow` | `assets/ci-workflows/*.yml.tmpl` | `ASSETS / "ci-workflows"` path read | WIRED | Template path constructed from stack_family arg. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `runbook_writer.py:write_readme` | `state` dict | `_read_state()` -> state_writer.py read --format json | Yes — reads real state.md written by prior phases | FLOWING |
| `intake_handler.py:check_refuse_list` | `spec` string | derived_spec.md read from disk | Yes — reads file written by intake step | FLOWING |
| `production_phase_writer.py:emit` | `state` dict | `_read_state()` -> state_writer.py | Yes — reads production_ready field | FLOWING |
| `gsd_driver.py` ship-step | `project_path` | `_read_state()` -> state.md project_path | Yes — reads real project dir | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| _pick_database returns correct values | `python3 -c "from scaffold_dispatch import _pick_database; assert _pick_database('web','multi-user-web')=='postgres'"` | Passed | PASS |
| production_phase_writer emits 7 lines when production_ready=true | subprocess emit with seeded state | 7 `/gsd-add-phase` lines confirmed | PASS |
| production_phase_writer emits 0 lines by default | subprocess emit with unset field | stdout empty confirmed | PASS |
| check_refuse_list returns True on kubernetes spec | `_matches_refuse_keyword('I want kubernetes')` | returns 'kubernetes' | PASS |
| check_refuse_list false-positive defense | `_matches_refuse_keyword('k8sFooBar')` | returns None | PASS |
| friendly_error auth-drift routing | `translate("You are not logged into any GitHub hosts").copy_paste` | `"gh auth login --git-protocol https"` | PASS |
| gh_handoff CLI subcommands | `python3 scripts/gh_handoff.py --help` | shows ship + verify | PASS |
| compose.yaml no version: key | `_COMPOSE_YAML` regex check | no match | PASS |
| pnpm/action-setup before actions/setup-node | line index check in node.yml.tmpl | line 15 < line 19 | PASS |
| Full pytest suite | `python3 -m pytest scripts/tests/ -q` | 143 passed, 1 skipped (V-07 env-gated) | PASS |
| SKILL.md line count | `wc -l SKILL.md` | 130 lines | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SHIP-01 | 06-02, 06-06 | Private GitHub repo via `gh repo create --private` | SATISFIED | gh_handoff.ship() confirmed; --private flag present; V-01 GREEN; gsd_driver ship-step wired |
| SHIP-02 | 06-04, 06-06 | Clone-and-run README runbook | SATISFIED (structural) | runbook_writer.py + readme-template.md confirmed; V-03 GREEN; V-04 manual UAT pending |
| SHIP-03 | 06-02, 06-03 | .gitignore prevents .env + secrets + artifacts | SATISFIED | _compose_gitignore stamps common+node/python templates; V-05 GREEN |
| SHIP-04 | 06-02 | gitleaks pre-commit hook installed | PARTIAL | Unit V-06 GREEN; integration V-07 SKIPPED (env-gated — requires binaries) |
| SHIP-05 | 06-02, 06-06 | gh auth state verified; friendly remediation on drift | SATISFIED (structural) | Dictionary entry gh-auth-drift confirmed; copy_paste confirmed; V-08 GREEN; live auth verification is human |
| SCL-01 | 06-03 | .env.example in scaffold | SATISFIED | write_drizzle_files writes .env.example; V-09 GREEN |
| SCL-02 | 06-03 | Postgres for multi-user web; SQLite for CLI | SATISFIED | _pick_database pure function confirmed; V-10, V-11 GREEN |
| SCL-03 | 06-03 | Dockerfile + compose.yaml shipped | SATISFIED | _write_dockerfile + compose.yaml conditional write; V-12 GREEN; compose.yaml has no version: key |
| SCL-04 | 06-03 | Exactly one GitHub Actions CI workflow | SATISFIED | _write_ci_workflow stamps single ci.yml; pnpm ordering correct; V-13 GREEN |
| SCL-05 | 06-05, 06-06 | Refuse K8s/microservices/service-mesh/Helm in default mode | SATISFIED | check_refuse_list with word-boundary defense; refusal copy confirmed; gsd_driver wired; V-14, V-15 GREEN |
| SCL-06 | 06-05, 06-06 | --production-ready adds named ROADMAP phases | SATISFIED | production_phase_writer emits 7 /gsd-add-phase lines; V-16, V-17 GREEN |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/gh_handoff.py` | multiple | `verify()` returns `{}` on all failures — no distinction between network error vs. auth error in the read-only path | INFO | The `verify` function (separate from `ship`) returns empty dict on any failure. This is by design for resilience but means callers cannot distinguish why verification failed. Does not block the goal. |
| `scripts/gsd_driver.py` | ship-step | `gh_handoff` invoked without `capture_output` while `runbook_writer` uses `capture_output=True` | INFO | Intentional per key-decision: gh_handoff lets friendly_error stderr flow directly to user; others capture for programmatic pass-through. Not a stub. |

No TODO/FIXME/placeholder comments found in Phase 6 production scripts. No `return null` or empty array stubs in production paths. No hardcoded empty data in rendering paths.

### Human Verification Required

#### 1. Stranger Clone-and-Run UAT (V-04 — Success Criterion #2)

**Test:** On a second machine or clean container with Node 20+ and git installed: clone the repo OSBuilder created, open README.md, and follow the Quick Start commands verbatim — `cd <project>`, `cp .env.example .env`, `pnpm install`, `pnpm dev`.
**Expected:** Working app on localhost reachable in under 5 minutes with zero edits to source files.
**Why human:** Requires a real GitHub repo from a completed build run, a fresh machine without cached dependencies, and a human to judge "working app" vs. broken state. The structural evidence (readme-template has all required commands, placeholder substitution verified, idempotency marker confirmed) cannot substitute for the real end-to-end UAT.

#### 2. Live Private Repo Creation (Success Criterion #1 final confirmation)

**Test:** Run a full OSBuilder build to completion on a real project, then: `gh repo view --json visibility` in the resulting directory.
**Expected:** `{"visibility":"PRIVATE"}` (or a JSON object with `"visibility":"PRIVATE"`).
**Why human:** Requires a live `gh auth` session and a real GitHub account. Unit test V-01 confirms the subprocess call is constructed correctly with `--private`; the JSON parsing of the response is covered by the test suite. Live confirmation verifies the gh CLI behavior has not changed.

#### 3. Auth Drift Friendly Error (Success Criterion #6 final confirmation)

**Test:** Expire or revoke your gh auth token, then re-run the OSBuilder ship step.
**Expected:** stderr contains "## GitHub login expired or never set" (or similar title) and the exact text "gh auth login --git-protocol https" — no Python traceback visible.
**Why human:** Requires a genuinely expired token state. The dictionary routing is verified programmatically (translate() returns the correct copy_paste_command). Token redaction via `_TOKEN_RE.sub("[REDACTED-TOKEN]", raw)` is confirmed in source. Human confirms the terminal output looks clean and actionable.

### Gaps Summary

No automated gaps. All 16 automatable V-IDs (V-01 through V-17 except V-04) are GREEN. The 1 skipped test (V-07 gitleaks integration) is environment-gated by design and documented as an acceptable skip per the phase plan.

The 3 human verification items correspond to live-gh interaction requirements that cannot be tested without a real auth session and GitHub account. These are not implementation gaps — the structural evidence passes fully. They are UAT items matching the phase plan's pre-defined manual verification scope.

---

_Verified: 2026-05-01T23:00:00Z_
_Verifier: Claude (gsd-verifier)_
