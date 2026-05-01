# OSBuilder Tech Writer Role — Narration Brief

> Reference for the Tech Writer role. Loaded at module import by `scripts/narration.py`.
> Owns step 9 in the GSD phase loop: `/gsd-docs-update` and the humanizer pipeline.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [TECH-WRITER] {action}...
ok: [TECH-WRITER] {action} ✓
fail: [TECH-WRITER] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the tech writer. I write the README — the one-page guide someone uses to set your app up and run it on their own machine.

## Per-Step Copy

/gsd-docs-update:
  banner: Updating your documents
  tutor: I am updating the project notes so they describe what your app actually does right now.

generate-readme:
  banner: Writing your README
  tutor: I am writing the one-page guide that explains what your app is and how to run it on a new computer.

check-humanizer:
  banner: Checking the README reads naturally
  tutor: I am reading the guide back to make sure it sounds like a person wrote it, not a robot.

rewrite-readme:
  banner: Polishing the README
  tutor: I am cleaning up the guide so it is short, clear, and easy to follow.

## Failure Copy

/gsd-docs-update: Tech Writer could not finish updating your documents. Details below.
generate-readme: Tech Writer could not write the README. Details below.
check-humanizer: Tech Writer thought the README still sounded too stiff. Details below.
rewrite-readme: Tech Writer hit a snag while polishing the guide. Details below.
