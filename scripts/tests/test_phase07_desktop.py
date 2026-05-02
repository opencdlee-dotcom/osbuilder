"""Tests for the desktop playbook (SCAF-04; phase 7 plan 04).

All tests SKIP (not error) before Wave 1 of plan 07-04 lands. That is by
design (TDD RED state). `scaffold_dispatch` is imported lazily inside the
`sd` fixture; the `has_desktop` fixture additionally skips when
`scaffold_desktop` has not yet been added.

The 6 tests here lock in:
  - presence of the playbook spec (.md, 7 sections, ≤ 80 lines, inline
    Tauri-not-Electron rationale per D-09)
  - subprocess argv shape of scaffold_desktop — verbatim 12-element
    create-tauri-app argv per D-07 (--manager pnpm, --template react-ts,
    --identifier <reverse-dns>, --tauri-version 2, -y)
  - ensure_pnpm runs BEFORE create-tauri-app (Pitfall 1)
  - Tauri CI workflow stamped post-scaffold (dtolnay/rust-toolchain)
  - reverse-DNS identifier sanitization rule (Pitfall 7) — pure function
    _build_tauri_identifier produces "com.osbuilder.<sanitized>".

Subprocess matchers use argv-list-element style (per element checks) not
loose " ".join substring scans, per STATE.md decision log (07-03).
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
        pytest.skip("scaffold_dispatch module not yet desktop-ready (Wave 1 target)")


@pytest.fixture
def has_desktop(sd):
    """Skips the test if scaffold_desktop hasn't been added yet (Wave 1 target)."""
    if not hasattr(sd, "scaffold_desktop"):
        pytest.skip("scaffold_desktop not yet added (Wave 1 target)")
    if not hasattr(sd, "_build_tauri_identifier"):
        pytest.skip("_build_tauri_identifier not yet added (Wave 1 target)")
    return sd


# ---------- 1. playbook .md presence + 7-section structure + ≤ 80 lines + D-09 ----------

def test_desktop_playbook_md_present():
    """SCAF-04: references/playbooks/desktop.md exists with 7 sections; ≤ 80 lines;
    contains inline Tauri-not-Electron rationale per D-09."""
    playbook = REPO_ROOT / "references" / "playbooks" / "desktop.md"
    if not playbook.exists():
        pytest.skip("references/playbooks/desktop.md not yet created (Wave 1 target)")
    content = playbook.read_text(encoding="utf-8")
    required_headings = [
        "## What the desktop playbook produces",
        "## Scaffold command",
        "## Post-scaffold files",
        "## Files OSBuilder must NOT write",
        "## Refuse list",
        "## Stack",
        "## See also",
    ]
    missing = [h for h in required_headings if h not in content]
    assert not missing, f"desktop.md missing required headings: {missing}"
    line_count = len(content.splitlines())
    assert line_count <= 80, (
        f"desktop.md must be ≤ 80 lines (progressive disclosure budget); got {line_count}"
    )
    # D-09: inline Tauri-not-Electron rationale (both terms must appear together)
    assert "Tauri 2" in content, (
        "desktop.md must mention 'Tauri 2' (D-09 inline rationale)"
    )
    assert "Electron" in content, (
        "desktop.md must mention 'Electron' for the refusal cross-reference (D-09)"
    )


# ---------- 2. scaffold_desktop subprocess argv shape (verbatim D-07 flag set) ----------

def test_scaffold_desktop_subprocess_calls(has_desktop, fake_shell, fake_which, tmp_path):
    """SCAF-04 D-07: scaffold_desktop runs `pnpm create tauri-app@latest <name>` with
    the verbatim flag set --manager pnpm --template react-ts --identifier <reverse-dns>
    --tauri-version 2 -y (verified by `npx --yes create-tauri-app --help` 2026-05-01).
    """
    sd = has_desktop
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create tauri-app", returncode=0, stdout="")
    sd.scaffold_desktop("test-app", tmp_path)

    # Find the create-tauri-app call by argv list-element matching
    tauri_calls = [
        c[0] for c in fake_shell.calls
        if isinstance(c[0], list)
        and len(c[0]) >= 4
        and c[0][0] == "pnpm"
        and any("tauri-app@latest" in tok for tok in c[0])
    ]
    assert len(tauri_calls) == 1, (
        f"Expected exactly 1 create-tauri-app call; got {tauri_calls}. "
        f"All calls: {[c[0] for c in fake_shell.calls]}"
    )
    cmd = tauri_calls[0]
    # Verbatim D-07 flag set
    assert "--manager" in cmd and cmd[cmd.index("--manager") + 1] == "pnpm", (
        "Must pass --manager pnpm (D-07)"
    )
    assert "--template" in cmd and cmd[cmd.index("--template") + 1] == "react-ts", (
        "Must pass --template react-ts (D-07)"
    )
    assert "--identifier" in cmd, "Missing --identifier flag (Pitfall 7)"
    assert cmd[cmd.index("--identifier") + 1] == "com.osbuilder.testapp", (
        f"--identifier must be reverse-DNS com.osbuilder.testapp (Pitfall 7); "
        f"got {cmd[cmd.index('--identifier') + 1]!r}"
    )
    assert "--tauri-version" in cmd and cmd[cmd.index("--tauri-version") + 1] == "2", (
        "Must pass --tauri-version 2 (D-07; pins Tauri major)"
    )
    assert "-y" in cmd, "Must pass -y for non-interactive (D-07)"


# ---------- 3. ensure_pnpm called BEFORE create-tauri-app (Pitfall 1) ----------

def test_scaffold_desktop_calls_ensure_pnpm(has_desktop, fake_shell, fake_which, tmp_path, monkeypatch):
    """SCAF-04 Pitfall 1: ensure_pnpm() must run BEFORE create-tauri-app.

    pnpm forwards --template cleanly; npm requires `--` to separate flags from
    the package name. The scaffold uses pnpm; ensure_pnpm is the install gate.
    """
    sd = has_desktop
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create tauri-app", returncode=0, stdout="")

    # Track whether ensure_pnpm was called
    called = {"ensure_pnpm": False, "before_create": False}
    real_ensure_pnpm = sd.ensure_pnpm

    def tracking_ensure_pnpm():
        called["ensure_pnpm"] = True
        # capture how many tauri-app calls have happened so far
        prior_tauri = sum(
            1 for c in fake_shell.calls
            if isinstance(c[0], list) and any("tauri-app@latest" in tok for tok in c[0])
        )
        called["before_create"] = (prior_tauri == 0)
        return real_ensure_pnpm()

    monkeypatch.setattr(sd, "ensure_pnpm", tracking_ensure_pnpm)
    sd.scaffold_desktop("test-app", tmp_path)
    assert called["ensure_pnpm"], "scaffold_desktop must call ensure_pnpm (Pitfall 1)"
    assert called["before_create"], (
        "ensure_pnpm must run BEFORE create-tauri-app (Pitfall 1)"
    )


# ---------- 4. tauri CI workflow stamped post-scaffold ----------

def test_scaffold_desktop_writes_tauri_ci(has_desktop, fake_shell, fake_which, tmp_path):
    """SCAF-04 SCL-04: scaffold writes Tauri CI workflow at .github/workflows/ci.yml
    (or test.yml) — content includes dtolnay/rust-toolchain action."""
    sd = has_desktop
    fake_which["pnpm"] = "/usr/local/bin/pnpm"
    fake_shell.program("pnpm create tauri-app", returncode=0, stdout="")
    project_dir = sd.scaffold_desktop("test-app", tmp_path)
    # Workflow location follows existing pattern (_write_ci_workflow writes to ci.yml)
    candidates = [
        project_dir / ".github" / "workflows" / "ci.yml",
        project_dir / ".github" / "workflows" / "test.yml",
        project_dir / ".github" / "workflows" / "tauri.yml",
    ]
    found = [p for p in candidates if p.exists()]
    assert found, (
        f"scaffold_desktop must stamp a Tauri CI workflow under "
        f"{project_dir}/.github/workflows/ — checked {[str(p) for p in candidates]}"
    )
    content = found[0].read_text(encoding="utf-8")
    assert "dtolnay/rust-toolchain" in content, (
        f"Tauri CI workflow must use dtolnay/rust-toolchain action; "
        f"got: {content[:200]!r}"
    )


# ---------- 5. _build_tauri_identifier — Pitfall 7 reverse-DNS rule ----------

def test_desktop_identifier_format(has_desktop):
    """Pitfall 7: reverse-DNS identifier required by Tauri bundler.

    Format: com.osbuilder.<sanitized> where sanitized = lowercase + remove
    hyphens + remove non-alphanumerics.
    """
    sd = has_desktop
    assert sd._build_tauri_identifier("my-cool-app") == "com.osbuilder.mycoolapp"
    assert sd._build_tauri_identifier("Test_App") == "com.osbuilder.testapp"
    assert sd._build_tauri_identifier("App-2-3") == "com.osbuilder.app23"


def test_desktop_identifier_strips_special_chars(has_desktop):
    """Pitfall 7 edge cases: underscores + mixed case all sanitized.

    `_build_tauri_identifier("My_App-2")` → `"com.osbuilder.myapp2"`
    (lowercased + hyphens removed + underscores removed).
    """
    sd = has_desktop
    assert sd._build_tauri_identifier("My_App-2") == "com.osbuilder.myapp2"
    # Idempotent on already-sanitized input
    assert sd._build_tauri_identifier("alreadyclean") == "com.osbuilder.alreadyclean"
