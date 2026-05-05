# Phase 5: Common-person UX polish — Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 22 (7 new scripts/modules + 7 new role briefs + 2 new data files + 6 modified scripts)
**Analogs found:** 22 / 22

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/narration.py` | script-module | event-driven | `scripts/failure_classifier.py` | role-match |
| `scripts/friendly_error.py` | script-module | transform | `scripts/failure_classifier.py` | exact |
| `scripts/tests/test_narration.py` | test-suite | request-response | `scripts/tests/test_gsd_driver.py` | exact |
| `scripts/tests/test_friendly_error.py` | test-suite | request-response | `scripts/tests/test_failure_classifier.py` | exact |
| `scripts/tests/test_tutor_mode.py` | test-suite | request-response | `scripts/tests/test_gsd_driver.py` | role-match |
| `scripts/tests/test_mode_gating.py` | test-suite | request-response | `scripts/tests/test_intake.py` | role-match |
| `scripts/tests/test_tech_writer.py` | test-suite | request-response | `scripts/tests/test_gsd_driver.py` | role-match |
| `references/roles/pm.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/architect.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/frontend.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/backend.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/devops.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/reviewer.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/roles/tech-writer.md` | role-brief | event-driven | `references/roles/qa.md` | exact |
| `references/friendly-errors/dictionary.yaml` | dictionary-data | transform | `scripts/failure_classifier.py` (pattern lists) | role-match |
| `references/friendly-errors/README.md` | documentation | — | `references/roles/qa.md` | role-match |
| `scripts/gsd_driver.py` (modified) | wiring-edit | event-driven | itself (PHASE_STEP_COMMANDS at lines 32–43) | exact |
| `scripts/state_writer.py` (modified) | state-extension | CRUD | itself (ALLOWED_FIELDS at lines 36–44) | exact |
| `scripts/preflight_check.py` (modified) | wiring-edit | request-response | `scripts/scaffold_dispatch.py` error paths | exact |
| `scripts/scaffold_dispatch.py` (modified) | wiring-edit | request-response | itself (error paths at lines 140–145) | exact |
| `scripts/stack_researcher.py` (modified) | wiring-edit | request-response | itself (mode-gate site at line 107) | exact |
| `scripts/intake_handler.py` (modified) | wiring-edit | request-response | itself (parse_paragraph at line 93) | exact |

---

## Pattern Assignments

### `scripts/narration.py` (script-module, event-driven)

**Analog:** `scripts/failure_classifier.py`

**Imports pattern** (failure_classifier.py lines 1–21):
```python
#!/usr/bin/env python3
"""narration.py — OSBuilder role-banner + tutor-mode emitter."""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path
import re
import sys
from typing import Literal
```

**Module-level constants pattern** (failure_classifier.py lines 27–65 — dictionary lists):
```python
# Module-init constants — same pattern as failure_classifier's PATTERN lists
REPO_ROOT = Path(__file__).resolve().parent.parent
_BRIEF_DIR = REPO_ROOT / "references" / "roles"
_FORBIDDEN_JARGON = frozenset([
    "framework", "endpoint", "responsive", "ORM",
    "dependency injection", "transpiler",
])
_ROLE_BRIEFS: dict[str, dict] = {}  # loaded at module import, keyed by role name
_TUTOR_ENABLED: bool = True          # default ON; overridden by --quiet
_MODE: str = "beginner"              # default; overridden by --advanced
```

**State-read pattern** (gsd_driver.py `_read_state` lines 82–93):
```python
def _refresh_state(project_root: Path) -> None:
    """Snapshot mode + tutor_enabled from state.md once per session.

    Mirrors gsd_driver._read_state: calls state_writer subprocess, parses JSON.
    Cached for the session — never called on every emit() (Pitfall 5).
    """
    global _TUTOR_ENABLED, _MODE
    result = subprocess.run(
        [sys.executable, str(STATE_WRITER), "read", "--format", "json",
         "--project-root", str(project_root)],
        capture_output=True, text=True, shell=False, check=False,
    )
    if result.returncode == 0:
        import json
        state = json.loads(result.stdout)
        _MODE = state.get("mode", "beginner")
        _TUTOR_ENABLED = state.get("tutor_enabled", "true").lower() not in ("false", "0", "no")
```

**Core emit pattern** (RESEARCH.md Pattern 2, lines 369–421):
```python
Status = Literal["start", "ok", "fail"]

def emit(role: str, action: str, status: Status, detail: str | None = None) -> None:
    """Render one role-banner line; if status="ok" and tutor enabled, emit tutor line."""
    brief = _ROLE_BRIEFS.get(role)
    symbol = {"start": "...", "ok": "✓", "fail": "✗"}[status]
    if brief is None:
        suffix = f" — {detail}" if detail else ""
        print(f"[{role.upper()}] {action}{symbol}{suffix}")
        return
    template = brief["banner_template"][status]
    print(template.format(action=action, detail=detail or ""))
    if status == "ok" and _TUTOR_ENABLED and _MODE == "beginner":
        tutor_template = brief.get("tutor_per_step", {}).get(action, brief["tutor_template"])
        print("> " + tutor_template.format(action=action, detail=detail or ""))
```

**Subprocess capture pattern** (RESEARCH.md Pattern 1, lines 291–356 — thread-per-stream):
```python
def _drain_stream(stream, lines: list[str], log_handle) -> None:
    for line in iter(stream.readline, ""):
        lines.append(line.rstrip("\n"))
        log_handle.write(line)
        log_handle.flush()
    stream.close()

def capture_subprocess(
    cmd: list[str], role: str, action: str,
    *, log_path: Path, cwd: Path | None = None, timeout: float | None = None,
) -> tuple[int, list[str], list[str]]:
    """Run cmd line-buffered; return (rc, stdout_lines, stderr_lines).
    Raw output appended to log_path. User sees only role banner.
    """
    emit(role, action, "start", detail=" ".join(cmd[:2]))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=1, text=True, shell=False,
            cwd=str(cwd) if cwd else None,
        )
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        t_out = threading.Thread(target=_drain_stream, args=(proc.stdout, stdout_lines, log))
        t_err = threading.Thread(target=_drain_stream, args=(proc.stderr, stderr_lines, log))
        t_out.start(); t_err.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()
        t_out.join(); t_err.join()
    if proc.returncode == 0:
        emit(role, action, "ok")
    else:
        emit(role, action, "fail", detail="(see debug log)")
    return proc.returncode, stdout_lines, stderr_lines
```

**Brief parser pattern** (RESEARCH.md Pattern 3, lines 429–466):
```python
def _parse_brief_markdown(text: str) -> dict:
    """Parse H2 sections from a role brief. Stdlib only — re.split on ## headings."""
    sections = re.split(r"^## ", text, flags=re.MULTILINE)
    result = {"banner_template": {}, "tutor_template": "", "tutor_per_step": {}, "failure_copy": {}}
    for section in sections[1:]:
        title, _, body = section.partition("\n")
        title = title.strip().lower()
        if "banner" in title:
            for line in body.splitlines():
                for status in ("start", "ok", "fail"):
                    if line.strip().startswith(f"{status}:"):
                        result["banner_template"][status] = line.split(":", 1)[1].strip()
        elif "tutor template" in title:
            for line in body.splitlines():
                if line.strip().startswith(">"):
                    result["tutor_template"] = line.strip().lstrip(">").strip()
        elif "per-step" in title or "per step" in title:
            # key: value blocks under H3 headings
            current_step = None
            for line in body.splitlines():
                if re.match(r"^\w[\w-]*:$", line.strip()):
                    current_step = line.strip().rstrip(":")
                    result["tutor_per_step"][current_step] = {}
                elif current_step and ":" in line:
                    k, _, v = line.strip().partition(":")
                    result["tutor_per_step"][current_step][k.strip()] = v.strip()
        elif "failure" in title:
            for line in body.splitlines():
                if ":" in line:
                    k, _, v = line.strip().partition(":")
                    result["failure_copy"][k.strip()] = v.strip()
    return result
```

---

### `scripts/friendly_error.py` (script-module, transform)

**Analog:** `scripts/failure_classifier.py`

**Imports + module shape** (failure_classifier.py lines 1–21, dataclass pattern from preflight_check.py lines 80–100):
```python
#!/usr/bin/env python3
"""friendly_error.py — OSBuilder raw-error → FriendlyMessage translator."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
DICTIONARY_PATH = REPO_ROOT / "references" / "friendly-errors" / "dictionary.yaml"
```

**Dataclass shape** (preflight_check.py `ToolStatus` at lines 81–88, adapted):
```python
Severity = Literal["info", "warn", "error", "fatal"]

@dataclass
class FriendlyMessage:
    title: str
    what_broke: str
    what_to_do: str
    copy_paste: str | None
    severity: Severity
```

**Pattern dictionary + classify pattern** (failure_classifier.py lines 27–75 — ORDER MATTERS comment + `_matches`):
```python
_DICTIONARY: list[dict] = []  # loaded at module import

def load_dictionary(path: Path = DICTIONARY_PATH) -> list[dict]:
    """Load + validate dictionary. Format-version check mirrors failure_classifier's
    pattern-list initialization: fail fast with clear error on malformed input."""
    global _DICTIONARY
    raw = path.read_text(encoding="utf-8")
    parsed = _parse_yaml_subset(raw)
    if not parsed or parsed[0].get("format_version") != "1.0":
        raise SystemExit(
            "OSBuilder: friendly-errors dictionary format-version mismatch. "
            "Expected 1.0; got " + str(parsed[0].get("format_version") if parsed else None)
        )
    _DICTIONARY = parsed[1:]
    if len(_DICTIONARY) < 30:
        raise SystemExit(f"OSBuilder: dictionary has {len(_DICTIONARY)} entries; expected >= 30.")
    return _DICTIONARY
```

**Core translate function** (mirrors failure_classifier.py `classify` at lines 83–138 — first-match + fallback pattern):
```python
def translate(raw_error: str | Exception, ctx: dict | None = None) -> FriendlyMessage:
    """Pure translator. First-match over dictionary; generic fallback.
    ORDER MATTERS — same rule as failure_classifier.py:
    VALIDATION_FAILURE_PATTERNS checked before TRANSIENT to prevent overlap.
    Here: specific patterns (e.g., 'pnpm-not-found') before generic (e.g., 'enoent-generic').
    """
    text = str(raw_error)
    ctx = ctx or {}
    for entry in _DICTIONARY:
        pattern = entry["match_pattern"]
        is_regex = entry.get("pattern_type", "substring") == "regex"
        if (is_regex and re.search(pattern, text)) or (not is_regex and pattern in text):
            return _build_message(entry, ctx)
    return _generic_translator(text, ctx)
```

**Traceback-strip pattern** (RESEARCH.md Example 1, lines 930–946):
```python
def _strip_tracebacks(text: str) -> str:
    """Remove Python tracebacks and Node stack frames.
    Same regex patterns as narration.py's acceptance check."""
    lines = text.splitlines()
    out = []
    in_py_tb = False
    for line in lines:
        if line.startswith("Traceback (most recent"):
            in_py_tb = True; continue
        if in_py_tb:
            if line.startswith(" ") or line.startswith("\t") or 'File "' in line:
                continue
            in_py_tb = False
        if re.match(r"^\s+at .+\(.+:\d+\)$", line):  # Node stack frame
            continue
        out.append(line)
    return "\n".join(out)
```

**Module-init load** (failure_classifier.py has no module-init — but registry_verify.py and stack_researcher.py demonstrate the load-on-import pattern):
```python
# Module-init: load dictionary so translate() is ready from first import
try:
    load_dictionary()
except (FileNotFoundError, SystemExit):
    pass  # allow import even if dictionary not yet created; raise on first translate()
```

**CLI shim** (failure_classifier.py `main` at lines 264–278 — same compact pattern):
```python
if __name__ == "__main__":
    import sys
    msg = translate(sys.stdin.read())
    print(f"## {msg.title}\n\n{msg.what_broke}\n\n**What to do:** {msg.what_to_do}")
    if msg.copy_paste:
        print(f"\n```\n{msg.copy_paste}\n```")
```

---

### `references/friendly-errors/dictionary.yaml` (dictionary-data, transform)

**Analog:** `scripts/failure_classifier.py` pattern lists (lines 27–59)

**Structural pattern** — failure_classifier uses ordered Python lists where ORDER MATTERS (comment at line 29). The YAML dictionary follows the same rule: more-specific entries before generic. Failure_classifier's 4-class architecture maps to dictionary's `category` field with 9 values.

**The 30 seed entries** are documented verbatim in RESEARCH.md lines 690–721. The planner must write each as a YAML block with 8 fields: `id`, `match_pattern`, `pattern_type` (implicit `substring` unless regex), `category`, `title`, `what_broke`, `what_to_do`, `copy_paste_command`, `phase_seen`, `expansion_note`.

**Format-version metadata block** (first entry in file — mirrors failure_classifier's module-level constants):
```yaml
- format_version: "1.0"
  schema_fields:
    - id
    - match_pattern
    - category
    - title
    - what_broke
    - what_to_do
    - copy_paste_command
    - phase_seen
    - expansion_note
```

**Ordering rule** (failure_classifier.py line 99 comment — critical):
```
# ORDER MATTERS — more specific patterns must come before generic ones.
# e.g., 'slopsquat-blocked' (entry 19) before 'npm-404' (entry 17)
#       'pnpm-not-found' before 'npm-not-found'
```

---

### `references/friendly-errors/README.md` (documentation)

**Analog:** `references/roles/qa.md`

**Section structure** (qa.md uses H2 sections with purpose, format, rules, examples, counts):
qa.md provides the exact section-heading style to copy. The 5 required sections for this README map to qa.md's structure:

```markdown
# OSBuilder Friendly-Error Dictionary

## Location and Format
[file path, format choice (YAML), format-version field]

## Field Schema
[all 8 fields with type + description + example]

## How to Test a New Entry
[add to dictionary.yaml, run `pytest scripts/tests/test_friendly_error.py -x`]

## Inclusion Criteria
[seen in dogfood build N times OR blocks user progress]

## Format Version
[format_version field; friendly_error.py rejects anything other than "1.0"]
```

---

### `references/roles/pm.md` through `references/roles/tech-writer.md` (role-brief, event-driven)

**Analog:** `references/roles/qa.md` (entire file — 92 lines)

**Structure pattern** (qa.md lines 1–92):
qa.md has: `# OSBuilder QA Role — …`, `## Purpose`, `## VERIFICATION.md Format`, `## Falsifiability Rule`, `## Forbidden Criterion Patterns`, `## Valid Criterion Examples`, `## Count Rule`, `## Escalation Note`.

For Phase 5 role briefs, the 4 required sections replace qa.md's sections:

```markdown
# OSBuilder {Role} Role — Narration Brief

## Banner Templates

start: [{ROLE}] {action}...
ok: [{ROLE}] {action} ✓
fail: [{ROLE}] {action} ✗ ({detail})

## Tutor Template (default)

> In plain English: {explanation}

## Per-Step Copy

{step-name}:
  banner: {short action phrase}
  tutor: {plain-English one sentence, no jargon}

## Failure Copy

{step-name}: {Role} hit a snag: {plain-English description}. Details below.
```

**Jargon constraint** (SPEC lines 91–92): 6 tokens forbidden in default-mode sections — `framework`, `endpoint`, `responsive`, `ORM`, `dependency injection`, `transpiler`. Advanced-copy sections (if any) may use them.

**File size target:** 50–200 lines per SPEC. Realistic: 80–120 lines. qa.md at 92 lines is the exact size target.

**Per-role step mapping** (RESEARCH.md lines 738–748):
| Role | Steps owned | Key per-step actions |
|---|---|---|
| PM | step 0 + intake calls | intake-paragraph, intake-structured, spec-lock |
| Architect | step 1 + stack research | plan-phase, stack-research, plan-lock |
| Frontend | part of step 3 (UI phases) | execute-ui, build-component, build-page |
| Backend | part of step 3 (API/DB phases) | execute-api, build-route, build-schema |
| DevOps | step 2 + scaffold | registry-gate, scaffold, install-deps |
| QA | steps 4 + 8 | run-tests, verify-criteria, write-verification |
| Reviewer | steps 5 + 6 | security-scan, code-review, lock-review |
| Tech Writer | new step 9 | generate-readme, check-humanizer, rewrite-readme |

---

### `scripts/tests/test_narration.py` (test-suite, request-response)

**Analog:** `scripts/tests/test_gsd_driver.py` (entire file)

**Lazy-import fixture pattern** (test_gsd_driver.py lines 13–19 — copy verbatim):
```python
@pytest.fixture
def nrt():
    """Lazy import of scripts/narration.py — skips when not yet created."""
    try:
        return importlib.import_module("narration")
    except ImportError:
        pytest.skip("narration module not yet created (Wave 1 target)")
```

**State-writer-based setup pattern** (test_gsd_driver.py lines 23–28 — `writer` fixture + `tmp_project_root`):
```python
def test_eight_role_briefs_exist(nrt):
    """UX-04: find references/roles -name '*.md' | wc -l must return 8."""
    brief_dir = Path(nrt.REPO_ROOT) / "references" / "roles"
    briefs = list(brief_dir.glob("*.md"))
    assert len(briefs) == 8, f"Expected 8 role briefs, found {len(briefs)}: {[b.name for b in briefs]}"
```

**capsys raw-output assertion pattern** (test_gsd_driver.py lines 23–28):
```python
def test_capture_subprocess_routes_raw_to_log(nrt, tmp_path, capsys):
    """ROLE-09: raw subprocess output goes to build.log; user sees only role banner."""
    log_path = tmp_path / "build.log"
    rc, out, err = nrt.capture_subprocess(
        ["echo", "hello world"], role="devops", action="probe", log_path=log_path,
    )
    captured = capsys.readouterr()
    assert "[DEVOPS]" in captured.out.upper()
    assert "hello world" not in captured.out      # raw not on stdout
    assert "hello world" in log_path.read_text()  # raw IS in build.log
```

**Regex-scan pattern** (test_gsd_driver.py `test_criteria_not_tests_pass` at lines 143–154 — read file, grep content):
```python
def test_no_python_tracebacks_in_user_output(nrt, tmp_path, capsys):
    """ROLE-09: zero Traceback lines in default-mode stdout."""
    log_path = tmp_path / "build.log"
    nrt.capture_subprocess(
        ["python3", "-c", "raise RuntimeError('boom')"],
        role="qa", action="run-tests", log_path=log_path,
    )
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out
    assert 'File "' not in captured.out
```

**Minimum 15 stubs required** (RESEARCH.md line 1149) — test names drawn from RESEARCH.md lines 1107–1134:
- `test_eight_role_briefs_exist`
- `test_brief_has_required_sections`
- `test_emit_at_every_dispatch` (integration — monkeypatch gsd_driver)
- `test_eight_banners_in_e2e`
- `test_no_node_stack_frames`
- `test_no_python_tracebacks_in_user_output`
- `test_raw_stderr_to_log`
- `test_capture_subprocess_routes_raw_to_log`
- `test_emit_start_ok_fail_statuses`
- `test_emit_graceful_without_brief`
- `test_role_brief_loaded_at_import`
- `test_forbidden_jargon_not_in_banners`
- `test_tutor_line_has_gt_prefix`
- `test_quiet_mode_no_tutor_lines`
- `test_build_log_created_on_first_capture`

---

### `scripts/tests/test_friendly_error.py` (test-suite, request-response)

**Analog:** `scripts/tests/test_failure_classifier.py` (entire file — 93 lines)

**Lazy-import fixture** (test_failure_classifier.py lines 13–18 — copy verbatim, rename `fc` → `fe`):
```python
@pytest.fixture
def fe():
    """Lazy import of scripts/friendly_error.py — skips when not yet created."""
    try:
        return importlib.import_module("friendly_error")
    except ImportError:
        pytest.skip("friendly_error module not yet created (Wave 1 target)")
```

**Pure-function test pattern** (test_failure_classifier.py lines 22–43 — no fixtures, just `fc` + string arg):
```python
def test_translate_returns_friendly_message(fe):
    """UX-02: translate() returns a FriendlyMessage with all 5 fields."""
    msg = fe.translate("EADDRINUSE: address already in use")
    assert hasattr(msg, "title")
    assert hasattr(msg, "what_broke")
    assert hasattr(msg, "what_to_do")
    assert hasattr(msg, "severity")
    # copy_paste may be None for some entries

def test_dictionary_entry_match_wins_over_generic(fe):
    """UX-02: dictionary hit returns entry copy, not generic fallback."""
    msg = fe.translate("pnpm: command not found")
    assert msg.title != "Something went wrong"  # not the generic fallback
    assert msg.copy_paste is not None            # entry has a copy_paste_command
```

**Count/schema assertion pattern** (same style as test_failure_classifier.py `test_structured_handoff_produced`):
```python
def test_dictionary_has_30_entries(fe):
    """UX-05: dictionary file contains >= 30 entries."""
    entries = fe.load_dictionary()
    assert len(entries) >= 30

def test_dictionary_schema_all_8_fields(fe):
    """UX-05: each entry has all 8 documented fields."""
    required = {"id", "match_pattern", "category", "title",
                "what_broke", "what_to_do", "copy_paste_command", "phase_seen"}
    for entry in fe.load_dictionary():
        missing = required - set(entry.keys())
        assert not missing, f"Entry {entry.get('id')} missing fields: {missing}"
```

**Minimum 10 stubs required** (RESEARCH.md line 1150).

---

### `scripts/tests/test_tutor_mode.py` (test-suite, request-response)

**Analog:** `scripts/tests/test_gsd_driver.py` + `scripts/tests/conftest.py`

**Writer + tmp_project_root fixtures** (conftest.py lines 17–42 — both fixtures already in shared conftest; do not duplicate):
```python
# test_tutor_mode.py — uses existing conftest fixtures: writer, tmp_project_root
# Plus the nrt fixture from test_narration.py if importing from the same session
```

**State-write-then-assert pattern** (test_gsd_driver.py lines 101–109):
```python
def test_quiet_flag_suppresses_tutor_lines(nrt, tmp_project_root, writer, capsys):
    """UX-01: --quiet mode → zero '> ' prefix lines in stdout."""
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "tutor_enabled", "--value", "false",
           project_root=tmp_project_root)
    nrt._refresh_state(tmp_project_root)
    nrt.emit("pm", "Reading your description", "ok")
    captured = capsys.readouterr()
    assert not any(line.startswith("> ") for line in captured.out.splitlines())
    # Role banner must still appear
    assert "[PM]" in captured.out.upper()
```

**Jargon-grep pattern** (test_gsd_driver.py `test_criteria_not_tests_pass` lines 143–154):
```python
FORBIDDEN_JARGON = ["framework", "endpoint", "responsive", "ORM",
                    "dependency injection", "transpiler"]

def test_no_forbidden_jargon_in_default_tutor_lines(nrt, tmp_project_root, writer, capsys):
    """UX-01: zero forbidden jargon tokens in default-mode tutor output."""
    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    writer("write", "--field", "tutor_enabled", "--value", "true",
           project_root=tmp_project_root)
    nrt._refresh_state(tmp_project_root)
    # Emit all 8 role banners in "ok" status
    for role in ("pm", "architect", "frontend", "backend", "devops", "qa", "reviewer", "tech-writer"):
        nrt.emit(role, "working", "ok")
    captured = capsys.readouterr()
    for token in FORBIDDEN_JARGON:
        assert token.lower() not in captured.out.lower(), \
            f"Forbidden jargon '{token}' found in default-mode output"
```

**Minimum 8 stubs required** (RESEARCH.md line 1151).

---

### `scripts/tests/test_mode_gating.py` (test-suite, request-response)

**Analog:** `scripts/tests/test_intake.py` + `scripts/tests/conftest.py`

**Writer + intake lazy-import** (test_gsd_driver.py fixture pattern + conftest `writer` fixture):
```python
@pytest.fixture
def intake():
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet available")

@pytest.fixture
def researcher():
    try:
        return importlib.import_module("stack_researcher")
    except ImportError:
        pytest.skip("stack_researcher module not yet available")
```

**Mode-write-then-assert pattern** (RESEARCH.md Example 3, lines 1019–1045):
```python
def test_beginner_mode_no_jargon_in_prompts(intake, tmp_project_root, writer, capsys):
    """UX-03: default-mode TODO web app produces zero jargon prompts."""
    writer("init", "--goal", "TODO web app", project_root=tmp_project_root)
    writer("write", "--field", "mode", "--value", "beginner",
           project_root=tmp_project_root)
    intake.parse_paragraph("I want a TODO web app", project_root=tmp_project_root)
    captured = capsys.readouterr()
    forbidden = ["Next.js", "SvelteKit", "Postgres", "SQLite", "Vercel",
                 "Fly.io", "Railway", "Drizzle", "Tailwind"]
    for token in forbidden:
        assert token not in captured.out, f"Beginner mode leaked '{token}'"
```

**Minimum 6 stubs required** (RESEARCH.md line 1152).

---

### `scripts/tests/test_tech_writer.py` (test-suite, request-response)

**Analog:** `scripts/tests/test_gsd_driver.py` (dispatch-assertion pattern)

**PHASE_STEP_COMMANDS assertion pattern** (test_gsd_driver.py lines 32–75 — step→command mapping tests):
```python
@pytest.fixture
def gd():
    try:
        return importlib.import_module("gsd_driver")
    except ImportError:
        pytest.skip("gsd_driver module not yet available")

def test_phase_step_commands_includes_tech_writer(gd):
    """ROLE-07: PHASE_STEP_COMMANDS must contain a tech-writer step."""
    commands = gd.PHASE_STEP_COMMANDS
    tech_writer_steps = [
        k for k, v in commands.items()
        if "gsd-docs-update" in str(v) or "tech-writer" in str(v)
    ]
    assert tech_writer_steps, "No tech-writer step found in PHASE_STEP_COMMANDS"
```

**State-write + monkeypatch pattern** (test_gsd_driver.py `test_step_2_calls_registry_verify` lines 206–249):
```python
def test_tech_writer_step_emits_gsd_docs_update(gd, tmp_project_root, writer, monkeypatch, capsys):
    """ROLE-07: tech-writer phase step emits /gsd-docs-update."""
    import subprocess as _real_subprocess
    _real_run = _real_subprocess.run

    writer("init", "--goal", "TODO app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "9",  # tech-writer step
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-docs-update" in captured.out
```

**humanizer_score state-persistence pattern** (test_gsd_driver.py `test_resume_preserves_retry_count` lines 119–128):
```python
def test_humanizer_score_written_to_state(gd, tmp_project_root, writer):
    """ROLE-07: after tech-writer step, humanizer_score field exists in state.md."""
    # ... set up phase_step at tech-writer value ...
    result = writer("read", "--field", "humanizer_score",
                    project_root=tmp_project_root, check=False, capture=True)
    assert result.stdout.strip() != "", "humanizer_score not written to state.md"
```

**Minimum 5 stubs required** (RESEARCH.md line 1153).

---

### `scripts/gsd_driver.py` — PHASE_STEP_COMMANDS insertion (wiring-edit)

**Analog:** itself

**Exact insertion point** (lines 32–43 — PHASE_STEP_COMMANDS dict):
```python
# CURRENT (lines 32–43):
PHASE_STEP_COMMANDS: dict[int, str] = {
    0: "/gsd-spec-phase",
    1: "/gsd-plan-phase",
    # 2: registry_verify gate — handled in-line
    3: "/gsd-execute-phase",
    4: "/code-tester",
    5: "/predator",
    6: "/gsd-code-review",
    # 7: write VERIFICATION.md — handled in-line
    8: "/gsd-verify-work",
    # 9: advance current_phase, reset phase_step to 0 — handled in-line
}

# PHASE 5 TARGET: add step 9 for tech-writer; shift phase-advance to step 10.
# Steps 2, 7, and 10 remain in-line (no slash command).
PHASE_STEP_COMMANDS: dict[int, str] = {
    0: "/gsd-spec-phase",
    1: "/gsd-plan-phase",
    # 2: registry_verify gate — handled in-line
    3: "/gsd-execute-phase",
    4: "/code-tester",
    5: "/predator",
    6: "/gsd-code-review",
    # 7: write VERIFICATION.md — handled in-line
    8: "/gsd-verify-work",
    9: "/gsd-docs-update",  # Tech Writer: README generation (step A)
    # humanizer invocation and score parsing handled in-line at step 9.5 (new block)
    # 10: advance current_phase, reset phase_step to 0 — handled in-line
}
```

**narration.emit insertion point pattern** (gsd_driver.py `emit_next_command` lines 254–309):

Insert `narration.emit(role, action, "start")` before each `print(cmd)` at lines 298–301, and `narration.emit(role, action, "ok")` after each `_bump_field` call. For fail paths, insert `narration.emit(role, action, "fail", detail=friendly_error.translate(...).title)` before each `return 1`.

Role assignment heuristic for step 3 (RESEARCH.md lines 749):
```python
# After reading state at line 265, determine role for this step:
def _role_for_step(phase_step: int, state: dict) -> str:
    if phase_step in (0,): return "pm"
    if phase_step in (1,): return "architect"
    if phase_step in (2, 3): return "devops"
    if phase_step in (4,): return "qa"
    if phase_step in (5, 6): return "reviewer"
    if phase_step in (7, 8): return "qa"
    if phase_step in (9,): return "tech-writer"
    # For step 3, inspect phase spec title to pick frontend vs backend:
    title = state.get("next_action", "").lower()
    if any(w in title for w in ("ui", "frontend", "homepage", "screen", "page")):
        return "frontend"
    if any(w in title for w in ("api", "backend", "database", "model")):
        return "backend"
    return "devops"
```

**Phase-advance in-line block update** (lines 292–296 — shift `phase_step == 9` condition to `phase_step == 10`):
```python
# CURRENT line 292:
if phase_step == 9:
    _write_field(project_root, "phase_step", "0")
    _write_field(project_root, "current_phase", str(current_phase + 1))
    return 0

# PHASE 5 TARGET (shift to 10):
if phase_step == 10:
    _write_field(project_root, "phase_step", "0")
    _write_field(project_root, "current_phase", str(current_phase + 1))
    return 0
```

**WARNING — Pitfall 7** (RESEARCH.md lines 835–838): Phase 4 tests pin step values. The test at line 157–166 (`test_verify_work_emitted`) asserts `phase_step=8` → `/gsd-verify-work`. This still holds. The test at line 194–203 (`test_state_updates_after_emission`) checks step increments to 1. Phase 5 Wave 0 must update `test_tech_writer.py` stubs before the Phase 4 suite can run green after the `phase_step == 9 → 10` rename.

---

### `scripts/state_writer.py` — ALLOWED_FIELDS extension (state-extension)

**Analog:** itself

**Exact insertion point** (lines 36–44 — ALLOWED_FIELDS set literal):
```python
# CURRENT (lines 36–44):
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    "project_path",
    "stack_choices",
    "stack_overrides",
    # Phase 4 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3)
    "gsd_phase_count",
    "failure_class",
    "escalation_log",
}

# PHASE 5 TARGET: append 4 new fields at the end of the set literal, inside the
# closing brace, after the existing "escalation_log" line:
    # Phase 5 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3/4)
    "mode",             # "beginner" | "advanced"
    "tutor_enabled",    # "true" | "false" — set by --quiet flag
    "humanizer_score",  # int | "skipped" — count of critical AI-pattern issues
    "build_log_path",   # absolute path to .planning/osbuilder/build.log
```

**Pattern contract** (state_writer.py lines 36–44 comments + `_check_field_allowed` at lines 49–55):

All 4 new fields go into `ALLOWED_FIELDS` only — NOT `REQUIRED_FIELDS` and NOT `COUNTER_FIELDS`. This exactly mirrors how Phase 3 added `project_path`/`stack_choices`/`stack_overrides` and Phase 4 added `gsd_phase_count`/`failure_class`/`escalation_log`. The `_check_field_allowed` allowlist enforcement at line 50–55 automatically covers the new fields once they are in `ALLOWED_FIELDS`.

---

### `scripts/preflight_check.py` — error-path wiring (wiring-edit)

**Analog:** itself (error-path sites)

**Exact insertion points** — every `sys.stderr.write(...)` that surfaces a raw error to the user:

1. **Line 474–478** (`except (FileNotFoundError, OSError)` in `apply()`):
```python
# CURRENT line 476:
sys.stderr.write(f"OSBuilder: {action.tool} install failed: {e}\n")

# PHASE 5 TARGET — translate before write:
from scripts import friendly_error as _fe
_msg = _fe.translate(str(e), ctx={"tool": action.tool})
sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
if _msg.copy_paste:
    sys.stderr.write(f"\n  {_msg.copy_paste}\n")
```

2. **Line 487–490** (install exit non-zero in `apply()`):
```python
# CURRENT line 487–490:
sys.stderr.write(
    f"OSBuilder: {action.tool} install exited {result.returncode}; rolling back...\n"
)

# PHASE 5 TARGET:
raw = (result.stderr or "").strip() or f"exit code {result.returncode}"
_msg = _fe.translate(raw, ctx={"tool": action.tool})
sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
```

**Import pattern** (preflight_check.py lines 23–33 — stdlib-only imports; add friendly_error import at module level following the existing pattern):
```python
# Add after existing imports, guarded for graceful degrade if module not yet built:
try:
    import sys as _sys; import importlib as _importlib
    _friendly_error = _importlib.import_module("friendly_error")
except ImportError:
    _friendly_error = None  # graceful degrade — raw error output until Phase 5 ships
```

---

### `scripts/scaffold_dispatch.py` — error-path wiring (wiring-edit)

**Analog:** itself (error paths at lines 140–145)

**Exact insertion points:**

1. **Lines 140–142** (`except (FileNotFoundError, OSError)` in `scaffold_web()`):
```python
# CURRENT line 141:
sys.stderr.write(f"OSBuilder: scaffold failed — pnpm not found: {e}\n")

# PHASE 5 TARGET:
_msg = _fe.translate(str(e), ctx={"tool": "pnpm"})
sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
```

2. **Lines 143–145** (`except subprocess.CalledProcessError` in `scaffold_web()`):
```python
# CURRENT line 144:
sys.stderr.write(f"OSBuilder: create-next-app exited {e.returncode}\n{e.stderr}\n")

# PHASE 5 TARGET:
_msg = _fe.translate(e.stderr or f"exit {e.returncode}", ctx={})
sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
```

3. **Lines 154–158** (pnpm add drizzle-orm warning — currently `sys.stderr.write`):
```python
# CURRENT line 155–158:
sys.stderr.write(
    f"OSBuilder: warning — pnpm add drizzle-orm postgres failed "
    f"(exit {result.returncode}). Run manually in {project_dir}\n"
)

# PHASE 5 TARGET:
_msg = _fe.translate(f"pnpm add drizzle-orm postgres failed exit {result.returncode}",
                     ctx={"project_dir": str(project_dir)})
sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
```

---

### `scripts/stack_researcher.py` — mode-gate wiring (wiring-edit)

**Analog:** itself

**Exact insertion point** (lines 107–111 — `research_stack` body after brainiac call):

The mode-gate inserts at the top of `research_stack()`, before line 107 (`brainiac_result = _call_brainiac(app_type)`):

```python
# PHASE 5 insertion — read mode from state.md:
def research_stack(
    app_type: str,
    project_root: Path | None = None,
    advanced_overrides: dict | None = None,
) -> dict:
    resolved_root = _resolve_project_root(None if project_root is None else str(project_root))

    # NEW: read mode field — beginner skips brainiac; uses stack-menu defaults only
    mode = "beginner"
    state_md = resolved_root / ".planning" / "osbuilder" / "state.md"
    if state_md.exists():
        try:
            import subprocess as _sp
            r = _sp.run([sys.executable, str(STATE_WRITER), "read", "--field", "mode",
                         "--project-root", str(resolved_root)],
                        capture_output=True, text=True, shell=False, check=False)
            mode = r.stdout.strip() or "beginner"
        except Exception:
            pass

    if mode == "beginner":
        # Skip brainiac entirely; use stack-menu defaults (RES-03 path)
        stack_choices = _read_stack_menu(REFERENCES_ROOT)
    else:
        # EXISTING lines 107–125 (advanced mode — call brainiac, merge fallback)
        brainiac_result = _call_brainiac(app_type)
        ...
```

**Error-path wiring** (stack_researcher.py lines 92–94 — `except` in `_call_brainiac`; currently returns `{}`):
```python
# CURRENT line 92–95:
except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
    return {}

# PHASE 5 TARGET: translate before returning empty (non-fatal, no stderr write needed here;
# the empty dict triggers the stack-menu fallback which is the intended behavior).
# stack_researcher's error surface is already graceful-degrade; only add translate() where
# errors are currently written to stderr (none currently). No change needed here.
```

---

### `scripts/intake_handler.py` — mode-gate wiring (wiring-edit)

**Analog:** itself

**Exact insertion points** (parse_paragraph at line 93, parse_structured at line 105):

`intake_handler.py` currently has no mode-gate. Phase 5 adds a mode check that omits stack-hint fields from derived_spec.md in beginner mode:

```python
# PHASE 5: add mode_from_state helper (mirrors stack_researcher's mode-read pattern):
def _mode_from_state(project_root: Path) -> str:
    """Read mode field from state.md; default 'beginner' on any failure."""
    state_md = project_root / ".planning" / "osbuilder" / "state.md"
    if not state_md.exists():
        return "beginner"
    try:
        import subprocess as _sp
        r = _sp.run([sys.executable, str(REPO_ROOT / "scripts" / "state_writer.py"),
                     "read", "--field", "mode", "--project-root", str(project_root)],
                    capture_output=True, text=True, shell=False, check=False)
        return r.stdout.strip() or "beginner"
    except Exception:
        return "beginner"
```

**Question-bank gate** (question-bank.md line 37 — `Q: External access` → "API" jargon → advanced-only):

In `parse_paragraph` at line 101, after calling `_render_derived_spec`, add a mode-aware post-processing step that strips stack_hints from beginner-mode specs:
```python
# CURRENT line 101:
atomic_write(dest, _render_derived_spec(goal=text.strip(), app_type="web"))

# PHASE 5 TARGET: pass mode to _render_derived_spec (new kwarg `mode`):
_mode = _mode_from_state(root)
atomic_write(dest, _render_derived_spec(
    goal=text.strip(), app_type="web",
    mode=_mode,  # new kwarg — beginner mode omits stack_hints from output
))
```

**_render_derived_spec mode kwarg** (line 69 function signature):
```python
def _render_derived_spec(
    goal: str,
    app_type: str = "web",
    features: list | None = None,
    users: list | None = None,
    stack_hints: list | None = None,
    mode: str = "beginner",  # NEW: beginner omits stack_hints line from output
) -> str:
    ...
    # Only include stack_hints line if mode == "advanced":
    if stack_hints and mode == "advanced":
        lines.append(f"**Stack hints:** {', '.join(stack_hints)}")
```

---

## Shared Patterns

### Lazy-import fixture (applies to all 5 new test files)

**Source:** `scripts/tests/test_failure_classifier.py` lines 12–18; `scripts/tests/test_gsd_driver.py` lines 13–19

```python
@pytest.fixture
def {module_short_name}():
    """Lazy import — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("{module_name}")
    except ImportError:
        pytest.skip("{module_name} module not yet created (Wave 1 target)")
```

### `writer` + `tmp_project_root` fixtures (applies to all 5 new test files)

**Source:** `scripts/tests/conftest.py` lines 17–42

These fixtures already exist in the shared conftest. New test files must NOT redefine them. Import via pytest's automatic conftest discovery. The `writer` fixture returns `run_state_writer` which calls state_writer.py as a subprocess with `--project-root`.

### REPO_ROOT path constant (applies to narration.py, friendly_error.py)

**Source:** `scripts/gsd_driver.py` line 25; `scripts/scaffold_dispatch.py` line 16; `scripts/stack_researcher.py` line 21

```python
REPO_ROOT = Path(__file__).resolve().parent.parent
```

All scripts use this identical one-liner. Copy verbatim.

### `_resolve_project_root` function (applies to narration.py)

**Source:** `scripts/gsd_driver.py` lines 50–60; identical copies in scaffold_dispatch.py lines 66–75 and state_writer.py lines 66–76

```python
def _resolve_project_root(arg: str | None) -> Path:
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()
```

### Atomic write (applies to narration.py for build.log init)

**Source:** `scripts/state_writer.py` lines 115–127; identical copies in scaffold_dispatch.py lines 78–89 and intake_handler.py lines 54–65

narration.py does not need `atomic_write` for the build.log (append-mode is correct). Use `Path.open("a")` instead — but the pattern for creating parent directories is:
```python
log_path.parent.mkdir(parents=True, exist_ok=True)
```

### Error-path import guard (applies to all 5 modified scripts)

**Source:** derived from preflight_check.py's graceful-degrade pattern for missing tools

```python
try:
    from scripts import friendly_error as _fe
except ImportError:
    _fe = None  # graceful degrade before Phase 5 ships

# At error site:
if _fe is not None:
    _msg = _fe.translate(raw, ctx)
    sys.stderr.write(f"## {_msg.title}\n{_msg.what_broke}\n\n{_msg.what_to_do}\n")
else:
    sys.stderr.write(f"OSBuilder: error — {raw}\n")  # original behavior
```

### State-field access via subprocess (applies to narration.py, intake_handler.py mode gate)

**Source:** `scripts/gsd_driver.py` `_read_state` lines 82–93 and `_write_field` lines 104–111

```python
# Read a single field:
result = subprocess.run(
    [sys.executable, str(STATE_WRITER), "read", "--field", field_name,
     "--project-root", str(project_root)],
    capture_output=True, text=True, shell=False, check=False,
)
value = result.stdout.strip() or default

# Write a single field:
subprocess.run(
    [sys.executable, str(STATE_WRITER), "write",
     "--field", field_name, "--value", value,
     "--project-root", str(project_root)],
    shell=False, check=True,
)
```

### `from __future__ import annotations` + `#!/usr/bin/env python3` (all new scripts)

**Source:** Every existing script (gsd_driver.py line 1–2, state_writer.py line 1–2, failure_classifier.py line 1–2)

Always open with shebang + future import. Pure stdlib comment on line 3. No exceptions.

---

## No Analog Found

All Phase 5 files have analogs in the codebase. The following files draw primarily from RESEARCH.md patterns rather than direct codebase analogs, but the analog file is still the closest match:

| File | Role | Data Flow | Note |
|---|---|---|---|
| `references/friendly-errors/dictionary.yaml` | dictionary-data | transform | No YAML file exists in the codebase. The pattern dict structure maps from failure_classifier.py's list-of-patterns. Hand-rolled YAML subset parser must be authored from scratch following RESEARCH.md guidance. |
| `references/roles/pm.md` through `tech-writer.md` | role-brief | event-driven | qa.md provides structure; the 4-section format for narration briefs is new (qa.md has a different section set). Copy qa.md's heading style and file length; replace section content per RESEARCH.md Pattern 3. |

---

## Metadata

**Analog search scope:** `scripts/`, `scripts/tests/`, `references/roles/`
**Files read:** 14 source files
**Pattern extraction date:** 2026-04-30

---

## PATTERN MAPPING COMPLETE

**Phase:** 5 - Common-person UX polish
**Files classified:** 22
**Analogs found:** 22 / 22

### Coverage
- Files with exact analog: 9 (test files + failure_classifier → friendly_error + gsd_driver self-edit + state_writer self-edit)
- Files with role-match analog: 11 (narration.py, role briefs, dictionary, README, wiring edits)
- Files with no analog: 2 (dictionary.yaml format is new; role brief sections are new — but structure analogs exist)

### Key Patterns Identified
1. All new scripts open with `#!/usr/bin/env python3` + `from __future__ import annotations` + `Pure stdlib — no third-party deps.` docstring comment — copy verbatim from every existing script.
2. `REPO_ROOT = Path(__file__).resolve().parent.parent` is used identically in gsd_driver.py, scaffold_dispatch.py, and stack_researcher.py — copy verbatim into narration.py and friendly_error.py.
3. `failure_classifier.py`'s ordered-list + `_matches()` + first-match pattern is the direct template for `friendly_error.py`'s translate() function; the "ORDER MATTERS" comment at line 99 of failure_classifier.py must carry forward into the dictionary YAML.
4. All 5 test files use the lazy-import `pytest.fixture` + `pytest.skip("...not yet created (Wave 1 target)")` pattern from test_failure_classifier.py lines 13–18 — copy verbatim, rename fixture variable.
5. All modified scripts' error paths follow the same graceful-degrade import guard: `try: import friendly_error; except ImportError: _fe = None` — ensures Phase 3/4 tests pass before Phase 5 ships.
6. `state_writer.py` ALLOWED_FIELDS extension is a 4-line append inside the existing set literal (lines 36–44) — not a refactor, not a new function; matches Phase 3 and Phase 4 extension commits exactly.
7. `gsd_driver.py` PHASE_STEP_COMMANDS needs step 9 inserted for tech-writer, with the phase-advance condition shifted from `phase_step == 9` to `phase_step == 10` — Phase 4 tests that assert step 9 behavior must be updated in Wave 0 before any Phase 5 code is written.

### File Created
`/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/.planning/phases/05-common-person-ux-polish/05-PATTERNS.md`

### Ready for Planning
Pattern mapping complete. Planner can now reference analog patterns in PLAN.md files.
