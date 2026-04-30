# OSBuilder Web Playbook

> Specification for the web scaffold path (`app_type: web`).
> Loaded on-demand by the Architect role. NOT pulled into SKILL.md
> (line limit ≤ 200; see Phase 1 Plan 01-02).

## What the web playbook produces

A runnable Next.js 16 + Drizzle + Postgres + Tailwind 4 project on disk.
The user can `pnpm install && pnpm dev` and see the scaffolded homepage
on `localhost:3000` — with zero hand-written `package.json` or `tsconfig.json`.

## Scaffold command (non-interactive)

```bash
pnpm create next-app@latest <project-name> \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --eslint \
  --use-pnpm \
  --disable-git \
  --import-alias "@/*"
```

Source: nextjs.org/docs/app/api-reference/cli/create-next-app (verified 2026-04-30).
Note: `--disable-git` prevents a nested git init inside the scaffold directory (Pitfall 2).
Note: Do not use the shortcut flag that accepts all defaults — it reads saved machine preferences and may produce Pages Router or wrong layout. Always pass flags explicitly.

## Post-scaffold files written by OSBuilder

After `create-next-app` runs, OSBuilder writes exactly these 4 files:

| File | Purpose |
|------|---------|
| `src/lib/db.ts` | Drizzle + postgres.js connection (3 lines) |
| `drizzle.config.ts` | Drizzle Kit config with postgresql dialect |
| `.env.example` | `DATABASE_URL=` placeholder (committed; not secret) |
| `compose.yaml` | Docker Compose v2: postgres:18-alpine service |

## Files OSBuilder must NOT write

`create-next-app` already produces these — OSBuilder touching them causes conflicts:

`package.json`, `tsconfig.json`, `.eslintrc.json` (or `eslint.config.mjs`),
`next.config.ts`, `postcss.config.mjs`, `tailwind.config.ts`, `README.md`,
`src/app/` directory.

## Refuse list

In v1 default builds, OSBuilder refuses:

- Kubernetes / Helm / service mesh
- Microservices architecture
- Electron (use Tauri 2 via desktop playbook)
- Auto-deploy without explicit consent
- Public GitHub repos by default (use `--public` to override)

## Stack (pinned versions — verified 2026-04-30)

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Scaffold | create-next-app | 16.2.4 | includes Next.js 16 + React 19.2 + TS 5.x |
| CSS | tailwindcss | 4.2.4 | CSS-first config via `@theme`; no tailwind.config.js |
| ORM | drizzle-orm | 0.45.2 | lighter than Prisma; type-safe; locked decision |
| Migrations | drizzle-kit | 0.31.10 | companion to drizzle-orm |
| DB driver | postgres (postgres.js) | 3.4.9 | recommended for serverless/edge |
| Package mgr | pnpm | 10.33.2 | `--use-pnpm` flag in create-next-app |
| Database | postgres Docker | 18-alpine | pinned; `compose.yaml` service name: `postgres` |

## See also

- `references/stack-menu.md` — fallback defaults for stack_researcher.py
- `references/question-bank.md` — plain-English intake questions
- `scripts/scaffold_dispatch.py` — implementation that reads this spec
- `RESEARCH.md` Phase 3 — verification sources and pitfall catalog
