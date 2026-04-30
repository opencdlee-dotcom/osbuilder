# Phase 2: Pre-flight installer (cross-platform) — Research

**Researched:** 2026-04-29
**Domain:** Cross-platform Python preflight checker — detect + auto-install Node 20+, Python 3.13+, git, gh, Docker on macOS / Ubuntu+Fedora / Windows 11, with rollback, dry-run, and uninstall paths.
**Confidence:** HIGH for OSBuilder-internal carry-forward decisions (Phase 1 patterns); HIGH for verified package IDs (winget/brew/apt/dnf cross-checked against official registries Apr 2026); MEDIUM for the operational UX of admin-elevation flows and version-manager routing (category-pattern reasoning + verified general guidance, but no single canonical "right answer" — flagged for plan-time confirmation).

---

## Summary

Phase 2 builds **`scripts/preflight_check.py`** — a Python 3.13 stdlib-only preflight checker — plus three per-OS reference matrices (`references/preflight/{macos,linux,windows}.md`) and a sibling **`scripts/uninstall.py`** to fulfill PRE-06. The module exposes a small public API (`detect()`, `plan()`, `apply()`, `rollback()`, `uninstall()`) that can be driven from a future role-narration layer without changes.

The phase's central architectural decision is **detection-first**: probe for existing version managers (nvm, pyenv, mise, asdf, volta, fnm) and tool versions before proposing an install. If a manager is present, route through it (or — more conservatively — refuse to clobber it and ask the user to install the tool through their existing manager). Hand-rolling a Node installer when nvm is present is the documented #1 way preflight breaks user trust permanently (Pitfall 13).

The phase's central operational decision is **JSON install-log per-tool, all-or-nothing batch rollback**: every action OSBuilder takes (`brew install X`, `winget install X`, etc.) records `{tool, action, package_id, manager, started_at, succeeded_at, uninstall_command}` to `~/.osbuilder/install-log.json`. On any single failure inside a batch, OSBuilder iterates the log in reverse and runs each `uninstall_command`. This is simpler than partial-batch rollback, matches user mental model ("you said you'd undo it; undo it"), and aligns with how openSUSE's `transactional-update` thinks about atomicity at a higher level [CITED: github.com/openSUSE/transactional-update].

**Primary recommendation:** Two waves, mirroring Phase 1. **Wave 0** lands lazy-import-via-fixture test stubs (`test_preflight.py`, `test_uninstall.py`) covering ≥ 12 RED tests for PRE-01..07, plus a `FakeShell` harness in `conftest.py` that mocks `subprocess.run` so install logic can be exercised without ever touching the real system. **Wave 1** lands `preflight_check.py` + `uninstall.py` + the three `references/preflight/*.md` matrices in parallel (disjoint files). Using the same Wave 0 → Wave 1 pattern that Phase 1 validated keeps the cognitive load low and reuses the conftest fixture vocabulary already in the repo.

---

## User Constraints (from Phase 1 STATE.md + project-level instructions; CONTEXT.md not yet authored for Phase 2)

> Phase 2 has no `02-CONTEXT.md` yet (no `/gsd-discuss-phase` was run). The constraints below are extracted from STATE.md "Key Decisions Locked In", PROJECT.md / SKILL.md hard rules, and CLAUDE.md. The planner MUST honor these.

### Locked Decisions (carry forward from Phase 1)

- **Helper-script language:** Python 3.13 stdlib-only. No `requests`, no third-party HTTP, no `subprocess32`. Bash is allowed only for *trivial* glue and only POSIX `sh` (no `[[ ]]`, no arrays).
- **Atomic write pattern:** `os.replace()` via `atomic_write(path, content)` — pattern established in `scripts/state_writer.py:100-112`. Every JSON-or-MD write that must survive a crash uses this helper (or an inlined equivalent).
- **Test pattern:** Lazy-import-via-fixture (`@pytest.fixture def pf(): try: return importlib.import_module("preflight_check"); except ImportError: pytest.skip(...)`). NEVER `pytest.importorskip` at module top — breaks Nyquist `>= N tests collected` gates.
- **Line-ending discipline:** `*.sh text eol=lf` glob form already enforced by `.gitattributes`. Don't add new bash files; if you must, follow the glob.
- **4-dir layout:** `references/`, `scripts/`, `assets/`, `examples/` — no nesting deeper than one level. Phase 2 stays inside `scripts/` and `references/preflight/`.
- **Strict single-threaded execution:** Detection probes MUST be sequential, not threaded. (Justification below in `Detection Speed Budget`.)
- **3-reflection cap on retries:** A failed install retries at most 3 times within the same batch before triggering rollback. After rollback, the user gets a structured handoff (Phase 4's failure_classifier surface — Phase 2 only emits the failure; classification is Phase 4).
- **Composition rule:** Phase 2 does NOT implement `friendly_error.py` (Phase 5), `registry_verify.py` (Phase 4), or `failure_classifier.py` (Phase 4). When preflight fails, it returns a structured error dict — Phase 5 wraps it later.
- **Single-confirmation prompt:** PRE-02 — *one* yes/no for the whole batch after the dry-run preview. NOT one prompt per tool.
- **`--no-docker` mode:** PRE-07 — preflight skips Docker detection AND install, AND records the choice so downstream phases (scaffolder dispatch in Phase 3) honor it.

### Claude's Discretion (research → recommend; planner picks unless flagged for user)

- Install-log filesystem location (`~/.osbuilder/install-log.json` vs `<project-root>/.planning/osbuilder/install-log.json`) — see Open Question 10. **Recommendation: `~/.osbuilder/install-log.json`** (rationale below).
- Linux distro coverage scope for v1 — see Open Question 5. **Recommendation: apt + dnf only**; zypper/pacman/apk become a "send a PR" surface area in v2.
- Exact wording of dry-run preview and confirmation prompt (constrained by PRE-02, PRE-05 falsifiability but not by exact UX strings) — Phase 5 polishes; Phase 2 ships a working v1 that the friendly_error layer can later wrap.
- `preflight_check.py` public-API shape — recommendation in *Code Examples* below.
- Whether to merge `uninstall.py` into `preflight_check.py` or keep separate — see Open Question (file structure). **Recommendation: separate file** — clean responsibility boundary, mirrors `state_writer.py`'s subcommand pattern, easier to test.

### Deferred Ideas (OUT OF SCOPE — DO NOT ADD)

- **Slopsquatting / `registry_verify.py`** → Phase 4
- **Friendly error wrapping** (`ENOENT` → "the file isn't there") → Phase 5
- **Failure classifier** (transient / context / tool / validation) → Phase 4
- **gh auth flow polish** (auth-state-drift detection) → Phase 6 (Ship phase)
- **Real-machine CI matrix** (V2-XPL-01) → v2 milestone
- **Tutor-mode narration** ("PM is checking your machine...") → Phase 5
- **Self-healing retry beyond simple backoff** → Phase 4
- **WSL detection / WSL-aware install path** → out of scope for v1; document in `references/preflight/windows.md` as "if WSL is detected, defer to Linux path" but only as a flag, not a code path
- **Snap / Chocolatey-as-primary** → already on the refuse-list (PROJECT.md)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRE-01 | Detect missing prerequisites (Node 20+, Python 3.13+, git, `gh`, Docker — Docker only when needed) on first run | `Detection Strategy` section + `Detection Commands per Platform` table |
| PRE-02 | Single-confirmation auto-install per missing tool ("To build this app I need a tool called Node.js…") | `Single-Confirmation UX` section in *Pitfalls / Known Pitfalls*; `plan()` API in *Code Examples* |
| PRE-03 | Cross-platform: macOS Homebrew, Linux apt/dnf with auto-detection, Windows winget→scoop→choco | `Install Commands per Platform` table + `Linux distro auto-detect` algorithm; STACK.md verified package IDs |
| PRE-04 | Transactional install — failed installs roll back, never leave system half-broken | `Install-Log Schema + Rollback Algorithm` section |
| PRE-05 | Dry-run preview ("Here's what I'll install: …") before any state change | `plan()` returns the preview struct; `apply()` is the only function that mutates the system |
| PRE-06 | Uninstall path that cleanly removes anything OSBuilder added (and only that) | `Uninstall Strategy` section + `Uninstall Commands per Platform` table; `~/.osbuilder/install-log.json` is the source of truth |
| PRE-07 | `--no-docker` mode lets users build SQLite-only single-user apps | `--no-docker Flow` section + state.md interaction |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Detection (which tools are missing) | OS shell (`which`/`where`/`Get-Command`) via Python `subprocess.run` | Version-manager probes (`~/.nvm`, `~/.pyenv`, etc. existence checks) | OS already has the answer — wrap, don't re-implement PATH parsing |
| Decision (what to install, via what manager) | Python decision tree in `preflight_check.py:plan()` | `references/preflight/{os}.md` reference matrix | Decision logic = code; explanation/rationale per platform = reference doc loaded on demand |
| Action (running installs) | OS package managers (`brew`, `apt-get`, `dnf`, `winget`, `scoop`) | Python `subprocess.run` orchestrator | Never re-implement an installer; always delegate to the OS-blessed tool |
| State (install log) | Local JSON file at `~/.osbuilder/install-log.json` | OS keychain — NOT used (no secrets in preflight) | One-user tool; survives across runs; portable; no network |
| Rollback | Iterate install log in reverse, call recorded `uninstall_command` | Python `subprocess.run` | All-or-nothing semantics match user expectation; per-tool partial rollback is harder to reason about and less safe |
| User confirmation | TTY prompt (`input()` via stdlib) | (Phase 5 friendly-error wrap eventually) | Phase 2 ships a plain-but-correct prompt; Phase 5 polishes |
| Privilege escalation | OS-native (`sudo` invocation on Linux, UAC elevation on Windows) | Pre-warn user in dry-run preview | Detect-and-narrate is the contract; never `sudo` silently |

---

## Standard Stack

### Core (carry-forward from Phase 1)

| Library / Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| Python stdlib `subprocess` | 3.13 | Run `which`, `brew install`, `winget install`, etc. | Cross-platform, no third-party deps, already used in `bootstrap.sh` and `state_writer.py` |
| Python stdlib `shutil.which` | 3.13 | Cross-platform `which`/`where` replacement | Native Windows + POSIX support; preferred over invoking `which` as a subprocess [CITED: docs.python.org/3/library/shutil.html] |
| Python stdlib `platform` | 3.13 | Detect macOS vs Linux vs Windows | `platform.system()` → `"Darwin" / "Linux" / "Windows"` — used in `bootstrap.sh:15` for OS detection already |
| Python stdlib `platform.freedesktop_os_release` | 3.10+ | Linux distro detection (apt vs dnf) | Built into stdlib in 3.10+; replaces hand-parsing `/etc/os-release` [CITED: docs.python.org/3/library/platform.html#platform.freedesktop_os_release] |
| Python stdlib `json` | 3.13 | Read/write install-log + state interop | Already used in `state_writer.py` |
| Python stdlib `pathlib` | 3.13 | Path manipulation cross-platform | Carry-forward from Phase 1 |
| Python stdlib `argparse` | 3.13 | CLI subcommand pattern (mirror `state_writer.py`) | Carry-forward from Phase 1 |
| pytest | 8.x (already in repo) | Test runner | Already configured in `pyproject.toml`; same fixture style as Phase 1 |
| `pytest.MonkeyPatch` | bundled with pytest | Replace `subprocess.run` in tests so no real installs run | Standard pattern; documented at [docs.pytest.org/en/stable/how-to/monkeypatch.html] |

**Version verification (executed Apr 2026):**

`platform.freedesktop_os_release` first appeared in Python 3.10 — all currently-supported Python versions include it [CITED: docs.python.org/3/library/platform.html#platform.freedesktop_os_release]. `shutil.which` has been in stdlib since Python 3.3 [CITED: docs.python.org/3/library/shutil.html#shutil.which]. No version verification needed for stdlib modules.

### Per-OS Package Managers (verified against official sources Apr 2026)

| OS | Manager | Verified | Notes |
|---|---|---|---|
| macOS | Homebrew | [VERIFIED: brew.sh] | Detection: `command -v brew` |
| macOS (Docker only) | Homebrew Cask `orbstack` | [VERIFIED: docs.orbstack.dev/install] | `brew install --cask orbstack` (note: STACK.md said `--cask`; current docs say plain `brew install orbstack` — the `--cask` form still works but unnecessary; recommend the simpler form) |
| Linux Debian/Ubuntu | apt-get | [VERIFIED: in /etc/os-release ID=ubuntu or ID_LIKE=debian] | Detection: `command -v apt-get` AND `'debian' in ID_LIKE` |
| Linux Fedora/RHEL | dnf | [VERIFIED: in /etc/os-release ID=fedora or ID_LIKE includes 'fedora' or 'rhel'] | Detection: `command -v dnf` AND `'fedora' in ID_LIKE` |
| Windows 11 | winget | [VERIFIED: built into Win10 1809+ / 11; no separate install needed] [CITED: learn.microsoft.com/en-us/windows/package-manager/winget/] | Detection: `Get-Command winget -ErrorAction SilentlyContinue` |
| Windows 11 fallback | scoop | [VERIFIED: scoop.sh] | Only if winget fails or returns "no applicable installer" |
| Windows 11 last resort | choco | [VERIFIED: chocolatey.org] | Only when both winget and scoop have no package; requires admin elevation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff | Recommendation |
|---|---|---|---|
| stdlib `subprocess.run` | `sh` library, `plumbum`, `invoke` | Adds dep, breaks "stdlib-only" constraint | KEEP stdlib |
| Hand-parse `/etc/os-release` | `distro` PyPI package | Adds dep, but distro lib has more edge-case coverage | KEEP `platform.freedesktop_os_release` (3.10+ stdlib); fall back to manual parse only if `freedesktop_os_release` raises |
| Single big `preflight_check.py` | Split into `detect.py`, `install.py`, `rollback.py` modules | More files = more import boilerplate; Phase 1 chose single-file for `state_writer.py` | KEEP single file; the split happens at the CLASS or FUNCTION level inside it |
| Merge `uninstall.py` into `preflight_check.py` | One file with `uninstall` subcommand | Cleaner CLI surface | SEPARATE files — `state_writer.py` is the precedent for "one CLI per script", and PRE-06's "uninstall path" reads more naturally as `python uninstall.py` than as `python preflight_check.py uninstall` |
| TTY prompt via `input()` | `click.confirm()`, `questionary`, etc. | Adds dep | KEEP `input()`; Phase 5 wraps for tutor mode |

**Installation:** No new dependencies. Phase 2 is stdlib-only.

---

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  /osbuilder invocation (or scripts/preflight_check.py CLI)      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
              ┌──────────────────┐
              │  detect()        │  ← reads NOTHING from filesystem
              │   → status dict  │     except `~/.osbuilder/install-log.json`
              │                  │     (to know what we previously installed)
              └────────┬─────────┘
                       │
        ┌──────────────┼─────────────────┐
        ▼              ▼                 ▼
    OS detect    Tool detect       VM detect
   platform.     shutil.which     ~/.nvm exists?
   system()     for each tool   ~/.pyenv exists?
   /etc/os-      AND version     ~/.mise exists?
   release      probe (--version) ~/.asdf exists?
                                 ~/.volta exists?
                                 ~/.fnm exists?
        │              │                 │
        └──────────────┼─────────────────┘
                       ▼
              ┌──────────────────┐
              │  plan()          │  ← pure function: status → install plan
              │  no side-effects │     consults references/preflight/{os}.md
              │                  │     decision tree (encoded in code)
              │   → install plan │
              │                  │
              │   if VM present  │
              │   AND tool       │
              │   missing →      │
              │   defer-to-VM    │
              │   recommendation │
              │   (don't auto-   │
              │   install)       │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  print preview   │ PRE-05: dry-run BEFORE any state change
              │  (PRE-05)        │
              │                  │
              │  ?? --dry-run    │ flag → exit 0 here
              └────────┬─────────┘
                       │ user types "y"
                       ▼
              ┌──────────────────┐
              │  apply()         │ PRE-04: transactional
              │  for each tool:  │
              │   1. record      │ ← write to install-log BEFORE install
              │      "started"   │   (so even SIGKILL leaves a trail)
              │   2. subprocess  │
              │      .run(install)│
              │   3. on success: │
              │      record      │ ← os.replace atomic update
              │      "succeeded" │
              │   4. on failure: │
              │      → rollback()│
              │                  │
              │  ?? exception    │
              │  during install  │ → rollback() automatically
              │  (Ctrl-C, SIGINT)│
              └────────┬─────────┘
                       │
                       ▼
                  ┌──────────┐
                  │ done     │
                  └──────────┘
                       │
                       │ separately, on user request:
                       ▼
              ┌──────────────────┐
              │  uninstall()     │ PRE-06
              │  read log,       │
              │  iterate REVERSE,│
              │  call each       │
              │  recorded        │
              │  uninstall_cmd   │
              └──────────────────┘
```

### Component Responsibilities

| Component | File | Role |
|---|---|---|
| Public API: `detect`, `plan`, `apply`, `rollback`, `uninstall` | `scripts/preflight_check.py` | Single Python module, callable as CLI or imported as library |
| CLI entry: `python scripts/preflight_check.py {check\|install\|preview\|rollback}` | `scripts/preflight_check.py:main()` | argparse subcommands, mirroring `state_writer.py` |
| CLI entry: `python scripts/uninstall.py` | `scripts/uninstall.py` | Thin wrapper around `preflight_check.uninstall()` — kept separate so `/osbuilder uninstall` reads naturally |
| Decision tree explanations | `references/preflight/macos.md` | Per-OS install matrix + decision tree + edge cases — loaded on-demand by Architect role at planning time, not at run time |
| Decision tree explanations | `references/preflight/linux.md` | apt + dnf matrices + ID_LIKE detection rationale |
| Decision tree explanations | `references/preflight/windows.md` | winget→scoop→choco fallback chain + PATH-refresh gotcha + admin-elevation UX |
| Test harness | `scripts/tests/conftest.py` | Adds `FakeShell` fixture (mocks `subprocess.run`) and `tmp_install_log` fixture (isolates `~/.osbuilder/`) |
| RED stubs (Wave 0) | `scripts/tests/test_preflight.py` | ≥ 10 tests covering PRE-01..05 and PRE-07 |
| RED stubs (Wave 0) | `scripts/tests/test_uninstall.py` | ≥ 2 tests covering PRE-06 |

### Recommended Project Structure (delta from existing repo)

```
scripts/
├── preflight_check.py          # NEW (Wave 1) — Python 3.13 stdlib only
├── uninstall.py                # NEW (Wave 1) — thin wrapper around preflight_check.uninstall()
└── tests/
    ├── conftest.py             # EDIT (Wave 0) — add FakeShell + tmp_install_log fixtures
    ├── test_preflight.py       # NEW (Wave 0) — RED stubs for PRE-01..05, PRE-07
    └── test_uninstall.py       # NEW (Wave 0) — RED stubs for PRE-06
references/preflight/
├── macos.md                    # NEW (Wave 1)
├── linux.md                    # NEW (Wave 1)
└── windows.md                  # NEW (Wave 1)
```

No edits required to: `SKILL.md`, `state_writer.py`, `bootstrap.sh`, `bootstrap.ps1`, `install.sh`, `pyproject.toml`, `.gitattributes`. Phase 2 is purely additive on top of Phase 1.

### Pattern 1: Detection-First (do not install if the user has a version manager)

**What:** Before proposing any install, probe for: nvm, pyenv, mise, asdf, volta, fnm. If found, ROUTE through them or REFUSE to clobber.

**When to use:** Always, on every Node and Python detection.

**Why:** Pitfall 13 — auto-installing Node when nvm is present produces *two* Nodes; one of them shadows the other depending on PATH ordering. User wakes up to a broken `git` (because some module needed Node 18 from nvm but PATH now points at brew's Node 24). One bad preflight kills trust permanently.

**Decision tree (codified in `plan()`):**

```python
# Pseudocode — full version in Code Examples below
node_detected = shutil.which("node") is not None
node_version_ok = node_detected and _probe_node_major() >= 20

vm_detected = (
    Path.home().joinpath(".nvm").exists()
    or shutil.which("nvm") is not None
    or shutil.which("fnm") is not None
    or Path.home().joinpath(".volta").exists()
    or shutil.which("mise") is not None
    or shutil.which("asdf") is not None
)

if node_version_ok:
    return Plan(action="none", reason="node already present and version OK")
elif vm_detected and node_detected:
    # User has a VM AND has Node, but version is below 20
    return Plan(
        action="defer-to-vm",
        message=f"You have {detected_vm} managing your Node. Please run "
                f"`{vm_install_cmd}` to install Node 20+. I won't touch this.",
        block=True,
    )
elif vm_detected and not node_detected:
    # Edge case — VM installed but no Node yet; user is in a half-set-up state
    return Plan(
        action="defer-to-vm",
        message=f"You have {detected_vm} but no Node installed. "
                f"Please run `{vm_install_cmd}`. I won't touch this.",
        block=True,
    )
else:
    # No VM, no Node → safe to install via system manager
    return Plan(action="install", manager=system_manager, ...)
```

**Example:**

```python
# Source: distilled from STACK.md preflight matrix + Pitfall 13 mitigation
# Verification: shutil.which path-checks confirmed in Python 3.13 stdlib docs

def detect_version_managers() -> dict[str, bool]:
    """Returns {'nvm': True, 'pyenv': False, ...} — never installs anything."""
    home = Path.home()
    return {
        "nvm":    (home / ".nvm").exists() or shutil.which("nvm") is not None,
        "pyenv":  (home / ".pyenv").exists() or shutil.which("pyenv") is not None,
        "mise":   shutil.which("mise") is not None,
        "asdf":   (home / ".asdf").exists() or shutil.which("asdf") is not None,
        "volta":  (home / ".volta").exists() or shutil.which("volta") is not None,
        "fnm":    shutil.which("fnm") is not None,
    }
```

### Pattern 2: Detect-Before-Install ordering, with PATH-aware re-probe

**What:** On Windows specifically, after `winget install`, the current shell's PATH is stale. Probing `shutil.which("python")` immediately after install will return None even though the install succeeded.

**When to use:** Every Windows install. (macOS Homebrew and Linux apt/dnf don't have this problem because they install to already-on-PATH locations.)

**Why:** Documented winget bug [CITED: github.com/microsoft/winget-cli/issues/3359, github.com/microsoft/winget-cli/issues/531]. `bootstrap.ps1` already addresses this for Python via the "two-mode" pattern: capture pre-install state, exit gracefully with "reopen shell" message if just-installed.

**How:**
- After a winget install, do NOT re-probe with `shutil.which`. Instead, mark the install as "succeeded" based on `subprocess.run().returncode == 0`, and skip the post-install version probe for THIS run.
- Append a "reopen shell" line to the post-install summary on Windows.
- Document this in `references/preflight/windows.md` so the planner doesn't try to "smarten" the post-install probe.

**Example:**

```python
# Source: bootstrap.ps1 lines 39-44 (existing two-mode pattern); winget issue #531
# Verification: VERIFIED behavior in Phase 1's bootstrap.ps1 reopens-shell flow

def _post_install_verify(tool: str, *, just_installed: bool, on_windows: bool) -> bool:
    """On Windows, just-installed tools are not on PATH yet — trust returncode.
    Elsewhere, re-probe via shutil.which to confirm install succeeded."""
    if on_windows and just_installed:
        return True  # PATH stale; trust subprocess returncode
    return shutil.which(tool) is not None
```

### Pattern 3: Install-Log-Per-Action (atomic JSON append-then-replace)

**What:** Every install action records `{tool, action, package_id, manager, started_at, succeeded_at, uninstall_command}` to `~/.osbuilder/install-log.json` BEFORE the install begins, then UPDATES the entry to "succeeded" after.

**When to use:** Every `apply()` invocation.

**Why:** PRE-04 transactional + PRE-06 uninstall both depend on this. If OSBuilder is SIGKILLed mid-install, the log shows "started but not succeeded" — the uninstall path can still recover (the package may be partially installed, but the log records what we tried).

**Schema (verified against openSUSE transactional-update model + dpkg/rpm postinst patterns):**

```json
{
  "schema_version": "1",
  "actions": [
    {
      "tool": "node",
      "package_id": "OpenJS.NodeJS.LTS",
      "manager": "winget",
      "platform": "windows-11",
      "started_at": "2026-04-29T18:34:11Z",
      "succeeded_at": "2026-04-29T18:34:47Z",
      "install_command": "winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements",
      "uninstall_command": "winget uninstall -e --id OpenJS.NodeJS.LTS",
      "status": "succeeded"
    },
    {
      "tool": "gh",
      "package_id": "GitHub.cli",
      "manager": "winget",
      "started_at": "2026-04-29T18:34:48Z",
      "succeeded_at": null,
      "install_command": "winget install -e --id GitHub.cli ...",
      "uninstall_command": "winget uninstall -e --id GitHub.cli",
      "status": "started"
    }
  ]
}
```

`status` ∈ `{"started", "succeeded", "failed", "rolled-back"}`.

The file is updated via the SAME `atomic_write` helper Phase 1 uses for `state.md` (`os.replace` after writing to a sibling tmp file).

### Anti-Patterns to Avoid

- **Threading detection probes for speed.** `subprocess.run` for `which` + `--version` on 5 tools is < 1 second sequentially. Threading adds Windows-PATH-stale race conditions and serializes nothing meaningful. **Sequential only.** (Pitfall 14 cross-platform path assumptions get worse with concurrency.)
- **Hand-rolling a Node installer.** Always delegate to brew/apt/dnf/winget/scoop. (Pitfall 13.)
- **Touching macOS system Python (`/usr/bin/python3`).** Apple ships it, Apple breaks it. Always install Python 3.13 to a separate path via brew. STACK.md has this as an explicit anti-recommendation.
- **Auto-`sudo` without telling the user.** Linux installs need root. Show the exact command in the dry-run preview, then let `sudo` itself prompt for the password (don't try to capture it via `getpass`).
- **Embedding `sudo` in a Python `subprocess.run` call without `stdin=sys.stdin`.** Without TTY passthrough, sudo silently waits forever. Use `subprocess.run([...], check=False)` and let sudo own the TTY.
- **Re-probing PATH after a Windows winget install.** PATH is stale; trust returncode. (See Pattern 2.)
- **Ignoring the install log on rollback.** Rollback MUST iterate the log in reverse and call each recorded `uninstall_command`. Do NOT recompute uninstall commands from scratch — the recorded one is what we know works.
- **Mixing `--no-docker` and Docker-detection.** If `--no-docker` is passed, Docker is BOTH undetected AND uninstalled (un-detection-targeted). Don't print "Docker is missing — install?" for a user who explicitly opted out.
- **Snap on Linux.** Already on the refuse-list. Confinement breaks `gh auth login` in surprising ways (STACK.md anti-recommendation).
- **Chocolatey-as-primary on Windows.** Already on the refuse-list. winget is built-in; choco requires admin + separate install.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Cross-platform `which` | Wrap `subprocess.run("which" / "where")` | `shutil.which()` | stdlib, handles `.exe` extension on Windows, returns `None` cleanly |
| Linux distro detection | Hand-parse `/etc/os-release` | `platform.freedesktop_os_release()` | stdlib in 3.10+; handles ID_LIKE field, escape sequences, and missing-file cases |
| OS detection | Parse `uname -s` output | `platform.system()` | stdlib, returns "Darwin" / "Linux" / "Windows" canonical strings |
| Atomic file writes | `path.write_text(...)` | `atomic_write()` helper from Phase 1's `state_writer.py:100-112` (extract or duplicate) | `os.replace` is atomic on POSIX AND Windows; Phase 1 already proved this pattern |
| TTY prompt | `sys.stdin.readline()` parse | `input()` | stdlib, handles SIGINT cleanly (raises KeyboardInterrupt — uncaught propagates to main()) |
| ISO-8601 timestamp | `datetime.now().isoformat()` (timezone-naive — wrong) | Phase 1's `_now_iso()` helper from `state_writer.py:73-74` (UTC + Z suffix) | Already canonical in repo |
| Subprocess mocking in tests | Manually wrap `subprocess.run` | `monkeypatch.setattr("subprocess.run", FakeShell())` in conftest | pytest builtin; documented at [docs.pytest.org/en/stable/how-to/monkeypatch.html] |
| Node version detection | Hand-parse `node --version` | `int(_probe("node", "--version").lstrip("v").split(".")[0])` | One-liner; works on Node ≥ 0.10 |
| Python version detection | Hand-parse `python3 --version` | `sys.version_info` for the running interpreter; `subprocess` for the SYSTEM interpreter | We're inside Python — for OUR version use `sys`; for the SYSTEM Python (which may differ) use subprocess |

**Key insight:** The cross-platform problem is *almost entirely* solved by Python 3.13 stdlib. Every Phase 2 file should import from `subprocess`, `shutil`, `platform`, `pathlib`, `json`, `os`, `argparse`, `datetime`, `sys` — and nothing else.

---

## Runtime State Inventory

> Phase 2 is greenfield (no rename / refactor / migration). However, since OSBuilder Phase 2 *creates* runtime state on the user's machine for the first time, this inventory documents what state Phase 2 introduces, where it lives, and what cleans it up.

| Category | Items Created by Phase 2 | Action Required |
|---|---|---|
| Stored data | `~/.osbuilder/install-log.json` — JSON record of every install action | Cleaned up by `uninstall.py` (PRE-06); consider removing the directory if log becomes empty after uninstall |
| Live service config | None — preflight installs CLIs only, no daemons | None |
| OS-registered state | Whatever `brew`/`apt`/`dnf`/`winget`/`scoop` registers when installing the actual tools (Node binary on PATH, etc.) | All managed by the OS package manager; rollback delegates the uninstall back to the same manager |
| Secrets/env vars | None — preflight does NOT touch `.env`, `gh auth`, or any credential | None (gh auth flow lives in Phase 6) |
| Build artifacts | None — Phase 2 does not compile anything | None |

**Nothing found in `Live service config`, `Secrets`, `Build artifacts`:** Verified by reading PROJECT.md scope (preflight is install-CLIs-only) and the STACK.md preflight matrix (no daemon installs in v1).

---

## Detection Commands per Platform

Per-tool, per-platform: detection probe + version probe + version-manager (VM) probe.

### macOS

| Tool | Detection probe | Version probe | VM probe (skip install if found) |
|---|---|---|---|
| Node 20+ | `shutil.which("node") is not None` | `node --version` → parse leading `v`, take major | `~/.nvm` exists, `~/.volta` exists, `which mise`, `which asdf`, `which fnm` |
| Python 3.13+ | `shutil.which("python3") is not None` | `python3 --version` → parse `Python X.Y.Z`, require X==3 AND Y>=13 | `~/.pyenv` exists, `which mise`, `which asdf`, `~/.asdf` exists |
| git 2.40+ | `shutil.which("git") is not None` | `git --version` → parse `git version X.Y.Z` | None (no VM ecosystem for git) |
| gh 2.x | `shutil.which("gh") is not None` | `gh --version` → parse `gh version X.Y.Z` | None |
| Docker | `shutil.which("docker") is not None` AND `docker info` returns non-error | `docker --version` | None (Docker is daemon-based, not version-managed) |
| OrbStack (Mac Docker preferred) | `shutil.which("orb") is not None` OR `/Applications/OrbStack.app` exists | `orb --version` | — |

### Linux (apt + dnf only — see Open Question 5 for v2 scope)

Distro detect first:
```python
osr = platform.freedesktop_os_release()  # Python 3.10+
ids = {osr.get("ID", ""), *osr.get("ID_LIKE", "").split()}
manager = "apt-get" if "debian" in ids else "dnf" if ("fedora" in ids or "rhel" in ids) else None
```

Then per-tool (commands match the bootstrap.sh existing pattern):

| Tool | Detection probe | Version probe | VM probe |
|---|---|---|---|
| Node 20+ | `shutil.which("node") is not None` | `node --version` | `~/.nvm` exists, `~/.volta`, `which mise`, `which asdf`, `which fnm` |
| Python 3.13+ | `shutil.which("python3") is not None` AND `shutil.which("python3.13") is not None` (apt frequently ships old python3) | `python3.13 --version` | `~/.pyenv`, `which mise`, `which asdf` |
| git 2.40+ | `shutil.which("git") is not None` | `git --version` | None |
| gh 2.x | `shutil.which("gh") is not None` | `gh --version` | None |
| Docker | `shutil.which("docker") is not None` AND `docker info` non-error | `docker --version` | None |

### Windows 11

| Tool | Detection probe | Version probe | VM probe |
|---|---|---|---|
| Node 20+ | `shutil.which("node") is not None` | `node --version` | `%USERPROFILE%\.nvm` (nvm-windows), `%USERPROFILE%\.volta`, `where fnm`, `where mise` |
| Python 3.13+ | `shutil.which("python") is not None` (NOT `python3` — Windows uses `python`) AND version ≥ 3.13 | `python --version` | `%USERPROFILE%\.pyenv` (pyenv-win), `where mise` |
| git 2.40+ | `shutil.which("git") is not None` | `git --version` | None |
| gh 2.x | `shutil.which("gh") is not None` | `gh --version` | None |
| Docker | `shutil.which("docker") is not None` AND `docker info` non-error | `docker --version` | — (Docker Desktop is the only viable path; no Windows Docker VM ecosystem) |

---

## Install Commands per Platform

> All package IDs verified against official sources Apr 2026. Pin the exact ID; never use search-by-name (which can match wrong packages).

| Tool | macOS (brew) | Linux apt-get | Linux dnf | Windows winget | Windows scoop fallback |
|---|---|---|---|---|---|
| Node 20+ | `brew install node@20` (or `node` for latest LTS — `node` defaults to current LTS at install time) [VERIFIED: brew.sh] | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo -E bash - && sudo apt-get install -y nodejs` [CITED: github.com/nodesource/distributions] | `sudo dnf install -y nodejs:20/common` (module stream) [CITED: docs.fedoraproject.org] | `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements` [VERIFIED: winget.run/pkg/OpenJS/NodeJS.LTS — current LTS 24.11.0] | `scoop install nodejs-lts` |
| Python 3.13+ | `brew install python@3.13` [VERIFIED: brew.sh] (matches bootstrap.sh:33) | `sudo apt-get install -y python3.13 python3.13-venv` (Ubuntu 24.10+; older needs deadsnakes PPA) | `sudo dnf install -y python3.13` (Fedora 41+) | `winget install -e --id Python.Python.3.13 --accept-source-agreements --accept-package-agreements` [VERIFIED: matches bootstrap.ps1:27] | `scoop install python` |
| git 2.40+ | `brew install git` [VERIFIED] | `sudo apt-get install -y git` | `sudo dnf install -y git` | `winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements` [VERIFIED: winget.run] | `scoop install git` |
| gh 2.x | `brew install gh` [VERIFIED] | Add GitHub repo: `(type -p wget >/dev/null \|\| sudo apt-get install wget -y) && sudo mkdir -p -m 755 /etc/apt/keyrings && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \| sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \| sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt-get update && sudo apt-get install -y gh` [CITED: github.com/cli/cli/blob/trunk/docs/install_linux.md] | `sudo dnf config-manager addrepo --from-repofile=https://cli.github.com/packages/rpm/gh-cli.repo && sudo dnf install -y gh` [CITED: cli.github.com] | `winget install -e --id GitHub.cli --accept-source-agreements --accept-package-agreements` [VERIFIED: winget.run] | `scoop install gh` |
| Docker | `brew install orbstack` (no `--cask` needed in current docs) [VERIFIED: docs.orbstack.dev] — fallback `brew install --cask docker` if user explicitly wants Docker Desktop | `sudo apt-get install -y docker.io docker-compose-plugin` (or follow Docker's repo for latest) | `sudo dnf install -y docker docker-compose-plugin` (or follow Docker's RHEL repo) | `winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements` [VERIFIED: winget.run/pkg/Docker/DockerDesktop] — pre-warn user about license terms (see *Common Pitfalls / Pitfall 4*) | (No good scoop equivalent for Docker on Windows — fall back to manual download URL with friendly message) |

**Note on `gh` Linux apt path:** The full keyring + repo dance is the OFFICIAL install per cli.github.com — but it is LONG and brittle. For Phase 2 v1, **prefer using whatever apt package is in the user's existing repo** (`sudo apt-get install -y gh` works on Ubuntu 24.10+); fall back to the repo-add only if the package isn't found. Document the long form in `references/preflight/linux.md`. [CITED: November 2025 community guidance — community apt repo gh 2.45.x/2.46.x reportedly broken, recommend official Debian packages over community ones].

---

## Uninstall Commands per Platform

> The uninstall command for each install IS RECORDED IN THE INSTALL LOG at install time. The table below documents the standard inverse for each manager — used to populate the log entry.

| Manager | Uninstall command form |
|---|---|
| `brew` | `brew uninstall <package>` |
| `brew` (cask) | `brew uninstall --cask <name>` (only if installed via cask) |
| `apt-get` | `sudo apt-get remove --purge -y <package>` |
| `dnf` | `sudo dnf remove -y <package>` |
| `winget` | `winget uninstall -e --id <package_id>` |
| `scoop` | `scoop uninstall <package>` |
| NodeSource setup script (Linux Node) | `sudo apt-get remove --purge -y nodejs && sudo rm /etc/apt/sources.list.d/nodesource.list` |

**Rule:** The uninstall command is computed at INSTALL time (when we know which manager succeeded) and stored in `install-log.json`. The uninstall path in `uninstall.py` reads the log and invokes each recorded command — it does NOT re-derive uninstall commands.

---

## Common Pitfalls

### Pitfall 1: Auto-installing Node when nvm is present

**What goes wrong:** User has `nvm` managing Node 18 for an existing project. OSBuilder runs `brew install node@20`. Now `which node` returns `/opt/homebrew/bin/node` (v20), but their existing project's `package.json` was tested on v18. Their old project breaks. They blame OSBuilder. They never use it again.

**Why:** STACK.md anti-recommendation matches Pitfall 13. "Install Node" has 8 right answers (nvm/n/fnm/mise/brew/apt/choco/scoop/official/asdf). LLM picks the most-trained-on answer; user's environment may not match.

**Avoid:** Detection-first — see Pattern 1. If nvm/pyenv/mise/asdf/volta/fnm is detected, REFUSE to install via brew/apt and ASK the user to use their VM. Phase 5 polishes the message; Phase 2 ships a working refusal.

**Warning signs:** `~/.nvm` directory exists. `which nvm` succeeds. `node --version` shows a managed version (often <20). User's shell init sources nvm.

---

### Pitfall 2: macOS system Python tampering

**What goes wrong:** `/usr/bin/python3` is Apple's system Python — used by macOS internal tooling, Xcode, and `sw_vers`. Touching it via `brew install python3` doesn't break the system Python (brew installs to `/opt/homebrew/bin/python3` or `/usr/local/bin/python3`), BUT a naive script that does `sudo rm /usr/bin/python3` (or worse) breaks Apple's tools.

**Why:** STACK.md anti-recommendation. Apple updates the system Python on every macOS update; user-installed tools that rely on `/usr/bin/python3` get clobbered.

**Avoid:** Always use `brew install python@3.13` to install Python 3.13. Use `python3.13` (not `python3`) when invoking it. Document in `references/preflight/macos.md`.

**Warning signs:** Code that reads from or writes to `/usr/bin/python3`. Code that does `sudo rm` anywhere on macOS.

---

### Pitfall 3: Windows winget PATH refresh after install

**What goes wrong:** After `winget install Python.Python.3.13`, the current PowerShell session's PATH is stale. `python --version` returns "command not found" or the OLD Python. The naive script flow ("install, then verify by re-probing") fails — preflight reports "install failed" when in fact it succeeded; the user reopens their shell next time and Python is there.

**Why:** Documented winget bug [VERIFIED: github.com/microsoft/winget-cli/issues/3359, github.com/microsoft/winget-cli/issues/531]. winget does not refresh the parent process's environment variables.

**Avoid:** See Pattern 2. On Windows, after `subprocess.run` returns 0, treat the install as succeeded WITHOUT re-probing. Append a "reopen your shell" line to the post-install summary. `bootstrap.ps1:39-44` already implements exactly this for Python.

**Warning signs:** Tests pass on macOS/Linux but fail on Windows. CI matrix shows Windows-only failures with "command not found" after install. User reports "I ran preflight, it said failed, but Python is actually there."

---

### Pitfall 4: Docker Desktop license surprise

**What goes wrong:** OSBuilder auto-installs Docker Desktop on a developer's Windows machine at a 250+ employee company. The dev's IT department sends them a "license violation" email two months later. Trust gone.

**Why:** Docker Desktop is FREE for personal use and small companies (< 250 employees AND < $10M revenue), but paid for everyone else (~$11-24/user/month) [VERIFIED: docker.com/pricing — Apr 2026].

**Avoid:**
- Pre-warn in the dry-run preview: "Docker Desktop is free for personal use; paid in companies with 250+ employees or $10M+ revenue. Continue?"
- Make the warning unmissable on Windows specifically (where Docker Desktop is the only viable Docker option)
- Document in `references/preflight/windows.md`
- Honor `--no-docker` (PRE-07) — for users who don't want to deal with this, SQLite-only single-user CLI builds work without Docker

**Warning signs:** User asks "do I need this?" — they already aren't sure. User invokes from a corporate-domain-joined Windows machine.

---

### Pitfall 5: Linux sudo prompt eaten by subprocess

**What goes wrong:** `subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], capture_output=True)` captures stderr — including sudo's password prompt — so the user sees the script HANG with no visible prompt. They Ctrl-C. They blame OSBuilder.

**Why:** sudo writes the password prompt to `/dev/tty` (not stderr) BUT password ECHO suppression and prompt formatting depends on sudo having a TTY. `capture_output=True` may break this on some sudo configurations.

**Avoid:**
- For `sudo` calls: do NOT use `capture_output=True`. Let stdout/stderr flow to the user's terminal. Use `subprocess.run([..."sudo", "apt-get"...], check=False)`.
- Pre-warn the user in the dry-run: "I will need your password to install via apt-get. You'll see a sudo prompt — type your password normally."
- On `apply()` start, print "About to invoke sudo for apt-get..." so the prompt is contextualized.

**Warning signs:** Linux preflight hangs on the first sudo invocation. User reports "it just stops."

---

### Pitfall 6: Rollback partial-install — the package manager kept artifacts

**What goes wrong:** `brew install gh` succeeded; `brew install docker` failed; rollback runs `brew uninstall gh`. But `brew install gh` ALSO pulled in ~10 dependency formulae (e.g., `gh` depends on `oniguruma`). `brew uninstall gh` doesn't auto-remove dependencies; user is left with `oniguruma` they didn't have before.

**Why:** Package managers don't track "what depended on this user-initiated install." `brew autoremove` exists but isn't always safe.

**Avoid:**
- Document this in `references/preflight/macos.md` as a known limitation: "Uninstall reverses the user-facing tool you installed. Transitive dependencies brought in by Homebrew may remain — run `brew autoremove` manually if you want to clean those up."
- Do NOT run `brew autoremove` automatically (it can remove stuff the user did want).
- Better answer for v2: snapshot `brew list` before install, diff after, record the delta in install-log; uninstall reverses the delta. This is HIGH-EFFORT for v1 — defer.

**Warning signs:** `brew list` after uninstall shows formulae that weren't there before preflight ran. User reports "uninstall didn't fully clean up."

---

### Pitfall 7: `--no-docker` flag passed but Docker still detected/prompted

**What goes wrong:** User runs `/osbuilder --no-docker`, OSBuilder still runs `docker info`, prints "Docker is missing — install?". User is confused — they EXPLICITLY said no.

**Why:** Detection and install are separate phases; the `--no-docker` flag must short-circuit BOTH.

**Avoid:**
- The flag is consumed at `detect()` entry: if `no_docker=True`, the `docker` entry is removed from the tools-to-detect list ENTIRELY.
- The flag also persists to `state.md` (`scripts/state_writer.py`) so a `/clear`'d session re-running preflight still respects it. Field name: `no_docker_mode`. (Adding a field requires updating REQUIRED_FIELDS in state_writer.py — that's a Phase 1 module edit, FLAG for the planner.)

**FLAG FOR PLANNER:** Adding `no_docker_mode` to state_writer's 10-field schema is a 1-line change but counts as a Phase 1 module edit. Alternative: store `no_docker_mode` in `~/.osbuilder/preflight-config.json` (separate from state.md). **Recommendation: use a separate file** to keep state.md schema stable.

---

### Pitfall 8: First-run-after-Phase-1-bootstrap does NOT run preflight automatically

**What goes wrong:** Phase 1's `bootstrap.sh` / `bootstrap.ps1` install Python and re-exec into `state_writer.py`. User assumes preflight ran — it didn't. They expect Node/git/gh to be installed. They type `/osbuilder build a TODO app` and get "node: command not found."

**Why:** Phase 1's bootstrap is *ONLY* for Python (so state_writer can run). Preflight (Node/git/gh/Docker) is Phase 2's responsibility. The handoff is fuzzy in the docs.

**Avoid:**
- `state_writer.py read` returning an empty/uninitialized state.md is the trigger for preflight. Phase 2's plan should add a tiny check: after bootstrap re-execs into state_writer, the next step (in SKILL.md routing) is to run `preflight_check.py check` if `next_action` is `gather-requirements` AND the install-log doesn't exist.
- Document the handoff in SKILL.md's "Resume Protocol" section. (Minor SKILL.md edit — flag for planner. Likely 5 lines.)

**FLAG FOR PLANNER:** SKILL.md edit is needed to document preflight handoff. Keep edit minimal — SKILL.md is at the 200-line cap, so adding lines requires removing equivalents. Alternative: add a `references/preflight/README.md` that SKILL.md links to, keeping SKILL.md unchanged.

---

## Approaches to the 11 Open Research Questions (from SUMMARY.md)

### Q1: Windows-without-WSL preflight UX

**Approach:** Use `bootstrap.ps1`'s established two-mode pattern. PowerShell 5.1 (built into Windows 10/11) is the host. WSL detection is OUT OF SCOPE for v1 — `references/preflight/windows.md` includes a one-liner "if WSL is detected (`wsl --status` returns 0 with "Default Version: 2"), prefer the Linux preflight path inside WSL", but the v1 implementation ignores this.

UAC elevation: NOT NEEDED for `winget install` of user-scope packages (winget defaults to user scope). Document this. If `winget install` requires admin (system-scope packages), winget itself triggers UAC — let the OS handle it, don't try to elevate the Python script.

PATH refresh: see Pitfall 3 + Pattern 2 — print "reopen shell" message after each Windows install.

**Confidence:** MEDIUM (no real-machine test in research session; matches `bootstrap.ps1` proven pattern).

---

### Q2: Version-manager detection (nvm/pyenv/mise/asdf/fnm/volta/rustup)

**Approach:** Pattern 1 — detect via filesystem path checks (`~/.nvm`, `~/.pyenv`, etc.) AND `shutil.which` for the manager binary. If detected, route through their docs (REFUSE auto-install; PRINT the right command for them to run).

This is more conservative than "auto-install through their VM" because each VM has different commands and edge cases — Phase 2 v1 doesn't try to know all of them.

`rustup` is **OUT OF SCOPE** — Tauri/desktop is Phase 7. Phase 2 detects nvm/pyenv/mise/asdf/fnm/volta only.

**Confidence:** HIGH for the refuse-and-defer approach; MEDIUM for whether v2 should auto-install via VM.

---

### Q3: Privilege escalation UX (Linux sudo, Windows admin)

**Approach:**

- **Linux:** Pre-warn in dry-run preview ("I'll use sudo for these commands…"). Run sudo commands without `capture_output` so the prompt flows naturally. (See Pitfall 5.)
- **Windows:** Don't try to programmatically elevate. winget user-scope installs don't need admin. If a system-scope install is required, winget itself triggers UAC; let it.
- **macOS:** brew installs don't require sudo (Homebrew installs to user-owned paths). No special handling.

Document each in the per-OS reference matrix.

**Confidence:** MEDIUM. The "let sudo own the TTY" pattern is well-documented but failure modes vary by sudo config.

---

### Q4: Rollback granularity — partial-batch vs all-or-nothing

**Approach:** **All-or-nothing** at the batch level. If install of tool 3 of 5 fails, rollback uninstalls tools 1 and 2 (already succeeded), and reports "I tried to install [list], failed at [tool 3] because [error], cleaned up [tool 1, tool 2]."

Rationale:
- Partial-batch leaves the user in an inconsistent state — they have to figure out which tools are partly there
- Rollback is what we promised in PRE-04 ("rolled-back machine is in the exact state it was in before preflight ran")
- "All-or-nothing" matches openSUSE transactional-update semantics [CITED: github.com/openSUSE/transactional-update] and dpkg/rpm postinst conventions

Schema for install-log:

```json
{
  "schema_version": "1",
  "actions": [
    {"tool": "...", "package_id": "...", "manager": "...",
     "platform": "...", "started_at": "...", "succeeded_at": "...|null",
     "install_command": "...", "uninstall_command": "...",
     "status": "started|succeeded|failed|rolled-back"}
  ]
}
```

**Confidence:** HIGH for all-or-nothing at the batch level; HIGH for the schema.

---

### Q5: Linux distro coverage scope for v1

**Approach:** **apt-get + dnf only.** Detection via `platform.freedesktop_os_release()` ID + ID_LIKE.

- Ubuntu, Debian, Linux Mint, Pop!_OS, ElementaryOS → apt (`debian` in ID_LIKE)
- Fedora, RHEL, CentOS, Rocky, AlmaLinux → dnf (`fedora` or `rhel` in ID_LIKE)
- Arch, Manjaro, openSUSE, Alpine, NixOS → **REFUSE preflight in v1** with a friendly "your distro isn't supported yet — please install Node 20+, Python 3.13+, git, gh, and Docker through your package manager. PR welcome."

Rationale: Charlie's audience is overwhelmingly macOS + Windows + Ubuntu/Fedora. Coverage of the niche distros isn't worth the maintenance cost in v1.

`references/preflight/linux.md` documents the refusal path for unsupported distros.

**Confidence:** HIGH. matches PROJECT.md "common person" framing.

---

### Q6: Docker Desktop licensing communication for non-developers

**Approach:** See Pitfall 4. Pre-warn in dry-run preview, especially on Windows where Docker Desktop is the only viable option. The warning text is OWNED by Phase 5 (friendly_error.py) — Phase 2 ships a basic version like:

> "Docker Desktop is free for personal use. If you work for a company with 250+ employees or $10M+ revenue, your company needs a paid subscription. Continue? [y/N]"

If the user picks `--no-docker`, this prompt doesn't fire.

**Confidence:** HIGH for the licensing facts (verified Apr 2026); MEDIUM for the right wording.

---

### Q7: `--no-docker` flow timing — CLI flag vs preflight prompt vs auto-skip

**Approach:** **CLI flag passed at `/osbuilder` invocation, persisted to `~/.osbuilder/preflight-config.json`, honored by both detect() and apply().**

- Default: detect Docker, prompt if missing
- `--no-docker` set: don't detect Docker, don't prompt, record the choice
- Auto-skip on Windows for individual users: NO — too magical. User must explicitly set `--no-docker`.

The flag persists to `~/.osbuilder/preflight-config.json` (NOT state.md — see Pitfall 7 FLAG FOR PLANNER). State.md schema stays at 10 fields.

**Confidence:** HIGH for the flag; HIGH for not auto-detecting individual users (too brittle).

---

### Q8: Detection speed budget — sequential vs parallel

**Approach:** **Sequential.** Total budget for 5 tool detections + 1 OS detect + 6 VM probes = ~12 subprocess calls. At 50ms each on warm cache, that's 600ms; on cold cache, ~2-3 seconds. Well under the 10-second SLA in success criterion #1.

Threading adds:
- Windows-PATH-stale race conditions
- Test mocking complexity (FakeShell across threads is messy)
- ZERO real benefit at this scale

**Confidence:** HIGH.

---

### Q9: End-to-end ≤ 3 minute SLA on fresh Mac (success criterion #6)

**Approach:** Budget breakdown:

| Phase | Time | Notes |
|---|---|---|
| Detection | 2-5s | Sequential subprocess calls |
| Dry-run preview render + user typing "y" | 5s | User-bound |
| `brew install node@20` | 30-60s | Network: ~30MB tarball + deps |
| `brew install python@3.13` | 30-60s | Network: ~30MB |
| `brew install git` | 5-15s | Often already on macOS via Xcode CLT |
| `brew install gh` | 5-15s | Small |
| `brew install orbstack` | 30-60s | ~100MB |
| Post-install verification | 2-5s | shutil.which probes |
| **Total** | **~110-220s** | **Well within 3-min SLA** |

Risk: cold Homebrew tap (`homebrew/cask`) can add 30s on first install. Document.

Recommendation: do NOT pre-update brew (`brew update`) — it's slow (sometimes 30+ seconds on a cold cache) and not strictly necessary. STACK.md doesn't require it.

**Confidence:** MEDIUM (estimated based on typical brew install times; will need real-machine validation).

---

### Q10: `install-log.json` location convention

**Recommendation: `~/.osbuilder/install-log.json`** (HOME directory, not project-root).

Rationale:
- Preflight is INSTALLED ONCE PER USER MACHINE, not per project. The user installs Node/Python/git/gh/Docker globally; the log of "what we installed" is global.
- A project-local install-log makes uninstall require knowing which project to read from
- Pitfall 13 explicitly suggests `~/.osbuilder/install-log.json`
- This is consistent with how Phase 5 will write `~/.osbuilder/learned.json` (Pitfall 19) and Phase 4 will write `~/.osbuilder/handoffs/{timestamp}/` (Pitfall 18)

`state.md` correctly stays at `<project-root>/.planning/osbuilder/state.md` because state IS per-project.

**Confidence:** HIGH.

---

### Q11: Test strategy — cross-platform install logic without actual installs

**Approach:** **Mock `subprocess.run` and `shutil.which` via `monkeypatch` in pytest. Use a `FakeShell` class that records every command and returns canned output per command.**

Pattern:

```python
# scripts/tests/conftest.py — added in Wave 0

class FakeShell:
    """Records every subprocess.run call and replays canned results.
    Use to test install logic without actually installing anything."""
    def __init__(self):
        self.calls = []  # [(cmd_list, returncode, stdout, stderr), ...]
        self._programmed = {}  # cmd_signature -> (returncode, stdout, stderr)

    def program(self, cmd_signature: str, returncode: int = 0,
                stdout: str = "", stderr: str = ""):
        """Pre-program a response for any subprocess.run that matches cmd_signature."""
        self._programmed[cmd_signature] = (returncode, stdout, stderr)

    def __call__(self, cmd, *args, **kwargs):
        # cmd may be list or string; normalize to a signature
        sig = " ".join(cmd) if isinstance(cmd, list) else cmd
        for prefix, (rc, so, se) in self._programmed.items():
            if sig.startswith(prefix):
                self.calls.append((cmd, rc, so, se))
                return subprocess.CompletedProcess(cmd, rc, so, se)
        # default: return success with empty output
        self.calls.append((cmd, 0, "", ""))
        return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def fake_shell(monkeypatch):
    fs = FakeShell()
    monkeypatch.setattr("subprocess.run", fs)
    return fs


@pytest.fixture
def fake_which(monkeypatch):
    """Programmable shutil.which — set fake_which.found = {"node": "/usr/bin/node"}."""
    found: dict[str, str | None] = {}
    monkeypatch.setattr("shutil.which", lambda name: found.get(name))
    return found


@pytest.fixture
def tmp_install_log(tmp_path, monkeypatch):
    """Isolate ~/.osbuilder/ to a tmp dir for tests."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    return fake_home / ".osbuilder" / "install-log.json"
```

Tests then exercise full install flows:

```python
def test_macos_node_install_records_log(fake_shell, fake_which, tmp_install_log,
                                          monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_shell.program("brew install node@20", returncode=0)
    # node not installed initially
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    # first probe: node missing
    fake_which["node"] = None

    pf = importlib.import_module("preflight_check")
    plan = pf.plan(no_docker=True)
    pf.apply(plan)

    log = json.loads(tmp_install_log.read_text())
    assert log["actions"][0]["tool"] == "node"
    assert log["actions"][0]["status"] == "succeeded"
    assert log["actions"][0]["uninstall_command"] == "brew uninstall node@20"
```

This way, `pytest scripts/tests/` runs in < 1 second, never touches the user's machine, and verifies cross-platform install logic deterministically.

**Confidence:** HIGH.

---

## Code Examples

### `preflight_check.py` Public API

```python
# Source: distilled from Phase 1 state_writer.py argparse pattern + this research
# Verification: matches the bootstrap.{sh,ps1} re-exec contract

# preflight_check.py — public API the planner should target
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ToolStatus:
    tool: str
    detected: bool
    version: str | None
    version_ok: bool
    vm_routing: str | None  # "nvm" | "pyenv" | etc., or None
    notes: list[str]


@dataclass
class InstallAction:
    tool: str
    manager: str
    package_id: str
    install_command: str
    uninstall_command: str
    requires_sudo: bool
    notes: list[str]


@dataclass
class Plan:
    os: str  # "macos" | "linux-debian" | "linux-fedora" | "windows"
    statuses: list[ToolStatus]
    actions: list[InstallAction]  # empty if all tools present + version OK
    blocked_by_vm: list[str]  # tool names where a VM is present (can't auto-install)
    no_docker: bool


def detect(*, no_docker: bool = False) -> dict[str, ToolStatus]:
    """Read-only: inspect machine, return status per tool. No side effects."""

def plan(*, no_docker: bool = False) -> Plan:
    """Pure: detect() + apply per-OS decision tree. No side effects."""

def render_preview(plan: Plan) -> str:
    """Render the dry-run preview for PRE-05.
    Format: numbered list of tools + manager + size estimate."""

def apply(plan: Plan) -> int:
    """Execute the plan. Records every action to install-log.json BEFORE running.
    On any failure, calls rollback() automatically.
    Returns 0 on full success, non-zero on rollback completion."""

def rollback() -> int:
    """Read install-log.json, iterate actions in REVERSE, run each uninstall_command.
    Marks each action as 'rolled-back' in the log on success.
    Returns 0 on clean rollback, non-zero if some uninstalls failed."""

def uninstall() -> int:
    """PRE-06 — same logic as rollback() but invoked by the user, not auto-triggered.
    Removes everything OSBuilder ever installed (per the log)."""


# CLI entry — mirrors state_writer.py argparse style
def main(argv: list[str] | None = None) -> int:
    """argparse subcommands:
       check     — print Plan in human-readable form (detect + plan)
       preview   — print Plan AND render_preview (PRE-05 dry-run)
       install   — apply() with single-confirmation prompt (PRE-02)
       install --dry-run — same as preview (one-flag alias for habit)
       install --no-docker — PRE-07
       rollback  — invoke rollback() (typically auto-called, but available manually)
       uninstall — PRE-06
    """
```

### `uninstall.py` (thin wrapper)

```python
#!/usr/bin/env python3
"""uninstall.py — remove anything OSBuilder's preflight installed (PRE-06)."""
import sys
from pathlib import Path

# importable: this script's parent dir contains preflight_check.py
sys.path.insert(0, str(Path(__file__).parent))
from preflight_check import uninstall  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(uninstall())
```

### Linux distro detection (drop-in)

```python
# Source: VERIFIED against docs.python.org/3/library/platform.html#platform.freedesktop_os_release
# Cross-checked against actions/runner PR #3155 ID_LIKE handling

import platform

def detect_linux_manager() -> str | None:
    """Returns 'apt-get', 'dnf', or None if unsupported."""
    try:
        osr = platform.freedesktop_os_release()
    except (OSError, NotImplementedError):
        return None  # Not Linux, or os-release missing
    ids = {osr.get("ID", ""), *osr.get("ID_LIKE", "").split()}
    if "debian" in ids or "ubuntu" in ids:
        return "apt-get"
    if "fedora" in ids or "rhel" in ids:
        return "dnf"
    return None  # arch / opensuse / alpine / etc. — refuse preflight in v1
```

---

## State of the Art

| Old Approach | Current Approach (2026) | Why Changed | Impact |
|---|---|---|---|
| Hand-parse `/etc/os-release` | `platform.freedesktop_os_release()` | Stdlib added the helper in Python 3.10 | Cleaner code, handles edge cases (escape sequences, missing file) |
| Bash preflight scripts | Python 3 preflight | Bash fails on Windows even via Git Bash; Pitfall 14 | Reliability across the macOS/Linux/Windows matrix |
| `subprocess.call` | `subprocess.run` | `.run` is the post-3.5 modern API; `.call` is legacy | Consistent return type, `check=True` for exception-on-nonzero |
| Chocolatey-as-primary on Windows | winget primary, scoop fallback, choco last | winget is built-in on Win10 1809+ / 11; choco requires admin + separate install | Lower friction for non-developers |
| Docker Desktop on Mac | OrbStack on Mac | Faster startup (2s vs 20-30s), 1.7× more battery-efficient, 2-10× faster filesystem | Better UX on Apple Silicon |
| Manually parse `node --version` | Same — there's no better stdlib API | (no change) | n/a |

**Deprecated/outdated:**
- `lsb_release` for Linux distro detection — superseded by `/etc/os-release` (and Python's wrapper)
- Per-distro install scripts hand-coded into bash — superseded by `freedesktop_os_release()` + a small dispatch table
- Chocolatey as Windows-default — superseded by winget (built-in)
- Colima as Mac Docker default — superseded by OrbStack (smaller, faster, drop-in CLI)
- Docker Desktop as Mac Docker default for new installs — see above; OrbStack is the 2026 default

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The end-to-end ≤ 3 minute SLA holds on a fresh Mac with average broadband (~50Mbps) | Q9 | Real-machine test may show > 3 min on slow networks; mitigation = state SLA assumption explicitly in tests, accept 3-5 min as acceptable |
| A2 | `brew install python@3.13` on macOS does not require sudo (Homebrew installs to user-owned `/opt/homebrew/`) | Pitfall 5 + macOS column | If user has a non-standard brew install (`/usr/local` on Apple Silicon — unusual), behavior may differ |
| A3 | `winget install` user-scope packages don't require admin elevation | Q1 + Q3 | If a tool's winget manifest requires system-scope, UAC prompt fires; we delegate to OS |
| A4 | Auto-installing Docker Desktop on Windows triggers Docker's own license-acceptance flow | Pitfall 4 | If winget bypasses the license screen, we may be installing without user license consent — mitigation = pre-warn before install |
| A5 | nvm-windows uses `~/.nvm` like nvm on POSIX | Windows VM probe | nvm-windows actually stores at `%APPDATA%\nvm` per its docs — VERIFY when implementing windows VM detection |
| A6 | NodeSource setup script for apt is still the recommended Linux Node 20 install path in Apr 2026 | Linux Node row | NodeSource has changed packaging; verify at implementation time |
| A7 | `brew install orbstack` (no `--cask`) is the current command per docs.orbstack.dev | macOS Docker row | STACK.md says `brew install --cask orbstack`; current docs say plain `brew install orbstack`. Both work today; pick the simpler form |
| A8 | The `nodejs:20/common` dnf module stream exists on Fedora 39+ | Linux Node row dnf | If module stream is renamed, install fails; fallback = `nodejs` (latest stable) |
| A9 | The "FLAG FOR PLANNER: SKILL.md edit needed" in Pitfall 8 is acceptable to the user | Pitfall 8 | If user wants SKILL.md untouched, route preflight handoff via `references/preflight/README.md` instead |
| A10 | `~/.osbuilder/preflight-config.json` is the right place for `--no-docker` persistence | Pitfall 7 + Q7 | If user wants single-config-file (state.md only), revisit and add `no_docker_mode` to the 10-field schema (Phase 1 module edit) |
| A11 | Windows nvm-windows / pyenv-win VMs are detectable via the same patterns as nvm-posix / pyenv-posix | Windows VM row | nvm-windows in particular is structurally different from nvm-posix; window-specific detection logic may be needed |

> The 11 items above are knowledge from training/research that wasn't directly verified in this session. Planner should consider any A1-A11 worth confirming with the user before locking into the plan.

---

## Open Questions (for planner / discuss-phase)

1. **Should `--no-docker` persist via state.md (10-field schema edit) or a separate `~/.osbuilder/preflight-config.json`?** Recommendation: separate file (no Phase 1 schema churn). Decision is reversible.
2. **Should the `references/preflight/README.md` exist as a 4th file in the preflight reference directory, or do we put the SKILL.md preflight-handoff text directly in `references/preflight/macos.md`?** Recommendation: README.md as the entry point.
3. **For Linux Node install, `apt-get install nodejs` ships an old version on most distros. Use NodeSource setup script (verbose curl-pipe-bash) or document "use the snap version" (refused) or "install via nvm yourself"?** Recommendation: NodeSource for Ubuntu/Debian, dnf module stream for Fedora.
4. **For Linux gh install, use the apt-repo-add ceremony or just `apt-get install gh`?** Recommendation: try `apt-get install gh` first; if not in repo or version is old, add the official repo.
5. **Should preflight ATTEMPT to auto-update brew (`brew update`) before installs?** Recommendation: NO (slow; STACK.md doesn't require it).
6. **Should we test on Windows during Phase 2 development?** Recommendation: YES via WSL or a Windows VM at plan-execute time; the FakeShell test harness covers logic but real Windows shell quirks (PATH refresh) need at least one manual real-machine smoke test.
7. **Should the `apply()` confirmation prompt accept any input besides `y`/`yes`/`n`/`no`?** Recommendation: case-insensitive y/yes accept; everything else cancels (PRE-02 single confirmation, fail-safe default).
8. **On `Ctrl-C` mid-install, do we automatically rollback or just exit?** Recommendation: catch KeyboardInterrupt in apply(), call rollback(), then re-raise. User sees both "rolling back" message AND the cancel.

---

## Environment Availability

> Phase 2 is BUILDING the preflight checker. The host environment for DEVELOPING Phase 2 is Charlie's machine (macOS).

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.13+ | preflight_check.py development | ✓ (assumed — Phase 1 already needs it) | per Phase 1 bootstrap | Phase 1 bootstrap.sh installs |
| pytest | tests | ✓ (in pyproject.toml from Phase 1) | 8.x | — |
| brew (macOS) | dev-machine smoke testing | ✓ | per machine | — |
| Linux VM or container | Linux smoke testing | ✗ (not required; FakeShell covers logic) | — | Docker container with apt-get / dnf for ad-hoc smoke if needed |
| Windows VM | Windows smoke testing | ✗ (not required for v1; FakeShell + bootstrap.ps1 patterns cover the surface) | — | Document this gap; v2 milestone V2-XPL-01 closes it |
| `subprocess` mocking lib | tests | ✓ via `pytest.MonkeyPatch` (stdlib bundled) | — | — |

**Missing dependencies with no fallback:** None blocking. Real-machine Windows + Linux validation deferred to v2 cross-platform CI matrix (V2-XPL-01).

**Missing dependencies with fallback:** Real Linux/Windows hosts → Docker container ad-hoc + FakeShell test harness covers in CI-equivalent.

---

## Validation Architecture

Test infrastructure for Phase 2. Required because `workflow.nyquist_validation = true` in `.planning/config.json`.

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest 8.x (already configured in `pyproject.toml` from Phase 1) |
| Config file | `pyproject.toml` (Wave 0 of Phase 1 set `[tool.pytest.ini_options]`) |
| Quick run command | `pytest scripts/tests/test_preflight.py scripts/tests/test_uninstall.py -x` |
| Full suite command | `pytest scripts/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| PRE-01 | Detect missing Node/Python/git/gh/Docker | unit | `pytest scripts/tests/test_preflight.py::test_detect_missing_tools_macos -x` | ❌ Wave 0 |
| PRE-01 | Detect installed Node version too low (< 20) | unit | `pytest scripts/tests/test_preflight.py::test_detect_node_below_required -x` | ❌ Wave 0 |
| PRE-01 | Detect VM (nvm/pyenv/mise) and refuse to clobber | unit | `pytest scripts/tests/test_preflight.py::test_vm_detected_blocks_install -x` | ❌ Wave 0 |
| PRE-01 | Detect Linux distro (Ubuntu vs Fedora) via os-release | unit | `pytest scripts/tests/test_preflight.py::test_detect_linux_distro_ubuntu -x` | ❌ Wave 0 |
| PRE-02 | Single confirmation prompt for whole batch | unit | `pytest scripts/tests/test_preflight.py::test_single_confirmation_for_batch -x` | ❌ Wave 0 |
| PRE-03 | macOS uses brew | unit | `pytest scripts/tests/test_preflight.py::test_macos_uses_brew -x` | ❌ Wave 0 |
| PRE-03 | Linux Debian uses apt-get | unit | `pytest scripts/tests/test_preflight.py::test_linux_debian_uses_apt -x` | ❌ Wave 0 |
| PRE-03 | Linux Fedora uses dnf | unit | `pytest scripts/tests/test_preflight.py::test_linux_fedora_uses_dnf -x` | ❌ Wave 0 |
| PRE-03 | Windows uses winget | unit | `pytest scripts/tests/test_preflight.py::test_windows_uses_winget -x` | ❌ Wave 0 |
| PRE-04 | Failed install rolls back prior installs | unit | `pytest scripts/tests/test_preflight.py::test_failure_triggers_rollback -x` | ❌ Wave 0 |
| PRE-04 | install-log.json recorded BEFORE install starts | unit | `pytest scripts/tests/test_preflight.py::test_log_recorded_before_subprocess -x` | ❌ Wave 0 |
| PRE-05 | Dry-run preview prints before any subprocess call | unit | `pytest scripts/tests/test_preflight.py::test_dry_run_no_state_change -x` | ❌ Wave 0 |
| PRE-06 | Uninstall reverses all logged installs | unit | `pytest scripts/tests/test_uninstall.py::test_uninstall_reverses_all -x` | ❌ Wave 0 |
| PRE-06 | Uninstall preserves pre-existing tools (only removes what we logged) | unit | `pytest scripts/tests/test_uninstall.py::test_uninstall_preserves_pre_existing -x` | ❌ Wave 0 |
| PRE-07 | `--no-docker` skips Docker detection AND prompt | unit | `pytest scripts/tests/test_preflight.py::test_no_docker_mode_skips_docker -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest scripts/tests/test_preflight.py scripts/tests/test_uninstall.py -x`
- **Per wave merge:** `pytest scripts/tests/ -v` (Phase 1 + Phase 2 tests)
- **Phase gate:** Full suite green before `/gsd-verify-work`; manual real-machine smoke test on macOS (Charlie's machine) + at least one Linux container smoke test before Phase 2 marked done.

### Wave 0 Gaps

- [ ] `scripts/tests/test_preflight.py` — covers PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-07 (≥ 12 RED stubs)
- [ ] `scripts/tests/test_uninstall.py` — covers PRE-06 (≥ 2 RED stubs)
- [ ] `scripts/tests/conftest.py` — add `FakeShell`, `fake_shell`, `fake_which`, `tmp_install_log` fixtures
- [ ] `scripts/preflight_check.py` — file does not exist yet (lazy-import-via-fixture pattern handles this)
- [ ] `scripts/uninstall.py` — file does not exist yet
- [ ] No new framework install needed (pytest already in pyproject.toml from Phase 1)

---

## Wave Decomposition Recommendation

**Mirror Phase 1's pattern: Wave 0 (test infrastructure) → Wave 1 (parallel implementation).**

### Wave 0 — Test infrastructure (1 plan)

- File: `02-01-PLAN.md`
- Edits: `scripts/tests/conftest.py` (extend with FakeShell + fixtures)
- New: `scripts/tests/test_preflight.py` (≥ 12 RED stubs), `scripts/tests/test_uninstall.py` (≥ 2 RED stubs)
- All tests use lazy-import-via-fixture pattern from `test_state_writer.py:25-31`
- Acceptance: `pytest --collect-only` reports ≥ 14 new tests, all in SKIPPED state (not collection-error state)
- Estimated tasks: 2 (one for conftest extensions, one for the 14+ test stubs)

### Wave 1 — Implementation (3 plans, parallel-safe)

All Wave 1 plans target disjoint files, so they can run in parallel. Each Wave 1 plan flips a subset of the Wave 0 RED stubs to GREEN.

#### `02-02-PLAN.md` — `scripts/preflight_check.py` (TDD)

- Build the public API: `detect`, `plan`, `render_preview`, `apply`, `rollback`, `uninstall`, `main`
- Implement detection probes (shutil.which + version probes) for all 5 tools across 4 platforms
- Implement decision tree (apt-get vs dnf via freedesktop_os_release; winget vs scoop fallback on Windows)
- Implement install-log read/write (atomic_write helper extracted from state_writer.py or duplicated)
- Implement `apply()` with auto-rollback on failure
- Flips ~12 of the Wave 0 stubs to GREEN
- Estimated tasks: 4-6 (detect, plan, apply, rollback, render_preview, main + argparse)

#### `02-03-PLAN.md` — `scripts/uninstall.py` (thin wrapper)

- Tiny — imports `preflight_check.uninstall` and calls it from `__main__`
- Flips PRE-06 tests to GREEN
- Estimated tasks: 1

#### `02-04-PLAN.md` — `references/preflight/{macos,linux,windows}.md` + `README.md`

- Per-OS reference matrix (decision tree + edge cases + commands)
- README.md serves as the entry point linked from SKILL.md handoff
- Documents version-manager refusal flows
- Documents PATH-refresh gotcha (Windows)
- Documents Docker Desktop license consideration (Windows)
- Documents sudo prompt UX (Linux)
- Estimated tasks: 4 (one per file)

### Wave 2 (optional / merge to Wave 1) — SKILL.md handoff stub

If the planner decides Pitfall 8's flag is in-scope: a tiny edit to SKILL.md (or addition of `references/preflight/README.md` linked from SKILL.md) documenting the bootstrap → preflight handoff. Could be merged into 02-04-PLAN.md.

### Dependency Chain

```
Wave 0: 02-01 (test infra)
        ├── extends conftest.py
        ├── adds test_preflight.py (RED)
        └── adds test_uninstall.py (RED)
            ▼
Wave 1: 02-02 (preflight_check.py)  ←  02-03 (uninstall.py imports preflight_check)
        02-04 (references/preflight/*.md) — independent of code
```

`02-03` depends on `02-02`'s `uninstall()` symbol being importable. `02-04` is reference docs, parallel-safe with everything.

If parallelism is desired, run 02-02 and 02-04 in parallel; gate 02-03 on 02-02 completion.

---

## Risks Specific to This Phase

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Real-machine Windows behavior differs from FakeShell test predictions | MEDIUM | HIGH | Document Windows-specific behaviors in `references/preflight/windows.md`; manual smoke test on a Windows machine before Phase 2 marked done; Pitfall 3 (PATH refresh) explicitly covered in code via Pattern 2 |
| Auto-installing Node clobbers user's nvm setup | LOW (because we detect VMs first) | CATASTROPHIC (trust loss) | Pattern 1 — refuse to auto-install when VM detected. Test stub covers (PRE-01 VM detection) |
| Rollback leaves partial state because `brew uninstall gh` doesn't remove transitive deps | MEDIUM | MEDIUM | Document as known limitation in macos.md; defer perfect cleanup to v2 (snapshot/diff approach) |
| User's HOME has no write access (locked-down corp environment) | LOW | MEDIUM | install-log fails; preflight refuses to proceed with friendly error. Document. |
| Linux user's distro is Arch / openSUSE / Alpine / NixOS (unsupported) | MEDIUM | LOW | Refuse with clear message + manual-install instructions. Document in linux.md. |
| Docker Desktop license violation on a corporate Windows machine | MEDIUM | HIGH (legal) | Pre-warn in dry-run preview before Docker install on Windows. `--no-docker` honors |
| `--no-docker` flag persistence schema choice (state.md vs separate file) is wrong | LOW | LOW | Both choices reversible; recommendation = separate file is the conservative pick |
| Preflight is invoked from a non-TTY context (CI / pipe) and `input()` blocks forever | MEDIUM | MEDIUM | Detect `sys.stdin.isatty()`; if False, refuse with friendly error "preflight requires a terminal" |
| State.md doesn't persist `no_docker_mode`, so a `/clear`'d session re-prompts | LOW | LOW | `~/.osbuilder/preflight-config.json` persists the choice. Documented. |
| The 3-minute SLA fails on slow networks | MEDIUM | LOW | Document SLA assumes ≥ 50Mbps; relax to "≤ 5 min on average broadband" if real-machine validation requires |
| FakeShell harness diverges from real subprocess behavior | LOW | MEDIUM | Cross-validate with at least one real `brew install` smoke test on macOS before Phase 2 marked done |
| The version-manager detection logic produces false positives (e.g., empty `~/.nvm` left from uninstall) | MEDIUM | MEDIUM | Combine path-existence with `which nvm` — both must succeed. Document. |
| `gh` apt install via repo-add ceremony fails on Ubuntu LTS due to keyring path changes | MEDIUM | MEDIUM | Try `apt-get install gh` first (often works on Ubuntu 24.10+); fall back to repo-add. Document. |
| The schema-version field of install-log.json gets bumped without backward-compat | LOW | LOW (yet) | Version field is reserved at "1" from day one; v2 migration is out of scope for v1 |

---

## Project Constraints (from CLAUDE.md and Phase 1 STATE.md)

The following directives must be honored by Phase 2 plans. Treat with the same authority as locked decisions.

- **From CLAUDE.md (user global, project-relevant subset):**
  - Skill router: don't announce routing decisions ("I am X skill"). Phase 2 doesn't generate user-facing routing messages, so this is a constraint on tutor-mode wording (Phase 5).
  - When in doubt, prefer action over planning. Phase 2 has clear scope; this manifests as "ship the working preflight, don't bikeshed UX wording".
- **From Phase 1 STATE.md "Key Decisions Locked In":**
  - Form: skill at `~/.claude/skills/osbuilder/` — NOT a standalone CLI (relevant: preflight_check.py is invoked through `/osbuilder`, not a standalone install)
  - Helper-script language: Python 3.13 stdlib-only
  - Test pattern: lazy-import-via-fixture
  - Single-threaded execution; multi-agent narration only
  - 3-reflection cap (applies to install retries within batch)
  - Composition rule: don't reimplement gsd / brainiac / predator / code-tester / problem-solver inside OSBuilder
- **From PROJECT.md / SKILL.md hard rules:**
  - Always use deterministic scaffolders (not relevant to preflight — but is relevant for Phase 3)
  - 3-reflection cap (applies)
  - Slopsquatting gate (Phase 4 — out of scope)
  - Refuse-list: K8s, microservices, service-mesh, Helm, Electron, public repos by default — not directly relevant to preflight, but Pre-flight should NEVER suggest installing K8s/kubectl/helm even if user mentions them.
  - Privacy by default (Phase 6)
  - Composition over reimplementation
- **From STACK.md anti-recommendations:**
  - NO Chocolatey-primary on Windows
  - NO Colima default on Mac
  - NO Snap on Linux
  - DO NOT auto-install without confirmation (single-confirmation prompt is the trust contract)

---

## Sources

### Primary (HIGH confidence)

- [Python 3 stdlib `shutil.which`](https://docs.python.org/3/library/shutil.html#shutil.which) — cross-platform `which`/`where`
- [Python 3 stdlib `platform.freedesktop_os_release`](https://docs.python.org/3/library/platform.html#platform.freedesktop_os_release) — Linux distro detection (3.10+)
- [pytest monkeypatch docs](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) — subprocess mocking pattern
- [WinGet docs (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/package-manager/winget/) — package IDs + behavior
- [winget.run/pkg/OpenJS/NodeJS.LTS](https://winget.run/pkg/OpenJS/NodeJS.LTS) — Node LTS package ID verified
- [winget.run/pkg/Docker/DockerDesktop](https://winget.run/pkg/Docker/DockerDesktop) — Docker Desktop package ID verified
- [winget.run/pkg/GitHub/cli](https://winget.run/pkg/GitHub/cli) — GitHub CLI package ID verified
- [Homebrew](https://brew.sh) — macOS install commands
- [docs.orbstack.dev/install](https://docs.orbstack.dev/) — current OrbStack install command
- [github.com/cli/cli/blob/trunk/docs/install_linux.md](https://github.com/cli/cli/blob/trunk/docs/install_linux.md) — gh Linux install official path
- [github.com/microsoft/winget-cli/issues/3359](https://github.com/microsoft/winget-cli/issues/3359) — winget PATH-refresh issue
- [github.com/microsoft/winget-cli/issues/531](https://github.com/microsoft/winget-cli/issues/531) — winget reload PATH variable

### Primary OSBuilder-internal sources (HIGH confidence — direct file inspection)

- `.planning/research/STACK.md` — verified package matrix, anti-recommendations
- `.planning/research/PITFALLS.md` (#13 Preflight breaks system, #14 Cross-platform script breakage)
- `.planning/research/SUMMARY.md` — Phase 2 research flags (the 11 open questions)
- `.planning/STATE.md` — Phase 1 locked decisions
- `.planning/ROADMAP.md` — Phase 2 goal + 6 success criteria
- `.planning/REQUIREMENTS.md` — PRE-01..07 definitions
- `~/.claude/skills/osbuilder/SKILL.md` — installed skill reference (architecture target)
- `scripts/state_writer.py` — Phase 1 patterns (atomic_write, argparse subcommands, V5/V12 input validation)
- `scripts/bootstrap.{sh,ps1}` — Phase 1 cross-platform shim patterns (two-mode, OS detection)
- `scripts/tests/conftest.py` + `test_state_writer.py` — Phase 1 lazy-import-via-fixture test pattern

### Secondary (MEDIUM confidence)

- [docker.com/pricing](https://www.docker.com/pricing/) — license terms (250-employee threshold)
- [orbstack.dev/docs/compare/docker-desktop](https://orbstack.dev/docs/compare/docker-desktop) — performance comparison
- [DEV: How to Parse /etc/os-release](https://dev.to/htv2012/how-to-parse-etc-os-release-3kaj) — secondary verification of ID_LIKE handling
- [actions/runner PR #3155](https://github.com/actions/runner/pull/3155) — ID_LIKE detection in CI tooling

### Tertiary (LOW confidence — flagged for validation)

- Windows nvm-windows / pyenv-win path conventions (A5, A11) — not directly verified in this session; verify at implementation time
- NodeSource setup script being current Apr 2026 (A6) — verify at implementation time
- The exact end-to-end timing on a fresh Mac (A1, Q9) — needs real-machine measurement

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all package IDs verified against official registries Apr 2026
- Architecture (Wave 0/1 + dependency chain + file structure): HIGH — mirrors Phase 1 pattern that already shipped
- Pitfalls: HIGH for #1, #2, #3 (cross-checked against multiple sources); MEDIUM for #6 transitive-deps, #5 sudo TTY (category-pattern reasoning)
- The 11 Open Questions: HIGH for Q4, Q5, Q8, Q10, Q11; MEDIUM for Q1, Q3, Q9, Q6, Q7, Q2

**Research date:** 2026-04-29
**Valid until:** 2026-07-29 (90 days — package IDs verified, but Node LTS / Python 3.13.x point releases will tick; verify versions at plan-execute time if more than 30 days out)
