# Demo Recording Checklist

Reproducible workflow for recording the OSBuilder 60-second demo.
Re-run this checklist any time the README's `assets/demo/osbuilder-demo.gif`
needs to be re-rendered (e.g., after a stack version bump that changes
visible terminal output).

## Goal

A <= 60 second asset showing OSBuilder running paragraph -> working app on
private GitHub, end-to-end, with no cuts hiding friction.

## Pre-recording (security — Pitfall 2 from 08-RESEARCH.md)

- [ ] Use a throwaway `gh auth login` profile, NOT your primary GitHub account
- [ ] Run `history -c` (or close + reopen the terminal) to clear shell history
- [ ] Confirm `printenv | grep -iE "(token|secret|password|key)"` returns empty
- [ ] If the demo will use a real `.env`, redact it BEFORE recording — leave
      only `.env.example` content visible
- [ ] Confirm `gh auth status` shows the throwaway account (not the real one)
- [ ] Set terminal theme to a vanilla default (Terminal.app default on macOS,
      gnome-terminal default on Linux) — exotic themes render unpredictably in GIF

## Recording — option A: asciinema + agg (recommended)

1. Install asciinema: `brew install asciinema` (macOS) or `pipx install asciinema` (Linux)
2. Install agg: `cargo install --git https://github.com/asciinema/agg`
3. Start recording: `asciinema rec assets/demo/osbuilder-demo.cast`
4. Run the demo (see "Demo script" below)
5. Exit recording: `Ctrl-D` or `exit`
6. Convert to GIF: `agg --speed 2 assets/demo/osbuilder-demo.cast assets/demo/osbuilder-demo.gif`
   (`--speed 2` post-processes a 2-minute real run down to ~60s; capture every
   state visibly per Pitfall 6 — speed up but don't cut)

## Recording — option B: screen-recorder + ffmpeg fallback

If asciinema is unavailable, capture via:
- macOS: QuickTime -> File -> New Screen Recording -> save .mov -> `ffmpeg -i in.mov -vf "fps=10,scale=800:-1" assets/demo/osbuilder-demo.gif`
- Linux: SimpleScreenRecorder -> save .mp4 -> `ffmpeg -i in.mp4 -vf "fps=10,scale=800:-1" assets/demo/osbuilder-demo.gif`
- Windows: ScreenToGif -> save .gif directly to assets/demo/osbuilder-demo.gif

Note: option B does NOT produce an asciinema `.cast` source. Document that in
this checklist post-recording so future maintainers know the cast file is not
in sync with the GIF.

## Demo script (the 60s itself)

Pick a single, simple intake — TODO web app is the canonical example
(matches Phase 3 SC-1 verbatim). Run from a clean working directory.

1. Type: `/osbuilder I want a TODO web app where I can add tasks and check them off`
2. Show OSBuilder picking the web playbook (1 line of narration)
3. Show preflight check (1-2 lines: "all prerequisites already installed")
4. Show scaffolder running: `pnpm create next-app...` (compressed via --speed)
5. Show GSD plan-phase emitting plan files (1-2 lines)
6. Show execute-phase landing the first phase (compressed)
7. Show verify pass (1 line: "TODO list renders, check-off works")
8. Show `gh repo create --private` + final URL printed
9. End frame: a real GitHub repo URL visible (private — that's expected)

Total runtime AFTER `--speed` post-processing: <= 60 seconds.

## Post-recording sanity checks

- [ ] `ffprobe assets/demo/osbuilder-demo.gif 2>&1 | grep Duration` (or replay) confirms <= 60s
- [ ] `du -sh assets/demo/osbuilder-demo.gif` reports <= 5MB (GitHub's recommended GIF cap)
- [ ] Replay the GIF and confirm: NO `gh auth token` visible, NO `.env` contents visible, NO ssh key fragments visible
- [ ] If GIF was produced via asciinema, also commit `osbuilder-demo.cast` (the source)
- [ ] Replay end frame: a real GitHub repo URL is visible (proof of end-to-end)
- [ ] Run `uv run pytest scripts/tests/test_readme.py::test_demo_asset_present` — should pass

## When the GIF needs re-rendering

Triggers:
- SKILL.md narration text changes (terminal output looks different)
- Stack defaults change (Next.js 17 lands; demo still shows 16)
- A new playbook becomes the demo subject (TODO web -> AI summarizer)

Re-run this entire checklist. The asciinema `.cast` source is preserved so
you can replay the original at any time via `asciinema play
assets/demo/osbuilder-demo.cast`.

## See also

- `.planning/phases/08-skill-quality-publish-bar/08-RESEARCH.md` Pitfall 2 (security), Pitfall 6 (unedited honesty)
- `.planning/phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md` row 2 (manual gate for honesty review)
- README.md `## 60-Second Demo` section (where the GIF embeds)
