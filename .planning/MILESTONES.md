# Milestones: OSBuilder

Historical record of shipped versions. For current status, see `.planning/ROADMAP.md`.

---

## v1.0 — Publish-Ready (shipped 2026-05-05)

**Phases:** 1-8 (45 plans, ~125 tasks)
**Timeline:** 2026-04-29 → 2026-05-05 (7 days)
**Test surface:** 207 passed / 3 skipped (3 skips intentional and documented)
**Codebase:** 124 deliverable files; 10,704 LOC Python (incl. tests); 1,609 LOC reference Markdown
**Git range:** `6f64c7b` (project init) → `e2db698` (URL re-lock); 226 commits
**Diff:** 277 files changed, +65,303 / −7
**Tag:** `v1.0`

### Delivered

OSBuilder is open-source publish-ready as a Claude Code skill. A non-developer describes an app in plain English; OSBuilder drives the full intake → research → scaffold → verify → ship loop, ending at a working local app pushed to a private GitHub repo. The full v1 surface — 4 playbooks (web, ai-service, cli, desktop) + hub-platform — landed with deterministic-scaffolder-first discipline, classified failure handling capped at 3 reflections, dev-team narration over GSD/brainiac/predator/code-tester/problem-solver/gsd-debug, and a `--production-ready` upgrade path that adds K8s/observability/Sentry as named ROADMAP phases instead of default code.

### Key accomplishments

1. **Skill skeleton + state plumbing** (Phase 1) — SKILL.md at 136/200 lines; 4-directory layout; 10-field `state.md` checkpoint with atomic `os.replace`; cross-platform `bootstrap.sh` + `bootstrap.ps1` Python install shims.
2. **Cross-platform pre-flight installer** (Phase 2) — 595-line `preflight_check.py` with transactional rollback, AST-verified read-only `render_preview()`, version-manager refusal (nvm/pyenv/mise/asdf), per-OS package matrices for brew / apt / dnf / winget. `--no-docker` mode for Windows individual users.
3. **Intake → research → web scaffold E2E** (Phase 3) — Plain-English paragraph or structured spec → `derived_spec.md` → brainiac-driven stack research with `stack-menu.md` fallback → pinned `pnpm create next-app@latest` flags + 4 Drizzle post-scaffold files (`compose.yaml` v2, never `docker-compose.yml`). Jargon-free question bank with "I don't know, you decide" on every Q.
4. **GSD handoff + verify loop + classified self-healing** (Phase 4) — 678-line `gsd_driver.py` orchestrator; 4-class failure taxonomy with 3-reflection cap; transient retries with 1s → 4s → 16s exponential backoff; slopsquatting gate via `registry_verify.py` (npm/PyPI/crates.io HEAD-request). Falsifiable VERIFICATION.md per phase.
5. **Common-person UX polish** (Phase 5) — 39-entry friendly-error dictionary with versioned format gate; 8 dev-team role briefs driving `[ROLE]` banners + `> In plain English` tutor lines; beginner-mode default with zero hits for 9 forbidden tech tokens; tech-writer step with humanizer integration + graceful degrade.
6. **Ship to private GitHub + scalable defaults** (Phase 6) — `gh repo create --private` with token redaction; `runbook_writer.py` clone-and-run README from template; gitleaks pre-commit hook pinned to v8.30.1; refuse-list with word-boundary regex (K8s/microservices/Helm); `--production-ready` emits 7 named upgrades verbatim.
7. **4 playbooks + hub-platform** (Phase 7) — AI-service (FastAPI + uv + Pydantic v2), CLI (Typer + Rich + SQLite, NO Dockerfile), desktop (Tauri 2 with `_build_tauri_identifier` reverse-DNS), hub-platform (pure file-stamping with vendored `professor-snapshot/`). 5-way `app_type` inference; Electron globally refused with binary-size + RAM rationale.
8. **Publish-bar quality surface** (Phase 8) — `check_skill_md_length.py` + `check_skill_versions.py` (pure stdlib); `requires:` block in SKILL.md frontmatter declares 5 sub-skill minimums; CI workflow with pinned `@v6` actions; README with dev-team metaphor + `--production-ready` doc; 3-example gallery (web/cli/ai-service); RECORDING-CHECKLIST.md for the deferred 60s demo recording.

### Known deferred items at close

11 (see STATE.md `## Deferred Items`).

By-design manual-UAT and live-machine UX judgments for an open-source publish-bar milestone:

- 5 phases with pending HUMAN-UAT (02, 03, 05, 07, 08): clean-machine install, live build narration, stranger clone-and-run across 4 playbooks, demo honesty, README plain-English read.
- 6 phases with `human_needed` VERIFICATION.md status (02, 03, 05, 06, 07, 08): all structurally complete at the automated level; live UX confirmation pending.
- 3 documented waivers in 08-VERIFICATION.md frontmatter: demo binary, real example screenshots, NOT_PUBLISHED repo URLs.

### Archives

- Roadmap: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- Requirements: [milestones/v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)
- Phase directories: [milestones/v1.0-phases/](milestones/v1.0-phases/) (8 phases × 5-8 plans each)
