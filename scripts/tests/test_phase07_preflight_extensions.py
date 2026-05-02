"""Tests for preflight extensions added by phase 7 (uv detection + install matrices).

This file owns the uv portion. The cargo portion is added by plan 07-04 and
will extend this file in-place (additive — never replace existing tests).

All tests SKIP cleanly before Wave 1 of plan 07-02 lands. The lazy-import
fixture pattern from `test_preflight.py` is reused so pytest --collect-only
counts these as live stubs, not errored modules.

The 3 tests here lock in:
  - uv detection returns None when missing (existing _probe_version unchanged)
  - macOS install matrix has a uv entry using the curl-pipe-sh installer
  - Windows winget install matrix uses the EXACT package ID 'astral-sh.uv'
    (lowercase, hyphenated — RESEARCH.md correction of D-21 typo 'Astral.UV')

Note: the test for "Astral.UV must NOT appear" intentionally embeds the
typo string in this file — that's the negative assertion (we're testing
the regression catcher).
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def pf():
    """Lazy import of scripts/preflight_check.py."""
    try:
        return importlib.import_module("preflight_check")
    except ImportError:
        pytest.skip("preflight_check module not yet importable")


# ---------- 1. probe_version returns None when uv missing ----------

def test_uv_detection_returns_none_when_missing(pf, fake_which):
    """_probe_version('uv') returns None when shutil.which('uv') is None."""
    # fake_which is empty; no 'uv' key set → shutil.which returns None
    result = pf._probe_version("uv")
    assert result is None, (
        f"_probe_version('uv') must return None when uv is not on PATH; got {result!r}"
    )


# ---------- 2. macOS install matrix has uv entry with the Astral installer ----------

def test_uv_install_action_macos(pf):
    """SCAF-02 D-20: _MACOS_INSTALL has uv entry using the official curl-pipe-sh installer."""
    if not hasattr(pf, "_MACOS_INSTALL"):
        pytest.skip("preflight_check._MACOS_INSTALL not present")
    if "uv" not in pf._MACOS_INSTALL:
        pytest.skip("uv not yet added to _MACOS_INSTALL (Wave 1 target)")
    entry = pf._MACOS_INSTALL["uv"]
    # entry shape: (manager, package_label, install_argv)
    assert len(entry) == 3, f"_MACOS_INSTALL['uv'] must be 3-tuple; got {entry!r}"
    install_argv = entry[2]
    assert isinstance(install_argv, list), "install_argv must be a list"
    # The installer is curl-pipe-sh per RESEARCH.md; sh -c is the wrapper
    assert "sh" in install_argv[0] or install_argv[0] == "sh", (
        f"macOS uv install must use sh wrapper for curl-pipe-sh; got argv[0]={install_argv[0]!r}"
    )
    joined = " ".join(install_argv)
    assert "astral.sh/uv/install.sh" in joined, (
        f"macOS uv install must hit astral.sh/uv/install.sh; got: {joined}"
    )


# ---------- 3. winget package ID is 'astral-sh.uv' (NOT 'Astral.UV' typo) ----------

def test_uv_winget_id_exact(pf):
    """SCAF-02 D-21 (RESEARCH.md correction): winget id MUST be 'astral-sh.uv', not 'Astral.UV'."""
    if not hasattr(pf, "_WINGET_INSTALL"):
        pytest.skip("preflight_check._WINGET_INSTALL not present")
    if "uv" not in pf._WINGET_INSTALL:
        pytest.skip("uv not yet added to _WINGET_INSTALL (Wave 1 target)")
    entry = pf._WINGET_INSTALL["uv"]
    assert len(entry) == 3, f"_WINGET_INSTALL['uv'] must be 3-tuple; got {entry!r}"
    install_argv = entry[2]
    joined = " ".join(install_argv)
    # Positive: the correct lowercase, hyphenated namespace MUST appear
    assert "astral-sh.uv" in joined, (
        f"Expected 'astral-sh.uv' in winget cmd; got {joined!r}"
    )
    # Negative: the documented typo MUST NOT appear (RESEARCH.md correction of D-21)
    assert "Astral.UV" not in joined, (
        "Must NOT use 'Astral.UV' — RESEARCH.md typo correction. "
        "Correct ID is 'astral-sh.uv' (lowercase, hyphenated)."
    )


# ============================================================================
# Phase 7 Plan 04 — cargo / Rust toolchain extensions (extends this file
# additively, mirroring the uv tests above). Tests SKIP cleanly until 07-04
# Wave 1 lands `_MACOS_INSTALL["cargo"]` and friends.
# ============================================================================


# ---------- 4. probe_version returns None when cargo missing ----------

def test_cargo_detection_returns_none_when_missing(pf, fake_which):
    """SCAF-04 D-20: _probe_version('cargo') returns None when cargo is missing.

    Reuses the same _probe_version surface as uv — no new probe needed; this
    test just locks in that the existing probe handles the cargo tool name.
    """
    # fake_which is empty; no 'cargo' key set → shutil.which returns None
    result = pf._probe_version("cargo")
    assert result is None, (
        f"_probe_version('cargo') must return None when cargo not on PATH; got {result!r}"
    )


# ---------- 5. macOS install matrix has cargo (rustup) entry ----------

def test_cargo_install_action_macos(pf):
    """SCAF-04 D-20: _MACOS_INSTALL has cargo entry using the official rustup installer.

    Per RESEARCH.md, the installer is `curl --proto '=https' --tlsv1.2
    https://sh.rustup.rs -sSf | sh -s -- -y` wrapped in `sh -c`.
    """
    if not hasattr(pf, "_MACOS_INSTALL"):
        pytest.skip("preflight_check._MACOS_INSTALL not present")
    if "cargo" not in pf._MACOS_INSTALL:
        pytest.skip("cargo not yet added to _MACOS_INSTALL (Wave 1 target)")
    entry = pf._MACOS_INSTALL["cargo"]
    assert len(entry) == 3, f"_MACOS_INSTALL['cargo'] must be 3-tuple; got {entry!r}"
    install_argv = entry[2]
    assert isinstance(install_argv, list), "install_argv must be a list"
    # The installer is curl-pipe-sh per RESEARCH.md; sh -c is the wrapper
    assert install_argv[0] == "sh", (
        f"macOS cargo install must use sh wrapper for curl-pipe-sh; "
        f"got argv[0]={install_argv[0]!r}"
    )
    joined = " ".join(install_argv)
    assert "sh.rustup.rs" in joined, (
        f"macOS cargo install must hit sh.rustup.rs; got: {joined}"
    )
    assert "-y" in joined, (
        f"macOS cargo install must pass -y for non-interactive (D-20); got: {joined}"
    )


# ---------- 6. winget package ID for rustup is exactly 'Rustlang.Rustup' ----------

def test_rustup_winget_id_exact(pf):
    """SCAF-04 D-21: winget id MUST be the literal 'Rustlang.Rustup' (case-sensitive)."""
    if not hasattr(pf, "_WINGET_INSTALL"):
        pytest.skip("preflight_check._WINGET_INSTALL not present")
    if "cargo" not in pf._WINGET_INSTALL:
        pytest.skip("cargo not yet added to _WINGET_INSTALL (Wave 1 target)")
    entry = pf._WINGET_INSTALL["cargo"]
    assert len(entry) == 3, f"_WINGET_INSTALL['cargo'] must be 3-tuple; got {entry!r}"
    install_argv = entry[2]
    joined = " ".join(install_argv)
    # Positive: the exact winget package ID MUST appear
    assert "Rustlang.Rustup" in joined, (
        f"Expected 'Rustlang.Rustup' in winget cmd; got {joined!r}"
    )
