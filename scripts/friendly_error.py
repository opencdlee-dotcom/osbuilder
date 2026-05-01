#!/usr/bin/env python3
"""friendly_error.py — OSBuilder raw-error → FriendlyMessage translator.

Translates raw subprocess/exception strings into plain-English FriendlyMessage
objects via a dictionary of known error patterns + a generic-fallback path that
strips Python tracebacks and Node stack frames.

Pure stdlib — no third-party deps. Hand-rolled YAML subset parser for the
30-entry dictionary file.

Subcommands (CLI shim):
  (no subcommand) reads stdin, prints translated message to stdout.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
DICTIONARY_PATH = REPO_ROOT / "references" / "friendly-errors" / "dictionary.yaml"

Severity = Literal["info", "warn", "error", "fatal"]


@dataclass
class FriendlyMessage:
    title: str
    what_broke: str
    what_to_do: str
    copy_paste: str | None
    severity: Severity


# ---------------------------------------------------------------------------
# Module-level dictionary (loaded at import; populated by load_dictionary).
# ---------------------------------------------------------------------------

_DICTIONARY: list[dict] = []


# ---------------------------------------------------------------------------
# Hand-rolled YAML subset parser.
#
# Handles ONLY the structure used by dictionary.yaml:
#   - Top-level YAML block sequence: each record begins with `- key: value`
#   - Inline scalar values: `key: value` and `key: "value"`
#   - Tilde (`~`) → None
#   - Nested block sequences for the format_version record's schema_fields list
#   - Comments (`#`) and blank lines are skipped
#
# Multi-line block scalars (`|` / `>`) are NOT used by the dictionary; the
# parser does not implement them. If a future entry requires multi-line text,
# the parser must be extended (and tests added).
# ---------------------------------------------------------------------------


def _strip_quotes(value: str) -> str:
    """Strip surrounding single or double quotes from a YAML scalar value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _coerce_scalar(value: str) -> object:
    """Coerce a YAML scalar string to None for ~, otherwise unquoted string."""
    raw = value.strip()
    if raw in ("~", "null", "Null", "NULL", ""):
        return None
    return _strip_quotes(raw)


def _indent_of(line: str) -> int:
    """Return the count of leading spaces in line (tabs are forbidden by YAML spec)."""
    return len(line) - len(line.lstrip(" "))


def _parse_yaml_subset(raw: str) -> list[dict]:
    """Parse the dictionary.yaml subset → list[dict].

    Algorithm: walk lines, tracking the indent of each record. Each top-level
    record starts with `- ` at indent 0. Nested block sequences (indent > 0,
    starts with `-`) are collected as lists.
    """
    # Strip comments and blank lines, but preserve indent of remaining lines.
    cleaned: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        cleaned.append(line.rstrip())

    records: list[dict] = []
    current: dict | None = None
    pending_list_key: str | None = None
    pending_list: list[str] | None = None
    pending_list_indent: int | None = None

    def _flush_pending_list() -> None:
        nonlocal pending_list_key, pending_list, pending_list_indent
        if current is not None and pending_list_key is not None and pending_list is not None:
            current[pending_list_key] = pending_list
        pending_list_key = None
        pending_list = None
        pending_list_indent = None

    for line in cleaned:
        indent = _indent_of(line)
        body = line.lstrip(" ")

        # Top-level record start: `- key: value` at indent 0
        if indent == 0 and body.startswith("- "):
            _flush_pending_list()
            if current is not None:
                records.append(current)
            current = {}
            inline = body[2:]  # strip leading "- "
            if ":" in inline:
                k, _, v = inline.partition(":")
                current[k.strip()] = _coerce_scalar(v)
            continue

        # Nested block-sequence item: `- value` at indent > 0
        if indent > 0 and body.startswith("- "):
            list_item = body[2:].strip()
            if pending_list is None or pending_list_indent != indent:
                # New nested list — but we only enter this state via a `key:`
                # line that had no inline value. If pending_list_key wasn't
                # set, treat as malformed and skip.
                if pending_list_key is None:
                    continue
                pending_list = []
                pending_list_indent = indent
            pending_list.append(_strip_quotes(list_item))
            continue

        # Regular `key: value` line within current record.
        if current is None:
            # Stray line outside any record — skip.
            continue

        if ":" in body:
            _flush_pending_list()
            k, _, v = body.partition(":")
            key = k.strip()
            value = v.strip()
            if value == "":
                # Empty value → expect a nested list on subsequent lines.
                pending_list_key = key
                pending_list = None
                pending_list_indent = None
            else:
                current[key] = _coerce_scalar(value)

    _flush_pending_list()
    if current is not None:
        records.append(current)

    return records


def load_dictionary(path: Path = DICTIONARY_PATH) -> list[dict]:
    """Load + validate dictionary; check format-version field.

    Raises SystemExit on:
      - format_version missing or != "1.0" (T-05-02-02 — tampering gate)
      - fewer than 30 entries (after the metadata record)
    """
    global _DICTIONARY
    raw = path.read_text(encoding="utf-8")
    parsed = _parse_yaml_subset(raw)
    if not parsed or parsed[0].get("format_version") != "1.0":
        raise SystemExit(
            "OSBuilder: friendly-errors dictionary format-version mismatch. "
            "Expected 1.0; got "
            + str(parsed[0].get("format_version") if parsed else None)
        )
    _DICTIONARY = parsed[1:]
    if len(_DICTIONARY) < 30:
        raise SystemExit(
            f"OSBuilder: dictionary has {len(_DICTIONARY)} entries; expected >= 30."
        )
    return _DICTIONARY


# ---------------------------------------------------------------------------
# Translation core.
# ---------------------------------------------------------------------------


def _safe_format(template: str, ctx: dict) -> str:
    """Apply ctx.format(**ctx); on KeyError, return the original template.

    T-05-02-03 mitigation: malformed ctx (missing keys) cannot inject
    unexpected text or raise — the original template is returned unchanged.
    """
    if not ctx:
        return template
    try:
        return template.format(**ctx)
    except (KeyError, IndexError, ValueError):
        return template


def _build_message(entry: dict, ctx: dict | None) -> FriendlyMessage:
    """Format dictionary entry with ctx interpolation.

    T-05-02-03: copy_paste is rendered as plain text only; never executed.
    """
    ctx = ctx or {}
    title = _safe_format(str(entry.get("title", "")), ctx)
    what_broke = _safe_format(str(entry.get("what_broke", "")), ctx)
    what_to_do = _safe_format(str(entry.get("what_to_do", "")), ctx)
    cp_raw = entry.get("copy_paste_command")
    if cp_raw is None or cp_raw == "":
        copy_paste: str | None = None
    else:
        formatted = _safe_format(str(cp_raw), ctx)
        copy_paste = formatted or None
    severity_raw = str(entry.get("severity", "error"))
    if severity_raw not in ("info", "warn", "error", "fatal"):
        severity_raw = "error"
    severity: Severity = severity_raw  # type: ignore[assignment]
    return FriendlyMessage(
        title=title,
        what_broke=what_broke,
        what_to_do=what_to_do,
        copy_paste=copy_paste,
        severity=severity,
    )


def _strip_tracebacks(text: str) -> str:
    """Remove Python tracebacks and Node stack frames.

    T-05-02-01 mitigation: traceback blocks (multi-line "Traceback (most
    recent call last):" + indented File frames) and Node stack frames are
    stripped before the cleaned text is returned to the generic translator.
    """
    lines = text.splitlines()
    out: list[str] = []
    in_tb = False
    for line in lines:
        if line.startswith("Traceback (most recent"):
            in_tb = True
            continue
        if in_tb:
            if line.startswith(" ") or line.startswith("\t") or 'File "' in line:
                continue
            in_tb = False
        if re.match(r"^\s+at .+\(.+:\d+\)$", line):  # Node stack frame
            continue
        if re.match(r'^\s+File ".*", line \d+,', line):  # Python File frame
            continue
        out.append(line)
    return "\n".join(out)


def _generic_translator(text: str, ctx: dict | None) -> FriendlyMessage:
    """Fallback: strip stack traces, surface last meaningful line."""
    cleaned = _strip_tracebacks(text)
    lines = cleaned.strip().splitlines() or ["unknown error"]
    last = lines[-1][:200]
    return FriendlyMessage(
        title="Something went wrong",
        what_broke=last,
        what_to_do="Check the debug log at .planning/osbuilder/build.log for details.",
        copy_paste=None,
        severity="error",
    )


def translate(raw_error: str | Exception, ctx: dict | None = None) -> FriendlyMessage:
    """Translate a raw error string/exception → FriendlyMessage.

    First-match precedence over the dictionary; generic fallback if no entry
    matches. Order in the dictionary file determines precedence — more
    specific patterns must be earlier in the file than generic ones.

    T-05-02-03: ctx values are only interpolated via _safe_format which
    catches KeyError; copy_paste is never auto-executed.
    """
    text = str(raw_error)
    for entry in _DICTIONARY:
        pattern = entry.get("match_pattern")
        if not isinstance(pattern, str) or not pattern:
            continue
        is_regex = entry.get("pattern_type") == "regex"
        try:
            if is_regex:
                if re.search(pattern, text, re.IGNORECASE):
                    return _build_message(entry, ctx)
            else:
                if pattern in text:
                    return _build_message(entry, ctx)
        except re.error:
            # Malformed regex in dictionary — skip this entry rather than crash.
            continue
    return _generic_translator(text, ctx)


# ---------------------------------------------------------------------------
# Module-init: load dictionary so translate() is ready from first import.
#
# T-05-02-04: parser exceptions surface as SystemExit with clear message.
# Initial load suppresses both FileNotFoundError (dictionary not yet shipped)
# and SystemExit (format-version drift); translate() will hit the empty-
# dictionary fallback in either case.
# ---------------------------------------------------------------------------

try:
    load_dictionary()
except (FileNotFoundError, SystemExit):
    pass


# ---------------------------------------------------------------------------
# CLI shim.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    msg = translate(sys.stdin.read())
    print(f"## {msg.title}\n\n{msg.what_broke}\n\n**What to do:** {msg.what_to_do}")
    if msg.copy_paste:
        print(f"\n```\n{msg.copy_paste}\n```")
