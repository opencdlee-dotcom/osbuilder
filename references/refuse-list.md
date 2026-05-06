# OSBuilder Refuse List (v1 default)

> Cross-referenced by `scripts/intake_handler.py:check_refuse_list`. The keyword list
> below is the source of truth — `intake_handler.REFUSE_KEYWORDS` mirrors it. The user-
> facing refusal copy lives under `## Refusal copy` and is read at runtime.
> NOT pulled into `SKILL.md` (which is locked at <= 200 lines per QUAL-01).

## Why a refuse list?

OSBuilder targets non-developers shipping their FIRST app. Kubernetes, microservices,
service mesh, and Helm are premature-complexity traps for v1: they multiply ops surface
area without solving any problem the user has yet. We refuse them in default mode AND
offer a documented path (`--production-ready`) that adds them as named ROADMAP phases —
NOT as default scaffold code.

## Refuse keywords

The intake handler matches these (case-insensitive, word-boundary for single-word; substring
for multi-word phrases):

- kubernetes
- k8s
- helm
- service mesh
- service-mesh
- microservice
- microservices
- istio
- linkerd
- consul
- electron

## Refusal copy

The `intake_handler.check_refuse_list` function loads everything in this section
(between `## Refusal copy` and the next `## See also`) and prints it to stderr,
substituting `{{keyword}}` with the matched term.

Hi — OSBuilder spotted **{{keyword}}** in your spec. In v1 default mode, OSBuilder
won't add Kubernetes, microservices, Helm, or service-mesh to your build. These add
ops complexity that almost always hurts a first build more than it helps.

OSBuilder v1 does NOT scaffold Kubernetes / microservices / service-mesh — those
are out of scope for the v1 playbooks (web, ai-service, cli, desktop, hub-platform).
Two practical paths forward:

1. **Drop the requirement for v1.** Ship a single-process app first; you can split
   it into microservices later when you have real load that justifies the ops cost.
   Rephrase your goal without **{{keyword}}** and re-run.
2. **Use a different tool.** If you genuinely need Kubernetes from day one, OSBuilder
   is the wrong choice — use the cloud provider's native tooling (EKS, GKE, AKS) or
   a platform like Render, Fly.io, or Railway that exposes K8s primitives.

Separately, if your concern is production-readiness rather than orchestration,
the `--production-ready` flag adds the seven scalable-by-default upgrades
(observability, migrations, healthchecks, secret manager, Sentry, rate limiting,
backups) as **named phases in your ROADMAP** — but it does NOT add Kubernetes
or microservices. They are different things.

**Electron (refused; use Tauri 2 instead).** OSBuilder builds desktop apps with Tauri 2, not Electron. Tauri produces ~10MB binaries (Electron is ~150MB) and uses ~50% less RAM. Tauri uses the system WebView (WebKit on macOS, WebView2 on Windows, webkit2gtk on Linux) plus a Rust runtime — Electron bundles a full Chromium per app. If you specifically need Electron-only APIs, that is out of scope for v1; the desktop playbook (`references/playbooks/desktop.md`) covers everything else.

## See also

- `scripts/intake_handler.py` — the gate (search for `check_refuse_list`)
- `scripts/production_phase_writer.py` — the `--production-ready` opt-in route

<!-- IN-20: maintainer-only references — these paths only exist in the source
repo (github.com/.../OSBuilder). At install time the skill lives at
~/.claude/skills/osbuilder/ and does not include `.planning/`. Keep this block
HTML-commented so installed-skill users do not see broken links. -->
<!--
- `.planning/milestones/v1.0-REQUIREMENTS.md` — SCL-05 + SCL-06 requirement IDs (maintainers only)
- `.planning/milestones/v1.0-ROADMAP.md` Phase 6 success criteria #5 — the falsifiable test (maintainers only)
-->

