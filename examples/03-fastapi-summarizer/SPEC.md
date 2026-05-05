# Example 03: FastAPI document summarizer

**Playbook:** ai-service
**Built:** <pending — placeholder example until OSBuilder Phase 6+7 complete>
**Repo:** [repo-url.txt](repo-url.txt)

## Original paragraph (intake)

> "I want an HTTP API that summarizes documents with an LLM. Other tools
> should be able to POST a document and get back a 200-word summary. I want
> it to run locally on my machine."

## OSBuilder's expected interpretation

- **App type:** ai-service
- **Playbook:** `references/playbooks/ai-service.md` (FastAPI + uv +
  Pydantic v2 + `assets/fastapi-starter/`)
- **Inferred from keywords:** "HTTP API" (ai-service), "summarize with an
  LLM" (LLM-shaped endpoint), "POST a document" (REST contract).
- **Notable refusals:** none. (User did not request K8s, microservices, or
  multi-region deploy — defaults apply.)
- **Production-ready flag:** OFF — single-user local API does not need
  OpenTelemetry / Sentry / rate-limiting in default mode.

## Before / After

| Stage | What it looked like | Screenshot |
|-------|---------------------|------------|
| Intake (paragraph) | (the paragraph above) | — |
| Derived spec | endpoint contract + Pydantic v2 schemas | `screenshots/derived-spec.png` (pending) |
| Scaffolded project | uv + fastapi-starter + pydantic v2 | `screenshots/scaffold-tree.png` (pending) |
| Working app | `uv run fastapi dev` boots `/docs` page | `screenshots/docs-page.png` (pending) |
| /summarize smoke | `curl -X POST /summarize -d ...` returns summary | `screenshots/summarize-200.png` (pending) |
| Pydantic v2 validation | empty-text request returns 422 (Pitfall 4) | `screenshots/422-error.png` (pending) |
| Private GitHub | `gh repo create --private` URL | `screenshots/repo-view.png` (pending) |

## How OSBuilder built this (expected sequence)

1. **PM** gathered requirements; asked one clarifying question ("Where will
   the summarized text come from? — you'll send it in the request, the API
   will read it from a URL, or you'll upload a file"). User picks "send it
   in the request"; `multi_user: false` (single-user local).
2. **Architect** chose FastAPI + uv + Pydantic v2 + the OSBuilder-supplied
   `assets/fastapi-starter/` template (since no `create-fastapi-app`
   exists). Locked Pydantic v2 syntax (NOT v1) per Phase 7 Pitfall 4.
3. **DevOps** ran `uv init` + `uv add fastapi[standard]` (brackets
   preserved as a single argv token per 07-02 D-21 implementation).
4. **Backend** built the `/summarize` POST endpoint with Pydantic v2
   `Field(min_length=1)` validation; **Frontend** N/A.
5. **DevOps** stamped Dockerfile + python.yml CI workflow.
6. **QA** ran `/code-tester` (adversarial: empty body → 422; unicode →
   passes; oversize body → expected to be truncated). **Reviewer** ran
   `/predator` + `/gsd:code-review`.
7. **Tech Writer** wrote README documenting `uv run fastapi dev` + the
   endpoint contract.
8. **DevOps** pushed to private GitHub.

## Status

This example is currently a SPEC placeholder. It will be upgraded to a real
built repo once OSBuilder Phase 6 (ship-to-private-github) completes and a
real run produces a real URL. `repo-url.txt` will be flipped from
`NOT_PUBLISHED` to the real URL at that point.

## See also

- [`../../references/playbooks/ai-service.md`](../../references/playbooks/ai-service.md) — ai-service playbook reference
- [`../README.md`](../README.md) — gallery index
