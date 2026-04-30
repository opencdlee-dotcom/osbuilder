---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
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
| **Full suite command** | `pytest scripts/tests/ && shellcheck scripts/bootstrap.sh scripts/install.sh` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest scripts/tests/test_<file>.py -x` (the unit test for the file just changed)
- **After every plan wave:** Run `pytest scripts/tests/ && shellcheck scripts/bootstrap.sh scripts/install.sh`
- **Before `/gsd-verify-work`:** Full pytest suite + shellcheck green + manual smoke install on fresh machine (or Docker) — phase cannot pass otherwise
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-W0-01 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f pyproject.toml && grep -q "pytest" pyproject.toml` | ❌ W0 | ⬜ pending |
| 1-W0-02 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f .gitattributes && grep -q "bootstrap.sh text eol=lf" .gitattributes` | ❌ W0 | ⬜ pending |
| 1-W0-03 | W0 | 0 | infra | — | N/A | Wave 0 | `test -f scripts/tests/__init__.py` | ❌ W0 | ⬜ pending |
| 1-01-01 | 01 | 1 | FOUND-01 | T-1-V5 | Reject reserved-word names in frontmatter | smoke | `test -d ~/.claude/skills/osbuilder && head -20 ~/.claude/skills/osbuilder/SKILL.md \| grep -E '^name: osbuilder$'` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | FOUND-01 | T-1-V5 | Frontmatter passes Anthropic rules (name regex, description ≤1024 chars, no XML tags / reserved words) | unit | `pytest scripts/tests/test_skill_md.py::test_frontmatter_valid` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | FOUND-02 | — | N/A | smoke | `[ "$(wc -l < ~/.claude/skills/osbuilder/SKILL.md)" -le 200 ]` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | FOUND-02 | — | N/A | unit | `pytest scripts/tests/test_skill_md.py::test_has_references_link` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | FOUND-03 | T-1-V12 | One-level-deep nesting (no `..` traversal in any path) | smoke | `find ~/.claude/skills/osbuilder/{references,scripts,assets,examples} -mindepth 2 -type d \| grep -q . && exit 1 \|\| exit 0` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | FOUND-04 | T-1-V14 | Idempotent install; never rm -rf; sudo only when apt/dnf require | manual+smoke | `docker run -it python-less-image bash bootstrap.sh && python3 --version` (manual; CI-able post-Phase-2) | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | FOUND-04 | T-1-V14 | bootstrap.ps1 syntax-valid PowerShell 5.1 | static | `pwsh -NoProfile -Command "[System.Management.Automation.PSParser]::Tokenize((Get-Content bootstrap.ps1 -Raw),[ref]\$null)"` | ❌ W0 | ⬜ pending |
| 1-03-03 | 03 | 2 | FOUND-04 | T-1-V7 | bootstrap.sh exits clean on missing-Python (no raw stack trace) | smoke | `shellcheck scripts/bootstrap.sh; echo $?` (must be 0) | ❌ W0 | ⬜ pending |
| 1-04-01 | 04 | 2 | FOUND-05 | T-1-V12 | Atomic write via os.replace — interrupted write does not corrupt existing state.md | unit | `pytest scripts/tests/test_state_writer.py::test_atomic_replace_no_partial` | ❌ W0 | ⬜ pending |
| 1-04-02 | 04 | 2 | FOUND-05 | T-1-V5 | Reject newline in `--value`; reject unknown `--field` | unit | `pytest scripts/tests/test_state_writer.py::test_input_validation` | ❌ W0 | ⬜ pending |
| 1-04-03 | 04 | 2 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_init_creates_all_fields` | ❌ W0 | ⬜ pending |
| 1-04-04 | 04 | 2 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_line_count_under_20` | ❌ W0 | ⬜ pending |
| 1-04-05 | 04 | 2 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_round_trip` | ❌ W0 | ⬜ pending |
| 1-04-06 | 04 | 2 | FOUND-05 | — | N/A | unit | `pytest scripts/tests/test_state_writer.py::test_validate_rejects_missing` | ❌ W0 | ⬜ pending |
| 1-04-07 | 04 | 2 | Phase-1-SC#5 | — | After simulated `/clear`, state.md round-trips `current_role`/`current_phase` | integration | `pytest scripts/tests/test_state_writer.py::test_resume_simulated_clear` | ❌ W0 | ⬜ pending |
| 1-04-08 | 04 | 2 | FOUND-05 | T-1-V12 | `--project-root` is resolved absolute path; reject `..` in field values | unit | `pytest scripts/tests/test_state_writer.py::test_path_traversal_rejected` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `~/.claude/skills/osbuilder/pyproject.toml` — pytest config; declare `pythonpath = ["scripts"]`
- [ ] `~/.claude/skills/osbuilder/.gitattributes` — `*.sh text eol=lf`, `*.ps1 text eol=crlf`, `*.py text eol=lf` (prevents Pitfall 9 — CRLF on Windows checkout)
- [ ] `~/.claude/skills/osbuilder/scripts/tests/__init__.py` — empty package marker
- [ ] `~/.claude/skills/osbuilder/scripts/tests/conftest.py` — shared pytest fixtures (tmp project root, fake skill dir)
- [ ] `~/.claude/skills/osbuilder/scripts/tests/test_state_writer.py` — stubs for FOUND-05 (8 test functions per the verification map)
- [ ] `~/.claude/skills/osbuilder/scripts/tests/test_skill_md.py` — stubs for FOUND-01 + FOUND-02 (frontmatter validity, line count, references link)
- [ ] `~/.claude/skills/osbuilder/scripts/tests/test_install.sh` — bash smoke test wrapper for FOUND-01/03 (or absorb into pytest with subprocess)
- [ ] **Framework install:** `python3 -m pip install pytest` (state_writer.py itself uses no third-party deps — pytest is dev-only)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bootstrap on a Python-less Mac/Linux/Windows machine | FOUND-04 | Auto-installer modifies system state; CI surface for this is Phase 2's preflight installer | 1) Spin up Docker image / VM without Python. 2) Run `bash bootstrap.sh` (POSIX) or `pwsh bootstrap.ps1` (Windows). 3) Verify exit 0 and `python3 --version` reports 3.13+. 4) Windows-only: bootstrap.ps1 should exit 0 with "reopen shell" message after winget install (PATH-refresh gotcha). |
| Skill install via `install.sh` on a fresh machine | FOUND-01, FOUND-03 | Modifies `~/.claude/skills/`; full automation deferred to Phase 8 (`install.sh` polish) | 1) On a machine without `~/.claude/skills/osbuilder/`, run the skill's `install.sh`. 2) Verify `~/.claude/skills/osbuilder/SKILL.md` exists. 3) Verify all four sub-directories present. 4) Verify `wc -l SKILL.md ≤ 200`. |
| Compaction-resume mechanic — after simulated `/clear`, SKILL.md routes user back to last `current_role`/`current_phase` | Phase 1 Success Criterion #5 | The "/clear" simulation involves invoking SKILL.md from a fresh Claude session — automated test would require harness scaffolding worth its own phase. Round-trip read/write of state.md fields is automated (1-04-07). | 1) `python3 scripts/state_writer.py write --goal "test" --current_role "PM" --current_phase "1"`. 2) Re-invoke OSBuilder skill. 3) Verify the resume protocol output mentions `current_role: PM` and `current_phase: 1`. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter (after Wave 0 lands)

**Approval:** pending
