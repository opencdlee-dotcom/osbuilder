# Phase 8: Skill quality / publish-bar - Research

**Researched:** 2026-05-02
**Domain:** Open-source publish-bar for a Claude Code skill — CI lint, install one-liner, README/demo, examples gallery, version-drift validator, `--production-ready` flag verification
**Confidence:** HIGH for codebase state (read directly), Anthropic skill conventions (verified via Anthropic docs), CI scaffolding patterns (verified against actions/setup-* live versions on GitHub Marketplace 2026-05-02). MEDIUM for ecosystem version-detection (`requires:` is a custom convention OSBuilder is inventing — not an upstream Anthropic standard). MEDIUM for demo-video format choice (asciinema vs GIF tradeoff is project-call). LOW for example-app candidate selection (depends on what OSBuilder has actually built — currently nothing in `examples/` beyond `.gitkeep`).

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QUAL-01 | SKILL.md is ≤ 200 lines (verified via lint script) | Existing test `test_skill_md_line_count_under_200` in `scripts/tests/test_skill_md.py` covers asserting locally at test time. Phase 8 adds: (1) standalone lint script `scripts/check_skill_md_length.py` runnable from CI without pytest, (2) GitHub Actions workflow `.github/workflows/ci.yml` invoking it on every PR. Current SKILL.md = 130 lines (69 lines of headroom). |
| QUAL-02 | Clean `install.sh` one-liner installs OSBuilder for someone never used Claude Code skills | Existing `install.sh` (79 lines) handles repo-local install via `cp`. Phase 8 must add a published one-liner: `curl -fsSL https://raw.githubusercontent.com/<owner>/osbuilder/main/install.sh \| sh` works ONLY when there is a public mirror to fetch from. Repo currently has NO `git remote`; the planner must lock the published-repo URL before this requirement is verifiable. |
| QUAL-03 | README explains dev-team metaphor + links 60-second demo video | No README.md exists in repo root today. Phase 8 creates `README.md` from scratch: (1) ≥ 1 section mapping the 8 dev-team roles to user-facing narration, (2) embed/link of a 60-second demo video. Recommendation locked: GIF (works on bare GitHub) + asciinema link (works for those with JS). |
| QUAL-04 | `examples/` contains ≥ 3 (target 5) reference apps | `examples/` exists but holds only `.gitkeep`. Phase 8 must produce 3-5 example sub-directories, each with: README/SPEC, screenshots, repo URL or public mirror. Candidate apps come from running OSBuilder against canned paragraphs (the work itself produces the gallery — this is partially a UAT exercise). |
| QUAL-05 | First-invocation skill-version-drift validator | New script `scripts/check_skill_versions.py` reads `requires:` block from SKILL.md frontmatter. **Critical research finding:** `requires:` is NOT a standard Anthropic frontmatter field, AND of the 5 target sub-skills (gsd, brainiac, predator, code-tester, problem-solver), only 3 currently expose a `version:` field — gsd and predator have NO version field in their SKILL.md as of 2026-05-02. The validator must handle missing-version gracefully (not block), AND the project must define a fallback signal (e.g., "if `version:` absent, treat as `0.0.0` and warn). |

**Note on success criterion 6 (`--production-ready` flag — not a numbered REQ):** Phase 6 already shipped `scripts/production_phase_writer.py` (137 lines) that emits `/gsd-add-phase {observability,migrations,healthchecks,secret-manager,sentry,rate-limiting,backups}` slash commands when `state.md production_ready=='true'`. The flag is plumbed end-to-end (intake_handler.py → state_writer.py → gsd_driver.py step ~3 → production_phase_writer.py emit). Phase 8 work for this criterion is **verification only** — confirm the existing implementation matches the success-criterion language and add a documentation pass; **do not re-implement.**
</phase_requirements>

---

<user_constraints>
## User Constraints (from CONTEXT.md)

**No CONTEXT.md exists yet** — this RESEARCH.md is feeding `gsd-discuss-phase` next, not the planner directly. The locked decisions and Claude's-discretion areas will be set by the user during the discuss step. Until then, the items in `## Open Decisions` below are the questions the discuss phase needs to answer.
</user_constraints>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SKILL.md line-count linting | CI pipeline (.github/workflows) | Local pytest (`test_skill_md.py`) | CI fails the PR; pytest catches it locally. Same assertion, two surfaces. |
| Install one-liner (`curl … \| sh`) | Public-internet fetch (GitHub raw) | Local copy via `install.sh` | The remote URL is what makes it "one-liner"; the script content is identical to the repo-local installer. |
| README dev-team metaphor doc | Documentation (root README.md) | Cross-link to `references/roles/*.md` | README is shop-window; `references/roles/` is the canonical narration source — link, don't duplicate. |
| Demo video | Hosted asset (GIF in repo or asciinema.org) | README embed | Video lives outside the skill loadout — it's marketing, not runtime. |
| Examples gallery | Repository tree (`examples/<name>/`) | Public-mirror repos (GitHub) | Each example is a directory in OSBuilder repo + URL of the (private) repo OSBuilder built. |
| Version-drift validator | Helper script (`scripts/check_skill_versions.py`) | Session marker (state.md or `~/.osbuilder/`) | Validator is Python stdlib; "first invocation this session" needs a marker file because Python has no session state. |
| `--production-ready` flag | Already-shipped (Phase 6 `production_phase_writer.py`) | Verification-only docs | Implementation done; Phase 8 only verifies + documents. |

---

## Standard Stack

### Core (OSBuilder's Phase 8 implementation language — locked by project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.13 | All Phase 8 helper scripts | Project rule: pure stdlib — `friendly_error.py`, `state_writer.py`, `production_phase_writer.py` all stdlib-only. No new third-party deps for QUAL-05 validator. [VERIFIED: scripts/*.py docstrings all read "Pure stdlib"] |
| pytest | ≥ 8.0 | Test framework | Already in `pyproject.toml [project.optional-dependencies] dev`. [VERIFIED: pyproject.toml] |
| GitHub Actions | latest | CI pipeline for QUAL-01 | No alternative — repo will live on GitHub. [VERIFIED: docs.github.com/actions] |
| Bash (POSIX `sh`) | n/a | install.sh one-liner | Existing `install.sh` is `#!/bin/sh` POSIX-portable. [VERIFIED: install.sh line 1] |

### Supporting (CI workflow + tooling)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `actions/checkout@v6` | v6 (latest) | Check out code in CI | Default for any GitHub Actions workflow. [VERIFIED: github.com/actions/checkout latest release tag v6 as of 2026-05-02] |
| `actions/setup-python@v6` | v6 | Install Python in CI | Same major version as already used in `assets/ci-workflows/python.yml.tmpl`. [VERIFIED: assets/ci-workflows/python.yml.tmpl line 14] |
| `astral-sh/setup-uv@v6` | v6 | Install uv in CI | Faster than pip; project already uses uv (`uv.lock` present). [VERIFIED: assets/ci-workflows/python.yml.tmpl line 17] |
| `agg` (asciinema-gif-generator) | latest | Convert asciinema cast → GIF | If user picks asciinema-recorded demo. Optional toolchain. [CITED: docs.asciinema.org/manual/agg/] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Standalone Python lint script | Bash one-liner: `[ "$(wc -l < SKILL.md)" -le 200 ]` | Pro: one fewer file. Con: less testable, no exit-code semantics, no friendly error message. Reject in favor of `scripts/check_skill_md_length.py`. |
| `packaging.version.Version` for semver compare | Hand-rolled stdlib tuple comparison | Project rule = pure stdlib. `packaging` not in deps; adding it violates Phase 1's "no third-party" decision. Hand-roll a 20-line `_parse_version("1.2.3") -> tuple[int, ...]` helper instead. |
| `curl … \| sh` install pattern | `git clone && cd && ./install.sh` | Pro of curl-pipe: literally one line, never asks user about clone target. Con: harder to audit (security teams flag pipe-to-shell). Project parallel: predator's install.sh runs from existing skill dir; OSBuilder's lives in repo. **Recommendation:** ship BOTH — README has `git clone` for security-conscious users + `curl \| sh` for max-friction-removal. |
| asciinema embed (script tag) | GIF or static thumbnail | GitHub READMEs strip `<script>`. Cannot embed asciinema player directly. **Decision:** GIF (auto-plays in README) + asciinema link as secondary (better quality, copy-pasteable transcript). [CITED: docs.asciinema.org getting started] |
| Custom `requires:` block | Hardcoded version constants in `check_skill_versions.py` | Hardcoding ties dependency versions to the validator file (must edit code to change minimums). Frontmatter block is data-driven. **Decision:** custom `requires:` in SKILL.md frontmatter — BUT must respect Anthropic's "all-fields-optional" hands-off frontmatter policy (no upstream conflict; just adds an extra key). |

**Installation (no new packages):**
```bash
# All Phase 8 scripts are pure stdlib; no `pip install` needed.
# CI pipeline uses GitHub Actions runners' default toolchain.
```

**Version verification (2026-05-02):**

| Component | Detected version | Verification |
|-----------|------------------|--------------|
| Python | 3.13.13 | `python3 --version` on dev machine [VERIFIED] |
| pytest | ≥ 8.0 | `pyproject.toml` constraint [VERIFIED] |
| GitHub Actions setup-python | v6 | already pinned in `assets/ci-workflows/python.yml.tmpl` [VERIFIED] |
| GitHub Actions setup-uv | v6 | already pinned in `assets/ci-workflows/python.yml.tmpl` [VERIFIED] |
| gh CLI (for one-liner verification) | 2.90.0 | Phase 6 RESEARCH.md noted on dev machine [CITED: 06-RESEARCH.md] |
| asciinema CLI | latest | optional; only if asciinema chosen for demo [CITED: docs.asciinema.org] |
| agg (asciinema → GIF) | latest | optional; converts asciinema casts to embedded GIFs [CITED: docs.asciinema.org/manual/agg/] |

---

## Architecture Patterns

### System Architecture Diagram

```
                           Phase 8 Surface
                                  │
        ┌─────────────────────────┼──────────────────────────┐
        │                         │                          │
        ▼                         ▼                          ▼
   QUAL-01 (CI lint)        QUAL-02 (install)         QUAL-03 (README)
        │                         │                          │
        │                         │                          │
   ┌────┴─────┐            ┌──────┴───────┐          ┌───────┴────────┐
   │          │            │              │          │                │
   ▼          ▼            ▼              ▼          ▼                ▼
 lint       CI yml     install.sh     README        dev-team       demo
 script   workflow      (existing,   one-liner      metaphor       video
  (new)    (new)        unchanged)   doc snippet    section        (new)
   │         │              │             │          │                │
   └─────────┴──────────────┴─────────────┴──────────┴────────────────┘
                                  │
        ┌─────────────────────────┼──────────────────────────┐
        ▼                         ▼                          ▼
   QUAL-04 (gallery)        QUAL-05 (validator)       SC-6 (--prod-ready)
        │                         │                          │
   ┌────┴─────┐            ┌──────┴───────┐          ┌───────┴───────┐
   │          │            │              │          │               │
   ▼          ▼            ▼              ▼          ▼               ▼
 examples/  per-app      requires:    check_skill   verify         doc
 dir        SPEC.md +    block in     _versions.py  existing       update
 (3-5       screenshots  SKILL.md     (new)         emit() impl    (no code)
 entries)   (new)        (new)         │            (Phase 6)
                                       │
                                  session marker
                                  (~/.osbuilder/
                                  last_check.txt)
```

Data flow:
- Each PR commit → CI workflow runs lint script → SKILL.md > 200 lines = PR fails
- User runs install one-liner → curl fetches install.sh from public mirror → install.sh copies repo → ~/.claude/skills/osbuilder/
- User invokes `/osbuilder` first time per session → check_skill_versions.py reads `requires:` from SKILL.md → reads each sub-skill's `version:` from `~/.claude/skills/<name>/SKILL.md` → compares semver → friendly error + refuse if drift

### Recommended Project Structure (Phase 8 additions)

```
OSBuilder/
├── SKILL.md                            # add `requires:` block to frontmatter
├── README.md                           # NEW: dev-team metaphor + demo video + install one-liner
├── install.sh                          # unchanged; already idempotent and POSIX-portable
├── .github/                            # NEW directory
│   └── workflows/
│       └── ci.yml                      # NEW: lint + pytest on PR
├── scripts/
│   ├── check_skill_md_length.py        # NEW: standalone lint script (200-line cap)
│   ├── check_skill_versions.py         # NEW: first-session validator (QUAL-05)
│   └── tests/
│       ├── test_check_skill_md_length.py    # NEW
│       └── test_check_skill_versions.py     # NEW
├── examples/                           # FILL: currently only .gitkeep
│   ├── README.md                       # NEW: gallery index
│   ├── 01-todo-web/                    # NEW: ≥ 3, target 5
│   │   ├── SPEC.md                     # paragraph + before/after
│   │   ├── screenshots/
│   │   └── repo-url.txt                # private repo URL or public mirror
│   ├── 02-cli-photo-organizer/
│   ├── 03-fastapi-summarizer/
│   ├── 04-tauri-tray-app/              # if 5
│   └── 05-hub-platform-mini/           # if 5
└── assets/
    └── demo/                           # NEW
        ├── osbuilder-demo.gif          # NEW: 60s GIF for README embed
        └── osbuilder-demo.cast         # NEW: asciinema source for re-renders
```

### Pattern 1: Standalone-script-with-CLI (matches existing OSBuilder script shape)

**What:** Each new helper script (check_skill_md_length.py, check_skill_versions.py) is invokable as a CLI from CI / shell, with stdlib-only argparse, exits non-zero on failure, prints friendly user-facing error on stderr.

**When to use:** Every Phase 8 lint/validator. Mirrors `state_writer.py`, `production_phase_writer.py`, `registry_verify.py` exactly.

**Example:**
```python
# Source: scripts/production_phase_writer.py (verified pattern)
#!/usr/bin/env python3
"""check_skill_md_length.py — fail CI if SKILL.md exceeds 200 lines."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"
LIMIT = 200


def check(skill_md: Path = SKILL_MD, limit: int = LIMIT) -> int:
    if not skill_md.exists():
        sys.stderr.write(f"OSBuilder: SKILL.md not found at {skill_md}\n")
        return 2
    lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    if lines > limit:
        sys.stderr.write(
            f"OSBuilder: SKILL.md is {lines} lines, limit is {limit}. "
            f"Move detail to references/ via progressive disclosure.\n"
        )
        return 1
    print(f"OK: SKILL.md is {lines}/{limit} lines.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_skill_md_length")
    parser.add_argument("--skill-md", default=str(SKILL_MD))
    parser.add_argument("--limit", type=int, default=LIMIT)
    args = parser.parse_args(argv)
    return check(Path(args.skill_md), args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Pattern 2: GitHub Actions workflow with `uv` + standalone-script invocation

**What:** Single `ci.yml` running lint + pytest on every PR. Mirrors what OSBuilder *itself* generates for built repos via `assets/ci-workflows/python.yml.tmpl` — eat your own dog food.

**When to use:** Phase 8 PR-bar enforcement.

**Example:**
```yaml
# Source: actions/setup-python v6 + assets/ci-workflows/python.yml.tmpl pattern
# Verified 2026-05-02 (setup-python v6, setup-uv v6 both latest)
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-skill-md:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - run: python3 scripts/check_skill_md_length.py

  test:
    runs-on: ubuntu-latest
    needs: lint-skill-md
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run pytest
```

### Pattern 3: Frontmatter block parsing (stdlib-only)

**What:** Read `requires:` block from SKILL.md frontmatter. Pattern already in `scripts/tests/test_skill_md.py:_read_frontmatter` (hand-parses YAML without PyYAML).

**When to use:** check_skill_versions.py reads BOTH OSBuilder's SKILL.md (for the `requires:` minimums) and each sub-skill's SKILL.md (for the `version:` declaration).

**Example (extending existing pattern):**
```python
# Source: scripts/tests/test_skill_md.py:_read_frontmatter (verified)
# Adds nested-block support for `requires:` (key: value pairs indented under requires:)

import re
from pathlib import Path

def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields: dict = {}
    current_key = None
    nested: dict | None = None
    for line in m.group(1).splitlines():
        # Detect indented sub-keys under e.g. `requires:`
        if line.startswith("  ") and nested is not None:
            sub_k, _, sub_v = line.strip().partition(":")
            nested[sub_k.strip()] = sub_v.strip()
            continue
        if line.startswith(" ") and current_key:
            fields[current_key] += " " + line.strip()
            continue
        nested = None
        if ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key == "requires" and not value:
                fields[key] = {}
                nested = fields[key]  # type: ignore[assignment]
            elif value == ">":
                fields[key] = ""
                current_key = key
            else:
                fields[key] = value
                current_key = key
    return fields
```

### Anti-Patterns to Avoid

- **Hardcoding version constants in `check_skill_versions.py`:** ties dependency policy to code; harder to update. Use the `requires:` block as the single source of truth (data-driven).
- **Using PyYAML or `packaging`:** violates project's pure-stdlib rule. Hand-roll the 20-line semver parser + frontmatter reader.
- **Recording the demo with terminal-specific styling:** asciinema captures the exact terminal escape sequences; if you record on a kitten/iTerm with custom themes, the GIF rendering may not match what most users see. Record in a vanilla terminal (Terminal.app default theme or Linux gnome-terminal default).
- **Embedding `<video>` HTML in README:** GitHub strips `<script>` AND many `<video>` configurations. Use a GIF that auto-plays + a click-through link to a hosted MP4 / asciinema cast for high-quality.
- **Putting screenshots in `examples/<app>/screenshots/` AND committing 5MB PNGs:** GitHub repo bloat. Use compressed JPG ≤ 200KB each, or stash in `.gitignore` + link to externally-hosted URLs (project parallel: install.sh shouldn't grow with screenshot count).
- **Treating `--production-ready` as new work:** Phase 6 already shipped it (`production_phase_writer.py` 137 lines, wired into `gsd_driver.py` step 3). Phase 8 must verify, not re-implement. Easy regression: a planner who didn't read Phase 6 history could create duplicate plans here.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Run lint on every PR | Custom git pre-receive hook | GitHub Actions workflow | GH Actions is the universal CI surface; `pre-receive` requires GitHub Enterprise. |
| Detect skill version | Custom file-walking heuristic | Frontmatter `version:` field (existing convention) | brainiac, code-tester, problem-solver already use it; extend pattern. |
| Compare semver in Python | Custom regex | Tuple-of-ints comparison | `tuple(int(x) for x in s.split("."))` works for `MAJOR.MINOR.PATCH`. Avoid pre-releases (e.g., `1.0.0-beta1`) — sub-skills don't use them. |
| Embed video in GitHub README | Custom video player JS | GIF auto-play + asciinema link | GitHub strips `<script>`. GIF is the lowest-friction format. |
| Generate the gallery index | Hand-write `examples/README.md` table from scratch | Generate from each sub-dir's `SPEC.md` heading | Cheap stdlib script avoids drift between sub-dir SPEC and the index. |
| Create a public mirror of a private repo | Manual `git push` to a second remote | `gh repo create --public --clone` of a sanitized snapshot | If example repos are private, a thin public mirror surfaces example code without leaking user data. Optional. |

**Key insight:** Phase 8 is mostly **assembly + verification**, not new logic. The hard parts (state machine, scaffolders, refusal gates, `--production-ready`) are done. The remaining work is documentation polish, CI plumbing, and producing the gallery from earlier phases' output. Don't over-architect.

---

## Runtime State Inventory

This phase has no rename, refactor, or migration components — it is purely additive (new files, new doc sections, new CI). No runtime state inventory needed.

---

## Common Pitfalls

### Pitfall 1: SKILL.md exceeds 200 lines mid-phase as new sections accrete

**What goes wrong:** Adding `requires:` block to frontmatter + any in-body callouts pushes SKILL.md past 200 lines, failing the very lint script being built.
**Why it happens:** SKILL.md is currently 130 lines (69 lines of headroom). The `requires:` block alone is ~10 lines. Phase 8 may want to also document the install one-liner inline.
**How to avoid:** Move install one-liner doc to README.md, NOT SKILL.md. Push any explanatory `requires:` policy to `references/version-policy.md`. Keep SKILL.md edits to the 5-line frontmatter block + zero body changes.
**Warning signs:** Lint script returning 1 on the same PR that added it.

### Pitfall 2: Sub-skill version field is missing entirely (gsd, predator)

**What goes wrong:** `check_skill_versions.py` reads `~/.claude/skills/gsd/SKILL.md` frontmatter, finds no `version:` field, raises `KeyError` and crashes — the validator that's supposed to catch drift becomes a broken-on-arrival blocker.
**Why it happens:** Anthropic skill spec marks `version:` as optional. Confirmed via direct file read: gsd's SKILL.md has no version field; predator's has no version field; only brainiac (6.0.0), code-tester (3.1.0), problem-solver (3.0.0) declare versions. [VERIFIED: `head -10 ~/.claude/skills/{gsd,predator}/SKILL.md` shows no `version:` field on 2026-05-02]
**How to avoid:** Treat absence-of-version as `0.0.0` AND emit a "warn but proceed" message. Friendly text: `"⚠️  gsd has no version field — cannot enforce minimum X.Y.Z. Proceeding anyway. (Reported in non-blocking mode.)"` Two-mode design: (a) blocking mode for skills that DO declare a version, (b) advisory mode for those that don't. Downstream: file an issue against gsd & predator to add `version:` blocks (Composition rule says fix the sub-skill, don't fork — but we can't BLOCK on that landing).
**Warning signs:** Validator throws `KeyError: 'version'` on first invocation.

### Pitfall 3: First-invocation marker collides across CWDs

**What goes wrong:** "First invocation per session" detection uses a marker file. If marker lives at `<project-root>/.planning/osbuilder/checked.txt`, then a user with two projects gets the validator run twice (once per project). If marker lives at `~/.osbuilder/last_check.txt`, then a single-project user sees it run only on the very first day.
**Why it happens:** "Session" is fuzzy in Claude Code — there is no per-session lifecycle hook. Phase 1 already chose to scope state to `<project-root>/.planning/osbuilder/state.md` (per-project). But version-drift is **per-machine**, not per-project.
**How to avoid:** Marker location: `~/.osbuilder/last_check.txt` (per-user-global, NOT per-project). Trigger condition: file does not exist OR mtime is older than $X (e.g., 24h, or simply absent — recommend absent). Validator writes the file on success. User wipes file to force re-check. Document the location in README.
**Warning signs:** User reports validator fires on every `/osbuilder` invocation (marker logic broken) or never fires after first day (mtime check too coarse).

### Pitfall 4: `install.sh` one-liner served from a not-yet-existing public repo

**What goes wrong:** README says `curl -fsSL https://raw.githubusercontent.com/<owner>/osbuilder/main/install.sh | sh`, but the repo has no remote yet. The one-liner is a documentation lie until the repo is published.
**Why it happens:** Repo currently has NO `git remote` configured (`git remote -v` returns empty). The repo URL must be locked BEFORE the README's one-liner can be verified to work end-to-end on a clean machine. [VERIFIED 2026-05-02: `git remote -v` empty]
**How to avoid:** Discuss-phase locks the GitHub owner/repo URL. Pre-flight test: spin up a fresh container (Docker `ubuntu:latest`), run the one-liner, verify `~/.claude/skills/osbuilder/SKILL.md` lands. Do this BEFORE marking QUAL-02 done.
**Warning signs:** README has a `<TODO: replace owner>` placeholder at phase-end; or the lint job ALSO needs the URL but doesn't have it.

### Pitfall 5: Examples gallery is 5 toy apps that don't exercise different playbooks

**What goes wrong:** All 5 examples are TODO-list variants. Gallery proves nothing about OSBuilder's range; reads as filler.
**Why it happens:** Easy temptation to scaffold 5 identical-shaped builds. ROADMAP success criterion 4 says "validation + onboarding" — gallery must demonstrate breadth.
**How to avoid:** Constraint each example to a different playbook (web, ai-service, cli, desktop, hub-platform — Phase 7 shipped all 5). Lock candidate matrix during discuss-phase: 1 web, 1 cli, 1 ai-service is the minimum 3; for 5, add desktop + hub-platform. Each example's SPEC.md includes the original paragraph + the playbook OSBuilder picked.
**Warning signs:** Examples gallery README has no playbook column or it has the same playbook on 4/5 rows.

### Pitfall 6: Demo video shows aspirational UX, not the real thing

**What goes wrong:** 60-second demo records a curated edit of OSBuilder running. User clones, runs OSBuilder, gets different (worse) output, loses trust.
**Why it happens:** Lovable / v0 trust loss precedent (cited in `.planning/PROJECT.md` refuse-list rationale) — over-promising on demo is a documented v1 trust killer.
**How to avoid:** Record an end-to-end real run (paragraph → working app → private GitHub URL shown). NO cuts that hide friction. NO "voice-over saying what's about to happen if it worked." If the run takes 5 minutes, speed up to 60s in post but keep every state visible. Consider 2 demos: 60s "happy path" + 3-5min "real-time, unedited" companion linked from README.
**Warning signs:** Demo doesn't show the OSBuilder output at the same speed as captured; demo skips a phase ("now imagine the verify step ran...").

### Pitfall 7: `requires:` block invented as a custom convention without disclaimer

**What goes wrong:** Future Anthropic skill spec adds `requires:` with different semantics than OSBuilder's; conflict.
**Why it happens:** Confirmed via web research 2026-05-02: `requires:` is NOT a standard frontmatter field. Anthropic's docs list `name`, `description`, `allowed-tools`, `disable-model-invocation` as known fields; everything else is optional/custom and could be absorbed/redefined in future versions. [CITED: code.claude.com/docs/en/skills + platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices]
**How to avoid:** Document the `requires:` block format in `references/version-policy.md` clearly as "OSBuilder convention." Use a namespaced key if conflict-aversion matters: `osbuilder-requires:` (longer but unambiguous). **Recommendation:** keep `requires:` (shorter, intuitive); add a comment in SKILL.md frontmatter clarifying it's an OSBuilder-local convention.
**Warning signs:** A future Anthropic doc release adds `requires:` with different semantics (link rot risk).

### Pitfall 8: Production-ready verification re-implements instead of verifying

**What goes wrong:** Phase 8 work creates a duplicate `--production-ready` script or alters production_phase_writer.py in ways that break Phase 6 tests (`test_production_ready.py`).
**Why it happens:** Phase 8 success criterion 6 reads like a TODO. It is not — Phase 6 finished it.
**How to avoid:** Phase 8 task for SC-6 = "run `pytest scripts/tests/test_production_ready.py` + manually verify with a test repo + add docs in README." Zero code changes to scripts/.
**Warning signs:** A Plan in Phase 8 lists `scripts/production_phase_writer.py` as a target file to modify.

---

## Code Examples

Verified patterns from official sources / existing OSBuilder code:

### Reading a SKILL.md frontmatter block (stdlib regex)

```python
# Source: scripts/tests/test_skill_md.py (existing OSBuilder pattern, verified)
import re
from pathlib import Path

def read_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields
```

### Stdlib semver tuple comparison

```python
# Source: hand-rolled (project rule = pure stdlib, packaging not in deps)
def parse_version(s: str) -> tuple[int, ...]:
    """Parse "MAJOR.MINOR.PATCH" → (major, minor, patch). Pre-releases not supported."""
    if not s:
        return (0, 0, 0)
    parts = s.strip().split(".")
    try:
        return tuple(int(p) for p in parts[:3]) + (0,) * (3 - len(parts))
    except ValueError:
        return (0, 0, 0)  # malformed = "older than anything" — fail-safe

# Usage:
assert parse_version("1.2.3") < parse_version("1.10.0")
assert parse_version("") == (0, 0, 0)
assert parse_version("v6.0.0".lstrip("v")) == (6, 0, 0)
```

### GitHub Actions: minimal CI for SKILL.md lint + pytest

```yaml
# Source: actions/setup-python@v6 + actions/checkout@v6 + astral-sh/setup-uv@v6
# Verified 2026-05-02 against assets/ci-workflows/python.yml.tmpl + GitHub Marketplace
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - name: Lint SKILL.md line count
        run: python3 scripts/check_skill_md_length.py
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run pytest
```

### Install one-liner pattern (POSIX-portable, README snippet)

```bash
# Source: standard curl-pipe-shell pattern; verified against predator's install.sh idiom
# Recommended in README.md after locking the public-repo URL.

# Quick install (one-liner — fastest, requires trusting the pipe):
curl -fsSL https://raw.githubusercontent.com/<owner>/osbuilder/main/install.sh | sh

# Audited install (preferred if security policy requires reading first):
git clone https://github.com/<owner>/osbuilder ~/osbuilder-src
cd ~/osbuilder-src && ./install.sh
```

### check_skill_versions.py first-session marker check

```python
# Source: hand-rolled to project conventions (~/.osbuilder/ for per-user-global state)
import os
from pathlib import Path

MARKER = Path(os.path.expanduser("~/.osbuilder/last_check.txt"))

def is_first_session() -> bool:
    return not MARKER.exists()

def record_check_complete() -> None:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text("ok\n", encoding="utf-8")
```

---

## State of the Art

| Old Approach | Current Approach (2026) | When Changed | Impact |
|--------------|-------------------------|--------------|--------|
| `actions/setup-python@v4` | `actions/setup-python@v6` | 2025 | v6 supports Python 3.13 directly, faster cache lookup. |
| `astral-sh/setup-uv@v1` (early adopters) | `astral-sh/setup-uv@v6` | 2025 | Mature `enable-cache` + `--frozen` support. |
| asciicast2gif (deprecated) | `agg` (Rust-based) | 2023 | asciicast2gif Node tooling deprecated; agg is the supported successor for asciinema → GIF. [CITED: docs.asciinema.org/manual/agg/] |
| `<video>` HTML in README | GIF + linked MP4/asciinema | always (GitHub limitation) | GitHub strips most `<video>` configs; GIF auto-plays inline. [CITED: thelinuxcode.com 2026 playbook] |
| Hardcoded version constants | Frontmatter `requires:` block (custom) | OSBuilder 2026 | Data-driven; future-readable. (NOT a standard Anthropic field — OSBuilder convention.) |

**Deprecated/outdated:**
- asciicast2gif: replaced by `agg`.
- `actions/checkout@v3` and earlier: superseded by v6.
- Bare `bash <(curl ...)`: use `curl ... | sh` (project-wide POSIX-portable convention).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The OSBuilder repo will be hosted publicly on GitHub at a URL the user controls. | QUAL-02 | If repo stays private/never publishes, the curl one-liner literally cannot work; QUAL-02 becomes "TODO until publish." Lock URL in discuss-phase. |
| A2 | A 60-second demo can be recorded end-to-end without exposing the user's real GitHub credentials. | QUAL-03 | Recording shows `gh auth login` flow → reveals credential bits if not redacted; record on a throwaway gh login. |
| A3 | At least 3 of OSBuilder's 5 playbooks (web, ai-service, cli, desktop, hub-platform) can produce a viable example app within Phase 8's time budget. | QUAL-04 | If Phase 6 + 7 outputs aren't ready (Phase 6 status: 0/6 plans complete per ROADMAP), then OSBuilder cannot produce gallery apps yet; gallery work is gated on Phase 6 completion. |
| A4 | Skipping `version:`-less sub-skills with a non-blocking warn is acceptable UX for QUAL-05's "refuses to proceed until upgraded" success criterion. | QUAL-05 + Pitfall 2 | Strict reading of "refuses to proceed" might require BLOCKING on missing version. Discuss-phase must lock policy: warn-and-continue OR refuse-and-prompt-fix. |
| A5 | Anthropic will not introduce a conflicting `requires:` frontmatter field within OSBuilder v1's lifecycle. | Pitfall 7 | If they do, OSBuilder needs a frontmatter migration. Mitigation: use `osbuilder-requires:` if the user wants belt-and-suspenders. |
| A6 | The session-marker file `~/.osbuilder/last_check.txt` is acceptable per-user-global state — Phase 1 only locked per-project state for state.md, not against per-user state for unrelated concerns. | Pitfall 3 | If user dislikes ~/.osbuilder/, alternative is putting marker in `<project-root>/.planning/osbuilder/version_check.txt` and accepting per-project re-runs. |
| A7 | Phase 6's `production_phase_writer.py` already covers SC-6's full intent; no Phase 8 code change needed. | Pitfall 8 + SC-6 | If discuss-phase decides SC-6 needs additional work (e.g., 8th named upgrade, custom upgrades, --production-ready=ALL flag variant), then plan must add new code despite Phase 6 baseline. |

---

## Open Questions (RESOLVED)

1. **Public repo URL for the install one-liner**
   - What we know: Repo currently has no remote. install.sh is repo-local-only.
   - What's unclear: GitHub owner / repo name OSBuilder will publish under.
   - Recommendation: Discuss-phase locks the URL. Suggest `<github-username>/osbuilder` or `osbuilder-skill/osbuilder` (org).
   - **RESOLVED:** Locked at the 08-01 Task 0 URL gate (checkpoint:decision). User selects option-personal/option-org/option-defer; chosen URL written to `08-URL-LOCK.md` and substituted by 08-04 (CI badge), 08-06 (README), and 08-HUMAN-UAT.md. (see 08-01)

2. **GIF vs asciinema cast for the demo (60s)**
   - What we know: GitHub strips `<script>`; GIFs auto-play; asciinema is higher quality but requires click-through.
   - What's unclear: User's preference for "good enough auto-play" vs "high quality with click-through."
   - Recommendation: Both — GIF in README body + asciinema link in caption. Cost is one extra recording session.
   - **RESOLVED:** Both — GIF embedded in README + asciinema `.cast` linked alongside, per recommendation. Demo assets land at `assets/demo/osbuilder-demo.{gif,cast}` (see 08-07).

3. **Sub-skill version-missing policy**
   - What we know: gsd and predator have no `version:` field. Composition rule says fix sub-skills, not OSBuilder.
   - What's unclear: Should QUAL-05 BLOCK on missing version OR WARN and continue?
   - Recommendation: WARN. Document in `references/version-policy.md`. File issues upstream against gsd & predator to add `version:` blocks.
   - **RESOLVED:** WARN (not BLOCK) — `check_skill_versions.py` returns rc 0 with stderr warning when `version:` is absent on an installed sub-skill. Documented in `references/version-policy.md` 4-row behavior table (see 08-04).

4. **Examples gallery: 3 vs 5**
   - What we know: ROADMAP says "≥ 3 (target 5)." Phase 6 (ship) is 0/6 — no shippable build yet from the OSBuilder loop.
   - What's unclear: Whether to block Phase 8 on having 5 real examples (sequential dependency on Phase 6 + Phase 7) or ship 3 with TODO for 4-5.
   - Recommendation: 3 minimum to pass; document path to 5 in `examples/README.md`. Each must use a different playbook.
   - **RESOLVED:** 3 examples minimum (web / cli / ai-service — three distinct playbooks per Pitfall 5). Path to 5 (desktop, hub-platform) documented in `examples/README.md` and gated on Phase 6 + 7 real builds via 08-HUMAN-UAT.md row 4 (see 08-08).

5. **Custom `requires:` namespace decision**
   - What we know: `requires:` is non-standard in Anthropic frontmatter spec.
   - What's unclear: Risk-aversion preference: short-and-clear (`requires:`) vs forward-compatible (`osbuilder-requires:`).
   - Recommendation: Short-and-clear. Document in `references/version-policy.md`. Migrate later if needed.
   - **RESOLVED:** `requires:` (short-and-clear). Documented as an OSBuilder-local convention in `references/version-policy.md` with migration note for the (low-risk) future case where Anthropic standardizes a conflicting `requires:` semantics (see 08-02 + references/version-policy.md).

6. **First-session marker location**
   - What we know: Two viable spots: `~/.osbuilder/last_check.txt` (per-user) vs `<project-root>/.planning/osbuilder/version_check.txt` (per-project).
   - What's unclear: Which best matches "first invocation each session."
   - Recommendation: Per-user (`~/.osbuilder/last_check.txt`); document the location.
   - **RESOLVED:** Per-user-global at `~/.osbuilder/last_check.txt`. Documented in `check_skill_versions.py` docstring + README troubleshooting section (`rm -f ~/.osbuilder/last_check.txt` to force a re-check) (see 08-04).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All Phase 8 helper scripts + CI workflow | ✓ | 3.13.13 | — |
| pytest | Phase 8 test additions | ✓ | ≥ 8.0 (per pyproject.toml) | — |
| gh CLI | Manual creation of public mirror repos for examples (optional) | ✓ | 2.90.0 (from Phase 6) | git push to remote already configured |
| asciinema | Recording demo as `.cast` (optional) | ✗ | — | Use OBS or QuickTime to record screen → ffmpeg convert to GIF |
| agg | Convert asciinema → GIF (optional) | ✗ | — | Use ffmpeg directly on screen recording, or LICEcap (macOS) |
| GitHub Actions runner | CI workflow | ✓ via GitHub | latest ubuntu-latest | — |
| Public GitHub repo | install.sh one-liner via curl | ✗ (no remote yet) | — | None — must publish before QUAL-02 verifiable |
| ffmpeg | Video format conversion (optional) | unknown — not checked | — | LICEcap, ScreenToGif (macOS/Linux/Windows alt) |

**Missing dependencies with no fallback:**
- Public GitHub repo URL — blocks QUAL-02 verification on a clean machine. Must be locked in discuss-phase.

**Missing dependencies with fallback:**
- asciinema/agg: if user picks GIF route, ffmpeg or LICEcap suffices.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -x` (default; -x stops on first failure per project convention) |
| Full suite command | `uv run pytest` |
| Slow tests (excluded by default) | `-m 'not slow'` (already in addopts) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUAL-01 | SKILL.md line count ≤ 200 (in-process) | unit | `uv run pytest scripts/tests/test_skill_md.py::test_skill_md_line_count_under_200 -x` | ✅ existing |
| QUAL-01 | check_skill_md_length.py exit code 0 when OK | unit | `uv run pytest scripts/tests/test_check_skill_md_length.py -x` | ❌ Wave 0 |
| QUAL-01 | check_skill_md_length.py exit code 1 when over limit | unit | `uv run pytest scripts/tests/test_check_skill_md_length.py::test_fails_over_limit -x` | ❌ Wave 0 |
| QUAL-01 | CI workflow yaml is valid + invokes the lint script | unit | `uv run pytest scripts/tests/test_ci_workflow.py -x` | ❌ Wave 0 |
| QUAL-02 | install.sh produces ~/.claude/skills/osbuilder/ on fresh HOME | integration | `uv run pytest scripts/tests/test_install.py -x` | ✅ existing (test_install_creates_four_dirs, test_install_idempotent, test_install_copies_artifacts) |
| QUAL-02 | install.sh remains POSIX-portable (no bashisms) | unit | `uv run pytest scripts/tests/test_install.py::test_install_is_posix -x` | ❌ Wave 0 (recommend new) |
| QUAL-02 | README contains the documented one-liner pattern | unit | `uv run pytest scripts/tests/test_readme.py::test_has_install_one_liner -x` | ❌ Wave 0 |
| QUAL-02 | One-liner end-to-end on a clean container | manual | UAT in `08-HUMAN-UAT.md` (cannot automate without remote URL locked) | ❌ Wave 0 (UAT row) |
| QUAL-03 | README has a dev-team metaphor section | unit | `uv run pytest scripts/tests/test_readme.py::test_has_dev_team_section -x` | ❌ Wave 0 |
| QUAL-03 | README references the demo asset (GIF or asciinema) | unit | `uv run pytest scripts/tests/test_readme.py::test_links_demo -x` | ❌ Wave 0 |
| QUAL-03 | Demo asset file exists in assets/demo/ | unit | `uv run pytest scripts/tests/test_readme.py::test_demo_asset_present -x` | ❌ Wave 0 |
| QUAL-04 | examples/ has ≥ 3 sub-directories (each with SPEC.md) | unit | `uv run pytest scripts/tests/test_examples.py::test_min_three -x` | ❌ Wave 0 |
| QUAL-04 | Each example covers a distinct playbook | unit | `uv run pytest scripts/tests/test_examples.py::test_distinct_playbooks -x` | ❌ Wave 0 |
| QUAL-04 | Each example has a screenshots/ dir + at least 1 image | unit | `uv run pytest scripts/tests/test_examples.py::test_has_screenshots -x` | ❌ Wave 0 |
| QUAL-04 | Each example has a repo-url.txt (or NOT_PUBLISHED placeholder) | unit | `uv run pytest scripts/tests/test_examples.py::test_has_repo_url -x` | ❌ Wave 0 |
| QUAL-05 | check_skill_versions.py exits 0 when all sub-skills meet minimums | unit | `uv run pytest scripts/tests/test_check_skill_versions.py::test_all_meet_minimum -x` | ❌ Wave 0 |
| QUAL-05 | check_skill_versions.py exits non-zero with friendly error when below minimum | unit | `uv run pytest scripts/tests/test_check_skill_versions.py::test_blocks_on_drift -x` | ❌ Wave 0 |
| QUAL-05 | Validator handles missing-version gracefully (warn, do not crash) | unit | `uv run pytest scripts/tests/test_check_skill_versions.py::test_warns_on_missing_version -x` | ❌ Wave 0 |
| QUAL-05 | First-invocation marker creation/check semantics | unit | `uv run pytest scripts/tests/test_check_skill_versions.py::test_first_session_marker -x` | ❌ Wave 0 |
| QUAL-05 | Validator wired into `/osbuilder` first-call entry path | integration | `uv run pytest scripts/tests/test_gsd_driver.py::test_version_check_runs_first -x` | ❌ Wave 0 |
| SC-6 | `--production-ready` flag emits 7 named-phase commands | unit | `uv run pytest scripts/tests/test_production_ready.py::test_emits_seven_phases -x` | ✅ existing (Phase 6) |
| SC-6 | Default mode (no flag) emits zero | unit | `uv run pytest scripts/tests/test_production_ready.py::test_no_emit_when_default -x` | ✅ existing (Phase 6) |
| SC-6 | README documents the flag and its 7 named phases | unit | `uv run pytest scripts/tests/test_readme.py::test_documents_production_ready -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -x` (project default; -x stops on first failure)
- **Per wave merge:** `uv run pytest` (full suite)
- **Phase gate:** Full suite green + `08-HUMAN-UAT.md` checklist signed off before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `scripts/check_skill_md_length.py` — covers QUAL-01 standalone (CI-callable)
- [ ] `scripts/check_skill_versions.py` — covers QUAL-05 (with stdlib semver, marker file)
- [ ] `.github/workflows/ci.yml` — covers QUAL-01 CI surface
- [ ] `README.md` — covers QUAL-02 (install one-liner doc), QUAL-03 (dev-team metaphor + demo)
- [ ] `examples/README.md` + `examples/<name>/SPEC.md` × 3-5 — covers QUAL-04
- [ ] `assets/demo/osbuilder-demo.gif` (+ `.cast` source) — covers QUAL-03 demo asset
- [ ] `references/version-policy.md` — explains custom `requires:` convention
- [ ] `scripts/tests/test_check_skill_md_length.py` — Wave 0 RED stubs (≥ 2)
- [ ] `scripts/tests/test_check_skill_versions.py` — Wave 0 RED stubs (≥ 4)
- [ ] `scripts/tests/test_ci_workflow.py` — Wave 0 RED stubs (≥ 2)
- [ ] `scripts/tests/test_readme.py` — Wave 0 RED stubs (≥ 5)
- [ ] `scripts/tests/test_examples.py` — Wave 0 RED stubs (≥ 4)
- [ ] SKILL.md frontmatter `requires:` block addition (5 sub-skill minimums)
- [ ] `08-HUMAN-UAT.md` — manual checklist for one-liner E2E + demo recording UAT

*(Existing test infrastructure covers SC-6 and pre-existing QUAL-01 in-process check; new scripts above are net-new.)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface in Phase 8 — all artifacts are static doc/CI/scripts. |
| V3 Session Management | partial | "First-session marker" file (~/.osbuilder/last_check.txt) is technically session state but not security-bearing — used for run-throttling, not access control. |
| V4 Access Control | no | Read-only validators; no privilege escalation paths. |
| V5 Input Validation | yes | check_skill_versions.py reads YAML frontmatter — must reject malformed/over-long values; check_skill_md_length.py reads SKILL.md. Existing pattern from `state_writer.py:_check_value_safe`. |
| V6 Cryptography | no | No crypto in Phase 8. |
| V8 Data Protection | partial | install.sh one-liner (curl-pipe-shell) is a known security concern for some users — document the audited-install alternative (clone-then-run). Do not include any auth tokens / secrets in the install.sh body. [VERIFIED: install.sh has zero secrets — read 79 lines on 2026-05-02] |
| V12 Files and Resources | yes | Marker file at ~/.osbuilder/last_check.txt + traversal guards. Reuse `_resolve_project_root` traversal-rejection pattern. |
| V14 Configuration | yes | CI workflow config (.github/workflows/ci.yml) — must pin action versions to exact major (`@v6`), not `@latest`. |

### Known Threat Patterns for Phase 8

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `curl … \| sh` accepts any redirect/MITM into shell execution | Tampering | Use `https://` only; recommend pinning to a tagged release URL in README (`/v1.0.0/install.sh` not `/main/install.sh`) once tagging is in place. |
| Demo video accidentally records `gh auth token` or `.env` contents | Information Disclosure | Pre-record checklist: clear shell history, redact env, use throwaway gh login, screen-grab post-review checklist before publish. |
| Examples gallery commits `.env`, secrets, or auth tokens from real builds | Information Disclosure | Each example SPEC.md is hand-curated; screenshots reviewed; gitleaks pre-commit hook (already shipped from Phase 6) catches obvious leaks. |
| YAML frontmatter parser eats `>>` redirect chars or path-traversal tokens | Tampering / Injection | Hand-rolled parser already in test_skill_md.py rejects ad-hoc fields; validator extends it with explicit type/length checks per state_writer's V5/V12 pattern. |
| `requires:` block contains version string with shell metacharacters | Tampering | Restrict version values to `[0-9.]{1,16}` in the validator; reject anything else with friendly error. |
| CI workflow uses `@latest` action tags, allowing supply-chain drift | Supply chain | Pin to exact major (`@v6`); document upgrade cadence in `references/version-policy.md`. |
| Marker file at ~/.osbuilder/last_check.txt could be poisoned by another process | Tampering | Marker presence is informational only — validator re-runs on absence; cannot be tricked into skipping a check (presence only blocks re-runs, never blocks runs). |

---

## Sources

### Primary (HIGH confidence)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/SKILL.md` — current 130 lines, frontmatter without `requires:` block
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/install.sh` — current 79 lines, POSIX-portable, idempotent, repo-local-only
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/scripts/state_writer.py` — ALLOWED_FIELDS pattern, _check_value_safe pattern, _resolve_project_root pattern
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/scripts/production_phase_writer.py` — already implements `--production-ready` (137 lines, Phase 6 — confirms SC-6 is verification-only)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/scripts/tests/test_skill_md.py` — _read_frontmatter pattern (verified hand-roller)
- `/Users/charlie/Documents/Work & Projects/VSCode Projects/OSBuilder/assets/ci-workflows/python.yml.tmpl` — verified pattern for setup-python@v6 + setup-uv@v6
- `/Users/charlie/.claude/skills/{gsd,brainiac,predator,code-tester,problem-solver}/SKILL.md` — direct read confirms gsd & predator have no `version:`, others do (6.0.0, 3.1.0, 3.0.0)
- `code.claude.com/docs/en/skills` — Anthropic skills overview, frontmatter schema
- `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices` — Best practices, optional-fields rule

### Secondary (MEDIUM confidence)
- `docs.asciinema.org/getting-started/` + `docs.asciinema.org/manual/agg/` — asciinema vs GIF tradeoff, agg = asciicast2gif successor
- `thelinuxcode.com/how-to-embed-a-video-into-a-github-readmemd-practical-2026-playbook/` — GitHub README video-embed limitations 2026
- `cesarsotovalero.net/blog/enhance-your-readme-with-asciinema.html` — asciinema script-tag stripping in GitHub READMEs
- `github.com/anthropics/skills` — public skill examples, frontmatter conventions in the wild
- `docs.astral.sh/uv/guides/integration/github/` — uv + GitHub Actions integration patterns

### Tertiary (LOW confidence — flagged for validation)
- `aipractitioner.substack.com/p/building-claude-skills-a-new-paradigm` — only one source mentioning `requires:`-style fields; treated as confirmation-of-absence not confirmation-of-existence

---

## Metadata

**Confidence breakdown:**
- Standard stack (Python stdlib, GitHub Actions, pytest): HIGH — verified against existing OSBuilder code and live actions
- Architecture (script-with-CLI pattern, frontmatter parser, semver tuple): HIGH — direct extension of existing OSBuilder patterns
- Pitfalls (missing version field, public-repo-not-yet, marker file collisions): HIGH — verified by direct file reads + grep
- `requires:` convention as Anthropic-future-proof: MEDIUM — `requires:` is custom; future Anthropic spec changes are unknowable
- Examples gallery candidate selection: LOW — depends on Phase 6/7 completion state and what apps OSBuilder has actually built (currently nothing in `examples/`)
- Demo video format/length recommendations: MEDIUM — best practice in 2026 favors GIF + asciinema, but exact 60-second script is project-call

**Research date:** 2026-05-02
**Valid until:** 2026-06-02 (30 days; CI action versions move slowly; sub-skill versions could change faster — re-verify gsd & predator if Phase 8 stretches >2 weeks).
