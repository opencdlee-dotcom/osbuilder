#!/usr/bin/env python3
"""narration.py — OSBuilder role-banner emitter, tutor-mode renderer, subprocess capturer.

Phase 5 (UX-01, UX-04, ROLE-09). Pure stdlib — no third-party deps.

Public surface:
  emit(role, action, status, detail=None)         — role banner + optional tutor line
  capture_subprocess(cmd, role, action, *, log_path, ...) — thread-per-stream capture
  _refresh_state(project_root)                    — refresh tutor + mode flags from state.md
  _init_build_log(log_path)                       — truncate build.log on new-build start
  _load_briefs()                                  — re-read briefs from references/roles/

Module-level state:
  _ROLE_BRIEFS    — dict[role -> parsed brief]; populated by _load_briefs() at import
  _TUTOR_ENABLED  — bool; True by default (suppressed by --quiet)
  _MODE           — str; "beginner" by default ("advanced" hides tutor lines)

Cross-platform note: ASCII banner symbols by default ("[OK]"/"[FAIL]"/"...") to satisfy
Phase 2's Windows-cmd.exe compatibility mandate. Set OSBUILDER_UNICODE=1 to use ✓/✗.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Literal


REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"
_BRIEF_DIR = REPO_ROOT / "references" / "roles"

FORBIDDEN_JARGON = frozenset([
    "framework", "endpoint", "responsive", "ORM",
    "dependency injection", "transpiler",
])

_ROLE_BRIEFS: dict[str, dict] = {}   # role-name → parsed brief dict; loaded at module import
_TUTOR_ENABLED: bool = True           # default ON; set False by --quiet
_MODE: str = "beginner"               # default; set "advanced" by --advanced flag

Status = Literal["start", "ok", "fail"]


# ---------------------------------------------------------------------------
# Brief parser — pure stdlib regex
# ---------------------------------------------------------------------------


def _parse_brief_markdown(text: str) -> dict:
    """Parse a role-brief Markdown file into structured dict.

    Returns:
      {
        "banner_template": {"start": str, "ok": str, "fail": str},
        "tutor_template": str,
        "tutor_per_step": {step_name: {"banner": str, "tutor": str}},
        "failure_copy": {step_name: str},
      }

    Tolerant of missing sections — callers fall back to generic emit() output.
    """
    result: dict = {
        "banner_template": {},
        "tutor_template": "",
        "tutor_per_step": {},
        "failure_copy": {},
    }
    sections = re.split(r"^## ", text, flags=re.MULTILINE)
    for section in sections[1:]:
        title, _, body = section.partition("\n")
        title_l = title.strip().lower()
        if "banner" in title_l:
            for line in body.splitlines():
                stripped = line.strip()
                for status in ("start", "ok", "fail"):
                    if stripped.startswith(f"{status}:"):
                        result["banner_template"][status] = stripped.split(":", 1)[1].strip()
        elif "tutor template" in title_l:
            for line in body.splitlines():
                stripped = line.strip()
                if stripped.startswith(">"):
                    result["tutor_template"] = stripped.lstrip(">").strip()
                    break
        elif "per-step" in title_l or "per step" in title_l:
            current_step: str | None = None
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                # Top-level step key: matches "step-name:" with no leading spaces
                if re.match(r"^[\w/.\-]+:$", stripped) and not line.startswith((" ", "\t")):
                    current_step = stripped.rstrip(":")
                    result["tutor_per_step"][current_step] = {}
                elif current_step and ":" in stripped and line.startswith((" ", "\t")):
                    k, _, v = stripped.partition(":")
                    result["tutor_per_step"][current_step][k.strip()] = v.strip()
        elif "failure" in title_l:
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
                    continue
                if ":" in stripped:
                    k, _, v = stripped.partition(":")
                    result["failure_copy"][k.strip()] = v.strip()
    return result


def _load_briefs() -> None:
    """Load all role briefs from references/roles/*.md into _ROLE_BRIEFS.

    Graceful degrade: missing directory or unreadable file is non-fatal —
    emit() falls back to a generic banner when no brief is found for a role.
    """
    _ROLE_BRIEFS.clear()
    if not _BRIEF_DIR.is_dir():
        return
    for brief_path in _BRIEF_DIR.glob("*.md"):
        role = brief_path.stem  # "pm", "architect", ...
        try:
            _ROLE_BRIEFS[role] = _parse_brief_markdown(
                brief_path.read_text(encoding="utf-8")
            )
        except Exception:
            # graceful degrade: keep going so a single bad brief never breaks emit()
            pass


# ---------------------------------------------------------------------------
# build.log rotation (Open Question 6)
# ---------------------------------------------------------------------------


def _init_build_log(log_path: Path) -> None:
    """Truncate (not append) build.log at the start of each new build.

    Call this when phase_step==0 (new build starting) or from gsd_driver's
    build-init path. Resolves Open Question 6: build.log must not grow
    unboundedly across builds — each build gets a clean log file.

    Location: .planning/osbuilder/build.log (caller passes in as log_path).
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")  # truncate


# ---------------------------------------------------------------------------
# State refresh — read mode + tutor_enabled from state.md
# ---------------------------------------------------------------------------


def _refresh_state(project_root: Path) -> None:
    """Refresh _TUTOR_ENABLED and _MODE from state.md via state_writer subprocess.

    Mirrors gsd_driver._read_state. Failures (missing state.md, JSON parse error,
    subprocess error) keep the in-memory defaults — emit() continues to function.
    """
    global _TUTOR_ENABLED, _MODE
    try:
        result = subprocess.run(
            [sys.executable, str(STATE_WRITER), "read", "--format", "json",
             "--project-root", str(project_root)],
            capture_output=True, text=True, shell=False, check=False,
        )
        if result.returncode == 0:
            state = json.loads(result.stdout)
            _MODE = state.get("mode", "beginner") or "beginner"
            quiet_val = str(state.get("tutor_enabled", "true")).lower()
            _TUTOR_ENABLED = quiet_val not in ("false", "0", "no")
    except Exception:
        pass  # keep defaults on any failure


# ---------------------------------------------------------------------------
# Banner emission
# ---------------------------------------------------------------------------


def _symbols() -> dict[str, str]:
    """Status → symbol map. ASCII by default; Unicode when OSBUILDER_UNICODE is set."""
    if os.environ.get("OSBUILDER_UNICODE", ""):
        return {"start": "...", "ok": "✓", "fail": "✗"}
    return {"start": "...", "ok": "[OK]", "fail": "[FAIL]"}


def _safe_format(template: str, **ctx: str) -> str:
    """Format template with ctx; on any KeyError/IndexError return template unchanged."""
    try:
        return template.format(**ctx)
    except (KeyError, IndexError, ValueError):
        return template


def emit(role: str, action: str, status: Status, detail: str | None = None) -> None:
    """Render one role banner; in beginner+tutor mode, also emit a '> ' tutor line on 'ok'.

    role:    role-brief stem ("pm","architect","frontend","backend","devops","qa",
             "reviewer","tech-writer"); unknown role → graceful generic banner.
    action:  short action label, used as a Per-Step Copy lookup key. May be a slash
             command like "/gsd-spec-phase" or a free-form phrase like "working".
    status:  "start" | "ok" | "fail".
    detail:  optional extra text appended to the banner / interpolated into the template.
    """
    symbols = _symbols()
    symbol = symbols.get(status, "")
    brief = _ROLE_BRIEFS.get(role)

    # Per-step banner override (used by both branches): role brief may define
    # a friendlier action label for slash commands and known step names.
    per_step_banner: str | None = None
    if brief is not None:
        per_step_banner = (
            brief.get("tutor_per_step", {}).get(action, {}).get("banner")
        )

    display_action = per_step_banner or action

    if brief is None or not brief.get("banner_template"):
        # graceful degrade: plain banner without brief lookup
        suffix = f" — {detail}" if detail else ""
        if status == "start":
            print(f"[{role.upper()}] {display_action}{symbol}{suffix}")
        else:
            print(f"[{role.upper()}] {display_action} {symbol}{suffix}")
    else:
        template = brief["banner_template"].get(status)
        if template is None:
            suffix = f" — {detail}" if detail else ""
            if status == "start":
                print(f"[{role.upper()}] {display_action}{symbol}{suffix}")
            else:
                print(f"[{role.upper()}] {display_action} {symbol}{suffix}")
        else:
            # Templates use literal status markers — replace ✓/✗/... with the
            # currently configured symbol set so OSBUILDER_UNICODE actually flips
            # the rendering. Banner templates may also include {action} / {detail}.
            line = _safe_format(template, action=display_action, detail=detail or "")
            line = line.replace("✓", symbols["ok"]).replace("✗", symbols["fail"])
            print(line)

    # Tutor line: only on success, only in beginner+tutor mode
    if status == "ok" and _TUTOR_ENABLED and _MODE == "beginner":
        tutor_text: str | None = None
        if brief is not None:
            per_step = brief.get("tutor_per_step", {}).get(action, {})
            tutor_text = per_step.get("tutor") or brief.get("tutor_template") or None
        if tutor_text:
            print("> " + _safe_format(
                tutor_text, action=display_action, detail=detail or "",
            ))


# ---------------------------------------------------------------------------
# Subprocess capture — thread-per-stream (cross-platform)
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _drain_stream(stream, lines: list[str], log_handle) -> None:
    """Drain a Popen stream line-by-line; tee to lines list and log file."""
    try:
        for line in iter(stream.readline, ""):
            lines.append(line.rstrip("\n"))
            log_handle.write(line)
            log_handle.flush()
    finally:
        try:
            stream.close()
        except Exception:
            pass


def capture_subprocess(
    cmd: list[str],
    role: str,
    action: str,
    *,
    log_path: Path,
    cwd: Path | None = None,
    timeout: float | None = None,
) -> tuple[int, list[str], list[str]]:
    """Run cmd line-buffered; emit role banner; route raw stdout/stderr to log_path.

    The user only sees role banners. Raw subprocess output goes to log_path (append mode).
    Threads drain stdout and stderr concurrently — works on Windows (where select.select
    cannot poll pipes).

    capture_subprocess is intentionally stateless w.r.t. build lifecycle: it never calls
    _init_build_log(). Callers (gsd_driver) decide when to truncate the log.

    Returns:
        (returncode, stdout_lines, stderr_lines)
    """
    emit(role, action, "start", detail=" ".join(cmd[:2]))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    rc = -1
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n# {_now_iso()} {role} {action}: {' '.join(cmd)}\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
            shell=False,
            cwd=str(cwd) if cwd else None,
        )
        t_out = threading.Thread(
            target=_drain_stream, args=(proc.stdout, stdout_lines, log),
        )
        t_err = threading.Thread(
            target=_drain_stream, args=(proc.stderr, stderr_lines, log),
        )
        t_out.start()
        t_err.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        t_out.join()
        t_err.join()
        rc = proc.returncode if proc.returncode is not None else -1

    if rc == 0:
        emit(role, action, "ok")
    else:
        emit(role, action, "fail", detail="(see debug log)")
    return rc, stdout_lines, stderr_lines


# ---------------------------------------------------------------------------
# Module init
# ---------------------------------------------------------------------------


try:
    _load_briefs()
except Exception:
    pass


if __name__ == "__main__":
    # Tiny CLI shim for ad-hoc testing: `python3 narration.py role action status [detail]`
    if len(sys.argv) >= 4:
        emit(sys.argv[1], sys.argv[2], sys.argv[3],  # type: ignore[arg-type]
             detail=sys.argv[4] if len(sys.argv) > 4 else None)
