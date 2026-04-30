# Pre-flight on Windows

> Reference matrix for `scripts/preflight_check.py` on Windows 10+ / 11 systems.
> Verified Apr 2026 against winget.run and learn.microsoft.com.

## OS detection

`platform.system() == "Windows"` → `Plan.os == "windows"`.

PowerShell 5.1 (built into Windows 10/11) hosts `bootstrap.ps1`. Preflight runs
Python 3.13 invoked via the bootstrap re-exec. WSL is NOT detected as Linux in v1
— Windows preflight runs natively in PowerShell. (See `02-RESEARCH.md` Q1.)

## Package manager: winget (primary)

Detection: `shutil.which("winget") is not None`.

Built into Windows 10 1809+ and Windows 11 — no separate install needed.
[Microsoft docs](https://learn.microsoft.com/en-us/windows/package-manager/winget/).

User-scope packages do NOT require admin. If a package is system-scope, winget
triggers the OS UAC prompt — preflight does NOT try to programmatically elevate.

## Package manager: scoop (fallback at runtime)

If `shutil.which("winget") is None` (rare — Windows 10 < 1809) OR a winget package
ID is missing, preflight switches to scoop. v1 implementation uses winget primary
only; the scoop fallback path is documented here but is a single-line `if` in the
code (Plan 02-02).

[scoop.sh](https://scoop.sh) — install via PowerShell:
`iwr -useb get.scoop.sh | iex` (NOT auto-run by preflight; user opt-in only).

## Chocolatey: NOT used (anti-recommendation)

Per [PROJECT.md refuse-list](../../.planning/PROJECT.md) and STACK.md
anti-recommendations: chocolatey requires admin + separate install + has documented
package-quality concerns. winget (built-in) → scoop (community-maintained,
user-scope) is the v1 path. Preflight refuses any choco-based path.

## Install matrix — winget

| Tool | Command | Package ID | Notes |
|---|---|---|---|
| Node 20+ | `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements` | `OpenJS.NodeJS.LTS` | Verified at [winget.run/pkg/OpenJS/NodeJS.LTS](https://winget.run/pkg/OpenJS/NodeJS.LTS) — current LTS as of Apr 2026 |
| Python 3.13+ | `winget install -e --id Python.Python.3.13 --accept-source-agreements --accept-package-agreements` | `Python.Python.3.13` | Matches `bootstrap.ps1:27` |
| git 2.40+ | `winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements` | `Git.Git` | — |
| gh 2.x | `winget install -e --id GitHub.cli --accept-source-agreements --accept-package-agreements` | `GitHub.cli` | — |
| Docker | `winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements` | `Docker.DockerDesktop` | License warning required — see Pitfall 4 below |

## Pitfall 3 — winget PATH refresh

After `winget install` succeeds, the running PowerShell session's PATH does NOT
refresh. `shutil.which("python")` returns None even though the install succeeded;
if preflight tries to "verify by re-probing" it falsely reports a failure.

Mitigation (already implemented in `scripts/bootstrap.ps1:39-44`):

The "two-mode" pattern — capture pre-install state; if Python (or any tool) was
JUST INSTALLED in this session, exit gracefully with a "reopen your shell"
message and do NOT try to re-probe. Trust the subprocess returncode instead.

`scripts/preflight_check.py` mirrors this: on Windows, if a package install
returncode is 0, the install is treated as succeeded WITHOUT re-probing
`shutil.which`. The post-install summary appends "Reopen your shell to use
these tools" — same line bootstrap.ps1 emits at line 43.

Verified GitHub issues: [winget-cli#3359](https://github.com/microsoft/winget-cli/issues/3359),
[winget-cli#531](https://github.com/microsoft/winget-cli/issues/531).

## Pitfall 4 — Docker Desktop license

Docker Desktop is FREE for personal use, but PAID for companies with 250+ employees
OR $10M+ revenue (~$11-24/user/month per [docker.com/pricing](https://www.docker.com/pricing/)).

On Windows specifically, Docker Desktop is the only viable Docker runtime — there
is no OrbStack equivalent, no first-class WSL-native Docker. Preflight pre-warns
in the dry-run preview:

> "Docker Desktop is free for personal use. If you work for a company with 250+
> employees or $10M+ revenue, your company needs a paid subscription. Continue?"

Users who don't want this should pass `--no-docker` (PRE-07) — preflight skips
Docker detection AND prompt; SQLite-only single-user CLI builds work without
Docker. The `--no-docker` choice persists to `~/.osbuilder/preflight-config.json`.

## Version-manager detection (Windows)

nvm-windows and pyenv-win are STRUCTURALLY DIFFERENT from their POSIX counterparts:

- **nvm-windows** stores at `%APPDATA%\nvm` (NOT `~/.nvm`). Detection probe:
  `os.environ.get("APPDATA")` joined with `nvm`, OR `shutil.which("nvm")`. v1 implementation uses
  `(Path.home() / ".nvm").exists() or shutil.which("nvm") is not None` — the `~/.nvm`
  probe is a false negative on Windows but `shutil.which("nvm")` catches it. Documented
  flag: revisit the path probe in v2 to handle `%APPDATA%\nvm` explicitly.
- **pyenv-win** stores at `%USERPROFILE%\.pyenv` — same as POSIX `~/.pyenv` semantically;
  v1 detection works.
- **volta-win** uses `%USERPROFILE%\.volta` — same as POSIX semantically; v1 detection works.

Same Pitfall-13 mitigation: detected → refuse to clobber.

## Privilege escalation

User-scope winget installs do NOT require admin. If a package's manifest requires
system-scope, winget itself triggers UAC — preflight delegates and never tries to
elevate the Python script.

## Connection to code

`_WINGET_INSTALL` table in `scripts/preflight_check.py` MUST match the package IDs
here. The two-mode PATH-refresh pattern in `apply()` mirrors `bootstrap.ps1:39-44`.

## Known gaps (v2 milestones)

- No real-machine Windows CI in v1 (V2-XPL-01 closes this); rely on FakeShell
  tests + manual smoke on a Windows VM at phase verification time
- WSL detection is documented as a future flag — if `wsl --status` returns
  `"Default Version: 2"`, prefer the Linux preflight path inside WSL. v1 ignores.

## Sources

- [winget docs (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
- [winget.run/pkg/OpenJS/NodeJS.LTS](https://winget.run/pkg/OpenJS/NodeJS.LTS)
- [winget.run/pkg/Docker/DockerDesktop](https://winget.run/pkg/Docker/DockerDesktop)
- [docker.com/pricing](https://www.docker.com/pricing/) — license terms
- `.planning/research/STACK.md` §"Windows column"
- `.planning/research/PITFALLS.md` §13 (preflight breaks system) and §14 (cross-platform script breakage)
- `scripts/bootstrap.ps1:14-44` — the two-mode PATH-refresh pattern this preflight reuses
