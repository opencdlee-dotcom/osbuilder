# OSBuilder Stack Menu — Web Playbook Defaults

> Fallback defaults loaded by `stack_researcher.py` when `/brainiac` times out
> or returns a low-confidence result (RES-03).
> Loaded on-demand — not pulled into SKILL.md.

## Web playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| Framework | next.js | 16.2.4 | Full-stack React; App Router default; create-next-app scaffolded |
| ORM | drizzle-orm | 0.45.2 | 33KB bundle; type-safe; faster cold start than Prisma |
| Database | postgres | 18-alpine | Multi-user default; compose.yaml service |
| CSS | tailwindcss | 4.2.4 | Bundled by create-next-app --tailwind; CSS-first in v4 |
| Package Manager | pnpm | 10.33.2 | Disk-efficient; --use-pnpm flag in create-next-app |

Supporting packages (not parsed by `_read_stack_menu` — for reference only):

| Package | Version | Role |
|---------|---------|------|
| drizzle-kit | 0.31.10 | Migrations + codegen (companion to drizzle-orm) |
| postgres.js | 3.4.9 | Postgres driver for Drizzle (postgres package) |

## How stack_researcher.py reads this file

`_read_stack_menu()` parses rows in the "## Web playbook defaults" table above.
It maps column 1 (Component) to internal keys: framework, orm, database, css, package_manager.
Returns `{"framework": {"name": "next.js", "version": "16.2.4", "source": "stack-menu"}, ...}`.
Returns hardcoded equivalent if this file is absent or unreadable.

## Updating defaults

When a package releases a new major version:
1. Verify against npm registry: `npm view <pkg> version`
2. Update the version in the table above
3. Update RESEARCH.md Standard Stack section to match
4. Run `python3 -m pytest scripts/tests/ -x` to confirm no test regressions

## ai-service playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| Framework | fastapi | 0.136.1 | tiangolo canonical; `[standard]` extra ships fastapi-cli runner |
| Models | pydantic | 2.13.3 | v2 BaseModel + Field; transitive via fastapi[standard] |
| Server | uvicorn | 0.46.0 | ASGI; transitive via fastapi[standard] |
| Pkg manager | uv | 0.11.8 | Astral all-in-one (init + add + sync + run) |

## cli playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| CLI framework | typer | 0.25.1 | type-hint ergonomics; rich help free; D-13 locked |
| Terminal styling | rich | 15.0.0 | hard-dep of typer ≥0.25; auto-installed |
| Persistence | sqlite3 | stdlib | zero-deps; SC-02's "persists state across runs" |
| Pkg manager | uv | 0.11.8 | Astral all-in-one |

## desktop playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| Scaffolder | create-tauri-app | 4.6.2 | Tauri team owns template; verified flag set 2026-05-01 |
| Runtime | tauri | 2.x | `--tauri-version 2` lock; modern API surface |
| JS dev CLI | @tauri-apps/cli | 2.11.0 | bundled by create-tauri-app |
| Rust toolchain | rustup-toolchain | stable | preflight installs via D-20 (sh.rustup.rs / Rustlang.Rustup) |
| Pkg manager | pnpm | 10.33.2 | Pitfall 1: required for clean --template forwarding |

## hub-platform playbook defaults

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| Routing format | CLAUDE.md table | n/a | Top-level routing-table mirrors `../professor/` per D-05 |
| Per-subtool format | CLAUDE.md placeholder | n/a | One per sub-tool dir; user fills in via re-invocation |

## See also

- `references/playbooks/web.md` — playbook spec that consumes these defaults
- `references/playbooks/ai-service.md` — ai-service playbook spec
- `references/playbooks/cli.md` — cli playbook spec
- `references/playbooks/desktop.md` — desktop playbook spec
- `references/playbooks/hub-platform.md` — hub-platform playbook spec
- `scripts/stack_researcher.py` — implementation that reads this file
