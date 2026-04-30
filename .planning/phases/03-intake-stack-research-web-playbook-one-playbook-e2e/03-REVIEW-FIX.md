---
phase: 03-intake-stack-research-web-playbook-one-playbook-e2e
fixed_at: 2026-04-30T19:13:39Z
review_path: .planning/phases/03-intake-stack-research-web-playbook-one-playbook-e2e/03-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-04-30T19:13:39Z
**Source review:** .planning/phases/03-intake-stack-research-web-playbook-one-playbook-e2e/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (1 Critical, 3 Warning)
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: Optional state fields silently dropped on every write

**Files modified:** `scripts/state_writer.py`
**Commit:** 6a6ae32
**Applied fix:** Replaced the `render_state_md` docstring and body to add an `extras` loop that iterates `sorted(ALLOWED_FIELDS - set(REQUIRED_FIELDS))` and writes any of those keys that are present in `fields`. This ensures `project_path`, `stack_choices`, and `stack_overrides` survive every `write_state` call, preventing sequential-write data loss.

### WR-01: pnpm installed at @latest instead of pinned version

**Files modified:** `scripts/scaffold_dispatch.py`
**Commit:** bfe96f7
**Applied fix:** Added module-level constant `_PNPM_VERSION = "10.33.2"` (with sync comment) and replaced the hardcoded `"pnpm@latest"` string in `ensure_pnpm()` with `f"pnpm@{_PNPM_VERSION}"`.

### WR-02: pnpm add failures silently swallowed

**Files modified:** `scripts/scaffold_dispatch.py`
**Commit:** bfe96f7
**Applied fix:** Captured the return value of both `subprocess.run` calls in `scaffold_web` and added `if result.returncode != 0` blocks that write actionable warning messages to `sys.stderr`, including the exit code and the project directory path for manual recovery.

### WR-03: Inline comment incorrectly describes compose.yaml password length

**Files modified:** `scripts/scaffold_dispatch.py`
**Commit:** bfe96f7
**Applied fix:** Split the single ambiguous comment into two distinct comments — one immediately above `_ENV_EXAMPLE` (naming it and its 5-char `"myapp"` password) and one immediately above `_COMPOSE_YAML` (naming it and its `"myapp_secret"` dev-only placeholder) — both referencing the T-3-04 threat model annotation.

---

_Fixed: 2026-04-30T19:13:39Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
