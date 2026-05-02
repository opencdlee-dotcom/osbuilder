# assets/fastapi-starter/main.py — verified Pydantic v2 + FastAPI 0.136.1 patterns
# Source: https://fastapi.tiangolo.com/fastapi-cli/ (verified 2026-05-01)
# Source: https://docs.pydantic.dev/latest/concepts/models/ (Pydantic v2 BaseModel)
"""OSBuilder FastAPI starter (ai-service playbook)."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="OSBuilder AI Service Starter",
    version="0.1.0",
)


class SummarizeRequest(BaseModel):
    """Pydantic v2 model — uses Field(...) for declarative defaults + constraints."""
    text: str = Field(..., min_length=1, max_length=100_000,
                       description="Input text to summarize.")


class SummarizeResponse(BaseModel):
    summary: str


def summarize(text: str) -> str:
    """Stub — returns first 200 chars.

    TO WIRE A REAL LLM: replace this body with a call to your provider.
    Example (after `uv add anthropic`):

        from anthropic import Anthropic
        client = Anthropic()  # reads ANTHROPIC_API_KEY from env
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": f"Summarize: {text}"}],
        )
        return msg.content[0].text
    """
    return text[:200]


@app.get("/")
def read_root():
    return {"message": "Hello from OSBuilder AI Service"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def post_summarize(req: SummarizeRequest):
    return SummarizeResponse(summary=summarize(req.text))
