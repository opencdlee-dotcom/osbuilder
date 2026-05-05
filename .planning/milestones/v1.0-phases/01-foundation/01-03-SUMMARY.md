# Plan 01-03 Summary — install.sh + .gitkeep markers

**Status:** ✓ Complete
**Requirements covered:** FOUND-03 (and BLOCKER 1 from iter-1 plan-checker)
**Commit:** `cee92cb` (or whichever the install.sh commit ended up with)
**Tests:** `pytest scripts/tests/test_install.py` — 4/4 GREEN

## Deliverables

| File | Purpose |
|------|---------|
| `install.sh` | Idempotent skill installer (canonical pattern from `predator/install.sh`) |
| `assets/.gitkeep` | Tracks empty directory in git |
| `examples/.gitkeep` | Tracks empty directory in git |
| `scripts/.gitkeep` | Tracks empty directory in git |

## install.sh Logic

1. `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` — resolve repo root
2. `mkdir -p` the four-dir layout under `${HOME}/.claude/skills/osbuilder/`
3. **Copy step (BLOCKER 1 closure)** — source-guarded copies of SKILL.md,
   references/, scripts/state_writer.py, scripts/bootstrap.sh, scripts/bootstrap.ps1
4. `chmod +x` on installed scripts
5. Idempotent: second run produces identical layout

## Anti-patterns avoided

- No `rm -rf`
- No sudo
- No nested directories beyond one level
- Source-guarded copies (warn-and-skip on missing source — partial-repo states still install cleanly)

## End-to-End Smoke Test

```
$ bash install.sh
Installing OSBuilder to /Users/charlie/.claude/skills/osbuilder...
OSBuilder installed at /Users/charlie/.claude/skills/osbuilder
Run /osbuilder in a Claude Code session to start.
$ ls ~/.claude/skills/osbuilder/
SKILL.md  assets/  examples/  references/  scripts/
$ ls ~/.claude/skills/osbuilder/scripts/
bootstrap.ps1  bootstrap.sh  state_writer.py
```

`/osbuilder` is now visible in Claude Code's skill list.

## Self-Check: PASSED

- [x] `bash install.sh` exits 0; second run also exits 0 (idempotent)
- [x] `find ~/.claude/skills/osbuilder -mindepth 3 -type d` returns empty (one-level rule)
- [x] `pytest scripts/tests/test_install.py` 4/4 GREEN (including test_install_copies_artifacts)
- [x] `/bin/sh -n install.sh` parses cleanly (POSIX-portable)
