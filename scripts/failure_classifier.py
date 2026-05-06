#!/usr/bin/env python3
"""failure_classifier.py — OSBuilder error class + retry router.

Classifies a raw error string into one of four failure classes and
returns the appropriate retry strategy. Pure function — no file I/O,
no subprocess calls.

Classes: transient, context-overflow, tool-failure, validation-failure

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Error pattern lists — ORDER MATTERS in classify() (validation checked first)
# ---------------------------------------------------------------------------

VALIDATION_FAILURE_PATTERNS = [
    r"test.*failed",
    r"assertion.*error",
    r"verification.*failed",
    r"criterion.*not met",
    r"code-tester.*fail",
]

TOOL_FAILURE_PATTERNS = [
    r"skill not found",
    r"SKILL\.md.*error",
    r"command not found",
    r"No such file or directory",
]

CONTEXT_OVERFLOW_PATTERNS = [
    r"context.length.exceeded",
    r"max.tokens",
    r"too many tokens",
    r"context window",
]

TRANSIENT_PATTERNS = [
    r"ECONNRESET",
    r"ETIMEDOUT",
    r"ECONNREFUSED",
    r"EAI_AGAIN",
    r"503",
    r"Connection timed out",
    r"Read timed out",
    r"Network unreachable",
    r"pnpm install.*failed",
]

# ---------------------------------------------------------------------------
# Backoff table (seconds): retry_count → wait seconds
# ---------------------------------------------------------------------------

BACKOFF_SECONDS = {0: 1, 1: 4, 2: 16}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _matches(patterns: list[str], error: str) -> bool:
    """Return True if any pattern matches the error string (case-insensitive)."""
    return any(re.search(p, error, re.IGNORECASE) for p in patterns)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify(error: str, context: dict | None = None) -> dict:
    """Classify a raw error string into a failure class and retry strategy.

    Args:
        error: Raw error string from an external process.
        context: Optional dict with keys such as ``retry_count`` (int).

    Returns:
        {
            "class": "transient" | "context-overflow" | "tool-failure" | "validation-failure",
            "strategy": "backoff" | "compress-retry" | "fallback" | "re-plan",
            "retry_ok": bool,           # False when retry_count >= 3
            "backoff_seconds": int | None,  # set only for transient class
        }

    CRITICAL: VALIDATION_FAILURE_PATTERNS are checked BEFORE TRANSIENT_PATTERNS
    to prevent "test.*failed" from being misclassified as transient.
    """
    retry_count = int((context or {}).get("retry_count", 0))
    retry_ok = retry_count < 3

    # Validation must be checked first — "test.*failed" overlaps with "pnpm install.*failed"
    if _matches(VALIDATION_FAILURE_PATTERNS, error):
        return {
            "class": "validation-failure",
            "strategy": "re-plan",
            "retry_ok": retry_ok,
            "backoff_seconds": None,
        }

    if _matches(TOOL_FAILURE_PATTERNS, error):
        return {
            "class": "tool-failure",
            "strategy": "fallback",
            "retry_ok": retry_ok,
            "backoff_seconds": None,
        }

    if _matches(CONTEXT_OVERFLOW_PATTERNS, error):
        return {
            "class": "context-overflow",
            "strategy": "compress-retry",
            "retry_ok": retry_ok,
            "backoff_seconds": None,
        }

    if _matches(TRANSIENT_PATTERNS, error):
        return handle_transient(error, retry_count=retry_count)

    # Unknown error — escalate immediately, no retry
    return {
        "class": "transient",
        "strategy": "escalate",
        "retry_ok": False,
        "backoff_seconds": None,
    }


def handle_transient(error: str, retry_count: int = 0) -> dict:
    """Apply exponential backoff for a transient error.

    Calls ``time.sleep(wait)`` before returning. If ``retry_count >= 3``,
    returns an escalate result without sleeping.

    Args:
        error: Raw error string (passed through for context; not inspected here).
        retry_count: How many retries have already been attempted (0-indexed).

    Returns:
        {
            "class": "transient",
            "strategy": "backoff" | "escalate",
            "retry_ok": bool,
            "backoff_seconds": int | None,
        }
    """
    if retry_count >= 3:
        return {
            "class": "transient",
            "strategy": "escalate",
            "retry_ok": False,
            "backoff_seconds": None,
        }
    wait = BACKOFF_SECONDS.get(retry_count, 16)
    time.sleep(wait)
    return {
        "class": "transient",
        "strategy": "backoff",
        "retry_ok": True,
        "backoff_seconds": wait,
    }


def build_escalation_handoff(
    phase: int,
    role: str,
    failure_class: str,
    last_error: str,
    escalation_log: list[str],
) -> str:
    """Build a structured markdown escalation handoff string.

    Args:
        phase: Numeric phase index (e.g. 2).
        role: Role name (e.g. "QA").
        failure_class: One of the four failure class strings.
        last_error: Raw last error message.
        escalation_log: Ordered list of escalation steps attempted.

    Returns:
        Markdown string with sections: OSBuilder Escalation Handoff, Last Error,
        What Was Tried, State Checkpoint, Recommended Next Action.
    """
    ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    tried_lines = "\n".join(
        f"{i + 1}. {step}" for i, step in enumerate(escalation_log)
    )
    next_action_map = {
        "transient": "Check network connectivity, then run `/osbuilder resume`",
        "validation-failure": (
            "Review the failing criterion in VERIFICATION.md, fix manually, "
            "then run `/osbuilder resume`"
        ),
        "tool-failure": (
            "Verify that the required skill is installed at `~/.claude/skills/`, "
            "then run `/osbuilder resume`"
        ),
        "context-overflow": "Start a new session and run `/osbuilder resume`",
    }
    next_action = next_action_map.get(failure_class, "Run `/osbuilder resume`")
    return f"""# OSBuilder Escalation Handoff

**Timestamp:** {ts}
**Phase:** {phase}
**Role:** {role}
**Last failure class:** {failure_class}
**Retry count:** 3

## Last Error

```
{last_error}
```

## What Was Tried

{tried_lines}

## State Checkpoint

All state persisted in: `.planning/osbuilder/state.md`

## Recommended Next Action

{next_action}
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="failure_classifier",
        description="Classify an OSBuilder error string and return a retry strategy as JSON.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cls_p = sub.add_parser("classify", help="Classify an error string.")
    cls_p.add_argument("--error", required=True, help="Raw error string to classify.")
    cls_p.add_argument(
        "--retry-count",
        type=int,
        default=0,
        help="Current retry count (default: 0).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        raise

    if args.command == "classify":
        result = classify(args.error, context={"retry_count": args.retry_count})
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
