# OSBuilder Pre-flight — Reference Index

> Per-OS install matrices, decision trees, and edge-case notes for `scripts/preflight_check.py`.
> Loaded on-demand by the Architect role at planning time. NOT pulled into `SKILL.md`
> (which is locked at ≤ 200 lines; see Phase 1 Plan 01-02).

## What pre-flight does

Before OSBuilder builds anything, it ensures the user's machine has the five required
tools installed:

- **Node 20+** (Next.js / pnpm / build tools)
- **Python 3.13+** (OSBuilder helper scripts; `state_writer.py`, `preflight_check.py`)
- **git** (version control; required for ship-to-private-GitHub flow in Phase 6)
- **gh** (GitHub CLI; private-repo creation in Phase 6)
- **Docker** (Postgres-via-compose for multi-user web apps; opt-out via `--no-docker` for SQLite-only single-user CLI builds)

## How pre-flight works

1. **Detection-first** — probe `~/.nvm`, `~/.pyenv`, `~/.mise`, `~/.asdf`, `~/.volta`, `~/.fnm`
   BEFORE proposing any install. If a version manager is detected for Node or Python,
   refuse to clobber. (See [Pitfall 13 — preflight breaks user system](../../.planning/research/PITFALLS.md).)
2. **Plan + dry-run preview** — `preflight_check.py preview` prints the install batch
   (PRE-05); no state change.
3. **Single confirmation** — one `[y/N]` prompt covers the whole batch (PRE-02).
4. **Atomic install-log + auto-rollback** — every action records `started_at` to
   `~/.osbuilder/install-log.json` BEFORE invoking the package manager. On any failure,
   the batch rolls back in reverse (PRE-04). Phase 2 SC #3.
5. **Uninstall path** — `python scripts/uninstall.py` reads the same log and reverses
   every action OSBuilder ever took (PRE-06). Phase 2 SC #4.

## Per-OS reference matrices

- [macos.md](./macos.md) — Homebrew install matrix, OrbStack as default Docker runtime, system-Python pitfall, transitive-deps caveat
- [linux.md](./linux.md) — apt + dnf decision tree, ID_LIKE detection rationale, sudo prompt UX, unsupported-distro refusal flow
- [windows.md](./windows.md) — winget primary + scoop fallback, PATH-refresh two-mode pattern, Docker Desktop license note, nvm-windows %APPDATA% caveat

## Handoff from bootstrap

`scripts/bootstrap.sh` and `scripts/bootstrap.ps1` install Python 3 if missing,
then re-exec into `state_writer.py`. They do NOT run preflight. The handoff is:

1. Bootstrap finishes; `state_writer.py read` returns either uninitialized (`current_role: PM`)
   or partially populated state.
2. `/osbuilder` (the skill router) sees `next_action: gather-requirements` AND no
   `~/.osbuilder/install-log.json` AND runs `preflight_check.py preview` next.
3. User confirms; preflight runs; OSBuilder proceeds to intake (Phase 3 work).

This handoff is documented HERE (not in SKILL.md) per D-13 to keep SKILL.md ≤ 200 lines.

## --no-docker mode (PRE-07)

Pass `--no-docker` to `/osbuilder` (or directly to `preflight_check.py install`).
Preflight skips Docker detection AND prompt; the choice persists to
`~/.osbuilder/preflight-config.json` so a `/clear`'d session re-running preflight
still respects it. Use case: Windows users who want SQLite-only single-user CLI
builds without Docker Desktop license friction.

## Known follow-up (deferred to Phase 8)

- `install.sh` (Phase 1) does not yet copy `preflight_check.py` and `uninstall.py`
  to `~/.claude/skills/osbuilder/scripts/`. During Phase 2 development, the local
  repo IS the installed copy. Phase 8 (publish-bar) updates `install.sh` to copy
  these as part of the open-source-publish polish.

## See also

- `.planning/phases/02-pre-flight-installer-cross-platform/02-RESEARCH.md` — full
  research output that informed this design
- `.planning/research/STACK.md` §"Pre-flight Installer — Cross-Platform Compatibility Matrix" — verified package IDs
- `.planning/research/PITFALLS.md` §13 (preflight breaks system) and §14 (cross-platform script breakage)
