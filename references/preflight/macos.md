# Pre-flight on macOS

> Reference matrix for `scripts/preflight_check.py` on Darwin systems.
> Verified Apr 2026 against brew.sh and docs.orbstack.dev.

## OS detection

`platform.system() == "Darwin"` → `Plan.os == "macos"`.

## Package manager: Homebrew

Detection: `shutil.which("brew") is not None` (resolves to `/opt/homebrew/bin/brew` on
Apple Silicon, `/usr/local/bin/brew` on Intel).

Homebrew installs to user-owned paths — **no sudo required** for `brew install`.

## Install matrix

| Tool | Command | Package ID | Notes |
|---|---|---|---|
| Node 20+ | `brew install node@20` | `node@20` | Pinned to LTS major; `node` (latest LTS) also works but un-pinned drifts |
| Python 3.13+ | `brew install python@3.13` | `python@3.13` | NEVER touch `/usr/bin/python3` (Apple system Python) — see Pitfall 2 below |
| git 2.40+ | `brew install git` | `git` | Often already present via Xcode CLT; preflight idempotent — brew skip-if-installed |
| gh 2.x | `brew install gh` | `gh` | — |
| Docker (default) | `brew install orbstack` | `orbstack` | OrbStack is the 2026 default Mac Docker runtime — faster startup, less RAM, drop-in CLI compatibility with `docker` and `docker compose`; see [docs.orbstack.dev](https://docs.orbstack.dev) |
| Docker (opt-in) | `brew install --cask docker` | `docker` (cask) | Docker Desktop fallback; requires explicit opt-in (license terms — see Pitfall 4 in windows.md) |

> **Code note (D-11):** `scripts/preflight_check.py` `_MACOS_INSTALL["docker"]` currently
> uses package_id `"docker"` (not `"orbstack"`) due to a test-stub constraint predating the
> D-11 OrbStack-default lock. The runtime install command is `brew install docker`. This is
> a known v1 inconsistency tracked for v2: the OrbStack-first install path will supersede
> this once the test suite is updated to match. The _intent_ of D-11 (OrbStack as the
> preferred runtime) is correctly documented here.

## Version-manager detection

Before proposing any Node or Python install, preflight probes:

- `~/.nvm` exists OR `shutil.which("nvm") is not None` → Node-VM detected
- `~/.volta` exists OR `shutil.which("volta") is not None` → Node-VM detected
- `shutil.which("fnm") is not None` → Node-VM detected
- `~/.pyenv` exists OR `shutil.which("pyenv") is not None` → Python-VM detected
- `~/.asdf` exists OR `shutil.which("asdf") is not None` → both
- `shutil.which("mise") is not None` → both

If any is detected for the relevant tool ecosystem, preflight REFUSES to install
and asks the user to install via their existing version manager. This is the
Pitfall 13 mitigation (auto-installing Node when nvm is present is the documented
#1 way preflight breaks user trust permanently).

## Pitfall 2 — macOS system Python

`/usr/bin/python3` is Apple's system Python — used by macOS internal tooling, Xcode,
and `sw_vers`. Never touch it.

Always:
- Use `brew install python@3.13` (installs to `/opt/homebrew/bin/python3.13` or
  `/usr/local/bin/python3.13`)
- Invoke as `python3.13` explicitly when running OSBuilder helper scripts
- Never `sudo rm /usr/bin/python3` or any system Python path

Apple updates the system Python on every macOS update; user-installed tools that
rely on `/usr/bin/python3` get clobbered by Apple. Brew's separate path avoids
this entirely.

## Pitfall 6 — Transitive dependencies remain after uninstall

Known v1 limitation: `brew install gh` pulls in ~10 dependency formulae (e.g.,
`oniguruma`). `brew uninstall gh` does NOT auto-remove those dependencies. After
`python scripts/uninstall.py`, the user-facing tools are gone but transitive deps
may remain.

Workaround: user can manually run `brew autoremove` to clean up. Preflight does
NOT run this automatically — it can remove things the user did want.

Future improvement (v2): snapshot `brew list` before install, diff after, record
the delta in install-log; uninstall reverses the delta. Out of scope for v1.

## Privilege escalation

No sudo required. Homebrew installs to user-owned paths.

## Connection to code

Package IDs and argv lists in this matrix MUST match `scripts/preflight_check.py`'s
`_MACOS_INSTALL` table. If a Homebrew package is renamed or a new tool is added,
update both this file AND the code in lockstep.

## Sources

- [brew.sh](https://brew.sh) — Homebrew install + package search
- [docs.orbstack.dev](https://docs.orbstack.dev) — OrbStack install (current command is plain `brew install orbstack`, no `--cask` needed; both forms work)
- `.planning/research/STACK.md` §"macOS column"
- `.planning/research/PITFALLS.md` §13 (preflight breaks system; macOS system Python sub-section)
