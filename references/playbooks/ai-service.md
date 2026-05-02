# OSBuilder AI-Service Playbook

> Specification for the ai-service scaffold path (`app_type: ai-service`).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md (line limit ≤ 200).

## What the ai-service playbook produces

A FastAPI + uv + Pydantic v2 project. After `uv sync && uv run fastapi dev`,
the user sees a working `/docs` page at `http://127.0.0.1:8000/docs` with
three routed endpoints: `/`, `/health`, and `/summarize` (a Pydantic v2-validated
POST stub returning `text[:200]`). No API key required to boot (D-11).

## Scaffold command (non-interactive)

```
uv init --app <project-name>
cd <project-name>
uv add 'fastapi[standard]'
```

Source: https://fastapi.tiangolo.com/fastapi-cli/ + https://docs.astral.sh/uv/guides/integration/fastapi/ (verified 2026-05-01)

## Post-scaffold files written by OSBuilder

| File | Purpose |
|------|---------|
| `main.py` | Vendored from `assets/fastapi-starter/main.py`; routes /, /health, /summarize |
| `Dockerfile` | Multi-stage uv image; `fastapi run main.py` entrypoint |
| `.github/workflows/ci.yml` | uv sync + pytest CI on PR |

## Files OSBuilder must NOT write

- `pyproject.toml` (owned by `uv init`)
- `uv.lock` (owned by `uv add`)

## Refuse list

- Frontend in same project (use the web playbook for client-side React/Next)
- Real Anthropic API call wired in starter (D-11 — stub only; user owns auth surface)
- Hardcoded API keys (env-var only; never written to disk by OSBuilder)

## Stack (pinned versions — verified 2026-05-01)

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Framework | fastapi | 0.136.1 | `[standard]` extra for fastapi-cli (Pitfall 2) |
| Models | pydantic | 2.13.3 | v2-native syntax mandatory (Pitfall 4) |
| Server | uvicorn | 0.46.0 | Transitive of fastapi[standard] |
| Pkg manager | uv | 0.11.8 | preflight installs via D-20 |

## See also

- `references/stack-menu.md` (## ai-service playbook defaults)
- `references/question-bank.md`
- `scripts/scaffold_dispatch.py` (scaffold_ai_service)
- `.planning/phases/07-additional-playbooks/07-RESEARCH.md`
