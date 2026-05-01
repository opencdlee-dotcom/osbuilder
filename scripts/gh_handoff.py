#!/usr/bin/env python3
"""gh_handoff.py — OSBuilder GitHub handoff (ship to private repo + verify) (SHIP-01, SHIP-03, SHIP-04, SHIP-05).

Pure stdlib. Subcommands: ship, verify.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Phase 6: friendly-error translation layer (graceful degrade if module not yet built)
try:
    import friendly_error as _fe
except ImportError:
    _fe = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_WRITER = REPO_ROOT / "scripts" / "state_writer.py"
ASSETS = REPO_ROOT / "assets"
GITLEAKS_REV = "v8.30.1"  # locked decision D-09; pinned via assets/gitleaks/.pre-commit-config.yaml

# OSBuilder default markers for idempotency (do not change without bumping all stamping helpers)
_GITIGNORE_MARKER = "# OSBuilder default"

# Token-redaction pattern (T-06-02-03: prevent accidental gh token disclosure in stderr)
_TOKEN_RE = re.compile(r"gh[ps]_[A-Za-z0-9_]{20,}")


# ---------- helpers (verbatim duplicates per project policy D-05) ----------

def _resolve_project_root(arg: str | None) -> Path:
    if arg is None:
        cur = Path.cwd().resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".planning").is_dir():
                return parent
        return cur
    if ".." in arg:
        raise SystemExit("OSBuilder: --project-root cannot contain '..' segments.")
    return Path(arg).resolve()


def atomic_write(path: Path, content: str) -> None:
    """Atomic file write via os.replace (atomic on POSIX + Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.stem}.{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _write_state_field(project_root: Path, field: str, value: str) -> None:
    """Write a single field to state.md via state_writer write subcommand."""
    subprocess.run(
        [sys.executable, str(STATE_WRITER), "write",
         "--field", field, "--value", value,
         "--project-root", str(project_root)],
        shell=False, check=True,
    )


# ---------- friendly-error wrapper ----------

def _friendly(raw: str, *, tool: str = "gh") -> None:
    """Route a raw error string to friendly_error.translate() and write to stderr.

    Falls back to plain stderr write if friendly_error is unavailable (graceful degrade).
    Redacts gh tokens before routing (T-06-02-03).
    """
    # T-06-02-03: redact tokens before logging
    raw = _TOKEN_RE.sub("[REDACTED-TOKEN]", raw)
    if _fe is not None:
        msg = _fe.translate(raw, ctx={"tool": tool})
        sys.stderr.write(
            f"## {msg.title}\n{msg.what_broke}\n\n"
            f"**What to do:** {msg.what_to_do}\n"
        )
        if msg.copy_paste:
            sys.stderr.write(f"\n  {msg.copy_paste}\n")
    else:
        sys.stderr.write(f"OSBuilder: {tool} failed — {raw}\n")


# ---------- stamp helpers ----------

def _compose_gitignore(project_dir: Path, stack_family: str = "node") -> None:
    """Compose .gitignore from common + stack-family templates (SHIP-03).

    stack_family: "node" or "python".
    Idempotent: if .gitignore already contains _GITIGNORE_MARKER, skip.
    """
    common = (ASSETS / "gitignore-templates" / "common.gitignore").read_text(encoding="utf-8")
    lang = (ASSETS / "gitignore-templates" / f"{stack_family}.gitignore").read_text(encoding="utf-8")
    composed = (
        f"{_GITIGNORE_MARKER} — common\n"
        + common.strip() + "\n\n"
        + f"{_GITIGNORE_MARKER} — {stack_family}\n"
        + lang.strip() + "\n"
    )
    target = project_dir / ".gitignore"
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if _GITIGNORE_MARKER in existing:
            return  # already stamped (idempotent)
        composed = composed + "\n# --- existing .gitignore ---\n" + existing
    atomic_write(target, composed)


def _install_gitleaks_hook(project_dir: Path) -> None:
    """Stamp .pre-commit-config.yaml + .gitleaks.toml in the built repo (SHIP-04).

    Does NOT auto-install the hook (per RESEARCH Pitfall 2 + Anti-Pattern: hook
    activation is documented in README runbook via `pre-commit install`).
    """
    pre_commit_src = (ASSETS / "gitleaks" / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    gitleaks_src = (ASSETS / "gitleaks" / ".gitleaks.toml").read_text(encoding="utf-8")
    atomic_write(project_dir / ".pre-commit-config.yaml", pre_commit_src)
    atomic_write(project_dir / ".gitleaks.toml", gitleaks_src)


# ---------- public API ----------

def ship(project_dir: Path, project_root: Path, *, private: bool = True,
         stack_family: str = "node") -> int:
    """Run the terminal ship pipeline: preflight + stamp + commit + create + push + verify.

    Returns 0 on success, 1 on failure. Idempotent: re-running on an already-pushed
    project_dir is a no-op (detected via `git remote get-url origin`).

    Steps:
      1. SHIP-05 — gh auth status preflight (per D-08)
      2. SHIP-03 + SHIP-04 — stamp .gitignore + .pre-commit-config.yaml + .gitleaks.toml
      3. git init -b main + git add -A + git commit (only if dirty)
      4. SHIP-01 — gh repo create --private --source=. --push (only if remote not set)
      5. Verify via `gh repo view --json visibility,nameWithOwner,sshUrl`
      6. Persist state.md fields: repo_visibility, repo_url, gh_auth_status, pre_commit_installed
    """
    # 1. SHIP-05 preflight: gh auth status
    try:
        auth = subprocess.run(
            ["gh", "auth", "status"],
            shell=False, capture_output=True, text=True,
        )
    except (FileNotFoundError, OSError) as e:
        _friendly(f"gh: command not found: {e}", tool="gh")
        _write_state_field(project_root, "gh_auth_status", "unauthenticated")
        return 1
    if auth.returncode != 0:
        raw = (auth.stderr or "").strip() or f"gh auth status exit {auth.returncode}"
        _friendly(raw, tool="gh")
        _write_state_field(project_root, "gh_auth_status", "drift")
        return 1
    _write_state_field(project_root, "gh_auth_status", "ok")

    # 2. SHIP-03 + SHIP-04 — stamp .gitignore + gitleaks files
    _compose_gitignore(project_dir, stack_family)
    _install_gitleaks_hook(project_dir)
    _write_state_field(project_root, "pre_commit_installed", "true")

    # 3. git init + commit (idempotent)
    if not (project_dir / ".git").is_dir():
        init = subprocess.run(
            ["git", "init", "-b", "main"], cwd=str(project_dir),
            shell=False, capture_output=True, text=True,
        )
        if init.returncode != 0:
            _friendly((init.stderr or "git init failed").strip(), tool="git")
            return 1
    add = subprocess.run(
        ["git", "add", "-A"], cwd=str(project_dir),
        shell=False, capture_output=True, text=True,
    )
    if add.returncode != 0:
        _friendly((add.stderr or "git add failed").strip(), tool="git")
        return 1
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(project_dir),
        shell=False, capture_output=True, text=True,
    )
    if status.returncode != 0:
        _friendly((status.stderr or "git status failed").strip(), tool="git")
        return 1
    if status.stdout.strip():
        commit = subprocess.run(
            ["git", "commit", "-m", "chore: initial scaffold by OSBuilder"],
            cwd=str(project_dir), shell=False, capture_output=True, text=True,
        )
        if commit.returncode != 0:
            _friendly((commit.stderr or "git commit failed").strip(), tool="git")
            return 1

    # 4. SHIP-01 — gh repo create (idempotent: skip if remote already exists)
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=str(project_dir),
        shell=False, capture_output=True, text=True,
    )
    if remote.returncode != 0:  # no origin → create
        visibility_flag = "--private" if private else "--public"
        create = subprocess.run(
            ["gh", "repo", "create",
             f"--source={project_dir}",
             "--remote=origin",
             "--push",
             visibility_flag],
            shell=False, capture_output=True, text=True,
        )
        if create.returncode != 0:
            raw = (create.stderr or "").strip() or f"gh repo create exit {create.returncode}"
            _friendly(raw, tool="gh")
            return 1

    # 5. Verify visibility
    view = subprocess.run(
        ["gh", "repo", "view", "--json", "visibility,nameWithOwner,sshUrl"],
        cwd=str(project_dir), shell=False, capture_output=True, text=True,
    )
    if view.returncode != 0:
        _friendly((view.stderr or "gh repo view failed").strip(), tool="gh")
        return 1
    try:
        repo_info = json.loads(view.stdout)
    except json.JSONDecodeError as e:
        _friendly(f"gh repo view returned non-JSON output: {e}", tool="gh")
        return 1
    visibility = repo_info.get("visibility", "")
    ssh_url = repo_info.get("sshUrl", "")
    if visibility not in ("PRIVATE", "PUBLIC"):
        _friendly(f"gh repo view returned unexpected visibility: {visibility!r}", tool="gh")
        return 1

    # 6. Persist to state.md (sanitize URL: strip newlines per Pitfall 7)
    _write_state_field(project_root, "repo_visibility", visibility)
    _write_state_field(project_root, "repo_url", ssh_url.strip().replace("\n", " "))
    return 0


def verify(project_dir: Path) -> dict:
    """Re-run `gh repo view --json visibility,nameWithOwner,sshUrl` and return parsed dict.

    Returns {} on any failure (caller checks for "visibility" key).
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "visibility,nameWithOwner,sshUrl"],
            cwd=str(project_dir), shell=False, capture_output=True, text=True,
        )
        if result.returncode != 0:
            return {}
        return json.loads(result.stdout)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}


# ---------- CLI ----------

def _cmd_ship(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    project_dir = project_root / args.project_name
    if not project_dir.is_dir():
        _friendly(f"project_dir does not exist: {project_dir}", tool="osbuilder")
        return 1
    return ship(project_dir, project_root,
                private=not args.public,
                stack_family=args.stack_family)


def _cmd_verify(args: argparse.Namespace) -> int:
    project_root = _resolve_project_root(args.project_root)
    project_dir = project_root / args.project_name
    info = verify(project_dir)
    if not info:
        sys.stderr.write("OSBuilder: gh repo view failed or returned empty.\n")
        return 1
    print(json.dumps(info))
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="gh_handoff",
        description="OSBuilder GitHub handoff (ship to private repo + verify).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_ship = sub.add_parser("ship", help="Create/push private GitHub repo from a built project.")
    p_ship.add_argument("--project-name", required=True, dest="project_name")
    p_ship.add_argument("--project-root", default=None, dest="project_root")
    p_ship.add_argument("--public", action="store_true",
                        help="Create a public repo instead of the locked-default private.")
    p_ship.add_argument("--stack-family", default="node", choices=("node", "python"),
                        dest="stack_family")
    p_ship.set_defaults(func=_cmd_ship)

    p_verify = sub.add_parser("verify", help="Re-check repo visibility via `gh repo view`.")
    p_verify.add_argument("--project-name", required=True, dest="project_name")
    p_verify.add_argument("--project-root", default=None, dest="project_root")
    p_verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
