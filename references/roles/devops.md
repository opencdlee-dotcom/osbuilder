# OSBuilder DevOps Role — Narration Brief

> Reference for the DevOps role. Loaded at module import by `scripts/narration.py`.
> Owns step 2 (registry verify gate) and project scaffolding.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [DEVOPS] {action}...
ok: [DEVOPS] {action} ✓
fail: [DEVOPS] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the operations person. I set up the project files, install the parts your app needs, and make sure the build environment is safe.

## Per-Step Copy

/gsd-execute-phase:
  banner: Running the build steps
  tutor: I am working through the list of small steps the architect laid out, one at a time.

registry-gate:
  banner: Checking the tools list for safety
  tutor: I am making sure every outside piece your app pulls in is a real, trusted package — not a fake one made to trick the build.

scaffold:
  banner: Setting up your project files
  tutor: I am creating the basic folder layout and starter files your app needs to run.

install-deps:
  banner: Getting your app's requirements ready
  tutor: I am downloading the outside pieces your app needs so it can actually run on this machine.

## Failure Copy

/gsd-execute-phase: DevOps could not finish a build step. Details below.
registry-gate: DevOps blocked an outside piece because it could not be verified as real. Details below.
scaffold: DevOps could not set up your project files. Details below.
install-deps: DevOps could not download one of the outside pieces your app needs. Details below.
