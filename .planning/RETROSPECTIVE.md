# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Publish-Ready

**Shipped:** 2026-05-05
**Phases:** 8 | **Plans:** 45 | **Commits:** 226 (across 7 days, 2026-04-29 → 2026-05-05)

### What Was Built

- Claude Code skill at `~/.claude/skills/osbuilder/` — orchestrator pattern with SKILL.md (136/200 lines) routing to `references/` playbooks and `scripts/` helpers
- Cross-platform pre-flight installer (`preflight_check.py`, 595 lines, pure stdlib) with transactional rollback, AST-verified read-only `render_preview()`, version-manager refusal, per-OS package matrices for brew / apt / dnf / winget
- Intake → research → scaffold loop for 4 playbooks (web, ai-service, cli, desktop) + hub-platform: deterministic-scaffolder-first; vendored `professor-snapshot/` for hub-platform
- GSD handoff orchestrator (`gsd_driver.py`, 678 lines) with 4-class failure taxonomy, 3-reflection cap (Aider's empirically-validated limit), exponential backoff, slopsquatting gate via `registry_verify.py`
- Common-person UX: 39-entry friendly-error dictionary with `format_version: "1.0"` gate; 8 dev-team role briefs driving `[ROLE]` banner + `> In plain English` tutor lines; beginner-mode default with zero hits for 9 forbidden tech tokens
- Ship-to-private-GitHub flow: `gh repo create --private` with token redaction; `runbook_writer.py` clone-and-run README from template; gitleaks pre-commit hook v8.30.1; refuse-list with word-boundary regex
- Publish-bar surface: `check_skill_md_length.py` + `check_skill_versions.py`; `requires:` block declaring 5 sub-skill minimums; CI workflow with pinned `@v6` actions; install one-liner; 3-example gallery (web/cli/ai-service)

### What Worked

- **Wave-0-RED-stubs-first cadence:** Every phase landed its full test inventory in plan 01 before any production code in plans 02+. Tests served as the falsifiable VERIFICATION.md spec; gaps surfaced immediately via collection counts (e.g., "≥ 71 tests collected") rather than as silent skipped suites.
- **Lazy-import-via-fixture pattern:** `pytest.importorskip` at module top causes whole-file collection skip and breaks Nyquist `>= N tests collected` gates. Switching to per-test fixtures (`sw`/`pf`/`ih`-style) preserved individual test names in `--collect-only`. Set the testing convention for every later phase.
- **Pure-stdlib discipline:** Zero third-party Python dependencies across 14 helper scripts. Made the install one-liner viable (no pip-compile chains in `install.sh`); side-stepped Anthropic's "third-party-deps in skills" trap.
- **Glob-form `.gitattributes`:** `*.sh text eol=lf` matched the VALIDATION regex `^\*\.sh text eol=lf$` cleanly. Per-file form would have failed regex without flagging it as a real bug. Confirmed: write validation gates against the *form* you want, not just any form that happens to work.
- **Atomic commits per plan:** 45 plans → 45+ feature commits, each pinned to a specific test-set flip. Made `/gsd-undo` and post-mortem inspection cheap.
- **Single-threaded narration discipline:** Treating "dev-team metaphor" as narration-only (never parallel agents) avoided DeepMind Dec 2025's documented 41-86.7% multi-agent failure rates. The temptation to spin up agent-per-role would have torpedoed reliability.

### What Was Inefficient

- **`gsd-sdk milestone.complete` CLI bug:** The `milestoneComplete` handler passes empty args to `phasesArchive`, which validates `args[0]` and throws "version required". Cost ~5 minutes diagnosing and working around. Tracked as upstream issue: `phase-lifecycle.ts:1442` should pass `[version]` not `[]`.
- **Two stale checkboxes in REQUIREMENTS.md:** FOUND-01..05 + QUAL-04 stayed `[ ]` in the traceability table even after their phases shipped. Phase 03's VERIFICATION.md flagged this explicitly ("status column should be updated"); the per-phase `/gsd-transition` flow didn't propagate the flip back to REQUIREMENTS.md. v1.1 should add a checkbox-flip step to phase verification, OR a CI lint that cross-references REQUIREMENTS.md against PROJECT.md Validated.
- **Phase 7 single-day burndown vs Phase 4-6 multi-day cadence:** Phase 7 (4 playbooks + hub) shipped in one session because of the per-playbook-mirror-scaffold_web pattern. Phases 4-6 fragmented across multiple sessions despite similar plan counts. The "shape mirroring" trick is reusable: when a new feature is structurally identical to an existing one, lift the shape first, then customize.
- **Overconservative `human_needed` VERIFICATION status:** All 6 of the cross-phase `human_needed` flags reflect "live machine UX needs confirmation" rather than "implementation gap". The label is honest but masks the substance. Future phases could split into `automated_passed` + `manual_pending` instead of one `human_needed` umbrella.

### Patterns Established

- **Per-playbook scaffold shape verbatim:** Every `scaffold_<playbook>` mirrors `scaffold_web`'s 4-step shape: validate name → ensure_<tool> → subprocess.run scaffold cmd → atomic_write of vendored starter + Dockerfile + CI workflow. New playbooks should follow this template; the `_PLAYBOOK_DISPATCH` dict in `scaffold_dispatch.py` and `_PLAYBOOK_TOOLS` dict in `preflight_check.py` are the routing surfaces.
- **Argv-token script-path matching:** Test predicates that classify subprocess calls match by argv token (`c.endswith("script.py")`), never `" ".join(cmd)` substring scan. Values written through state_writer can legitimately contain tool/script names and would otherwise be misclassified.
- **Recursion-safe monkeypatch:** When tests intercept `subprocess.run`, capture `_real_run = subprocess.run` BEFORE `monkeypatch.setattr(...)`. The patched function delegates to `_real_run`, never to `subprocess.run` (which is now the patched proxy → infinite recursion). Python module-attribute mutation is global.
- **Comment-string negative-assertion trap:** When a test asserts `literal_X` is absent from a file, comments inside that file MUST NOT embed `literal_X` to discourage its use — the assertion trips on the comment. Use rephrasing ("legacy bundled-extras spelling" instead of "typer[all]").
- **Neutral last_failure messaging:** Avoid embedding tool names like "registry_verify" in `last_failure` values; use threat-class names ("slopsquatting gate") instead. Keeps test substring matchers honest AND surfaces user-facing language closer to "what threat was prevented" rather than "what tool ran".
- **Refuse-list-as-signal:** If Docker isn't a fit for the deployment target (e.g., CLI playbook = single-user local), skip the Dockerfile call rather than stamping a placeholder. CLI playbook ships NO Dockerfile by design.

### Key Lessons

1. **Test-collection counts are a Nyquist gate, not a coverage gate.** "≥ 25 RED stubs collected" is a different signal from "test passed". The lazy-import-via-fixture pattern was the only way to keep both signals honest after `pytest.importorskip` proved incompatible with collection-count gates.
2. **State-machine ALLOWED_FIELDS extension is cheap; REQUIRED_FIELDS extension is breaking.** state_writer.py grew from 10 fields → 19 fields across 5 phases without breaking Phase 1 fixtures because every new field went into ALLOWED_FIELDS only. REQUIRED_FIELDS stayed locked at 10. Phase compatibility came from this discipline.
3. **The "common person" audience constraint forced the right architectural choices.** Tutor mode ON by default + jargon-grep enforcement at runtime + friendly-error dictionary at every error-write site = a system that *cannot* leak technical jargon to the user except in `--advanced` mode. Without the audience constraint, the team would have rationalized "show the error" as fine.
4. **Scaffolder-first beats LLM-generation by ~10×.** Bolt.new burns 10M+ tokens to produce a `package.json` an LLM hand-wrote; OSBuilder calls `pnpm create next-app@latest` for free and gets idiomatic, reproducible output. Always check if a deterministic tool exists before reaching for LLM generation.
5. **Manual-UAT-pending is the correct steady-state for publish-bar phases.** Phase 8 verification is `phase-verified-with-waiver`, NOT `verified`. The 5 manual rows can't be automated (they're UX honesty + comprehension judgments). Treating that as a "gap" rather than a "by-design state" leads to either skipping UAT or pretending automated tests cover it.

### Cost Observations

- Model mix: ~95% opus, ~5% sonnet (estimated; opus carried planning + execution + verification; sonnet handled lightweight queries via gsd-sdk subprocess calls)
- Sessions: ~25-30 (rough estimate from STATE.md commit timestamps clustered by day)
- Notable: Phases 1, 2, 7 each shipped in single-session burndowns (1-day each); Phases 3, 4, 5, 6, 8 spanned 2-3 sessions with mid-phase `/clear` + state.md resume. The state.md checkpoint's compaction-survival design paid off concretely 3-4 times.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~25-30 | 8 | Wave-0-RED-stubs-first; lazy-import-via-fixture; per-playbook scaffold shape mirror; pure-stdlib discipline |

### Cumulative Quality

| Milestone | Tests | LOC (Python, incl. tests) | Zero-Dep Helper Scripts |
|-----------|-------|---------------------------|-------------------------|
| v1.0 | 207 passed / 3 skipped | 10,704 | 14 |

### Top Lessons (Verified Across Milestones)

1. (To be cross-validated in v1.1+)
