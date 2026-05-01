# OSBuilder Backend Role — Narration Brief

> Reference for the Backend role. Loaded at module import by `scripts/narration.py`.
> Owns step 3 when the current phase is API or data work.
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [BACKEND] {action}...
ok: [BACKEND] {action} ✓
fail: [BACKEND] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the backend developer. I build the part of your app that stores and looks up your data behind the scenes.

## Per-Step Copy

execute-api:
  banner: Building the data layer
  tutor: I am wiring up the part of your app that saves and looks up information.

build-route:
  banner: Setting up how data moves
  tutor: I am setting up the paths your app uses to send data back and forth.

build-schema:
  banner: Setting up the data storage
  tutor: I am deciding what kinds of information your app needs to remember and how to lay it out.

migrate-data:
  banner: Moving data into place
  tutor: I am putting your stored information into the new shape so the app can read it.

## Failure Copy

execute-api: Backend could not finish wiring up the data layer. Details below.
build-route: Backend ran into a problem setting up a data path. Details below.
build-schema: Backend could not lay out the storage shape. Details below.
migrate-data: Backend hit a snag moving stored information into place. Details below.
