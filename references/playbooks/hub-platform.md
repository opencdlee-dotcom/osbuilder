# OSBuilder Hub-Platform Playbook

> Specification for the hub-platform scaffold path (`app_type: hub-platform`).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md.

## What the hub-platform playbook produces

A top-level `CLAUDE.md` routing table + N empty sub-tool subdirectories (e.g., `grading/`, `rostering/`). Each sub-tool gets its own placeholder `CLAUDE.md`. The user re-runs `/osbuilder` from inside each subfolder to scaffold its real implementation in a later session.

## Scaffold command (non-interactive)

Hub-platform is the only playbook that does NOT shell out to an external scaffolder. OSBuilder writes files directly via `scripts/scaffold_dispatch.py:scaffold_hub` (pure file-stamping per RESEARCH.md Pattern 4).

No external command. Sub-tool names come from intake parsing via `_extract_subtools` (D-06). When ambiguous, OSBuilder asks the question-bank fallback.

```bash
python3 scripts/scaffold_dispatch.py scaffold \
  --project-name <hub-name> \
  --playbook hub-platform \
  --subtool grading --subtool rostering
```

## Post-scaffold files written by OSBuilder

| File | Purpose |
|------|---------|
| `<project>/CLAUDE.md` | Top-level routing table; lists all sub-tools |
| `<project>/<subtool>/CLAUDE.md` | Per-subtool placeholder (one per subtool) |

## Files OSBuilder must NOT write

- Sub-tool implementation code (D-04 — user re-runs `/osbuilder` per sub-tool to fill in)
- `pyproject.toml` / `package.json` (hub is a workspace, not a single app)
- `Dockerfile` / `compose.yaml` / CI workflow (hub doesn't ship as a single artifact)

## Refuse list

- **Inline scaffolding all sub-tools at once** (D-04 — defer to per-subtool re-invocation)
- All standard refusals from `references/refuse-list.md` (Kubernetes, Helm, microservices, service-mesh, Electron — global refuse-list applies)

## Stack (no real stack — hub is structural)

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Routing format | CLAUDE.md table | n/a | Mirrors `../professor/` shape per D-05 |

Structural verification compares the built hub against `assets/hub-template/professor-snapshot/` (vendored at planning time per D-05 — NOT a live filesystem dependency).

## See also

- `references/stack-menu.md` (## hub-platform playbook defaults)
- `assets/hub-template/README.md` (snapshot vendor procedure)
- `scripts/scaffold_dispatch.py` (scaffold_hub)
- `scripts/intake_handler.py` (_extract_subtools)
- `.planning/phases/07-additional-playbooks/07-RESEARCH.md` (§Pattern 4)
