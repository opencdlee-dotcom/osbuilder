#!/usr/bin/env python3
"""check_skill_versions.py — first-session sub-skill version-drift validator (QUAL-05).

Reads OSBuilder's SKILL.md frontmatter `requires:` block; for each declared
sub-skill, reads its installed `version:` from ~/.claude/skills/<name>/SKILL.md;
compares semver via stdlib tuple comparison; emits a friendly upgrade command
if drift is detected.

Marker file at ~/.osbuilder/last_check.txt throttles re-runs to once per session.

Exit codes:
  0 = all sub-skills meet declared minimums (or marker present and not --force)
  1 = at least one sub-skill below minimum, or sub-skill not installed

Behavior matrix (see references/version-policy.md):
  version >= minimum     -> pass silently
  version < minimum      -> BLOCK + friendly upgrade command
  version field absent   -> WARN + proceed (Pitfall 2 — non-blocking)
  skill dir absent       -> BLOCK + install command

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"
SKILLS_DIR = Path(os.path.expanduser("~/.claude/skills"))
MARKER = Path(os.path.expanduser("~/.osbuilder/last_check.txt"))

# Security V5: version values must be dotted-integer literals only.
_VERSION_RE = re.compile(r"^[0-9.]{1,16}$")


def parse_version(s: str) -> tuple[int, ...]:
    """Parse 'MAJOR.MINOR.PATCH' -> (major, minor, patch).

    Pre-releases not supported. Malformed input returns (0, 0, 0) — fail-safe
    ('older than anything') per project's V5 input-validation pattern.
    """
    if not s:
        return (0, 0, 0)
    s = s.strip().lstrip("v")
    if not _VERSION_RE.match(s):
        return (0, 0, 0)
    parts = s.split(".")
    try:
        ints = tuple(int(p) for p in parts[:3])
    except ValueError:
        return (0, 0, 0)
    return ints + (0,) * (3 - len(ints))


def _read_frontmatter(path: Path) -> dict:
    """Read SKILL.md frontmatter as dict; supports nested sub-keys under `requires:`.

    Hand-rolled — no PyYAML dep. Returns {} if no frontmatter found.
    Extends test_skill_md.py:_read_frontmatter for nested-block parsing
    (the `requires:` block needs {sub_skill: version_str} structure).
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields: dict = {}
    current_key: str | None = None
    nested: dict | None = None
    for line in m.group(1).splitlines():
        # Indented sub-key under a nested block (e.g., requires:)
        if line.startswith("  ") and nested is not None:
            stripped = line.strip()
            if ":" in stripped:
                sub_k, _, sub_v = stripped.partition(":")
                nested[sub_k.strip()] = sub_v.strip()
            continue
        # Continuation of a `>` folded scalar (e.g., description)
        if line.startswith(" ") and current_key and nested is None:
            existing = fields.get(current_key, "")
            if isinstance(existing, str):
                fields[current_key] = (existing + " " + line.strip()).strip()
            continue
        nested = None
        if ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if not value:
                # Nested-block opener (e.g., requires:)
                fields[key] = {}
                nested = fields[key]
                current_key = key
            elif value == ">":
                # Folded scalar opener (e.g., description: >)
                fields[key] = ""
                current_key = key
            else:
                fields[key] = value
                current_key = key
    return fields


def _read_installed_version(skill_name: str) -> str | None:
    """Return installed `version:` for a sub-skill, or None if field/file absent.

    Returns None for both 'skill installed but no version: field' AND
    'skill SKILL.md has no frontmatter'. The caller distinguishes these via
    the skill-dir-existence check that runs first.
    """
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_md.exists():
        return None
    fm = _read_frontmatter(skill_md)
    version = fm.get("version")
    if version and isinstance(version, str):
        return version
    return None


def is_first_session() -> bool:
    """True if the per-user marker does not yet exist."""
    return not MARKER.exists()


def record_check_complete() -> None:
    """Create the marker file (idempotent)."""
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text("ok\n", encoding="utf-8")


def check_versions() -> int:
    """Validate all sub-skills declared in SKILL.md `requires:` block.

    Returns 0 if all met (or only soft-warnings), 1 if any block-level fault.
    """
    fm = _read_frontmatter(SKILL_MD)
    requires = fm.get("requires") or {}
    if not isinstance(requires, dict) or not requires:
        sys.stderr.write(
            "OSBuilder: SKILL.md has no `requires:` block. Nothing to validate.\n"
        )
        return 0

    any_block = False
    for sub_skill, min_str in requires.items():
        minimum = parse_version(min_str)
        skill_dir = SKILLS_DIR / sub_skill
        if not skill_dir.exists():
            sys.stderr.write(
                f"OSBuilder: sub-skill '{sub_skill}' is not installed at "
                f"{skill_dir}. Run: cd ~/.claude/skills && "
                f"git clone <{sub_skill}-repo-url> {sub_skill}\n"
            )
            any_block = True
            continue
        installed_str = _read_installed_version(sub_skill)
        if installed_str is None:
            # Pitfall 2: missing version field => warn, do not block
            sys.stderr.write(
                f"OSBuilder: ⚠️  {sub_skill} has no version field "
                f"— cannot enforce minimum {min_str}. "
                f"Proceeding anyway. (Reported in non-blocking mode.)\n"
            )
            continue
        installed = parse_version(installed_str)
        if installed < minimum:
            sys.stderr.write(
                f"OSBuilder: {sub_skill} {installed_str} is below required "
                f"{min_str}. Run: cd ~/.claude/skills/{sub_skill} && git pull\n"
            )
            any_block = True

    return 1 if any_block else 0


def _cmd_check(args: argparse.Namespace) -> int:
    if args.force or is_first_session():
        rc = check_versions()
        if rc == 0:
            record_check_complete()
        return rc
    return 0  # already checked this session


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="check_skill_versions",
        description="OSBuilder sub-skill version-drift validator (QUAL-05).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser(
        "check",
        help="Run drift check (skips if marker present unless --force).",
    )
    p.add_argument("--force", action="store_true",
                   help="Run check even if marker file exists")
    p.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover — defensive
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
