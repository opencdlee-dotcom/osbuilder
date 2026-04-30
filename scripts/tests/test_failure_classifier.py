"""test_failure_classifier.py — RED stubs for Phase 4 failure_classifier.py (Wave 0).

All tests skip until failure_classifier module is created in Wave 1.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def fc():
    """Lazy import of scripts/failure_classifier.py — skips when not yet created."""
    try:
        return importlib.import_module("failure_classifier")
    except ImportError:
        pytest.skip("failure_classifier module not yet created (Wave 1 target)")


# HEAL-01: ECONNRESET maps to transient class
def test_transient_econnreset(fc):
    result = fc.classify("pnpm install failed: ECONNRESET")
    assert result["class"] == "transient"
    assert result["strategy"] == "backoff"


# HEAL-01: "context window" maps to context-overflow class
def test_context_overflow(fc):
    result = fc.classify("Error: context window exceeded")
    assert result["class"] == "context-overflow"
    assert result["strategy"] == "compress-retry"


# HEAL-01: "command not found" maps to tool-failure class
def test_tool_failure(fc):
    result = fc.classify("bash: /gsd-spec-phase: command not found")
    assert result["class"] == "tool-failure"
    assert result["strategy"] == "fallback"


# HEAL-01: "test_login failed" maps to validation-failure (NOT transient)
def test_validation_failure(fc):
    result = fc.classify("test_login failed: AssertionError: expected 200 got 401")
    assert result["class"] == "validation-failure"
    assert result["strategy"] == "re-plan"


# HEAL-02: transient → time.sleep(1) on retry_count=0
def test_sleep_called_for_transient_retry_0(fc, monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fc.handle_transient("ECONNRESET", retry_count=0)
    assert slept == [1], "retry 0 must sleep exactly 1 second"


# HEAL-02: transient → time.sleep(4) on retry_count=1
def test_sleep_called_for_transient_retry_1(fc, monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fc.handle_transient("ECONNRESET", retry_count=1)
    assert slept == [4], "retry 1 must sleep exactly 4 seconds"


# HEAL-02: validation-failure strategy is re-plan (no backoff)
def test_validation_failure_does_not_backoff(fc):
    result = fc.classify("code-tester failed: assertion error in test_login")
    assert result["class"] == "validation-failure"
    assert result["strategy"] == "re-plan"
    assert result.get("backoff_seconds") is None


# HEAL-03: retry_count >= 3 returns retry_ok=False
def test_cap_at_3_reflections(fc):
    result = fc.classify("ECONNRESET", context={"retry_count": 3})
    assert result["retry_ok"] is False


# HEAL-04: 4th failure produces structured handoff string
def test_structured_handoff_produced(fc):
    handoff = fc.build_escalation_handoff(
        phase=2,
        role="QA",
        failure_class="transient",
        last_error="ECONNRESET on pnpm install",
        escalation_log=["retry 1 backoff 1s", "retry 2 backoff 4s", "retry 3 backoff 16s",
                        "/gsd-debug invoked", "/problem-solver invoked"],
    )
    assert "OSBuilder Escalation Handoff" in handoff
    assert "last_error" in handoff.lower() or "last error" in handoff.lower()
    assert "retry" in handoff.lower()
    assert "recommended" in handoff.lower()
