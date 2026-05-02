#!/usr/bin/env python3
"""intake_handler.py — OSBuilder intake handler.

Parses a plain-English paragraph OR a structured dict/JSON spec into a
canonical derived_spec.md at <project-root>/.planning/osbuilder/derived_spec.md.
Writes state.md fields: goal, app_type, playbook via state_writer.py.

Pure stdlib — no third-party deps.

Subcommands:
  parse     paragraph text or @path-to-spec → derived_spec.md (IN-01, IN-02).
  validate  check derived_spec.md is suitable for /gsd-new-project --auto (IN-05).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Phase 5: friendly-error translation layer (graceful degrade if module not yet built)
try:
    import friendly_error as _fe
except ImportError:
    _fe = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"

_REQUIRED_SECTIONS = ("# OSBuilder Derived Spec", "**Goal:**", "**App type:**", "**Playbook:**")
# IN-16: defense-in-depth secret-shape detection. gitleaks at commit time is the
# real backstop (see assets/gitleaks/.gitleaks.toml + Phase 6 SHIP-04). This
# list catches obvious paste-mistakes in the user's plain-English spec BEFORE
# it reaches state.md or any subprocess. Keep entries lower-case — comparison
# is case-insensitive in _cmd_validate.
_SECRET_PATTERNS = (
    "api_key",
    "password",
    "token",
    "database_url=postgresql://",
    # AI service token prefixes — common paste-from-dashboard shapes
    "openai_api_key",
    "anthropic_api_key",
    "sk-",       # OpenAI / Anthropic / Stripe key prefix
    "bearer ",   # Authorization header paste — trailing space disambiguates from words like "bearer-token"
)

# Phase 6 — refuse-list (SCL-05): hardcoded keyword tuple sourced from references/refuse-list.md
# Ordering invariant (WR-04): _matches_refuse_keyword returns the FIRST keyword in this
# tuple that appears in the spec, not the first one occurring in the spec text. The order
# below is "most-specific / most-severe first" so that a spec mentioning both `helm` and
# `kubernetes` reports `kubernetes` (the broader infrastructure flag) rather than `helm`.
# When adding new keywords, place broader/more-severe terms above narrower ones.
REFUSE_KEYWORDS = (
    "service mesh",
    "service-mesh",
    "microservices",
    "microservice",
    "kubernetes",
    "k8s",
    "helm",
    "istio",
    "linkerd",
    "consul",
)

REFUSE_LIST_MD = REPO_ROOT / "references" / "refuse-list.md"


# Phase 7 — playbook routing (D-01..D-03): weighted keyword-bag inference per playbook.
# Source-of-truth lives here; tests pin specific weights so changes surface in code review.
# See references/question-bank.md for the low-confidence fallback question.
# T-07-01-03: callers should cap paragraph length upstream — _score_playbooks runs
# ~50 keyword regexes against text.lower() and is O(n*k) on input length.
PLAYBOOK_KEYWORDS = {
    "web": {
        "website": 3, "web app": 3, "browser": 2, "homepage": 3,
        "landing page": 3, "frontend": 2, "html": 1, "todo app": 2,
        "blog": 2, "marketplace": 2, "saas": 2,
    },
    "ai-service": {
        "api": 2, "http api": 3, "endpoint": 2, "rest": 2,
        "summarize": 3, "llm": 3, "openai": 2, "anthropic": 2,
        "fastapi": 3, "service": 1,
        "embeddings": 2, "rag": 3, "agent": 2,
    },
    "cli": {
        "cli": 3, "command line": 3, "command-line": 3, "terminal": 2,
        "script": 2, "tool": 1, "automation": 2, "organize": 2,
        "batch": 2, "convert": 2, "rename": 2,
    },
    "desktop": {
        "desktop app": 3, "desktop": 2, "tray icon": 3, "system tray": 3,
        "native window": 3, "windows app": 2, "macos app": 2, "linux app": 2,
        "tauri": 3,
        "menu bar": 3, "offline app": 2,
    },
    "hub-platform": {
        "hub": 3, "platform": 2, "umbrella": 3, "workspace": 2,
        "professor hub": 4, "like professor": 4, "multiple tools": 3,
        "monorepo": 2, "suite": 2, "router": 1,
    },
}


def _score_playbooks(text: str) -> "dict[str, float]":
    """Return {playbook_name: score} given a paragraph. Pure function: no I/O.

    Word-boundary matching mirrors `_matches_refuse_keyword`: multi-word /
    hyphenated keywords use substring on lowercased text; single-word keywords
    use \\b regex to avoid false positives.
    """
    lower = text.lower()
    scores: "dict[str, float]" = {pb: 0.0 for pb in PLAYBOOK_KEYWORDS}
    for pb, kws in PLAYBOOK_KEYWORDS.items():
        for kw, w in kws.items():
            if " " in kw or "-" in kw:
                if kw in lower:
                    scores[pb] += w
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                    scores[pb] += w
    return scores


def infer_app_type(text: str) -> "tuple[str, float]":
    """Return (best_playbook, top_score) for a plain-English paragraph (D-01).

    Confidence rules (D-02 — caller wiring decides whether to commit or fall
    back to the question-bank):
        - top_score < 2.0  → low confidence; ask question-bank fallback
        - top_score - 2nd_score < 1.0 → tied; ask question-bank fallback
    """
    scores = _score_playbooks(text)
    best = max(scores, key=lambda k: scores[k])
    return best, scores[best]


def _is_low_confidence(scores: "dict[str, float]") -> bool:
    """True if no clear winner — caller should ask question-bank fallback (D-02)."""
    sorted_scores = sorted(scores.values(), reverse=True)
    if not sorted_scores or sorted_scores[0] < 2.0:
        return True
    if len(sorted_scores) >= 2 and (sorted_scores[0] - sorted_scores[1]) < 1.0:
        return True
    return False


# Phase 7 (07-05) — hub-platform sub-tool extraction (D-06).
# Pattern: "build me a hub for X, Y, and Z" or "hub like ... for X and Y".
# Strategy: capture everything after "for " up to end-of-string OR a clausal
# break (period, semicolon, " that ", " with the ", " so that "). Single
# " and " is NOT a clausal break — it's the most common subtool separator
# (X and Y), so the splitter handles it AFTER capture.
# T-07-05-04: bounded quantifier + per-result 40-char cap + regex sanitization
# means worst-case input still terminates and can never produce a path-traversing
# subtool name.
_SUBTOOL_PATTERN = re.compile(
    r"\bfor\s+(.+?)(?:[.;]|\s+that\s+(?:does|can|will)|\s+with\s+the\s+|\s+so\s+that\s+|$)",
    re.IGNORECASE,
)


def _extract_subtools(text: str) -> "list[str]":
    """Parse 'hub for X and Y and Z' → ['X', 'Y', 'Z'] (D-06).

    Returns [] if no clear list parseable; caller should ask the question-bank
    fallback per RESEARCH.md Open Q5.

    Each result is regex-sanitized to `[a-zA-Z0-9_-]` (T-07-05-01 defense in
    depth — `_validate_project_name` is the security gate, this just prevents
    obviously-bad input from reaching it).
    """
    m = _SUBTOOL_PATTERN.search(text[:500])  # bound input (T-07-05-04; mirrors _score_playbooks)
    if not m:
        return []
    raw = m.group(1)
    # Split on " and " (with word boundaries) or commas. Comma takes precedence
    # so "a, b, and c" → ["a", "b", "and c"] → drop the leading "and " in cleanup.
    parts = re.split(r",|\s+and\s+", raw, flags=re.IGNORECASE)
    result: "list[str]" = []
    for p in parts:
        cleaned = p.strip().rstrip(".").strip()
        # Drop a leading "and " left over from "a, b, and c" pattern
        cleaned = re.sub(r"^and\s+", "", cleaned, flags=re.IGNORECASE).strip()
        if not cleaned or len(cleaned) > 40:  # sanity cap (T-07-05-04)
            continue
        # Sanitize for use as directory names — collapse anything outside
        # [a-zA-Z0-9_-] to a single hyphen, then strip leading/trailing
        # hyphens. The output is guaranteed to satisfy
        # _validate_project_name's regex (or be empty, in which case we drop it).
        sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", cleaned).strip("-")
        if sanitized:
            result.append(sanitized)
    return result


def _derived_spec_path(project_root: Path) -> Path:
    return project_root / ".planning" / "osbuilder" / "derived_spec.md"


def _read_state(project_root: Path) -> dict:
    """Read state.md as JSON dict via state_writer read subcommand (D-05 duplicate)."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return {}
    result = subprocess.run(
        [sys.executable, str(STATE_WRITER), "read", "--format", "json",
         "--project-root", str(project_root)],
        capture_output=True, text=True, shell=False, check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def _write_state_field(project_root: Path, field: str, value: str) -> None:
    """Write a single field to state.md via state_writer (D-05 duplicate)."""
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "write",
         "--field", field, "--value", value,
         "--project-root", str(project_root)],
        shell=False, check=True,
    )


def _load_refusal_copy(matched_keyword: str) -> str:
    """Read references/refuse-list.md and return the user-facing refusal copy section.

    Extracts the section under '## Refusal copy' H2 until the next H2.
    Falls back to a minimal hardcoded message if the file is missing.
    """
    if not REFUSE_LIST_MD.exists():
        return (
            f"OSBuilder: this build asks for '{matched_keyword}', which is on the v1 default "
            f"refuse-list (Kubernetes, microservices, service-mesh, Helm). Re-run with "
            f"--production-ready to add these as named ROADMAP phases instead.\n"
        )
    text = REFUSE_LIST_MD.read_text(encoding="utf-8")
    # Extract the section under "## Refusal copy" until next H2.
    # WR-09: match either start-of-file or a preceding newline so the H2 is found
    # even if it appears as the very first line. Inline backtick references in
    # blockquotes (e.g., `## Refusal copy`) are still excluded because they are
    # not at column 0.
    match = re.search(r"(?:^|\n)## Refusal copy", text)
    if match is None:
        return text  # whole file is fallback
    after = text[match.end():]
    next_h2 = after.find("\n## ")
    body = after if next_h2 < 0 else after[:next_h2]
    # Substitute the matched keyword if the copy uses {{keyword}}
    return body.replace("{{keyword}}", matched_keyword).strip() + "\n"


def _matches_refuse_keyword(spec: str) -> "str | None":
    """Return the first refuse keyword matched in spec with word-boundary semantics, else None.

    For multi-word keywords (containing space or hyphen), use substring check on lowercased text.
    For single-word keywords, use \\b regex to avoid false positives ('k8sFooBar' must NOT match).
    """
    lower = spec.lower()
    for kw in REFUSE_KEYWORDS:
        if " " in kw or "-" in kw:
            # multi-word / hyphenated — substring on lowercased text is fine
            if kw in lower:
                return kw
        else:
            # single-word — strict word boundary
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                return kw
    return None


def check_refuse_list(project_root: Path) -> bool:
    """SCL-05: refusal gate. Returns True if request was refused.

    Reads derived_spec.md and state.md; if state production_ready=='true', short-circuit-False.
    On hit: writes last_failure='refused: <kw>' via state_writer; prints refusal copy to stderr.

    The refusal does NOT exit non-zero — gsd_driver.py interprets the True return as
    'do not advance phase_step' while preserving the resume protocol.
    """
    # Bypass when production-ready
    state = _read_state(project_root)
    if state.get("production_ready", "false") == "true":
        return False

    spec_path = project_root / ".planning" / "osbuilder" / "derived_spec.md"
    if not spec_path.exists():
        return False

    spec = spec_path.read_text(encoding="utf-8")
    matched = _matches_refuse_keyword(spec)
    if matched is None:
        return False

    # Hit — write state field + emit refusal copy
    _write_state_field(project_root, "last_failure", f"refused: {matched}")
    sys.stderr.write(_load_refusal_copy(matched))
    return True


def _resolve_project_root(arg: str | None) -> Path:
    """Resolve --project-root to an absolute Path; auto-detect if omitted."""
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


def _mode_from_state(project_root: Path) -> str:
    """Read mode field from state.md; default 'beginner' on any failure (UX-03)."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return "beginner"
    try:
        r = subprocess.run(
            [sys.executable, str(STATE_WRITER), "read",
             "--field", "mode", "--project-root", str(project_root)],
            capture_output=True, text=True, shell=False, check=False,
        )
        return r.stdout.strip() or "beginner"
    except Exception:
        return "beginner"


def atomic_write(path: Path, content: str) -> None:
    """Atomic file write via os.replace (atomic on POSIX + Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.stem}.{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _render_derived_spec(
    goal: str,
    app_type: str = "web",
    features: list | None = None,
    users: list | None = None,
    stack_hints: list | None = None,
    mode: str = "beginner",
) -> str:
    """Render derived_spec.md content in /gsd-new-project --auto handoff format.

    UX-03: stack_hints are only included when mode == 'advanced'. Beginner
    mode (default) omits the **Stack hints:** line entirely so technology
    names (Next.js, Drizzle, Postgres, etc.) never surface to the user.
    """
    features = features or []
    users = users or []
    stack_hints = stack_hints or []
    lines = ["# OSBuilder Derived Spec", "", f"**Goal:** {goal}", ""]
    if users:
        lines += ["**User types:**"] + [f"- {u}" for u in users] + [""]
    if features:
        lines += ["**Core features:**"] + [f"- {f}" for f in features] + [""]
    lines.append(f"**App type:** {app_type}")
    lines.append(f"**Playbook:** references/playbooks/{app_type}.md")
    if stack_hints and mode == "advanced":
        lines.append(f"**Stack hints:** {', '.join(stack_hints)}")
    lines += ["", "**Build with:** /gsd-new-project --auto"]
    return "\n".join(lines) + "\n"


def parse_paragraph(text: str, project_root: Path | None = None) -> Path:
    """IN-01: Parse plain-English paragraph → derived_spec.md.

    T-3-03: text is treated as data only — never executed or interpolated.
    UX-03: mode (beginner/advanced) is read from state.md; beginner mode
    suppresses stack_hints in the rendered spec.
    Returns the Path of the written derived_spec.md.

    WR-10 / Phase 7 (D-01..D-03): app_type is inferred via PLAYBOOK_KEYWORDS
    across all 5 playbooks (web / ai-service / cli / desktop / hub-platform).
    On low confidence or ties, the caller (orchestrator / SKILL.md) is expected
    to ask the question-bank "What kind of thing" fallback. Non-interactive
    callers (this function) default to "web" — same default as the
    "I don't know, you decide" branch in references/question-bank.md.
    parse_structured continues to respect an explicit app_type key.
    """
    root = _resolve_project_root(str(project_root) if project_root is not None else None)
    dest = _derived_spec_path(root)
    _mode = _mode_from_state(root)
    # Phase 7 (D-01..D-03): replace hardcoded "web" with inferred routing.
    scores = _score_playbooks(text)
    if _is_low_confidence(scores):
        # D-02 fallback: ask the question-bank rather than coin-flipping.
        # The actual interactive prompt is owned by the orchestrator (SKILL.md);
        # for non-interactive callers, we default to "web" (matches the
        # "I don't know, you decide" branch in references/question-bank.md).
        inferred_app_type = "web"
    else:
        inferred_app_type = max(scores, key=lambda k: scores[k])
    atomic_write(dest, _render_derived_spec(
        goal=text.strip(), app_type=inferred_app_type, mode=_mode,
    ))
    return dest


def parse_structured(data: dict, project_root: Path | None = None) -> Path:
    """IN-02: Parse structured dict spec → derived_spec.md.

    Keys: goal (required), features, users, app_type, stack_hints (all optional).
    UX-03: mode (beginner/advanced) is read from state.md; beginner mode
    suppresses stack_hints in the rendered spec.
    Returns the Path of the written derived_spec.md.
    """
    root = _resolve_project_root(str(project_root) if project_root is not None else None)
    dest = _derived_spec_path(root)
    _mode = _mode_from_state(root)
    atomic_write(dest, _render_derived_spec(
        goal=str(data.get("goal", "")),
        app_type=str(data.get("app_type", "web")),
        features=list(data.get("features", [])),
        users=list(data.get("users", [])),
        stack_hints=list(data.get("stack_hints", [])),
        mode=_mode,
    ))
    return dest


def _cmd_parse(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    inp: str = args.input
    if inp.startswith("@"):
        fp = Path(inp[1:])
        if not fp.exists():
            sys.stderr.write(f"OSBuilder: spec file not found: {fp}\n")
            return 1
        raw = fp.read_text(encoding="utf-8")
        try:
            parse_structured(json.loads(raw), project_root)
        except json.JSONDecodeError:
            parse_paragraph(raw, project_root)
    else:
        parse_paragraph(inp, project_root)
    print(f"Written: {_derived_spec_path(project_root)}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    dest = _derived_spec_path(_resolve_project_root(args.project_root))
    if not dest.exists():
        sys.stderr.write(f"OSBuilder: derived_spec.md not found at {dest}\n")
        return 1
    content = dest.read_text(encoding="utf-8")
    missing = [s for s in _REQUIRED_SECTIONS if s not in content]
    if missing:
        sys.stderr.write("OSBuilder: derived_spec.md missing: " + ", ".join(missing) + "\n")
        return 1
    found = [p for p in _SECRET_PATTERNS if p in content.lower()]
    if found:
        sys.stderr.write("OSBuilder: derived_spec.md contains secrets: " + ", ".join(found) + "\n")
        return 1
    print("OK — derived_spec.md is valid for /gsd-new-project --auto")
    return 0


def _cmd_check_refuse_list(args: argparse.Namespace) -> int:
    """CLI: returns 0 if no refusal, 2 if refused (so callers can distinguish from real errors)."""
    project_root = _resolve_project_root(args.project_root)
    if check_refuse_list(project_root):
        return 2  # sentinel exit code: "refused — do not advance"
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="intake_handler", description="OSBuilder intake handler.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_parse = sub.add_parser("parse", help="parse input → derived_spec.md")
    p_parse.add_argument("--input", required=True, help="paragraph string or @path-to-spec-file")
    p_parse.add_argument("--project-root", default=None, dest="project_root")
    p_parse.set_defaults(func=_cmd_parse)

    p_validate = sub.add_parser("validate", help="check derived_spec.md format")
    p_validate.add_argument("--project-root", default=None, dest="project_root")
    p_validate.set_defaults(func=_cmd_validate)

    p_refuse = sub.add_parser("check-refuse-list",
                              help="Check derived_spec.md against refuse-list (SCL-05).")
    p_refuse.add_argument("--project-root", default=None, dest="project_root")
    p_refuse.set_defaults(func=_cmd_check_refuse_list)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
