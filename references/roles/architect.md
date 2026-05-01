# OSBuilder Architect Role — Narration Brief

> Reference for the Architect role. Loaded at module import by `scripts/narration.py`.
> Owns step 1 in the GSD phase loop: `/gsd-plan-phase` and stack research.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [ARCHITECT] {action}...
ok: [ARCHITECT] {action} ✓
fail: [ARCHITECT] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the architect. I figure out the shape of the build and pick the best set of tools so the work can start on solid ground.

## Per-Step Copy

/gsd-plan-phase:
  banner: Planning out the build
  tutor: I broke the work into a list of small steps the team can do one at a time.

stack-research:
  banner: Choosing the right tools
  tutor: I picked the best set of tools for your app based on what works well together and is well-supported.

plan-lock:
  banner: Confirming the build plan
  tutor: I read through the plan and made sure each step has a clear goal before we start building.

design-review:
  banner: Reviewing the overall shape
  tutor: I looked at how the parts of your app fit together to catch problems before any code is written.

## Failure Copy

/gsd-plan-phase: Architect could not finish the plan. Details below.
stack-research: Architect could not pick a complete set of tools. Details below.
plan-lock: Architect thinks the plan still has gaps. Details below.
design-review: Architect spotted a problem in how the parts fit together. Details below.
