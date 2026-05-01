# {{project_name}}

<!-- OSBuilder runbook -->
> Built by OSBuilder. Stack: {{stack_summary}}. Playbook: {{playbook}}.

## Quick Start

Clone the repo, copy the env example, install deps, and run.

```bash
git clone {{repo_url}}
cd {{project_name}}
cp .env.example .env
{{install_command}}
{{run_command}}
```

After cloning, install the gitleaks pre-commit hook so secrets can't be committed:

```bash
pip install pre-commit  # or: brew install pre-commit
pre-commit install
```

## Requirements

- Node 20+ (for `pnpm` / Next.js builds) or Python 3.13+ (for `uv` / FastAPI / CLI builds)
- git
- Docker + Docker Compose v2 (only when the app uses Postgres via `compose.yaml`)

## Configuration

Copy `.env.example` to `.env` and edit any placeholders. Never commit your `.env` —
the gitleaks pre-commit hook (installed above) blocks accidental secret commits.

```bash
cp .env.example .env
```

## Development

```bash
{{install_command}}
{{run_command}}
```

If the app uses Postgres, start it with:

```bash
docker compose up -d
```

## Tests

```bash
{{test_command}}
```

## How OSBuilder built this

This section is filled in by the Tech Writer step (`/gsd-docs-update`) — it explains
the dev-team metaphor (PM gathered requirements, Architect chose the stack, Frontend +
Backend + DevOps + QA built and reviewed it) in plain English.

If you're seeing this placeholder line, the Tech Writer step has not run yet on this
build. Re-run `/osbuilder` to complete the runbook.
