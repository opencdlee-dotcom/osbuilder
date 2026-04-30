"""Tests for SKILL.md — FOUND-01 (frontmatter validity) and FOUND-02 (line count, references link)."""
from __future__ import annotations
import re
from pathlib import Path
import pytest

SKILL_MD = Path(__file__).resolve().parents[2] / "SKILL.md"

# Anthropic frontmatter rules (verbatim from RESEARCH.md Pattern 1)
NAME_REGEX = re.compile(r"^[a-z0-9-]{1,64}$")
RESERVED_WORDS = ("anthropic", "claude")
DESCRIPTION_MAX_CHARS = 1024


def _read_frontmatter() -> dict:
    if not SKILL_MD.exists():
        pytest.skip("SKILL.md not yet created (Plan 02 target)")
    text = SKILL_MD.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        pytest.fail("SKILL.md missing YAML frontmatter delimited by `---`")
    body = m.group(1)
    # Hand-parse — no PyYAML dep allowed
    fields: dict = {}
    current_key = None
    for line in body.splitlines():
        if line.startswith(" ") and current_key:
            fields[current_key] += " " + line.strip()
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == ">":
                fields[key] = ""
                current_key = key
            else:
                fields[key] = value
                current_key = key
    return fields


def test_frontmatter_valid():
    """1-01-02: Frontmatter satisfies Anthropic's hard rules."""
    fm = _read_frontmatter()

    assert "name" in fm, "frontmatter missing required `name`"
    assert NAME_REGEX.match(fm["name"]), \
        f"name `{fm['name']}` violates [a-z0-9-]{{1,64}}"
    for word in RESERVED_WORDS:
        assert word not in fm["name"], f"name contains reserved word: {word}"

    assert "description" in fm and fm["description"], \
        "frontmatter missing required `description`"
    assert len(fm["description"]) <= DESCRIPTION_MAX_CHARS, \
        f"description {len(fm['description'])} chars > 1024 cap"
    assert "<" not in fm["description"], "description contains XML-like tag (forbidden)"


def test_skill_md_line_count_under_200():
    """1-01-03: SKILL.md must be <= 200 lines (user constraint, stricter than Anthropic's 500)."""
    if not SKILL_MD.exists():
        pytest.skip("SKILL.md not yet created (Plan 02 target)")
    line_count = len(SKILL_MD.read_text(encoding="utf-8").splitlines())
    assert line_count <= 200, f"SKILL.md is {line_count} lines (cap 200)"


def test_has_references_link():
    """1-01-04: SKILL.md body links into references/ (progressive disclosure proof)."""
    if not SKILL_MD.exists():
        pytest.skip("SKILL.md not yet created (Plan 02 target)")
    body = SKILL_MD.read_text(encoding="utf-8")
    assert re.search(r"references/", body), \
        "SKILL.md must reference at least one path under references/"
