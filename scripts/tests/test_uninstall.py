"""Tests for scripts/uninstall.py + scripts/preflight_check.py uninstall() — PRE-06.

All tests in this file FAIL or SKIP before Plan 02-03 lands.
Lazy-import-via-fixture pattern (see test_preflight.py header for rationale).
"""
from __future__ import annotations
import importlib
import json
import pytest


@pytest.fixture
def un():
    """Lazy import of scripts/preflight_check.py — uninstall() lives there;
    scripts/uninstall.py is a thin wrapper. Skip until Plan 02-02 lands."""
    try:
        return importlib.import_module("preflight_check")
    except ImportError:
        pytest.skip("preflight_check module not yet created (Plan 02-02 target)")


def test_uninstall_reverses_all(un, fake_shell, tmp_install_log, monkeypatch):
    """PRE-06: uninstall reverses every action in install-log.json (in REVERSE order)."""
    tmp_install_log.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "schema_version": "1",
        "actions": [
            {"tool": "node", "manager": "brew", "package_id": "node@20",
             "platform": "macos", "started_at": "2026-04-29T10:00:00Z",
             "succeeded_at": "2026-04-29T10:00:30Z",
             "install_command": "brew install node@20",
             "install_argv": ["brew", "install", "node@20"],
             "uninstall_command": "brew uninstall node@20",
             "uninstall_argv": ["brew", "uninstall", "node@20"],
             "status": "succeeded"},
            {"tool": "gh", "manager": "brew", "package_id": "gh",
             "platform": "macos", "started_at": "2026-04-29T10:00:31Z",
             "succeeded_at": "2026-04-29T10:00:45Z",
             "install_command": "brew install gh",
             "install_argv": ["brew", "install", "gh"],
             "uninstall_command": "brew uninstall gh",
             "uninstall_argv": ["brew", "uninstall", "gh"],
             "status": "succeeded"},
        ],
    }
    tmp_install_log.write_text(json.dumps(log), encoding="utf-8")
    un.uninstall()
    signatures = [c[0] if isinstance(c[0], str) else " ".join(c[0])
                  for c in fake_shell.calls]
    # Reverse order: gh first, then node
    gh_idx = next(i for i, s in enumerate(signatures) if "brew uninstall gh" in s)
    node_idx = next(i for i, s in enumerate(signatures) if "brew uninstall node@20" in s)
    assert gh_idx < node_idx, f"uninstall must run in REVERSE log order; got {signatures}"


def test_uninstall_preserves_pre_existing(un, fake_shell, tmp_install_log, monkeypatch):
    """PRE-06: uninstall only reverses logged actions — never touches pre-existing tools.

    Pre-populate log with ONE action (brew install gh). Assert exactly one
    'brew uninstall ...' call occurs and it is 'brew uninstall gh' — NOT node.
    """
    tmp_install_log.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "schema_version": "1",
        "actions": [
            {"tool": "gh", "manager": "brew", "package_id": "gh",
             "platform": "macos", "started_at": "2026-04-29T10:00:31Z",
             "succeeded_at": "2026-04-29T10:00:45Z",
             "install_command": "brew install gh",
             "install_argv": ["brew", "install", "gh"],
             "uninstall_command": "brew uninstall gh",
             "uninstall_argv": ["brew", "uninstall", "gh"],
             "status": "succeeded"},
        ],
    }
    tmp_install_log.write_text(json.dumps(log), encoding="utf-8")
    un.uninstall()
    signatures = [c[0] if isinstance(c[0], str) else " ".join(c[0])
                  for c in fake_shell.calls]
    uninstall_calls = [s for s in signatures if "brew uninstall" in s]
    assert len(uninstall_calls) == 1, (
        f"Expected exactly 1 uninstall call; got {len(uninstall_calls)}: {uninstall_calls}"
    )
    assert "brew uninstall gh" in uninstall_calls[0], (
        f"Expected 'brew uninstall gh'; got: {uninstall_calls[0]!r}"
    )
    node_calls = [s for s in signatures if "node" in s.lower()]
    assert len(node_calls) == 0, (
        f"uninstall must NOT touch node (not in log); got: {node_calls}"
    )
