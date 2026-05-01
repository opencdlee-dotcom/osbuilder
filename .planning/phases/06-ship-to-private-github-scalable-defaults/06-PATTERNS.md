# Phase 6: Ship to Private GitHub + Scalable Defaults — Pattern Map

**Mapped:** 2026-05-01
**Files analyzed:** 26 new/extended files (3 new prod scripts, 3 extended scripts, 14 new template/reference assets, 5 new test files, 1 extended test conftest, 2 fixture markdowns, 1 SKILL.md edit)
**Analogs found:** 26 / 26

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/gh_handoff.py` (NEW) | orchestrator-script | event-driven (subprocess shell-out + state writes) | `scripts/scaffold_dispatch.py` | exact — same stdlib/argparse/_fe-graceful-degrade/_resolve_project_root/atomic_write/state_writer-subprocess pattern |
| `scripts/runbook_writer.py` (NEW) | orchestrator-script | transform (state.md + template → README.md) | `scripts/scaffold_dispatch.py` (`write_drizzle_files`) and `scripts/gsd_driver.py` (`_write_verification_md`) | role-match — pure templated stamping with placeholder substitution |
| `scripts/production_phase_writer.py` (NEW) | orchestrator-script | transform (state.md → stdout slash-commands) | `scripts/gsd_driver.py` (`emit_next_command` / `_run_tech_writer_step`) | role-match — read state.md → emit slash commands to stdout |
| `scripts/scaffold_dispatch.py` (EXTEND) | extension | event-driven | self (Phase 3 pattern) | self — extends `_DB_TS`-style constants and `write_drizzle_files()` boundary |
| `scripts/state_writer.py` (EXTEND) | extension | CRUD | self (Phase 3/4/5 ALLOWED_FIELDS additive pattern) | self |
| `scripts/intake_handler.py` (EXTEND) | extension | request-response | self (existing `_validate_project_name` + `_secret_patterns` gating) | self — adds refusal gate at intake; mirrors existing `_SECRET_PATTERNS` membership check |
| `SKILL.md` (EDIT) | reference-doc | — | self (line 87 already names `gh_handoff.py`) | self — confirm dispatch entry exists |
| `references/refuse-list.md` (NEW) | reference-doc | — | `references/preflight/README.md` | role-match — top-level explainer + machine-readable list block |
| `references/friendly-errors/gh-auth-drift.md` (NEW) | reference-doc | — | `references/friendly-errors/dictionary.yaml` entries (e.g., `pnpm-not-found`) | role-match — same 9-field schema, one entry per .md or one combined append |
| `references/friendly-errors/gh-not-installed.md` (NEW) | reference-doc | — | `references/friendly-errors/dictionary.yaml` entry `pnpm-not-found` | exact |
| `references/friendly-errors/gh-token-scope.md` (NEW) | reference-doc | — | dictionary.yaml entry `pnpm-not-found` | exact |
| `references/friendly-errors/gh-name-collision.md` (NEW) | reference-doc | — | dictionary.yaml entry `npm-404` | exact |
| `references/friendly-errors/gh-network.md` (NEW) | reference-doc | — | dictionary.yaml entry `pnpm-not-found` | exact |
| `assets/gitignore-templates/base.gitignore` (NEW) | template-asset | — | `_ENV_EXAMPLE` constant in `scaffold_dispatch.py:52` | role-match — promoted from inline string to file because it grows |
| `assets/gitignore-templates/node.gitignore` (NEW) | template-asset | — | same | role-match |
| `assets/gitignore-templates/python.gitignore` (NEW) | template-asset | — | same | role-match |
| `assets/gitleaks/.pre-commit-config.yaml` (NEW) | template-asset | — | `_COMPOSE_YAML` constant in `scaffold_dispatch.py:55-70` | role-match — single static YAML block, pinned to upstream version |
| `assets/gitleaks/.gitleaks.toml` (NEW) | template-asset | — | `_COMPOSE_YAML` constant | role-match |
| `assets/readme-template.md` (NEW) | template-asset | — | `_DRIZZLE_CONFIG` constant in `scaffold_dispatch.py:36-49` | role-match — placeholder-bearing template; substitution is pure-function in runbook_writer |
| `assets/ci/node.yml` (NEW) | template-asset | — | `_COMPOSE_YAML` constant | role-match |
| `assets/ci/python.yml` (NEW) | template-asset | — | `_COMPOSE_YAML` constant | role-match |
| `scripts/tests/test_gh_handoff.py` (NEW) | test-stub | — | `scripts/tests/test_scaffold_dispatch.py` | exact — same lazy-import `sd`-style fixture + `fake_shell.program` for subprocess capture |
| `scripts/tests/test_runbook_writer.py` (NEW) | test-stub | — | `scripts/tests/test_scaffold_dispatch.py::test_db_ts_written` | exact — file-presence + content-pattern asserts on tmp_path |
| `scripts/tests/test_scaffold_extensions.py` (NEW) | test-stub | — | `scripts/tests/test_scaffold_dispatch.py` | exact (extends the same module) |
| `scripts/tests/test_refusal.py` (NEW) | test-stub | — | `scripts/tests/test_intake.py` (pattern detection on derived_spec.md content) | role-match |
| `scripts/tests/test_production_ready.py` (NEW) | test-stub | — | `scripts/tests/test_state_writer.py::test_input_validation` (subprocess + stdout capture) | role-match |
| `scripts/tests/conftest.py` (EXTEND) | test-stub | — | self (existing `fake_shell` / `tmp_project_root` / `writer`) | self — additive new fixtures only |
| `scripts/tests/fixtures/derived_spec_with_k8s.md` (NEW) | fixture | — | `references/playbooks/web.md` Refuse list block | role-match — minimal markdown with refuse-keyword |
| `scripts/tests/fixtures/derived_spec_clean.md` (NEW) | fixture | — | `intake_handler._render_derived_spec()` output | exact |

---

# Track A — `gh_handoff.py` (private GitHub repo creation + push)

### `scripts/gh_handoff.py` (orchestrator-script, event-driven)

**Analog:** `scripts/scaffold_dispatch.py`

**Imports + module header pattern** (`scaffold_dispatch.py:1-23`):
```python
#!/usr/bin/env python3
"""scaffold_dispatch.py — OSBuilder web playbook scaffold dispatcher (SCAF-01, SCAF-06).

Pure stdlib. Subcommands: scaffold.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
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
```

**`_resolve_project_root` + `atomic_write` (verbatim duplicate, do NOT import — duplication is the project policy per D-05)** (`scaffold_dispatch.py:72-96`):
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

**Subprocess-with-friendly-error pattern** (`scaffold_dispatch.py:141-171`):
```python
try:
    subprocess.run(
        cmd, cwd=str(project_root), check=True,
        capture_output=True, text=True, shell=False,
    )
except (FileNotFoundError, OSError) as e:
    _raw = f"pnpm: command not found: {e}"
    if _fe is not None:
        _msg = _fe.translate(_raw, ctx={"tool": "pnpm"})
        sys.stderr.write(
            f"## {_msg.title}\n{_msg.what_broke}\n\n"
            f"**What to do:** {_msg.what_to_do}\n"
        )
        if _msg.copy_paste:
            sys.stderr.write(f"\n  {_msg.copy_paste}\n")
    else:
        sys.stderr.write(f"OSBuilder: scaffold failed — pnpm not found: {e}\n")
    raise SystemExit(1)
```

**Subprocess + canned-failure-routed-through-friendly-error (`scripts/registry_verify.py:22-37` — the secondary analog the researcher named for "external CLI + canned failure")**:
```python
def verify_npm(package_name: str, timeout: int = 10) -> bool:
    """Return True if the package exists on the npm registry, False if 404."""
    url = f"https://registry.npmjs.org/{package_name}"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except (urllib.error.URLError, OSError):
        return True  # fail-open
```

**state.md write via subprocess (verbatim from `scaffold_dispatch.py:222-232`)**:
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

**argparse + main scaffold pattern** (`scaffold_dispatch.py:238-264`):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="scaffold_dispatch",
        description="OSBuilder web playbook scaffold dispatcher.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scaffold = sub.add_parser("scaffold", help="...")
    p_scaffold.add_argument("--project-name", required=True, dest="project_name")
    p_scaffold.add_argument("--project-root", default=None, dest="project_root")
    p_scaffold.set_defaults(func=_cmd_scaffold)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1
```

**Patterns to replicate:**
- Module header: shebang + module docstring + `from __future__ import annotations` + `try/except ImportError: _fe = None` graceful-degrade for friendly_error
- Public surface: `def ship(project_dir: Path, project_root: Path, *, private: bool = True) -> int` — return-int convention; idempotency check via `git remote get-url origin` BEFORE `gh repo create`
- Every `subprocess.run(..., shell=False, capture_output=True, text=True)`; never `shell=True` (Phase 4 locked decision T-04-02-03)
- On non-zero return-code from `gh ...` or `git ...`: ALWAYS route stderr through `_fe.translate(...)` and write the formatted message to `sys.stderr` (literal copy of lines 141-171)
- Persist `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed` via `subprocess.run([sys.executable, str(STATE_WRITER), "write", ...])` — never edit state.md inline
- argparse subcommands: `ship`, `verify` (read-only `gh repo view --json` recheck for tests)

**Diverge here:**
- gh_handoff is a TERMINAL action (the last orchestrator-script in a build), not a SCAFFOLD step — do NOT call `pnpm` or `create-next-app` patterns; the project_dir already exists
- Add an explicit idempotency guard at top of `ship()`: check `git remote get-url origin` returns 0 with a github URL → return 0 immediately (do not re-create the repo)

---

### `references/refuse-list.md` (reference-doc)

**Analog:** `references/preflight/README.md` (top-level explainer style) + `references/playbooks/web.md` lines 50-58 (existing refuse-list block)

**Existing refuse list shape (`references/playbooks/web.md:50-58`)** — to be lifted out and expanded:
```markdown
## Refuse list

In v1 default builds, OSBuilder refuses:

- Kubernetes / Helm / service mesh
- Microservices architecture
- Electron (use Tauri 2 via desktop playbook)
- Auto-deploy without explicit consent
- Public GitHub repos by default (use `--public` to override)
```

**Reference-doc layout (`references/preflight/README.md:1-9`)**:
```markdown
# OSBuilder Pre-flight — Reference Index

> Per-OS install matrices, decision trees, and edge-case notes for `scripts/preflight_check.py`.
> Loaded on-demand by the Architect role at planning time. NOT pulled into `SKILL.md`
> (which is locked at ≤ 200 lines; see Phase 1 Plan 01-02).

## What pre-flight does

Before OSBuilder builds anything, it ensures the user's machine has the five required
tools installed:
```

**Patterns to replicate:**
- Top H1 + blockquote disclosure note ("loaded on demand; NOT pulled into SKILL.md")
- A `## Refuse keywords` H2 with a flat bullet list — the keywords are exactly the `REFUSE_KEYWORDS` tuple from RESEARCH.md Pattern 6 (kubernetes, k8s, helm, service mesh, service-mesh, microservice, microservices, istio, linkerd, consul). The intake-handler refusal gate parses this list at runtime (`(spec.lower())` membership)
- A `## Refusal copy` H2 with the user-facing message that mentions `--production-ready` opt-in path verbatim (SCL-05 success criterion #2)
- A `## See also` footer linking back to `scripts/intake_handler.py` (the gate) and `scripts/production_phase_writer.py` (the opt-in route)

**Diverge here:**
- Unlike preflight/README.md, this file is parsed by code (`intake_handler.py`) — keep keywords in a single fenced block or a flat bullet list with `- keyword` shape so a regex like `^- (\w+[\w- ]*)$` can extract them deterministically

---

### `references/friendly-errors/gh-*.md` (5 NEW reference-doc entries)

**Analog:** existing entries in `references/friendly-errors/dictionary.yaml:49-57` (`pnpm-not-found`)

**Pattern excerpt (`dictionary.yaml:49-57`)**:
```yaml
- id: pnpm-not-found
  match_pattern: "pnpm: command not found"
  category: preflight
  title: "pnpm isn't installed yet"
  what_broke: "The 'pnpm' command was not found on PATH."
  what_to_do: "Install pnpm globally, or let OSBuilder install it via preflight."
  copy_paste_command: "npm install -g pnpm"
  phase_seen: "preflight"
  expansion_note: "Phase 2 preflight dogfood"
```

**Patterns to replicate (per gh-* entry, 9 fields each, ALL required):**
- `id`, `match_pattern`, `category`, `title`, `what_broke`, `what_to_do`, `copy_paste_command`, `phase_seen`, `expansion_note` — exactly the schema enforced by `friendly_error.py:165-186` `load_dictionary()`
- `match_pattern`: include the substring that gh writes to stderr (e.g., `gh-auth-drift.md` matches `"You are not logged into any GitHub hosts"` and the alternative `"token is expired"`)
- `copy_paste_command`: a runnable single-line command (e.g., `gh auth login --git-protocol https`) — never `~` for these gh entries since each has a known fix
- ORDER MATTERS in dictionary.yaml: more-specific patterns BEFORE generic ones (file header line 2-4 calls this out)

**Diverge here:**
- The researcher prompt names 5 distinct files (`gh-auth-drift.md`, `gh-not-installed.md`, `gh-token-scope.md`, `gh-name-collision.md`, `gh-network.md`) — but `friendly_error.py:23` reads ONLY `references/friendly-errors/dictionary.yaml`. There are TWO viable shapes: (a) append 5 entries to dictionary.yaml AND drop the .md files (simpler, matches existing loader), or (b) keep .md files as expansion source + a build step that compiles them into dictionary.yaml. RECOMMENDED for v1: append 5 entries to dictionary.yaml; the .md files become Markdown-form documentation (one per failure mode) that lives in `references/friendly-errors/` and is referenced by `expansion_note` only. The planner must pick one and be consistent.
- `gh-name-collision.md` should set `match_pattern: "already exists on this account"` (HTTP 422 stderr fragment per RESEARCH Pitfall 4) and `copy_paste_command: ~` since the fix is interactive (suggest a new name)

---

# Track B — Built-app scaffold extensions

### `scripts/scaffold_dispatch.py` (EXTEND — `_write_dockerfile`, `_write_ci_workflow`, `_pick_database`, gitignore composition, gitleaks files)

**Analog:** self — `scaffold_dispatch.py:25-127` (the existing `_DB_TS` / `_COMPOSE_YAML` constant + `write_drizzle_files()` boundary)

**Existing constant + write_drizzle_files boundary (`scaffold_dispatch.py:25-70`, `122-127`)**:
```python
# Post-scaffold file contents (verbatim from RESEARCH.md Pattern 2)
_DB_TS = """\
// src/lib/db.ts — written post-scaffold by scaffold_dispatch.py
// Source: https://orm.drizzle.team/docs/get-started-postgresql
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

const queryClient = postgres(process.env.DATABASE_URL!);
export const db = drizzle({ client: queryClient });
"""

_COMPOSE_YAML = """\
services:
  postgres:
    image: postgres:18-alpine
    ...
"""

def write_drizzle_files(project_dir: Path) -> None:
    """Write ONLY 4 Drizzle + Postgres files (SCAF-06): db.ts, drizzle.config.ts, .env.example, compose.yaml."""
    atomic_write(project_dir / "src" / "lib" / "db.ts", _DB_TS)
    atomic_write(project_dir / "drizzle.config.ts", _DRIZZLE_CONFIG)
    atomic_write(project_dir / ".env.example", _ENV_EXAMPLE)
    atomic_write(project_dir / "compose.yaml", _COMPOSE_YAML)
```

**Patterns to replicate:**
- Add `_pick_database(playbook: str, app_type: str) -> str` as a pure function near the top constants (RESEARCH.md `## Code Examples` "Pure-function database choice" — verbatim)
- Add `_write_dockerfile(project_dir: Path, stack_family: str)` and `_write_ci_workflow(project_dir: Path, stack_family: str)` as new helpers — same shape as `write_drizzle_files`: read template from `assets/`, call `atomic_write(project_dir / "<dest>", content)`. Use `Path(__file__).resolve().parent.parent / "assets" / ...` to resolve template paths (matches RESEARCH `## Code Examples` `_compose_gitignore` pattern at line 860).
- New helpers `_compose_gitignore(project_dir, stack_family)` and `_install_gitleaks_hook(project_dir)` — also live in scaffold_dispatch.py (per RESEARCH responsibility map line 83-84) OR in gh_handoff.py (per RESEARCH `_compose_gitignore` excerpt line 862). RECOMMENDED: keep them in `gh_handoff.py` since they are stamped at the SHIP boundary (post-scaffold, just before `git init`), NOT at the create-next-app boundary; the responsibility map's claim that scaffold_dispatch owns them is contradicted by the researcher's own code excerpt. PLANNER MUST PICK ONE.
- ALL new template content lives in `assets/<subdir>/<file>` and is read with `(ASSETS / "<file>").read_text(encoding="utf-8")` — do NOT inline as Python f-strings (RESEARCH Anti-Pattern: "Hand-writing the Dockerfile in Python f-strings")
- Hook into `scaffold_web()` ONLY at the `write_drizzle_files()` boundary (line 174); add new calls AFTER it in the same function. Do NOT introduce new dispatch points.

**Diverge here:**
- DO NOT promote existing `_DB_TS` / `_DRIZZLE_CONFIG` / `_ENV_EXAMPLE` to assets/ — they are < 10 lines and Phase 3 already shipped them inline. Only the NEW templates (Dockerfile multi-stage, CI workflow, gitignore composition, gitleaks) move to `assets/` because each is > 15 lines or > 1 stack family
- `_pick_database` returns "postgres" or "sqlite" — but the SCL-02 success criterion only fires the existing `compose.yaml` write when the result is "postgres". When `_pick_database()` returns "sqlite", scaffold_dispatch must SKIP the `compose.yaml` write entirely (existing code unconditionally writes it on line 127 — this is the bug Plan 06-Track-B must fix)

---

### `assets/gitignore-templates/{base,node,python}.gitignore` (NEW template-assets)

**Analog:** `_ENV_EXAMPLE = "DATABASE_URL=postgresql://myapp:myapp@localhost:5432/myapp\n"` (`scaffold_dispatch.py:52`)

**Patterns to replicate:**
- Static text file under `assets/` — no placeholders, no substitution. Pure file copy via `read_text() → atomic_write`
- `base.gitignore` MUST contain the negative-match block from RESEARCH `## Code Examples` "`.env.example` allowlist negative match":
  ```
  .env
  .env.*
  !.env.example
  !.env.sample
  ```
- `node.gitignore` content list: `node_modules/`, `dist/`, `build/`, `.next/`, `.turbo/`, `coverage/`, `*.tsbuildinfo` (RESEARCH Standard Stack table line 136)
- `python.gitignore` content list: `__pycache__/`, `*.pyc`, `*.egg-info/`, `.venv/`, `venv/`, `.pytest_cache/`, `.mypy_cache/`, `dist/`, `build/`, `*.egg` (RESEARCH Standard Stack table line 137)

**Diverge here:**
- Researcher prompt names the files `base.gitignore` / `node.gitignore` / `python.gitignore`; the responsibility map and code-example ASSETS path call the directory `gitignore-templates/` and the common file `common.gitignore`. RECOMMENDED: use the responsibility-map name (`common.gitignore`) since the in-code reference at RESEARCH line 868 reads `(ASSETS / "common.gitignore")`. Planner must reconcile to `common.gitignore` when wiring `_compose_gitignore`

---

### `assets/gitleaks/.pre-commit-config.yaml` and `assets/gitleaks/.gitleaks.toml` (NEW template-assets)

**Analog:** `_COMPOSE_YAML` constant in `scaffold_dispatch.py:55-70`

**Patterns to replicate:**
- Static YAML/TOML file with NO placeholders; pinned to gitleaks v8.30.1 (RESEARCH Pattern 2 line 449-457)
- `.pre-commit-config.yaml` exact content (verbatim from RESEARCH Pattern 2):
  ```yaml
  repos:
    - repo: https://github.com/gitleaks/gitleaks
      rev: v8.30.1
      hooks:
        - id: gitleaks
  ```
- `.gitleaks.toml` allowlist entries (RESEARCH Pattern 2 line 459-474): permissive starter that allowlists `.env.example`, `README.md`, `docs/*.md`
- File destination in built repo: `<project_dir>/.pre-commit-config.yaml` and `<project_dir>/.gitleaks.toml` (NOT under `assets/gitleaks/`); the asset-side path is just the SOURCE template

**Diverge here:**
- DO NOT auto-install the hook into `<project_dir>/.git/hooks/pre-commit`. Per RESEARCH Pitfall 2 + Anti-Pattern "Auto-installing pre-commit hooks during scaffold", the hook activation is documented in the README (`pre-commit install`) and run by the user post-clone

---

### `assets/ci/{node,python}.yml` (NEW template-assets)

**Analog:** `_COMPOSE_YAML` constant — same pattern (static YAML, no placeholders)

**Patterns to replicate:**
- `node.yml` exact content from RESEARCH Pattern 4 (lines 508-533) — `actions/checkout@v6`, `pnpm/action-setup@v4` BEFORE `actions/setup-node@v4`, `cache: 'pnpm'`, `pnpm install --frozen-lockfile`, `pnpm test`
- `python.yml` shape per RESEARCH Standard Stack table line 141: `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v6`
- Single workflow file per repo (SCL-04 success criterion: EXACTLY ONE `.github/workflows/*.yml` file)
- `on: pull_request: branches: [main]` trigger only (no `push` trigger — keeps CI cost down per RESEARCH alternatives table)

**Diverge here:**
- DO NOT include `cache: 'pnpm'` AHEAD of the `pnpm/action-setup` step — RESEARCH `## Anti-Patterns to Avoid` notes that reversed order silently breaks caching

---

### `assets/readme-template.md` (NEW template-asset)

**Analog:** `_DRIZZLE_CONFIG` (`scaffold_dispatch.py:36-49`) — placeholder-bearing template with `{{NAME}}` substitution shape; combined with `_write_verification_md` (`gsd_driver.py:145-178`) which builds an entire markdown doc by f-string substitution.

**`_write_verification_md` excerpt (`gsd_driver.py:145-178`)**:
```python
def _write_verification_md(project_root: Path, current_phase: int) -> None:
    now_iso = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""\
# Phase {current_phase} Verification

**Generated:** {now_iso}
**Phase:** {current_phase}

## Falsifiable Success Criteria
...
"""
    ver_path = project_root / ".planning" / "osbuilder" / "VERIFICATION.md"
    _atomic_write(ver_path, content)
```

**Patterns to replicate:**
- Template uses `{{placeholder_name}}` (double-brace) syntax for runbook_writer's `str.replace` substitution — NOT Python f-strings (the asset is plain text on disk)
- Required sections per SHIP-02: `# {{project_name}}`, `## Quick Start` (≤ 5 commands), `## Requirements`, `## Configuration`, `## Development`, `## Tests`, `## How OSBuilder built this` (Phase 5 Plan 05-05 already populates this section via `/gsd-docs-update`)
- Quick Start section MUST include a `pre-commit install` line (RESEARCH Pitfall 2 mitigation)
- Placeholders to provide: `project_name`, `stack_summary`, `run_command`, `install_command`, `test_command`, `repo_url`, `playbook` — all sourced from state.md by runbook_writer

**Diverge here:**
- Unlike `_write_verification_md`, the runbook is NOT regenerated on every phase advance — it is stamped ONCE during the ship step. Make it idempotent: if `<project_dir>/README.md` already exists AND contains the marker `<!-- OSBuilder runbook -->`, skip the write (matches the `_compose_gitignore` idempotency pattern at RESEARCH line 879)

---

### `scripts/runbook_writer.py` (NEW orchestrator-script)

**Analog:** `scripts/scaffold_dispatch.py` `write_drizzle_files()` (lines 122-127) + `gsd_driver.py` `_write_verification_md()` (lines 145-178)

**Patterns to replicate:**
- Module header: same docstring/`__future__`/`try _fe import` shape as gh_handoff.py (above)
- Public API: `def write_readme(project_dir: Path, project_root: Path) -> Path` — reads state.md via `subprocess.run([sys.executable, str(STATE_WRITER), "read", "--format", "json", "--project-root", ...])` (verbatim from `gsd_driver.py:107-112` `_read_state`)
- Read template from `Path(__file__).resolve().parent.parent / "assets" / "readme-template.md"`
- Substitute placeholders via `content.replace("{{name}}", value)` for each field — NOT `str.format()` (Phase 5 friendly_error uses `_safe_format` for ctx interpolation; runbook is simpler — the placeholder set is closed and known)
- `atomic_write(project_dir / "README.md", composed)` — duplicate the atomic_write helper verbatim (do NOT import; project policy D-05)
- argparse: `python3 runbook_writer.py write --project-root <path> --project-dir <path>`

**Diverge here:**
- DO NOT route through the LLM — runbook is pure deterministic stamping. The "How OSBuilder built this" LLM section is written by Phase 5's `/gsd-docs-update` flow already; runbook_writer ONLY produces the deterministic Quick Start + Requirements + Tests sections (RESEARCH Track C lines 108-110 — "composition is the pattern: deterministic Quick Start + LLM polish for the dev-team-metaphor section")

---

# Track C — README runbook (covered above under `runbook_writer.py` and `assets/readme-template.md`)

(See Track B section above for both files.)

---

# Track D — Refusal mechanics + production-ready slash commands

### `scripts/intake_handler.py` (EXTEND — refusal gate at `phase_step == 1`)

**Analog:** self — existing `_validate_project_name()` + `_SECRET_PATTERNS` membership check

**Existing pattern (`intake_handler.py:33-34`, `183-198`)**:
```python
_SECRET_PATTERNS = ("api_key", "password", "token", "database_url=postgresql://")

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
```

**RESEARCH Pattern 6 (`gsd_driver.py` extension — verbatim from `06-RESEARCH.md:570-601`)**:
```python
REFUSE_KEYWORDS = (
    "kubernetes", "k8s", "helm", "service mesh",
    "service-mesh", "microservice", "microservices",
    "istio", "linkerd", "consul",
)

def _check_refuse_list(project_root: Path, state: dict) -> bool:
    if state.get("production_ready", "false") == "true":
        return False
    spec_path = project_root / ".planning" / "osbuilder" / "derived_spec.md"
    if not spec_path.exists():
        return False
    spec = spec_path.read_text(encoding="utf-8").lower()
    for kw in REFUSE_KEYWORDS:
        if kw in spec:
            _write_field(project_root, "last_failure", f"refused: {kw}")
            _emit("architect", "refusal", "fail", detail=f"detected '{kw}' in spec")
            sys.stderr.write(_load_refusal_copy(kw))
            return True
    return False
```

**Patterns to replicate:**
- Same `for kw in TUPLE: if kw in lower_text` membership-check shape as `_SECRET_PATTERNS` lookup (line 193)
- ALWAYS check `state.get("production_ready", "false") == "true"` FIRST and short-circuit-return False (the flag is the bypass)
- On hit: write `last_failure="refused: <kw>"` via the existing state_writer subprocess pattern; emit narration via `_emit("architect", "refusal", "fail", ...)`; load copy from `references/refuse-list.md` (NOT inline)
- The refusal gate runs at `phase_step == 1` (architect / `/gsd-plan-phase` boundary) per RESEARCH line 567 — researcher prompt says intake_handler also runs the gate. RECOMMENDED: put the actual gate function in `intake_handler.py` (where derived_spec.md is FIRST written) and have `gsd_driver.py:_emit_next_command` call into it at phase_step==1. Planner picks the exact wiring.

**Diverge here:**
- The existing `_SECRET_PATTERNS` check exits with stderr write — refusal must NOT exit non-zero in the same way. It must: (a) write `last_failure`, (b) print the friendly refusal copy, (c) return a sentinel that gsd_driver.py interprets as "do not advance phase_step". Treating it like a fatal error would break the resume protocol.
- Whitespace-bounded match: `if " kubernetes " in (" " + spec + " ")` to avoid false positives where `kubernetes` appears inside another word (RESEARCH Pitfall 10). Researcher's verbatim code uses naive `if kw in spec:` — the planner SHOULD harden this.

---

### `scripts/state_writer.py` (EXTEND — `ALLOWED_FIELDS` adds 5 fields)

**Analog:** self — existing Phase 3/4/5 additive pattern at `state_writer.py:36-50`

**Existing additive pattern (`state_writer.py:36-50`)**:
```python
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    "project_path",    # absolute path to scaffolded project on disk
    "stack_choices",   # JSON string: researched/confirmed stack (RES-02)
    "stack_overrides", # JSON string: --advanced user overrides (RES-04)
    # Phase 4 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3)
    "gsd_phase_count",
    "failure_class",
    "escalation_log",
    # Phase 5 additions — ALLOWED only, NOT REQUIRED (same pattern as Phase 3/4)
    "mode",
    "tutor_enabled",
    "humanizer_score",
    "build_log_path",
    "tech_writer_sub_step",
}
```

**Patterns to replicate:**
- Add 5 new entries inside the same set literal: `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`, `production_ready`
- Add a `# Phase 6 additions — ALLOWED only, NOT REQUIRED` comment header above them (mirrors the Phase 3/4/5 comment pattern)
- DO NOT add to `REQUIRED_FIELDS` — additive only, so Phase 1-5 state.md files still pass `validate` (this is the explicit invariant from RESEARCH line 91 + `state_writer.py:34`)

**Diverge here:** none — this is the canonical additive extension. Mirror exactly.

---

### `scripts/production_phase_writer.py` (NEW orchestrator-script)

**Analog:** `scripts/gsd_driver.py` `_run_tech_writer_step` (`gsd_driver.py:300-388`) and `emit_next_command` print-to-stdout pattern

**`_run_tech_writer_step` excerpt — slash-command emission pattern (`gsd_driver.py:326-356`)**:
```python
if sub_step == "":
    _emit("tech-writer", "generate-readme", "start")
    planning_dir = project_root / ".planning" / "osbuilder"
    planning_dir.mkdir(parents=True, exist_ok=True)
    readme_context_path = planning_dir / "readme-context.md"
    readme_context_path.write_text(...)
    print(f"/gsd-docs-update @{readme_context_path}")
    _write_field(project_root, "tech_writer_sub_step", "awaiting-humanizer")
    return 0
```

**Patterns to replicate:**
- Read state.md via `_read_state(project_root)` (verbatim from `gsd_driver.py:101-112`); check `state.get("production_ready", "false") == "true"`
- If true: iterate over a hardcoded tuple of 7 phase names (`observability`, `migrations`, `healthchecks`, `secret-manager`, `sentry`, `rate-limiting`, `backups` — RESEARCH lines 290-296) and `print(f"/gsd-add-phase {name}")` for each — exactly the `print(f"/gsd-docs-update @...")` shape from line 353
- If false: print nothing, return 0
- argparse: a single `emit` subcommand with `--project-root`

**Diverge here:**
- Unlike `_run_tech_writer_step`, this emits MULTIPLE slash commands in ONE invocation (the test SCL-06 asserts exactly 7 lines of stdout). `gsd_driver.py:emit_next_command` always emits exactly one; this one emits 7. That is the whole point — embrace the divergence.
- DO NOT bump `phase_step` after emission — this script is ANCILLARY to the phase loop, not a step in it. It is invoked from gsd_driver.py at the ship boundary AFTER the phase loop has already terminated.

---

# Test files (Wave 0 RED stubs)

### `scripts/tests/test_gh_handoff.py` (NEW test-stub)

**Analog:** `scripts/tests/test_scaffold_dispatch.py`

**Lazy-import fixture pattern (`test_scaffold_dispatch.py:16-22`)**:
```python
@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet created."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet created (Wave 1 target)")
```

**fake_shell mock pattern (`test_scaffold_dispatch.py:42-66`)**:
```python
def test_scaffold_cmd_flags(sd, fake_shell, fake_which, tmp_path):
    """SCAF-06: scaffold_web() runs create-next-app with the correct flags."""
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    scaffold_calls = [s for s in signatures if "next-app@latest" in s]
    assert len(scaffold_calls) == 1
    cmd = scaffold_calls[0]
    assert "--typescript" in cmd
```

**Patterns to replicate:**
- Lazy-import fixture named `gh` (parallel to `sd`, `sw`, `ih`, `fc`, `rv`, `fe`)
- Use existing `fake_shell` fixture (in `conftest.py:80-84`) and `fake_shell.program("gh repo create", returncode=0, stdout="...")` to canned-response gh
- Test names map to SHIP-* requirements: `test_ship_runs_private_create`, `test_failure_modes_friendly`, `test_auth_drift_friendly` (verbatim from RESEARCH Phase Requirements → Test Map line 758-765)
- For each failure mode (gh-not-installed, gh-auth-not-authenticated, gh-token-expired, repo-name-collision, network-failure): `fake_shell.program("gh ...", returncode=N, stderr="...")` then assert stderr captured contains friendly_error fields (title, what_to_do, copy_paste_command). Mirror `test_friendly_error.py:31-46`'s assertion shape.

**Diverge here:**
- `test_scaffold_dispatch.py` uses `fake_which` for `pnpm` resolution; gh_handoff.py uses subprocess directly without `shutil.which` first — so omit `fake_which` for these tests
- Add a SKIP marker `@pytest.mark.skipif(shutil.which("gh") is None)` for any test that wants to run live against `gh` (RESEARCH line 841-847 Option B — opt-in `pytest -m live_gh` marker)

---

### `scripts/tests/test_runbook_writer.py` (NEW test-stub)

**Analog:** `test_scaffold_dispatch.py::test_db_ts_written` (lines 93-107)

**Pattern excerpt**:
```python
def test_db_ts_written(sd, fake_which, tmp_path):
    project_dir = tmp_path / "my-app"
    project_dir.mkdir()
    sd.write_drizzle_files(project_dir)
    db_ts = project_dir / "src" / "lib" / "db.ts"
    assert db_ts.exists()
    content = db_ts.read_text(encoding="utf-8")
    assert "drizzle-orm/postgres-js" in content
    assert "process.env.DATABASE_URL" in content
```

**Patterns to replicate:**
- Lazy-import fixture `rw` for `runbook_writer`
- Use `tmp_project_root` + `state_md_path` + `writer` (existing conftest fixtures) to seed a fake state.md, then call `rw.write_readme(...)` and assert section-presence on the resulting README.md
- Assert each required H2 section literal (`"## Quick Start" in content`, `"## Requirements" in content`, etc.)
- Assert all placeholders are substituted (`"{{project_name}}" not in content`, `"{{run_command}}" not in content`)

**Diverge here:**
- Use the new `fake_state_md` fixture (added to conftest in Wave 0) instead of going through subprocess state_writer — runbook_writer reads JSON, so the test can directly write a JSON state.md file

---

### `scripts/tests/test_scaffold_extensions.py` (NEW test-stub)

**Analog:** `test_scaffold_dispatch.py` (extends the same module)

**Patterns to replicate:**
- Same `sd` lazy-import fixture (import from existing test_scaffold_dispatch.py module's pattern, do NOT redefine)
- Tests for SCL-01..04: `test_gitignore_composition`, `test_gitleaks_config`, `test_env_example_committed`, `test_pick_database`, `test_db_default_per_playbook`, `test_docker_artifacts`, `test_one_ci_workflow`, `test_gitleaks_blocks_real_secret` (names verbatim from RESEARCH Phase Requirements → Test Map)
- For `test_gitleaks_blocks_real_secret`: use the `@pytest.mark.skipif(shutil.which("pre-commit") is None or shutil.which("gitleaks") is None, reason=...)` marker — pattern verbatim from RESEARCH line 823-826
- File-content assertions use `(project_dir / "compose.yaml").read_text()` and check substrings — same shape as `test_compose_yaml_written` (line 148-163)

**Diverge here:**
- `test_pick_database` is a PURE function test — no tmp_path, no fake_shell, no fake_which. Just `assert sd._pick_database("web", "multi-user") == "postgres"`. Diverges from the existing module pattern.

---

### `scripts/tests/test_refusal.py` (NEW test-stub)

**Analog:** `scripts/tests/test_intake.py` (pattern detection on derived_spec.md content) + `scripts/tests/test_state_writer.py::test_input_validation` (subprocess + assertion on state.md write)

**`test_intake.py` lazy-import fixture (verbatim shape)**:
```python
@pytest.fixture
def ih():
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet created (Wave 1 target)")
```

**Patterns to replicate:**
- Use `ih` (intake_handler) lazy-import fixture if the gate lives there, OR `gd` (gsd_driver) if it lives in gsd_driver.py — either way, copy the lazy-import pattern verbatim
- Two fixtures: `derived_spec_with_k8s.md` and `derived_spec_clean.md` (markdown files in `scripts/tests/fixtures/`); test loads them via `Path(__file__).parent / "fixtures" / "derived_spec_with_k8s.md"` and writes them to `tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"` before invoking the gate
- Test names mapping to SCL-05: `test_kubernetes_refused`, `test_clean_spec_passes`, `test_production_ready_bypass`, `test_refusal_copy_mentions_opt_in` (the last one greps `references/refuse-list.md` content for `"production-ready"` literal)
- After invoking the gate: read state.md via the `writer` fixture's read mode and assert `last_failure` value matches `^refused: kubernetes` regex (RESEARCH SCL-05 success criterion)

**Diverge here:**
- Unlike intake tests which test the parse_paragraph path, refusal tests stage a derived_spec.md directly on disk — skip the parse step entirely. The gate consumes the file, doesn't parse it.

---

### `scripts/tests/test_production_ready.py` (NEW test-stub)

**Analog:** `test_state_writer.py::test_input_validation` (lines 98-119) — subprocess invocation with assertion on returncode/stdout

**Pattern excerpt (`test_state_writer.py:98-119`)**:
```python
def test_input_validation(sw, tmp_project_root, writer):
    writer("init", "--goal", "ok", project_root=tmp_project_root)
    state_writer_file = sw.__file__ or str(_state_writer_path())
    bad_newline = subprocess.run(
        [sys.executable, state_writer_file,
         "--project-root", str(tmp_project_root),
         "write", "--field", "goal", "--value", "line1\nline2"],
        capture_output=True, text=True,
    )
    assert bad_newline.returncode != 0
```

**Patterns to replicate:**
- Lazy-import `pp` for `production_phase_writer`
- Use `writer` fixture to seed state.md with `production_ready=true`, then run `subprocess.run([sys.executable, str(production_phase_writer_path), "emit", "--project-root", str(tmp_project_root)], capture_output=True, text=True)` and `assert result.stdout.count("/gsd-add-phase") == 7`
- Negative test: same setup with `production_ready=false` (or omitted) → `assert result.stdout.strip() == ""`

**Diverge here:**
- Unlike `test_state_writer.py` which only asserts return-code, `test_production_ready` asserts on STDOUT content (the slash-command lines). Use `result.stdout.splitlines()` and count `/gsd-add-phase` occurrences (RESEARCH SCL-06 success criterion).

---

### `scripts/tests/conftest.py` (EXTEND — new fixtures)

**Analog:** self — existing fixtures `tmp_project_root`, `state_md_path`, `writer`, `fake_shell`, `fake_which` (`conftest.py:17-92`)

**Patterns to replicate:**
- New fixture `fake_built_app(tmp_path) -> Path`: creates a tmp_path subdir with `package.json` (or `pyproject.toml`), runs `subprocess.run(["git", "init", "-b", "main"], cwd=...)`, returns the dir. Mirror RESEARCH `test_gitleaks_blocks_real_secret` fixture pattern (line 813-821).
- New fixture `fake_state_md(tmp_project_root) -> Path`: builder fixture that takes `**fields` kwargs, seeds them into state.md via the existing `writer` fixture, returns the state_md_path. Use `pytest.fixture(scope="function")` so each test gets a fresh state.md.
- New fixture `mock_gh_subprocess`: extends the existing `fake_shell` with parameterized canned responses for the 5 gh failure modes (returncode + stderr per mode). Same shape as `fake_shell.program(...)` but pre-loaded with the dictionary of failure modes from RESEARCH lines 245-249.
- New fixture `mock_git_subprocess`: similar — clean tree / dirty tree / no-init scenarios for `git status --porcelain` and `git remote get-url origin`

**Diverge here:**
- ADDITIVE only — do NOT modify or rename existing fixtures. The Phase 5 test suite (127 tests) imports them; renaming is a regression vector.

---

### `scripts/tests/fixtures/derived_spec_with_k8s.md` (NEW fixture)

**Analog:** `references/playbooks/web.md` lines 50-58 (existing refuse-list block) + `intake_handler._render_derived_spec()` output format

**Patterns to replicate:**
- Use the exact `_render_derived_spec()` output format (`intake_handler.py:95-122`) so the file looks like a real derived_spec.md
- Embed at least one refuse keyword in the body (e.g., the `**Goal:**` line: `**Goal:** Build a multi-tenant SaaS with Kubernetes orchestration and microservices`)

### `scripts/tests/fixtures/derived_spec_clean.md` (NEW fixture)

**Analog:** same — `intake_handler._render_derived_spec()` output

**Patterns to replicate:**
- Same format, but goal/features contain NO refuse keywords. Test fixture for the negative case (gate must NOT fire).

---

# Shared Patterns

### Authentication / Auth (N/A)

OSBuilder has no auth surface — all subprocess calls run as the local user. The closest analog is the `gh auth status` PREFLIGHT in `gh_handoff.py` (covered above under Track A).

### Error Handling

**Source:** `scripts/scaffold_dispatch.py:141-171` + `scripts/friendly_error.py:276-302` `translate()`
**Apply to:** every NEW production script (`gh_handoff.py`, `runbook_writer.py`, `production_phase_writer.py`)

**Excerpt — error-routing wrapper that EVERY new script must adopt verbatim**:
```python
try:
    result = subprocess.run([...], shell=False, capture_output=True, text=True)
    if result.returncode != 0:
        raw = result.stderr or f"exit {result.returncode}"
        if _fe is not None:
            msg = _fe.translate(raw, ctx={"tool": "gh"})
            sys.stderr.write(
                f"## {msg.title}\n{msg.what_broke}\n\n"
                f"**What to do:** {msg.what_to_do}\n"
            )
            if msg.copy_paste:
                sys.stderr.write(f"\n  {msg.copy_paste}\n")
        else:
            sys.stderr.write(f"OSBuilder: failed: {raw}\n")
        return 1
except (FileNotFoundError, OSError) as e:
    # tool not on PATH → friendly_error route
    ...
```

### Atomic Write

**Source:** `scripts/scaffold_dispatch.py:84-96` (and verbatim duplicates in `state_writer.py:121-133`, `gsd_driver.py:84-96`, `intake_handler.py:80-92`, `preflight_check.py:65-77`)
**Apply to:** all new production scripts that write files (`gh_handoff.py`, `runbook_writer.py`, `production_phase_writer.py`, `scaffold_dispatch.py` extensions)

**Excerpt**:
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

**Project policy D-05:** DUPLICATE this helper into every new script. Do NOT factor it into a shared module. (See `preflight_check.py:63` comment "duplicated from state_writer.py:100-112 per D-05".)

### Project-Root Resolution

**Source:** `scripts/scaffold_dispatch.py:72-81` (verbatim duplicates in 5 other scripts)
**Apply to:** all new scripts that take `--project-root`

**Excerpt**:
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

### State.md Writes via state_writer Subprocess

**Source:** `scripts/scaffold_dispatch.py:222-232` and `gsd_driver.py:123-130` `_write_field()`
**Apply to:** every NEW script that needs to set state.md fields (`gh_handoff.py` writes `repo_visibility`, `repo_url`, `gh_auth_status`, `pre_commit_installed`)

**Excerpt (`gsd_driver.py:123-130`)**:
```python
def _write_field(project_root: Path, field: str, value: str) -> None:
    """Write a single field to state.md via state_writer write subcommand."""
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "write",
         "--field", field, "--value", value,
         "--project-root", str(project_root)],
        shell=False, check=True,
    )
```

**Project policy:** never edit state.md inline — always go through state_writer subprocess so its allowlist + atomicity guards apply. T-04-02-01 (integer parse) and T-04-02-02 (no value interpolation in slash commands) are enforced this way.

### Lazy-Import Test Fixture

**Source:** `scripts/tests/test_scaffold_dispatch.py:16-22` (and verbatim duplicates in `test_state_writer.py:25-31`, `test_intake.py:20-26`, `test_friendly_error.py:19-25`, `test_failure_classifier.py`)
**Apply to:** every NEW test file in Wave 0

**Excerpt**:
```python
@pytest.fixture
def gh():  # rename per module: rw, pp, ih, etc.
    """Lazy import of scripts/gh_handoff.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("gh_handoff")
    except ImportError:
        pytest.skip("gh_handoff module not yet created (Wave 1 target)")
```

**Why:** ensures Wave 0 RED stubs COLLECT (not error) when their target module is not yet implemented. The Wave 0 acceptance gate counts collected tests; pytest.importorskip at module level removes the entire module from collection.

---

## No Analog Found

None. All 26 NEW/EXTENDED files have a strong (exact or role-match) analog in the existing codebase. Every Track-A and Track-D production script mirrors `scaffold_dispatch.py` shape; every test mirrors an existing test module; every template-asset mirrors the inline `_DB_TS`/`_COMPOSE_YAML` constant pattern (now promoted to files because they grow).

---

## Metadata

**Analog search scope:**
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/scripts/` (10 production scripts)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/scripts/tests/` (18 existing test files + conftest)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/references/` (friendly-errors, playbooks, preflight, roles)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/assets/` (currently empty — first inhabitants land in Phase 6)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/SKILL.md`

**Files scanned:** 17 (scaffold_dispatch.py, state_writer.py, friendly_error.py, registry_verify.py, intake_handler.py, failure_classifier.py, preflight_check.py, narration.py, gsd_driver.py, conftest.py, test_scaffold_dispatch.py, test_state_writer.py, test_friendly_error.py, test_intake.py, dictionary.yaml, web.md, preflight/README.md, SKILL.md)

**Pattern extraction date:** 2026-05-01

**Open questions for the planner:**
1. Where do `_compose_gitignore()` and `_install_gitleaks_hook()` live — in `gh_handoff.py` (matches RESEARCH `## Code Examples` ASSETS path at line 860, where the function is shown defined) or in `scaffold_dispatch.py` (matches RESEARCH `## Architectural Responsibility Map` at line 83-84)? RECOMMENDED: gh_handoff.py, since the stamping happens at the SHIP boundary (post-scaffold, pre-commit), and Track B's scaffold extensions are about Dockerfile/CI workflow only.
2. The 5 `references/friendly-errors/gh-*.md` files — append to `dictionary.yaml` (loader-compatible) or keep as standalone .md (require new build step)? RECOMMENDED: append to dictionary.yaml; keep .md files as Markdown-form expansion docs only.
3. Asset directory naming — `gitignore-templates/common.gitignore` (RESEARCH responsibility map) vs `gitignore-templates/base.gitignore` (researcher prompt) — pick one and use consistently. RECOMMENDED: `common.gitignore` (matches the in-code reference at RESEARCH line 868).
