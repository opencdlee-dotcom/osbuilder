# OSBuilder Examples Gallery

Real apps OSBuilder built end-to-end from a plain-English paragraph. Each
example shows the original spec, before/after screenshots (where available),
and a link to the resulting (private or public-mirror) GitHub repo.

> **Pitfall 5 guard:** every example uses a different playbook to demonstrate
> OSBuilder's range. We refuse "5 TODO-list variants" filler.

## Current examples

| # | Example | Playbook | Spec | Repo |
|---|---------|----------|------|------|
| 1 | TODO web app | web | [SPEC.md](01-todo-web/SPEC.md) | [repo-url.txt](01-todo-web/repo-url.txt) |
| 2 | Photo library CLI organizer | cli | [SPEC.md](02-cli-photo-organizer/SPEC.md) | [repo-url.txt](02-cli-photo-organizer/repo-url.txt) |
| 3 | FastAPI document summarizer | ai-service | [SPEC.md](03-fastapi-summarizer/SPEC.md) | [repo-url.txt](03-fastapi-summarizer/repo-url.txt) |

Repo-root paths for cross-referencing from elsewhere in the codebase:

- `examples/01-todo-web/SPEC.md`
- `examples/02-cli-photo-organizer/SPEC.md`
- `examples/03-fastapi-summarizer/SPEC.md`

## Repo URL placeholders

A `repo-url.txt` containing `NOT_PUBLISHED` means the example's SPEC has been
documented but a real OSBuilder build has not yet produced a GitHub repo for
it (e.g., the build is gated on Phase 6 / Phase 7 completion of OSBuilder
itself). The manual UAT in
`.planning/milestones/v1.0-phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md` row 4 tracks
the upgrade-to-real-URL milestone.

Once a real OSBuilder build produces a repo URL, replace the placeholder
with the literal URL (must match `^https://github\.com/`).

## Adding a new example

1. Run OSBuilder against a paragraph describing the new app:
   `/osbuilder I want a <description>`
2. Note the inferred playbook (from `state.md` `playbook` field or from
   OSBuilder's narration).
3. Create the example directory: `examples/NN-slug/` (NN = next number,
   zero-padded; slug = short kebab-case description)
4. Copy the resulting derived_spec.md → `examples/NN-slug/SPEC.md`; flesh
   out the before/after sections with screenshots.
5. Capture 2-3 screenshots → `examples/NN-slug/screenshots/`. Keep PNGs
   compressed (<= 200KB each) per Pitfall in 08-RESEARCH.md.
6. Write the resulting repo URL into `examples/NN-slug/repo-url.txt`. If
   the repo is private and you don't want to publish a mirror yet, use
   `NOT_PUBLISHED`.
7. Add a row to the table above, preserving the playbook-distinctness rule
   (Pitfall 5).

## Target

QUAL-04 minimum is 3 examples; target is 5. The next two candidate
playbooks for examples 4 and 5 are:

- **04-tauri-tray-app** (desktop playbook — Tauri 2 + React)
- **05-hub-platform-mini** (hub-platform — top-level CLAUDE.md routing)

These are deferred because Phase 6 (ship-to-private-github) and Phase 7
(additional playbooks) need to ship before real built apps exist for desktop
and hub-platform; until then the SPEC.md alone would not have a real repo
to point to.

## See also

- [`../README.md`](../README.md) — main project README (links to this gallery)
- [`../references/playbooks/`](../references/playbooks/) — per-playbook scaffolder docs
- [`../.planning/milestones/v1.0-phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md`](../.planning/milestones/v1.0-phases/08-skill-quality-publish-bar/08-HUMAN-UAT.md) row 4 — manual UAT for "examples were really built"
