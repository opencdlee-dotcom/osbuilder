"""Tests for the hub-platform playbook (SCAF-05; phase 7 plan 05).

All tests SKIP (not error) before Wave 1 of plan 07-05 lands. That is by
design (TDD RED state). `scaffold_dispatch`, `intake_handler`, and
`state_writer` are imported lazily inside fixtures.

The 8 tests here lock in:
  - presence of the playbook spec (`.md`, 7 sections, ≤ 80 lines)
  - presence of both hub-template files (CLAUDE.md.tmpl + subtool-CLAUDE.md.tmpl)
  - presence of the vendored professor-snapshot/ test fixture (D-05)
  - routing-table substitution: scaffold_hub renders one row per subtool
  - structural diff: built tree is a SUPERSET of snapshot signature (Pattern 3)
  - idempotency or clean failure on second call (mkdir(exist_ok=False))
  - intake parsing: `_extract_subtools("hub for grading and rostering")` (D-06)
  - state_writer: `subtools` field added to ALLOWED_FIELDS (additive — Phase 6 pattern)

Pure file-stamping per RESEARCH.md §Pattern 4 — NO subprocess, NO `fake_shell`
fixture needed. Structural-diff helper is verbatim from RESEARCH.md Pattern 3.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO_ROOT / "assets" / "hub-template" / "professor-snapshot"


@pytest.fixture
def sd():
    """Lazy import of scripts/scaffold_dispatch.py — skips when not yet importable."""
    try:
        return importlib.import_module("scaffold_dispatch")
    except ImportError:
        pytest.skip("scaffold_dispatch module not yet hub-ready (Wave 1 target)")


@pytest.fixture
def has_hub(sd):
    """Skips the test if scaffold_hub hasn't been added yet (Wave 1 target)."""
    if not hasattr(sd, "scaffold_hub"):
        pytest.skip("scaffold_hub not yet added (Wave 1 target)")
    return sd


@pytest.fixture
def ih():
    """Lazy import of scripts/intake_handler.py."""
    try:
        return importlib.import_module("intake_handler")
    except ImportError:
        pytest.skip("intake_handler module not yet importable")


@pytest.fixture
def sw():
    """Lazy import of scripts/state_writer.py."""
    try:
        return importlib.import_module("state_writer")
    except ImportError:
        pytest.skip("state_writer module not yet importable")


# ---------- structural-diff helper (verbatim from RESEARCH.md Pattern 3) ----------

def _structural_signature(root: Path) -> "set[tuple[str, str]]":
    """Return {(relpath, kind), ...} where kind in {'dir', 'file'}."""
    sig: "set[tuple[str, str]]" = set()
    for entry in root.iterdir():
        if entry.name.startswith(".") or entry.name == "node_modules":
            continue
        if entry.is_dir():
            sig.add((entry.name, "dir"))
            if (entry / "CLAUDE.md").exists():
                sig.add((f"{entry.name}/CLAUDE.md", "file"))
        elif entry.is_file():
            sig.add((entry.name, "file"))
    return sig


# ---------- 1. playbook .md presence + 7-section structure + ≤ 80 lines ----------

def test_hub_playbook_md_present():
    """SCAF-05: references/playbooks/hub-platform.md exists; 7 mandatory sections; ≤ 80 lines."""
    playbook = REPO_ROOT / "references" / "playbooks" / "hub-platform.md"
    if not playbook.exists():
        pytest.skip("references/playbooks/hub-platform.md not yet created (Wave 1 target)")
    content = playbook.read_text(encoding="utf-8")
    required_headings = [
        "## What the hub-platform playbook produces",
        "## Scaffold command",
        "## Post-scaffold files",
        "## Files OSBuilder must NOT write",
        "## Refuse list",
        "## Stack",
        "## See also",
    ]
    missing = [h for h in required_headings if h not in content]
    assert not missing, f"hub-platform.md missing required headings: {missing}"
    line_count = len(content.splitlines())
    assert line_count <= 80, (
        f"hub-platform.md must be ≤ 80 lines (progressive disclosure budget); got {line_count}"
    )


# ---------- 2. hub-template templates present ----------

def test_hub_template_files_present():
    """SCAF-05: assets/hub-template/CLAUDE.md.tmpl + subtool-CLAUDE.md.tmpl exist with placeholders."""
    top_tmpl = REPO_ROOT / "assets" / "hub-template" / "CLAUDE.md.tmpl"
    sub_tmpl = REPO_ROOT / "assets" / "hub-template" / "subtool-CLAUDE.md.tmpl"
    if not (top_tmpl.exists() and sub_tmpl.exists()):
        pytest.skip("hub-template files not yet created (Wave 1 target)")
    top_content = top_tmpl.read_text(encoding="utf-8")
    sub_content = sub_tmpl.read_text(encoding="utf-8")
    assert "{{routing_table}}" in top_content, (
        "Top-level template must contain {{routing_table}} placeholder"
    )
    assert "{{project_name}}" in top_content, (
        "Top-level template must contain {{project_name}} placeholder"
    )
    assert "{{subtool}}" in sub_content, (
        "Per-subtool template must contain {{subtool}} placeholder"
    )


# ---------- 3. vendored professor-snapshot/ exists ----------

def test_hub_snapshot_vendored():
    """D-05: assets/hub-template/professor-snapshot/ vendored with CLAUDE.md, AGENTS.md, ≥ 1 subdir."""
    if not SNAPSHOT.exists():
        pytest.skip("professor-snapshot not yet vendored (Wave 1 target)")
    assert (SNAPSHOT / "CLAUDE.md").exists(), (
        "snapshot must vendor top-level CLAUDE.md (the routing table contract)"
    )
    assert (SNAPSHOT / "AGENTS.md").exists(), (
        "snapshot must vendor AGENTS.md (auxiliary router doc)"
    )
    sig = _structural_signature(SNAPSHOT)
    subdirs = {n for n, k in sig if k == "dir"}
    assert subdirs, "snapshot must vendor at least one sub-tool dir"
    # Each subdir must have either a CLAUDE.md or a .gitkeep marker so git tracks it
    for sub in subdirs:
        sub_path = SNAPSHOT / sub
        has_marker = (
            (sub_path / "CLAUDE.md").exists()
            or (sub_path / ".gitkeep").exists()
        )
        assert has_marker, (
            f"snapshot subdir {sub} must contain CLAUDE.md or .gitkeep "
            f"(otherwise git won't track empty dir)"
        )


# ---------- 4. routing-table substitution ----------

def test_hub_routing_table(has_hub, tmp_path):
    """SCAF-05 D-04: scaffold_hub renders one routing-table row per subtool."""
    sd = has_hub
    project_dir = sd.scaffold_hub("test-hub", tmp_path, subtools=["grading", "rostering"])
    top_md = project_dir / "CLAUDE.md"
    assert top_md.exists(), f"top-level CLAUDE.md must be written at {top_md}"
    content = top_md.read_text(encoding="utf-8")
    assert "| `grading/` |" in content, (
        f"routing table missing grading row. Got:\n{content}"
    )
    assert "| `rostering/` |" in content, (
        f"routing table missing rostering row. Got:\n{content}"
    )
    assert "{{routing_table}}" not in content, (
        "Template substitution incomplete — {{routing_table}} placeholder still present"
    )
    assert "{{project_name}}" not in content, (
        "Template substitution incomplete — {{project_name}} placeholder still present"
    )
    # Each subtool dir must exist with its own CLAUDE.md
    for sub in ("grading", "rostering"):
        sub_md = project_dir / sub / "CLAUDE.md"
        assert sub_md.exists(), f"per-subtool CLAUDE.md missing at {sub_md}"
        sub_content = sub_md.read_text(encoding="utf-8")
        assert "{{subtool}}" not in sub_content, (
            f"Per-subtool placeholder unsubstituted in {sub_md}"
        )
        assert sub in sub_content, (
            f"Per-subtool CLAUDE.md must mention its own name '{sub}'"
        )


# ---------- 5. structural-diff: built tree is SUPERSET of snapshot ----------

def test_hub_matches_professor_structure(has_hub, tmp_path):
    """D-05 / Pattern 3: structural signature of built dir is SUPERSET of snapshot signature."""
    sd = has_hub
    if not SNAPSHOT.exists():
        pytest.skip("Snapshot not yet vendored (Wave 1 target)")
    snapshot_sig = _structural_signature(SNAPSHOT)
    # Subtools = directories in the snapshot
    subtools = sorted(name for name, kind in snapshot_sig if kind == "dir")
    if not subtools:
        pytest.skip("Snapshot has no subdirs")
    project_dir = sd.scaffold_hub("test-hub", tmp_path, subtools=subtools)
    built_sig = _structural_signature(project_dir)
    # Top-level CLAUDE.md must exist in built
    assert ("CLAUDE.md", "file") in built_sig, (
        "built dir missing top-level CLAUDE.md"
    )
    # Every snapshot subdir must exist in built
    snapshot_dirs = {n for n, k in snapshot_sig if k == "dir"}
    built_dirs = {n for n, k in built_sig if k == "dir"}
    assert snapshot_dirs.issubset(built_dirs), (
        f"Missing subtool dirs: {snapshot_dirs - built_dirs}"
    )
    # Every subdir must have its own CLAUDE.md
    for sub in snapshot_dirs:
        assert (project_dir / sub / "CLAUDE.md").exists(), (
            f"Missing CLAUDE.md for subtool {sub}"
        )


# ---------- 6. idempotency or clean failure on second call ----------

def test_hub_idempotent_or_fails_cleanly(has_hub, tmp_path):
    """RESEARCH.md line 535: mkdir(exist_ok=False) means second call must either be idempotent OR raise clearly."""
    sd = has_hub
    sd.scaffold_hub("test-hub", tmp_path, subtools=["grading"])
    # Second call: accept either behavior — idempotent OR clean error
    raised = False
    try:
        sd.scaffold_hub("test-hub", tmp_path, subtools=["grading"])
    except (FileExistsError, SystemExit, OSError):
        raised = True
    # Either path is acceptable; what's NOT acceptable is silent-corrupt or crash
    # without raising. The original CLAUDE.md must still be present and valid.
    top_md = tmp_path / "test-hub" / "CLAUDE.md"
    assert top_md.exists(), (
        "After second-call attempt, the original CLAUDE.md must still be present "
        "(no silent corruption)"
    )
    # Document which path the implementation took (for debug clarity).
    # No assertion on `raised` — both paths valid.
    _ = raised


# ---------- 7. _extract_subtools intake parsing (D-06) ----------

def test_extract_subtools_simple(ih):
    """D-06: _extract_subtools('hub for grading and rostering') returns list with both."""
    if not hasattr(ih, "_extract_subtools"):
        pytest.skip("_extract_subtools not yet added (Wave 1 target)")
    result = ih._extract_subtools(
        "build me a hub like Professor Hub for grading and rostering"
    )
    assert isinstance(result, list), (
        f"_extract_subtools must return list; got {type(result).__name__}"
    )
    # Both subtools should appear (case-insensitive match accepted)
    lowered = [s.lower() for s in result]
    assert "grading" in lowered, (
        f"Expected 'grading' in subtools; got {result}"
    )
    assert "rostering" in lowered, (
        f"Expected 'rostering' in subtools; got {result}"
    )


# ---------- 8. state_writer subtools field (additive — Phase 6 pattern) ----------

def test_state_writer_subtools_field(sw):
    """Phase 6 additive pattern: 'subtools' in ALLOWED_FIELDS but NOT REQUIRED_FIELDS."""
    assert "subtools" in sw.ALLOWED_FIELDS, (
        f"'subtools' missing from ALLOWED_FIELDS. Got: {sorted(sw.ALLOWED_FIELDS)}"
    )
    # Should NOT be in REQUIRED_FIELDS (additive — Phase 3/4/5/6 pattern)
    if hasattr(sw, "REQUIRED_FIELDS"):
        assert "subtools" not in sw.REQUIRED_FIELDS, (
            "subtools must NOT be required (additive). It is hub-only and would "
            "break validate() for non-hub builds."
        )
