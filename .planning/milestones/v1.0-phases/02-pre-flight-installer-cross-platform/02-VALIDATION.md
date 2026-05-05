---
phase: 2
slug: pre-flight-installer-cross-platform
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `02-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already configured in `pyproject.toml` from Phase 1) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]` set in Phase 1 Wave 0) |
| **Quick run command** | `pytest scripts/tests/test_preflight.py scripts/tests/test_uninstall.py -x` |
| **Full suite command** | `pytest scripts/tests/ -v` |
| **Estimated runtime** | ~5-10 seconds (FakeShell mocks subprocess — no real installs in unit tests) |

---

## Sampling Rate

- **After every task commit:** Run `pytest scripts/tests/test_preflight.py scripts/tests/test_uninstall.py -x`
- **After every plan wave:** Run `pytest scripts/tests/ -v` (Phase 1 + Phase 2 tests, full GREEN required)
- **Before `/gsd-verify-work`:** Full suite must be green AND a manual real-machine smoke test on Charlie's macOS machine plus at least one Linux container smoke test must have completed
- **Max feedback latency:** 10 seconds for unit tests; ~3 minutes for end-to-end fresh-Mac smoke (matches Phase 2 Success Criterion #6)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | PRE-01..07 | T-02-01 | conftest extensions emit no import errors; lazy-import-via-fixture pattern preserved | unit | `pytest --collect-only scripts/tests/test_preflight.py scripts/tests/test_uninstall.py 2>&1 \| grep -c "test session starts"` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | PRE-01..07 | T-02-01 | ≥ 14 RED stubs collected, all SKIPPED (not COLLECTION-ERROR) | unit | `pytest --collect-only scripts/tests/test_preflight.py scripts/tests/test_uninstall.py \| grep -c "test_"` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | PRE-01 | T-02-02 | `detect()` returns missing tools by name within 10s on a fresh fixture | unit | `pytest scripts/tests/test_preflight.py::test_detect_missing_tools_macos -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | PRE-01 | T-02-03 | Detect Node version below 20 as missing | unit | `pytest scripts/tests/test_preflight.py::test_detect_node_below_required -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | PRE-01 | T-02-04 | VM detected (nvm/pyenv/mise) → refuse to clobber, emit message | unit | `pytest scripts/tests/test_preflight.py::test_vm_detected_blocks_install -x` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 1 | PRE-01 | T-02-05 | Detect Linux distro Ubuntu via /etc/os-release | unit | `pytest scripts/tests/test_preflight.py::test_detect_linux_distro_ubuntu -x` | ❌ W0 | ⬜ pending |
| 02-02-05 | 02 | 1 | PRE-02 | T-02-06 | Single confirmation prompt covers entire batch (one y/n) | unit | `pytest scripts/tests/test_preflight.py::test_single_confirmation_for_batch -x` | ❌ W0 | ⬜ pending |
| 02-02-06 | 02 | 1 | PRE-03 | T-02-07 | macOS path uses brew | unit | `pytest scripts/tests/test_preflight.py::test_macos_uses_brew -x` | ❌ W0 | ⬜ pending |
| 02-02-07 | 02 | 1 | PRE-03 | T-02-08 | Debian path uses apt-get | unit | `pytest scripts/tests/test_preflight.py::test_linux_debian_uses_apt -x` | ❌ W0 | ⬜ pending |
| 02-02-08 | 02 | 1 | PRE-03 | T-02-09 | Fedora path uses dnf | unit | `pytest scripts/tests/test_preflight.py::test_linux_fedora_uses_dnf -x` | ❌ W0 | ⬜ pending |
| 02-02-09 | 02 | 1 | PRE-03 | T-02-10 | Windows path uses winget | unit | `pytest scripts/tests/test_preflight.py::test_windows_uses_winget -x` | ❌ W0 | ⬜ pending |
| 02-02-10 | 02 | 1 | PRE-04 | T-02-11 | Failed install triggers rollback of prior installs in batch | unit | `pytest scripts/tests/test_preflight.py::test_failure_triggers_rollback -x` | ❌ W0 | ⬜ pending |
| 02-02-11 | 02 | 1 | PRE-04 | T-02-12 | install-log.json recorded BEFORE install subprocess starts | unit | `pytest scripts/tests/test_preflight.py::test_log_recorded_before_subprocess -x` | ❌ W0 | ⬜ pending |
| 02-02-12 | 02 | 1 | PRE-05 | T-02-13 | Dry-run preview prints; zero subprocess.run side-effects observed | unit | `pytest scripts/tests/test_preflight.py::test_dry_run_no_state_change -x` | ❌ W0 | ⬜ pending |
| 02-02-13 | 02 | 1 | PRE-07 | T-02-14 | `--no-docker` skips Docker detection AND prompt | unit | `pytest scripts/tests/test_preflight.py::test_no_docker_mode_skips_docker -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 1 | PRE-06 | T-02-15 | Uninstall reverses every action in install-log.json | unit | `pytest scripts/tests/test_uninstall.py::test_uninstall_reverses_all -x` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 1 | PRE-06 | T-02-16 | Uninstall preserves pre-existing tools (only what we logged) | unit | `pytest scripts/tests/test_uninstall.py::test_uninstall_preserves_pre_existing -x` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 1 | PRE-03 | — | `references/preflight/macos.md` documents brew install matrix + OrbStack note | doc-grep | `grep -q "brew install" .claude/skills/osbuilder/references/preflight/macos.md \|\| grep -q "brew install" references/preflight/macos.md` | ❌ W1 | ⬜ pending |
| 02-04-02 | 04 | 1 | PRE-03 | — | `references/preflight/linux.md` documents apt + dnf decision tree | doc-grep | `grep -qE "apt-get\|dnf install" references/preflight/linux.md` | ❌ W1 | ⬜ pending |
| 02-04-03 | 04 | 1 | PRE-03 | — | `references/preflight/windows.md` documents winget + PATH-refresh gotcha + Docker Desktop license note | doc-grep | `grep -qE "winget install" references/preflight/windows.md && grep -qi "PATH" references/preflight/windows.md` | ❌ W1 | ⬜ pending |
| 02-04-04 | 04 | 1 | PRE-01..07 | — | `references/preflight/README.md` is entry point linked from SKILL.md handoff | doc-grep | `test -f references/preflight/README.md && grep -q "preflight" references/preflight/README.md` | ❌ W1 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Threat refs (T-02-XX):** Allocated for the planner's `<threat_model>` block per workflow step 5.55. The threats are dominated by Pitfall 13 (clobbering version managers / system Python) and Pitfall 14 (cross-platform script breakage). The planner should map T-02-04 → "VM clobber refusal", T-02-11 → "rollback log integrity (atomicity)", T-02-12 → "dry-run preview before any state change", T-02-15 → "uninstall scope discipline (no over-deletion)" at minimum.

---

## Wave 0 Requirements

- [ ] `scripts/tests/test_preflight.py` — covers PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, PRE-07 (≥ 12 RED stubs)
- [ ] `scripts/tests/test_uninstall.py` — covers PRE-06 (≥ 2 RED stubs)
- [ ] `scripts/tests/conftest.py` extension — add `FakeShell`, `fake_shell`, `fake_which`, `tmp_install_log` fixtures
- [ ] `scripts/preflight_check.py` — file does not exist yet (lazy-import-via-fixture pattern handles this; pattern set in `test_state_writer.py:25-31`)
- [ ] `scripts/uninstall.py` — file does not exist yet
- [ ] *No new framework install needed* — pytest already in `pyproject.toml` from Phase 1.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fresh-Mac end-to-end ≤ 3 min | SC #6 (ROADMAP) | Real network bandwidth + brew tap creation + actual install — cannot be unit-mocked | On a clean macOS VM (or Charlie's secondary login), wipe `~/.osbuilder/`, then run `/osbuilder` → confirm time-to-prereqs-installed ≤ 180s |
| Windows winget PATH-refresh post-install | PRE-03 | New PATH entries don't propagate to the running shell — only verifiable on real Windows | After preflight installs Node via winget, open a fresh PowerShell session → `node --version` returns 20+; same shell that ran preflight may need to reopen |
| Linux sudo TTY prompt UX | PRE-02 | sudo password prompts cannot be reliably faked in CI | Run preflight on a fresh Ubuntu container with non-interactive shell → verify it either prompts cleanly with friendly pre-warning, or refuses and tells user to re-run from interactive shell |
| Docker Desktop license disclaimer (Windows) | PRE-07 | Disclaimer text rendering is a UX-correctness check, not a functional test | On Windows preflight that includes Docker, verify that the dry-run preview shows the Docker Desktop license note before user confirmation |
| Rollback after partial-batch failure | PRE-04 / SC #3 | Rollback correctness depends on actual package-manager behavior under failure | Inject a guaranteed-fail tool (e.g., point preflight at a non-existent winget package ID) → verify `which node` / `which python3` / `which gh` / `which docker` return the same as before preflight ran |

*Manual checks gate `/gsd-verify-work` — the full pytest suite passing is necessary but not sufficient for Phase 2 sign-off.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies (the manual-only rows above are explicitly the only exceptions, all tied to real-machine constraints)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (every implementation task in Wave 1 flips a Wave 0 stub to GREEN)
- [ ] Wave 0 covers all MISSING references (≥ 14 RED stubs across `test_preflight.py` + `test_uninstall.py`)
- [ ] No watch-mode flags (no `pytest --watch` or similar)
- [ ] Feedback latency < 10s (FakeShell-mocked unit tests; real installs only behind manual smoke)
- [ ] `nyquist_compliant: true` set in frontmatter once Wave 0 lands and `pytest --collect-only` confirms ≥ 14 stubs

**Approval:** pending
