---
phase: 6
slug: ship-to-private-github-scalable-defaults
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-01
---

# Phase 6 — Security

> Per-phase security contract for ship-to-private-github-scalable-defaults: 33 threats across 6 plans (Plan 01=5, Plan 02=7, Plan 03=5, Plan 04=5, Plan 05=6, Plan 06=5). 22 mitigate, 11 accept, 0 transfer. All mitigations verified present in implementation; all accepted risks documented below.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| test fixture → state_writer subprocess | `fake_state_md` invokes state_writer with kwargs | field+value strings; `_check_value_safe` rejects newline + `..` |
| test collection → not-yet-existing modules | Lazy-import fixtures (`gh`, `rw`, `pp`, `sd`, `ih`) skip cleanly via `pytest.skip` | importlib.import_module result |
| fixture file (derived_spec_with_k8s.md) → refusal gate | Markdown content read as text | refuse-list keywords (kubernetes/helm/microservices) |
| mock subprocess fixtures → production code | Test-only via monkeypatch; auto-undone at test end | mocked subprocess.run signatures |
| user-supplied --project-name → subprocess argv (gh/git) | CLI args passed as list[str], shell=False | project name string |
| `gh repo view --json` stdout → json.loads | Untrusted external input; bounded by gh JSON schema | JSON object {visibility, nameWithOwner, sshUrl} |
| ssh_url field → state.md | Sanitized via `.strip().replace("\n"," ")` | repo URL string |
| friendly_error stderr → user terminal | `_strip_tracebacks` + `_TOKEN_RE.sub` token redaction in `_friendly` | sanitized error message |
| assets/gitleaks/.gitleaks.toml allowlist regex → gitleaks runtime | End-anchored regex `(.*?)\.env\.example$` | allowlist file path patterns |
| stack_family arg → ASSETS path | Literal values from scaffold_web ("node-pnpm", "python-uv"); not user-supplied at Wave 1 | template filename component |
| _pick_database (playbook, app_type) → state.md | Pure function; output ∈ {"postgres","sqlite"} | db choice string |
| Asset file content → atomic_write to project_dir | Project-controlled in source control | template content |
| state.md → runbook_writer (via state_writer subprocess) | Values went through `_check_value_safe` | substituted README placeholders |
| repo_url → README quickstart `git clone` | Sanitized in gh_handoff before persistence | public SSH URL |
| derived_spec.md content → REFUSE_KEYWORDS membership | Plain-text Markdown; no parsing/exec; word-boundary regex | matched keyword string |
| state.md production_ready field → bypass logic | Value ∈ {"true","false"} per `_check_value_safe` | bypass boolean |
| references/refuse-list.md → user-facing stderr | Static repo file; not user-editable at build time | refusal copy section |
| matched keyword → state.md last_failure | Comes from hardcoded REFUSE_KEYWORDS tuple | "refused: <kw>" string |
| gsd_driver.py → child-script CLIs (intake_handler / gh_handoff / runbook_writer / production_phase_writer) | Subprocess.run with list[str], shell=False | sentinel exit codes (0/2) |
| state.md gsd_phase_count → ship-step trigger | `int()` with ValueError → 0 (safe default) | integer phase count |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-06-01-01 | Tampering | ALLOWED_FIELDS extension (5 new fields) | mitigate | Additive only inside existing set literal in `scripts/state_writer.py:51-55`; existing `_check_value_safe` enforces newline + `..` reject on all writes | closed |
| T-06-01-02 | Repudiation | Wave 0 RED stubs skip silently | accept | All stubs use `pytest.skip("Wave 1 target")` — visible in pytest output; Wave 1 has flipped all 17 stubs to GREEN (or env-gated SKIP for V-07) | closed |
| T-06-01-03 | Tampering | conftest.py mock fixtures override subprocess.run | mitigate | Fixtures use `monkeypatch.setattr` (auto-undone at test end); cannot leak; verified at `scripts/tests/conftest.py:206` | closed |
| T-06-01-04 | Information Disclosure | derived_spec_with_k8s.md fixture content reaches stderr via refusal copy | accept | Fixture content intentionally crafted; Kubernetes/Helm names are public, not secrets | closed |
| T-06-01-05 | DoS | Bad fake_state_md kwargs crash test setup | mitigate | `_check_value_safe` and `_check_field_allowed` in state_writer.py reject malformed inputs; fixture passes plain str values from test code | closed |
| T-06-02-01 | Tampering | `subprocess.run(["gh","repo","create",...])` | mitigate | All argv passed as list[str]; `shell=False` confirmed at all 11 subprocess sites in `scripts/gh_handoff.py` (grep -c "shell=True" = 0); URL flags use literal strings | closed |
| T-06-02-02 | Tampering | gh stderr → friendly_error.translate(ctx) | mitigate | `ctx={"tool":"gh"}` is literal at `scripts/gh_handoff.py:88`; user-derived input never enters ctx | closed |
| T-06-02-03 | Information Disclosure | Token leakage from `gh` stderr (`gh[opsur]_*` patterns) | mitigate | `_TOKEN_RE` defined at `scripts/gh_handoff.py:33-35` covers ghp_/ghs_/gho_/ghu_/ghr_/github_pat_*; redaction applied in `_friendly` at line 86 BEFORE `_fe.translate` | closed |
| T-06-02-04 | Tampering | gitleaks .gitleaks.toml allowlist | mitigate | `assets/gitleaks/.gitleaks.toml` allowlist entries are static + end-anchored (`.*\.env\.example$` etc.); upstream gitleaks default ruleset still applies | closed |
| T-06-02-05 | DoS | gh subprocess hang (no timeout) | accept | gh CLI has internal timeouts; user can ctrl-C; friendly_error message guides them; Phase 7 may add explicit timeout=30 if dogfood reveals hangs | closed |
| T-06-02-06 | Repudiation | state.md repo_url overwrite on re-run (idempotency) | mitigate | `_write_state_field` always writes the latest gh-reported value; `state_writer.py` atomic `os.replace` guarantees no corruption; `ssh_url.strip().replace("\n"," ")` at `scripts/gh_handoff.py:272` sanitizes before write | closed |
| T-06-02-07 | Spoofing | MITM on github.com HTTPS | accept | gh CLI uses system TLS; outside OSBuilder threat scope (matches T-04-04-05) | closed |
| T-06-03-01 | Tampering | `_write_dockerfile` path traversal via stack_family arg | mitigate | `stack_family` is a literal in scaffold_web at `scripts/scaffold_dispatch.py:232-233` ("node-pnpm","node"); current callers do NOT accept user-supplied stack_family. If exposed via CLI in Phase 7, validate against hardcoded allowlist tuple | closed |
| T-06-03-02 | Tampering | compose.yaml `version:` key reintroduction | mitigate | `_COMPOSE_YAML` constant has no `version:` key; verified by grep `^version:` (returns 0 against scaffold_dispatch.py and CI workflow templates) | closed |
| T-06-03-03 | Information Disclosure | Dockerfile leaks build secrets | accept | Templates contain no secrets; build-time secrets pass via build args/secrets at user build time, not in template | closed |
| T-06-03-04 | DoS | Workflow YAML triggers infinite loop | accept | `pull_request:` trigger only; no `push:` trigger; no schedule; bounded by GitHub Actions runtime limits | closed |
| T-06-03-05 | Tampering | actions/setup-node before pnpm/action-setup (cache silently breaks) | mitigate | Verified by line-index check: `assets/ci-workflows/node.yml.tmpl` line 22 (pnpm/action-setup@v4) precedes line 26 (actions/setup-node@v4); `test_one_ci_workflow` enforces this | closed |
| T-06-04-01 | Tampering | Placeholder injection via state.md value | mitigate | `str.replace` (not `str.format`) used at `scripts/runbook_writer.py:169`; post-substitution `leftover = [key for key in subs if key in composed]` (line 174) catches any unfilled key | closed |
| T-06-04-02 | Information Disclosure | repo_url printed in README quickstart | accept | repo_url is the public-facing SSH URL of user's own private repo; rendering it is the entire point (clone-and-run) | closed |
| T-06-04-03 | Tampering | LLM-section placeholder spoofing | accept | "How OSBuilder built this" line in template is intentionally a placeholder; Phase 5 Plan 05-05 fills it; persists with documented self-explaining placeholder text otherwise | closed |
| T-06-04-04 | DoS | Re-stamping overwriting `/gsd-docs-update` edits | mitigate | `OSBUILDER_MARKER = "<!-- OSBuilder runbook -->"` defined at `scripts/runbook_writer.py:33`; idempotency check at line 137 (`if OSBUILDER_MARKER in existing: return`) skips rewrite | closed |
| T-06-04-05 | Tampering | Path traversal via state.md project_path | mitigate | `Path(project_path).name` at `scripts/runbook_writer.py:151` extracts only the last component; `..` segments rejected upstream by `state_writer._check_value_safe` | closed |
| T-06-05-01 | Tampering | Refusal bypass via false-negative regex | mitigate | `_matches_refuse_keyword` at `scripts/intake_handler.py:147` uses `re.search(r"\b" + re.escape(kw) + r"\b", lower)` for single-word; `test_kubernetes_refused` verifies positive matches | closed |
| T-06-05-02 | Tampering | Refusal bypass via false-positive on benign words | mitigate | Same word-boundary regex; "kubectl apply" does NOT match (kubectl not in tuple); `test_clean_spec_passes` verifies negative case via `derived_spec_clean.md` fixture | closed |
| T-06-05-03 | Repudiation | Silent refusal — user thinks build is progressing | mitigate | `check_refuse_list` writes `last_failure="refused: <kw>"` to state.md AND prints refusal copy to stderr; `gsd_driver.py:648` interprets exit code 2 as "do not advance phase_step" so build halts visibly | closed |
| T-06-05-04 | Information Disclosure | refuse-list.md content leaks build internals | accept | refuse-list.md is project-internal documentation; content is intentionally user-facing; nothing sensitive | closed |
| T-06-05-05 | DoS | Massive derived_spec.md → linear regex scan | accept | derived_spec.md bounded by intake_handler's own size cap (~<2KB in practice); regex scan O(n*kw_count) with kw_count=10 | closed |
| T-06-05-06 | Tampering | production_phase_writer emits >7 lines (drift) | mitigate | `NAMED_UPGRADES` is a tuple constant at `scripts/production_phase_writer.py:22`; `test_emits_seven_phases` asserts exactly 7; static — no per-build mutation | closed |
| T-06-06-01 | Tampering | Refusal-gate bypass via subprocess return code spoof | mitigate | Exit code 2 is deterministic from `intake_handler._cmd_check_refuse_list`; tampering would require modifying intake_handler.py itself (same trust level as gsd_driver, out of threat scope) | closed |
| T-06-06-02 | Tampering | Ship-step double-trigger (idempotency violation) | mitigate | `gh_handoff.py` checks `git remote get-url origin` and skips create when remote exists; `runbook_writer.py` checks OSBUILDER_MARKER; `production_phase_writer.py` is stdout-only | closed |
| T-06-06-03 | Information Disclosure | gh_handoff stderr leaks tokens through gsd_driver passthrough | mitigate | T-06-02-03 redaction (`_TOKEN_RE.sub("[REDACTED-TOKEN]", raw)`) applied in `_friendly` before stderr write; gsd_driver passes already-sanitized stderr through unchanged | closed |
| T-06-06-04 | DoS | Ship-step runs on every emit_next_command call (no progress) | accept | Idempotency in all 3 sub-scripts means re-runs are cheap (read state, check marker/remote, return); worst case is ~3 fast subprocess calls and no destructive work | closed |
| T-06-06-05 | Tampering | SKILL.md grows beyond 200 lines (QUAL-01) | mitigate | `wc -l SKILL.md` = 130 (within 200 cap); all 3 new artifacts mentioned (`runbook_writer.py`, `production_phase_writer.py`, `refuse-list.md`) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-01 | T-06-01-02 | Wave 0 RED stubs intentionally `pytest.skip("Wave 1 target")` to satisfy Nyquist gate; visible in pytest output; Wave 1 has flipped all stubs GREEN (or env-gated SKIP for V-07 gitleaks integration). Repudiation surface bounded to 16 named tests with V-ID docstrings. | gsd-security-auditor | 2026-05-01 |
| AR-06-02 | T-06-01-04 | derived_spec_with_k8s.md fixture content (Kubernetes/Helm/microservices) is intentionally crafted to trigger refusal gate; all keywords are public technology names, not secrets. | gsd-security-auditor | 2026-05-01 |
| AR-06-03 | T-06-02-05 | gh subprocess hang without explicit timeout. Mitigation: gh CLI has internal HTTP timeouts; user retains ctrl-C; friendly_error guidance. Phase 7 may add `timeout=30` if dogfood surfaces hang reports. | gsd-security-auditor | 2026-05-01 |
| AR-06-04 | T-06-02-07 | MITM on github.com HTTPS. gh CLI uses system TLS trust store; OSBuilder cannot improve on system trust. Out of scope (matches T-04-04-05 acceptance). | gsd-security-auditor | 2026-05-01 |
| AR-06-05 | T-06-03-03 | Dockerfile templates do not embed secrets. Build-time secrets pass via Docker build args / BuildKit secrets supplied by user at `docker build` time, not by OSBuilder. | gsd-security-auditor | 2026-05-01 |
| AR-06-06 | T-06-03-04 | CI workflow templates use `pull_request:` trigger only (no `push:`, no `schedule:`). GitHub Actions enforces 6-hour job timeout and 35-day total per repo runtime caps. Infinite loop bounded externally. | gsd-security-auditor | 2026-05-01 |
| AR-06-07 | T-06-04-02 | repo_url rendered in README Quick Start `git clone` command. The URL is the public SSH URL of the user's own private repo; rendering it is the entire point of the clone-and-run runbook. Visibility of the URL alone does not grant access (private repo gates on GitHub auth). | gsd-security-auditor | 2026-05-01 |
| AR-06-08 | T-06-04-03 | "How OSBuilder built this" placeholder section in `assets/readme-template.md` is filled by Phase 5 `/gsd-docs-update` (Plan 05-05) LLM-augmented step. If unfilled, the template ships a self-explaining placeholder telling the user to re-run `/osbuilder`. No spoofable surface. | gsd-security-auditor | 2026-05-01 |
| AR-06-09 | T-06-05-04 | references/refuse-list.md is project-internal documentation that ships with OSBuilder. Content is intentionally user-facing (refusal copy + opt-in path). No build-internal secrets present. | gsd-security-auditor | 2026-05-01 |
| AR-06-10 | T-06-05-05 | derived_spec.md is bounded by intake_handler size constraints (~<2KB observed). Regex scan over 10 refuse keywords is O(n*10) per scan. Even pathological 1MB input runs in milliseconds; insufficient surface for DoS. | gsd-security-auditor | 2026-05-01 |
| AR-06-11 | T-06-06-04 | Ship-step block runs on every `emit_next_command` call when `current_phase > gsd_phase_count`. All 3 child scripts (runbook_writer / gh_handoff / production_phase_writer) carry their own idempotency checks (OSBUILDER_MARKER / `git remote get-url origin` / stdout-only). Re-runs are cheap reads; no destructive work. | gsd-security-auditor | 2026-05-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-01 | 33 | 33 | 0 | gsd-security-auditor (Opus 4.7 1M) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-01
