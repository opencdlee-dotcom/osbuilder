---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
reviewed: 2026-04-30T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - references/playbooks/web.md
  - references/question-bank.md
  - references/stack-menu.md
  - scripts/intake_handler.py
  - scripts/scaffold_dispatch.py
  - scripts/stack_researcher.py
  - scripts/state_writer.py
  - scripts/tests/test_intake.py
  - scripts/tests/test_scaffold_dispatch.py
  - scripts/tests/test_stack_researcher.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-30T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed four Python scripts (intake_handler, scaffold_dispatch, stack_researcher, state_writer), their three test files, and three reference documents (web playbook, question-bank, stack-menu). The scripts are generally well-structured with consistent patterns: atomic file writes, input allowlists, path-traversal guards, and graceful subprocess error handling.

One critical data-loss bug exists in `state_writer.py`: the `render_state_md` function only serializes the 10 required fields, silently dropping the three optional allowed fields (`project_path`, `stack_choices`, `stack_overrides`) on every write. This means sequential writes to these optional fields corrupt each other. Three warnings cover: unpinned `pnpm` installation in `scaffold_dispatch.py`, silently swallowed `pnpm add` failures, and a misleading inline comment. Two info items cover a redundant test call pattern and a minor inaccuracy in the stack-menu comment.

---

## Critical Issues

### CR-01: Optional state fields silently dropped on every write

**File:** `scripts/state_writer.py:88`
**Issue:** `render_state_md` iterates only `REQUIRED_FIELDS` (the 10 original fields). The three optional allowed fields — `project_path`, `stack_choices`, and `stack_overrides` — are never written back. Because every `write_state` call goes through `render_state_md`, any value previously stored in those fields is lost the moment any other field is updated. For example: after `state_writer.py write --field project_path --value /some/path`, a subsequent `state_writer.py write --field stack_choices --value '{...}'` silently erases `project_path`.

This is confirmed by the data flow:
1. `_cmd_write` calls `read_state(path)` — `parse_state_md` reads all `key: value` lines including `project_path` into `fields`
2. `fields[args.field] = args.value` — updates one key
3. `write_state(path, fields)` → `render_state_md(fields)` — only iterates `REQUIRED_FIELDS`, never writing the optional fields back

**Fix:**
```python
def render_state_md(fields: dict) -> str:
    """Render state.md. Writes required fields first, then any extra allowed fields."""
    lines = ["# OSBuilder State", ""]
    for f in REQUIRED_FIELDS:
        lines.append(f"{f}: {fields.get(f, '')}")
    # Persist optional allowed fields so sequential writes don't erase each other
    extras = sorted(ALLOWED_FIELDS - set(REQUIRED_FIELDS))
    for f in extras:
        if f in fields:
            lines.append(f"{f}: {fields[f]}")
    lines.append(f"updated_at: {fields.get('updated_at', _now_iso())}")
    return "\n".join(lines) + "\n"
```

---

## Warnings

### WR-01: pnpm installed at @latest instead of pinned version

**File:** `scripts/scaffold_dispatch.py:106`
**Issue:** `ensure_pnpm()` installs `pnpm@latest` when pnpm is absent, but the entire codebase pins pnpm at version `10.33.2` (web.md, stack-menu.md, _WEB_DEFAULTS). A fresh CI or user machine that triggers `ensure_pnpm()` gets an unpinned pnpm, which can break `create-next-app` invocation or produce a different `pnpm-lock.yaml` format than expected.

**Fix:**
```python
_PNPM_VERSION = "10.33.2"  # keep in sync with stack-menu.md and _WEB_DEFAULTS

def ensure_pnpm() -> None:
    """Install pnpm via npm if absent (Pitfall 5 mitigation)."""
    if shutil.which("pnpm") is not None:
        return
    subprocess.run(
        ["npm", "install", "-g", f"pnpm@{_PNPM_VERSION}"],
        shell=False, check=True,
    )
```

### WR-02: pnpm add failures silently swallowed

**File:** `scripts/scaffold_dispatch.py:143-150`
**Issue:** Both `pnpm add drizzle-orm postgres` and `pnpm add -D drizzle-kit` are invoked with `check=False` and no error logging. If either command fails (e.g., network error, registry outage), the scaffold completes successfully from the caller's perspective, but the project is left without its core dependencies. The user gets a broken project with no diagnostic message.

**Fix:**
```python
result = subprocess.run(
    ["pnpm", "add", "drizzle-orm", "postgres"],
    cwd=str(project_dir), shell=False, check=False,
)
if result.returncode != 0:
    sys.stderr.write(
        f"OSBuilder: warning — pnpm add drizzle-orm postgres failed "
        f"(exit {result.returncode}). Run manually in {project_dir}\n"
    )

result = subprocess.run(
    ["pnpm", "add", "-D", "drizzle-kit"],
    cwd=str(project_dir), shell=False, check=False,
)
if result.returncode != 0:
    sys.stderr.write(
        f"OSBuilder: warning — pnpm add -D drizzle-kit failed "
        f"(exit {result.returncode}). Run manually in {project_dir}\n"
    )
```

### WR-03: Inline comment incorrectly describes compose.yaml password length

**File:** `scripts/scaffold_dispatch.py:45`
**Issue:** The comment `# Password is 5 chars — placeholder only, not a real credential (T-3-04)` refers to the `_ENV_EXAMPLE` password (`myapp`, 5 chars), but it is placed immediately above the `_ENV_EXAMPLE` constant and is relied upon by the T-3-04 threat model. However, `_COMPOSE_YAML` uses `POSTGRES_PASSWORD: myapp_secret` (12 chars), not `myapp`. A future reviewer auditing this comment against the compose template will find the count wrong, undermining confidence in the security annotation.

**Fix:** Correct the comment and clarify which constant it applies to:
```python
# _ENV_EXAMPLE: DATABASE_URL uses password "myapp" (5 chars) — placeholder only (T-3-04)
_ENV_EXAMPLE = "DATABASE_URL=postgresql://myapp:myapp@localhost:5432/myapp\n"

# _COMPOSE_YAML: POSTGRES_PASSWORD uses "myapp_secret" — dev-only placeholder (T-3-04)
_COMPOSE_YAML = """\
...
```

---

## Info

### IN-01: test_drizzle_deps_added pre-populates project dir unnecessarily

**File:** `scripts/tests/test_scaffold_dispatch.py:72-74`
**Issue:** The test creates `tmp_path / "my-app"` and calls `write_drizzle_files()` on it at lines 72-74, then tests `scaffold_web("my-app2", tmp_path)` — a different project name. The first three lines are dead setup: they write files into `my-app` but the test assertion only inspects subprocess calls from `scaffold_web("my-app2", ...)`. The extra `write_drizzle_files` call also adds file-write entries to `fake_shell.calls` if it ever invoked subprocess (it does not), so it's harmless but misleading.

**Fix:** Remove the dead setup, or rename to make the two project names match:
```python
def test_drizzle_deps_added(sd, fake_shell, fake_which, tmp_path):
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create next-app@latest", returncode=0, stdout="")
    sd.scaffold_web("my-app", tmp_path)
    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    drizzle_calls = [s for s in signatures if "drizzle" in s]
    assert len(drizzle_calls) >= 1, ...
```

### IN-02: stack_researcher.py imports re inside a function

**File:** `scripts/stack_researcher.py:56`
**Issue:** `import re` appears inside `_read_stack_menu()` rather than at the module top level. This is inconsistent with the rest of the stdlib imports at the top of the file and makes the dependency non-obvious to readers. Python caches module imports so there is no runtime cost, but the style is inconsistent.

**Fix:** Move `import re` to the module-level import block alongside the other stdlib imports.

---

_Reviewed: 2026-04-30T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
