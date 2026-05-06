# OSBuilder CLI Playbook

> Specification for the cli scaffold path (`app_type: cli`).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md.

## What the cli playbook produces

A Python + Typer + Rich + SQLite project. After `uv sync && uv run <app-name> --help`, the user sees a Rich-formatted help screen. Running `<app-name> ping` writes a row to `~/.<app-name>/state.db` and reads it back — proving SC-02's "persists state across runs" contract.

## Scaffold command (non-interactive)

```bash
uv init --app <project-name>
cd <project-name>
uv add typer
```

No bundled-extras spelling — `rich >=13.8.0` is a hard dep of typer 0.25.1+ (Pitfall 5).

Source: https://typer.tiangolo.com/tutorial/ + https://docs.astral.sh/uv/ (verified 2026-05-01)

## Post-scaffold files written by OSBuilder

| File | Purpose |
|------|---------|
| `<module_name>/__main__.py` | Vendored from `assets/cli-starter/__main__.py.tmpl`; Typer app + ping subcommand |
| `.github/workflows/ci.yml` | uv sync + pytest CI on PR |

Note: `<module_name>` = `<project-name>` with hyphens replaced by underscores (`my-cli` → `my_cli`).

## Files OSBuilder must NOT write

- `pyproject.toml` (owned by `uv init` — adds `[project.scripts]` entry separately)
- `uv.lock` (owned by `uv add`)

## Refuse list

- GUI components (use desktop playbook)
- Multi-user state (use ai-service or web playbook)
- Docker container shipping (CLI is a local tool, not a container)

## Stack (pinned versions — verified 2026-05-01)

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| CLI framework | typer | 0.25.1 | hard-deps `rich >=13.8.0` (Pitfall 5) |
| Terminal styling | rich | 15.0.0 | transitive via typer |
| Persistence | sqlite3 | stdlib | path: `~/.<app-name>/state.db` (D-13) |
| Pkg manager | uv | 0.11.8 | preflight installs via D-20 |

## See also

- `references/stack-menu.md` (## cli playbook defaults)
- `references/question-bank.md`
- `scripts/scaffold_dispatch.py` (`scaffold_cli`)
- `.planning/milestones/v1.0-phases/07-additional-playbooks/07-RESEARCH.md` (Pitfall 5)
