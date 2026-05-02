"""Tests for the ai-service playbook (SCAF-02; phase 7 plan 02).

All tests SKIP (not error) before Wave 1 of plan 07-02 lands. That is by
design (TDD RED state). `scaffold_dispatch` is imported lazily inside the
`sd` fixture; the `has_ai_service` fixture additionally skips when
`scaffold_ai_service` has not yet been added.

The 6 tests here lock in:
  - presence of the playbook spec (.md, 7 sections)
  - presence + Pydantic-v2-shape of the vendored fastapi-starter/main.py
  - subprocess argv shape of scaffold_ai_service (uv init --app + uv add fastapi[standard])
  - post-scaffold artifacts (main.py, Dockerfile)

Subprocess matchers use argv-token style ("uv init --app {name}" fragment in
the joined-signature) per STATE.md decision log.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet importable."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet ai-service-ready (Wave 1 target)")


@pytest.fixture
def has_ai_service(sd):
    """Skips the test if scaffold_ai_service hasn't been added yet (Wave 1 target)."""
    if not hasattr(sd, "scaffold_ai_service"):
        pytest.skip("scaffold_ai_service not yet added (Wave 1 target)")
    return sd


# ---------- 1. playbook .md presence + 7-section structure ----------

def test_ai_service_playbook_md_present():
    """SCAF-02: references/playbooks/ai-service.md exists with the 7 mandatory sections."""
    playbook = REPO_ROOT / "references" / "playbooks" / "ai-service.md"
    if not playbook.exists():
        pytest.skip("references/playbooks/ai-service.md not yet created (Wave 1 target)")
    content = playbook.read_text(encoding="utf-8")
    required_headings = [
        "## What the ai-service playbook produces",
        "## Scaffold command",
        "## Post-scaffold files written by OSBuilder",
        "## Files OSBuilder must NOT write",
        "## Refuse list",
        "## Stack (pinned versions",
        "## See also",
    ]
    missing = [h for h in required_headings if h not in content]
    assert not missing, f"ai-service.md missing required headings: {missing}"


# ---------- 2-3. fastapi-starter/main.py presence + Pydantic v2 shape ----------

def test_fastapi_starter_main_present():
    """SCAF-02: assets/fastapi-starter/main.py exists with FastAPI + Pydantic + 3 routes."""
    main_py = REPO_ROOT / "assets" / "fastapi-starter" / "main.py"
    if not main_py.exists():
        pytest.skip("assets/fastapi-starter/main.py not yet created (Wave 1 target)")
    content = main_py.read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in content, (
        "main.py must import FastAPI"
    )
    assert "from pydantic import BaseModel" in content, (
        "main.py must import Pydantic BaseModel"
    )
    assert "class SummarizeRequest" in content, "must define SummarizeRequest model"
    assert "class SummarizeResponse" in content, "must define SummarizeResponse model"
    assert "def summarize(" in content, "must define summarize() helper"
    assert '@app.get("/")' in content, "must register GET /"
    assert '@app.get("/health")' in content, "must register GET /health"
    assert '@app.post("/summarize"' in content, "must register POST /summarize"


def test_fastapi_starter_uses_pydantic_v2():
    """SCAF-02 Pitfall 4: starter must use Pydantic v2 syntax — NO @validator, NO class Config:."""
    main_py = REPO_ROOT / "assets" / "fastapi-starter" / "main.py"
    if not main_py.exists():
        pytest.skip("assets/fastapi-starter/main.py not yet created (Wave 1 target)")
    content = main_py.read_text(encoding="utf-8")
    # Pydantic v1 markers — must be absent
    assert "@validator" not in content, (
        "Must NOT use @validator (Pydantic v1) — replaced by @field_validator in v2 (Pitfall 4)"
    )
    assert "class Config:" not in content, (
        "Must NOT use class Config: (Pydantic v1) — replaced by model_config in v2 (Pitfall 4)"
    )


# ---------- 4. scaffold_ai_service subprocess argv shape ----------

def test_scaffold_ai_service_subprocess_calls(has_ai_service, fake_shell, fake_which, tmp_path):
    """SCAF-02 D-10: scaffold_ai_service runs `uv init --app <name>` AND `uv add fastapi[standard]`.

    The 'fastapi[standard]' element is preserved as a SINGLE argv element (Pitfall 2 —
    quoting is meaningless to subprocess.run when shell=False; the brackets must
    travel as one string token, not split across multiple tokens).
    """
    sd = has_ai_service
    fake_which["uv"] = "/usr/local/bin/uv"
    # Pre-program both expected subprocess calls
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add", returncode=0, stdout="")
    sd.scaffold_ai_service("test-svc", tmp_path)

    signatures = [
        " ".join(c[0]) if isinstance(c[0], list) else c[0]
        for c in fake_shell.calls
    ]
    init_calls = [s for s in signatures if "uv init --app test-svc" in s]
    add_calls = [
        s for s in signatures
        if "uv add" in s and "fastapi[standard]" in s
    ]
    assert len(init_calls) == 1, (
        f"Expected exactly 1 'uv init --app test-svc' call; got {init_calls}. "
        f"All calls: {signatures}"
    )
    assert len(add_calls) == 1, (
        f"Expected exactly 1 'uv add fastapi[standard]' call; got {add_calls}. "
        f"All calls: {signatures}"
    )

    # Pitfall 2: the fastapi[standard] token must be a single argv element.
    add_call_argv = next(
        c[0] for c in fake_shell.calls
        if isinstance(c[0], list) and "uv" in c[0] and "add" in c[0]
        and any("fastapi[standard]" in tok for tok in c[0])
    )
    assert "fastapi[standard]" in add_call_argv, (
        "fastapi[standard] must be a SINGLE argv element (Pitfall 2 — no shell-split)"
    )


# ---------- 5. scaffold writes main.py post-init ----------

def test_scaffold_ai_service_writes_main_py(has_ai_service, fake_shell, fake_which, tmp_path):
    """SCAF-02 D-10: after the mocked subprocess, project_dir/main.py exists and matches starter."""
    sd = has_ai_service
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add", returncode=0, stdout="")
    project_dir = sd.scaffold_ai_service("test-svc", tmp_path)
    written = project_dir / "main.py"
    assert written.exists(), (
        f"scaffold_ai_service must write {written} after `uv init --app` runs"
    )
    starter = REPO_ROOT / "assets" / "fastapi-starter" / "main.py"
    assert written.read_text(encoding="utf-8") == starter.read_text(encoding="utf-8"), (
        "Written main.py content must match assets/fastapi-starter/main.py byte-for-byte"
    )


# ---------- 6. scaffold writes Dockerfile from python-uv template ----------

def test_scaffold_ai_service_writes_dockerfile(has_ai_service, fake_shell, fake_which, tmp_path):
    """SCAF-02 SHIP-03: scaffold writes Dockerfile via _write_dockerfile(stack_family=python-uv)."""
    sd = has_ai_service
    fake_which["uv"] = "/usr/local/bin/uv"
    fake_shell.program("uv init --app", returncode=0, stdout="")
    fake_shell.program("uv add", returncode=0, stdout="")
    project_dir = sd.scaffold_ai_service("test-svc", tmp_path)
    dockerfile = project_dir / "Dockerfile"
    assert dockerfile.exists(), (
        f"scaffold_ai_service must stamp {dockerfile} from python-uv.Dockerfile.tmpl (SHIP-03)"
    )
    content = dockerfile.read_text(encoding="utf-8")
    assert content.strip(), "Dockerfile must be non-empty"
