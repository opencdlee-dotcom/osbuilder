# OSBuilder Desktop Playbook

> Specification for the desktop scaffold path (`app_type: desktop`).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md
> (line limit ≤ 200; see Phase 1 Plan 01-02).

## What the desktop playbook produces

A Tauri 2 (Vite + React + Rust) project. After `pnpm install && pnpm tauri dev` the user sees a native window with hot-reload — Rust backend + WebView frontend. ~10MB binaries (Electron is ~150MB) and ~50% less RAM.

## Scaffold command (non-interactive)

```bash
pnpm create tauri-app@latest <project-name> \
  --manager pnpm \
  --template react-ts \
  --identifier <reverse-dns-id> \
  --tauri-version 2 \
  -y
```

Source: `npx --yes create-tauri-app --help` (verified 2026-05-01); pinned to create-tauri-app 4.6.2 per D-08.

The reverse-DNS identifier is built by `_build_tauri_identifier` (Pitfall 7): lowercase + remove non-alphanumeric chars, then prepend `com.osbuilder.`.

## Post-scaffold files written by OSBuilder

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Rust + Node combined CI on PR (uses `assets/ci-workflows/tauri.yml.tmpl`) |

OSBuilder does NOT modify Tauri's scaffolded files (D-08).

## Files OSBuilder must NOT write

- `Cargo.toml` (owned by create-tauri-app)
- `src-tauri/tauri.conf.json` (owned by create-tauri-app)
- `package.json` (owned by create-tauri-app)
- `pnpm-lock.yaml` (owned by pnpm install)

## Refuse list

- **Electron** — refused globally per `references/refuse-list.md`. Tauri 2 is the v1 desktop framework because (1) ~10MB binaries vs Electron's ~150MB, (2) ~50% less RAM, (3) uses the system WebView (WebKit on macOS, WebView2 on Windows, webkit2gtk on Linux) plus a Rust runtime, (4) Electron bundles a full Chromium per app. If you specifically need Electron-only APIs, that is out of scope for v1.
- **Native mobile (iOS/Android)** — out of scope for v1 (use a web playbook with mobile-responsive design instead).
- **Auto-deploy / code-signing pipelines** — desktop builds ship build artifacts; signing is the user's call (App Store, Microsoft Store, notarization).

## Stack (pinned versions — verified 2026-05-01)

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Scaffolder | create-tauri-app | 4.6.2 | non-interactive flag set verified |
| Tauri runtime | tauri | 2.x | `--tauri-version 2` flag pins major |
| JS dev/build CLI | @tauri-apps/cli | 2.11.0 | bundled by create-tauri-app |
| Rust toolchain | rustup-toolchain | stable | preflight installs via D-20 |
| Pkg manager | pnpm | 10.33.2 | Pitfall 1: required for clean --template forwarding |

On Windows, after rustup install: `rustup default stable-msvc` (Pitfall 3 — the gnu default fails Tauri's MSVC-linked toolchain).

## See also

- `references/stack-menu.md` — `## desktop playbook defaults` table
- `references/refuse-list.md` — global Electron refusal copy
- `scripts/scaffold_dispatch.py` — `scaffold_desktop` + `_build_tauri_identifier`
- `scripts/preflight_check.py` — cargo install matrix entries (D-20)
- `assets/ci-workflows/tauri.yml.tmpl` — CI template (Rust+Node, 30min timeout)
