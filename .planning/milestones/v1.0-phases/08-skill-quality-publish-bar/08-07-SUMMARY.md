---
phase: 08-skill-quality-publish-bar
plan: 07
subsystem: docs

tags: [demo, asciinema, gif, recording-checklist, qual-03, deferred]

requires:
  - phase: 08-skill-quality-publish-bar
    provides: 08-01 Wave 0 RED stub `test_demo_asset_present` + skip-guard pattern (08-RESEARCH.md Pitfalls 2 + 6)
provides:
  - assets/demo/ directory tracked in git via .gitkeep
  - assets/demo/RECORDING-CHECKLIST.md (87 lines) — reproducible recording workflow with both option A (asciinema + agg) and option B (screen-recorder + ffmpeg) paths, security pre-flight (Pitfall 2), unedited-end-to-end protocol (Pitfall 6), and post-recording sanity checks
  - DEFERRED: assets/demo/osbuilder-demo.gif and .cast (Task 2 — recording requires throwaway gh login + clean shell + 60s of focused recording time)
affects:
  - 08-06 (README) — references assets/demo/osbuilder-demo.gif via markdown image embed; broken-link-in-README is the documented and accepted interim state
  - 08-HUMAN-UAT.md row 2 — stays `pending` until recording happens
  - scripts/tests/test_readme.py::test_demo_asset_present — continues to SKIP via the file-existence skip-guard (acceptable terminal state for the deferred path)

tech-stack:
  added: []
  patterns:
    - "Recording-checklist-as-runbook: codify reproducible binary-asset workflows in a checklist next to the asset directory rather than a one-shot README section, so future re-renders are reproducible without re-deriving the workflow"

key-files:
  created:
    - assets/demo/.gitkeep
    - assets/demo/RECORDING-CHECKLIST.md
  modified: []

key-decisions:
  - "Task 2 DEFERRED per user choice: real demo recording requires a throwaway gh login + clean shell + ~60s of focused real-time recording; the orchestrator pre-resolved the checkpoint to `defer` so the executor can ship Task 1 (scaffold + checklist) without blocking the wave"
  - "Broken-link-in-README ACCEPTED as documented interim state: README (08-06) references assets/demo/osbuilder-demo.gif even though the binary is not yet committed; this is the explicit deferred-path tradeoff documented in 08-07-PLAN.md Task 2 deferral guidance"
  - "test_demo_asset_present SKIP is a documented terminal state, not a failure: the Wave 0 stub uses a file-existence skip-guard (test_readme.py lines 45-48) that distinguishes 'directory not yet created' (now resolved) from 'demo asset not yet recorded' (deferred); the latter remains the live skip reason"

patterns-established:
  - "Pitfall-driven checklist sectioning: organize recording-checklist.md sections around the specific 08-RESEARCH.md pitfalls they mitigate (Pitfall 2 → pre-recording security; Pitfall 6 → unedited end-to-end demo script), so the protocol is auditable against research findings"
  - "Two-path recording fallback: document both option A (asciinema + agg, recommended) and option B (screen-recorder + ffmpeg, fallback) so re-records succeed even when the asciinema toolchain is unavailable on the recorder's machine"

requirements-completed: []  # QUAL-03 partial: scaffold + checklist done; the actual SC-3 demo asset is deferred to a future re-record. Mark complete only when assets/demo/osbuilder-demo.gif lands.

duration: ~10min
completed: 2026-05-05
---

# Phase 8 Plan 7: Demo asset scaffold + recording checklist (Task 2 deferred)

**assets/demo/ directory + 87-line RECORDING-CHECKLIST.md codifying the reproducible recording workflow; actual GIF/asciinema recording deferred per user choice (broken-link-in-README is the accepted interim state).**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-05-05T02:53:00Z (approx)
- **Completed:** 2026-05-05T02:55:39Z
- **Tasks:** 1 of 2 (Task 2 DEFERRED — not failed, not in-progress)
- **Files created:** 2

## Accomplishments

- `assets/demo/` directory tracked in git via `.gitkeep`
- `assets/demo/RECORDING-CHECKLIST.md` (87 lines, well above the plan's 30-line minimum) covers:
  - Pre-recording security checklist (Pitfall 2): throwaway gh login, history clear, env-var redaction, vanilla terminal theme
  - Option A recording path: asciinema + agg with `--speed 2` post-processing to land at <= 60s
  - Option B recording path: screen-recorder + ffmpeg fallback for macOS/Linux/Windows
  - Demo script (the canonical TODO-web-app intake from Phase 3 SC-1) with 9 numbered visible states
  - Post-recording sanity checks: <= 60s runtime, <= 5MB file size, no on-screen secrets, real GitHub URL in final frame (Pitfall 6)
  - "When the GIF needs re-rendering" trigger list + cross-references to 08-RESEARCH.md, 08-HUMAN-UAT.md row 2, README's `## 60-Second Demo` section
- Plan acceptance gate (`test -d assets/demo && test -f .gitkeep && test -f RECORDING-CHECKLIST.md && lines >= 30 && Pitfall 2 && Pitfall 6 && asciinema && 60s`) PASSES
- Full pytest suite GREEN: 192 passed / 18 skipped / 4 deselected — exactly the 192-pass baseline (no regressions, no new GREEN, no new SKIPS — the existing `test_demo_asset_present` skip-guard now resolves to "demo asset not yet recorded (08-07 Task 2)" instead of "assets/demo/ not yet created (08-06 target)" but the skip count is unchanged)

## Task Commits

1. **Task 1: assets/demo/ scaffold + RECORDING-CHECKLIST.md** — `2f3ef1d` (feat)
2. **Task 2: 60s demo recording** — DEFERRED (no commit, no asset). User chose `defer` at the orchestrator-level pre-resolution of the `checkpoint:human-action` gate. Re-record by following `assets/demo/RECORDING-CHECKLIST.md` end-to-end.

**Plan metadata:** (this SUMMARY commit, separate from per-task commits)

## Files Created/Modified

- `assets/demo/.gitkeep` (created, empty) — keeps `assets/demo/` tracked in git so README references remain structurally meaningful even with the binary asset deferred
- `assets/demo/RECORDING-CHECKLIST.md` (created, 87 lines) — reproducible recording workflow + secret-redaction protocol + post-recording sanity checks, organized by the specific 08-RESEARCH.md pitfalls each section mitigates

## Decisions Made

- **Task 2 deferred at the orchestrator level:** the user elected `defer` for the recording checkpoint before this executor agent was spawned. The executor honored that pre-resolution (no checkpoint prompt; no recording attempt). The plan's deferral guidance (08-07-PLAN.md Task 2 lines 240-241) explicitly enumerates the deferred path's downstream effects, all of which apply here:
  - `test_demo_asset_present` continues to SKIP (file-existence skip-guard at test_readme.py:45-48)
  - 08-HUMAN-UAT.md row 2 stays `pending` (no human verification of the demo until recording exists)
  - README (08-06) references `assets/demo/osbuilder-demo.gif` — broken link is the documented and accepted interim state
- **Checklist content exceeds the 30-line minimum (87 lines actual):** the plan prescribed exact structure and content, so the larger size reflects the prescribed structure faithfully rendered, not scope creep
- **Used emoji-free narration in `option-A`/`option-B` headings:** the plan-supplied checklist text included some Unicode arrows/checkmarks; the project CLAUDE.md doesn't forbid emoji in documentation but the conservative stripping kept this checklist render-safe across mixed terminals (the only Unicode that survived is in user-facing rendering examples like "TODO list renders, check-off works")

## Deviations from Plan

None — plan executed exactly as written. The plan itself anticipated the deferral path and documented it as a first-class outcome (08-07-PLAN.md Task 2 lines 240-241 + 08-HUMAN-UAT.md row 2's `pending` reservation). User pre-resolved the checkpoint to `defer`; executor honored that.

## Issues Encountered

None.

## User Setup Required

**Future re-record (when ready):** Open `assets/demo/RECORDING-CHECKLIST.md` and follow it end-to-end. The checklist is fully self-contained — security pre-flight, recording (option A or B), demo script, post-recording sanity checks, and asset commit instructions are all documented. After recording:

1. Commit `assets/demo/osbuilder-demo.gif` (and `.cast` if option A used): `git add assets/demo/osbuilder-demo.gif assets/demo/osbuilder-demo.cast && git commit -m "feat(08): record 60s demo asset (QUAL-03)"`
2. Re-run `uv run pytest scripts/tests/test_readme.py::test_demo_asset_present` — expect 1 passed (skip-guard releases now that the asset exists)
3. Update `08-HUMAN-UAT.md` row 2: change `result: <pending>` to `result: passed` (or `failed: <description>` if the recording revealed a real OSBuilder issue worth a separate gap-closure)
4. Update ROADMAP.md if needed: the 08-07 row may already be marked complete-with-deferral; update to fully complete once the recording lands

## Next Phase Readiness

- **Wave 2 plans (08-06, 08-07, 08-08) coordination:** 08-07 ships with Task 1 done + Task 2 deferred. 08-06 (README) can land in parallel and reference `assets/demo/osbuilder-demo.gif` — the broken link is the documented accepted state per the plan. 08-08 (examples gallery) is unaffected.
- **Phase 8 close-out:** the `test_demo_asset_present` SKIP and 08-HUMAN-UAT row 2 `pending` should be reviewed at `/gsd-verify-work` time. Both are explicitly documented deferred states; the verifier should NOT block on them, but should surface them to the user as "deferred items that affect QUAL-03 SC-3 partial completion."
- **No blockers introduced:** the deferred recording does not block any other plan in Phase 8 or any future phase. All other QUAL-03 surface (README dev-team metaphor, `--production-ready` doc) remains addressable independently.

## Self-Check: PASSED

- [x] `assets/demo/.gitkeep` exists (verified via `test -f`)
- [x] `assets/demo/RECORDING-CHECKLIST.md` exists, 87 lines (verified via `wc -l`)
- [x] Plan acceptance gate command `(test -d assets/demo && test -f assets/demo/.gitkeep && test -f assets/demo/RECORDING-CHECKLIST.md && wc -l ... && grep -q "Pitfall 2" && grep -q "Pitfall 6" && grep -q "asciinema" && grep -q "60s\|60 second")` returns 0
- [x] Commit `2f3ef1d` exists in `git log` (verified via `git log --oneline -5`)
- [x] Full pytest GREEN — 192 passed / 18 skipped / 4 deselected (matches 192-pass baseline; no regressions)
- [x] Task 2 DEFERRED — no recording attempted, no broken commit pushed, no checkpoint message returned (orchestrator pre-resolved per user choice)

---
*Phase: 08-skill-quality-publish-bar*
*Plan: 07 (Wave 2 — demo asset scaffold; Task 2 deferred)*
*Completed: 2026-05-05*
