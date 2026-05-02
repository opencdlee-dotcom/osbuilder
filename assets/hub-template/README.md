# OSBuilder hub-template assets

This directory contains the assets used by `scaffold_hub` (Phase 7, plan 07-05).

## Files

- `CLAUDE.md.tmpl` — the top-level template stamped into a new hub workspace. Substitutes `{{project_name}}` and `{{routing_table}}`.
- `subtool-CLAUDE.md.tmpl` — the per-subtool placeholder. Substitutes `{{subtool}}`.
- `professor-snapshot/` — **TEST FIXTURE ONLY.** A point-in-time vendor of `../professor/` top-level structure. Used by `scripts/tests/test_phase07_hub_platform.py` to verify scaffolded structure matches the canonical Professor Hub layout. NOT loaded at runtime; not packaged with built repos.

## Snapshot vendoring date

Vendored: 2026-05-02 from `../professor/`. The snapshot is a STRUCTURAL contract (file kinds, nesting depth, routing-table presence) — NOT a content contract. Drift in `../professor/` content is acceptable; structural drift requires re-vendoring + test update.

## Update procedure

1. `rsync -av --include='CLAUDE.md' --include='AGENTS.md' --exclude='.git/' --exclude='.planning/' --exclude='.venv/' --exclude='node_modules/' ../professor/ assets/hub-template/professor-snapshot/`
2. Verify `scripts/tests/test_phase07_hub_platform.py::test_hub_matches_professor_structure` still passes
3. Commit the snapshot delta separately from any scaffold_hub changes
