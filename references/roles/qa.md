# OSBuilder QA Role — Falsifiable Criteria Patterns

> Reference for the QA role. Loaded on-demand when generating VERIFICATION.md.
> NOT pulled into SKILL.md (line limit <= 200; see Phase 1 Plan 01-02).

## Purpose

This file governs the VERIFICATION.md content generated at phase_step=7 in the GSD phase loop
(`scripts/gsd_driver.py`). Each time a GSD phase completes, the QA role authors 2-5 falsifiable
success criteria that describe what an observer with no code access can verify. Criteria are
LLM-generated per phase based on what was actually planned and built — not drawn from a static bank.
This file provides the format contract, the falsifiability rule, and concrete examples.

## VERIFICATION.md Format

The format below is what `gsd_driver.py` writes at phase_step=7 and `/gsd-verify-work` reads:

```markdown
# Phase [N] Verification — [Phase Name]

**Generated:** [ISO timestamp]
**Phase:** [N]

## Falsifiable Success Criteria

1. **[Observable behavior]:** [What a user can see/do to confirm this works]
   - How to check: [concrete step — "navigate to /dashboard and see..." or "run `curl localhost:3000/api/health`"]
   - NOT acceptable: "unit tests pass"

2. **[Observable behavior]:** ...

[2-5 criteria total — never fewer than 2, never more than 5]

## Out of Scope for This Phase

- [Anything explicitly deferred]
```

## Falsifiability Rule

> Each criterion must be verifiable by a person with no code access — only browser, terminal,
> or observable application output. If a criterion requires reading source code, examining test
> results, or inspecting log files not visible in the UI, it is not falsifiable.

## Forbidden Criterion Patterns

The following patterns are NOT acceptable as standalone criteria:

- **"All unit tests pass."** — Circular: tests can be wrong; this tests the tests, not the behavior.
- **"pytest exits 0."** — Not an observable user behavior; requires code access and test runner.
- **"No errors appear in the logs."** — Not observable without code access; normal logs contain non-error output too.
- **"The API returns the correct response."** — Too vague: which API endpoint, which response body, from where?
- **"The feature works correctly."** — Subjective and unverifiable; what does "correctly" mean to an observer?

## Valid Criterion Examples

**Route navigation:** User can navigate to `/login`, enter `test@example.com` / `password123`, and be redirected to `/dashboard`.
- How to check: Open http://localhost:3000/login in a browser, enter the credentials, confirm the page URL changes to /dashboard.
- Acceptable because: The redirect is observable without code access — the browser URL bar is the signal.

**Data persistence:** Data entered in the form at `/todos/new` persists after a page refresh — the item appears in the list at `/todos`.
- How to check: Create a to-do item, refresh the browser (F5), confirm the item is visible in the list.
- Acceptable because: The persistence is directly observable — the item either appears or does not.

**API liveness:** The health endpoint responds with HTTP 200.
- How to check: Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health` — output must be `200`.
- Acceptable because: The command produces a single numeric output that is either 200 or not.

**Error handling:** Submitting the login form with an invalid email shows an inline error message "Invalid email address" without a page reload.
- How to check: Enter `notanemail` in the email field, click Submit, confirm the error message appears inline (no page reload).
- Acceptable because: The error message is a concrete observable string; its presence or absence is unambiguous.

**Scaffolded project boots:** Running `pnpm dev` from the project directory starts the dev server and `http://localhost:3000` responds with HTTP 200.
- How to check: Run `pnpm dev`, wait for "ready" output in the terminal, then `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` — output must be `200`.
- Acceptable because: The exit code of curl is machine-verifiable; "ready" output is observable in the terminal.

**File on disk:** After scaffolding, the file `.env.example` exists at the project root and contains at least one `=` character (it is not empty).
- How to check: Run `test -s .env.example && grep -q '=' .env.example && echo OK` — output must be `OK`.
- Acceptable because: The file either exists with content or does not — binary observable outcome.

## Count Rule

Each VERIFICATION.md must contain 2 to 5 criteria. Fewer than 2 means the phase was not
verified. More than 5 means the phase scope was too large or criteria are not truly independent.

## Escalation Note

If `gsd_driver.py` cannot generate 2 valid falsifiable criteria for a phase (because the phase
produced no observable user behavior), it must flag this as a scope review rather than generating
un-falsifiable criteria. Prefer narrowing the criterion to something visible over broadening it to
something convenient.
