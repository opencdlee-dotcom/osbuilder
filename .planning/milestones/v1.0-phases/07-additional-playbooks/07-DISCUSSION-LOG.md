# Phase 7: Additional playbooks - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 07-additional-playbooks
**Areas discussed:** Routing, Hub shape, Desktop scaffold, Plan slicing, FastAPI starter, Verify, Preflight

---

## Routing — intake `app_type` inference

| Option | Description | Selected |
|--------|-------------|----------|
| Infer + ask if unsure | Keyword scoring picks a playbook; low confidence or near-tie falls back to a plain-English question. | ✓ |
| Always ask via question-bank | Unconditional "What kind of thing are you building?" question every build. | |
| Pure inference, no fallback | Scoring routes silently; ties default to web. | |
| Explicit --playbook flag only | User must pass --playbook X; no inference, no question. | |

**User's choice:** Infer + ask if unsure (Recommended)
**Notes:** Preserves "I don't know, you decide" principle (IN-04) while keeping the common-person-friendly UX.

---

## Hub-platform shape (SC-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Empty hub + N named sub-tool stubs | Top-level CLAUDE.md routing table + N empty sub-tool dirs named from intake. | ✓ |
| Hub + first sub-tool fully scaffolded | Same hub skeleton, plus first named sub-tool runs full inner playbook. | |
| Mirror professor/ file-for-file | Copy professor/ structure verbatim, then rename. | |
| Hub-only (no sub-tools yet) | Just the routing table + CLAUDE.md, no sub-tool subdirs. | |

**User's choice:** Empty hub + N named sub-tool stubs (Recommended)
**Notes:** Mirrors professor/ structurally without coupling tests to a live filesystem dependency. Sub-tool autoscaffolding deferred.

---

## Desktop scaffolding (SC-03)

| Option | Description | Selected |
|--------|-------------|----------|
| create-tauri-app, pinned flags | `pnpm create tauri-app@latest <name> --template react-ts --manager pnpm --identifier <id>` — same model as create-next-app. | ✓ |
| assets/tauri-starter/ template | Vendor a full Vite+React+Rust skeleton in-repo. | |
| Hybrid: create-tauri-app + post-scaffold overlay | create-tauri-app for the shell, then OSBuilder writes additions. | |

**User's choice:** create-tauri-app, pinned flags (Recommended)
**Notes:** Matches Phase 3's web playbook pattern. Tauri owns template drift, same risk model accepted previously.

---

## Plan slicing

| Option | Description | Selected |
|--------|-------------|----------|
| 4 playbook plans + 1 routing plan + 1 E2E plan | 6 plans total; clean wave parallelism after 07-01. | ✓ |
| 1 plan per playbook, routing folded into 07-02 | 5 plans; routing changes touch all 4 playbooks. | |
| Vertical slices: ai-service E2E, then CLI E2E... | Each plan ships one playbook end-to-end with its own E2E test. | |
| Defer hub-platform to Phase 7.1 | Phase 7 ships ai-service+cli+desktop only; hub gets a decimal phase. | |

**User's choice:** 4 playbook plans + 1 routing plan + 1 E2E plan (Recommended)
**Notes:** Mirrors Phase 6's plan-per-concern shape. 07-02..07-05 wave-parallelizable after 07-01.

---

## FastAPI starter contents (SC-01)

| Option | Description | Selected |
|--------|-------------|----------|
| /, /health, /docs + LLM stub | Routed `/`, `/health`, automatic `/docs`, plus stub `/summarize` POST endpoint. | ✓ |
| Just / and /health | Bare runnable API; user adds LLM endpoint themselves. | |
| / + /health + /summarize wired to real Claude API | Full LLM endpoint using ANTHROPIC_API_KEY from .env.example. | |

**User's choice:** /, /health, /docs + LLM stub (Recommended)
**Notes:** Matches SC-01's example verbatim ("summarizes documents with an LLM") so the AI shape is visible without API key friction.

---

## Verification (SC-05)

| Option | Description | Selected |
|--------|-------------|----------|
| One parametrized E2E harness, 4 cases | `test_e2e_playbooks.py` runs 5-step contract parametrized over [ai-service, cli, desktop, hub]. | ✓ |
| One E2E test file per playbook | 4 separate test files mirroring the 4 playbook plans. | |
| Manual UAT only (deferred to /gsd-verify-work) | Phase 6 V-04 pattern — human gate covers stranger-clone. | |

**User's choice:** One parametrized E2E harness, 4 cases (Recommended)
**Notes:** Single source of truth for the contract. Manual UAT remains in 07-HUMAN-UAT.md as a complementary human gate.

---

## Preflight extensions

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-install with single confirmation | Same model as Node/Docker — curl install scripts for Rust and uv (winget on Windows). | ✓ |
| Detect-and-instruct only | Preflight prints install commands but doesn't run them. | |
| Lazy: only check when playbook requires | Skip Rust unless desktop selected; skip uv unless ai-service or cli. | |

**User's choice:** Auto-install with single confirmation (Recommended)
**Notes:** Matches Phase 2's cross-platform contract and the common-person UX principle.

---

## Claude's Discretion

- Inference scoring algorithm details (weighted vs. bag-of-words) — planner picks; "ask if unsure" is the safety net.
- Exact wording of playbook-fallback question in question-bank.md — must match existing outcome-framed style.
- Where to vendor the professor/ snapshot for hub-platform diff verification.
- Internal section ordering inside each new playbook .md (default: mirror web.md).

## Deferred Ideas

- Real Claude API wiring in fastapi-starter (stub-only ships in Phase 7).
- Sub-tool autoscaffolding for hub-platform builds.
- Additional language ecosystems (Go, Ruby, Java, Elixir) — out of v1.
- Deployment beyond private GitHub (Vercel/Fly/Railway integrations).
- Per-playbook --advanced stack overrides (current --advanced is component-level only).
