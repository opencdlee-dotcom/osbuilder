# Example 01: TODO web app

**Playbook:** web
**Built:** <pending — placeholder example until OSBuilder Phase 6+7 complete>
**Repo:** [repo-url.txt](repo-url.txt)

## Original paragraph (intake)

> "I want a TODO web app where I can add tasks and check them off. It should
> work on my phone too, and I want my tasks to still be there if I close the
> browser and come back tomorrow."

## OSBuilder's expected interpretation

- **App type:** web
- **Playbook:** `references/playbooks/web.md` (Next.js 16.x + Drizzle +
  Postgres + Tailwind 4 + pnpm)
- **Inferred from keywords:** "web app", "phone too" (responsive), "still be
  there tomorrow" (persistence)
- **Notable refusals:** none in this example
- **Production-ready flag:** OFF (default — single-user TODO app does not
  need OpenTelemetry / Sentry / etc.)

## Before / After

| Stage | What it looked like | Screenshot |
|-------|---------------------|------------|
| Intake (paragraph) | (the paragraph above) | — |
| Derived spec | structured features list + stack hints | `screenshots/derived-spec.png` (pending) |
| Scaffolded project | Next.js + Drizzle + Postgres tree | `screenshots/scaffold-tree.png` (pending) |
| Working app | http://localhost:3000 with TODO list rendering | `screenshots/running.png` (pending) |
| Private GitHub | `gh repo create --private` succeeds; URL shown | `screenshots/repo-view.png` (pending) |

## How OSBuilder built this (expected sequence)

1. **PM** gathered requirements from the paragraph; asked one clarifying
   question ("Should other people be able to share your TODO list, or just
   you?" — user picks "just me", which sets `app_type: web` + `multi_user:
   false` (Postgres still appropriate per Phase 3 SC-4).
2. **Architect** chose Next.js 16.x + Drizzle + Postgres + Tailwind 4 + pnpm
   (per `references/playbooks/web.md`).
3. **DevOps** ran `pnpm create next-app@latest` then wired Drizzle schema +
   compose.yaml.
4. **Frontend** built the TODO list page; **Backend** wired the persistence
   layer; **DevOps** stamped Dockerfile + .github/workflows/test.yml.
5. **QA** ran `/code-tester` adversarial tests; **Reviewer** ran `/predator`
   + `/gsd:code-review`.
6. **Tech Writer** stamped a clone-and-run README via `/gsd:docs-update` +
   `/humanizer`.
7. **DevOps** ran `gh repo create --private` and pushed.

## Status

This example is currently a SPEC placeholder. It will be upgraded to a real
built repo once OSBuilder Phase 6 (ship-to-private-github) and Phase 7
(additional playbooks) complete and a real run produces a real URL.
`repo-url.txt` will be flipped from `NOT_PUBLISHED` to the real URL at that
point.

## See also

- [`../../references/playbooks/web.md`](../../references/playbooks/web.md) — web playbook reference
- [`../README.md`](../README.md) — gallery index
