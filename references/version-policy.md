# OSBuilder Version Policy (`requires:` convention)

> Cross-referenced by `scripts/check_skill_versions.py:check_versions`. The
> `requires:` block in OSBuilder's SKILL.md frontmatter is the source of truth
> for sub-skill minimum versions.
>
> **NOT a standard Anthropic frontmatter field** (verified 2026-05-02 against
> `code.claude.com/docs/en/skills` and
> `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices`).
> This is an OSBuilder-local convention; future Anthropic spec changes are
> tracked in Pitfall 7 of `.planning/milestones/v1.0-phases/08-skill-quality-publish-bar/08-RESEARCH.md`.

## Format

In SKILL.md frontmatter:

```yaml
requires:
  gsd: 1.0.0
  brainiac: 6.0.0
  predator: 1.0.0
  code-tester: 3.1.0
  problem-solver: 3.0.0
```

Indentation is exactly 2 spaces. Versions are dotted integers
(`MAJOR.MINOR.PATCH`); pre-releases (`1.0.0-beta1`) are not supported in v1.

## Behavior on first invocation

`scripts/check_skill_versions.py` runs once per Claude Code session, gated by
the `~/.osbuilder/last_check.txt` marker (presence = already checked this
session). For each sub-skill listed in `requires:`:

| Installed state | Behavior | Exit code |
|-----------------|----------|-----------|
| Sub-skill `version:` >= declared minimum | Pass silently | 0 |
| Sub-skill `version:` < declared minimum | **BLOCK** with friendly upgrade command | 1 |
| Sub-skill `version:` field absent (gsd, predator as of 2026-05-02) | **WARN** but proceed (non-blocking) | 0 |
| Sub-skill not installed at `~/.claude/skills/<name>/` | **BLOCK** with install command | 1 |

Rationale for warn-not-block on missing version: of the 5 sub-skills, gsd and
predator currently expose no `version:` frontmatter field. Blocking on absence
would brick first-run for every OSBuilder user. The composition rule says:
fix the sub-skill, never fork it. We file issues against gsd & predator to add
`version:` blocks; in the meantime, warn-and-proceed is the user-friendly
posture.

## Resetting the marker

To force a re-check (e.g., after upgrading a sub-skill mid-session):

```bash
rm -f ~/.osbuilder/last_check.txt
```

Next `/osbuilder` invocation will re-run the validator.

## Why per-user-global, not per-project

The marker file lives at `~/.osbuilder/last_check.txt`, not under any project's
`.planning/`. Version drift is a per-machine concern (you upgrade brainiac on
your laptop, not on a per-project basis). See Pitfall 3 in 08-RESEARCH.md for
the full rationale.

## Updating the minimums

1. Bump the version value in SKILL.md `requires:` block.
2. Confirm the new minimum is realistic by reading
   `~/.claude/skills/<name>/SKILL.md` for the currently-installed version.
3. The validator picks up the change on next session (or after marker reset).

## See also

- `SKILL.md` — frontmatter `requires:` block (source of truth)
- `scripts/check_skill_versions.py` — implementation
- `~/.claude/skills/{gsd,brainiac,predator,code-tester,problem-solver}/SKILL.md` — installed versions
- `.planning/milestones/v1.0-phases/08-skill-quality-publish-bar/08-RESEARCH.md` Pitfall 2 (missing-version policy), Pitfall 7 (Anthropic-future-proofing)
