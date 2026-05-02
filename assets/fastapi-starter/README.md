# OSBuilder FastAPI Starter

Vendored by `scaffold_ai_service` into your project at `main.py`.

## Quickstart

```bash
uv sync
uv run fastapi dev
```

Then open http://127.0.0.1:8000/docs — you'll see the auto-generated Swagger UI
with three routes:

| Method | Path         | What it does                                       |
|--------|--------------|----------------------------------------------------|
| GET    | `/`          | Returns a hello message                            |
| GET    | `/health`    | Returns `{"status": "ok"}`                         |
| POST   | `/summarize` | Validates a `SummarizeRequest` and returns `text[:200]` |

No API key, no env-vars, no LLM provider account is needed to boot. The
`/summarize` endpoint is a deliberate stub — it returns the first 200 characters
of the input. This is by design (decision D-11): you own the LLM-provider
auth surface, not OSBuilder.

## Wiring a real LLM

Open `main.py` and find the `summarize()` function. Its docstring shows the
exact replacement using Anthropic's SDK:

```bash
uv add anthropic
export ANTHROPIC_API_KEY=...   # NOT committed; goes in your local shell or .env
```

Then replace the `return text[:200]` line with the `client.messages.create(...)`
call shown in the docstring.

## Production deployment

The Dockerfile that ships alongside this starter (`Dockerfile`, written by
`scaffold_ai_service`) uses uv's official multi-stage image and the
`fastapi run` production entrypoint — *not* `fastapi dev`. The dev command
is for local iteration only.
