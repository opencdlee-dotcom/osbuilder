---
phase: 02-pre-flight-installer-cross-platform
reviewed: 2026-04-30T08:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - references/preflight/README.md
  - references/preflight/linux.md
  - references/preflight/macos.md
  - references/preflight/windows.md
  - scripts/preflight_check.py
  - scripts/tests/conftest.py
  - scripts/tests/test_preflight.py
  - scripts/tests/test_uninstall.py
  - scripts/uninstall.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-30T08:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

All 15 tests pass against the delivered `preflight_check.py` and `uninstall.py`. The
implementation correctly satisfies PRE-01 through PRE-07: detection-first design,
single-confirmation batch, atomic log-before-subprocess ordering, auto-rollback on
failure, and no-docker persistence. Cross-platform OS detection, version-manager
blocking, and pure-stdlib constraints are all met.

Two warnings were found. Both are test-isolation gaps that cause tests to write to the
developer's real `~/.osbuilder/install-log.json`; the confirmed side effect is a 138-entry
log already present at `~/.osbuilder/install-log.json` on the review machine. The
production code itself has no critical bugs. Three low-severity info items cover dead
code and a documented design divergence.

## Warnings

### WR-01: `test_single_confirmation_for_batch` writes to real `~/.osbuilder/`

**File:** `scripts/tests/test_preflight.py:65`
**Issue:** The test calls `pf.apply(plan)` but does not include the `tmp_install_log`
fixture. `apply()` calls `_write_install_log()` which resolves to
`Path.home() / ".osbuilder" / "install-log.json"` — the developer's real home
directory, not a temp path. Every pytest run adds 5 `"started"` entries to
`~/.osbuilder/install-log.json`. This has already polluted the review machine
(138 entries with status `"rolled-back"`), and will cause any subsequent
`preflight_check.py rollback` or `uninstall` to attempt to undo those fake entries
via subprocess calls.

**Fix:**
```python
def test_single_confirmation_for_batch(
    pf, fake_shell, fake_which, monkeypatch, tmp_install_log  # add fixture
):
    ...
```
Add `tmp_install_log` to the parameter list. The fixture already exists in
`conftest.py` and monkeypatches `Path.home()` to a temp dir, which is exactly what
this test needs.

---

### WR-02: `test_failure_triggers_rollback` writes to real `~/.osbuilder/`

**File:** `scripts/tests/test_preflight.py:131`
**Issue:** Same root cause as WR-01. This test also calls `pf.apply(plan)` without
the `tmp_install_log` fixture. The rollback path additionally calls `_write_install_log`
after marking entries `"rolled-back"`, so two write operations hit the real filesystem.

**Fix:**
```python
def test_failure_triggers_rollback(
    pf, fake_shell, fake_which, monkeypatch, tmp_install_log  # add fixture
):
    ...
```

---

## Info

### IN-01: Dead keys in `_UNINSTALL_FORM`

**File:** `scripts/preflight_check.py:285`
**Issue:** `_UNINSTALL_FORM` contains two keys — `"brew --cask"` and `"scoop"` — that
no entry in any of the four install tables (`_MACOS_INSTALL`, `_APT_INSTALL`,
`_DNF_INSTALL`, `_WINGET_INSTALL`) ever references. `_build_action()` at line 306
passes `mgr` (the manager string from the install table) to `_UNINSTALL_FORM[mgr]`;
since no install table uses `"brew --cask"` or `"scoop"`, those lambdas are
unreachable in production.

If a `brew --cask` install were added to `_MACOS_INSTALL` in the future without also
noting this dead key, it would work correctly because the key already exists — but the
dead entries are confusing and suggest an incomplete feature branch (cask support and
scoop fallback were planned but not wired to any install table in v1).

**Fix:** Either remove the dead keys to match what v1 actually supports, or add a
comment marking them as reserved for v2 (scoop fallback is documented in
`windows.md:27-29`):
```python
_UNINSTALL_FORM = {
    "brew":    lambda pkg: ["brew", "uninstall", pkg],
    # "brew --cask": reserved v2 — cask Docker Desktop fallback (see macos.md)
    "apt-get": lambda pkg: ["sudo", "apt-get", "remove", "--purge", "-y", pkg],
    "dnf":     lambda pkg: ["sudo", "dnf", "remove", "-y", pkg],
    "winget":  lambda pkg: ["winget", "uninstall", "-e", "--id", pkg],
    # "scoop": reserved v2 — scoop fallback path (see windows.md:27)
}
```

---

### IN-02: macOS Docker install diverges from D-11 OrbStack intent

**File:** `scripts/preflight_check.py:261`
**Issue:** `_MACOS_INSTALL["docker"]` uses package ID `"docker"` and installs via
`brew install docker`, but the design decision D-11 and `references/preflight/macos.md`
specify OrbStack (`brew install orbstack`) as the preferred macOS Docker runtime. The
code comment at line 258 acknowledges this divergence and attributes it to a
test-stub constraint predating the D-11 lock.

This means a macOS user running `preflight_check.py install` gets `docker` (the CLI
shim / Docker Engine formula) rather than OrbStack, which contradicts the documented
design. The install-log will record `package_id: "docker"` and `uninstall_argv: ["brew",
"uninstall", "docker"]` — both pointing at the wrong package for the intended runtime.

**Fix:** Update `_MACOS_INSTALL["docker"]` to orbstack and update the test stub in
`test_failure_triggers_rollback` to match (the test programs `"brew install docker"`
because the old package ID was `docker`):
```python
_MACOS_INSTALL = {
    ...
    "docker":  ("brew", "orbstack", ["brew", "install", "orbstack"]),
}
```
And in `test_failure_triggers_rollback`:
```python
fake_shell.program("brew install orbstack", returncode=1)
```
And verify the rollback assertion:
```python
rollback_calls = [s for s in signatures if "brew uninstall gh" in s]
```

---

### IN-03: Non-TTY auto-install path has no dedicated test

**File:** `scripts/tests/test_preflight.py`
**Issue:** `apply()` has two distinct code paths: (a) TTY — print preview, prompt for
`y/n`, and (b) non-TTY — print preview, proceed immediately without confirmation
(the T-02-20 mitigation at line 441-447). Only the TTY path is exercised by tests
(`test_single_confirmation_for_batch` explicitly patches `sys.stdin.isatty` to
`True`). Tests that call `apply()` without patching `isatty` (WR-01, WR-02) happen
to run in non-TTY under pytest, but this is implicit and not asserted.

There is no test that explicitly validates: "when stdin is not a TTY, `apply()`
proceeds without prompting." Adding one would close the coverage gap and document the
T-02-20 contract explicitly.

**Fix:** Add a test:
```python
def test_non_tty_proceeds_without_prompt(
    pf, fake_shell, fake_which, monkeypatch, tmp_install_log
):
    """T-02-20: In non-TTY context, apply() installs without prompting."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    fake_which["brew"] = "/opt/homebrew/bin/brew"
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    prompts = []
    monkeypatch.setattr("builtins.input", lambda *a, **kw: prompts.append(a) or "")
    plan = pf.plan(no_docker=True)
    rc = pf.apply(plan)
    assert len(prompts) == 0, "Non-TTY path must not call input()"
    assert rc == 0
```

---

_Reviewed: 2026-04-30T08:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
