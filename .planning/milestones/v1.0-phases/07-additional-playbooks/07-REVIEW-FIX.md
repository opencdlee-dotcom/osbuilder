---
phase: 07-additional-playbooks
fixed_at: 2026-05-02T21:04:36Z
review_path: .planning/phases/07-additional-playbooks/07-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 7: Code Review Fix Report

**Fixed at:** 2026-05-02T21:04:36Z
**Source review:** .planning/phases/07-additional-playbooks/07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: Silent failure when `uv add` exits non-zero in `scaffold_ai_service` and `scaffold_cli`

**Files modified:** `scripts/scaffold_dispatch.py`
**Commit:** d682947
**Applied fix:** Both `subprocess.run(["uv", "add", ...], check=False)` calls now capture output and inspect `returncode`. On non-zero exit, a warning is written to stderr via the friendly-errors translator (if available) or a plain-text fallback message that includes the project directory so the user can run the command manually.

---

### WR-02: `_SUBTOOL_PATTERN` regex uses `re.DOTALL` without anchoring — unbounded match on long input

**Files modified:** `scripts/intake_handler.py`
**Commit:** 2830aa1
**Applied fix:** Removed `re.DOTALL` from `_SUBTOOL_PATTERN` compilation (terminators contain no newlines so the flag was unnecessary and allowed the lazy quantifier to scan across multi-paragraph pastes). Added `text[:500]` slice at the `_SUBTOOL_PATTERN.search()` call in `_extract_subtools`, consistent with the T-07-05-04 mitigation already documented in the `_score_playbooks` comment.

---

### WR-03: Tauri CI workflow only targets `ubuntu-latest` — macOS and Windows link failures will go undetected

**Files modified:** `assets/ci-workflows/tauri.yml.tmpl`
**Commit:** 62135a5
**Applied fix:** Added a three-line comment block at the top of the template (after the existing header comments) explaining that `ubuntu-latest` is intentional for Phase 7 v1, that macOS/Windows builds require code-signing secrets (D-08), and that a matrix build should only be added once signing is configured.

---

### WR-04: `_resolve_project_root` path-traversal guard is a string check, not a component check

**Files modified:** `scripts/intake_handler.py`, `scripts/scaffold_dispatch.py`
**Commit:** 3795d3f
**Applied fix:** Replaced `".." in arg` substring check with `any(part == ".." for part in Path(arg).parts)` in `_resolve_project_root` in both files. The `Path.parts` approach handles OS-specific separators correctly and avoids false positives from directory names that happen to contain two consecutive dots for non-traversal reasons.

---

### WR-05: `_init_db()` in the CLI starter template does not close the connection on exception

**Files modified:** `assets/cli-starter/__main__.py.tmpl`
**Commit:** 5961de2
**Applied fix:** Replaced the manual `conn = _init_db()` / `conn.close()` pattern in `ping()` with `with _init_db() as conn:`, guaranteeing connection close on both normal exit and exception. Variables `ts` and `count` assigned inside the `with` block remain accessible for the `console.print` calls after it.

---

_Fixed: 2026-05-02T21:04:36Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
