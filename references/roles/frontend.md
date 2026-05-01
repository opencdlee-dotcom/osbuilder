# OSBuilder Frontend Role — Narration Brief

> Reference for the Frontend role. Loaded at module import by `scripts/narration.py`.
> Owns step 3 when the current phase is UI work (homepage, screens, pages).
> Plain-English banner + tutor copy — no jargon in default-mode sections.

## Banner Templates

start: [FRONTEND] {action}...
ok: [FRONTEND] {action} ✓
fail: [FRONTEND] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: I am the frontend developer. I build the screens and buttons your users will actually see and click on.

## Per-Step Copy

execute-ui:
  banner: Building your screens
  tutor: I am putting together the pages people will see when they open your app.

build-component:
  banner: Building a piece of your app
  tutor: I am creating one small piece of the screen — like a button, a card, or a form.

build-page:
  banner: Building a page in your app
  tutor: I am putting together a whole page that someone using your app can visit.

style-pass:
  banner: Polishing how it looks
  tutor: I am making the layout, spacing, and colors look clean so the app feels finished.

## Failure Copy

execute-ui: Frontend could not finish building a screen. Details below.
build-component: Frontend ran into a problem with a small piece of the screen. Details below.
build-page: Frontend could not finish a page. Details below.
style-pass: Frontend hit a snag while polishing how the app looks. Details below.
