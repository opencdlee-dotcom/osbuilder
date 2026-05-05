#!/usr/bin/env python3
"""check_skill_md_length.py — fail CI if SKILL.md exceeds 200 lines (QUAL-01).

Standalone CI lint — invokable as `python3 scripts/check_skill_md_length.py`
without any test runner or third-party dep. Mirrors the in-process assertion
in scripts/tests/test_skill_md.py::test_skill_md_line_count_under_200, but
runs at CI surface so a PR pushing SKILL.md to 201 lines fails before review.

Exit codes:
  0 = SKILL.md is at or under the line limit
  1 = SKILL.md exceeds the line limit (BLOCK PR)
  2 = SKILL.md not found (defensive — should not happen in CI)

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"
LIMIT = 200


def check(skill_md: Path = SKILL_MD, limit: int = LIMIT) -> int:
    """Return 0 if line count <= limit, 1 if over, 2 if file missing."""
    if not skill_md.exists():
        sys.stderr.write(f"OSBuilder: SKILL.md not found at {skill_md}\n")
        return 2
    lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    if lines > limit:
        sys.stderr.write(
            f"OSBuilder: SKILL.md is {lines} lines, limit is {limit}. "
            f"Move detail to references/ via progressive disclosure.\n"
        )
        return 1
    print(f"OK: SKILL.md is {lines}/{limit} lines.")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="check_skill_md_length",
        description="OSBuilder SKILL.md line-count CI gate (QUAL-01).",
    )
    parser.add_argument("--skill-md", default=str(SKILL_MD),
                        help="Path to SKILL.md (default: <repo>/SKILL.md)")
    parser.add_argument("--limit", type=int, default=LIMIT,
                        help=f"Line-count cap (default: {LIMIT})")
    args = parser.parse_args(argv)
    return check(Path(args.skill_md), args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
