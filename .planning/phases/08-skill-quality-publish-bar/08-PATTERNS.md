# Phase 8: Skill quality / publish-bar - Pattern Map

**Mapped:** 2026-05-02
**Files analyzed:** 17 (8 new scripts/tests, 1 modify SKILL.md, 1 modify+create README.md, 1 examples/README.md, 3-5 example sub-directories, 1 references/version-policy.md, 2 demo assets, 1 CI workflow, 1 HUMAN-UAT.md)
**Analogs found:** 16 / 17 (the 60-second demo asset is a binary GIF/asciinema recording with no codebase analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/check_skill_md_length.py` | utility (CLI lint script) | file-I/O → exit-code | `scripts/registry_verify.py` | exact (CLI gate, stdlib-only, friendly stderr, exit 0/1) |
| `scripts/check_skill_versions.py` | utility (CLI validator + frontmatter parser + state-marker) | file-I/O → exit-code + side-effecting marker | `scripts/production_phase_writer.py` (subcommand structure + project-root resolution) + `scripts/tests/test_skill_md.py:_read_frontmatter` (parser) | role-match (composite — combines two existing patterns) |
| `scripts/tests/test_check_skill_md_length.py` | test (unit, subprocess + module) | request-response | `scripts/tests/test_registry_verify.py` (lazy module import + monkeypatch) + `scripts/tests/test_production_ready.py` (subprocess invocation) | exact |
| `scripts/tests/test_check_skill_versions.py` | test (unit + integration: marker + frontmatter + semver) | request-response | `scripts/tests/test_registry_verify.py` (HTTP-style fail-open patterns translated to file-system fail-open) + `scripts/tests/test_production_ready.py` (subprocess + fixture) | role-match |
| `scripts/tests/test_ci_workflow.py` | test (unit, file-existence + YAML grep) | file-I/O | `scripts/tests/test_skill_md.py` (file-read + regex assertion) | role-match |
| `scripts/tests/test_readme.py` | test (unit, file-existence + multi-section grep) | file-I/O | `scripts/tests/test_skill_md.py` (text-content assertions on a single markdown file) | exact |
| `scripts/tests/test_examples.py` | test (unit, directory-walk + per-subdir invariants) | file-I/O | `scripts/tests/test_install.py::test_install_no_nested_dirs` (Path.rglob + structural invariant) | role-match |
| `.github/workflows/ci.yml` | config (CI pipeline) | event-driven (PR/push trigger) | `assets/ci-workflows/python.yml.tmpl` | exact (literal template — copy + add lint job) |
| `README.md` (NEW at repo root) | documentation | static-content | `assets/readme-template.md` (clone-and-run runbook structure) + `SKILL.md` (current frontmatter + dev-team table) | role-match |
| `examples/README.md` | documentation (gallery index) | static-content | `references/playbooks/web.md` table-of-contents pattern + `references/markers.md` (registry table style) | role-match |
| `examples/<name>/SPEC.md` × 3-5 | documentation (per-app brief) | static-content | `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` (per-test row structure) + `references/playbooks/*.md` | role-match |
| `examples/<name>/screenshots/` | asset directory (binaries) | static-content | `assets/ci-workflows/` (directory-of-template-files pattern) | partial — analog provides "directory of artifacts" precedent only |
| `examples/<name>/repo-url.txt` | data file (one-line URL or NOT_PUBLISHED placeholder) | static-content | none in repo (smallest analog: `.gitkeep` markers across `examples/`, `scripts/`, `assets/`) | no-analog |
| `assets/demo/osbuilder-demo.gif` | asset (binary) | static-content | none — first binary asset in repo | no-analog |
| `assets/demo/osbuilder-demo.cast` | asset (asciinema source) | static-content | none — first asciinema asset in repo | no-analog |
| `references/version-policy.md` | documentation (policy reference) | static-content | `references/refuse-list.md` (policy doc that scripts read at runtime) + `references/markers.md` (maintainer reference, NOT runtime-loaded) | exact |
| `SKILL.md` (modify — add `requires:` block) | documentation (frontmatter) | static-content | current `SKILL.md` lines 1-8 (frontmatter shape) | exact (in-place edit) |
| `08-HUMAN-UAT.md` | documentation (manual test checklist) | static-content | `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` | exact |

---

## Pattern Assignments

### `scripts/check_skill_md_length.py` (utility, CLI lint script)

**Analog:** `scripts/registry_verify.py` (CLI gate exit-code semantics) + `scripts/production_phase_writer.py` (REPO_ROOT pattern + friendly stderr)

**Imports + module header pattern** (registry_verify.py lines 1-19):
```python
#!/usr/bin/env python3
"""check_skill_md_length.py — fail CI if SKILL.md exceeds 200 lines.

Pure stdlib — no third-party deps.

Exit codes:
  0 = SKILL.md is at or under the line limit
  1 = SKILL.md exceeds the line limit (BLOCK PR)
  2 = SKILL.md not found (defensive — should not happen in CI)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
```

**REPO_ROOT anchor + module-level constants pattern** (production_phase_writer.py lines 18-30):
```python
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"
LIMIT = 200
```

**Friendly-error stderr pattern** (registry_verify.py lines 92-97):
```python
sys.stderr.write(
    f"OSBuilder: SKILL.md is {lines} lines, limit is {limit}. "
    f"Move detail to references/ via progressive disclosure.\n"
)
return 1
```

**CLI main() pattern** (registry_verify.py lines 73-98 — single-purpose CLI, no subcommands):
```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="check_skill_md_length",
        description="OSBuilder SKILL.md line-count CI gate (QUAL-01).",
    )
    parser.add_argument("--skill-md", default=str(SKILL_MD))
    parser.add_argument("--limit", type=int, default=LIMIT)
    args = parser.parse_args(argv)
    return check(Path(args.skill_md), args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
```

---

### `scripts/check_skill_versions.py` (utility, validator + frontmatter parser + marker)

**Analog:** Composite pattern combining:
- `scripts/production_phase_writer.py` for subcommand + project-root + state I/O
- `scripts/tests/test_skill_md.py:_read_frontmatter` for hand-rolled YAML parsing
- RESEARCH.md `parse_version` example for stdlib semver

**Imports + REPO_ROOT pattern** (production_phase_writer.py lines 10-19, register_verify.py lines 14-19):
```python
#!/usr/bin/env python3
"""check_skill_versions.py — first-session sub-skill version-drift validator (QUAL-05).

Reads `requires:` block from OSBuilder's SKILL.md frontmatter; for each declared
sub-skill, reads its installed `version:` from ~/.claude/skills/<name>/SKILL.md;
compares semver via stdlib tuple comparison; emits friendly upgrade command if drift.

Marker file at ~/.osbuilder/last_check.txt throttles re-runs to once per session.

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"
SKILLS_DIR = Path(os.path.expanduser("~/.claude/skills"))
MARKER = Path(os.path.expanduser("~/.osbuilder/last_check.txt"))
```

**Frontmatter parser pattern** (test_skill_md.py:_read_frontmatter lines 15-40 — extend with nested-key support per RESEARCH.md Pattern 3):
```python
def _read_frontmatter(path: Path) -> dict:
    """Read SKILL.md frontmatter as dict; supports indented sub-keys under `requires:`.
    
    Hand-rolled — no PyYAML dep. Returns {} if no frontmatter found.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields: dict = {}
    current_key = None
    nested: dict | None = None
    for line in m.group(1).splitlines():
        # Indented sub-key under `requires:` block
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
                nested = fields[key]
            else:
                fields[key] = value
                current_key = key
    return fields
```

**Stdlib semver pattern** (RESEARCH.md Code Examples — hand-rolled per project's no-third-party rule):
```python
_VERSION_RE = re.compile(r"^[0-9.]{1,16}$")


def parse_version(s: str) -> tuple[int, ...]:
    """Parse 'MAJOR.MINOR.PATCH' → (major, minor, patch). Pre-releases not supported."""
    if not s:
        return (0, 0, 0)
    s = s.strip().lstrip("v")
    if not _VERSION_RE.match(s):
        return (0, 0, 0)  # malformed = "older than anything" — fail-safe (V5 input validation)
    parts = s.split(".")
    try:
        return tuple(int(p) for p in parts[:3]) + (0,) * (3 - len(parts))
    except ValueError:
        return (0, 0, 0)
```

**Marker file pattern** (RESEARCH.md Code Examples; conventions match `tmp_install_log` fixture in conftest.py lines 96-107 which uses `~/.osbuilder/`):
```python
def is_first_session() -> bool:
    return not MARKER.exists()


def record_check_complete() -> None:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text("ok\n", encoding="utf-8")
```

**Subcommand + main() pattern** (production_phase_writer.py lines 109-137):
```python
def _cmd_check(args: argparse.Namespace) -> int:
    if args.force or is_first_session():
        rc = check_versions()
        if rc == 0:
            record_check_complete()
        return rc
    return 0  # already checked this session


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="check_skill_versions",
        description="OSBuilder sub-skill version-drift validator (QUAL-05).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="Run drift check (skips if marker present unless --force).")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"OSBuilder: error — {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

**Friendly-error message pattern for missing-version warn** (per Pitfall 2 + friendly_error.py FriendlyMessage shape):
```python
# Two-mode reporting: BLOCK if version is below minimum, WARN if version field is missing
sys.stderr.write(
    f"OSBuilder: ⚠️  {sub_skill} has no version field — cannot enforce minimum {minimum}. "
    f"Proceeding anyway. (Reported in non-blocking mode.)\n"
)
# vs.
sys.stderr.write(
    f"OSBuilder: {sub_skill} {installed} is below required {minimum}. "
    f"Run: cd ~/.claude/skills/{sub_skill} && git pull\n"
)
return 1
```

---

### `scripts/tests/test_check_skill_md_length.py` (test, unit + subprocess)

**Analog:** `scripts/tests/test_registry_verify.py` (lazy module import + monkeypatch) + `scripts/tests/test_production_ready.py` (subprocess invocation pattern)

**Lazy module import fixture** (test_registry_verify.py lines 13-19):
```python
@pytest.fixture
def csml():
    """Lazy import of scripts/check_skill_md_length.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("check_skill_md_length")
    except ImportError:
        pytest.skip("check_skill_md_length module not yet created (Wave 1 target)")
```

**Subprocess invocation pattern** (test_production_ready.py lines 36-44):
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
CHECK_SKILL_MD = REPO_ROOT / "scripts" / "check_skill_md_length.py"


def test_passes_under_limit(csml, tmp_path):
    """QUAL-01: returns 0 when SKILL.md is at or under the limit."""
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 100), encoding="utf-8")
    assert csml.check(fake, limit=200) == 0


def test_fails_over_limit(csml, tmp_path):
    """QUAL-01: returns 1 when SKILL.md exceeds the limit."""
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 250), encoding="utf-8")
    assert csml.check(fake, limit=200) == 1


def test_cli_subprocess_exit_code(tmp_path):
    """QUAL-01: invoked as a subprocess, returns non-zero on over-limit (CI surface)."""
    fake = tmp_path / "SKILL.md"
    fake.write_text("\n".join(["line"] * 250), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(CHECK_SKILL_MD), "--skill-md", str(fake), "--limit", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "SKILL.md is 250 lines" in result.stderr
```

---

### `scripts/tests/test_check_skill_versions.py` (test, unit + integration)

**Analog:** `scripts/tests/test_registry_verify.py` (multi-mode behavior tests with monkeypatch) + `scripts/tests/test_production_ready.py` (fixture-driven state seeding)

**Lazy import + four-mode test split** (mirror test_registry_verify.py's "blocked / passes / fail-open" trio, extend to four modes per RESEARCH Validation Architecture rows for QUAL-05):
```python
@pytest.fixture
def csv_module():
    """Lazy import of scripts/check_skill_versions.py — skips when not yet created."""
    try:
        return importlib.import_module("check_skill_versions")
    except ImportError:
        pytest.skip("check_skill_versions module not yet created (Wave 1 target)")


@pytest.fixture
def fake_skills_dir(tmp_path, monkeypatch):
    """Fake ~/.claude/skills/ tree — each sub-skill gets a SKILL.md with a controllable version."""
    fake = tmp_path / "skills"
    fake.mkdir()
    monkeypatch.setattr("check_skill_versions.SKILLS_DIR", fake)
    
    def _seed(name: str, version: str | None):
        skill = fake / name
        skill.mkdir()
        if version is None:
            (skill / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        else:
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\nversion: {version}\n---\n", encoding="utf-8"
            )
    return _seed


def test_all_meet_minimum(csv_module, fake_skills_dir, tmp_path, monkeypatch):
    """QUAL-05: returns 0 when all sub-skills meet declared minimums."""
    # ... seed fake SKILL.md with `requires:` block + sub-skills with sufficient versions

def test_blocks_on_drift(csv_module, fake_skills_dir, ...):
    """QUAL-05: returns 1 with friendly upgrade command when below minimum."""

def test_warns_on_missing_version(csv_module, fake_skills_dir, ...):
    """Pitfall 2: missing `version:` field → exit 0 + warn to stderr (non-blocking)."""

def test_first_session_marker(csv_module, monkeypatch, tmp_path):
    """QUAL-05: marker file presence skips the check on subsequent invocations."""
```

---

### `scripts/tests/test_ci_workflow.py` (test, file-existence + YAML grep)

**Analog:** `scripts/tests/test_skill_md.py` (text-content assertions) + `scripts/tests/test_install.py` (REPO_ROOT path anchoring)

**REPO_ROOT anchor + file-existence guard** (test_install.py lines 12-13 + test_skill_md.py lines 7-12):
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created (Phase 8 target)")
    assert CI_YML.is_file()


def test_pins_action_versions():
    """Security V14: pin to exact major (`@v6`), not `@latest`."""
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created")
    text = CI_YML.read_text(encoding="utf-8")
    assert "@latest" not in text, "CI workflow must pin actions to exact major version"
    assert "actions/checkout@v6" in text
    assert "actions/setup-python@v6" in text


def test_invokes_lint_script():
    """QUAL-01: CI invokes scripts/check_skill_md_length.py."""
    if not CI_YML.exists():
        pytest.skip(".github/workflows/ci.yml not yet created")
    text = CI_YML.read_text(encoding="utf-8")
    assert "scripts/check_skill_md_length.py" in text
```

---

### `scripts/tests/test_readme.py` (test, multi-section grep)

**Analog:** `scripts/tests/test_skill_md.py` (regex-on-markdown-body pattern, lines 60-74)

**Pattern (extend test_skill_md.py for README's 5 required sections):**
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


def _readme_text() -> str:
    if not README.exists():
        pytest.skip("README.md not yet created (Phase 8 target)")
    return README.read_text(encoding="utf-8")


def test_has_install_one_liner():
    """QUAL-02: README documents the curl-pipe-shell install one-liner."""
    text = _readme_text()
    assert re.search(r"curl -fsSL.*install\.sh.*\| sh", text), \
        "README must contain the documented one-liner install command"


def test_has_dev_team_section():
    """QUAL-03: README explains the dev-team metaphor (PM/Architect/.../Tech Writer)."""
    text = _readme_text().lower()
    for role in ("pm", "architect", "frontend", "backend", "devops", "qa", "reviewer", "tech writer"):
        assert role in text, f"README must mention dev-team role '{role}'"


def test_links_demo():
    """QUAL-03: README references the 60s demo asset."""
    text = _readme_text()
    assert re.search(r"assets/demo/osbuilder-demo\.(gif|cast)", text)


def test_demo_asset_present():
    """QUAL-03: at least one of GIF/asciinema-cast assets exists in assets/demo/."""
    demo_dir = REPO_ROOT / "assets" / "demo"
    assets = list(demo_dir.glob("osbuilder-demo.*")) if demo_dir.exists() else []
    assert assets, "assets/demo/osbuilder-demo.{gif,cast} must exist"


def test_documents_production_ready():
    """SC-6: README documents --production-ready flag and 7 named upgrades."""
    text = _readme_text().lower()
    assert "--production-ready" in text
    for name in ("observability", "migrations", "healthchecks", "secret-manager",
                 "sentry", "rate-limiting", "backups"):
        assert name in text, f"README must document --production-ready upgrade '{name}'"
```

---

### `scripts/tests/test_examples.py` (test, directory-walk)

**Analog:** `scripts/tests/test_install.py::test_install_no_nested_dirs` (Path.rglob structural walk, lines 75-87)

**Pattern (per-subdir invariants via Path iteration):**
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples"

# Locked playbook list — must match infer_app_type's 5-way enum
EXPECTED_PLAYBOOKS = ("web", "ai-service", "cli", "desktop", "hub-platform")


def _example_dirs() -> list[Path]:
    if not EXAMPLES.exists():
        pytest.skip("examples/ not yet populated (Phase 8 target)")
    return [p for p in EXAMPLES.iterdir() if p.is_dir() and not p.name.startswith(".")]


def test_min_three():
    """QUAL-04: examples/ has ≥ 3 sub-directories."""
    assert len(_example_dirs()) >= 3


def test_each_has_spec():
    """QUAL-04: every example sub-dir has a SPEC.md."""
    for d in _example_dirs():
        assert (d / "SPEC.md").is_file(), f"{d.name}/SPEC.md missing"


def test_distinct_playbooks():
    """Pitfall 5: examples cover distinct playbooks (no 5-TODOs filler)."""
    playbooks = []
    for d in _example_dirs():
        spec = (d / "SPEC.md").read_text(encoding="utf-8").lower()
        for pb in EXPECTED_PLAYBOOKS:
            if pb in spec:
                playbooks.append(pb)
                break
    assert len(set(playbooks)) >= 3, f"examples must use ≥ 3 distinct playbooks; got {playbooks}"


def test_has_screenshots():
    """QUAL-04: each example has a screenshots/ dir + at least 1 image."""
    for d in _example_dirs():
        screenshots = d / "screenshots"
        if not screenshots.exists():
            continue  # allow opt-out for NOT_PUBLISHED examples
        images = [p for p in screenshots.iterdir()
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
        assert images, f"{d.name}/screenshots/ has no PNG/JPG"


def test_has_repo_url():
    """QUAL-04: each example has a repo-url.txt (real URL or NOT_PUBLISHED placeholder)."""
    for d in _example_dirs():
        url_file = d / "repo-url.txt"
        assert url_file.exists(), f"{d.name}/repo-url.txt missing"
        content = url_file.read_text(encoding="utf-8").strip()
        assert content, f"{d.name}/repo-url.txt is empty"
        # Either a real URL or the documented placeholder
        assert content.startswith("https://github.com/") or content == "NOT_PUBLISHED"
```

---

### `.github/workflows/ci.yml` (config, GitHub Actions)

**Analog:** `assets/ci-workflows/python.yml.tmpl` — verbatim template, copy and extend

**Source template (assets/ci-workflows/python.yml.tmpl, full file 23 lines):**
```yaml
# OSBuilder default — Python + uv CI workflow (SCL-04)
# Source: actions/setup-python + astral-sh/setup-uv (verified 2026-05-01)
name: Test on PR

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'

      - uses: astral-sh/setup-uv@v6

      - run: uv sync --frozen
      - run: uv run pytest
```

**Extension for Phase 8 (add a lint-skill-md job + push trigger per RESEARCH Pattern 2):**
```yaml
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
      - run: uv sync --frozen
      - run: uv run pytest
```

---

### `README.md` (NEW at repo root) (documentation)

**Analog:** `assets/readme-template.md` (clone-and-run runbook structure) + `SKILL.md` lines 17-30 (dev-team table)

**Quick-start section pattern** (assets/readme-template.md lines 5-23):
```markdown
# OSBuilder

> Build end-to-end apps from a plain-English description. PM → Architect →
> Frontend → Backend → DevOps → QA → Reviewer → Tech Writer, all running
> sequentially over your existing Claude Code skill ecosystem.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/osbuilder/main/install.sh | sh
```

(Audited install — for security-conscious users:)

```bash
git clone https://github.com/<owner>/osbuilder ~/osbuilder-src
cd ~/osbuilder-src && ./install.sh
```
```

**Dev-team metaphor section pattern** (SKILL.md lines 17-30 — copy table verbatim then expand each role with a one-line plain-English narration):
```markdown
## How OSBuilder Works (the dev-team metaphor)

OSBuilder narrates progress as a virtual studio. Each "role" is a sequential
delegation to your existing skill ecosystem — never parallel, never multi-agent.

| Role | What you'll see in the terminal | Delegates to |
|------|----------------------------------|--------------|
| **PM** | "PM is gathering requirements... ✓" | `/gsd-spec-phase` |
| **Architect** | "Architect chose Next.js because…" | `/brainiac` + `/gsd-plan-phase` |
| **Frontend** | "Frontend dev is building the homepage…" | `/gsd-execute-phase` |
| **Backend** | "Backend dev is wiring the database…" | `/gsd-execute-phase` |
| **DevOps** | "DevOps is setting up Docker Compose…" | `/gsd-execute-phase` |
| **QA** | "QA is running adversarial tests…" | `/code-tester` + `/gsd-verify-work` |
| **Reviewer** | "Reviewer is checking architecture…" | `/predator` + `/gsd-code-review` |
| **Tech Writer** | "Tech Writer is humanizing the README…" | `/gsd-docs-update` + `/humanizer` |

## 60-Second Demo

![OSBuilder demo — paragraph to private GitHub repo](assets/demo/osbuilder-demo.gif)

[Higher-quality version on asciinema](assets/demo/osbuilder-demo.cast)
```

**`--production-ready` flag documentation pattern** (SKILL.md lines 41-49 modes table — extend to a list of named upgrades for SC-6):
```markdown
## --production-ready

Adds these as **named ROADMAP phases** (not default scaffold code):

- `observability` — logs/metrics/traces via OpenTelemetry
- `migrations` — automated migrations via Drizzle Kit / Alembic
- `healthchecks` — `/healthz` endpoints
- `secret-manager` — secret manager integration
- `sentry` — Sentry error tracking
- `rate-limiting` — rate limiting middleware
- `backups` — backup strategy
```

---

### `examples/README.md` (documentation, gallery index)

**Analog:** `references/markers.md` (registry-table style, lines 21-26) + `references/refuse-list.md` (intro + table layout, lines 1-30)

**Pattern (table-of-contents per sub-dir):**
```markdown
# OSBuilder Examples Gallery

Real apps OSBuilder built end-to-end from a plain-English paragraph. Each
example shows the original spec, before/after screenshots, and the GitHub
URL of the resulting (private or public-mirror) repo.

> **Pitfall 5 guard:** every example uses a different playbook to demonstrate
> OSBuilder's range. We refuse "5 TODO-list variants" filler.

| Example | Playbook | Spec | Repo |
|---------|----------|------|------|
| 01-todo-web | web | [SPEC.md](01-todo-web/SPEC.md) | [repo](01-todo-web/repo-url.txt) |
| 02-cli-photo-organizer | cli | [SPEC.md](02-cli-photo-organizer/SPEC.md) | [repo](02-cli-photo-organizer/repo-url.txt) |
| 03-fastapi-summarizer | ai-service | [SPEC.md](03-fastapi-summarizer/SPEC.md) | [repo](03-fastapi-summarizer/repo-url.txt) |

## Adding a new example

1. Run OSBuilder against a paragraph describing the new app.
2. Copy the resulting derived_spec.md → `examples/NN-slug/SPEC.md`.
3. Capture 2-3 screenshots → `examples/NN-slug/screenshots/`.
4. Write the resulting repo URL into `examples/NN-slug/repo-url.txt` (or
   `NOT_PUBLISHED` if private and no public mirror).
5. Add a row to the table above.
```

---

### `examples/<name>/SPEC.md` × 3-5 (documentation, per-app brief)

**Analog:** `references/playbooks/web.md` structure (intake brief + before/after) + 07-HUMAN-UAT.md per-test row

**Pattern (per-app SPEC):**
```markdown
# Example: <App name>

**Playbook:** web | ai-service | cli | desktop | hub-platform
**Built:** YYYY-MM-DD
**Repo:** [repo-url.txt](repo-url.txt)

## Original paragraph (intake)

> "<verbatim user paragraph>"

## OSBuilder's interpretation

- **App type:** <inferred>
- **Stack:** <library list with versions>
- **Notable refusals:** <if any — e.g., "user mentioned Electron; OSBuilder routed to Tauri 2">

## Before / After

| Stage | What it looked like |
|-------|---------------------|
| Intake (paragraph) | (text) |
| Derived spec | screenshots/derived-spec.png |
| Scaffolded project | screenshots/scaffold-tree.png |
| Working app | screenshots/running.png |
| Private GitHub | screenshots/repo-view.png |

## How OSBuilder built this

1. PM gathered requirements (1 clarifying question).
2. Architect chose <stack> because <rationale>.
3. ...
```

---

### `references/version-policy.md` (documentation, policy reference)

**Analog:** `references/refuse-list.md` (policy doc that scripts read at runtime, lines 1-40) + `references/markers.md` (maintainer reference NOT runtime-loaded, lines 1-46)

**Pattern (header + cross-reference + policy section):**
```markdown
# OSBuilder Version Policy (`requires:` convention)

> Cross-referenced by `scripts/check_skill_versions.py:check_versions`. The
> `requires:` block in OSBuilder's SKILL.md frontmatter is the source of truth
> for sub-skill minimum versions.
>
> **NOT a standard Anthropic frontmatter field** (verified 2026-05-02 against
> `code.claude.com/docs/en/skills` and `platform.claude.com/.../best-practices`).
> This is an OSBuilder-local convention; future Anthropic spec changes are
> tracked in Pitfall 7 of `.planning/phases/08-skill-quality-publish-bar/08-RESEARCH.md`.

## Format

In SKILL.md frontmatter:

```yaml
requires:
  gsd: 1.0.0
  brainiac: 6.0.0
  predator: 1.0.0
  code-tester: 3.1.0
  problem-solver: 3.0.0
```

## Behavior on first invocation

`scripts/check_skill_versions.py` runs once per session (gated by
`~/.osbuilder/last_check.txt` marker). For each sub-skill listed:

| Installed state | Behavior |
|-----------------|----------|
| Version meets/exceeds minimum | Pass silently. |
| Version below minimum | **Block** with friendly upgrade command. Exit 1. |
| `version:` field absent (gsd, predator as of 2026-05-02) | **Warn** but proceed. Exit 0. |
| Sub-skill not installed | **Block** with install command. Exit 1. |

## See also

- `scripts/check_skill_versions.py` — implementation
- `~/.claude/skills/{gsd,brainiac,predator,code-tester,problem-solver}/SKILL.md` — installed versions
- `.planning/phases/08-skill-quality-publish-bar/08-RESEARCH.md` Pitfall 7 — Anthropic-future-proofing
```

---

### `SKILL.md` (modify — add `requires:` block to frontmatter)

**Analog:** current SKILL.md lines 1-8 (frontmatter shape — DO NOT touch other fields)

**Current frontmatter (SKILL.md lines 1-8):**
```yaml
---
name: osbuilder
description: >
  Builds end-to-end applications from a plain-English description. ...
allowed-tools: Read, Write, Edit, Bash, Agent, Glob, Grep, WebSearch, WebFetch
user-invocable: true
argument-hint: "[brief or @path/to/spec.md or 'build like ./reference-app']"
---
```

**Modification — add `requires:` block before closing `---` (Pitfall 1: SKILL.md is currently 130 lines, must stay ≤ 200 after this edit):**
```yaml
---
name: osbuilder
description: >
  Builds end-to-end applications from a plain-English description. ...
allowed-tools: Read, Write, Edit, Bash, Agent, Glob, Grep, WebSearch, WebFetch
user-invocable: true
argument-hint: "[brief or @path/to/spec.md or 'build like ./reference-app']"
requires:
  gsd: 1.0.0
  brainiac: 6.0.0
  predator: 1.0.0
  code-tester: 3.1.0
  problem-solver: 3.0.0
---
```

**Constraint:** zero changes to SKILL.md body. The `requires:` policy explanation lives in `references/version-policy.md` (Pitfall 1 mitigation).

---

### `08-HUMAN-UAT.md` (documentation, manual checklist)

**Analog:** `.planning/phases/07-additional-playbooks/07-HUMAN-UAT.md` (verbatim structure)

**Front-matter pattern** (07-HUMAN-UAT.md lines 1-7):
```markdown
---
status: pending
phase: 08-skill-quality-publish-bar
source: [08-VERIFICATION.md]
started:
updated:
---

## Current Test

[pending — runner has not started]

## Tests

### 1. Install one-liner end-to-end on a fresh container
expected: `curl -fsSL <repo-url>/install.sh | sh` on a clean Docker `ubuntu:latest` lands `~/.claude/skills/osbuilder/SKILL.md`.
test: `docker run --rm -it ubuntu:latest bash -c 'apt-get update && apt-get install -y curl python3 && curl -fsSL https://raw.githubusercontent.com/<owner>/osbuilder/main/install.sh | sh && cat ~/.claude/skills/osbuilder/SKILL.md | head -5'`
why_human: Requires public-repo URL (Pitfall 4) + container with no Claude Code skill prior. Cannot automate without a published remote.
result: <pending>

### 2. 60-second demo records an unedited end-to-end build
expected: Demo shows paragraph → derived_spec → scaffold → verify → private GitHub URL with no cuts hiding friction (Pitfall 6).
test: Record an end-to-end run with asciinema; play back; review.
why_human: Subjective UX honesty check.
result: <pending>

[... etc, one row per QUAL-XX requirement that has a manual gate ...]
```

---

## Shared Patterns

### Pure-stdlib + REPO_ROOT anchor (all new scripts)
**Source:** `scripts/production_phase_writer.py` lines 14-19 + `scripts/registry_verify.py` lines 14-19
**Apply to:** `scripts/check_skill_md_length.py`, `scripts/check_skill_versions.py`
```python
#!/usr/bin/env python3
"""<module> — <one-line summary>.

<one paragraph describing what + why>.

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
```

### Friendly stderr error format (all CLI scripts)
**Source:** `scripts/registry_verify.py` lines 92-97 + `scripts/production_phase_writer.py` line 132
**Apply to:** every script's user-facing error path
```python
sys.stderr.write(f"OSBuilder: <plain-English what broke>. <plain-English what to do>.\n")
return 1
```

### Lazy module-import test fixture (all new test files)
**Source:** `scripts/tests/test_registry_verify.py` lines 13-19 (mirrored in test_production_ready.py lines 22-27)
**Apply to:** `test_check_skill_md_length.py`, `test_check_skill_versions.py`, `test_ci_workflow.py`, `test_readme.py`, `test_examples.py`
```python
@pytest.fixture
def <module>():
    """Lazy import of scripts/<module>.py — skips when not yet created (Wave 1 target)."""
    try:
        return importlib.import_module("<module>")
    except ImportError:
        pytest.skip("<module> not yet created (Wave 1 target)")
```

### REPO_ROOT in tests (all new test files)
**Source:** `scripts/tests/test_skill_md.py` line 7 + `scripts/tests/test_install.py` line 12
**Apply to:** every new test file
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
```

### File-not-yet-created skip guard (file-existence tests)
**Source:** `scripts/tests/test_skill_md.py` lines 16-17, 60-63, 71-72
**Apply to:** `test_ci_workflow.py`, `test_readme.py`, `test_examples.py`
```python
if not <PATH>.exists():
    pytest.skip("<file> not yet created (Phase 8 target)")
```

### Subprocess CLI invocation in tests
**Source:** `scripts/tests/test_production_ready.py` lines 36-44
**Apply to:** `test_check_skill_md_length.py`, `test_check_skill_versions.py` for end-to-end exit-code verification
```python
result = subprocess.run(
    [sys.executable, str(SCRIPT), "<subcmd>", "--<arg>", "<value>"],
    capture_output=True, text=True,
)
assert result.returncode == <expected>
```

### Path-traversal + V5 input validation (any user-supplied paths)
**Source:** `scripts/state_writer.py:_check_value_safe` lines 72-77 + `scripts/production_phase_writer.py:_resolve_project_root` lines 35-45
**Apply to:** `scripts/check_skill_versions.py` (when reading user-controllable paths) and the version-string validator
```python
if ".." in arg:
    raise SystemExit("OSBuilder: --<flag> cannot contain '..' segments.")
# version-string allowlist (Security V5):
_VERSION_RE = re.compile(r"^[0-9.]{1,16}$")
if not _VERSION_RE.match(version_str):
    raise SystemExit(f"OSBuilder: malformed version '{version_str}'.")
```

### Markdown reference doc with cross-link to script + "See also" footer
**Source:** `references/refuse-list.md` lines 1-7 + `references/markers.md` lines 1-7, 41-46
**Apply to:** `references/version-policy.md`, `examples/README.md`
```markdown
# <Title>

> Cross-referenced by `scripts/<script>.py:<function>`. <one-line summary of role>.
> **NOT loaded at runtime / Loaded at runtime — clarify which.**

[... policy/data ...]

## See also

- `scripts/<script>.py` — <what it does>
- <other related files>
```

### Pinned GitHub Actions versions (CI security V14)
**Source:** `assets/ci-workflows/python.yml.tmpl` lines 13-19
**Apply to:** `.github/workflows/ci.yml`
- Pin to exact major: `@v6` not `@latest`
- `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v6`

---

## No Analog Found

Files with no close match in the codebase (planner uses RESEARCH.md guidance for these):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `assets/demo/osbuilder-demo.gif` | binary asset | static | First binary asset in the repo. RESEARCH §State of the Art locks: GIF (auto-plays in GitHub README) recorded via asciinema → `agg`. |
| `assets/demo/osbuilder-demo.cast` | asciinema source | static | First asciinema cast in the repo. Source-of-truth for re-renders. |
| `examples/<name>/repo-url.txt` | one-line URL data file | static | No precedent for a one-line `.txt` data file. Format is plain text: either `https://github.com/...` or `NOT_PUBLISHED`. |
| `examples/<name>/screenshots/` | image-binary directory | static | No image binaries currently committed. Pitfall: keep ≤ 200KB JPGs to avoid repo bloat. |

---

## Metadata

**Analog search scope:** `scripts/`, `scripts/tests/`, `assets/`, `assets/ci-workflows/`, `references/`, `.planning/phases/07-*/`, `examples/`, repo root (`SKILL.md`, `install.sh`)
**Files scanned:** ~40
**Pattern extraction date:** 2026-05-02
