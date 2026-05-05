# Phase 4: GSD Handoff + Verify Loop + Failure Classifier — Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 7 new/modified files
**Analogs found:** 7 / 7

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/gsd_driver.py` | utility/script | event-driven (state machine: read state → emit text → write state) | `scripts/scaffold_dispatch.py` | role-match (same stdlib/argparse/state_writer delegation pattern) |
| `scripts/failure_classifier.py` | utility/script | transform (error string → classification dict) | `scripts/preflight_check.py` (`plan()` function) | role-match (pure-function classification with no side effects) |
| `scripts/registry_verify.py` | utility/script | request-response (HTTP GET → bool exit code) | `scripts/preflight_check.py` (`detect()` / `_probe_version()`) | role-match (external tool probe → structured result) |
| `scripts/state_writer.py` (modify) | utility/script | CRUD | `scripts/state_writer.py` itself | self (extend ALLOWED_FIELDS same as Phase 3) |
| `scripts/tests/test_gsd_driver.py` | test | — | `scripts/tests/test_scaffold_dispatch.py` | exact (same lazy-import fixture, fake_shell, writer fixture chain) |
| `scripts/tests/test_failure_classifier.py` | test | — | `scripts/tests/test_preflight.py` | exact (lazy import + monkeypatch on stdlib calls) |
| `scripts/tests/test_registry_verify.py` | test | — | `scripts/tests/test_preflight.py` | exact (lazy import + monkeypatch on urllib) |
| `references/roles/qa.md` | config/reference doc | — | `references/playbooks/web.md` | role-match (flat one-level reference doc, not pulled into SKILL.md) |

---

## Pattern Assignments

### `scripts/gsd_driver.py` (utility/script, event-driven state machine)

**Analog:** `scripts/scaffold_dispatch.py`

**Imports pattern** (scaffold_dispatch.py lines 1–15):
```python
#!/usr/bin/env python3
"""gsd_driver.py — OSBuilder GSD phase loop driver.

Reads state.md to determine which GSD slash command to emit next,
prints it to stdout, then advances state.md. One invocation = one
command emission. Re-entry after /clear resumes from persisted state.

Pure stdlib — no third-party deps.

Subcommands:
  emit-next   Emit the next GSD slash command for the current phase/step.
  status      Print current phase, step, and role (read-only).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
```

Drop `shutil`, `subprocess` for the slash-command emission path; keep `subprocess` only for calling `state_writer.py` as a helper and `registry_verify.py` as a gate. Add `re` for ROADMAP.md phase-count parsing.

**REPO_ROOT + STATE_WRITER constant pattern** (scaffold_dispatch.py lines 16–17):
```python
REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"
```
Copy verbatim. `gsd_driver.py` uses the identical two-line pattern to locate `state_writer.py`.

**`_resolve_project_root` pattern** (scaffold_dispatch.py lines 66–75):
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
Copy verbatim — same auto-detect + path-traversal guard pattern used by all OSBuilder scripts.

**state_writer delegation pattern** (scaffold_dispatch.py lines 177–188):
```python
state_md = project_root / ".planning" / "osbuilder" / "state.md"
if state_md.exists():
    try:
        subprocess.run(
            [sys.executable, str(STATE_WRITER), "write",
             "--field", "project_path", "--value", str(project_dir),
             "--project-root", str(project_root)],
            shell=False, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pass  # state.md write failure is non-fatal
```
Apply this pattern for every state.md write in `gsd_driver.py`. Replace `"project_path"` / `str(project_dir)` with the target field/value pair. Use `bump` subcommand (not `write`) for `phase_step` and `retry_count` increments:
```python
subprocess.run(
    [sys.executable, str(STATE_WRITER), "bump",
     "--field", "phase_step",
     "--project-root", str(project_root)],
    shell=False, check=True,
)
```

**read_state pattern** (state_writer.py lines 132–137):
```python
def read_state(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"OSBuilder: no state.md at {path}. Run `state_writer.py init` first."
        )
    return parse_state_md(path.read_text(encoding="utf-8"))
```
`gsd_driver.py` calls `state_writer.py read --format json` via subprocess and `json.loads()` the output, OR imports `state_writer.read_state` and `state_writer.parse_state_md` directly. ALWAYS call this on entry — never initialize `retry_count` from a Python default.

**Core emission pattern** (architectural — not in existing scripts):
```python
# gsd_driver.py — core slash command emission
PHASE_STEP_COMMANDS = {
    0: "/gsd-spec-phase",
    1: "/gsd-plan-phase",
    # step 2 = registry_verify gate (no slash command; handled internally)
    3: "/gsd-execute-phase",
    4: "/code-tester",
    5: "/predator",
    6: "/gsd-code-review",
    # step 7 = write VERIFICATION.md (no slash command; handled internally)
    8: "/gsd-verify-work",
    # step 9 = advance phase + reset step to 0
}

def emit_next_command(project_root: Path) -> int:
    """Read state, emit the next slash command to stdout, advance state."""
    state_path = project_root / ".planning" / "osbuilder" / "state.md"
    # ALWAYS read state first — never initialize from Python defaults (Pitfall 2)
    state = read_state_via_subprocess(state_path, project_root)
    phase = int(state.get("current_phase", "0") or "0")
    step = int(state.get("phase_step", "0") or "0")
    retry_count = int(state.get("retry_count", "0") or "0")
    # ... dispatch to handler for (phase, step)
    command = PHASE_STEP_COMMANDS.get(step)
    if command:
        print(command)   # emitted to stdout — Claude Code runtime executes it
    # Bump phase_step after emission
    _bump_state_field("phase_step", project_root)
    return 0
```

**argparse dispatch pattern** (scaffold_dispatch.py lines 192–218):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="gsd_driver",
        description="OSBuilder GSD phase loop driver.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_emit = sub.add_parser("emit-next", help="emit next GSD slash command")
    p_emit.add_argument("--project-root", default=None, dest="project_root")
    p_emit.set_defaults(func=_cmd_emit_next)

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
```
Copy the `try/except SystemExit: raise` guard and the `__name__ == "__main__"` pattern verbatim from scaffold_dispatch.py lines 207–218.

**Error handling pattern** (scaffold_dispatch.py lines 135–145):
```python
try:
    subprocess.run(
        cmd, cwd=str(project_root), check=True,
        capture_output=True, text=True, shell=False,
    )
except (FileNotFoundError, OSError) as e:
    sys.stderr.write(f"OSBuilder: scaffold failed — pnpm not found: {e}\n")
    raise SystemExit(1)
except subprocess.CalledProcessError as e:
    sys.stderr.write(f"OSBuilder: create-next-app exited {e.returncode}\n{e.stderr}\n")
    raise SystemExit(1)
```
Use this exception tuple `(FileNotFoundError, OSError)` + `subprocess.CalledProcessError` pattern for all subprocess calls in `gsd_driver.py`. On error, write `last_failure` to state.md then route to `failure_classifier.py`.

---

### `scripts/failure_classifier.py` (utility/script, transform)

**Analog:** `scripts/preflight_check.py` (the `plan()` / `detect()` pure-function pattern)

**Imports pattern** (preflight_check.py lines 23–33 — minimal for classifier):
```python
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
```
Drop `json`, `os`, `platform`, `shutil`, `subprocess`, `dataclasses` — the classifier is a pure function that calls `time.sleep` and does regex matching only. Add `time` for exponential backoff.

**Module docstring pattern** (preflight_check.py lines 1–21 adapted):
```python
"""failure_classifier.py — OSBuilder error class + retry router.

Classifies a raw error string into one of four failure classes and
returns the appropriate retry strategy. Pure function — no side effects
beyond time.sleep() in the transient handler.

Pure stdlib — no third-party deps.

Classes: transient, context-overflow, tool-failure, validation-failure
"""
```

**Classification pattern — priority-ordered regex** (RESEARCH.md Pattern 2):
```python
# Check VALIDATION before TRANSIENT — "test.*failed" must not match transient (Pitfall 3)
VALIDATION_FAILURE_PATTERNS = [
    r"test.*failed",
    r"assertion.*error",
    r"verification.*failed",
    r"criterion.*not met",
    r"code-tester.*fail",
]
CONTEXT_OVERFLOW_PATTERNS = [
    r"context.length.exceeded",
    r"max.tokens",
    r"too many tokens",
    r"context window",
]
TOOL_FAILURE_PATTERNS = [
    r"skill not found",
    r"SKILL\.md.*error",
    r"command not found",
    r"No such file or directory",
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

def _matches(patterns: list[str], error: str) -> bool:
    return any(re.search(p, error, re.IGNORECASE) for p in patterns)
```
Pattern-list approach mirrors how `preflight_check.py` uses lookup tables (`_MACOS_INSTALL`, `_APT_INSTALL`) for decision routing — declarative table, not nested if-else.

**Pure function signature** (RESEARCH.md Pattern 2):
```python
def classify(error: str, context: dict | None = None) -> dict:
    """Classify an error string into a failure class.

    Returns:
        {
            "class": "transient" | "context-overflow" | "tool-failure" | "validation-failure",
            "strategy": "backoff" | "compress-retry" | "fallback" | "re-plan",
            "retry_ok": bool,   # False when retry_count >= 3
            "backoff_seconds": int | None,  # for transient class only
        }
    """
    retry_count = int((context or {}).get("retry_count", 0))
    retry_ok = retry_count < 3

    # Priority: validation > tool-failure > context-overflow > transient
    if _matches(VALIDATION_FAILURE_PATTERNS, error):
        return {"class": "validation-failure", "strategy": "re-plan",
                "retry_ok": retry_ok, "backoff_seconds": None}
    if _matches(TOOL_FAILURE_PATTERNS, error):
        return {"class": "tool-failure", "strategy": "fallback",
                "retry_ok": retry_ok, "backoff_seconds": None}
    if _matches(CONTEXT_OVERFLOW_PATTERNS, error):
        return {"class": "context-overflow", "strategy": "compress-retry",
                "retry_ok": retry_ok, "backoff_seconds": None}
    if _matches(TRANSIENT_PATTERNS, error):
        return handle_transient(error, retry_count=retry_count)
    # Unknown: escalate immediately
    return {"class": "transient", "strategy": "escalate",
            "retry_ok": False, "backoff_seconds": None}
```

**Exponential backoff pattern** (RESEARCH.md Pattern 3):
```python
def handle_transient(error: str, retry_count: int = 0) -> dict:
    """Exponential backoff for transient failures."""
    BACKOFF_SECONDS = {0: 1, 1: 4, 2: 16}
    if retry_count >= 3:
        return {"class": "transient", "strategy": "escalate",
                "retry_ok": False, "backoff_seconds": None}
    wait = BACKOFF_SECONDS.get(retry_count, 16)
    time.sleep(wait)
    return {"class": "transient", "strategy": "backoff",
            "retry_ok": True, "backoff_seconds": wait}
```

**Error handling pattern** (scaffold_dispatch.py argparse dispatch lines 207–213):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # ... argparse setup ...
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1
```
Copy verbatim for the CLI entry point; the classifier's `classify()` function itself never raises — it always returns a dict.

---

### `scripts/registry_verify.py` (utility/script, request-response)

**Analog:** `scripts/preflight_check.py` (the `_probe_version()` external-probe pattern)

**Imports pattern**:
```python
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path
```
No `subprocess`, `shutil`, `platform` — the registry check is a pure HTTP probe. `urllib.request` is stdlib; no `requests` needed.

**External probe pattern** (preflight_check.py lines 162–171 — _probe_version):
```python
def _probe_version(tool: str) -> str | None:
    """Run `<tool> --version` and return the trimmed stdout, or None on failure."""
    which = shutil.which(tool)
    if which is None:
        return None
    try:
        r = subprocess.run([tool, "--version"], capture_output=True, text=True,
                           shell=False, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    return (r.stdout or r.stderr or "").strip() or None
```
`registry_verify.py` follows the same "try → return result, catch exceptions → return safe default" shape. Replace `subprocess.run` with `urllib.request.urlopen`. The "safe default on exception" maps to fail-open (return `True` on `URLError`).

**Core verification pattern** (RESEARCH.md Pattern 4):
```python
def verify_npm(package_name: str, timeout: int = 10) -> bool:
    """Return True if package exists on npm registry. False = hallucinated or 404."""
    url = f"https://registry.npmjs.org/{package_name}"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404  # 4xx other than 404 = network error, not "not found"
    except (urllib.error.URLError, OSError):
        return True  # Network error ≠ hallucinated package; fail open


def verify_pypi(package_name: str, timeout: int = 10) -> bool:
    """Return True if package exists on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except (urllib.error.URLError, OSError):
        return True  # fail open
```

**CLI interface pattern** (scaffold_dispatch.py argparse pattern + RESEARCH.md Code Examples):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="registry_verify",
        description="OSBuilder package registry existence gate.",
    )
    parser.add_argument("--pkg", required=True)
    parser.add_argument("--ecosystem", choices=("npm", "pip", "cargo"), required=True)
    args = parser.parse_args(argv)

    verifiers = {"npm": verify_npm, "pip": verify_pypi, "cargo": verify_cargo}
    exists = verifiers[args.ecosystem](args.pkg)
    if not exists:
        sys.stderr.write(
            f"OSBuilder: package '{args.pkg}' not found on {args.ecosystem} registry. "
            f"Install blocked (slopsquatting defense).\n"
        )
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
Exit code 0 = exists/verified. Exit code 1 = does not exist (block install). Mirror the `preflight_check.py` pattern of `raise SystemExit(main())` as the `__main__` guard.

---

### `scripts/state_writer.py` (modify — ALLOWED_FIELDS extension)

**Analog:** `scripts/state_writer.py` itself (same Phase 3 extension pattern)

**ALLOWED_FIELDS extension pattern** (state_writer.py lines 36–40):
```python
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    # Phase 3 (already present)
    "project_path",
    "stack_choices",
    "stack_overrides",
    # Phase 4 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3)
    "gsd_phase_count",    # total phases discovered from GSD ROADMAP.md
    "failure_class",      # last classified failure class for resume
    "escalation_log",     # JSON array of escalation steps taken
}
```
Copy the existing block and append the three Phase 4 keys. Do NOT add to `REQUIRED_FIELDS` — these are optional per the established Phase 3 pattern. `COUNTER_FIELDS` does not change (phase_step, retry_count, escalation_level already listed at line 33).

---

### `scripts/tests/test_gsd_driver.py` (test)

**Analog:** `scripts/tests/test_scaffold_dispatch.py`

**Lazy import fixture pattern** (test_scaffold_dispatch.py lines 16–22):
```python
@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet created."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet created (Wave 1 target)")
```
Copy verbatim, rename fixture to `gd` and module to `"gsd_driver"`:
```python
@pytest.fixture
def gd():
    try:
        return importlib.import_module("gsd_driver")
    except ImportError:
        pytest.skip("gsd_driver module not yet created (Wave 1 target)")
```

**FakeShell usage pattern** (test_scaffold_dispatch.py lines 42–65):
```python
def test_scaffold_cmd_flags(sd, fake_shell, fake_which, tmp_path):
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
```
Apply `fake_shell` for any subprocess calls in `gsd_driver.py` that invoke `state_writer.py` as a subprocess. Capture `capsys` for slash-command emission assertions (the commands go to stdout, not subprocess).

**writer fixture for state.md setup** (conftest.py lines 30–42):
```python
def run_state_writer(*args: str, project_root: Path | None = None,
                     check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(STATE_WRITER), *args]
    if project_root is not None:
        cmd += ["--project-root", str(project_root)]
    return subprocess.run(cmd, capture_output=capture, text=True, check=check)

@pytest.fixture
def writer():
    return run_state_writer
```
Use `writer("init", "--goal", "test", project_root=tmp_project_root)` to set up state.md before each `gsd_driver` test, then `writer("write", "--field", ...)` to set specific state values. This is the established pattern from Phase 3 tests.

**Imports block** (test_scaffold_dispatch.py lines 1–13):
```python
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
```
Add `import io` and `import sys` for `capsys`-based stdout capture.

---

### `scripts/tests/test_failure_classifier.py` (test)

**Analog:** `scripts/tests/test_preflight.py`

**Lazy import fixture pattern** (test_preflight.py lines 17–23):
```python
@pytest.fixture
def pf():
    try:
        return importlib.import_module("preflight_check")
    except ImportError:
        pytest.skip("preflight_check module not yet created (Plan 02-02 target)")
```
Copy pattern, rename to `fc` / `"failure_classifier"`:
```python
@pytest.fixture
def fc():
    try:
        return importlib.import_module("failure_classifier")
    except ImportError:
        pytest.skip("failure_classifier module not yet created (Wave 1 target)")
```

**monkeypatch on stdlib pattern** (test_preflight.py lines 65–79 — builtins.input mock):
```python
monkeypatch.setattr("builtins.input", lambda *a, **kw: prompts.append(a) or "y")
```
Apply the same `monkeypatch.setattr` approach for `time.sleep`:
```python
def test_sleep_called_for_transient(fc, monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fc.handle_transient("ECONNRESET", retry_count=0)
    assert slept == [1], "retry 0 must sleep 1 second"
```

**Imports block**:
```python
from __future__ import annotations

import importlib
import pytest
```

---

### `scripts/tests/test_registry_verify.py` (test)

**Analog:** `scripts/tests/test_preflight.py`

**Lazy import fixture pattern** — same as test_failure_classifier.py:
```python
@pytest.fixture
def rv():
    try:
        return importlib.import_module("registry_verify")
    except ImportError:
        pytest.skip("registry_verify module not yet created (Wave 1 target)")
```

**monkeypatch on urllib.request.urlopen** (RESEARCH.md Pattern 6):
```python
def test_hallucinated_npm_package_blocked(rv, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(url=req.full_url, code=404, msg="Not Found",
                                    hdrs=None, fp=None)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert rv.verify_npm("@anthropic/clauded-code-helper") is False


def test_real_npm_package_passes(rv, monkeypatch):
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResponse())
    assert rv.verify_npm("next") is True
```
This uses `monkeypatch.setattr` on `"urllib.request.urlopen"` — the same string-path monkeypatch approach as the `builtins.input` mock in test_preflight.py. The FakeResponse context-manager class pattern (with `__enter__`/`__exit__`) matches the `with urllib.request.urlopen(...) as resp:` usage in the production code.

**Imports block**:
```python
from __future__ import annotations

import importlib
import urllib.error
import pytest
```

---

### `references/roles/qa.md` (config/reference doc)

**Analog:** `references/playbooks/web.md`

**Structure pattern** (web.md lines 1–29):
```markdown
# OSBuilder QA Role — Falsifiable Criteria Patterns

> Reference for the QA role. Loaded on-demand by gsd_driver.py.
> NOT pulled into SKILL.md (line limit <= 200; see Phase 1 Plan 01-02).

## Purpose

[One-paragraph description of what this file governs]

## [Section heading]

[Content]
```
Follow the same structure: `#` title, `>` blockquote for scope disclaimer, `##` sections. Keep it flat (no nested `###` unless needed). No YAML front-matter.

**Content requirements** — the file must document:
1. The VERIFICATION.md format (Phase/Criteria/Out-of-scope sections)
2. The falsifiability rule: each criterion must be verifiable without code access
3. Forbidden criterion patterns: "tests pass", "pytest exits 0", "no errors in logs" without attached user behavior
4. 5+ valid criterion examples using observable user behaviors
5. The 2-5 criteria count rule per phase

---

## Shared Patterns

### Atomic Write
**Source:** `scripts/state_writer.py` lines 111–123 (also duplicated in `scripts/scaffold_dispatch.py` lines 78–91 and `scripts/preflight_check.py` lines 59–71)
**Apply to:** `scripts/gsd_driver.py` if it needs to write any non-state.md files (e.g., VERIFICATION.md)
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

### state_writer.py Subprocess Delegation
**Source:** `scripts/scaffold_dispatch.py` lines 177–188; `scripts/stack_researcher.py` lines 133–144
**Apply to:** `scripts/gsd_driver.py` (all state writes), `scripts/failure_classifier.py` (retry_count bump)
```python
try:
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "write",
         "--field", "<field>", "--value", "<value>",
         "--project-root", str(project_root)],
        shell=False, check=True,
    )
except (OSError, subprocess.CalledProcessError):
    pass  # state.md write failure is non-fatal
```
Note: use `"bump"` subcommand (not `"write"`) for counter fields (`retry_count`, `phase_step`, `escalation_level`).

### `_check_value_safe` Input Validation
**Source:** `scripts/state_writer.py` lines 54–59
**Apply to:** Any string written to state.md via `failure_classifier.py` (error strings, escalation log entries)
```python
def _check_value_safe(value: str) -> None:
    """V5 input + V12 path-traversal: reject newlines and `..` in --value."""
    if "\n" in value or "\r" in value:
        raise SystemExit("OSBuilder: --value cannot contain newline characters.")
    if ".." in value:
        raise SystemExit("OSBuilder: --value cannot contain '..' (path traversal).")
```
Error strings passed to state.md `last_failure` field must be sanitized with this or an equivalent check (truncate + strip newlines) before writing.

### Lazy Import Fixture (Test Infrastructure)
**Source:** `scripts/tests/test_scaffold_dispatch.py` lines 16–22; `scripts/tests/test_preflight.py` lines 17–23
**Apply to:** All three new test files
```python
@pytest.fixture
def <module_abbrev>():
    try:
        return importlib.import_module("<module_name>")
    except ImportError:
        pytest.skip("<module_name> module not yet created (Wave 1 target)")
```
This pattern ensures pytest collects all test stubs in Wave 0 RED state without the module existing.

### `writer` Fixture for State.md Setup in Tests
**Source:** `scripts/tests/conftest.py` lines 30–42
**Apply to:** `scripts/tests/test_gsd_driver.py` (every test that needs a pre-seeded state.md)
```python
# In test body:
writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
writer("write", "--field", "current_phase", "--value", "1",
       project_root=tmp_project_root)
writer("write", "--field", "retry_count", "--value", "2",
       project_root=tmp_project_root)
# Read back a single field:
result = writer("read", "--field", "phase_step", project_root=tmp_project_root,
                check=True, capture=True)
step = int(result.stdout.strip())
```

### `from __future__ import annotations`
**Source:** All existing scripts (state_writer.py line 20, scaffold_dispatch.py line 5, preflight_check.py line 22)
**Apply to:** All three new scripts and all three new test files.
Always the first non-comment line after the module docstring.

### Main Guard Pattern
**Source:** `scripts/state_writer.py` line 302; `scripts/scaffold_dispatch.py` line 217
**Apply to:** All three new scripts
```python
if __name__ == "__main__":
    raise SystemExit(main())
```

---

## No Analog Found

All files have analogs. No entries.

---

## Metadata

**Analog search scope:** `scripts/`, `scripts/tests/`, `references/`
**Files scanned:** 9 (state_writer.py, preflight_check.py, scaffold_dispatch.py, stack_researcher.py, conftest.py, test_scaffold_dispatch.py, test_preflight.py, test_state_writer.py, references/playbooks/web.md)
**Pattern extraction date:** 2026-04-30
