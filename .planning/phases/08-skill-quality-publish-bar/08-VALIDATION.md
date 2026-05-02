---
phase: 8
slug: skill-quality-publish-bar
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-02
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~30 seconds (full); <5s (-x quick) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

> Populated by planner during plan generation. Each task with `<automated>` block lands here. See 08-RESEARCH.md "Validation Architecture" → "Phase Requirements → Test Map" for the canonical req-to-test mapping.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (planner fills) | | | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/check_skill_md_length.py` — QUAL-01 standalone CI lint
- [ ] `scripts/check_skill_versions.py` — QUAL-05 version-drift validator with semver tuple compare and missing-version warn-not-crash
- [ ] `.github/workflows/ci.yml` — QUAL-01 CI surface (pinned `@v6` actions, `setup-uv@v6`, `setup-python@v6`)
- [ ] `README.md` — install one-liner doc (QUAL-02), dev-team-metaphor section (QUAL-03), demo asset link (QUAL-03), `--production-ready` flag doc (SC-6)
- [ ] `examples/README.md` + `examples/<name>/SPEC.md` × 3-5 with `screenshots/` and `repo-url.txt` — QUAL-04
- [ ] `assets/demo/osbuilder-demo.gif` (+ `.cast` source) — QUAL-03 demo asset
- [ ] `references/version-policy.md` — documents the OSBuilder-local `requires:` frontmatter convention
- [ ] SKILL.md frontmatter `requires:` block (5 sub-skill minimums; verify SKILL.md stays ≤ 200 lines)
- [ ] `scripts/tests/test_check_skill_md_length.py` — Wave 0 RED stubs (≥ 2)
- [ ] `scripts/tests/test_check_skill_versions.py` — Wave 0 RED stubs (≥ 4)
- [ ] `scripts/tests/test_ci_workflow.py` — Wave 0 RED stubs (≥ 2)
- [ ] `scripts/tests/test_readme.py` — Wave 0 RED stubs (≥ 5)
- [ ] `scripts/tests/test_examples.py` — Wave 0 RED stubs (≥ 4)
- [ ] `08-HUMAN-UAT.md` — manual checklist for clean-machine one-liner E2E + demo recording

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Clean-machine `curl … \| sh` end-to-end install | QUAL-02 SC-2 | Cannot automate without locked public-repo URL and a fresh VM/container; relies on real network + real GitHub | Spin up a fresh container or VM, run the documented one-liner, verify `~/.claude/skills/osbuilder/` exists, run `/osbuilder` and confirm it loads |
| 60-second demo video recording captures end-to-end paragraph→app flow | QUAL-03 SC-3 | Recording is a manual artifact; quality is judged by humans | Record asciinema/GIF following 08-HUMAN-UAT.md script; verify <60s, no secrets visible, asset committed under `assets/demo/` |
| Example gallery apps were actually built by OSBuilder | QUAL-04 SC-4 | Each example must reflect a real OSBuilder run with real GitHub repo URL | Run OSBuilder on each example's intake brief, capture screenshots, link the produced repo URL |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
