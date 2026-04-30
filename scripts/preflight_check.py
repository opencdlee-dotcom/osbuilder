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
    """
    # Honor persisted --no-docker
    no_docker = no_docker or _read_no_docker_config()
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
    "docker":  ("brew", "orbstack",     ["brew", "install", "orbstack"]),  # brew install orbstack (D-11)
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

    Pure function — no side effects.
    """
    no_docker = no_docker or _read_no_docker_config()
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


# ---------- Task 2 stubs (NotImplementedError ensures deferred tests FAIL, not pass) ----------

def render_preview(plan: Plan) -> str:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def _read_install_log() -> dict:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def _write_install_log(log: dict) -> None:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def apply(plan: Plan) -> int:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def rollback() -> int:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def uninstall() -> int:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("Task 2 (Plan 02-02) implements this")


if __name__ == "__main__":
    raise SystemExit(main())
