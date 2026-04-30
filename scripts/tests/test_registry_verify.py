"""test_registry_verify.py — RED stubs for Phase 4 registry_verify.py (Wave 0).

All tests skip until registry_verify module is created in Wave 1.
"""
from __future__ import annotations

import importlib
import urllib.error

import pytest


@pytest.fixture
def rv():
    """Lazy import of scripts/registry_verify.py — skips when not yet created."""
    try:
        return importlib.import_module("registry_verify")
    except ImportError:
        pytest.skip("registry_verify module not yet created (Wave 1 target)")


# HEAL-05: hallucinated npm package → verify_npm returns False
def test_hallucinated_npm_package_blocked(rv, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            url=req.full_url, code=404, msg="Not Found", hdrs=None, fp=None
        )
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert rv.verify_npm("@anthropic/clauded-code-helper") is False


# HEAL-05: real npm package → verify_npm returns True
def test_real_npm_package_passes(rv, monkeypatch):
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResponse())
    assert rv.verify_npm("next") is True


# HEAL-05: network error → verify_npm returns True (fail-open)
def test_network_error_fails_open(rv, monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **kw: (_ for _ in ()).throw(
            urllib.error.URLError("Network unreachable")
        ),
    )
    assert rv.verify_npm("next") is True


# HEAL-05: hallucinated PyPI package → verify_pypi returns False
def test_hallucinated_pypi_package_blocked(rv, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            url=req.full_url, code=404, msg="Not Found", hdrs=None, fp=None
        )
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert rv.verify_pypi("anthropic-hallucinated-package-xyz") is False
