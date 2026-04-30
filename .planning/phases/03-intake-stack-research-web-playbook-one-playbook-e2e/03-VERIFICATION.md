---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
verified: 2026-04-30T19:30:00Z
status: human_needed
score: 9/11 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run pnpm install && pnpm dev in a freshly scaffolded project directory"
    expected: "Next.js scaffolded homepage appears on localhost:3000 without errors; zero hand-written package.json or tsconfig.json lines from OSBuilder"
    why_human: "scaffold_dispatch.py produces the correct 4 post-scaffold files and runs create-next-app with the right flags, but the actual pnpm install and dev-server boot requires a live system with pnpm installed and takes multiple minutes — cannot be verified with grep or a < 10 second command"
  - test: "Run end-to-end: call intake_handler.parse_paragraph with a TODO app description, then research_stack, then scaffold_web, and measure total time to working scaffold (excluding pnpm install network fetch)"
    expected: "Full intake → research → scaffold loop completes within 60 seconds; derived_spec.md written; stack_choices in state.md; project directory with all 4 Drizzle files on disk"
    why_human: "The 60-second E2E gate (SC-7) requires actual subprocess execution including pnpm create next-app, which takes 20-40 seconds on a real machine; cannot verify timing in < 10 seconds without running pnpm"
---

# Phase 3: Intake + Stack Research + Web Playbook Verification Report

**Phase Goal:** A user describes a web app in plain English and OSBuilder produces a scaffolded, runnable Next.js + Postgres + Tailwind project on disk — proving the full intake → research → scaffold loop end-to-end on the most-validated playbook before any other playbooks are added.
**Verified:** 2026-04-30T19:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can pass a plain-English paragraph and get a derived_spec.md written to disk | VERIFIED | `intake_handler.parse_paragraph()` writes `<project_root>/.planning/osbuilder/derived_spec.md`; Level-4 trace confirmed content starts with `# OSBuilder Derived Spec` and contains Goal/App type/Playbook sections |
| 2 | User can pass a structured spec dict and get the same derived_spec.md format | VERIFIED | `intake_handler.parse_structured()` confirmed functional; test_structured_spec_to_derived_spec PASSED |
| 3 | All clarifying questions are jargon-free with "I don't know, you decide" option | VERIFIED | `references/question-bank.md` has 6 Q sections; word-boundary grep for all 11 JARGON words returns 0; every Q section contains "I don't know, you decide"; test_questions_have_no_jargon + test_questions_have_you_decide_option both PASSED |
| 4 | Stack research returns a structured dict (framework/orm/database/css/package_manager with name/version) and falls back to stack-menu.md defaults | VERIFIED | `stack_researcher.research_stack()` returns structured dict; `_read_stack_menu()` parses `references/stack-menu.md` and returns `{name, version, source}` per component; hardcoded `_WEB_DEFAULTS` used when file absent; all 4 RES tests PASSED |
| 5 | `--advanced` overrides merge over researched stack choices and are logged to state.md | VERIFIED | Behavioral spot-check confirmed `research_stack(..., advanced_overrides={'orm': {'name': 'prisma', ...}})` returns prisma as orm; `stack_choices` written to `state.md` via state_writer subprocess; test_advanced_override PASSED |
| 6 | `scaffold_dispatch.py` runs `pnpm create next-app@latest` with explicit flags (never `--yes`) and produces a project with 4 Drizzle post-scaffold files | VERIFIED | `scaffold_web()` confirmed: --typescript, --tailwind, --app, --src-dir, --eslint, --use-pnpm, --disable-git flags present; `--yes` absent; `write_drizzle_files()` Level-4 trace: all 4 files (src/lib/db.ts, drizzle.config.ts, .env.example, compose.yaml) written with correct content; docker-compose.yml absent |
| 7 | compose.yaml is written (Compose v2); docker-compose.yml is never written | VERIFIED | `compose.yaml` exists in scaffold with `postgres:18-alpine`; grep for `docker-compose.yml` in scaffold_dispatch.py exits non-zero; test_compose_yaml_written PASSED |
| 8 | `pnpm install && pnpm dev` boots the scaffolded homepage on localhost:3000 | UNCERTAIN | Cannot verify without live pnpm execution; scaffold command and flags are structurally correct but actual boot requires human test |
| 9 | derived_spec.md contains no secrets, API keys, or passwords | VERIFIED | Security check in parse_paragraph/parse_structured: `_SECRET_PATTERNS` scanned; test_derived_spec_format PASSED; .env.example uses `myapp` (5-char placeholder below 8-char regex threshold) |
| 10 | state_writer.py accepts project_path, stack_choices, stack_overrides without SystemExit | VERIFIED | `state_writer.ALLOWED_FIELDS` confirmed to contain all three new fields; `len(REQUIRED_FIELDS) == 10` (unchanged); test_state_writer suite still 100% GREEN |
| 11 | End-to-end loop completes within 60 seconds (excluding network fetch) | UNCERTAIN | Cannot verify timing without live execution through pnpm subprocess |

**Score:** 9/11 truths verified

### Deferred Items

None — all items are either verified or require human testing (no items addressed in later phases).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/tests/test_intake.py` | 5 RED stubs, IN-01..IN-05 | VERIFIED | 5 tests, all PASSED (46-test suite 100% GREEN); lazy `ih` fixture; pytest.importorskip in docstring comment only (not a live call) |
| `scripts/tests/test_stack_researcher.py` | 4 RED stubs, RES-01..RES-04 | VERIFIED | 4 tests, all PASSED; lazy `sr` fixture |
| `scripts/tests/test_scaffold_dispatch.py` | 7 RED stubs, SCAF-01/SCAF-06 | VERIFIED | 7 tests, all PASSED; lazy `sd` fixture |
| `scripts/intake_handler.py` | parse_paragraph, parse_structured, ≤ 200 lines | VERIFIED | 186 lines; both functions present; atomic_write; _validate_project_name; argparse CLI |
| `scripts/stack_researcher.py` | research_stack, ≤ 200 lines | VERIFIED | 190 lines; research_stack, _call_brainiac, _read_stack_menu all present |
| `scripts/scaffold_dispatch.py` | scaffold_web, write_drizzle_files, ensure_pnpm, ≤ 200 lines | VERIFIED | 200 lines; all 3 functions present |
| `scripts/state_writer.py` | ALLOWED_FIELDS extended | VERIFIED | project_path, stack_choices, stack_overrides in ALLOWED_FIELDS; REQUIRED_FIELDS unchanged (10 fields) |
| `references/playbooks/web.md` | scaffold command, 4 post-scaffold files, ≤ 80 lines | VERIFIED | 77 lines; pnpm create next-app, --typescript, --disable-git, drizzle, compose.yaml all present |
| `references/stack-menu.md` | "## Web playbook defaults" table, parseable | VERIFIED | 42 lines; section header present; _read_stack_menu() smoke test: framework=next.js@16.2.4, package_manager=pnpm@10.33.2 |
| `references/question-bank.md` | ≥ 5 Q sections, jargon-free | VERIFIED | 66 lines; 6 Q sections; 0 jargon words; all sections have "I don't know, you decide" |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scripts/tests/test_intake.py` | `scripts/intake_handler.py` | `importlib.import_module("intake_handler")` in `ih` fixture | VERIFIED | Pattern found; importlib.import_module confirmed present |
| `scripts/tests/test_stack_researcher.py` | `scripts/stack_researcher.py` | `importlib.import_module("stack_researcher")` in `sr` fixture | VERIFIED | Pattern found |
| `scripts/tests/test_scaffold_dispatch.py` | `scripts/scaffold_dispatch.py` | `importlib.import_module("scaffold_dispatch")` in `sd` fixture | VERIFIED | Pattern found |
| `scripts/intake_handler.py` | `<project-root>/.planning/osbuilder/derived_spec.md` | `atomic_write()` in `parse_paragraph()` and `parse_structured()` | VERIFIED | Level-4 data-flow trace: file written and read back with correct content |
| `scripts/intake_handler.py` | `scripts/state_writer.py` | `state_writer` reference in module | VERIFIED | state_writer reference confirmed; ALLOWED_FIELDS extension enables downstream writes |
| `scripts/stack_researcher.py` | brainiac subprocess | `subprocess.run(['python3', '-m', 'brainiac', ...], shell=False, timeout=30)` | VERIFIED | `_call_brainiac` pattern confirmed; shell=False; timeout=30 present |
| `scripts/stack_researcher.py` | `references/stack-menu.md` | `_read_stack_menu(references_root)` | VERIFIED | Function present; smoke test parses file correctly; hardcoded fallback confirmed working |
| `scripts/stack_researcher.py` | `scripts/state_writer.py` | `subprocess.run([..., 'stack_choices', ...])` | VERIFIED | STATE_WRITER constant present; stack_choices write call confirmed |
| `scripts/scaffold_dispatch.py` | `pnpm create next-app@latest` subprocess | `subprocess.run(cmd, ..., shell=False)` | VERIFIED | next-app@latest pattern confirmed; shell=False; --yes absent; all 7 required flags present |
| `scripts/scaffold_dispatch.py` | `project_dir/src/lib/db.ts + drizzle.config.ts + .env.example + compose.yaml` | `atomic_write()` for each of 4 files | VERIFIED | Level-4 data-flow trace: all 4 files written with correct content; docker-compose.yml not written |
| `scripts/scaffold_dispatch.py` | `scripts/state_writer.py` | `subprocess.run([..., 'project_path', ...])` | VERIFIED | project_path write confirmed; STATE_WRITER constant present |
| `references/stack-menu.md` | `scripts/stack_researcher.py _read_stack_menu()` | "## Web playbook defaults" section parsed by regex | VERIFIED | Section header confirmed; smoke test parsing succeeds |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `scripts/intake_handler.py` | `derived_spec_path` | `_render_derived_spec()` renders from user paragraph/dict | Yes — content includes actual goal text, app_type, playbook path | VERIFIED (FLOWING) |
| `scripts/stack_researcher.py` | `stack_choices` | `_call_brainiac()` or `_read_stack_menu()` | Yes — structured dict with name/version per component; fallback returns hardcoded `_WEB_DEFAULTS` | VERIFIED (FLOWING) |
| `scripts/scaffold_dispatch.py` | `write_drizzle_files()` output | Template constants `_DB_TS`, `_DRIZZLE_CONFIG`, `_ENV_EXAMPLE`, `_COMPOSE_YAML` | Yes — real TypeScript/YAML file content written to disk | VERIFIED (FLOWING) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| parse_paragraph writes derived_spec.md with correct format | `intake_handler.parse_paragraph("I want a website...", tmp)` → read file | File exists; starts with `# OSBuilder Derived Spec`; Goal/App type/Playbook sections present | PASS |
| parse_structured produces same format as paragraph path | `intake_handler.parse_structured({goal, features, users, stack_hints}, tmp)` → read file | Same sections; no secrets | PASS |
| _read_stack_menu parses stack-menu.md file | `stack_researcher._read_stack_menu(Path('references'))` | Returns `{framework: {name: next.js, version: 16.2.4, source: stack-menu}, ...}` | PASS |
| write_drizzle_files writes all 4 files | `scaffold_dispatch.write_drizzle_files(proj_dir)` | db.ts has drizzle-orm/postgres-js; drizzle.config.ts has postgresql; .env.example has DATABASE_URL=; compose.yaml has postgres:18-alpine; docker-compose.yml absent | PASS |
| advanced overrides merge over researched choices | `research_stack('web', ..., advanced_overrides={'orm': {'name': 'prisma', ...}})` | result['orm']['name'] == 'prisma' | PASS |
| Input validation rejects path traversal and shell-unsafe chars | `_validate_project_name('..')` and `_validate_project_name('my app')` | Both raise SystemExit; valid name accepted | PASS |
| pnpm install && pnpm dev boots localhost:3000 | Manual run in scaffolded directory | NOT TESTED | SKIP (needs human) |
| End-to-end completes within 60 seconds | Full loop with live pnpm subprocess | NOT TESTED | SKIP (needs human) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| IN-01 | 03-02 | Paragraph input → OSBuilder takes it from there | SATISFIED | `parse_paragraph()` writes derived_spec.md; test_paragraph_to_derived_spec PASSED |
| IN-02 | 03-02 | Structured spec input supported | SATISFIED | `parse_structured()` functional; test_structured_spec_to_derived_spec PASSED |
| IN-03 | 03-05 | Clarifying questions jargon-free | SATISFIED | question-bank.md: 0 jargon words; test_questions_have_no_jargon PASSED |
| IN-04 | 03-05 | Every question has "I don't know, you decide" option | SATISFIED | All 6 Q sections confirmed; test_questions_have_you_decide_option PASSED |
| IN-05 | 03-02 | Brief synthesized for /gsd-new-project --auto handoff | SATISFIED | derived_spec.md starts with `# OSBuilder Derived Spec`; test_derived_spec_format PASSED |
| RES-01 | 03-03 | brainiac subprocess called for stack research | SATISFIED | `_call_brainiac()` uses `subprocess.run(['python3', '-m', 'brainiac', ...], shell=False, timeout=30)`; test_calls_brainiac PASSED |
| RES-02 | 03-03 | Stack research output is structured with verified versions | SATISFIED | Dict with framework/orm/database/css/package_manager, each with name/version; test_output_is_structured PASSED |
| RES-03 | 03-03 | Falls back to stack-menu.md on inconclusive result | SATISFIED | `_read_stack_menu()` parses references/stack-menu.md; hardcoded fallback when file absent; test_fallback_to_stack_menu PASSED |
| RES-04 | 03-03 | --advanced mode overrides researched stack | SATISFIED | `advanced_overrides` param merges over result; override wins on conflicting key; test_advanced_override PASSED |
| SCAF-01 | 03-04/03-05 | references/playbooks/web.md maintained with correct scaffold command | SATISFIED | File exists (77 lines); pnpm create next-app + all required flags documented; test_web_playbook_exists PASSED |
| SCAF-06 | 03-04 | scaffold_dispatch.py invokes deterministic scaffolder; never hand-writes package.json/tsconfig.json | SATISFIED | scaffold_web() runs create-next-app with 7 explicit flags; write_drizzle_files() writes only 4 permitted post-scaffold files; module docstring explicitly lists forbidden writes |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/tests/test_intake.py` | 8 | `pytest.importorskip` appears in docstring comment (not a call) | INFO | Not a real anti-pattern — the docstring explicitly explains why `importorskip` is the anti-pattern to avoid; the word appears in prose, not as executable code; grep check produces a false positive |

No blockers found. No stubs, no missing implementations, no hardcoded empty returns, no shell=True calls, no --yes flags.

### Human Verification Required

#### 1. Scaffold boots on localhost:3000

**Test:** In a terminal with pnpm available, run `scripts/scaffold_dispatch.py scaffold --project-name test-app --project-root /tmp/osbuilder-test`, then `cd /tmp/osbuilder-test/test-app && pnpm install && pnpm dev`.
**Expected:** Next.js 16 homepage appears at localhost:3000 without errors. No OSBuilder-written lines in package.json or tsconfig.json (those come from create-next-app exclusively).
**Why human:** Requires live pnpm installation and a running dev server. The scaffold command and all 7 flags are structurally verified, but actual boot of the Next.js app requires pnpm to be installed and takes 20-40 seconds — outside the < 10s spot-check constraint.

#### 2. End-to-end loop timing (SC-7)

**Test:** Measure time from calling `parse_paragraph("Build me a TODO web app...")` through `research_stack()` through `scaffold_web()` to a project directory with all 4 Drizzle files on disk.
**Expected:** Complete in under 60 seconds, excluding pnpm install network fetch time.
**Why human:** Requires live subprocess execution of pnpm create next-app which takes significant wall-clock time; the 60-second gate cannot be verified with a static code check.

### Gaps Summary

No gaps were found. All 9 automatically-verifiable must-haves pass at all four levels (exists, substantive, wired, data-flowing). The 2 human verification items (SC-5 and SC-7) relate to live execution behavior — the implementation is structurally complete and correct; what remains is runtime confirmation that the created scaffold actually boots and that the loop meets the 60-second target.

**Note on REQUIREMENTS.md status:** The traceability table in REQUIREMENTS.md still shows IN-01..IN-05, RES-01..RES-04, SCAF-01, SCAF-06 as "Pending". This is a documentation tracking issue only — the implementations are complete and all 46 tests pass. The status column in that table should be updated to "Complete" for these 11 requirements.

---

_Verified: 2026-04-30T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
