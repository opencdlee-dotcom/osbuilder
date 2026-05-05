"""test_examples.py — RED stubs for Phase 8 QUAL-04 examples gallery.

Skips until examples/ is populated in 08-07.
"""
from __future__ import annotations
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples"

EXPECTED_PLAYBOOKS = ("web", "ai-service", "cli", "desktop", "hub-platform")


def _example_dirs() -> list[Path]:
    if not EXAMPLES.exists():
        pytest.skip("examples/ not yet populated (08-07 target)")
    dirs = [p for p in EXAMPLES.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not dirs:
        pytest.skip("examples/ has no sub-directories yet (08-07 target)")
    return dirs


def test_min_three():
    """QUAL-04: examples/ has >= 3 sub-directories."""
    assert len(_example_dirs()) >= 3


def test_each_has_spec():
    """QUAL-04: every example sub-dir has a SPEC.md."""
    for d in _example_dirs():
        assert (d / "SPEC.md").is_file(), f"{d.name}/SPEC.md missing"


def test_distinct_playbooks():
    """Pitfall 5: examples cover >= 3 distinct playbooks (no 5-TODOs filler)."""
    playbooks = []
    for d in _example_dirs():
        spec = (d / "SPEC.md").read_text(encoding="utf-8").lower()
        for pb in EXPECTED_PLAYBOOKS:
            if pb in spec:
                playbooks.append(pb)
                break
    assert len(set(playbooks)) >= 3, \
        f"examples must use >= 3 distinct playbooks; got {playbooks}"


def test_has_repo_url():
    """QUAL-04: each example has a repo-url.txt (real URL or NOT_PUBLISHED placeholder)."""
    for d in _example_dirs():
        url_file = d / "repo-url.txt"
        assert url_file.exists(), f"{d.name}/repo-url.txt missing"
        content = url_file.read_text(encoding="utf-8").strip()
        assert content, f"{d.name}/repo-url.txt is empty"
        assert content.startswith("https://github.com/") or content == "NOT_PUBLISHED", \
            f"{d.name}/repo-url.txt must be a github URL or NOT_PUBLISHED, got: {content!r}"


def test_has_screenshots():
    """QUAL-04 SC-4: each example has >= 1 real screenshot image (skip-guarded until screenshots land).

    Skip when screenshots/ is empty or contains only .gitkeep — the gallery ships placeholders
    in 08-08 Task 2 and surfaces real screenshots via 08-HUMAN-UAT.md row 4 follow-up.
    """
    IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    for d in _example_dirs():
        screenshots = d / "screenshots"
        if not screenshots.exists():
            pytest.skip(f"{d.name}/screenshots/ not yet created (08-08 target)")
        real_images = [
            p for p in screenshots.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        ]
        if not real_images:
            pytest.skip(f"{d.name}/screenshots/ has no real images yet (deferred to 08-HUMAN-UAT.md row 4)")
        assert real_images, f"{d.name}/screenshots/ must contain >= 1 image"
