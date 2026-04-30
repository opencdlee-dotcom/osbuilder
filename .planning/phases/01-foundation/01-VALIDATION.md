---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
revised: 2026-04-29 (post-checker — BLOCKER 4 + WARNING 4 fixes)
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (Python stdlib `unittest` acceptable; pytest cleaner) + ShellCheck for bash |
| **Config file** | `~/.claude/skills/osbuilder/pyproject.toml` (Wave 0 creates it) |
| **Quick run command** | `pytest scripts/tests/ -x` |
| **Full suite command** | `pytest scripts/tests/ && shellcheck scripts/bootstrap.sh install.sh` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest scripts/tests/test_<file>.py -x` (the unit test for the file just changed)
- **After every plan wave:** Run `pytest scripts/tests/ && shellcheck scripts/bootstrap.sh install.sh`
- **Before `/gsd-verify-work`:** Full pytest suite + shellcheck green + manual smoke install on fresh machine (or Docker) — phase cannot pass otherwise
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-W0-01 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f pyproject.toml && grep -q "pytest" pyproject.toml` | ❌ W0 | ⬜ pending |
| 1-W0-02 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f .gitattributes && grep -qE "^\*\.sh text eol=lf$" .gitattributes` | ❌ W0 | ⬜ pending |
| 1-W0-03 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f scripts/tests/__init__.py` | ❌ W0 | ⬜ pending |
| 1-01-01 | 02 | 1 | FOUND-01 | T-1-V5 | Reject reserved-word names in frontmatter; SKILL.md reaches install location after `bash install.sh` runs (BLOCKER 1 closure) | smoke | `bash install.sh && test -f ~/.claude/skills/osbuilder/SKILL.md && head -20 ~/.claude/skills/osbuilder/SKILL.md \| grep -E '^name: osbuilder$'` | ❌ W0 | ⬜ pending |
| 1-01-02 | 02 | 1 | FOUND-01 | T-1-V5 | Frontmatter passes Anthropic rules (name regex, description ≤1024 chars, no XML tags / reserved words) | unit | `pytest scripts/tests/test_skill_md.py::test_frontmatter_valid` | ❌ W0 | ⬜ pending |
| 1-01-03 | 02 | 1 | FOUND-02 | — | N/A | smoke | `[ "$(wc -l < SKILL.md)" -le 200 ]` | ❌ W0 | ⬜ pending |
| 1-01-04 | 02 | 1 | FOUND-02 | — | N/A | unit | `pytest scripts/tests/test_skill_md.py::test_has_references_link` | ❌ W0 | ⬜ pending |
| 1-01-05 | 02 | 1 | FOUND-01 | T-1-V5 | No `<` characters in YAML frontmatter region (BLOCKER 2 / WARNING 2: angle-bracket placeholders only allowed in body, post-frontmatter) | smoke | `[ "$(awk '/^---$/{c++; next} c==1' SKILL.md \| grep -c '<')" = "0" ]` | ❌ W0 | ⬜ pending |
| 1-01-06 | 02 | 1 | FOUND-01 + Phase-1-SC#5 | T-1-V7 | Resume Protocol references the INSTALLED state_writer.py path (BLOCKER 2) | smoke | `grep -q '~/.claude/skills/osbuilder/scripts/state_writer.py' SKILL.md` | ❌ W0 | ⬜ pending |
| 1-02-01 | 03 | 1 | FOUND-03 | T-1-V12 | One-level-deep nesting (no `..` traversal in any path); 4 dirs created | smoke | `bash install.sh && find ~/.claude/skills/osbuilder -mindepth 3 -type d \| grep -q . && exit 1 \|\| exit 0` | ❌ W0 | ⬜ pending |
| 1-03-01 | 05 | 1 | FOUND-04 | T-1-V14 | Idempotent install; never rm -rf; sudo only when apt/dnf require | manual+smoke | `docker run -it python-less-image bash bootstrap.sh && python3 --version` (manual; CI-able post-Phase-2) | ❌ W0 | ⬜ pending |
| 1-03-02 | 05 | 1 | FOUND-04 | T-1-V14 | bootstrap.ps1 syntax-valid PowerShell 5.1 | static | `pwsh -NoProfile -Command "[System.Management.Automation.PSParser]::Tokenize((Get-Content scripts/bootstrap.ps1 -Raw),[ref]\$null)"` | ❌ W0 | ⬜ pending |
| 1-03-03 | 05 | 1 | FOUND-04 | T-1-V7 | bootstrap.sh exits clean on missing-Python (no raw stack trace) | smoke | `shellcheck -s sh scripts/bootstrap.sh; echo $?` (must be 0) | ❌ W0 | ⬜ pending |
| 1-03-04 | 03 | 1 | FOUND-03 | T-1-V14 | install.sh creates 4 dirs (BLOCKER 1 / WARNING 4) | unit | `pytest scripts/tests/test_install.py::test_install_creates_four_dirs` | ❌ W0 | ⬜ pending |
| 1-03-05 | 03 | 1 | FOUND-03 | T-1-V14 | install.sh idempotent — same listing both runs (BLOCKER 1 / WARNING 4) | unit | `pytest scripts/tests/test_install.py::test_install_idempotent` | ❌ W0 | ⬜ pending |
| 1-03-06 | 02+03 | 1 | FOUND-01 + FOUND-03 | T-1-V14 | install.sh COPIES SKILL.md into install location (BLOCKER 1 closure) | unit | `pytest scripts/tests/test_install.py::test_install_copies_artifacts` | ❌ W0 | ⬜ pending |
| 1-03-07 | 03 | 1 | FOUND-03 | T-1-V12 | No nesting deeper than one level under SKILL_DIR after install (Anthropic one-level-deep rule) | unit | `pytest scripts/tests/test_install.py::test_install_no_nested_dirs` | ❌ W0 | ⬜ pending |
| 1-03-08 | 05 | 1 | FOUND-04 + Phase-1-SC#3 | T-1-BLOCKER-3 | bootstrap.sh re-execs into state_writer.py (BLOCKER 3 / ROADMAP SC#3) | smoke | `grep -q 'exec python3 "\${STATE_WRITER}" "\$@"' scripts/bootstrap.sh` | ❌ W0 | ⬜ pending |
| 1-03-09 | 05 | 1 | FOUND-04 + Phase-1-SC#3 | T-1-BLOCKER-3 | bootstrap.ps1 has two-mode re-exec (existing-Python → exec; just-installed → reopen shell) | smoke | `grep -q 'pythonAlreadyPresent' scripts/bootstrap.ps1 && grep -q 'JustInstalled' scripts/bootstrap.ps1 && grep -q '& python \$StateWriter @args' scripts/bootstrap.ps1` | ❌ W0 | ⬜ pending |
| 1-04-01 | 04 | 1 | FOUND-05 | T-1-V12 | Atomic write via os.replace — interrupted write does not corrupt existing state.md | unit | `pytest scripts/tests/test_state_writer.py::test_atomic_replace_no_partial` | ❌ W0 | ⬜ pending |
| 1-04-02 | 04 | 1 | FOUND-05 | T-1-V5 | Reject newline in `--value`; reject unknown `--field` | unit | `pytest scripts/tests/test_state_writer.py::test_input_validation` | ❌ W0 | ⬜ pending |
| 1-04-03 | 04 | 1 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_init_creates_all_fields` | ❌ W0 | ⬜ pending |
| 1-04-04 | 04 | 1 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_line_count_under_20` | ❌ W0 | ⬜ pending |
| 1-04-05 | 04 | 1 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_round_trip` | ❌ W0 | ⬜ pending |
| 1-04-06 | 04 | 1 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_validate_rejects_missing` | ❌ W0 | ⬜ pending |
| 1-04-07 | 04 | 1 | Phase-1-SC#5 | — | After simulated `/clear`, state.md round-trips `current_role`/`current_phase` | integration | `pytest scripts/tests/test_state_writer.py::test_resume_simulated_clear` | ❌ W0 | ⬜ pending |
| 1-04-08 | 04 | 1 | FOUND-05 | T-1-V12 | `--project-root` is resolved absolute path; reject `..` in field values | unit | `pytest scripts/tests/test_state_writer.py::test_path_traversal_rejected` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave Structure (post-checker, WARNING 1 fix)

After applying the checker resolutions, Phase 1 collapses to **2 waves total**:

- **Wave 0** — Test infrastructure: Plan 01 (pyproject.toml, .gitattributes, test stubs incl. test_install.py)
- **Wave 1** — All implementation in parallel (disjoint files): Plan 02 (SKILL.md), Plan 03 (install.sh + .gitkeep), Plan 04 (state_writer.py), Plan 05 (bootstrap shims)

Phase verification (post-Wave 1) asserts:
- All pytest unit tests GREEN
- `bash install.sh && test -f ~/.claude/skills/osbuilder/SKILL.md` succeeds (BLOCKER 1 closure)
- ShellCheck clean on install.sh and bootstrap.sh
- pwsh-tokenizer clean on bootstrap.ps1 (when available)

---

## Wave 0 Requirements

- [ ] `pyproject.toml` (repo root) — pytest config; declare `pythonpath = ["scripts"]`
- [ ] `.gitattributes` (repo root) — `*.sh text eol=lf`, `*.ps1 text eol=crlf`, `*.py text eol=lf` (prevents Pitfall 9 — CRLF on Windows checkout). Verified by glob regex `^\*\.sh text eol=lf$` (BLOCKER 4 — matches the file's actual content)
- [ ] `scripts/tests/__init__.py` — empty package marker
- [ ] `scripts/tests/conftest.py` — shared pytest fixtures (`tmp_project_root`, `state_md_path`, `writer`, `fake_home`)
- [ ] `scripts/tests/test_state_writer.py` — stubs for FOUND-05 (8 test functions per the verification map)
- [ ] `scripts/tests/test_skill_md.py` — stubs for FOUND-01 + FOUND-02 (frontmatter validity, line count, references link)
- [ ] `scripts/tests/test_install.py` — stubs for FOUND-03 + BLOCKER 1 (4 test functions: `test_install_creates_four_dirs`, `test_install_idempotent`, `test_install_copies_artifacts`, `test_install_no_nested_dirs`) — WARNING 4 fix
- [ ] **Framework install:** `python3 -m pip install pytest` (state_writer.py itself uses no third-party deps — pytest is dev-only)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bootstrap on a Python-less Mac/Linux/Windows machine | FOUND-04 | Auto-installer modifies system state; CI surface for this is Phase 2's preflight installer | 1) Spin up Docker image / VM without Python. 2) Run `bash bootstrap.sh` (POSIX) or `pwsh bootstrap.ps1` (Windows). 3) Verify exit 0 and `python3 --version` reports 3.13+. 4) bootstrap.sh: confirm re-exec into state_writer.py fires when state_writer.py is at install location (BLOCKER 3). 5) bootstrap.ps1 just-installed branch: should exit 0 with "reopen shell" message after winget install (Pitfall 5 + BLOCKER 3 Mode B). 6) bootstrap.ps1 existing-Python branch: should `& python $StateWriter @args` when Python was already on PATH (BLOCKER 3 Mode A). |
| Skill install via `install.sh` on a fresh machine | FOUND-01, FOUND-03 | Modifies `~/.claude/skills/`; full automation deferred to Phase 8 (`install.sh` polish). The `test_install.py` suite covers most of this in CI now (WARNING 4) — manual is just the final smoke. | 1) On a machine without `~/.claude/skills/osbuilder/`, run the skill's `install.sh`. 2) Verify `~/.claude/skills/osbuilder/SKILL.md` exists (BLOCKER 1 closure). 3) Verify all four sub-directories present. 4) Verify `wc -l ~/.claude/skills/osbuilder/SKILL.md ≤ 200`. 5) Verify `~/.claude/skills/osbuilder/scripts/state_writer.py` exists and is +x. |
| Compaction-resume mechanic — after simulated `/clear`, SKILL.md routes user back to last `current_role`/`current_phase` | Phase 1 Success Criterion #5 | The "/clear" simulation involves invoking SKILL.md from a fresh Claude session — automated test would require harness scaffolding worth its own phase. Round-trip read/write of state.md fields is automated (1-04-07). | 1) `python3 ~/.claude/skills/osbuilder/scripts/state_writer.py write --field goal --value "test" --project-root <path>`. 2) Re-invoke OSBuilder skill. 3) Verify the resume protocol output mentions `current_role`/`current_phase` fields read from state.md. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] All 4 BLOCKERS closed:
  - BLOCKER 1 (install.sh copies artifacts): rows 1-03-04..07 + 1-01-01 phase smoke
  - BLOCKER 2 (Resume Protocol installed path + frontmatter no-`<`): rows 1-01-05, 1-01-06
  - BLOCKER 3 (bootstrap re-exec into state_writer.py): rows 1-03-08, 1-03-09
  - BLOCKER 4 (.gitattributes regex aligned with glob): row 1-W0-02
- [ ] All 4 WARNINGS resolved:
  - WARNING 1 (wave restructuring): waves collapsed to 0+1; depends_on cleaned up across plans
  - WARNING 2 (frontmatter `<` fragility): row 1-01-05 awk acceptance gate
  - WARNING 3 (atomic test monkeypatch): in-process patching documented in Plan 01 + Plan 04
  - WARNING 4 (install.sh idempotency automated): rows 1-03-04..07 (test_install.py)
- [ ] `nyquist_compliant: true` set in frontmatter (after Wave 0 lands)

**Approval:** pending
