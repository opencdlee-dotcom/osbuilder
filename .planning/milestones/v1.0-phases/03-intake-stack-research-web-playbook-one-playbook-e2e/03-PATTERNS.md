# Phase 3: Intake + Stack Research + Web Playbook (One-Playbook E2E) — Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 9 new/modified files
**Analogs found:** 9 / 9

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/intake_handler.py` | utility/script | transform (paragraph/JSON → markdown file) | `scripts/preflight_check.py` | role-match |
| `scripts/stack_researcher.py` | utility/script | request-response (subprocess delegation → structured JSON) | `scripts/preflight_check.py` | role-match |
| `scripts/scaffold_dispatch.py` | utility/script | batch (subprocess chain → files on disk) | `scripts/preflight_check.py` | exact (subprocess + atomic writes + argparse) |
| `scripts/tests/test_intake.py` | test | — | `scripts/tests/test_preflight.py` | exact |
| `scripts/tests/test_stack_researcher.py` | test | — | `scripts/tests/test_preflight.py` | exact |
| `scripts/tests/test_scaffold_dispatch.py` | test | — | `scripts/tests/test_preflight.py` | exact |
| `references/playbooks/web.md` | config/reference doc | — | `references/preflight/README.md` | role-match |
| `references/stack-menu.md` | config/reference doc | — | `references/preflight/README.md` | role-match |
| `references/question-bank.md` | config/reference doc | — | `references/preflight/README.md` | role-match |
| `scripts/state_writer.py` (modify) | utility/script | CRUD | `scripts/state_writer.py` itself | self (extend existing pattern) |

---

## Pattern Assignments

### `scripts/intake_handler.py` (utility, transform)

**Analog:** `scripts/preflight_check.py`

**Imports pattern** (preflight_check.py lines 23–33):
```python
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
```
Copy this block verbatim. `intake_handler.py` uses `argparse`, `json`, `pathlib.Path`, and `sys`; drop `subprocess`, `platform`, `shutil`, `dataclasses` since intake does not shell out or detect OS.

**Module-level docstring pattern** (preflight_check.py lines 1–21):
```python
"""intake_handler.py — OSBuilder intake handler.

Parses a plain-English paragraph OR a structured JSON/markdown spec into a
canonical derived_spec.md at <project-root>/.planning/osbuilder/derived_spec.md.
Writes state.md fields: goal, app_type, playbook.

Pure stdlib — no third-party deps.

Subcommands:
  parse     Parse paragraph or structured spec → derived_spec.md (IN-01, IN-02).
  validate  Check derived_spec.md format is suitable for /gsd-new-project --auto (IN-05).
"""
```
Adapt the triple-quoted docstring to describe intake_handler's subcommands; keep the "Pure stdlib" and subcommand table pattern.

**Atomic write pattern** (preflight_check.py lines 59–71 / state_writer.py lines 100–112):
```python
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
```
Copy verbatim — both analog files use this identical function. `intake_handler.py` uses it to write `derived_spec.md`.

**Path helper pattern** (preflight_check.py lines 49–54):
```python
def _derived_spec_path(project_root: Path) -> Path:
    return project_root / ".planning" / "osbuilder" / "derived_spec.md"
```
Adapt `_install_log_path()` → `_derived_spec_path()`. Use a function (not a module-level constant) so monkeypatching `Path.home` works in tests.

**Input validation pattern** (state_writer.py lines 48–54):
```python
def _check_value_safe(value: str) -> None:
    """V5 input + V12 path-traversal: reject newlines and `..` in --value."""
    if "\n" in value or "\r" in value:
        raise SystemExit("OSBuilder: --value cannot contain newline characters.")
    if ".." in value:
        raise SystemExit("OSBuilder: --value cannot contain '..' (path traversal).")
```
Apply to the `project_name` field from intake. Also validate `project_name` against `[a-zA-Z0-9_-]` only before passing anywhere (SECURITY — path traversal mitigation from RESEARCH.md).

**argparse dispatch pattern** (preflight_check.py lines 533–595):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="intake_handler",
        description="OSBuilder intake handler.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_parse = sub.add_parser("parse", help="parse input → derived_spec.md")
    p_parse.add_argument("--input", required=True,
                         help="paragraph string or path to structured spec file")
    p_parse.add_argument("--project-root", default=None)

    p_validate = sub.add_parser("validate", help="check derived_spec.md format")
    p_validate.add_argument("--project-root", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "parse":
        return _cmd_parse(args)
    if args.cmd == "validate":
        return _cmd_validate(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```
Copy the `main()` → subparser → dispatch → `raise SystemExit(main())` shell from preflight_check.py. Keep `if __name__ == "__main__": raise SystemExit(main())` exactly.

**Error handling pattern** (preflight_check.py lines 468–491 / state_writer.py lines 281–287):
```python
# state_writer.py pattern — wrap main() body in try/except
try:
    return args.func(args)
except SystemExit:
    raise
except Exception as e:
    sys.stderr.write(f"OSBuilder: error — {e}\n")
    return 1
```
Use `raise SystemExit(...)` for user-facing failures (unknown field, missing file). Propagate `SystemExit` through; catch generic `Exception` only at the `main()` boundary.

---

### `scripts/stack_researcher.py` (utility, request-response)

**Analog:** `scripts/preflight_check.py`

**Imports pattern** (preflight_check.py lines 23–33):
```python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
```
`stack_researcher.py` needs `subprocess` (for brainiac delegation), `json` (parse result + write stack_choices), `pathlib` (read stack-menu.md fallback). Drop `datetime`, `platform`, `shutil`, `dataclasses`, `os`.

**Subprocess pattern — list form, no shell=True** (preflight_check.py lines 462–468):
```python
result = subprocess.run(
    action.install_argv,   # list form — never shell=True
    shell=False,
    capture_output=cap,
    text=cap,
    check=False,
)
```
Adapt for brainiac invocation:
```python
result = subprocess.run(
    ["python3", "-m", "brainiac", "scan", query],
    shell=False,
    capture_output=True,
    text=True,
    timeout=30,   # RES-03: 30-second timeout before stack-menu fallback
    check=False,
)
```
Never use `shell=True`. Use list-form argv. `timeout=30` triggers the fallback path (Pitfall 7 mitigation).

**Fallback-read pattern** (preflight_check.py `_read_no_docker_config` lines 199–207):
```python
def _read_stack_menu(references_root: Path) -> dict:
    """RES-03 fallback: read stack-menu.md when brainiac times out."""
    p = references_root / "stack-menu.md"
    if not p.exists():
        return {}
    try:
        content = p.read_text(encoding="utf-8")
        # parse markdown table or structured section into dict
        ...
        return parsed
    except Exception:
        return {}
```
Pattern: read the fallback file, return empty dict on any failure (never raise from the fallback path).

**State.md write pattern** (state_writer.py lines 151–163):
```python
# Call state_writer.py as subprocess — same pattern as scaffold_dispatch.py
subprocess.run(
    [sys.executable, str(STATE_WRITER), "write",
     "--field", "stack_choices", "--value", json.dumps(stack_choices)],
    check=True,
)
```
Or import and call `write_state()` directly if state_writer.py is on `sys.path`. Follow the same call site pattern as `test_state_writer.py` uses `run_state_writer()`.

**Main/argparse pattern** (same as intake_handler.py above — copy from preflight_check.py lines 533–595):
```python
def main(argv: list[str] | None = None) -> int:
    ...
    p_research = sub.add_parser("research", help="research stack for app_type")
    p_research.add_argument("--app-type", required=True)
    p_research.add_argument("--advanced-overrides", default=None,
                            help="JSON string of user overrides (--advanced flag path)")
    p_research.add_argument("--project-root", default=None)
    ...

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### `scripts/scaffold_dispatch.py` (utility, batch)

**Analog:** `scripts/preflight_check.py` — exact match (subprocess chain, argparse, atomic file writes, rollback on failure)

**Imports pattern** (preflight_check.py lines 23–33):
```python
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
```

**pnpm detection + install pattern** (mirrors preflight_check.py `detect()` + `apply()` pattern):
```python
import shutil

def _ensure_pnpm() -> None:
    """Install pnpm via npm if absent (Pitfall 5 mitigation)."""
    if shutil.which("pnpm") is not None:
        return
    subprocess.run(
        ["npm", "install", "-g", "pnpm@latest"],
        shell=False,
        check=True,
    )
```
Pattern mirrors `_probe_version()` in preflight_check.py (lines 161–172): use `shutil.which` for detection, then `subprocess.run([..], shell=False, check=True)` for install.

**Non-interactive subprocess pattern — verified command** (RESEARCH.md Pattern 1 / preflight_check.py `apply()` lines 462–491):
```python
def scaffold_web(project_name: str, project_root: Path) -> Path:
    """Run create-next-app in fully non-interactive mode."""
    cmd = [
        "pnpm", "create", "next-app@latest", project_name,
        "--typescript",
        "--tailwind",
        "--app",
        "--src-dir",
        "--eslint",
        "--use-pnpm",
        "--disable-git",
        "--import-alias", "@/*",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return project_root / project_name
```
This is the exact RESEARCH.md verified command. Shell=False, list-form argv, `cwd=str(project_root)`, `check=True`. No `--yes` (Pitfall 1 mitigation).

**Atomic write for post-scaffold files** (preflight_check.py lines 59–71):
```python
# Use atomic_write() for every post-scaffold file OSBuilder writes:
# src/lib/db.ts, drizzle.config.ts, .env.example, compose.yaml
atomic_write(project_dir / "src" / "lib" / "db.ts", DB_TS_CONTENT)
atomic_write(project_dir / "drizzle.config.ts", DRIZZLE_CONFIG_CONTENT)
atomic_write(project_dir / ".env.example", ENV_EXAMPLE_CONTENT)
atomic_write(project_dir / "compose.yaml", COMPOSE_YAML_CONTENT)
```
Copy `atomic_write()` verbatim from preflight_check.py lines 59–71 or import from state_writer.py.

**State.md write pattern** (state_writer.py `_cmd_write` lines 151–163):
```python
# Write project_path to state.md after scaffold completes
subprocess.run(
    [sys.executable, STATE_WRITER, "write",
     "--field", "project_path", "--value", str(scaffolded_dir)],
    check=True,
)
```

**Error handling on subprocess failure** (preflight_check.py `apply()` lines 468–491):
```python
try:
    result = subprocess.run(cmd, ...)
except (FileNotFoundError, OSError) as e:
    sys.stderr.write(f"OSBuilder: scaffold failed: {e}\n")
    return 1
if result.returncode != 0:
    sys.stderr.write(
        f"OSBuilder: create-next-app exited {result.returncode}\n"
    )
    return 1
```
Catch `FileNotFoundError` (pnpm not found) and `OSError`. Check `returncode`. Write to `sys.stderr`. Return non-zero int.

**Main/argparse pattern** (preflight_check.py lines 533–595):
```python
def main(argv: list[str] | None = None) -> int:
    ...
    p_scaffold = sub.add_parser("scaffold", help="run create-next-app + Drizzle wiring")
    p_scaffold.add_argument("--project-name", required=True)
    p_scaffold.add_argument("--project-root", default=None)
    p_scaffold.add_argument("--playbook", default="web")
    ...

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### `scripts/tests/test_intake.py` (test)

**Analog:** `scripts/tests/test_preflight.py`

**File header + lazy import pattern** (test_preflight.py lines 1–23):
```python
"""Tests for scripts/intake_handler.py — IN-01..IN-05.

All tests in this file FAIL before Wave 1 lands.
That is by design (TDD RED state).
"""
from __future__ import annotations
import importlib
import pytest


@pytest.fixture
def ih():
    """Lazy import of scripts/intake_handler.py — skips when not yet created."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")
```
Copy this lazy-import fixture pattern exactly. Name the fixture `ih` (intake handler). The lazy import allows `--collect-only` to collect all stubs even before the module exists.

**Fixture usage pattern** (test_preflight.py lines 26–33):
```python
def test_paragraph_to_derived_spec(ih, tmp_project_root):
    """IN-01: paragraph input → derived_spec.md exists on disk with required sections."""
    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    ih.parse_paragraph("I want a website where students upload lab reports", tmp_project_root)
    assert spec_path.exists(), "derived_spec.md must be written to disk"
    content = spec_path.read_text(encoding="utf-8")
    assert "**Goal:**" in content
    assert "**App type:**" in content
```
Use `tmp_project_root` fixture from `conftest.py` (lines 17–20). Assert file existence + content sections. Match existing test style: one behavior per function, inline assertion messages.

**Monkeypatch pattern for external calls** (test_preflight.py lines 47–54):
```python
def test_questions_have_no_jargon(ih):
    """IN-03: question-bank.md contains no jargon words."""
    import re
    JARGON = {"responsive", "ORM", "framework", "endpoint", "middleware",
               "hydration", "SSR", "SSG", "CDN", "schema", "migration"}
    bank_path = Path(__file__).resolve().parents[2] / "references" / "question-bank.md"
    if not bank_path.exists():
        pytest.skip("question-bank.md not yet created (Wave 1 target)")
    content = bank_path.read_text(encoding="utf-8")
    found = {w for w in JARGON if re.search(rf'\b{w}\b', content, re.IGNORECASE)}
    assert not found, f"question-bank.md contains jargon: {found}"
```
Pattern: resolve reference file path relative to `__file__` parents; skip if file not yet created; regex-check content.

---

### `scripts/tests/test_stack_researcher.py` (test)

**Analog:** `scripts/tests/test_preflight.py`

**Lazy import fixture** (adapt from test_preflight.py lines 17–23):
```python
@pytest.fixture
def sr():
    """Lazy import of scripts/stack_researcher.py."""
    try:
        return importlib.import_module("stack_researcher")
    except ImportError:
        pytest.skip("stack_researcher module not yet created (Wave 1 target)")
```

**Mocking subprocess for brainiac** (test_preflight.py `fake_shell` fixture from conftest.py lines 80–85):
```python
def test_calls_brainiac(sr, fake_shell, tmp_project_root):
    """RES-01: stack_researcher calls brainiac subprocess and returns structured result."""
    fake_shell.program("python3 -m brainiac scan", returncode=0,
                       stdout='{"framework": {"name": "next.js", "version": "16.2.4"}}')
    result = sr.research(app_type="web", project_root=tmp_project_root)
    assert "framework" in result
    brainiac_calls = [c for c in fake_shell.calls if "brainiac" in str(c[0])]
    assert len(brainiac_calls) >= 1, "stack_researcher must call brainiac subprocess"
```
`fake_shell` from `conftest.py` intercepts `subprocess.run` calls. Program a brainiac response, verify the call was made and the output was parsed.

**Fallback test pattern** (adapt from test_preflight.py `test_no_docker_mode_skips_docker` lines 226–240):
```python
def test_fallback_to_stack_menu(sr, fake_shell, tmp_project_root):
    """RES-03: returns stack-menu defaults when brainiac times out."""
    # Program brainiac to return empty (simulate timeout fallback)
    fake_shell.program("python3 -m brainiac scan", returncode=0, stdout="")
    result = sr.research(app_type="web", project_root=tmp_project_root)
    # Must still return a non-empty dict (from stack-menu.md fallback)
    assert result, "fallback must return non-empty stack_choices"
    assert "framework" in result, "fallback must include framework key"
```

---

### `scripts/tests/test_scaffold_dispatch.py` (test)

**Analog:** `scripts/tests/test_preflight.py`

**Lazy import fixture** (same pattern):
```python
@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet created (Wave 1 target)")
```

**Subprocess mock for scaffold command** (test_preflight.py `test_macos_uses_brew` lines 84–95):
```python
def test_scaffold_cmd_flags(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: scaffold_dispatch runs create-next-app with correct flags."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    scaffold_calls = [s for s in signatures if "next-app@latest" in s]
    assert len(scaffold_calls) == 1, "Expected exactly one create-next-app call"
    cmd = scaffold_calls[0]
    assert "--typescript" in cmd
    assert "--tailwind" in cmd
    assert "--app" in cmd
    assert "--disable-git" in cmd
    assert "--yes" not in cmd, "--yes must NOT be used (Pitfall 1)"
```
Use `fake_shell` + `fake_which` from conftest. Check call signatures with `" ".join(c[0])` exactly as test_preflight.py does (lines 142–150).

**Post-scaffold file write tests** (test_preflight.py `test_dry_run_no_state_change` pattern):
```python
def test_db_ts_written(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: post-scaffold writes src/lib/db.ts with drizzle import."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    db_ts = project_dir / "src" / "lib" / "db.ts"
    assert db_ts.exists(), "src/lib/db.ts must be written"
    content = db_ts.read_text(encoding="utf-8")
    assert "drizzle-orm/postgres-js" in content
    assert "process.env.DATABASE_URL" in content
```

**Compose file name test** (specific to Pitfall 3 — Compose v2 filename):
```python
def test_compose_yaml_written(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: writes compose.yaml (not docker-compose.yml) — Compose v2 filename."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    assert (project_dir / "compose.yaml").exists(), "Must write compose.yaml (Compose v2)"
    assert not (project_dir / "docker-compose.yml").exists(), (
        "Must NOT write docker-compose.yml (deprecated Compose v1 filename)"
    )
```

---

### `references/playbooks/web.md` (reference doc)

**Analog:** `references/preflight/README.md`

**Document structure pattern** (references/preflight/README.md lines 1–72):
```markdown
# OSBuilder Web Playbook

> Specification for the web scaffold path (app_type: web).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md
> (locked at ≤ 200 lines; see Phase 1 Plan 01-02).

## What the web playbook produces
[brief description]

## Scaffold command (non-interactive)
[exact verified command from RESEARCH.md Pattern 1]

## Post-scaffold files written by OSBuilder
[list: src/lib/db.ts, drizzle.config.ts, .env.example, compose.yaml]

## Files OSBuilder must NOT write
[list: package.json, tsconfig.json, .eslintrc.json, next.config.ts, etc.]

## Refuse list
[K8s, microservices, etc. — per CLAUDE.md constraints]

## Stack (pinned versions)
[table: create-next-app 16.2.4, drizzle-orm 0.45.2, etc.]

## See also
[links to RESEARCH.md, stack-menu.md]
```
Pattern: lead with a blockquote explaining load-on-demand + ≤200-line SKILL.md constraint. Use `##` sections with imperative headers. End with "See also" cross-references. Keep prose minimal — bullet lists and tables over paragraphs.

---

### `references/stack-menu.md` (reference doc)

**Analog:** `references/preflight/README.md`

**Document structure pattern**:
```markdown
# OSBuilder Stack Menu — Web Playbook Defaults

> Fallback defaults loaded by `stack_researcher.py` when `/brainiac` times out
> or returns low-confidence results (RES-03).
> Loaded on-demand — not pulled into SKILL.md.

## Web playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| Framework | next.js (create-next-app) | 16.2.4 | ... |
| ORM | drizzle-orm | 0.45.2 | ... |
| ...       | ...     | ...     | ... |

## How stack_researcher.py reads this file
[brief: looks for the table in "## Web playbook defaults" section]

## Updating defaults
[instructions for when to bump versions]
```
Pattern: same load-on-demand blockquote at top, table-first structure, explicit "how this file is consumed" section.

---

### `references/question-bank.md` (reference doc)

**Analog:** `references/preflight/README.md`

**Document structure pattern**:
```markdown
# OSBuilder Question Bank — Web Playbook (v1)

> Plain-English clarifying questions for the PM role intake flow.
> Loaded on-demand by SKILL.md. NOT pulled into SKILL.md (≤ 200 line limit).
> Ask ≤ 5 questions per build. Never ask all questions.

## Q: Devices
"Should this work on phones and tablets too, or just on desktop computers?"
- Yes, phones too → [mobile-responsive scaffold flag]
- Just desktop is fine → [desktop-only note in spec]
- I don't know, you decide → YES (mobile-responsive default)

## Q: ...
[follow same 3-option format for each question]

## Jargon ban
Never use: responsive, ORM, framework, endpoint, middleware, hydration,
SSR, SSG, CDN, schema, migration.
```
One `##` section per question, identical 3-option bullet format, jargon-ban section at bottom.

---

### `scripts/state_writer.py` (modify — ALLOWED_FIELDS extension)

**Analog:** `scripts/state_writer.py` itself

**Current ALLOWED_FIELDS pattern** (state_writer.py lines 29–34):
```python
REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
)
COUNTER_FIELDS = ("retry_count", "escalation_level", "phase_step")
ALLOWED_FIELDS = set(REQUIRED_FIELDS)
```

**Target pattern after Phase 3 extension:**
```python
REQUIRED_FIELDS = (
    "goal", "app_type", "playbook", "current_role", "current_phase",
    "phase_step", "last_failure", "retry_count", "escalation_level", "next_action",
)
COUNTER_FIELDS = ("retry_count", "escalation_level", "phase_step")
# Phase 3 fields: optional (in ALLOWED_FIELDS, NOT in REQUIRED_FIELDS)
# so Phase 1/2 state files continue to pass `validate` without these fields.
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    "project_path",   # absolute path to scaffolded project on disk
    "stack_choices",  # JSON string: researched/confirmed stack (RES-02)
    "stack_overrides", # JSON string: --advanced user overrides (RES-04)
}
```
Key rule from RESEARCH.md Open Questions #1: add to `ALLOWED_FIELDS` only, NOT to `REQUIRED_FIELDS`. This keeps Phase 1/2 state files valid under `validate`. The `_check_field_allowed()` function (state_writer.py lines 39–45) automatically enforces the extended set without any other changes.

**render_state_md must not change** (state_writer.py lines 79–85):
```python
def render_state_md(fields: dict) -> str:
    """Render a 10-field state.md content string. ~13 lines."""
    lines = ["# OSBuilder State", ""]
    for f in REQUIRED_FIELDS:
        lines.append(f"{f}: {fields.get(f, '')}")
    lines.append(f"updated_at: {fields.get('updated_at', _now_iso())}")
    return "\n".join(lines) + "\n"
```
`render_state_md` iterates `REQUIRED_FIELDS` only. The 3 new Phase 3 fields are written by `write_state()` as extra keys in the `fields` dict — they appear in state.md as additional `key: value` lines after the 10 required fields. `parse_state_md()` (lines 88–97) is tolerant and reads any `key: value` line, so no changes to the parser are needed.

---

## Shared Patterns

### Stdlib-only imports
**Source:** `scripts/preflight_check.py` (lines 23–33) and `scripts/state_writer.py` (lines 20–28)
**Apply to:** All three new scripts (`intake_handler.py`, `stack_researcher.py`, `scaffold_dispatch.py`)
```python
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
```
No third-party imports. Pure stdlib. `from __future__ import annotations` on every file.

### Atomic write
**Source:** `scripts/preflight_check.py` lines 59–71 (or `scripts/state_writer.py` lines 100–112 — identical)
**Apply to:** `intake_handler.py` (write derived_spec.md), `scaffold_dispatch.py` (write post-scaffold files)
```python
def atomic_write(path: Path, content: str) -> None:
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
```

### Subprocess list-form, no shell=True
**Source:** `scripts/preflight_check.py` `apply()` lines 462–468
**Apply to:** `stack_researcher.py` (brainiac call), `scaffold_dispatch.py` (pnpm calls, npm install-g pnpm)
```python
subprocess.run(cmd_list, shell=False, capture_output=True, text=True, check=False)
```
Never interpolate user input into a shell string. Always pass argv as a list.

### Input validation — V5 allowlist + path-traversal
**Source:** `scripts/state_writer.py` lines 39–54
**Apply to:** `intake_handler.py` (project_name from intake), `scaffold_dispatch.py` (project_name arg)
```python
def _check_value_safe(value: str) -> None:
    if "\n" in value or "\r" in value:
        raise SystemExit("OSBuilder: --value cannot contain newline characters.")
    if ".." in value:
        raise SystemExit("OSBuilder: --value cannot contain '..' (path traversal).")
```

### Error exit pattern
**Source:** `scripts/state_writer.py` lines 281–287
**Apply to:** All three new scripts
```python
try:
    return args.func(args)
except SystemExit:
    raise
except Exception as e:
    sys.stderr.write(f"OSBuilder: error — {e}\n")
    return 1
```

### Lazy import fixture (test files)
**Source:** `scripts/tests/test_preflight.py` lines 17–23
**Apply to:** All three new test files (`test_intake.py`, `test_stack_researcher.py`, `test_scaffold_dispatch.py`)
```python
@pytest.fixture
def <name>():
    try:
        return importlib.import_module("<module_name>")
    except ImportError:
        pytest.skip("<module_name> module not yet created (Wave 1 target)")
```
This pattern lets `--collect-only` collect all RED stubs before the module is written.

### `fake_shell` + `fake_which` fixture usage
**Source:** `scripts/tests/conftest.py` lines 54–92
**Apply to:** All three new test files
```python
def test_example(sd, fake_shell, fake_which, tmp_project_root):
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0)
    # ... call subject under test ...
    signatures = [" ".join(c[0]) if isinstance(c[0], list) else c[0]
                  for c in fake_shell.calls]
```
`fake_shell` is automatically injected via `conftest.py` — it patches `subprocess.run`. `fake_which` patches `shutil.which`. Both fixtures require no additional setup beyond parameter declaration.

### Reference doc structure
**Source:** `references/preflight/README.md` (full file, 72 lines)
**Apply to:** `references/playbooks/web.md`, `references/stack-menu.md`, `references/question-bank.md`
- Lead with blockquote: "Loaded on-demand. NOT pulled into SKILL.md (≤ 200 lines)."
- Use `##` sections with imperative-noun headers.
- Tables for structured data (versions, matrices).
- End with "See also" cross-references.
- Keep each reference doc under ~80 lines.

### `if __name__ == "__main__": raise SystemExit(main())`
**Source:** `scripts/preflight_check.py` line 595 / `scripts/state_writer.py` line 291
**Apply to:** All three new scripts
```python
if __name__ == "__main__":
    raise SystemExit(main())
```

---

## No Analog Found

All files have analogs. No entries in this section.

---

## Metadata

**Analog search scope:** `scripts/`, `scripts/tests/`, `references/`
**Files scanned:** 5 (preflight_check.py, state_writer.py, test_preflight.py, conftest.py, references/preflight/README.md)
**Pattern extraction date:** 2026-04-30
