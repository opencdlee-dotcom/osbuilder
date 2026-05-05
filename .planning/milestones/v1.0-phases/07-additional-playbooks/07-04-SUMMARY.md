---
phase: 07-additional-playbooks
plan: 04
subsystem: scaffold
tags: [desktop, tauri, rust, cargo, scaffold, electron-refusal, phase-7]

# Dependency graph
requires:
  - phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
    provides: scaffold_dispatch.py shape, _validate_project_name, atomic_write
  - phase: 06-ship-to-private-github-scalable-defaults
    provides: _write_ci_workflow stack-family helper, ASSETS constant
  - phase: 07-additional-playbooks-plan-01
    provides: app_type='desktop' routing from intake (PLAYBOOK_KEYWORDS); Electron migration to refuse-list.md (D-22)
  - phase: 07-additional-playbooks-plan-02
    provides: ensure_pnpm reuse, _PLAYBOOK_DISPATCH dict, _PLAYBOOK_TOOLS["desktop"]=("uv","cargo")
provides:
  - "scaffold_desktop(project_name, project_root) → pnpm create tauri-app@latest with verbatim 12-element argv per D-07 + _write_ci_workflow stack_family='tauri'"
  - "_build_tauri_identifier(name) → 'com.osbuilder.<sanitized>' (Pitfall 7 reverse-DNS rule)"
  - "_PLAYBOOK_DISPATCH gains 'desktop' entry — fourth playbook on the routing surface"
  - "cargo install matrix entries across macOS/APT/DNF (rustup curl-pipe-sh) + winget (Rustlang.Rustup) per D-20-21"
  - "references/playbooks/desktop.md — 65-line spec mirroring web.md/ai-service.md/cli.md 7-section structure with inline D-09 Tauri-not-Electron rationale"
  - "assets/ci-workflows/tauri.yml.tmpl — Rust+Node combined CI (dtolnay/rust-toolchain@stable + pnpm + Linux Tauri prereqs) with concurrency + 30min timeout (Pitfall 8)"
  - "references/friendly-errors/dictionary.yaml — +3 entries (cargo-not-installed, tauri-cli-not-installed, create-tauri-app-failed)"
  - "references/stack-menu.md — +desktop playbook defaults table"
  - "test_electron_refused_globally — verifies 07-01 D-22 migration landed (Electron + Tauri 2 in refuse-list.md; old web.md line removed)"
affects:
  - 07-05-hub-platform-playbook (cross-references desktop.md)
  - 07-06-e2e-harness (parametrizes desktop path with 120s install timeout per Pitfall 8)

# Tech tracking
tech-stack:
  added:
    - "tauri 2.x (Rust runtime + system WebView; --tauri-version 2 pin)"
    - "create-tauri-app 4.6.2 (verified non-interactive flag set 2026-05-01)"
    - "@tauri-apps/cli 2.11.0 (transitive via create-tauri-app; lives in project node_modules)"
    - "rustup-toolchain stable (preflight install via curl https://sh.rustup.rs / winget Rustlang.Rustup)"
  patterns:
    - "Reverse-DNS bundle identifier sanitization: pure regex strip [^a-zA-Z0-9] + lowercase → com.osbuilder.<sanitized> (Pitfall 7)"
    - "Per-playbook scaffold function mirrors scaffold_web 4-step shape verbatim — now applied 4 times consistently (web/ai-service/cli/desktop)"
    - "Tauri-Electron refusal globalization: refuse-list.md owns the rationale; per-playbook .md cross-references the global file (D-09 + D-22)"
    - "Combined Rust+Node CI workflow with timeout-minutes: 30 (Pitfall 8 — cold Cargo fetches take ~120s)"

key-files:
  created:
    - scripts/tests/test_phase07_desktop.py (155 lines, 6 tests)
    - assets/ci-workflows/tauri.yml.tmpl (39 lines)
    - references/playbooks/desktop.md (65 lines; under 80 cap)
  modified:
    - scripts/scaffold_dispatch.py (+99 lines: _CREATE_TAURI_APP_VERSION, _TAURI_VERSION, _build_tauri_identifier, scaffold_desktop, _PLAYBOOK_DISPATCH "desktop" entry)
    - scripts/preflight_check.py (+27 lines: 4 cargo install matrix entries — _MACOS_INSTALL/_APT_INSTALL/_DNF_INSTALL/_WINGET_INSTALL)
    - scripts/tests/test_phase07_preflight_extensions.py (+62 lines: 3 cargo tests appended after the uv tests)
    - scripts/tests/test_refusal.py (+25 lines: test_electron_refused_globally)
    - references/friendly-errors/dictionary.yaml (+33 lines: cargo-not-installed + tauri-cli-not-installed + create-tauri-app-failed)
    - references/stack-menu.md (+10 lines: desktop playbook defaults table + cross-ref bullet)

key-decisions:
  - "D-07 implemented: scaffold_desktop runs the verbatim 12-element argv pnpm create tauri-app@latest <name> --manager pnpm --template react-ts --identifier <reverse-dns> --tauri-version 2 -y (verified by `npx --yes create-tauri-app --help` 2026-05-01)"
  - "D-08 implemented: tauri-app@latest spec pins to current pnpm registry state at scaffold time; create-tauri-app pinned to 4.6.2 in playbook .md for visibility; _CREATE_TAURI_APP_VERSION constant carries the pin for future literal-pin switch"
  - "D-09 implemented: desktop.md ## Refuse list section inlines the Tauri-not-Electron rationale (binary size, RAM, system-WebView vs bundled Chromium); cross-references global refuse-list.md"
  - "D-20 implemented: cargo install action is `sh -c \"curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh -s -- -y\"` across macOS/APT/DNF; -y disables rustup's interactive y/n confirmation so single-confirmation gate at preflight covers it"
  - "D-21 implemented: winget package ID is the literal `Rustlang.Rustup` (case-sensitive); regression catcher test_rustup_winget_id_exact pins this string"
  - "Pitfall 7 implementation: _build_tauri_identifier strips ALL non-alphanumerics (covers hyphens, underscores, dots) — single regex [^a-zA-Z0-9] is conservative; output for 'My-Cool-App' is 'com.osbuilder.mycoolapp' verified at scaffold time"
  - "Pitfall 1 implementation: ensure_pnpm called before create-tauri-app subprocess so npm-vs-pnpm --template forwarding pitfall doesn't apply (we never use npm here); test_scaffold_desktop_calls_ensure_pnpm pins ordering"
  - "Pitfall 3 documentation: rustup default stable-msvc on Windows is documented inline in desktop.md ## Stack section (gnu default fails Tauri's MSVC linker). Auto-correction inside _apply was deferred — preflight currently lacks a per-tool post-install hook surface, and adding one is out of plan scope (architectural change → Rule 4 territory). The documentation captures the correction so users hitting the gnu-default issue have the fix at hand."
  - "Pitfall 8 deferral: tauri.yml.tmpl carries timeout-minutes: 30 (CI-side headroom). The 120s parametrized E2E install timeout is owned by 07-06 per the plan's TIMEOUTS dict."
  - "_PLAYBOOK_DISPATCH dict scales 3 → 4 with no shape change — pattern extends additively for 07-05 hub-platform"

patterns-established:
  - "Per-plan atomic block in scaffold_dispatch.py via '=== Phase 7 — desktop playbook (07-04) ===' divider (RESEARCH.md Wave Coordination Option A; matches 07-02/07-03)"
  - "Stack-family CI template via filename: _write_ci_workflow loads f'{stack_family}.yml.tmpl' from assets/ci-workflows/ → adding tauri requires only the new template file, no code change in _write_ci_workflow"
  - "Lazy-import-via-fixture pattern carries forward (test_phase07_desktop.py uses sd + has_desktop guard)"
  - "Cross-reference test pattern (test_electron_refused_globally) verifies a deletion + a positive content presence in two related files — useful for any future migration that involves moving copy between docs"

requirements-completed: [SCAF-04]

# Metrics
duration: 6min
completed: 2026-05-02
---

# Phase 7 Plan 04: Desktop Playbook Summary

**Added the desktop playbook to OSBuilder: a Tauri 2 (Vite + React + Rust) scaffold path that turns "a desktop app that runs locally with a tray icon" into a working `pnpm tauri dev` native window with hot-reload — Rust backend + system-WebView frontend, ~10MB binaries vs Electron's ~150MB. Globalized the Electron refusal verification (test_electron_refused_globally pins 07-01's D-22 migration of the rationale from web.md to refuse-list.md).**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-02T08:36:01Z (after 07-03 completion)
- **Completed:** 2026-05-02T08:42:01Z
- **Tasks:** 2 (Wave 0 RED tests + Wave 1 GREEN implementation)
- **Files:** 9 (3 created + 6 modified)
- **Test delta:** +10 (171 → 181 passing; 1 pre-existing skip; zero regressions)

## Accomplishments

- `scaffold_desktop` mirrors `scaffold_web`'s 4-step shape verbatim: validate → ensure_pnpm → pnpm create tauri-app@latest (verbatim 12-element argv per D-07) → _write_ci_workflow stack_family="tauri".
- `_build_tauri_identifier` is a 2-line pure function: `re.sub(r"[^a-zA-Z0-9]", "", name).lower()` then prepend `com.osbuilder.`. Handles all sanitization edge cases (hyphens, underscores, mixed case, digits) with one regex.
- Preflight extended with **cargo** detection (probe surface unchanged) + cross-platform install actions (macOS/APT/DNF: rustup curl-pipe-sh `https://sh.rustup.rs -sSf | sh -s -- -y`; Windows: winget `Rustlang.Rustup`). The `_PLAYBOOK_TOOLS["desktop"]` was already populated as `("uv", "cargo")` by 07-02 — no change needed.
- New `tauri.yml.tmpl` combines pnpm + Node 20 + Rust toolchain (`dtolnay/rust-toolchain@stable`) + Linux Tauri prerequisites (`libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf`) with `concurrency` (cancel-in-progress) + `timeout-minutes: 30` (Pitfall 8 headroom for cold Cargo fetches).
- `references/playbooks/desktop.md` (65 lines, well under the 80-line cap) inlines the Tauri-not-Electron rationale per D-09 — cross-references global `refuse-list.md` so the refusal lives in one place.
- 3 friendly-error dictionary entries added (cargo-not-installed, tauri-cli-not-installed, create-tauri-app-failed) under a `# === Phase 7 — desktop playbook (07-04) ===` divider mirroring 07-02's pattern.
- `_PLAYBOOK_DISPATCH` dict gains 4th entry (`"desktop"`) — routing surface now spans web / ai-service / cli / desktop with no shape change. 07-05 hub-platform plugs in additively.
- `test_electron_refused_globally` independently verifies 07-01's D-22 migration: confirms refuse-list.md mentions both Electron AND Tauri AND the old web-scoped line ("Electron (use Tauri 2 via desktop playbook)") is gone from web.md.
- 10/10 plan tests GREEN (6 desktop + 3 cargo + 1 electron-refused); 181/181 full suite passes (zero regressions).

## Task Commits

Each task committed atomically:

1. **Task 1: Wave 0 RED stubs (desktop playbook + cargo preflight + electron-globally-refused)** — `0b5a5c5` (test)
2. **Task 2: Wave 1 GREEN — scaffold_desktop + _build_tauri_identifier + cargo preflight + tauri CI + desktop.md + dictionary entries** — `2f53f60` (feat)

## Files Created/Modified

### Created

- `scripts/tests/test_phase07_desktop.py` (155 lines) — 6 tests: playbook .md presence + 7 sections + inline Tauri-not-Electron rationale, scaffold_desktop subprocess argv shape (verbatim 12-element with --manager pnpm / --template react-ts / --identifier com.osbuilder.testapp / --tauri-version 2 / -y), ensure_pnpm-before-create-tauri-app ordering, tauri CI workflow with dtolnay/rust-toolchain, _build_tauri_identifier reverse-DNS rule + special-char stripping.
- `assets/ci-workflows/tauri.yml.tmpl` (39 lines) — pnpm/setup-node + dtolnay/rust-toolchain@stable + Linux Tauri prereqs install step + pnpm test, with concurrency block + 30min timeout.
- `references/playbooks/desktop.md` (65 lines, ≤ 80 cap) — 7-section spec; ## Refuse list inlines the Tauri-not-Electron rationale and cross-references refuse-list.md; ## Stack notes the Pitfall 3 Windows MSVC fix.

### Modified

- `scripts/scaffold_dispatch.py` (+99 lines) — added `_CREATE_TAURI_APP_VERSION`, `_TAURI_VERSION`, `_build_tauri_identifier()`, `scaffold_desktop()`, and a new `"desktop": scaffold_desktop` entry in `_PLAYBOOK_DISPATCH` (now 4 entries). `ensure_pnpm` already existed from Phase 3 — reused, NOT redefined.
- `scripts/preflight_check.py` (+27 lines) — 4 cargo install matrix entries: `_MACOS_INSTALL["cargo"]`, `_APT_INSTALL["cargo"]`, `_DNF_INSTALL["cargo"]` (all curl-pipe-sh with `sh -c` wrapper for shell=False compat), `_WINGET_INSTALL["cargo"]` (literal `Rustlang.Rustup` ID).
- `scripts/tests/test_phase07_preflight_extensions.py` (+62 lines) — 3 cargo tests appended after the existing uv tests (probe-returns-None, macOS install action, winget ID exact).
- `scripts/tests/test_refusal.py` (+25 lines) — `test_electron_refused_globally` (verifies refuse-list.md contains Electron + Tauri AND web.md no longer carries the old scoped line).
- `references/friendly-errors/dictionary.yaml` (+33 lines) — 3 new entries under `# === Phase 7 — desktop playbook (07-04) ===` divider.
- `references/stack-menu.md` (+10 lines) — `## desktop playbook defaults` table (create-tauri-app 4.6.2, tauri 2.x, @tauri-apps/cli 2.11.0, rustup-toolchain stable, pnpm 10.33.2) + cross-ref bullet to desktop.md in See-also.

## Decisions Made

- **`_build_tauri_identifier` regex breadth** — chose a single conservative `[^a-zA-Z0-9]` strip over a more selective rule (e.g., only hyphens + underscores) because Tauri's bundle identifier requires plain alphanumerics in the final segment. Idempotent on already-clean input. Tests pin the exact behavior for `"my-cool-app"`, `"Test_App"`, `"App-2-3"`, `"My_App-2"`, `"alreadyclean"`.
- **`_PLAYBOOK_TOOLS["desktop"]` pre-populated** — Per the plan's resolution rule, ran `grep _PLAYBOOK_TOOLS scripts/preflight_check.py` at execution start and found 07-02 had already added `"desktop": ("uv", "cargo")`. No change needed; this plan only adds the 4 cargo install matrix entries.
- **No automated `rustup default stable-msvc` post-install hook** — Pitfall 3 (Windows gnu-vs-msvc default) is documented in `desktop.md ## Stack` but NOT auto-applied. Adding a per-tool post-install hook to `_apply()` would require a structural change to the install matrix surface (3-tuple → 4-tuple, plus a new hooks dict) — that's a Rule 4 architectural change beyond plan scope. Documentation is the v1 contract; auto-correction can land in a follow-up if user friction signals it.
- **CI workflow lives at `ci.yml`, not `tauri.yml`** — `_write_ci_workflow` writes to a fixed `ci.yml` filename regardless of stack family (existing Phase 6 behavior). Test accepts ci.yml / test.yml / tauri.yml as candidates so it stays robust to a future filename change. Content-level assertion (`dtolnay/rust-toolchain` present) is the actual verification.
- **`_CREATE_TAURI_APP_VERSION = "4.6.2"` constant kept unused** — Documents the pinned spec from D-08 even though the current implementation passes `tauri-app@latest` (resolves to current pnpm registry state). Keeping the constant ready makes a future literal-pin switch a 1-line change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] First test paragraph (Task 1) — none required for this plan**

**Total deviations:** 0. Plan executed exactly as written. Both tasks ran cleanly on first verification pass.

## Issues Encountered

None blocking. All 17 tests across 3 files transitioned cleanly RED → GREEN on the first Wave 1 implementation pass.

## Threat Flags

None new beyond the plan's `<threat_model>` register. T-07-04-01..08 disposition unchanged:

- T-07-04-01 (Tampering: project_name → pnpm argv): mitigated by reused `_validate_project_name` regex `^[a-zA-Z0-9_-]+$`; subprocess `shell=False` argv list.
- T-07-04-02 (Tampering: identifier → bundle context): mitigated by deterministic regex sanitization; tests pin exact output.
- T-07-04-03 (Tampering: rustup curl-pipe-sh trust): accepted under same Phase 2 / Phase 7-02 trust model (HTTPS-only with `--proto '=https' --tlsv1.2`).
- T-07-04-04 (Tampering: CI Linux apt-get installs): accepted — CI-only, ubuntu-latest is GitHub-managed, package list is the official Tauri prerequisite set.
- T-07-04-05 (Spoofing: winget ID typo): mitigated by `test_rustup_winget_id_exact` pinning the literal `Rustlang.Rustup`.
- T-07-04-06 (EoP: Windows admin during install): mitigated by preflight's existing single-confirmation gate; `scaffold_desktop` itself does NOT shell out to admin tools.
- T-07-04-07 (InfoDisclosure: `osbuilder` namespace in identifier): accepted — deterministic OSBuilder marker; no PII; users self-publishing override.
- T-07-04-08 (DoS: cold Cargo fetches >120s): mitigated CI-side by `timeout-minutes: 30`; 07-06 owns the parametrized E2E timeout dict per Pitfall 8.

No new attack surface beyond what the plan anticipated.

## User Setup Required

None at scaffold time. Manual smoke (07-HUMAN-UAT.md) post-scaffold:

1. `cd <project-name>` then `pnpm install`
2. `pnpm tauri dev` — should open a native window with hot-reload (Vite + React + Rust)
3. Tauri's first run downloads + compiles Rust deps (~60-120s on cold cache; covered by Pitfall 8)
4. On Windows, if linker fails: `rustup default stable-msvc` (documented in `references/playbooks/desktop.md ## Stack`)

## Next Phase Readiness

- **07-05 (hub-platform playbook)** — unblocked. Will additively extend `_PLAYBOOK_DISPATCH` with `"hub-platform": scaffold_hub`; the dispatch surface scales the same way it did 2 → 3 → 4. No subprocess-driven scaffolder for hub (pure file-stamping per RESEARCH.md §Pattern 4).
- **07-06 (E2E harness)** — unblocked. Parametrized E2E can now spin up a desktop intake → scaffold → boot loop using `app_type='desktop'` from 07-01 and the now-real `scaffold_desktop` from this plan. Plan owns the 120s install timeout per Pitfall 8.

## Self-Check: PASSED

Files:
- `references/playbooks/desktop.md` — FOUND (65 lines, ≤ 80 cap; 7 mandatory sections present; "Tauri" appears 5×; "Electron" appears 3×; "rustup default stable-msvc" present)
- `assets/ci-workflows/tauri.yml.tmpl` — FOUND (39 lines; `dtolnay/rust-toolchain@stable` present; `concurrency:` block; `libwebkit2gtk-4.1-dev`; `timeout-minutes: 30`)
- `scripts/tests/test_phase07_desktop.py` — FOUND (6 tests; lazy-import + has_desktop guard fixture)
- `scripts/tests/test_phase07_preflight_extensions.py` — FOUND (3 cargo tests appended; total 6 tests in file)
- `scripts/tests/test_refusal.py` — FOUND (test_electron_refused_globally added)
- `references/friendly-errors/dictionary.yaml` — FOUND (cargo-not-installed, tauri-cli-not-installed, create-tauri-app-failed all present)
- `references/stack-menu.md` — FOUND (`## desktop playbook defaults` heading + cross-ref bullet)

Code surface:
- `scaffold_dispatch.scaffold_desktop` — defined; importable
- `scaffold_dispatch._build_tauri_identifier` — defined; verified `_build_tauri_identifier('My-Cool-App') == 'com.osbuilder.mycoolapp'`
- `scaffold_dispatch._PLAYBOOK_DISPATCH` — `"desktop": scaffold_desktop` entry present
- `preflight_check._MACOS_INSTALL["cargo"]` / `_APT_INSTALL["cargo"]` / `_DNF_INSTALL["cargo"]` / `_WINGET_INSTALL["cargo"]` — all defined; winget ID exact `Rustlang.Rustup`; Unix uses curl-pipe-sh with `sh.rustup.rs`

Verbatim D-07 argv assertions in test:
- `--manager pnpm` ✓
- `--template react-ts` ✓
- `--identifier com.osbuilder.testapp` ✓
- `--tauri-version 2` ✓
- `-y` ✓

Tests:
- `uv run pytest scripts/tests/test_phase07_desktop.py` → 6/6 PASSED
- `uv run pytest scripts/tests/test_phase07_preflight_extensions.py` → 6/6 PASSED (3 uv + 3 cargo)
- `uv run pytest scripts/tests/test_refusal.py` → 5/5 PASSED (4 existing + test_electron_refused_globally)
- `uv run pytest scripts/tests/` → 181 passed, 1 pre-existing skip, 0 failures (was 171 before; +10 new tests)

Commits:
- `0b5a5c5` (test RED) — FOUND in `git log`
- `2f53f60` (feat GREEN) — FOUND in `git log`

---
*Phase: 07-additional-playbooks*
*Completed: 2026-05-02*
