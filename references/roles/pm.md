# OSBuilder PM Role — Narration Brief

> Reference for the PM role. Loaded at module import by `scripts/narration.py`.
> Owns step 0 in the GSD phase loop: `/gsd-spec-phase` and intake calls.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [PM] {action}...
ok: [PM] {action} ✓
fail: [PM] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the project manager. I figure out what you want to build and write it down so the rest of the team knows the goal.

## Per-Step Copy

/gsd-spec-phase:
  banner: Locking in your requirements
  tutor: I wrote down everything you told me about your app so the build team knows exactly what to make.

/gsd-new-project --auto:
  banner: Starting a new project
  tutor: I am setting up a fresh workspace and writing down the goal you described.

intake-paragraph:
  banner: Reading your description
  tutor: I read what you wrote and pulled out the key things you said you wanted.

intake-structured:
  banner: Reading your spec
  tutor: I read your spec file and listed the features and who will use the app.

spec-lock:
  banner: Confirming the plan
  tutor: I made sure the description was clear enough to build from before handing it off.

phase-complete:
  banner: Wrapping up this round of work
  tutor: I checked off everything that was promised this round and lined up what comes next.

## Failure Copy

/gsd-spec-phase: PM ran into a problem locking the requirements. Details below.
/gsd-new-project --auto: PM could not start the project. Details below.
intake-paragraph: PM had trouble reading your description. Details below.
intake-structured: PM could not read your spec file. Details below.
spec-lock: PM thinks the description still has too many open questions. Details below.
phase-complete: PM could not wrap up this round. Details below.
