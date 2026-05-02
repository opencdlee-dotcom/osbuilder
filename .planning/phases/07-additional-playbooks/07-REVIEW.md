---
phase: 07-additional-playbooks
reviewed: 2026-05-02T00:00:00Z
depth: standard
files_reviewed: 36
files_reviewed_list:
  - scripts/intake_handler.py
  - scripts/tests/test_phase07_intake_inference.py
  - references/question-bank.md
  - references/refuse-list.md
  - references/playbooks/web.md
  - references/playbooks/ai-service.md
  - assets/fastapi-starter/main.py
  - assets/fastapi-starter/pyproject.snippet.toml
  - assets/fastapi-starter/README.md
  - scripts/scaffold_dispatch.py
  - scripts/preflight_check.py
  - references/friendly-errors/dictionary.yaml
  - references/stack-menu.md
  - assets/dockerfiles/python-uv.Dockerfile.tmpl
  - scripts/tests/test_phase07_ai_service.py
  - scripts/tests/test_phase07_preflight_extensions.py
  - references/playbooks/cli.md
  - assets/cli-starter/__main__.py.tmpl
  - assets/cli-starter/pyproject.snippet.toml
  - scripts/tests/test_phase07_cli.py
  - references/playbooks/desktop.md
  - assets/ci-workflows/tauri.yml.tmpl
  - scripts/tests/test_phase07_desktop.py
  - scripts/tests/test_refusal.py
  - references/playbooks/hub-platform.md
  - assets/hub-template/CLAUDE.md.tmpl
  - assets/hub-template/subtool-CLAUDE.md.tmpl
  - assets/hub-template/README.md
  - assets/hub-template/professor-snapshot/CLAUDE.md
  - assets/hub-template/professor-snapshot/AGENTS.md
  - assets/hub-template/professor-snapshot/LabNoteBookGrader/CLAUDE.md
  - assets/hub-template/professor-snapshot/Exam-grader/CLAUDE.md
  - scripts/tests/test_phase07_hub_platform.py
  - scripts/state_writer.py
  - scripts/tests/test_e2e_playbooks.py
  - scripts/tests/conftest.py
  - pyproject.toml
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-05-02T00:00:00Z
**Depth:** standard
**Files Reviewed:** 36
**Status:** issues_found

## Summary

Phase 7 adds four new scaffold playbooks (ai-service, CLI, desktop, hub-platform) plus 5-way playbook inference in the intake handler. The code is well-structured, security-conscious (path-traversal guards, input allowlisting, shell=False throughout), and the TDD fixture pattern is consistent. The curl-pipe-sh installer pattern for uv and Rust is intentional and documented.

Five warnings and six info items were found. No critical issues. The most impactful warnings are: (1) `uv add fastapi[standard]` and `uv add typer` failures are silently swallowed — the scaffold returns successfully even if the core dependency install failed; (2) `_extract_subtools` uses `re.DOTALL` without bounding the match, creating a worst-case O(n) scan against potentially long input; (3) the Tauri CI workflow only tests on `ubuntu-latest`, which will not catch macOS/Windows-specific Tauri link failures.

---

## Warnings

### WR-01: Silent failure when `uv add` exits non-zero in `scaffold_ai_service` and `scaffold_cli`

**File:** `scripts/scaffold_dispatch.py:361-364` (ai-service) and `439-441` (cli)
**Issue:** Both scaffold functions call `subprocess.run(["uv", "add", ...], check=False)` and discard the return value entirely. If `uv add fastapi[standard]` or `uv add typer` fails (network outage, registry timeout, corrupt cache), the function returns the `project_dir` as though the scaffold succeeded. The user's project will be missing its core runtime dependency, and subsequent `uv run` will fail with a confusing `ModuleNotFoundError` rather than a clear scaffold error.

This contrasts with `scaffold_web` which at least checks the return code and emits a warning to stderr for its `pnpm add` calls (lines 270-304).

**Fix:**
```python
result = subprocess.run(
    ["uv", "add", "fastapi[standard]"],
    cwd=str(project_dir), shell=False, check=False,
)
if result.returncode != 0:
    _raw = (result.stderr or "").strip() or f"uv add fastapi[standard] exit {result.returncode}"
    if _fe is not None:
        _msg = _fe.translate(_raw, ctx={"tool": "uv"})
        sys.stderr.write(
            f"## {_msg.title}\n{_msg.what_broke}\n\n"
            f"**What to do:** {_msg.what_to_do} Run manually in {project_dir}\n"
        )
    else:
        sys.stderr.write(
            f"OSBuilder: warning — uv add fastapi[standard] failed "
            f"(exit {result.returncode}). Run manually in {project_dir}\n"
        )
```
Apply the same pattern to `uv add typer` in `scaffold_cli`.

---

### WR-02: `_SUBTOOL_PATTERN` regex uses `re.DOTALL` without anchoring — unbounded match on long input

**File:** `scripts/intake_handler.py:161-164`
**Issue:** The compiled pattern uses `re.DOTALL`, which makes `.` match newlines. Combined with the `(.+?)` lazy quantifier and the `$` end-anchor alternative, a very long single-line spec (the comment at line 78 notes the O(n*k) concern for `_score_playbooks`, but this regex shares the same caller) will scan the entire remaining string from the first `\bfor\b` match. The T-07-05-04 "bounded quantifier" mitigation cited in the comment only applies to post-match cleanup (the 40-char cap), not to the regex engine's backtracking itself.

The `re.DOTALL` flag is also unnecessary: the clausal-break terminators (`.`, `;`, ` that `, ` with the `, ` so that `) do not themselves contain newlines, so `.+?` without DOTALL would find the same matches on normal input while rejecting multi-paragraph pastes cleanly.

**Fix:** Remove `re.DOTALL` from the pattern compilation:
```python
_SUBTOOL_PATTERN = re.compile(
    r"\bfor\s+(.+?)(?:[.;]|\s+that\s+(?:does|can|will)|\s+with\s+the\s+|\s+so\s+that\s+|$)",
    re.IGNORECASE,
)
```
Add an upstream `text[:500]` slice in `_extract_subtools` to match the mitigation already documented in the `_score_playbooks` comment (line 78).

---

### WR-03: Tauri CI workflow only targets `ubuntu-latest` — macOS and Windows link failures will go undetected

**File:** `assets/ci-workflows/tauri.yml.tmpl:17`
**Issue:** The `runs-on` value is hard-coded to `ubuntu-latest`. Tauri build failures that are specific to macOS (Apple Silicon, WebKit version) or Windows (MSVC toolchain, `rustup default stable-msvc` Pitfall 3) will not surface in CI. The desktop playbook's own documentation (line 57 of `desktop.md`) explicitly warns about the Windows toolchain problem, but the CI template does not provide a Windows job to catch regressions.

This is a design trade-off (single-OS CI keeps the YAML minimal for a first build), but it means users following the desktop playbook will have a CI configuration that only validates the Linux build path.

**Fix:** Consider adding a matrix to the template, or add a comment at the top of the template to document the intentional scope limitation so future maintainers do not mistake it for an oversight:
```yaml
# NOTE: single-OS CI (ubuntu-latest) is intentional for Phase 7 v1.
# macOS and Windows Tauri builds require code-signing secrets (D-08).
# Extend to a matrix build only when signing is configured.
```

---

### WR-04: `_resolve_project_root` path-traversal guard is a string check, not a component check

**File:** `scripts/intake_handler.py:317-318` and `scripts/scaffold_dispatch.py:133-135`
**Issue:** The guard `if ".." in arg` catches `../foo` and `foo/../bar`, but also rejects legitimate paths that happen to contain two consecutive dots for non-traversal reasons (e.g., a directory named `my..project` on a filesystem that allows it, or a future change that passes a URL as a path). More importantly it would NOT catch URL-encoded `%2e%2e` or Windows-style `..` with backslash (`..\\`) if the value arrives after some transformation, though neither is likely in this CLI context.

The stronger check would validate the resolved absolute path rather than the raw string:
```python
resolved = Path(arg).resolve()
# Ensure the resolved path is inside a known safe root, or simply:
if any(part == ".." for part in Path(arg).parts):
    raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
```
The `Path(arg).parts` check correctly handles OS-specific separators and rejects only true `..` components. The current string check is functional for the documented threat model, but the `parts`-based approach is more precise.

---

### WR-05: `_init_db()` in the CLI starter template does not close the connection on exception

**File:** `assets/cli-starter/__main__.py.tmpl:22-30`
**Issue:** `_init_db()` opens a `sqlite3.connect()` connection and returns it to the caller. If an exception occurs between `_init_db()` returning and the `conn.close()` call at the end of `ping()`, the connection is leaked. SQLite connections are cleaned up by GC eventually, but the pattern is fragile — particularly if a user extends `ping()` with additional logic that raises.

**Fix:** Use a context manager in `ping()` instead of manually calling `close()`:
```python
@app.command()
def ping():
    """Write a row to SQLite and read it back — proves persistence works."""
    with _init_db() as conn:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO pings (ts) VALUES (?)", (ts,))
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) FROM pings")
        count = cur.fetchone()[0]
    console.print(f"[green]ping #{count}[/green] at [cyan]{ts}[/cyan]")
    console.print(f"DB: [dim]{DB_PATH}[/dim]")
```
Alternatively, keep `conn.close()` but wrap the body in `try/finally`.

---

## Info

### IN-01: `pyproject.snippet.toml` placeholder `{{project_name_module}}` is never substituted

**File:** `assets/cli-starter/pyproject.snippet.toml:9`
**Issue:** The snippet declares `"{{project_name_module}}.__main__:app"` as the entry-point, but `scaffold_cli` only substitutes `{{project_name}}` in `__main__.py.tmpl` (line 435 of `scaffold_dispatch.py`). The snippet is documented as a reference-only artifact (the comment says `uv add typer` is used instead of splicing the snippet), so this placeholder is never actually rendered. However, if the procedure ever changes to splice the snippet into `pyproject.toml`, the `{{project_name_module}}` substitution would be silently skipped and produce a broken entry-point.

**Fix:** Add a comment in the snippet making the reference-only status explicit, or align placeholder names so a future splice step works without special casing:
```toml
# Reference only — scaffold_cli runs `uv add typer` and does NOT splice this snippet.
# If you add splice logic, substitute both {{project_name}} AND {{project_name_module}}.
```

---

### IN-02: `_build_tauri_identifier` produces an empty suffix for all-symbol project names

**File:** `scripts/scaffold_dispatch.py:465`
**Issue:** `_build_tauri_identifier` strips all non-alphanumeric characters. For a project name like `---` (valid under `_validate_project_name`'s `[a-zA-Z0-9_-]+` regex? No — hyphens are valid), the sanitized suffix would be empty, producing `com.osbuilder.` which is not a valid reverse-DNS identifier and would cause `create-tauri-app` to reject it with an unhelpful error.

`_validate_project_name` allows `[a-zA-Z0-9_-]+`, so a name like `---` passes validation but produces an empty suffix after stripping hyphens and underscores. A name of `_` also passes.

**Fix:** Add a guard after sanitization:
```python
sanitized = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
if not sanitized:
    raise SystemExit(
        f"OSBuilder: project name '{name}' produces an empty Tauri bundle identifier. "
        "Use a name that contains at least one letter or digit."
    )
return f"com.osbuilder.{sanitized}"
```

---

### IN-03: `check_refuse_list` writes `last_failure` state before confirming the file is for the current session

**File:** `scripts/intake_handler.py:304`
**Issue:** `check_refuse_list` writes `last_failure=refused: <kw>` to `state.md` whenever a refuse keyword is found in `derived_spec.md`. If a developer re-runs the check against a stale `derived_spec.md` from a previous (refused) build after having started a new session, the `last_failure` field of the new session's `state.md` will be overwritten. This is a minor state-management concern rather than a security issue — the resume protocol handles `last_failure` explicitly.

**Fix:** No code change required, but document the deliberate behavior in a comment near the `_write_state_field` call so future maintainers understand it is intentional.

---

### IN-04: `actions/checkout@v6` in the Tauri CI template references a non-existent version

**File:** `assets/ci-workflows/tauri.yml.tmpl:20`
**Issue:** The template references `actions/checkout@v6`. As of the knowledge cutoff, the current stable version of `actions/checkout` is v4. Referencing `@v6` will either resolve to a tag that does not exist (and fail CI on first use) or resolve to a future major version with potentially breaking interface changes.

Compare with the other two workflow templates (node and python), which likely use `@v4` — this template should match.

**Fix:**
```yaml
- uses: actions/checkout@v4
```

---

### IN-05: `ensure_uv` curl-pipe-sh installer on Unix has no certificate verification flag

**File:** `scripts/scaffold_dispatch.py:197`
**Issue:** The fallback `ensure_uv` installer uses `curl -LsSf https://astral.sh/uv/install.sh | sh`. This is the canonical form from Astral's docs, but the curl invocation omits `--proto '=https' --tlsv1.2` that the Rust installer (lines 334-337 of `preflight_check.py`) uses. The inconsistency is minor because `https://` is already enforced by the URL scheme and curl's default CA bundle, but the more explicit flags provide defence-in-depth against TLS downgrade.

**Fix:** Align with the rustup installer pattern:
```python
["sh", "-c",
 "curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh"],
```
Note: `preflight_check.py`'s `_MACOS_INSTALL["uv"]` (lines 307-309) also uses the shorter form — update both for consistency.

---

### IN-06: Dead comment in Dockerfile template references a feature that was already resolved

**File:** `assets/dockerfiles/python-uv.Dockerfile.tmpl:7-9`
**Issue:** Lines 7-9 contain a comment saying "When Phase 7 adds the cli playbook (07-03), CMD must be parameterised..." and "cli playbook will fork its own template." Phase 07-03 (CLI playbook) is now part of this phase and the resolution is documented — the CLI playbook has no Dockerfile (per `references/playbooks/cli.md`). The comment is now stale and could mislead future maintainers into thinking parameterisation is still pending.

**Fix:** Remove or update the comment to reflect the decided outcome:
```
# This template targets the ai-service (FastAPI) playbook only.
# CLI playbook (07-03) ships no Dockerfile (single-user local tool).
# Desktop playbook (07-04) ships build artifacts, not a container.
```

---

_Reviewed: 2026-05-02T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
