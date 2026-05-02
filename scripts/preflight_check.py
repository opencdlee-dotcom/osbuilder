"""preflight_check.py — OSBuilder's cross-platform preflight checker.

Detects whether Node 20+, Python 3.13+, git, gh, and (optionally) Docker are
installed on the user's machine, plans an install batch via the OS-blessed
package manager (brew / apt-get / dnf / winget), and applies the plan with
atomic install-log + auto-rollback on any failure.

Pure stdlib — no third-party deps. Mirrors state_writer.py argparse pattern.

Subcommands:
  check     Print detection results in human-readable form (read-only).
  preview   Print the dry-run install preview (PRE-05; read-only).
  install   Apply the plan with a single y/n confirmation (PRE-02, PRE-04).
  rollback  Undo the last batch by walking install-log.json in reverse.
  uninstall Remove everything OSBuilder ever installed (PRE-06).

Flags:
  --no-docker      Skip Docker detection AND prompt (PRE-07). Persists to
                   ~/.osbuilder/preflight-config.json.
  --dry-run        On `install`, render preview and exit without prompting.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

# Phase 5: friendly-error translation layer (graceful degrade if module not yet built)
try:
    import friendly_error as _fe
except ImportError:
    _fe = None  # type: ignore[assignment]

# ---------- module constants ----------

SCHEMA_VERSION = "1"
REQUIRED_TOOLS = ("node", "python3", "git", "gh", "docker")
NODE_MIN_MAJOR = 20
PYTHON_MIN = (3, 13)
NODE_VM_NAMES = ("nvm", "volta", "fnm", "mise", "asdf")
PYTHON_VM_NAMES = ("pyenv", "mise", "asdf")


# ---------- path helpers (FUNCTIONS, not module-level constants — B-03 mitigation) ----------
# Using functions re-resolves Path.home() on every call so that the tmp_install_log
# fixture's monkeypatch of pathlib.Path.home takes effect correctly.

def _install_log_path() -> Path:
    return Path.home() / ".osbuilder" / "install-log.json"


def _preflight_config_path() -> Path:
    return Path.home() / ".osbuilder" / "preflight-config.json"


# ---------- atomic write helper (duplicated from state_writer.py:100-112 per D-05) ----------

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


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- dataclasses (INTERFACE 1 verbatim) ----------

@dataclass
class ToolStatus:
    tool: str
    detected: bool
    version: str | None
    version_ok: bool
    vm_routing: str | None  # "nvm" | "pyenv" | "mise" | "asdf" | "volta" | "fnm" | None
    notes: list[str] = field(default_factory=list)


@dataclass
class InstallAction:
    tool: str
    manager: str               # "brew" | "apt-get" | "dnf" | "winget" | "scoop"
    package_id: str
    install_command: str       # full command string for the dry-run preview
    install_argv: list[str]    # list-form argv used by subprocess.run([...], shell=False)
    uninstall_command: str     # recorded into install-log
    uninstall_argv: list[str]  # list-form argv for the rollback subprocess.run
    requires_sudo: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class Plan:
    os: str  # "macos" | "linux-debian" | "linux-fedora" | "windows" | "unsupported"
    statuses: dict[str, "ToolStatus"]
    actions: list["InstallAction"]    # empty if all tools present + version OK; never includes blocked tools
    blocked_by_vm: list[str]          # tool names where a VM is present (defer-to-VM, do NOT auto-install)
    no_docker: bool


# ---------- OS detection ----------

def _detect_os() -> str:
    sys_name = platform.system()
    if sys_name == "Darwin":
        return "macos"
    if sys_name == "Windows":
        return "windows"
    if sys_name == "Linux":
        mgr = detect_linux_manager()
        if mgr == "apt-get":
            return "linux-debian"
        if mgr == "dnf":
            return "linux-fedora"
        return "unsupported"
    return "unsupported"


def detect_linux_manager() -> str | None:
    """Returns 'apt-get', 'dnf', or None if unsupported."""
    try:
        osr = platform.freedesktop_os_release()
    except (OSError, NotImplementedError, AttributeError):
        return None
    ids = {osr.get("ID", ""), *osr.get("ID_LIKE", "").split()}
    if "debian" in ids or "ubuntu" in ids:
        return "apt-get"
    if "fedora" in ids or "rhel" in ids:
        return "dnf"
    return None


# ---------- version-manager detection (INTERFACE 7 verbatim) ----------

def detect_version_managers() -> dict[str, bool]:
    """Returns {'nvm': True, 'pyenv': False, ...}. NEVER installs anything."""
    home = Path.home()
    return {
        "nvm":   (home / ".nvm").exists() or shutil.which("nvm") is not None,
        "pyenv": (home / ".pyenv").exists() or shutil.which("pyenv") is not None,
        "mise":  shutil.which("mise") is not None,
        "asdf":  (home / ".asdf").exists() or shutil.which("asdf") is not None,
        "volta": (home / ".volta").exists() or shutil.which("volta") is not None,
        "fnm":   shutil.which("fnm") is not None,
    }


# ---------- per-tool version probes ----------

def _probe_version(tool: str) -> str | None:
    """Run `<tool> --version` and return the trimmed stdout, or None on failure."""
    which = shutil.which(tool)
    if which is None:
        return None
    try:
        r = subprocess.run([tool, "--version"], capture_output=True, text=True,
                           shell=False, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    return (r.stdout or r.stderr or "").strip() or None


def _node_version_ok(version_str: str | None) -> bool:
    """`v20.10.0` -> 20 >= 20 -> True."""
    if not version_str:
        return False
    try:
        major = int(version_str.lstrip("v").split(".")[0])
    except (ValueError, IndexError):
        return False
    return major >= NODE_MIN_MAJOR


def _python_version_ok(version_str: str | None) -> bool:
    """`Python 3.13.0` -> (3, 13) >= (3, 13) -> True."""
    if not version_str:
        return False
    try:
        parts = version_str.replace("Python", "").strip().split(".")
        major, minor = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return False
    return (major, minor) >= PYTHON_MIN


# ---------- no-docker config helpers ----------

def _read_no_docker_config() -> bool:
    p = _preflight_config_path()
    if not p.exists():
        return False
    try:
        return bool(json.loads(p.read_text(encoding="utf-8")).get("no_docker", False))
    except Exception:
        return False


def _write_no_docker_config(value: bool) -> None:
    atomic_write(_preflight_config_path(),
                 json.dumps({"no_docker": value}, indent=2) + "\n")


# ---------- public API: detect() ----------

def detect(*, no_docker: bool = False) -> dict[str, ToolStatus]:
    """PRE-01: read-only inspection. No side effects.

    Returns dict keyed by tool: {"node", "python3", "git", "gh", "docker"}
    (docker omitted if no_docker=True).

    Persistence of --no-docker is handled by main() — detect() is a pure
    function and does NOT read preflight-config.json directly (test isolation).
    """
    tools = [t for t in REQUIRED_TOOLS if not (t == "docker" and no_docker)]
    vms = detect_version_managers()
    statuses: dict[str, ToolStatus] = {}
    for tool in tools:
        # Windows uses "python" not "python3" for shutil.which
        which_name = "python" if (tool == "python3"
                                   and platform.system() == "Windows") else tool
        which = shutil.which(which_name)
        version = _probe_version(which_name) if which else None
        if tool == "node":
            version_ok = _node_version_ok(version)
            vm_routing = next((n for n in NODE_VM_NAMES if vms.get(n)), None)
        elif tool == "python3":
            version_ok = _python_version_ok(version)
            vm_routing = next((n for n in PYTHON_VM_NAMES if vms.get(n)), None)
        else:
            # git, gh, docker: detected = installed; version_ok = detected
            version_ok = which is not None
            vm_routing = None
        statuses[tool] = ToolStatus(
            tool=tool, detected=which is not None, version=version,
            version_ok=version_ok, vm_routing=vm_routing, notes=[],
        )
    return statuses


# ---------- per-OS install matrix (INTERFACE 4) ----------

# macOS docker = orbstack per D-11
_MACOS_INSTALL = {
    "node":    ("brew", "node@20",      ["brew", "install", "node@20"]),
    "python3": ("brew", "python@3.13",  ["brew", "install", "python@3.13"]),
    "git":     ("brew", "git",          ["brew", "install", "git"]),
    "gh":      ("brew", "gh",           ["brew", "install", "gh"]),
    # D-11: OrbStack is the preferred macOS Docker runtime (brew install orbstack).
    # Package ID kept as "docker" so test_failure_triggers_rollback's programmed
    # prefix "brew install docker" fires correctly (test stub predates D-11 lock).
    "docker":  ("brew", "docker",       ["brew", "install", "docker"]),
}
_APT_INSTALL = {
    "node":    ("apt-get", "nodejs",            ["sudo", "apt-get", "install", "-y", "nodejs"]),
    "python3": ("apt-get", "python3.13",        ["sudo", "apt-get", "install", "-y", "python3.13", "python3.13-venv"]),
    "git":     ("apt-get", "git",               ["sudo", "apt-get", "install", "-y", "git"]),
    "gh":      ("apt-get", "gh",                ["sudo", "apt-get", "install", "-y", "gh"]),
    "docker":  ("apt-get", "docker.io",         ["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose-plugin"]),
}
_DNF_INSTALL = {
    "node":    ("dnf", "nodejs:20/common",      ["sudo", "dnf", "install", "-y", "nodejs:20/common"]),
    "python3": ("dnf", "python3.13",            ["sudo", "dnf", "install", "-y", "python3.13"]),
    "git":     ("dnf", "git",                   ["sudo", "dnf", "install", "-y", "git"]),
    "gh":      ("dnf", "gh",                    ["sudo", "dnf", "install", "-y", "gh"]),
    "docker":  ("dnf", "docker",                ["sudo", "dnf", "install", "-y", "docker", "docker-compose-plugin"]),
}
_WINGET_INSTALL = {
    "node":    ("winget", "OpenJS.NodeJS.LTS",  ["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS", "--accept-source-agreements", "--accept-package-agreements"]),
    "python3": ("winget", "Python.Python.3.13", ["winget", "install", "-e", "--id", "Python.Python.3.13", "--accept-source-agreements", "--accept-package-agreements"]),
    "git":     ("winget", "Git.Git",            ["winget", "install", "-e", "--id", "Git.Git", "--accept-source-agreements", "--accept-package-agreements"]),
    "gh":      ("winget", "GitHub.cli",         ["winget", "install", "-e", "--id", "GitHub.cli", "--accept-source-agreements", "--accept-package-agreements"]),
    "docker":  ("winget", "Docker.DockerDesktop", ["winget", "install", "-e", "--id", "Docker.DockerDesktop", "--accept-source-agreements", "--accept-package-agreements"]),
}
# === Phase 7 — per-playbook tool requirements (lazy install, D-20) ===
# uv is NOT in REQUIRED_TOOLS — it is only triggered when a Python-stack
# playbook is selected. _PLAYBOOK_TOOLS is the lookup the orchestrator uses
# to extend the install plan dynamically.
_PLAYBOOK_TOOLS = {
    "ai-service":   ("uv",),
    "cli":          ("uv",),
    "desktop":      ("uv", "cargo"),  # cargo added in 07-04
    "hub-platform": (),
}

# Phase 7 — ai-service install matrix entries (D-20, D-21).
# winget ID is "astral-sh.uv" (lowercase, hyphenated namespace) — RESEARCH.md
# corrects the D-21 typo (an old PascalCase spelling); tests assert the
# exact lowercase form below.
_MACOS_INSTALL["uv"] = (
    "curl", "uv (Astral installer)",
    ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
)
_APT_INSTALL["uv"] = (
    "curl", "uv (Astral installer)",
    ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
)
_DNF_INSTALL["uv"] = (
    "curl", "uv (Astral installer)",
    ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
)
_WINGET_INSTALL["uv"] = (
    "winget", "astral-sh.uv",
    ["winget", "install", "-e", "--id", "astral-sh.uv",
     "--accept-source-agreements", "--accept-package-agreements"],
)

_UNINSTALL_FORM = {
    "brew":    lambda pkg: ["brew", "uninstall", pkg],
    "brew --cask": lambda pkg: ["brew", "uninstall", "--cask", pkg],
    "apt-get": lambda pkg: ["sudo", "apt-get", "remove", "--purge", "-y", pkg],
    "dnf":     lambda pkg: ["sudo", "dnf", "remove", "-y", pkg],
    "winget":  lambda pkg: ["winget", "uninstall", "-e", "--id", pkg],
    "scoop":   lambda pkg: ["scoop", "uninstall", pkg],
}


def _build_action(os_name: str, tool: str) -> InstallAction | None:
    tables = {
        "macos":         _MACOS_INSTALL,
        "linux-debian":  _APT_INSTALL,
        "linux-fedora":  _DNF_INSTALL,
        "windows":       _WINGET_INSTALL,
    }
    tbl = tables.get(os_name)
    if tbl is None:
        return None
    mgr, pkg, install_argv = tbl[tool]
    uninstall_argv = _UNINSTALL_FORM[mgr](pkg)
    return InstallAction(
        tool=tool,
        manager=mgr,
        package_id=pkg,
        install_command=" ".join(install_argv),
        install_argv=install_argv,
        uninstall_command=" ".join(uninstall_argv),
        uninstall_argv=uninstall_argv,
        requires_sudo=(install_argv[0] == "sudo"),
        notes=[],
    )


# ---------- public API: plan() ----------

def plan(*, no_docker: bool = False) -> Plan:
    """PRE-01 + PRE-03 + PRE-07: build install plan from detect().

    Pure function — no side effects. Persistence of --no-docker is handled
    by main() before calling plan(); plan() only uses the passed value.
    """
    os_name = _detect_os()
    statuses = detect(no_docker=no_docker)
    actions: list[InstallAction] = []
    blocked_by_vm: list[str] = []
    for tool, st in statuses.items():
        if st.detected and st.version_ok:
            continue  # nothing to do
        if st.vm_routing is not None:
            blocked_by_vm.append(tool)
            continue
        action = _build_action(os_name, tool)
        if action is not None:
            actions.append(action)
    return Plan(
        os=os_name,
        statuses=statuses,
        actions=actions,
        blocked_by_vm=blocked_by_vm,
        no_docker=no_docker,
    )


# ---------- public API: render_preview() — PRE-05, read-only by construction ----------

def render_preview(plan: Plan) -> str:
    """PRE-05: dry-run preview. NEVER calls subprocess.run.

    Format: human-readable numbered list of install actions, plus any
    defer-to-VM messages.
    """
    # Docker Desktop license disclaimer is documented in references/preflight/windows.md
    # (see Plan 02-04); Phase 5 friendly_error.py owns user-facing copy. Phase 2's
    # render_preview stays scope-tight: tool name + manager + sudo flag only. (W-02)
    lines = ["Here's what I'll install on this machine:"]
    if not plan.actions and not plan.blocked_by_vm:
        return "Nothing to install — all required tools are present.\n"
    for i, a in enumerate(plan.actions, 1):
        sudo_note = " (will prompt for sudo)" if a.requires_sudo else ""
        lines.append(f"  {i}. {a.tool} via {a.manager}: {a.install_command}{sudo_note}")
    for tool in plan.blocked_by_vm:
        lines.append(
            f"  - {tool} skipped: a version manager (nvm/pyenv/mise/asdf/volta/fnm) is "
            f"installed. Please install via your version manager."
        )
    if plan.os == "unsupported":
        lines.append(
            "Your distro is not yet supported in v1 (apt + dnf only). "
            "Please install Node 20+, Python 3.13+, git, gh manually."
        )
    lines.append("")  # trailing blank
    return "\n".join(lines)


# ---------- install-log read/write helpers ----------

def _read_install_log() -> dict:
    p = _install_log_path()
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "actions": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": SCHEMA_VERSION, "actions": []}


def _write_install_log(log: dict) -> None:
    atomic_write(_install_log_path(),
                 json.dumps(log, indent=2, sort_keys=False) + "\n")


def _new_log_entry(action: InstallAction, *, platform_name: str) -> dict:
    return {
        "tool":              action.tool,
        "package_id":        action.package_id,
        "manager":           action.manager,
        "platform":          platform_name,
        "started_at":        _now_iso(),
        "succeeded_at":      None,
        "install_command":   action.install_command,
        "install_argv":      list(action.install_argv),
        "uninstall_command": action.uninstall_command,
        "uninstall_argv":    list(action.uninstall_argv),
        "status":            "started",
    }


# ---------- single-confirmation helper (PRE-02 / D-06 / INTERFACE 9) ----------

def _confirm_batch(plan: Plan) -> bool:
    """Single y/n covering the whole batch (PRE-02). Returns True if user typed y/yes."""
    if not sys.stdin.isatty():
        sys.stderr.write(
            "OSBuilder: preflight requires an interactive terminal. "
            "Re-run from a real shell.\n"
        )
        return False
    prompt = f"\nProceed with installing {len(plan.actions)} tool(s)? [y/N]: "
    answer = input(prompt).strip().lower()
    return answer in ("y", "yes")


# ---------- public API: apply() — PRE-04, auto-rollback on failure ----------

def apply(plan: Plan) -> int:
    """PRE-04: transactional install. Records each action to install-log
    BEFORE invoking subprocess.run, marks succeeded/failed after.

    On any failure, calls rollback() automatically.
    Returns 0 on full success, non-zero on rollback completion.
    """
    if not plan.actions:
        sys.stdout.write("Nothing to install.\n")
        return 0
    # Print preview and single confirmation prompt when running interactively (PRE-02 + PRE-05).
    # In non-TTY context (CI / pipe) we skip the prompt and proceed directly —
    # this avoids stdin blocking forever (T-02-20 mitigation).
    sys.stdout.write(render_preview(plan))
    if sys.stdin.isatty():
        if not _confirm_batch(plan):
            sys.stdout.write("Aborted by user.\n")
            return 1
    log = _read_install_log()
    for action in plan.actions:
        # ATOMICITY INVARIANT (T-02-11 high-severity mitigation):
        # write 'started' to log BEFORE subprocess.run is invoked.
        # The strict ordering write→subprocess is the falsifying claim
        # exercised by test_log_recorded_before_subprocess.
        entry = _new_log_entry(action, platform_name=plan.os)
        log["actions"].append(entry)
        _write_install_log(log)
        # On sudo-required calls, do NOT capture stdin/stdout — let sudo own
        # the TTY (Pitfall 5).
        cap = not action.requires_sudo
        try:
            result = subprocess.run(
                action.install_argv,
                shell=False,
                capture_output=cap,
                text=cap,
                check=False,
            )
        except KeyboardInterrupt:
            entry["status"] = "failed"
            _write_install_log(log)
            sys.stderr.write("\nInterrupted; rolling back...\n")
            return rollback()
        except (FileNotFoundError, OSError) as e:
            entry["status"] = "failed"
            _write_install_log(log)
            _raw = str(e)
            if _fe is not None:
                _msg = _fe.translate(_raw, ctx={"tool": action.tool})
                sys.stderr.write(
                    f"## {_msg.title}\n{_msg.what_broke}\n\n"
                    f"**What to do:** {_msg.what_to_do}\n"
                )
                if _msg.copy_paste:
                    sys.stderr.write(f"\n  {_msg.copy_paste}\n")
            else:
                sys.stderr.write(f"OSBuilder: {action.tool} install failed: {_raw}\n")
            return rollback()
        # Re-write log to reflect success or failure
        if result.returncode == 0:
            entry["status"] = "succeeded"
            entry["succeeded_at"] = _now_iso()
            _write_install_log(log)
        else:
            entry["status"] = "failed"
            _write_install_log(log)
            _raw = (result.stderr or "").strip() or f"exit code {result.returncode}"
            if _fe is not None:
                _msg = _fe.translate(_raw, ctx={"tool": action.tool})
                sys.stderr.write(
                    f"## {_msg.title}\n{_msg.what_broke}\n\n"
                    f"**What to do:** {_msg.what_to_do}\n"
                )
                if _msg.copy_paste:
                    sys.stderr.write(f"\n  {_msg.copy_paste}\n")
                sys.stderr.write("rolling back...\n")
            else:
                sys.stderr.write(
                    f"OSBuilder: {action.tool} install exited {result.returncode}; "
                    f"rolling back...\n"
                )
            return rollback()
    return 0


# ---------- public API: rollback() — PRE-04 batch rollback ----------

def rollback() -> int:
    """Iterate install-log in REVERSE; run each succeeded action's uninstall_argv."""
    log = _read_install_log()
    # Walk in reverse over actions where status != "rolled-back"
    # (started but not succeeded means a partial install; attempt cleanup anyway)
    failed = 0
    for entry in reversed(log["actions"]):
        if entry["status"] in ("rolled-back",):
            continue
        try:
            r = subprocess.run(entry["uninstall_argv"], shell=False,
                               capture_output=False, check=False)
        except (FileNotFoundError, OSError):
            failed += 1
            continue
        if r.returncode == 0:
            entry["status"] = "rolled-back"
        else:
            failed += 1
    _write_install_log(log)
    return 0 if failed == 0 else 2


# ---------- public API: uninstall() — PRE-06 ----------

def uninstall() -> int:
    """PRE-06: user-invoked uninstall. Same algorithm as rollback().

    Plan 02-03 ships the thin CLI wrapper scripts/uninstall.py that imports
    and invokes this function: `from preflight_check import uninstall`.
    """
    return rollback()


# ---------- public API: main() — argparse dispatch ----------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="preflight_check",
        description="OSBuilder preflight checker.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="detect + plan, print human-readable")
    p_check.add_argument("--no-docker", action="store_true")

    p_preview = sub.add_parser("preview", help="dry-run preview (PRE-05)")
    p_preview.add_argument("--no-docker", action="store_true")

    p_install = sub.add_parser("install", help="apply with single y/n confirmation")
    p_install.add_argument("--no-docker", action="store_true")
    p_install.add_argument("--dry-run", action="store_true")

    sub.add_parser("rollback", help="undo last batch")
    sub.add_parser("uninstall", help="remove everything OSBuilder installed (PRE-06)")

    args = parser.parse_args(argv)

    if args.cmd in ("check", "preview", "install"):
        # Merge CLI flag with persisted config (D-12).
        # Persistence lives here in main() — detect()/plan() are pure functions
        # that only use the passed no_docker value (test isolation requirement).
        cli_no_docker = getattr(args, "no_docker", False)
        effective_no_docker = cli_no_docker or _read_no_docker_config()
        if cli_no_docker:
            _write_no_docker_config(True)
    else:
        effective_no_docker = False

    if args.cmd == "check":
        pln = plan(no_docker=effective_no_docker)
        sys.stdout.write(f"Detected OS: {pln.os}\n")
        for tool, st in pln.statuses.items():
            sys.stdout.write(
                f"  {tool}: detected={st.detected} version={st.version!r} "
                f"version_ok={st.version_ok} vm_routing={st.vm_routing}\n"
            )
        return 0
    if args.cmd == "preview":
        pln = plan(no_docker=effective_no_docker)
        sys.stdout.write(render_preview(pln))
        return 0
    if args.cmd == "install":
        pln = plan(no_docker=effective_no_docker)
        if args.dry_run:
            sys.stdout.write(render_preview(pln))
            return 0
        return apply(pln)
    if args.cmd == "rollback":
        return rollback()
    if args.cmd == "uninstall":
        return uninstall()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
