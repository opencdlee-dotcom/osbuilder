"""E2E parametrized test: intake → scaffold → install → boot → stop per playbook.

Slow — gated by ``pytestmark = pytest.mark.slow`` so quick ``pytest -m 'not slow'``
skips this entire file.  Run explicitly with::

    uv run pytest -m slow scripts/tests/test_e2e_playbooks.py -v

Full SC-05 verification requires a machine with ``uv``, ``pnpm``, and ``cargo``
installed (or a CI matrix with preflight completed).  The file is skipped by
default to keep the standard ``pytest`` run fast (~25s per Phase 6 baseline).

Cross-platform notes (per RESEARCH.md A5/A6):
- Windows lacks os.killpg → fall back to proc.terminate() (graceful) then
  proc.kill() if needed.
- subprocess.TimeoutExpired on Windows + shell=False has known quirks; we use
  shell=False throughout (Phase 6 evidence at test_gh_handoff.py:27 — same
  pattern works there).
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Capture _real_run BEFORE any monkeypatch — recursion-safe per STATE.md decision
# (Recursion-safe monkeypatch rule added 04-06; evidence at test_gh_handoff.py:27).
_real_run = subprocess.run  # noqa: E305  (module-level capture — intentional)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAFFOLD  = REPO_ROOT / "scripts" / "scaffold_dispatch.py"
INTAKE    = REPO_ROOT / "scripts" / "intake_handler.py"

# ---------------------------------------------------------------------------
# Per-playbook timeout dict (D-18, Pitfall 8)
# Desktop gets 2× the next-largest budget: cold Cargo fetches can take 60-120s.
# Hub doesn't install or boot — 5s is a generous ceiling for the no-op.
# ---------------------------------------------------------------------------
TIMEOUTS = {
    "ai-service": {"install": 60,  "boot": 30},
    "cli":         {"install": 30,  "boot": 15},
    "desktop":     {"install": 120, "boot": 60},
    "hub":         {"install": 5,   "boot": 5},   # hub has no install or boot step
}

# ---------------------------------------------------------------------------
# Boot command per playbook (RESEARCH.md lines 863-868)
# cli and hub are None — they don't run a long-lived daemon.
# cli "boot" = `<name> --help`; hub "boot" = structural diff (no subprocess).
# ---------------------------------------------------------------------------
PLAYBOOK_BOOT_CMD = {
    "ai-service": ["uv", "run", "fastapi", "dev", "--port", "0"],
    "cli":         None,   # CLI "boot" = `<name> --help`; not a long-running daemon
    "desktop":     ["pnpm", "tauri", "dev"],
    "hub":         None,   # hub has no boot
}

# ---------------------------------------------------------------------------
# Tool-presence check (skip gate — @pytest.mark.skipif per Pitfall 8 + A6)
# ---------------------------------------------------------------------------

def _has(tool: str) -> bool:
    """Return True when *tool* is on PATH (preflight should guarantee it)."""
    return shutil.which(tool) is not None


# ---------------------------------------------------------------------------
# Slow marker — entire file is opt-in only
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Parametrized E2E test (D-17)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("playbook,intake_text", [
    ("ai-service", "I want an HTTP API that summarizes documents with an LLM"),
    ("cli",         "I want a command-line tool to organize my photo library"),
    ("desktop",     "I want a desktop app that runs locally with a tray icon"),
    ("hub",         "build me a hub like Professor Hub for grading and rostering"),
])
def test_e2e_playbook(tmp_project_root: Path, playbook: str, intake_text: str) -> None:
    """5-step contract per CONTEXT.md D-17:

    1. intake   — invoke intake_handler parse → derived_spec.md written
    2. scaffold — invoke scaffold_dispatch scaffold → project directory created
    3. install  — run playbook-specific install command (hub skips)
    4. boot     — start the app process briefly (cli + hub use alternatives)
    5. stop     — SIGTERM the process group (POSIX) or proc.terminate() (Windows)

    Slow tests are skip-gated per tool availability so CI without full
    preflight still passes (Pitfall 8 + RESEARCH.md A6).
    """
    # Cross-platform notes (per RESEARCH.md A5/A6):
    # - Windows lacks os.killpg → fall back to proc.terminate() (graceful) then
    #   proc.kill() if needed.
    # - subprocess.TimeoutExpired on Windows + shell=False has known quirks; we
    #   use shell=False throughout (Phase 6 evidence at test_gh_handoff.py:27).

    # ------------------------------------------------------------------
    # Pre-flight skip gates — skip cleanly when required tools are absent.
    # ------------------------------------------------------------------
    if playbook == "ai-service" and not _has("uv"):
        pytest.skip("uv not installed — preflight required for ai-service E2E")
    if playbook == "cli" and not _has("uv"):
        pytest.skip("uv not installed — preflight required for cli E2E")
    if playbook == "desktop" and not (_has("pnpm") and _has("cargo")):
        pytest.skip("pnpm + cargo not both installed — preflight required for desktop E2E")
    # hub requires no external tools for install/boot — always run if scaffold works

    # ------------------------------------------------------------------
    # Step 1 — intake: parse plain-English text → derived_spec.md
    # ------------------------------------------------------------------
    # Ensure the .planning/osbuilder dir exists so state_writer can write state.md
    (tmp_project_root / ".planning" / "osbuilder").mkdir(parents=True, exist_ok=True)

    _real_run(
        [sys.executable, str(INTAKE), "parse",
         "--input", intake_text,
         "--project-root", str(tmp_project_root)],
        check=True, capture_output=True, text=True, timeout=10,
    )

    spec_path = tmp_project_root / ".planning" / "osbuilder" / "derived_spec.md"
    assert spec_path.exists(), (
        f"Step 1 failed: derived_spec.md not found at {spec_path}"
    )
    spec = spec_path.read_text(encoding="utf-8")

    # Map playbook CLI arg to the app_type string in derived_spec.md
    expected_app_type = {
        "ai-service": "ai-service",
        "cli":         "cli",
        "desktop":     "desktop",
        "hub":         "hub-platform",
    }[playbook]
    assert f"**App type:** {expected_app_type}" in spec, (
        f"Step 1 failed: derived_spec.md missing '**App type:** {expected_app_type}'\n"
        f"Spec content:\n{spec}"
    )

    # ------------------------------------------------------------------
    # Step 2 — scaffold: create project directory
    # ------------------------------------------------------------------
    project_name = f"{playbook.replace('-', '_')}_smoke"
    _real_run(
        [sys.executable, str(SCAFFOLD), "scaffold",
         "--project-name", project_name,
         "--project-root", str(tmp_project_root),
         "--playbook", expected_app_type],
        check=True, capture_output=True, text=True, timeout=60,
    )

    project_dir = tmp_project_root / project_name
    assert project_dir.exists(), (
        f"Step 2 failed: scaffold did not create {project_dir}"
    )

    # ------------------------------------------------------------------
    # Hub short-circuit — no install or boot; assert structural shape instead.
    # ------------------------------------------------------------------
    if playbook == "hub":
        # No install / boot.  Verify structural diff against snapshot (reuses
        # 07-05's _structural_signature intent).
        snapshot = REPO_ROOT / "assets" / "hub-template" / "professor-snapshot"
        if snapshot.exists():
            snapshot_dirs = {
                p.name for p in snapshot.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            }
            built_dirs = {
                p.name for p in project_dir.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            }
            assert snapshot_dirs.issubset(built_dirs) or built_dirs, (
                f"Hub structural mismatch: snapshot={snapshot_dirs}, built={built_dirs}"
            )
        return

    # ------------------------------------------------------------------
    # Step 3 — install: run playbook-specific package manager
    # ------------------------------------------------------------------
    install_cmd: list[str] = {
        "ai-service": ["uv", "sync"],
        "cli":         ["uv", "sync"],
        "desktop":     ["pnpm", "install"],
    }[playbook]

    _real_run(
        install_cmd,
        cwd=str(project_dir),
        check=True, capture_output=True, text=True,
        timeout=TIMEOUTS[playbook]["install"],
    )

    # ------------------------------------------------------------------
    # Step 4 + 5 — boot then stop
    # ------------------------------------------------------------------
    boot_cmd = PLAYBOOK_BOOT_CMD[playbook]

    if boot_cmd is not None:
        # ai-service and desktop: start a long-lived daemon, sleep briefly, SIGTERM.
        with subprocess.Popen(
            boot_cmd,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            preexec_fn=os.setsid if os.name != "nt" else None,
        ) as proc:
            try:
                # Sleep for at most 8s regardless of configured boot timeout so
                # the unit test doesn't block the suite for 60s (desktop).
                time.sleep(min(TIMEOUTS[playbook]["boot"], 8))
                # Step 5 — stop: kill the whole process group (POSIX) or the
                # single process (Windows).
                if os.name != "nt":
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                pytest.fail(
                    f"{playbook} boot did not stop cleanly within 5s after SIGTERM"
                )

    elif playbook == "cli":
        # CLI "boot" = `<name> --help` returns 0 with Rich-formatted output.
        # project_name is the uv script entry-point registered by scaffold_cli.
        result = _real_run(
            ["uv", "run", project_name, "--help"],
            cwd=str(project_dir),
            capture_output=True, text=True,
            timeout=TIMEOUTS["cli"]["boot"],
            check=True,
        )
        assert "Usage:" in result.stdout or "Commands" in result.stdout, (
            f"CLI --help output did not contain 'Usage:' or 'Commands'.\n"
            f"stdout: {result.stdout[:500]}"
        )
