# Phase 5: Common-person UX polish — Specification

**Created:** 2026-04-30
**Ambiguity score:** 0.19 (gate: ≤ 0.20)
**Requirements:** 8 locked
**Mode:** `--auto` (no interactive interview — initial ambiguity already passed gate)

## Goal

Wrap OSBuilder's verified build loop in a UX layer a non-developer can drive end-to-end without seeing raw command output, framework jargon, or stack traces — tutor mode on by default, dev-team narration at every role transition, friendly-error translation for the top 30 documented failures, and beginner-mode default with `--advanced` opt-in for power users.

## Background

Phases 1–4 ship the build engine: state checkpointing, preflight installer, intake → research → scaffold, and the GSD-driven verify loop with failure classifier and registry gate. The codebase today exposes that engine raw:

- [SKILL.md](SKILL.md) **documents** tutor mode, `--quiet`, `--advanced`, friendly errors, and `scripts/friendly_error.py` — but **none of it is implemented**. `friendly_error.py` does not exist; the documented module is a forward reference.
- `scripts/gsd_driver.py` (Phase 4) drives the GSD per-phase loop and writes state directly. It emits no role-banner narration, no tutor explanations, and surfaces subprocess stdout/stderr unfiltered when delegated commands fail.
- [references/roles/](references/roles/) contains only `qa.md` (the falsifiable-criteria contract from Plan 04-05). The other 7 dev-team roles (PM, Architect, Frontend, Backend, DevOps, Reviewer, Tech Writer) have **no role briefs** — and ROLE-09 requires per-role narration scripts that do not exist.
- The intake question bank ([references/question-bank.md](references/question-bank.md), Plan 03-05) is jargon-free per Phase 3, but there is no flag-gating for `--advanced` and no mechanism that hides Postgres/Next.js/deploy-target prompts from default-mode users.
- No friendly-error dictionary exists in any form. Phase research ([.planning/research/PITFALLS.md](.planning/research/PITFALLS.md)) names ~10 high-frequency failures across preflight, gh auth, registry, and runtime — but Phase 5 needs 30 with translated messages and an expansion contract.
- The Tech Writer role (ROLE-07) has no defined contract for invoking `/gsd-docs-update` and `/humanizer`; there is no AI-pattern density check in any pipeline today.

The gap is a UX shell that wraps every gsd_driver step transition and every error surface. The shell renders narration, runs tutor explanations, intercepts raw errors and translates them, and gates jargon-bearing questions behind `--advanced`. Tech Writer becomes a real terminal phase that produces a humanizer-passed README before ship handoff to Phase 6.

## Requirements

1. **Friendly-error translation module**: A `scripts/friendly_error.py` module intercepts raw failures from delegated subprocesses and skill calls and emits translated user-facing messages.
   - Current: Module does not exist. Subprocess errors surface raw (ENOENT, EACCES, gh auth stack traces, Docker daemon errors, port-in-use messages, ModuleNotFoundError, npm registry 4xx, pnpm install failures).
   - Target: `friendly_error.py` exposes `translate(raw_error: str | Exception, context: dict) -> FriendlyMessage` returning `{title, what_broke, what_to_do, copy_paste_command | None, severity}`. Every error path in `gsd_driver.py`, `preflight_check.py`, `scaffold_dispatch.py`, `stack_researcher.py`, and `intake_handler.py` routes through it before user output. Raw stack traces are written to a debug log file (not stdout) and referenced in the friendly message footer.
   - Acceptance: Inducing each of the 30 catalog errors (port-in-use, missing Docker daemon, expired `gh` token, `ENOENT` on a known-missing path, `EACCES`, `ModuleNotFoundError`, npm 404, `pnpm: command not found`, registry-block from Phase 4 gate, etc.) produces output that contains no raw stack frames, no `Traceback`, no `errno`, no Python module names, and includes a concrete next-step the user can copy-paste.

2. **Top-30 friendly-error dictionary**: A starter dictionary covers the top 30 failures observed across preflight, intake, scaffold, install, GSD loop, and ship paths.
   - Current: No dictionary exists. Failure responses are ad-hoc raw error pass-through.
   - Target: `references/friendly-errors/dictionary.yaml` (or `.md` table — format to be locked in plan-phase) contains exactly 30 entries; each entry has fields `id`, `match_pattern` (regex or substring), `category` (preflight | gh-auth | registry | runtime | docker | filesystem | network | git | scaffold), `title`, `what_broke`, `what_to_do`, `copy_paste_command`, `phase_seen`, `expansion_note`. `friendly_error.py` loads this dictionary at import time and uses it as the primary translation source before falling back to a generic translator.
   - Acceptance: `wc -l` on the dictionary file shows >= 30 entries; running `python -c "from scripts.friendly_error import load_dictionary; assert len(load_dictionary()) >= 30"` exits 0; every entry includes all 8 documented fields (verified by a schema check in tests).

3. **Friendly-error dictionary expansion path**: The dictionary has a documented contribution contract so future versions can grow it without code changes.
   - Current: No expansion path documented; no contribution guide for future error entries.
   - Target: `references/friendly-errors/README.md` documents (a) the dictionary file location and format, (b) the field schema with examples, (c) how to test a new entry, (d) the criteria for inclusion ("seen in dogfood build N times" or "blocks user progress"), and (e) the format-version field that lets `friendly_error.py` reject malformed dictionaries with a clear error.
   - Acceptance: `references/friendly-errors/README.md` exists and includes all 5 documented sections; adding a new entry to the dictionary and re-running the test suite produces no code changes — only data changes.

4. **Dev-team narration module**: A `scripts/narration.py` module emits role-banner progress lines at every gsd_driver phase-step transition and intercepts subprocess output before it reaches the user.
   - Current: `gsd_driver.py` step transitions are silent at the user-facing layer; subprocess stdout/stderr from delegated commands prints raw.
   - Target: `narration.py` exposes `emit(role: Role, action: str, status: Literal["start", "ok", "fail"], detail: str | None = None)` rendering one line of the form `[PM] Gathering requirements... ✓` or `[Architect] Choosing the stack... (researching)`. `gsd_driver.py` calls `emit()` at every PHASE_STEP_COMMANDS dispatch boundary. Subprocess output is buffered, parsed for completion signals, and only the friendly summary is rendered — raw output goes to a debug log under `.planning/osbuilder/build.log`.
   - Acceptance: An end-to-end build of the TODO web app prints role banners for all 8 dev-team roles (PM, Architect, Frontend, Backend, DevOps, QA, Reviewer, Tech Writer) and contains zero lines matching the regexes `^\s+at .+\(.+:\d+\)$` (Node stack), `^\s+File ".*", line \d+,` (Python stack), `^npm ERR!`, `^pnpm ERR_`, `^Error: ENOENT`, or `^Traceback \(most recent`.

5. **Tutor mode (default ON, `--quiet` opt-out)**: Every role transition emits a 1–2 sentence "what just happened in plain English" line that explains the just-completed step at a non-developer reading level.
   - Current: No tutor lines emitted. No flag plumbing for `--quiet`.
   - Target: `narration.py` produces a tutor-mode line after each role's `status="ok"` emission. Tutor lines are sourced from per-role briefs (see Requirement 6) and use no jargon (`framework`, `endpoint`, `responsive`, `ORM`, `dependency injection`, `transpiler` are forbidden). `--quiet` flag (parsed by the OSBuilder entry point and propagated via `state.md`) suppresses tutor lines entirely while keeping role banners + final outputs. `--tutor` is a no-op alias for the default.
   - Acceptance: Default-mode build output contains >= 8 tutor lines (one per role transition) for the TODO web app E2E; `--quiet` mode build output contains zero lines starting with `> ` (the documented tutor-line prefix) but retains role banners; no tutor line contains any of the 6 forbidden jargon tokens (verified by grep on the captured output).

6. **Per-role narration briefs**: `references/roles/{pm,architect,frontend,backend,devops,reviewer,tech-writer}.md` define each role's narration template.
   - Current: Only `references/roles/qa.md` exists (Plan 04-05). Six other role briefs are missing.
   - Target: 7 new role briefs exist (one for each non-QA dev-team role), each with: (a) role-banner template (`[PM] {action}...`), (b) tutor-line template ("In plain English: {explanation}"), (c) per-phase-step copy variants for the role's actions (e.g., PM has copy for intake, spec, brief synthesis), and (d) failure-mode copy ("PM ran into a snag: {friendly_error}"). Each brief is between 50 and 200 lines and is loaded on-demand by `narration.py`.
   - Acceptance: `find references/roles -name "*.md" | wc -l` returns 8 (qa.md + 7 new); each new brief has the 4 documented sections (verified by a structural check in tests); no brief contains any of the 6 forbidden jargon tokens.

7. **Beginner-mode default with `--advanced` opt-in**: Default-mode runs never expose stack-choice questions, never name technologies before scaffolding starts, and never prompt for deploy targets. `--advanced` exposes all of these verbatim.
   - Current: Phase 3's question bank is jargon-free, but there is no gating mechanism for `--advanced`. Stack research output (Phase 3) is shown to the user via `state.md` raw fields; `state_writer.py` exposes `stack_choices` as user-readable.
   - Target: A `mode` field in `state.md` (`beginner` default | `advanced`) gates which questions from the question bank are shown to the user and which decisions are surfaced as user-facing prompts vs auto-resolved with the documented sensible default. `--advanced` flag at OSBuilder entry sets `mode=advanced` for the session. Stack choices, deploy targets, and scaffolder selection are surfaced as questions only when `mode=advanced`; in beginner mode they resolve silently to the documented defaults from `references/stack-menu.md`.
   - Acceptance: Default-mode end-to-end build for "TODO web app" produces zero prompts containing the words `Next.js`, `SvelteKit`, `Postgres`, `SQLite`, `Vercel`, `Fly.io`, `Railway`, `Drizzle`, or `Tailwind` (verified by capturing the prompt stream and grepping); `--advanced` mode exposes at least 3 of those terms across its prompts.

8. **Tech Writer phase + humanizer integration (ROLE-07)**: A Tech Writer phase runs after QA + Reviewer, delegates to `/gsd-docs-update` for README generation, and gates the result through `/humanizer` for AI-pattern density before the build is marked complete.
   - Current: ROLE-07 is unimplemented. No Tech Writer step in `gsd_driver.py`'s PHASE_STEP_COMMANDS. README generation is implicit (left to whatever Phase 6 ship does, which is also unbuilt).
   - Target: A new `phase_step` value in `gsd_driver.py` (`tech-writer`) invokes `/gsd-docs-update --target=README.md` then `/humanizer --check README.md` in sequence; the humanizer check produces a `humanizer_score` written to `state.md`; if the score reports >= 1 critical AI-pattern issue (em-dash overuse, inflated symbolism, vague attribution, AI vocabulary triad — categories named in the humanizer skill), the Tech Writer step retries once with `/humanizer --rewrite README.md` then fails the phase if still flagged. README explains the dev-team metaphor and the run command in language a non-developer can follow.
   - Acceptance: A built TODO-web-app produces a `README.md` containing a "How OSBuilder built this" section that names PM/Architect/Frontend/Backend/DevOps/QA/Reviewer/Tech Writer in plain English; running `/humanizer --check` against that README reports zero critical issues; `state.md` contains a `humanizer_score` field with a recorded value.

## Boundaries

**In scope:**
- `scripts/friendly_error.py` module + 30-entry dictionary + expansion path README
- `scripts/narration.py` module wired into every `gsd_driver.py` step transition and every subprocess call
- Tutor-mode rendering layer with `--quiet` flag plumbing
- Per-role narration briefs in `references/roles/{pm,architect,frontend,backend,devops,reviewer,tech-writer}.md`
- Beginner/advanced mode gating in question-bank surface (state field + flag)
- Tech Writer phase step + humanizer integration in `gsd_driver.py`
- Tests covering: friendly-error dictionary schema, narration emission for all 8 roles, tutor-line jargon scan, advanced-mode gating, humanizer score persistence in state.md

**Out of scope:**
- `gh` repo creation / push / runbook generation — Phase 6 (SHIP-01..05). Tech Writer in Phase 5 produces the README; the actual `gh repo create --private` push happens in Phase 6.
- `.env.example` / `compose.yaml` / `Dockerfile` / `.github/workflows/*.yml` scaffold defaults — Phase 6 (SCL-01..06). Phase 5 narrates these decisions but does not generate them.
- Friendly-error dictionary entries beyond the top 30 — explicitly an expansion-path concern (entries 31+ added via the contribution contract documented in Requirement 3).
- Voice intake or multimodal narration — v2 (V2-MM-01, V2-MM-02).
- Localization of narration / tutor copy to non-English — v2 (English-first per FEATURES.md MVP).
- Adding K8s / observability / Sentry / rate-limiting narration copy — Phase 8 (`--production-ready` named phases). Beginner mode in Phase 5 refuses these silently using the existing Phase 1 hard-rule list.
- Runtime humanizer rewrite suggestions inside tutor lines — humanizer runs only against the final README, not the live tutor stream.
- Changing the Phase 4 failure classifier or the registry gate — Phase 5 only consumes their outputs through the new translation layer.

## Constraints

- **No raw subprocess output may reach the user in default mode.** All stdout/stderr from delegated commands is captured by `narration.py` and either summarized or routed to the debug log. This is enforced by the regex check in Requirement 4's acceptance.
- **The 6 forbidden jargon tokens** (`framework`, `endpoint`, `responsive`, `ORM`, `dependency injection`, `transpiler`) must not appear in any default-mode tutor line, role banner, or friendly-error message. They may appear in `--advanced` mode and in role briefs' "advanced copy" sections.
- **`humanizer` is a userland skill at `~/.claude/skills/humanizer/`**, invoked via slash-command from `gsd_driver.py`. Phase 5 does not embed humanizer logic; it only invokes it. If humanizer is missing or version-drift'd, the Tech Writer step emits a friendly-error and falls back to a non-humanizer-gated README (with a warning logged to state.md and surfaced in the build summary).
- **`state.md` schema additions** (`mode`, `humanizer_score`, plus any narration-related fields) must extend `state_writer.py`'s `ALLOWED_FIELDS` list per the established Phase 4 pattern (commit history shows extensions in 04-01).
- **Dictionary file format** is a tabular human-editable format (YAML preferred over JSON for comments + multi-line strings). Lock the format choice in plan-phase; do not change it after Phase 5 ships.
- **All new narration / tutor / friendly-error copy must be authored in English.** Localization is explicitly v2.
- **No new Python dependencies.** Phase 5 stays on Python 3.13 stdlib (re-using the `pyyaml`-or-stdlib decision from earlier phases — if stdlib doesn't support the chosen format, fall back to a hand-rolled parser per the existing project pattern).

## Acceptance Criteria

- [ ] `scripts/friendly_error.py` exists and exposes `translate(raw_error, context) -> FriendlyMessage`
- [ ] `references/friendly-errors/dictionary.{yaml|md}` contains >= 30 entries, each with all 8 documented fields
- [ ] `references/friendly-errors/README.md` documents file location, format, schema, contribution criteria, and format-version
- [ ] `scripts/narration.py` exists and is invoked at every `gsd_driver.py` `phase_step` transition
- [ ] Default-mode E2E TODO-web-app build prints role banners for all 8 dev-team roles
- [ ] Default-mode E2E TODO-web-app build output contains zero raw stack frames, zero `Traceback`, zero `npm ERR!`, zero `pnpm ERR_`
- [ ] Default-mode tutor lines: >= 8 emitted across an E2E build; zero contain any of the 6 forbidden jargon tokens
- [ ] `--quiet` flag suppresses tutor lines (zero `> ` prefix lines) while keeping role banners
- [ ] `references/roles/` contains 8 files: `qa.md` + 7 new role briefs (pm, architect, frontend, backend, devops, reviewer, tech-writer)
- [ ] Each new role brief contains the 4 required sections (banner template, tutor template, per-step copy, failure copy)
- [ ] Default-mode TODO-web-app prompts contain zero jargon technology names from the documented list (Next.js, SvelteKit, Postgres, SQLite, Vercel, Fly.io, Railway, Drizzle, Tailwind)
- [ ] `--advanced` mode exposes >= 3 technology names across its prompts
- [ ] `gsd_driver.py` PHASE_STEP_COMMANDS includes a `tech-writer` step that invokes `/gsd-docs-update` then `/humanizer --check`
- [ ] Generated README contains a "How OSBuilder built this" section naming all 8 dev-team roles in plain English
- [ ] `humanizer --check` on the generated README reports zero critical AI-pattern issues
- [ ] `state.md` contains `mode` and `humanizer_score` fields after an E2E build

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                                                                 |
|--------------------|-------|------|--------|----------------------------------------------------------------------|
| Goal Clarity       | 0.85  | 0.75 | ✓      | 6 falsifiable success criteria from ROADMAP; goal is "wrap engine in UX shell" |
| Boundary Clarity   | 0.80  | 0.70 | ✓      | 7 mapped requirements; explicit Phase 6 hand-off boundary; 7 out-of-scope items |
| Constraint Clarity | 0.75  | 0.65 | ✓      | Forbidden-jargon list explicit; humanizer fallback documented; format choice deferred to plan-phase (assumption) |
| Acceptance Criteria| 0.80  | 0.70 | ✓      | 16 pass/fail criteria; humanizer "critical issue" definition assumes humanizer skill's existing taxonomy |
| **Ambiguity**      | 0.19  | ≤0.20| ✓      |                                                                      |

**Documented assumptions (planner should treat as locked-with-caveat):**
1. Friendly-error dictionary format is YAML by default; planner may choose Markdown table if YAML loading would require a non-stdlib dependency.
2. Humanizer "critical AI-pattern issue" maps to the humanizer skill's existing severity taxonomy. If humanizer's contract differs from this assumption when planner reads the skill, surface as a deviation in `--auto` planner mode.
3. The `mode` field in `state.md` is a string enum (`beginner` | `advanced`); upgrade path to a richer mode object (e.g., per-question-bank-section gates) is deferred to Phase 8 polish if needed.
4. Tutor lines use the `> ` prefix by default; planner may choose a different prefix as long as it is unique and grep-able.

## Interview Log

| Round | Perspective    | Question summary                  | Decision locked                                                              |
|-------|----------------|----------------------------------|------------------------------------------------------------------------------|
| 0     | Auto           | Initial ambiguity 0.19 ≤ 0.20    | Skipped interview per --auto rule; derived requirements from ROADMAP+REQS    |
| 0     | Auto           | Friendly-error dictionary format | YAML default, Markdown fallback if non-stdlib (assumption #1)                |
| 0     | Auto           | Humanizer integration semantics  | Critical-issue threshold = 0; retry once with --rewrite, then fail (asm #2)  |
| 0     | Auto           | --quiet semantics                | Suppresses tutor lines, keeps role banners + final outputs (per ROADMAP SC1) |
| 0     | Auto           | --advanced gating mechanism      | `mode` field in state.md; flag at entry sets it (assumption #3)              |
| 0     | Auto           | Forbidden jargon scope           | 6 tokens locked: framework, endpoint, responsive, ORM, DI, transpiler        |

---

*Phase: 05-common-person-ux-polish*
*Spec created: 2026-04-30*
*Next step: /gsd-discuss-phase 5 — implementation decisions (file format choice, narration buffer mechanics, tutor-line copy authoring workflow, etc.)*
