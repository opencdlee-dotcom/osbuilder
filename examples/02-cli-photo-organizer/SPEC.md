# Example 02: Photo library CLI organizer

**Playbook:** cli
**Built:** <pending — placeholder example until OSBuilder Phase 6+7 complete>
**Repo:** [repo-url.txt](repo-url.txt)

## Original paragraph (intake)

> "I want a command-line tool to organize my photo library. It should be
> able to scan a folder, tag photos by date, and let me search them later.
> It should remember what it tagged across runs."

## OSBuilder's expected interpretation

- **App type:** cli
- **Playbook:** `references/playbooks/cli.md` (Python + Typer + Rich + SQLite)
- **Inferred from keywords:** "command-line tool" (cli), "remember across
  runs" (SQLite persistence per Phase 7 SC-2)
- **Notable refusals:** none — single-user local tool fits the cli playbook
  exactly (no Dockerfile per CLI playbook decision in 07-03)
- **Production-ready flag:** OFF (single-user local tool)

## Before / After

| Stage | What it looked like | Screenshot |
|-------|---------------------|------------|
| Intake (paragraph) | (the paragraph above) | — |
| Derived spec | features list + Python + Typer stack | `screenshots/derived-spec.png` (pending) |
| Scaffolded project | uv project + typer + rich + sqlite | `screenshots/scaffold-tree.png` (pending) |
| Working tool | `uv run photo-organizer scan ~/Pictures` | `screenshots/running.png` (pending) |
| SQLite persistence | second run shows tagged-photo recall | `screenshots/persistence.png` (pending) |
| Private GitHub | `gh repo create --private` URL | `screenshots/repo-view.png` (pending) |

## How OSBuilder built this (expected sequence)

1. **PM** gathered requirements; confirmed single-user (no shared library);
   asked about photo formats (sensible default: JPEG + PNG + HEIC).
2. **Architect** chose Python + Typer + Rich + SQLite per the CLI playbook;
   NO Dockerfile per CLI playbook refuse-list (single-user local tool).
3. **DevOps** ran `uv init` + `uv add typer rich` (NOT `typer[all]` per
   07-03 D-13/D-14 — rich is hard-deped from typer 0.25.1+).
4. **Frontend** N/A (CLI tool — no frontend role in this build).
   **Backend** wired SQLite schema + the `scan` / `tag` / `search`
   subcommands; **DevOps** stamped python.yml CI workflow (no Dockerfile).
5. **QA** + **Reviewer** as usual.
6. **Tech Writer** wrote README documenting the CLI surface in plain English.
7. **DevOps** pushed to private GitHub.

## Status

This example is currently a SPEC placeholder. It will be upgraded to a real
built repo once OSBuilder Phase 6 (ship-to-private-github) completes and a
real run produces a real URL. `repo-url.txt` will be flipped from
`NOT_PUBLISHED` to the real URL at that point.

## See also

- [`../../references/playbooks/cli.md`](../../references/playbooks/cli.md) — cli playbook reference
- [`../README.md`](../README.md) — gallery index
