#!/usr/bin/env python3
"""run_demo.py — scripted OSBuilder pipeline run for the 60-second demo.

Drives the actual pipeline functions (intake_handler.parse_paragraph,
stack_researcher.research_stack, scaffold_dispatch.scaffold_web,
runbook_writer.write_readme) end-to-end against a fresh tmp project,
emitting the same dev-team narration banners /osbuilder uses at runtime.

This is the asset recorded by `asciinema rec assets/demo/osbuilder-demo.cast`
per assets/demo/RECORDING-CHECKLIST.md. The demo intentionally STOPS at
"ready to ship" rather than running `gh repo create`:

  - Pitfall 6 (no cuts hiding friction): a real `gh repo create` step would
    leak gh-auth state into the recording or require a throwaway-account
    setup most demo runners do not have. Showing the prepared command and
    letting the viewer execute it themselves is the honest stopping point.
  - The cli scaffold already works end-to-end against a real repo via the
    Phase 6 ship flow; this demo proves the upstream pipeline.

Usage (interactive demo):

    asciinema rec assets/demo/osbuilder-demo.cast \\
      -c "python3 scripts/demo/run_demo.py"
    agg --speed 2 assets/demo/osbuilder-demo.cast \\
      assets/demo/osbuilder-demo.gif

Pure stdlib + the existing OSBuilder helpers — no third-party deps.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import sys
import time
from pathlib import Path


@contextlib.contextmanager
def _silenced_stdout():
    """Redirect file-descriptor 1 to /dev/null so child subprocesses (state_writer
    CLI confirmations like `set X=Y`) stay quiet during demo recording. Python-level
    print() calls outside this block are unaffected, so narration stays visible.
    """
    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        os.dup2(saved, 1)
        os.close(devnull)
        os.close(saved)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import intake_handler  # noqa: E402
import narration  # noqa: E402
import runbook_writer  # noqa: E402
import scaffold_dispatch  # noqa: E402
import stack_researcher  # noqa: E402


PARAGRAPH = (
    "I want a TODO web app where I can add tasks and check them off. "
    "It should work on my phone too, and I want my tasks to still be "
    "there if I close the browser and come back tomorrow."
)
PROJECT_NAME = "demo-todo-app"


def _slow_print(text: str, gap: float = 0.04) -> None:
    """Print one char at a time so asciinema captures the typing pace."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(gap)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _seed_state(project_root: Path) -> None:
    osd = project_root / ".planning" / "osbuilder"
    osd.mkdir(parents=True, exist_ok=True)
    (osd / "state.md").write_text(
        "mode: beginner\n"
        "goal:\n"
        "app_type:\n"
        "playbook:\n"
        "current_role:\n"
        "current_phase:\n"
        "phase_step:\n"
        "last_failure:\n"
        "retry_count: 0\n"
        "escalation_level: 0\n"
        "next_action:\n",
        encoding="utf-8",
    )


def main() -> int:
    project_root = Path("/tmp/osbuilder-demo")
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True)
    _seed_state(project_root)

    started = time.perf_counter()

    print()
    _slow_print(f"$ /osbuilder {PARAGRAPH}", gap=0.015)
    print()

    narration.emit("pm", "intake-spec", "start")
    intake_handler.parse_paragraph(PARAGRAPH, project_root=project_root)
    narration.emit("pm", "intake-spec", "ok")

    narration.emit("architect", "research-stack", "start")
    with _silenced_stdout():
        stack_researcher.research_stack("web", project_root=project_root)
    narration.emit("architect", "research-stack", "ok")

    narration.emit("devops", "scaffold-web", "start")
    project_dir = scaffold_dispatch.scaffold_web(PROJECT_NAME, project_root)
    narration.emit("devops", "scaffold-web", "ok")

    # Seed the few state fields the runbook stamper expects so the README
    # renders concrete commands (no leftover OSBuilder placeholders).
    import subprocess
    SW = REPO_ROOT / "scripts" / "state_writer.py"
    for field, value in (
        ("goal", PARAGRAPH),
        ("app_type", "web"),
        ("playbook", "web"),
        ("repo_url", f"https://github.com/<your-account>/{PROJECT_NAME}"),
    ):
        subprocess.run(
            [sys.executable, str(SW), "write", "--field", field, "--value", value,
             "--project-root", str(project_root)],
            check=False, capture_output=True,
        )

    narration.emit("tech-writer", "write-readme", "start")
    runbook_writer.write_readme(project_dir, project_root)
    narration.emit("tech-writer", "write-readme", "ok")

    elapsed = time.perf_counter() - started

    print()
    _slow_print("Ready to ship.", gap=0.03)
    print()
    print(f"  Project:  {project_dir}")
    print(f"  Pipeline: {elapsed:.1f}s (parse -> research -> scaffold -> README)")
    print()
    _slow_print("Next step (you run this):", gap=0.025)
    print()
    print(f"  cd {project_dir}")
    print("  gh repo create --private --source=. --push")
    print()
    _slow_print("That ships it to a private GitHub repo. Done.", gap=0.025)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
