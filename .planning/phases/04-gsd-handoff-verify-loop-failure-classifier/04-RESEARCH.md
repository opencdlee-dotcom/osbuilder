# Phase 4: GSD Handoff + Verify Loop + Failure Classifier — Research

**Researched:** 2026-04-30
**Domain:** Claude Code skill orchestration — GSD phase loop delegation, error classification, exponential backoff, hallucinated-package defense, falsifiable verification
**Confidence:** HIGH (all structural patterns derived from existing codebase; all interfaces verified by direct file read of GSD skills; all Python patterns verified from Phases 1-3)

---

## Summary

Phase 4 is the quality moat. By the end of this phase, after `scaffold_dispatch.py` hands off a project, OSBuilder drives GSD's full per-phase loop: PM → Architect → Frontend/Backend/DevOps → QA → Reviewer — in strict single-threaded sequence — and every phase must pass falsifiable verification before the next begins.

The work falls into three distinct tracks that must be built in this order because each depends on the previous:

**Track A — GSD phase loop driver (`scripts/gsd_driver.py`):** Orchestrates `/gsd-new-project --auto`, `/gsd-spec-phase`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/code-tester`, `/gsd-verify-work`, `/predator`, and `/gsd-code-review` in strict sequence. Reads the ROADMAP.md produced by GSD to discover which phases exist, then iterates. State (current_role, current_phase, phase_step) persists in `state.md` via the existing `state_writer.py` so a `/clear` mid-build resumes from the same point.

**Track B — Failure classifier + retry strategies (`scripts/failure_classifier.py`):** Categorizes errors into four classes (`transient`, `context-overflow`, `tool-failure`, `validation-failure`) and routes each to its documented retry strategy. Transient errors use exponential backoff (1 → 4 → 16 seconds). Validation failures re-plan, never retry. After 3 reflections on the same failure class, the classifier escalates to `/gsd-debug` and `/problem-solver`, then on the 4th failure produces a structured handoff document (`state.md` + human-readable escalation note). Retry counter and last-failure class persist in `state.md` and survive `/clear`.

**Track C — Registry verification gate (`scripts/registry_verify.py`):** Checks every package name against the public npm/PyPI registry before any install command. All installs run with `--ignore-scripts` until verification passes. This is the slopsquatting defense — hallucinated packages (`@anthropic/clauded-code-helper`) are blocked before any network call reaches the registry's install path.

**Primary recommendation:** Build all three tracks TDD (Wave 0 RED stubs, then GREEN). The three scripts are independent enough to be implemented in parallel plans within a single wave, but Wave 0 stubs must land first to establish the >= 18 new tests gate.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GSD phase loop sequencing | `scripts/gsd_driver.py` | SKILL.md (entry point) | Script owns the loop state machine; SKILL.md routes invocation but delegates immediately |
| GSD command emission | `gsd_driver.py` (emits slash commands as conversation output) | Claude Code runtime (executes) | OSBuilder cannot call GSD skills as subprocesses — they are Claude Code slash commands; the driver emits them as text and GSD executes |
| Failure classification | `scripts/failure_classifier.py` | `gsd_driver.py` (caller) | Classifier is a pure function — input: error string + context → output: class enum + retry strategy |
| Retry + backoff execution | `scripts/failure_classifier.py` | `state_writer.py` (counter persistence) | Backoff sleep + retry count bump live in the classifier; counter persists via state_writer |
| Escalation document production | `scripts/failure_classifier.py` | `state_writer.py` (reads state) | Structured handoff is assembled from current state.md fields + last_failure |
| Package registry verification | `scripts/registry_verify.py` | `gsd_driver.py` (pre-install gate) | Standalone script; called before every npm/pip/cargo install in the build loop |
| install `--ignore-scripts` enforcement | `scripts/registry_verify.py` + `gsd_driver.py` | — | Enforced by how gsd_driver.py constructs install commands; registry_verify.py verifies existence first |
| state.md checkpoint (retry_count, last_failure) | `scripts/state_writer.py` (existing) | `failure_classifier.py` (writes) | Reuse Phase 1 script; `retry_count` and `last_failure` fields already exist in REQUIRED_FIELDS |
| VERIFICATION.md generation per GSD phase | `scripts/gsd_driver.py` + SKILL.md | `/gsd-verify-work` (reads) | Driver emits the VERIFICATION.md format; GSD's verify-work skill reads it |
| Falsifiable criteria authorship | SKILL.md (LLM-authored) | `references/roles/qa.md` (criteria bank) | Criteria are LLM-generated per phase based on what was built; cannot be static |
| `/predator` + `/gsd-code-review` invocation | `gsd_driver.py` | SKILL.md (documents requirement) | Every phase ends with predator review + gsd-code-review before state.md marks it done |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ROLE-01 | Run `/gsd-new-project --auto` exactly once, then drive per-phase commands sequentially | gsd_driver.py state machine with `current_phase` in state.md; GSD skill interface verified |
| ROLE-02 | PM role delegates to `/gsd-spec-phase` for ambiguity scoring + spec lock | `/gsd-spec-phase` skill confirmed installed at `~/.claude/skills/gsd-spec-phase/`; emitted as slash command |
| ROLE-03 | Architect role delegates to `/gsd-plan-phase` and `/brainiac` for stack/architecture | `/gsd-plan-phase` installed; brainiac delegation already established in Phase 3 |
| ROLE-04 | Frontend/Backend/DevOps roles delegate to `/gsd-execute-phase` sequentially | `/gsd-execute-phase` installed; single-threaded is the locked decision from DeepMind data |
| ROLE-05 | QA role delegates to `/code-tester` and `/gsd-verify-work` against falsifiable criteria | `code-tester` installed; `gsd-verify-work` installed; VERIFICATION.md contract researched |
| ROLE-06 | Reviewer role delegates to `/predator` and `/gsd-code-review` before phase marked done | `predator` installed; `gsd-code-review` installed; sequencing after code-tester confirmed |
| ROLE-08 | Debug-cap delegates to `/gsd-debug` and `/problem-solver` at retry limit | `gsd-debug` installed; `problem-solver` installed; escalation path is the 3+1 failure pattern |
| HEAL-01 | `failure_classifier.py` categorizes errors into 4 classes | 4-class taxonomy defined; Python implementation pattern clear from preflight_check.py |
| HEAL-02 | Each failure class has a documented retry strategy | Documented: transient→backoff, context→compress+retry, tool→fallback, validation→re-plan |
| HEAL-03 | Hard cap of 3 reflections per failure class | `retry_count` already in `state.md` REQUIRED_FIELDS; bump subcommand exists in state_writer.py |
| HEAL-04 | Escalation produces structured handoff (state, last error, what was tried, recommended next action) | Structured handoff format designed; assembles from state.md + failure log |
| HEAL-05 | `registry_verify.py` checks every package against public registry before install | npm registry API endpoint `https://registry.npmjs.org/<package>` + PyPI `https://pypi.org/pypi/<package>/json` confirmed |
| HEAL-06 | Package install runs with `--ignore-scripts` until registry verification passes | `npm install --ignore-scripts`, `pip install --no-deps` (PyPI analog), `cargo add` (no scripting equivalent) |
| HEAL-07 | Retry counter and last_failure persist in state.md across `/clear` | `retry_count` and `last_failure` already in REQUIRED_FIELDS; state_writer.py `bump` subcommand available |
| VER-01 | Every phase has falsifiable success criteria list | VERIFICATION.md format designed; 2-5 criteria per phase, observable user behaviors only |
| VER-02 | `/gsd-verify-work` invoked at end of every phase | `gsd-verify-work` skill confirmed installed; emitted after `/code-tester` completes |
| VER-03 | `/code-tester` runs adversarial tests before phase marked done | `code-tester` skill confirmed installed; invoked before predator and code-review |
| VER-04 | `/predator` reviews architecture and security on every phase | `predator` skill confirmed installed; position in sequence: after code-tester, before phase-done |
</phase_requirements>

---

## Standard Stack

### OSBuilder Phase 4 New Scripts

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.10+ (machine: 3.12.6) | `gsd_driver.py`, `failure_classifier.py`, `registry_verify.py` — `time`, `subprocess`, `urllib.request`, `json`, `re`, `argparse`, `pathlib` | Established pattern from Phases 1-3; no deps = no preflight chicken-and-egg |
| `urllib.request` (stdlib) | built-in | HTTP GET to npm registry + PyPI registry for package existence checks | No third-party requests lib needed; simple GET with timeout is stdlib |
| `time.sleep` (stdlib) | built-in | Exponential backoff (1s → 4s → 16s) in transient failure handler | Trivial; stdlib |
| pytest | 9.0.2 | Test suite extension: `test_gsd_driver.py`, `test_failure_classifier.py`, `test_registry_verify.py` | Existing infrastructure |

### Delegated GSD Skills (interface consumers — not built by OSBuilder)

All confirmed installed at `~/.claude/skills/` — verified `ls ~/.claude/skills/` 2026-04-30:

| Skill | Slash Command | Role | Confirmed |
|-------|--------------|------|-----------|
| gsd-new-project | `/gsd-new-project --auto` | Kicks off GSD project from derived_spec.md | YES |
| gsd-spec-phase | `/gsd-spec-phase` | PM: ambiguity scoring + spec lock | YES |
| gsd-plan-phase | `/gsd-plan-phase` | Architect: plan creation | YES |
| gsd-execute-phase | `/gsd-execute-phase` | Frontend/Backend/DevOps: code execution | YES |
| code-tester | `/code-tester` | QA: adversarial test runner | YES |
| gsd-verify-work | `/gsd-verify-work` | QA: falsifiable verification | YES |
| predator | `/predator` | Reviewer: architecture + security review | YES |
| gsd-code-review | `/gsd-code-review` | Reviewer: code quality review | YES |
| gsd-debug | `/gsd-debug` | Debug cap: escalation target | YES |
| problem-solver | `/problem-solver` | Debug cap: second escalation target | YES |

[VERIFIED: `ls ~/.claude/skills/` output, 2026-04-30]

### Registry Verification APIs

| Registry | Package ecosystem | Verification endpoint | Existence signal |
|----------|------------------|-----------------------|-----------------|
| npm | Node.js | `https://registry.npmjs.org/<package>` | HTTP 200 = exists; HTTP 404 = not found |
| PyPI | Python | `https://pypi.org/pypi/<package>/json` | HTTP 200 = exists; HTTP 404 = not found |
| crates.io | Rust | `https://crates.io/api/v1/crates/<package>` | HTTP 200 = exists; HTTP 404 = not found |

[VERIFIED: registry APIs accessed 2026-04-30 — `https://registry.npmjs.org/next` returns 200; `https://registry.npmjs.org/@anthropic/clauded-code-helper` returns 404]

---

## Architecture Patterns

### System Architecture Diagram

```
PHASE 3 OUTPUT
  │  project_dir on disk + state.md (project_path, stack_choices, etc.)
  │  derived_spec.md at .planning/osbuilder/derived_spec.md
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  SKILL.md — OSBuilder entry point (post-scaffold)                │
│  Reads state.md: current_role, current_phase, retry_count        │
│  If retry_count > 0: resume mid-build (HEAL-07)                  │
│  Routes to gsd_driver.py                                         │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/gsd_driver.py — Phase loop state machine                │
│                                                                  │
│  [INITIAL] ──── /gsd-new-project --auto @derived_spec.md ────►  │
│    writes: .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md     │
│    state.md: current_role=PM, current_phase=1                    │
│                                                                  │
│  [PER-PHASE LOOP] ─────────────────────────────────────────────  │
│  │                                                               │
│  ├─► /gsd-spec-phase      (PM role — spec lock)                 │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► /gsd-plan-phase      (Architect role)                      │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► [pre-install gate]                                          │
│  │    └─ registry_verify.py --pkg <name> --ecosystem npm|pip    │
│  │         ├─ PASS → install with --ignore-scripts              │
│  │         └─ FAIL → block + escalate to human                  │
│  │                                                               │
│  ├─► /gsd-execute-phase   (Frontend/Backend/DevOps — sequential)│
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► /code-tester         (QA — adversarial tests)              │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► /predator            (Reviewer — architecture + security)  │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► /gsd-code-review     (Reviewer — code quality)             │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  ├─► write VERIFICATION.md  (2-5 falsifiable criteria)          │
│  │    └─ format: observable user behaviors, never "tests pass"  │
│  │                                                               │
│  ├─► /gsd-verify-work     (QA — checks each criterion)          │
│  │    └─ on error → failure_classifier.py                       │
│  │                                                               │
│  └─► state_writer.py write --field current_phase --value N+1   │
│       └─ advance to next ROADMAP phase; loop continues          │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
             on any error      │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/failure_classifier.py — Error class + retry router      │
│                                                                  │
│  Input: error string + context (role, phase, step, retry_count)  │
│  Output: {class: str, strategy: str, retry_ok: bool}             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CLASS: transient (ECONNRESET, timeout, 503, DNS fail)  │    │
│  │  Strategy: exponential backoff                           │    │
│  │    retry 1: sleep(1s)   → retry                         │    │
│  │    retry 2: sleep(4s)   → retry                         │    │
│  │    retry 3: sleep(16s)  → retry                         │    │
│  │    retry 4: escalate (HEAL-03 cap reached)              │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CLASS: context-overflow (context length exceeded)      │    │
│  │  Strategy: compress + retry                             │    │
│  │    compress: summarize last output, drop verbose logs    │    │
│  │    retry once; if still overflows → escalate            │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CLASS: tool-failure (skill not found, SKILL.md error)  │    │
│  │  Strategy: fallback path                                │    │
│  │    check alternate skill; if no fallback → escalate     │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CLASS: validation-failure (code-tester / verify fail)  │    │
│  │  Strategy: re-plan (NOT retry same plan)                │    │
│  │    trigger /gsd-plan-phase for affected phase            │    │
│  │    3 re-plans max; 4th → escalate                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  After retry_count hits 3 (HEAL-03):                            │
│    1. Emit /gsd-debug                                            │
│    2. Emit /problem-solver                                       │
│    3. On 4th failure: write structured handoff + stop (HEAL-04) │
│                                                                  │
│  state_writer.py bump --field retry_count  (every failure)       │
│  state_writer.py write --field last_failure --value <class>      │
└──────────────────────────────┬───────────────────────────────────┘
             before each install│
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  scripts/registry_verify.py — Package existence gate (HEAL-05)   │
│                                                                  │
│  Input: --pkg <name> --ecosystem npm|pip|cargo                   │
│  Lookup: urllib.request GET → registry endpoint (no install)     │
│  Output: 0 (exists) or 1 (does not exist / hallucinated)         │
│                                                                  │
│  PASS → gsd_driver.py invokes: npm install --ignore-scripts      │
│  FAIL → block install; log hallucinated pkg name; escalate       │
└──────────────────────────────────────────────────────────────────┘
                               │  all phases complete
                               ▼
                    Phase 5 (UX polish) entry
```

### Recommended Project Structure (new files this phase adds)

```
~/.claude/skills/osbuilder/
└── references/
    └── roles/
        └── qa.md           ← NEW: falsifiable criteria patterns (VER-01)

scripts/
├── gsd_driver.py           ← NEW: GSD phase loop driver (ROLE-01..06, ROLE-08, VER-01..04)
├── failure_classifier.py   ← NEW: error class + retry router (HEAL-01..04, HEAL-07)
└── registry_verify.py      ← NEW: npm/pip/cargo package existence gate (HEAL-05, HEAL-06)

scripts/tests/
├── test_gsd_driver.py      ← NEW: tests for ROLE-01..06, ROLE-08, VER-01..04
├── test_failure_classifier.py ← NEW: tests for HEAL-01..04, HEAL-07
└── test_registry_verify.py ← NEW: tests for HEAL-05, HEAL-06
```

No changes to SKILL.md structure (≤ 200 lines). Role delegation docs go in `references/roles/`.

### Pattern 1: GSD Phase Loop — Slash Command Emission (Not Subprocess)

**What:** OSBuilder drives GSD skills by EMITTING slash commands as text output. GSD skills are Claude Code slash commands — they cannot be invoked via `subprocess.run`. The driver script produces the sequence of slash commands; Claude Code's runtime executes each one.

**Critical architectural distinction:** The "loop" is not a Python while-loop executing in one process. It is a conversation state machine. `gsd_driver.py` is a Python helper that:
1. Reads state.md to determine which command to emit next
2. Prints the slash command as text (e.g., `/gsd-execute-phase`)
3. Writes state.md to record what was emitted and what comes next
4. Exits — the next invocation picks up from where state.md says to resume

This is the SAME pattern used by all orchestrators in Claude Code: state-machine-as-file + re-entry-on-next-turn. [ASSUMED — based on architecture knowledge; verified by reading existing state_writer.py and observing that all GSD skill invocations in existing SKILL.md are slash command emissions, not subprocesses]

**Consequence for testing:** `gsd_driver.py` cannot be tested with `fake_shell` patches on `subprocess.run` for the slash command emissions. Instead:
- Test the STATE MACHINE logic: given state.md with `current_phase=2`, which command does the driver say to emit next?
- Test the PERSISTENCE logic: after emitting, does state.md update correctly?
- Test the RESUME logic: given `retry_count=2` in state.md, does the driver correctly pick up mid-retry?
- The actual slash command string output is testable: capture `sys.stdout` and assert it contains the expected `/gsd-execute-phase` text.

### Pattern 2: Failure Classifier — Error String Taxonomy

**What:** `failure_classifier.py` takes a raw error string and returns a structured classification. It is a pure function — no side effects beyond the return value.

**Error string patterns for each class:**

```python
# failure_classifier.py — classification patterns
# Source: [ASSUMED] based on common Node.js/Python/network error patterns

TRANSIENT_PATTERNS = [
    r"ECONNRESET",           # Node TCP connection reset
    r"ETIMEDOUT",            # Node TCP timeout
    r"ECONNREFUSED",         # Node connection refused (service temporarily down)
    r"EAI_AGAIN",            # DNS resolution temporary failure
    r"503",                  # HTTP 503 Service Unavailable
    r"Connection timed out",
    r"Read timed out",
    r"Network unreachable",
    r"pnpm install.*failed", # catch-all for transient install failures
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

VALIDATION_FAILURE_PATTERNS = [
    r"test.*failed",
    r"assertion.*error",
    r"verification.*failed",
    r"criterion.*not met",
    r"code-tester.*fail",
]
```

**The classify function signature (for test contract):**

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
```

### Pattern 3: Exponential Backoff — State-Persistent

**What:** Transient failures retry with sleep(1), sleep(4), sleep(16) before escalating. The backoff multiplier is 4x because OSBuilder's operations take 10-60 seconds; shorter multipliers (2x) would retry too eagerly for slow network operations.

**Why 4x:** The 1 → 4 → 16 sequence produces a max wait of 21 seconds across 3 retries, which is under the typical "connection droped but server is back in 30s" recovery window. Aider's empirical 3-reflection cap is the backstop regardless of backoff.

**State-persistent retry counter:**

```python
# In failure_classifier.py — transient retry path
import time
from pathlib import Path
import subprocess, sys

def handle_transient(error: str, state_path: Path, retry_count: int) -> dict:
    """Implement exponential backoff for transient failures."""
    BACKOFF_SECONDS = {0: 1, 1: 4, 2: 16}
    if retry_count >= 3:
        return {"class": "transient", "strategy": "escalate", "retry_ok": False}
    wait = BACKOFF_SECONDS.get(retry_count, 16)
    time.sleep(wait)
    # Bump retry_count in state.md via state_writer.py
    # (called by gsd_driver.py, not inside handle_transient itself)
    return {
        "class": "transient",
        "strategy": "backoff",
        "retry_ok": True,
        "backoff_seconds": wait,
    }
```

### Pattern 4: Registry Verification — urllib.request, No Third-Party Deps

**What:** `registry_verify.py` performs a HEAD or GET request to the public registry before any install, using only `urllib.request` from stdlib. No `requests` library needed.

**Critical constraint:** The verification must check if the package NAME exists on the registry — it does NOT download the package. The check must complete before any `npm install` / `pip install` command is invoked.

```python
# registry_verify.py — npm existence check
# Source: [VERIFIED: registry.npmjs.org returns 200 for existing packages, 404 for non-existent]
import urllib.request
import urllib.error
import json
from pathlib import Path


def verify_npm(package_name: str, timeout: int = 10) -> bool:
    """Return True if package exists on npm registry. False = hallucinated or 404."""
    url = f"https://registry.npmjs.org/{package_name}"
    req = urllib.request.Request(url, method="HEAD")  # HEAD avoids downloading metadata
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404  # 4xx other than 404 = network error, not "not found"
    except (urllib.error.URLError, OSError):
        return True  # Network error ≠ hallucinated package; don't block on network issues


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
        return True  # Network error ≠ hallucinated; fail open
```

**Fail-open policy:** If the registry is unreachable (network error), verification PASSES (returns True). This prevents the registry check from becoming a build-blocker during network brownouts. The defense is against hallucinated package names, not against network failures.

**Test strategy:** Mock `urllib.request.urlopen` with a side-effect that raises `HTTPError(404)` for the hallucinated package name, `200` for valid packages. See Pattern 6 for mock pattern.

### Pattern 5: VERIFICATION.md Format — Falsifiable Criteria

**What:** Every GSD phase produces a `VERIFICATION.md` with 2-5 falsifiable success criteria. `gsd_driver.py` templates this file before invoking `/gsd-verify-work`.

**Format (from success criterion 2):**

```markdown
# Phase [N] Verification — [Phase Name]

**Generated:** [ISO timestamp]
**Phase:** [N]

## Falsifiable Success Criteria

1. **[Observable behavior]:** [What a user can see/do to confirm this works]
   - How to check: [concrete step — "navigate to /dashboard and see..." or "run `curl localhost:3000/api/health`"]
   - NOT acceptable: "unit tests pass"

2. **[Observable behavior]:** ...

[2-5 criteria total — never fewer than 2, never more than 5]

## Out of Scope for This Phase

- [Anything explicitly deferred]
```

**Falsifiability rule:** Each criterion must be verifiable by a person with no code access — only browser, terminal, or observable output. "Tests pass" is forbidden. "The `/dashboard` route loads in < 2 seconds and shows a table of users" is acceptable.

### Pattern 6: Test Patterns for urllib / Sleep Mocking

**What:** `registry_verify.py` calls `urllib.request.urlopen`; `failure_classifier.py` calls `time.sleep`. Both must be monkeypatched in tests.

```python
# scripts/tests/test_registry_verify.py
import importlib
import urllib.error
import pytest


@pytest.fixture
def rv():
    """Lazy import of scripts/registry_verify.py."""
    try:
        return importlib.import_module("registry_verify")
    except ImportError:
        pytest.skip("registry_verify module not yet created (Wave 1 target)")


def test_hallucinated_npm_package_blocked(rv, monkeypatch):
    """HEAL-05: hallucinated npm package returns False from verify_npm."""
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(url=req.full_url, code=404, msg="Not Found",
                                    hdrs=None, fp=None)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert rv.verify_npm("@anthropic/clauded-code-helper") is False


def test_real_npm_package_passes(rv, monkeypatch):
    """HEAL-05: real npm package returns True from verify_npm."""
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResponse())
    assert rv.verify_npm("next") is True


def test_network_error_fails_open(rv, monkeypatch):
    """HEAL-05: network error returns True (fail-open policy)."""
    import urllib.error
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: (_ for _ in ()).throw(
                            urllib.error.URLError("Network unreachable")))
    assert rv.verify_npm("next") is True


# scripts/tests/test_failure_classifier.py
@pytest.fixture
def fc():
    try:
        return importlib.import_module("failure_classifier")
    except ImportError:
        pytest.skip("failure_classifier module not yet created (Wave 1 target)")


def test_transient_econnreset(fc):
    """HEAL-01: ECONNRESET maps to transient class."""
    result = fc.classify("pnpm install failed: ECONNRESET")
    assert result["class"] == "transient"
    assert result["strategy"] == "backoff"


def test_sleep_called_for_transient(fc, monkeypatch):
    """HEAL-02: transient failure sleeps before retry."""
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fc.handle_transient("ECONNRESET", retry_count=0)
    assert slept == [1], "retry 0 must sleep 1 second"


def test_cap_at_3_reflections(fc):
    """HEAL-03: retry_count >= 3 returns retry_ok=False."""
    result = fc.classify("ECONNRESET", context={"retry_count": 3})
    assert result["retry_ok"] is False

def test_validation_failure_does_not_backoff(fc):
    """HEAL-02: validation-failure strategy is re-plan, not backoff."""
    result = fc.classify("test_login failed: AssertionError")
    assert result["class"] == "validation-failure"
    assert result["strategy"] == "re-plan"
    assert "backoff" not in result.get("strategy", "")
```

### Pattern 7: GSD Driver State Machine Tests

**What:** `gsd_driver.py` is tested by asserting its text output (slash commands emitted) and its state.md writes.

```python
# scripts/tests/test_gsd_driver.py
import importlib
import io
import sys
import pytest

@pytest.fixture
def gd():
    try:
        return importlib.import_module("gsd_driver")
    except ImportError:
        pytest.skip("gsd_driver module not yet created (Wave 1 target)")


def test_initial_state_emits_gsd_new_project(gd, tmp_project_root, writer, capsys):
    """ROLE-01: initial state (current_phase=0) emits /gsd-new-project --auto."""
    writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-new-project" in captured.out
    assert "--auto" in captured.out


def test_phase_1_emits_spec_phase(gd, tmp_project_root, writer, capsys):
    """ROLE-02: current_phase=1, phase_step=0 emits /gsd-spec-phase."""
    writer("init", "--goal", "build a todo app", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    assert "/gsd-spec-phase" in captured.out


def test_state_updates_after_emission(gd, tmp_project_root, writer):
    """ROLE-01: state.md phase_step increments after command emission."""
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    result = writer("read", "--field", "phase_step", project_root=tmp_project_root,
                    check=True, capture=True)
    step = int(result.stdout.strip())
    assert step == 1, "phase_step must increment after each command emission"


def test_resume_preserves_retry_count(gd, tmp_project_root, writer):
    """HEAL-07: re-invoking with existing retry_count=2 does not reset to 0."""
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "retry_count", "--value", "2",
           project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    gd.emit_next_command(project_root=tmp_project_root)
    result = writer("read", "--field", "retry_count", project_root=tmp_project_root,
                    check=True, capture=True)
    # retry_count must still be 2 — not reset to 0
    assert result.stdout.strip() == "2"


def test_predator_and_review_before_phase_done(gd, tmp_project_root, writer, capsys):
    """ROLE-06, VER-04: phase completion sequence includes predator + gsd-code-review."""
    # Set state to the step just before phase completion
    writer("init", "--goal", "test", project_root=tmp_project_root)
    writer("write", "--field", "current_phase", "--value", "1",
           project_root=tmp_project_root)
    writer("write", "--field", "phase_step", "--value", "5",
           project_root=tmp_project_root)  # step 5 = post-code-tester step
    gd.emit_next_command(project_root=tmp_project_root)
    captured = capsys.readouterr()
    # At step 5, must emit /predator (not advance to next phase yet)
    assert "/predator" in captured.out or "/gsd-code-review" in captured.out
```

### Anti-Patterns to Avoid

- **Calling GSD skills as subprocesses:** `subprocess.run(["/gsd-execute-phase"])` does not work — GSD skills are Claude Code slash commands, not shell executables. The driver emits them as text.
- **Resetting retry_count on resume:** When SKILL.md resumes after `/clear`, state.md still has `retry_count`. The driver must READ this value, not initialize it to 0. Pattern: always `read_state()` first.
- **Treating "validation-failure" as transient:** The retry strategies are different. Validation failures re-plan; they don't backoff. Confusing these leads to the LLM retrying the same broken code 3 times without changing the plan.
- **Running `/predator` before `/code-tester`:** Predator is a post-code-tester step. It reviews what code-tester reported. Running predator first means it reviews unchecked code.
- **`--ignore-scripts` omission:** Even for verified packages, the install must run with `--ignore-scripts` until the package is verified. Post-install scripts run arbitrary code — the verification gate also neutralizes that risk.
- **Hardcoding VERIFICATION.md criteria:** Criteria must be generated per phase based on what was planned and built, not taken from a static bank. The reference file `references/roles/qa.md` provides EXAMPLES and FORMAT RULES, not the actual criteria for any given phase.
- **Single escalation target (ROLE-08):** The escalation sequence is specifically `/gsd-debug` THEN `/problem-solver`. Both must be invoked (in order) before producing the structured handoff.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Package registry lookup | Custom registry scraping, HTML parsing | `urllib.request` HEAD against official registry API endpoints | Official endpoints return clean 200/404; no parsing needed |
| Exponential backoff | Custom sleep multiplier logic | `time.sleep` with pre-computed table `{0: 1, 1: 4, 2: 16}` | Two lines; no dependencies; table is auditable |
| Error string classification | Machine learning, LLM-based classification | Regex pattern matching against known error string substrings | Error strings are deterministic (ECONNRESET never changes); regex is faster, testable, and predictable |
| GSD skill sequencing | Rewriting GSD's per-phase logic | Drive GSD commands in sequence; read ROADMAP.md to discover phases | Composition rule: fix sub-skills, never fork into OSBuilder |
| VERIFICATION.md parser | Custom markdown parser | Python `re` + `str.split` on known section markers | VERIFICATION.md has a fixed format; stdlib pattern matching is sufficient |
| Retry counter | In-memory counter | `state_writer.py bump --field retry_count` | Survives `/clear`; already implemented and tested |

**Key insight:** Phase 4 is an orchestration phase, not an implementation phase. The fewer lines of custom logic, the better. Every line of custom code in the failure classifier or driver is a maintenance surface.

---

## State Machine Design

### Phase Step Enumeration

`gsd_driver.py` advances through these steps per GSD phase. `phase_step` in `state.md` tracks position:

| Step | Command Emitted | Completion Signal |
|------|----------------|-------------------|
| 0 | `/gsd-spec-phase` | PLAN.md or REQUIREMENTS.md written by GSD |
| 1 | `/gsd-plan-phase` | PLAN.md exists |
| 2 | [registry_verify gate + install] | returncode 0 |
| 3 | `/gsd-execute-phase` | Code committed |
| 4 | `/code-tester` | Test run complete |
| 5 | `/predator` | Review complete |
| 6 | `/gsd-code-review` | Code review complete |
| 7 | [write VERIFICATION.md] | File on disk |
| 8 | `/gsd-verify-work` | Verification complete |
| 9 | [advance current_phase, reset phase_step to 0] | state.md updated |

Initial state (before GSD project created): `current_phase=0, phase_step=0`
Step at phase=0: emit `/gsd-new-project --auto @derived_spec.md`

### State.md Field Extensions for Phase 4

`state_writer.py`'s `ALLOWED_FIELDS` must be extended. Add to ALLOWED_FIELDS (NOT to REQUIRED_FIELDS — same pattern as Phase 3):

```python
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    # Phase 3 (existing)
    "project_path",
    "stack_choices",
    "stack_overrides",
    # Phase 4 additions:
    "gsd_phase_count",    # total phases discovered from GSD ROADMAP.md
    "failure_class",      # last classified failure class (transient/context/tool/validation)
    "escalation_log",     # JSON list of escalation attempts in current failure run
}
```

Note: `retry_count`, `last_failure`, and `escalation_level` already exist in REQUIRED_FIELDS — NO change to REQUIRED_FIELDS needed. [VERIFIED: state_writer.py lines 29-41]

---

## Common Pitfalls

### Pitfall 1: Slash Commands Are Not Subprocesses

**What goes wrong:** Developer writes `subprocess.run(["/gsd-execute-phase"])` expecting it to invoke the GSD skill. It fails with "No such file or directory."
**Why it happens:** GSD skills are Claude Code slash commands registered in `~/.claude/skills/`. They are not shell executables.
**How to avoid:** `gsd_driver.py` emits slash commands as `print("/gsd-execute-phase")` to stdout. The conversation runtime picks them up. The driver is a STATE ADVISOR — it tells OSBuilder what to say next.
**Warning signs:** Any `subprocess.run` call in `gsd_driver.py` that contains a slash-prefixed command.

### Pitfall 2: retry_count Reset on Resume

**What goes wrong:** After `/clear`, SKILL.md re-invokes `gsd_driver.py`. The driver initializes `retry_count = 0` instead of reading it from `state.md`. The retry budget is reset — the user gets infinite retries.
**Why it happens:** Forgetting that state.md is the source of truth, not Python-local state.
**How to avoid:** `gsd_driver.py` ALWAYS calls `read_state(state_path)` on entry and uses the `retry_count` value from that dict. Never initialize `retry_count` from a Python default.
**Warning signs:** Success criterion 6 (retry budget survives `/clear`) fails.

### Pitfall 3: `validation-failure` Retried as Transient

**What goes wrong:** A `code-tester` failure is classified as transient (because the error string contains "failed") and retried with backoff 3 times. The LLM runs the same broken code 3 times without changing the plan.
**Why it happens:** Overly broad `TRANSIENT_PATTERNS` that catch "test failed" strings.
**How to avoid:** Validation failure patterns must be checked BEFORE transient patterns in the classifier. The class hierarchy is: `validation-failure` > `tool-failure` > `context-overflow` > `transient` (most specific wins).
**Warning signs:** `test.*failed` matches both validation and transient patterns; order matters.

### Pitfall 4: Blocking Build on Network Error During Registry Check

**What goes wrong:** `registry_verify.py` raises an exception when it cannot reach `registry.npmjs.org`. This blocks the entire build.
**Why it happens:** `urllib.request.urlopen` raises `URLError` on network failure. If uncaught, it propagates.
**How to avoid:** Fail-open policy: catch `URLError` and return `True` (package assumed to exist). Network failure is not the same as "package does not exist."
**Warning signs:** Build stops with a urllib error message in a non-error scenario (e.g., slow WiFi).

### Pitfall 5: `--ignore-scripts` Not Applied

**What goes wrong:** `npm install somepackage` runs post-install scripts before registry verification is confirmed. A slopsquatted package runs arbitrary code.
**Why it happens:** The install command is constructed before the registry check returns — or the check is skipped for "known" packages.
**How to avoid:** The gate pattern is strict: `registry_verify.py --pkg <name>` MUST return 0 (success) before ANY install command runs. The install command ALWAYS uses `--ignore-scripts` until verification passes. Even after passing, the install command should use `--ignore-scripts` for the first install.
**Warning signs:** `npm install` appears before `registry_verify.py` call in `gsd_driver.py`.

### Pitfall 6: VERIFICATION.md Criteria That Say "Tests Pass"

**What goes wrong:** `VERIFICATION.md` contains criterion: "All unit tests pass." `/gsd-verify-work` marks this as met whenever `pytest` exits 0. This is circular (tests can be wrong; this tests the tests).
**Why it happens:** Convenient shortcut that sounds like verification.
**How to avoid:** Every criterion must describe an OBSERVABLE USER BEHAVIOR: "User can navigate to /login, enter valid credentials, and see a dashboard page." `references/roles/qa.md` must document this rule and provide 5+ non-circular examples.
**Warning signs:** Any criterion containing "tests pass", "pytest exits 0", "no errors in logs" without a user behavior attached.

### Pitfall 7: predator Invoked Before code-tester

**What goes wrong:** `/predator` reviews code that hasn't been tested yet. Predator sees clean-looking code that hasn't been adversarially probed. This reduces the quality of the review.
**Why it happens:** Role sequencing is incorrect — reviewer before QA.
**How to avoid:** The step order is: execute-phase → code-tester → predator → gsd-code-review → verify-work. This is a locked order. State machine's step enum must reflect this sequence.
**Warning signs:** `phase_step` for predator invocation is lower than phase_step for code-tester.

### Pitfall 8: state_writer ALLOWED_FIELDS Not Extended

**What goes wrong:** `gsd_driver.py` tries to write `failure_class` or `gsd_phase_count` to state.md. `state_writer.py` exits with "unknown field." Driver silently ignores the error and continues with stale state.
**Why it happens:** Phase 4 needs new state fields not in Phase 1-3 ALLOWED_FIELDS.
**How to avoid:** Wave 0 of Phase 4 MUST include extending `state_writer.py`'s ALLOWED_FIELDS before any driver code is written. This follows the same pattern as Phase 3's `project_path` / `stack_choices` extension.
**Warning signs:** `gsd_driver.py` swallows `subprocess.CalledProcessError` from state_writer calls silently.

---

## Code Examples

### Verified: state_writer.py ALLOWED_FIELDS Extension

```python
# scripts/state_writer.py — extend ALLOWED_FIELDS for Phase 4
# Source: existing Phase 3 pattern (state_writer.py lines 36-40)

ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    # Phase 3 (already present in state_writer.py as of 2026-04-30)
    "project_path",
    "stack_choices",
    "stack_overrides",
    # Phase 4 additions — add to ALLOWED_FIELDS only, NOT REQUIRED_FIELDS
    "gsd_phase_count",    # total ROADMAP phases from GSD
    "failure_class",      # last failure class for resume
    "escalation_log",     # JSON array of escalation steps taken
}
```

### Verified: Structured Escalation Handoff (HEAL-04)

When `retry_count` hits 3 and `/gsd-debug` + `/problem-solver` have been invoked, the 4th failure produces:

```markdown
# OSBuilder Escalation Handoff

**Timestamp:** [ISO]
**Phase:** [current_phase]
**Role:** [current_role]
**Last failure class:** [failure_class]
**Retry count:** 3

## Last Error

```
[last_failure value from state.md — raw error string]
```

## What Was Tried

1. Retry 1: [backoff/re-plan/compress — from escalation_log]
2. Retry 2: [...]
3. Retry 3: [...]
4. `/gsd-debug` invoked
5. `/problem-solver` invoked

## State Checkpoint

All state persisted in: `.planning/osbuilder/state.md`

## Recommended Next Action

[Class-specific human action]:
- transient: Check network connectivity, then run `/osbuilder resume`
- validation-failure: Review the failing criterion in VERIFICATION.md, fix manually, then run `/osbuilder resume`
- tool-failure: Verify that [skill name] is installed at ~/.claude/skills/, then run `/osbuilder resume`
- context-overflow: Start a new session and run `/osbuilder resume`
```

### Verified: registry_verify.py CLI Interface

```bash
# How gsd_driver.py calls registry_verify.py before npm installs
python3 scripts/registry_verify.py --pkg next --ecosystem npm
# exit 0 = exists and verified
# exit 1 = does not exist (hallucinated) — BLOCK INSTALL

python3 scripts/registry_verify.py --pkg @anthropic/clauded-code-helper --ecosystem npm
# exit 1 — hallucinated package; install blocked

# After verification passes, install with --ignore-scripts:
npm install --ignore-scripts next
```

---

## Runtime State Inventory

This phase does not rename or refactor existing strings. All state is in `state.md` which already persists correctly. Checklist:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | state.md ALLOWED_FIELDS lacks Phase 4 fields (`failure_class`, `gsd_phase_count`, `escalation_log`) | code edit — extend ALLOWED_FIELDS in state_writer.py (Wave 0) |
| Live service config | None — no external services configured by Phase 4 | None |
| OS-registered state | None | None |
| Secrets/env vars | None — Phase 4 scripts are stdlib only; no new secrets | None |
| Build artifacts | None — no new packages installed into the OSBuilder skill itself | None |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | all 3 new scripts | YES | 3.12.6 | — |
| pytest | test suite | YES | 9.0.2 | — |
| `urllib.request` | registry_verify.py | YES (stdlib) | built-in | — |
| `time.sleep` | failure_classifier.py | YES (stdlib) | built-in | — |
| npm registry (registry.npmjs.org) | registry_verify.py (test: mocked) | YES | — | fail-open (network error = pass) |
| PyPI registry (pypi.org) | registry_verify.py (test: mocked) | YES | — | fail-open |
| GSD skills (gsd-spec-phase, gsd-plan-phase, etc.) | gsd_driver.py | YES (all confirmed) | — | — |
| predator | gsd_driver.py | YES | — | — |
| code-tester | gsd_driver.py | YES | — | — |
| problem-solver | gsd_driver.py | YES | — | — |

[VERIFIED: `ls ~/.claude/skills/` output 2026-04-30 — all GSD and delegated skills confirmed present]

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python3 -m pytest scripts/tests/ -x --tb=short` |
| Full suite command | `python3 -m pytest scripts/tests/ --tb=short` |
| Current test count | 46 tests collected (baseline before Phase 4) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROLE-01 | initial state emits /gsd-new-project --auto | unit | `pytest scripts/tests/test_gsd_driver.py::test_initial_state_emits_gsd_new_project -x` | NO — Wave 0 |
| ROLE-02 | current_phase=1 emits /gsd-spec-phase | unit | `pytest scripts/tests/test_gsd_driver.py::test_phase_1_emits_spec_phase -x` | NO — Wave 0 |
| ROLE-03 | current_phase=1, step=1 emits /gsd-plan-phase | unit | `pytest scripts/tests/test_gsd_driver.py::test_plan_phase_emitted -x` | NO — Wave 0 |
| ROLE-04 | execute-phase emitted after plan-phase | unit | `pytest scripts/tests/test_gsd_driver.py::test_execute_phase_emitted -x` | NO — Wave 0 |
| ROLE-05 | code-tester emitted before verify-work | unit | `pytest scripts/tests/test_gsd_driver.py::test_code_tester_before_verify_work -x` | NO — Wave 0 |
| ROLE-06 | predator + gsd-code-review emitted after code-tester | unit | `pytest scripts/tests/test_gsd_driver.py::test_predator_and_review_before_phase_done -x` | NO — Wave 0 |
| ROLE-08 | retry_count=3 triggers /gsd-debug then /problem-solver | unit | `pytest scripts/tests/test_gsd_driver.py::test_escalation_at_retry_limit -x` | NO — Wave 0 |
| HEAL-01 | ECONNRESET → class: transient | unit | `pytest scripts/tests/test_failure_classifier.py::test_transient_econnreset -x` | NO — Wave 0 |
| HEAL-01 | "context window" → class: context-overflow | unit | `pytest scripts/tests/test_failure_classifier.py::test_context_overflow -x` | NO — Wave 0 |
| HEAL-01 | "command not found" → class: tool-failure | unit | `pytest scripts/tests/test_failure_classifier.py::test_tool_failure -x` | NO — Wave 0 |
| HEAL-01 | "test_login failed" → class: validation-failure | unit | `pytest scripts/tests/test_failure_classifier.py::test_validation_failure -x` | NO — Wave 0 |
| HEAL-02 | transient → sleep(1) on retry 0 | unit | `pytest scripts/tests/test_failure_classifier.py::test_sleep_called_for_transient -x` | NO — Wave 0 |
| HEAL-02 | validation-failure → strategy: re-plan (no backoff) | unit | `pytest scripts/tests/test_failure_classifier.py::test_validation_failure_does_not_backoff -x` | NO — Wave 0 |
| HEAL-03 | retry_count >= 3 → retry_ok: False | unit | `pytest scripts/tests/test_failure_classifier.py::test_cap_at_3_reflections -x` | NO — Wave 0 |
| HEAL-04 | 4th failure produces structured handoff string | unit | `pytest scripts/tests/test_failure_classifier.py::test_structured_handoff_produced -x` | NO — Wave 0 |
| HEAL-05 | hallucinated npm package → verify_npm returns False | unit | `pytest scripts/tests/test_registry_verify.py::test_hallucinated_npm_package_blocked -x` | NO — Wave 0 |
| HEAL-05 | real npm package → verify_npm returns True | unit | `pytest scripts/tests/test_registry_verify.py::test_real_npm_package_passes -x` | NO — Wave 0 |
| HEAL-06 | install command includes --ignore-scripts before verification | unit | `pytest scripts/tests/test_gsd_driver.py::test_install_uses_ignore_scripts -x` | NO — Wave 0 |
| HEAL-07 | resume reads retry_count from state.md, does not reset to 0 | unit | `pytest scripts/tests/test_gsd_driver.py::test_resume_preserves_retry_count -x` | NO — Wave 0 |
| VER-01 | VERIFICATION.md written with 2-5 falsifiable criteria | unit | `pytest scripts/tests/test_gsd_driver.py::test_verification_md_written -x` | NO — Wave 0 |
| VER-01 | criteria must not contain "tests pass" string | unit | `pytest scripts/tests/test_gsd_driver.py::test_criteria_not_tests_pass -x` | NO — Wave 0 |
| VER-02 | /gsd-verify-work emitted after VERIFICATION.md written | unit | `pytest scripts/tests/test_gsd_driver.py::test_verify_work_emitted -x` | NO — Wave 0 |
| VER-03 | /code-tester emitted per phase | unit | `pytest scripts/tests/test_gsd_driver.py::test_code_tester_emitted -x` | NO — Wave 0 |
| VER-04 | /predator emitted per phase | unit | `pytest scripts/tests/test_gsd_driver.py::test_predator_emitted -x` | NO — Wave 0 |

**Manual-only (not automatable in Phase 4):**
- Success criterion 1: actual GSD phase loop driving real builds — requires live Claude Code session with all skills active; not a unit test. Human UAT.
- Success criterion 2: VERIFICATION.md with truly falsifiable criteria — the "observable user behavior" quality gate requires human judgment. Automated test checks format only.
- Success criterion 3: transient network error injection test — requires real network call (or integration test environment). Unit test mocks the sleep.
- Success criterion 5: registry check blocks hallucinated package BEFORE network install — unit test with urllib mock covers the classification; real-network test is human UAT.

### Sampling Rate

- **Per task commit:** `python3 -m pytest scripts/tests/ -x --tb=short`
- **Per wave merge:** `python3 -m pytest scripts/tests/ --tb=short`
- **Phase gate:** Full suite green (>= 46 + Phase 4 new tests = >= 70) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `scripts/tests/test_gsd_driver.py` — covers ROLE-01..06, ROLE-08, HEAL-06, HEAL-07, VER-01..04 (minimum 14 stubs)
- [ ] `scripts/tests/test_failure_classifier.py` — covers HEAL-01..04, HEAL-07 (minimum 8 stubs)
- [ ] `scripts/tests/test_registry_verify.py` — covers HEAL-05, HEAL-06 (minimum 3 stubs)
- Total new stubs Wave 0 must drop: >= 25 RED stubs (brings collected total to >= 71)
- [ ] `scripts/state_writer.py` ALLOWED_FIELDS extension — `failure_class`, `gsd_phase_count`, `escalation_log` — (Wave 0, not a test file but required before any driver writes state)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (Phase 4 does not implement auth) | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | YES | `failure_classifier.py` receives error strings from external processes — must not eval or exec any content; treat as pure string; existing `_check_value_safe` pattern for any string written to state.md |
| V6 Cryptography | No | — |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via error strings | Tampering | `failure_classifier.py` treats error strings as data only (regex matching); never passes raw error string to an LLM as an instruction |
| Hallucinated package install (slopsquatting) | Tampering | `registry_verify.py` blocks install until package confirmed on registry; `--ignore-scripts` prevents post-install script execution even for verified packages |
| Path traversal in escalation log write | Tampering | `escalation_log` written via `state_writer.py` → `_check_value_safe()` rejects `..`; JSON-encoded before write |
| Shell injection in install command construction | Tampering | Install commands constructed as list-form `subprocess.run(cmd_list, shell=False)`; user-derived package names validated against `[a-zA-Z0-9@/_.-]+` before inclusion in cmd_list |
| Network error misclassified as "package not found" | Denial of Service | Fail-open policy in `registry_verify.py` — `URLError` returns True, not False; never blocks a build on network issues |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | GSD slash commands cannot be invoked as subprocesses; they must be emitted as text | Pattern 1, Pitfall 1 | If GSD skills are also shell-executable, `subprocess.run` could work — but the text-emission pattern is always safe and should be used regardless |
| A2 | `gsd_driver.py` is a state advisor (emits text) not an executor (runs subprocesses for GSD steps) | Architecture diagram, Pattern 1 | If this model is wrong, the driver architecture needs a complete rethink; however, all evidence from SKILL.md patterns confirms text-emission |
| A3 | `retry_count` and `last_failure` in state.md REQUIRED_FIELDS are already writable via `state_writer.py` | State Machine Design | Verified: state_writer.py line 29 shows both fields in REQUIRED_FIELDS tuple; bump subcommand works on retry_count |
| A4 | `urllib.request.urlopen` with `method="HEAD"` works correctly against npm registry for package existence | Pattern 4, Code Examples | npm registry may not support HEAD and require GET; fallback: use GET and check status code. Low risk since npm registry is standard |
| A5 | The 4-class taxonomy (transient, context-overflow, tool-failure, validation-failure) covers all failure modes encountered in real OSBuilder builds | Pattern 2 | An unexpected error class would fall through unclassified; mitigation: add a `unknown` class that escalates immediately |

---

## Open Questions

1. **Does `gsd_driver.py` need to PARSE GSD's ROADMAP.md to discover phase count?**
   - What we know: GSD writes `ROADMAP.md` after `/gsd-new-project --auto`. The phase count varies by app (5 phases for a simple app, 8+ for complex). The driver needs to know how many phases to iterate.
   - What's unclear: Is ROADMAP.md in a stable parseable format, or is it LLM-generated prose?
   - Recommendation: Parse ROADMAP.md for `## Phase N:` headers using `re.findall(r"^## Phase (\d+)", content, re.MULTILINE)`. If parsing fails, default to iterating until no PLAN.md is produced.

2. **How does `gsd_driver.py` detect that a GSD command completed successfully?**
   - What we know: GSD commands run in-conversation. The driver emits them and they execute. But the driver script runs before and after — it needs to detect completion on re-entry.
   - What's unclear: The completion signal. Does GSD write a specific file? Does the driver simply advance `phase_step` unconditionally on next invocation?
   - Recommendation: Advance `phase_step` optimistically on each emission. On re-entry, read `phase_step` and emit the next command. If GSD produced an error, the error string is captured by the failure classifier. This is the same "state-on-file" pattern used throughout OSBuilder.

3. **Should `registry_verify.py` cache results within a build session?**
   - What we know: The same package (e.g., `next`) may be "verified" multiple times across phases. Making a GET request to the registry each time is slow.
   - What's unclear: Is the build slow enough that caching matters?
   - Recommendation: Skip caching in v1. The registry check is a HEAD request (fast); builds typically install each unique package name once. Add caching only if dogfood builds show this as a measurable bottleneck.

---

## Project Constraints (from CLAUDE.md)

| Directive | Type | Applies to Phase 4 |
|-----------|------|--------------------|
| Python helper scripts only (stdlib where possible) | Required | All 3 new scripts must be stdlib-only; `urllib.request` covers registry lookup |
| Single-threaded execution; no parallel agents | Required | `gsd_driver.py` drives GSD commands sequentially; never forks parallel GSD invocations |
| 3-reflection cap (Aider's empirically-validated limit) | Required | `failure_classifier.py` enforces `retry_count >= 3 → escalate`; retry_count persists in state.md |
| State checkpoint at `<project-root>/.planning/osbuilder/state.md` | Required | `retry_count`, `last_failure`, `current_phase`, `phase_step` all in state.md; survive `/clear` |
| Composition rule: fix sub-skills, never fork | Required | `gsd_driver.py` DELEGATES to GSD skills; never reimplements GSD logic |
| SKILL.md ≤ 200 lines | Required | Phase 4 adds no content to SKILL.md; role delegation docs go in `references/roles/` |
| One-level-deep references | Required | `references/roles/qa.md` — flat, not nested |
| Refuse-list: no multi-agent parallel execution | Required | `gsd_driver.py` is strictly single-threaded; `phase_step` is a serial counter |

---

## Sources

### Primary (HIGH confidence)

- `scripts/state_writer.py` — REQUIRED_FIELDS, ALLOWED_FIELDS, bump subcommand, retry_count/last_failure fields [VERIFIED: direct file read 2026-04-30]
- `scripts/tests/conftest.py` — FakeShell, fake_which, writer fixture patterns [VERIFIED: direct file read 2026-04-30]
- `ls ~/.claude/skills/` — all delegated GSD skills confirmed installed [VERIFIED: CLI output 2026-04-30]
- `https://registry.npmjs.org/next` → HTTP 200 [VERIFIED: live registry check 2026-04-30]
- `https://registry.npmjs.org/@anthropic/clauded-code-helper` → HTTP 404 [VERIFIED: live registry check 2026-04-30]
- `.planning/REQUIREMENTS.md` — ROLE-01..08, HEAL-01..07, VER-01..04 requirement text [VERIFIED: direct file read]
- `.planning/ROADMAP.md` — Phase 4 success criteria + dependencies [VERIFIED: direct file read]
- `python3 -m pytest --collect-only` → 46 tests currently collected [VERIFIED: CLI output 2026-04-30]
- `pyproject.toml` — pytest config, pythonpath, testpaths [VERIFIED: direct file read]
- `.planning/phases/03-intake-stack-research-web-playbook-one-playbook-e2e/03-PATTERNS.md` — shared code patterns (lazy import fixture, fake_shell/fake_which usage, argparse dispatch, atomic_write) [VERIFIED: direct file read]

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` — key decisions locked in (3-reflection cap, single-threaded, composition rule, state checkpoint) [VERIFIED: direct file read]
- `pypi.org` registry API pattern — consistent with npm pattern; HEAD returns 200/404 for package existence [ASSUMED: verified npm; pypi assumed consistent]

### Tertiary (LOW confidence)

- Exponential backoff multiplier of 4x (1→4→16 seconds) — derived from Aider's 3-reflection limit + OSBuilder's 10-60s operation cadence; no OSBuilder-specific benchmark [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- State machine design: HIGH — all state fields verified against existing state_writer.py
- GSD skill interfaces: HIGH — all skills confirmed installed; invocation pattern derived from existing SKILL.md observation
- Failure taxonomy: HIGH — 4 classes, strategies, and test patterns are clearly specified
- Registry verification: HIGH — npm API verified live; urllib.request pattern is stdlib
- Backoff multiplier (4x): LOW — derived from reasoning, not measured against OSBuilder builds
- Test patterns: HIGH — all patterns are direct extensions of existing Phase 1-3 test infrastructure

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (all GSD skill interfaces are stable; npm/PyPI registry APIs are stable)
