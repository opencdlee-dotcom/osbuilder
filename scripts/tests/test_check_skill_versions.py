"""test_check_skill_versions.py — RED stubs for Phase 8 QUAL-05 sub-skill version-drift validator.

All tests skip until check_skill_versions module is created in 08-03.
"""
from __future__ import annotations
import importlib
from pathlib import Path
import pytest


@pytest.fixture
def csv_module():
    """Lazy import of scripts/check_skill_versions.py — skips when not yet created (08-03 target)."""
    try:
        return importlib.import_module("check_skill_versions")
    except ImportError:
        pytest.skip("check_skill_versions module not yet created (08-03 target)")


@pytest.fixture
def fake_skills_dir(tmp_path, monkeypatch, csv_module):
    """Fake ~/.claude/skills/ tree; each sub-skill seeded with controllable version."""
    fake = tmp_path / "skills"
    fake.mkdir()
    monkeypatch.setattr(csv_module, "SKILLS_DIR", fake)

    def _seed(name: str, version: str | None):
        skill = fake / name
        skill.mkdir()
        if version is None:
            (skill / "SKILL.md").write_text("---\nname: " + name + "\n---\n", encoding="utf-8")
        else:
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\nversion: {version}\n---\n", encoding="utf-8"
            )
    return _seed


@pytest.fixture
def fake_marker(tmp_path, monkeypatch, csv_module):
    """Redirect MARKER to tmp_path so tests don't pollute ~/.osbuilder/."""
    marker = tmp_path / "marker.txt"
    monkeypatch.setattr(csv_module, "MARKER", marker)
    return marker


def test_all_meet_minimum(csv_module, fake_skills_dir, fake_marker, tmp_path, monkeypatch):
    """QUAL-05: returns 0 when all sub-skills meet declared minimums."""
    fake_skills_dir("gsd", "1.0.0")
    fake_skills_dir("brainiac", "6.0.0")
    # Seed a fake OSBuilder SKILL.md with `requires:` block
    fake_skill = tmp_path / "SKILL.md"
    fake_skill.write_text(
        "---\nname: osbuilder\nrequires:\n  gsd: 1.0.0\n  brainiac: 6.0.0\n---\nbody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(csv_module, "SKILL_MD", fake_skill)
    assert csv_module.check_versions() == 0


def test_blocks_on_drift(csv_module, fake_skills_dir, fake_marker, tmp_path, monkeypatch, capsys):
    """QUAL-05: returns 1 with friendly upgrade command when below minimum."""
    fake_skills_dir("brainiac", "5.0.0")  # below minimum 6.0.0
    fake_skill = tmp_path / "SKILL.md"
    fake_skill.write_text(
        "---\nname: osbuilder\nrequires:\n  brainiac: 6.0.0\n---\nbody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(csv_module, "SKILL_MD", fake_skill)
    rc = csv_module.check_versions()
    assert rc == 1
    captured = capsys.readouterr()
    assert "brainiac" in captured.err
    assert "5.0.0" in captured.err or "below" in captured.err.lower()


def test_warns_on_missing_version(csv_module, fake_skills_dir, fake_marker, tmp_path, monkeypatch, capsys):
    """Pitfall 2: missing version field => exit 0 + warn (non-blocking)."""
    fake_skills_dir("gsd", None)  # gsd has no version field today (verified)
    fake_skill = tmp_path / "SKILL.md"
    fake_skill.write_text(
        "---\nname: osbuilder\nrequires:\n  gsd: 1.0.0\n---\nbody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(csv_module, "SKILL_MD", fake_skill)
    rc = csv_module.check_versions()
    assert rc == 0  # warn-not-block
    captured = capsys.readouterr()
    assert "gsd" in captured.err
    # Friendly warn signal: a warning glyph or the word "warn"/"no version"
    assert ("⚠" in captured.err) or ("no version" in captured.err.lower()) or ("warn" in captured.err.lower())


def test_first_session_marker(csv_module, fake_marker):
    """QUAL-05: marker file presence/absence drives is_first_session()."""
    assert csv_module.is_first_session() is True
    csv_module.record_check_complete()
    assert csv_module.is_first_session() is False
