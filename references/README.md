# OSBuilder references/

Progressive-disclosure documentation. Files in this directory are loaded **on demand** by `SKILL.md` when a specific code path needs them — never all at once.

## Layout (one level deep, per Anthropic skill guidance)

| Subdirectory | Purpose | Loaded When |
|--------------|---------|-------------|
| `playbooks/` | Per-app-type recipes — what scaffolder runs, what stack defaults, what verification | Architect role picks a playbook based on intake |
| `roles/` | Per-role briefs — what each virtual dev-team member does, when they hand off, what skill they delegate to | Each role transition |
| `preflight/` | Per-OS install matrices — Homebrew, apt/dnf, winget mappings | First-run preflight check |
| `stack-menu.md` | Fallback stack defaults when web research is inconclusive | Architect role research |
| `state-md-schema.md` | The 10-field state.md schema in detail | Compaction-resume / debugging state issues |

## Convention

- **Markdown only.** No code in `references/` — code lives in `scripts/`.
- **One level deep.** Don't nest `playbooks/web/extra/` — flatten to `playbooks/web-extra.md` instead.
- **Read on demand.** SKILL.md links into specific files. Don't pre-load everything.
- **No XML/HTML tags.** Plain markdown only. Anthropic skill format forbids tags in description; we extend the rule to bodies for safety.

## Adding a new playbook or role

1. Create the file under the appropriate subdirectory.
2. Link it from SKILL.md's routing table where the role/playbook is selected.
3. Add an entry to the table in this README.
4. Ship via the same phase that introduces the new capability.

## Phase Status

- **Phase 1 (Foundation):** This README. Other reference files arrive in subsequent phases.
- **Phase 3 (Web playbook):** `playbooks/web.md`, `stack-menu.md`
- **Phase 5 (Common-person UX):** `roles/*.md`
- **Phase 2 (Pre-flight):** `preflight/macos.md`, `preflight/linux.md`, `preflight/windows.md`
- **Phase 7 (Additional playbooks):** `playbooks/{ai-service,cli,desktop,hub-platform}.md`
