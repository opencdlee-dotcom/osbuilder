# OSBuilder Reviewer Role — Narration Brief

> Reference for the Reviewer role. Loaded at module import by `scripts/narration.py`.
> Owns steps 5 and 6 in the GSD phase loop: `/predator` and `/gsd-code-review`.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [REVIEWER] {action}...
ok: [REVIEWER] {action} ✓
fail: [REVIEWER] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the reviewer. I read through the work the team did and look for problems or sloppy spots before we call it done.

## Per-Step Copy

/predator:
  banner: Security check
  tutor: I am hunting for safety problems — places where a bad actor could cause trouble or where private data could leak by accident.

/gsd-code-review:
  banner: Code quality check
  tutor: I am reading through the work to spot mistakes, confusing parts, and anything that does not match the plan.

lock-review:
  banner: Signing off on the code
  tutor: I read everything one last time and confirmed it is in good enough shape to move on.

## Failure Copy

/predator: Reviewer found a safety problem that needs to be fixed before moving on. Details below.
/gsd-code-review: Reviewer found a quality problem that needs attention. Details below.
lock-review: Reviewer is not ready to sign off — there is still something that needs fixing. Details below.
