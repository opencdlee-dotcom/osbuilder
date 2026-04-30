# Pre-flight on Linux

> Reference matrix for `scripts/preflight_check.py` on Linux systems.
> Verified Apr 2026 against Debian/Ubuntu and Fedora/RHEL package indices.

## OS detection

`platform.system() == "Linux"` AND `platform.freedesktop_os_release()` is parsed
to determine distro family:

```python
osr = platform.freedesktop_os_release()  # Python 3.10+ stdlib
ids = {osr.get("ID", ""), *osr.get("ID_LIKE", "").split()}

if "debian" in ids or "ubuntu" in ids:
    manager = "apt-get"   # Plan.os == "linux-debian"
elif "fedora" in ids or "rhel" in ids:
    manager = "dnf"       # Plan.os == "linux-fedora"
else:
    manager = None        # Plan.os == "unsupported"; refuse with friendly error
```

The `ID_LIKE` field handles derivative distros (Linux Mint → debian; Pop!_OS → debian;
Rocky/Alma → rhel) without needing a per-distro lookup table.

## Supported distros (v1)

| Family | Examples | Manager |
|---|---|---|
| Debian | Debian, Ubuntu, Linux Mint, Pop!_OS, ElementaryOS, Kali | apt-get |
| RHEL | Fedora, RHEL, CentOS, Rocky, AlmaLinux | dnf |

## Unsupported distros (v1)

Arch / Manjaro, openSUSE, Alpine, NixOS, Gentoo, Slackware, Void.

Preflight refuses with this message:

> Your distro isn't supported in v1 (apt + dnf only). Please install Node 20+,
> Python 3.13+, git, gh, and Docker through your distro's package manager. PRs
> welcome — we're prioritizing common-person targets first.

Rationale: Charlie's audience is overwhelmingly macOS + Windows + Ubuntu/Fedora.
Coverage of niche distros isn't worth the maintenance cost in v1. (See `02-RESEARCH.md`
Q5.)

## Install matrix — Debian/Ubuntu (apt-get)

| Tool | Command | Notes |
|---|---|---|
| Node 20+ | `sudo apt-get install -y nodejs` | Tries the simple path first; v1 install matrix uses this. If the distro repo ships an OLD Node (< 20), the simple install fails the post-install version check; fallback to the [NodeSource setup script](https://github.com/nodesource/distributions) is documented but NOT auto-applied in v1 (avoid `curl \| sudo bash` without explicit user consent). |
| Python 3.13+ | `sudo apt-get install -y python3.13 python3.13-venv` | Available in Ubuntu 24.10+ default repo. For older Ubuntu LTS (22.04, 24.04 LTS), the user may need the deadsnakes PPA — preflight refuses with a friendly error and suggests `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt-get update && sudo apt-get install python3.13`. |
| git 2.40+ | `sudo apt-get install -y git` | — |
| gh 2.x | `sudo apt-get install -y gh` | Tries simple path. If `gh` is not in the user's repo (Ubuntu < 24.10), preflight emits a friendly error and points to [cli.github.com Linux install](https://github.com/cli/cli/blob/trunk/docs/install_linux.md) for the official keyring + repo dance. v2 may auto-execute the keyring add. |
| Docker | `sudo apt-get install -y docker.io docker-compose-plugin` | Distro-packaged Docker. The user may need to add themselves to the `docker` group: `sudo usermod -aG docker $USER && newgrp docker` — out of scope for v1, documented here for Phase 5 friendly-error to surface. |

## Install matrix — Fedora/RHEL (dnf)

| Tool | Command | Notes |
|---|---|---|
| Node 20+ | `sudo dnf install -y nodejs:20/common` | Module stream pin (Fedora 39+); falls back to plain `nodejs` if module stream is renamed in a future Fedora release |
| Python 3.13+ | `sudo dnf install -y python3.13` | Available in Fedora 41+ default repo |
| git 2.40+ | `sudo dnf install -y git` | — |
| gh 2.x | `sudo dnf install -y gh` | Available in Fedora repos |
| Docker | `sudo dnf install -y docker docker-compose-plugin` | Distro-packaged Docker; user may need to enable the docker daemon: `sudo systemctl enable --now docker` — out of scope for v1 |

## Pitfall 5 — sudo prompt eaten by `capture_output=True`

Preflight calls `subprocess.run([..."sudo", "apt-get", "install"...], shell=False)`.

For sudo-required calls, preflight passes `capture_output=False` (and `text=False`)
so sudo's password prompt flows naturally to the user's terminal. The
`requires_sudo` flag on each `InstallAction` triggers this branch.

Why: `capture_output=True` redirects sudo's stderr (where the password prompt is
typically written) and on some sudo configurations breaks the password flow
silently — the script appears to hang. Pitfall 5 in `02-RESEARCH.md`.

Preflight ALSO pre-warns in the dry-run preview:

> "These will use sudo on Linux — you'll see a sudo prompt; type your password normally."

## Pitfall 14 — Cross-platform shell discipline

All argv is list-form: `["sudo", "apt-get", "install", "-y", "git"]`. NEVER constructed
as a shell string (`subprocess.run(f"sudo apt-get install -y {pkg}", shell=True)`) —
that opens shell-injection surface and fails on edge-case package names.

Pre-flight uses `shell=False` everywhere; `pathlib.Path` for path manipulation;
no bash arrays, no `[[ ]]`, no `<()` process substitution.

## Version-manager detection

Same Pitfall-13 mitigation as macOS:
- `~/.nvm`, `~/.volta`, `~/.fnm`, `mise`, `asdf` → Node-VM detected → refuse
- `~/.pyenv`, `mise`, `asdf` → Python-VM detected → refuse

## Privilege escalation

Linux installs require sudo. Preflight pre-warns; sudo prompt flows to user's
terminal natively. Preflight does NOT attempt to capture or fake the password.

## Connection to code

`_APT_INSTALL` and `_DNF_INSTALL` tables in `scripts/preflight_check.py` MUST match
the install commands here. Update both in lockstep.

## Sources

- [Python 3 stdlib `platform.freedesktop_os_release`](https://docs.python.org/3/library/platform.html#platform.freedesktop_os_release)
- [github.com/nodesource/distributions](https://github.com/nodesource/distributions) — NodeSource fallback (v2)
- [github.com/cli/cli/blob/trunk/docs/install_linux.md](https://github.com/cli/cli/blob/trunk/docs/install_linux.md) — official gh Linux install
- `.planning/research/STACK.md` §"Linux columns"
- `.planning/research/PITFALLS.md` §13 (preflight breaks system) and §14 (cross-platform shell)
