# OSBuilder Marker Constants Index (maintainer reference)

> IN-06 follow-up. D-05 policy says scripts MUST NOT cross-import each other —
> they duplicate small helpers verbatim instead. This index gives maintainers a
> single place to spot-check that idempotency markers across modules stay in sync.
>
> **NOT loaded at runtime.** The actual constants live in the listed files.

## Why an index?

OSBuilder uses textual markers to make file writes idempotent. Re-running a
build on an already-stamped repo MUST NOT corrupt prior content. Each marker is
a short string the writer searches for before writing; if present, the writer
returns without rewriting.

If two modules both stamp the same file but use *different* markers, the second
writer will not see the first's marker and will rewrite (or worse, corrupt) the
file. This index exists so maintainers notice the drift before it ships.

## Marker registry

| Marker constant            | Defined in                          | Used in file               | Idempotency check                       |
|---                         |---                                  |---                         |---                                      |
| `_GITIGNORE_MARKER`        | `scripts/gh_handoff.py`             | `<project>/.gitignore`     | `existing.startswith(_GITIGNORE_MARKER)` (WR-06 anchored) |
| `OSBUILDER_MARKER`         | `scripts/runbook_writer.py`         | `<project>/README.md`      | `OSBUILDER_MARKER in existing` (substring; safe — readers expect it embedded after H1) |

## Cross-checks for maintainers

When adding a new marker:

1. Pick a string that is unlikely to appear in user-authored content (e.g. start
   with `# OSBuilder` or `<!-- OSBuilder ... -->`).
2. Add the constant + file + check style to the table above.
3. If two modules write the same target file, share the marker text by **value**
   (D-05: still no cross-import — duplicate the literal string and add a comment
   pointing to this index).
4. Anchor the check to start-of-file or a known structural position when a
   substring match could be tripped by hand-edited comments (see WR-06 for
   `_GITIGNORE_MARKER`).

## See also

- `scripts/gh_handoff.py` — `_GITIGNORE_MARKER` (Phase 6 SHIP-03)
- `scripts/runbook_writer.py` — `OSBUILDER_MARKER` (Phase 6 SHIP-02)
- D-05 (no cross-script imports) — see `.planning/milestones/v1.0-REQUIREMENTS.md`
