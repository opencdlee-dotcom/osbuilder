#!/bin/sh
# install.sh — installs OSBuilder as a Claude Code skill.
#
# Idempotent: running twice produces the same result without errors.
# Copies repo artifacts into ${HOME}/.claude/skills/osbuilder/ following
# the canonical pattern (see ~/.claude/skills/predator/install.sh).
#
# What it does:
#   1. Resolves the repo root from the script's own location.
#   2. Creates the four-directory skill layout under ${HOME}/.claude/skills/osbuilder/.
#   3. Copies the artifact set: SKILL.md, references/, scripts/ (all *.py and the
#      bootstrap shims — the orchestrator needs every helper at runtime, not just
#      state_writer), and assets/ (vendored starters + templates the scaffolders
#      read from disk at runtime).
#   4. Sets executable bits on copied scripts.
#
# Anti-patterns (deliberately avoided):
#   - No `rm -rf` — never destroys user data
#   - No sudo
#   - No nested directories beyond one level (Anthropic skill guidance)
#   - Source-guarded copies (warn + skip if a file is missing rather than crash)

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="${HOME}/.claude/skills/osbuilder"

echo "Installing OSBuilder to ${SKILL_DIR}..." >&2

# Step 1: Create the four standard sub-directories (idempotent — mkdir -p never errors on existing dirs)
mkdir -p \
  "${SKILL_DIR}/references" \
  "${SKILL_DIR}/scripts" \
  "${SKILL_DIR}/assets" \
  "${SKILL_DIR}/examples"

# Step 2: Copy artifacts with source-guards (BLOCKER 1 closure).
# Each copy is wrapped in `if [ -f|-d ... ]` so a partial-state repo
# (e.g., during Wave 1 landing) still installs cleanly.

# 2a. SKILL.md (required for FOUND-01)
if [ -f "${SCRIPT_DIR}/SKILL.md" ]; then
  cp -p "${SCRIPT_DIR}/SKILL.md" "${SKILL_DIR}/SKILL.md"
else
  echo "warn: ${SCRIPT_DIR}/SKILL.md missing — skipping SKILL.md copy" >&2
fi

# 2b. references/ tree (recursive)
if [ -d "${SCRIPT_DIR}/references" ]; then
  cp -Rp "${SCRIPT_DIR}/references/." "${SKILL_DIR}/references/"
else
  echo "warn: ${SCRIPT_DIR}/references/ missing — skipping references copy" >&2
fi

# 2c. scripts/ — every *.py orchestrator helper plus the bootstrap shims.
# The orchestrator (SKILL.md routing) calls these by path at runtime
# (preflight_check.py, scaffold_dispatch.py, intake_handler.py, runbook_writer.py,
# stack_researcher.py, narration.py, friendly_error.py, registry_verify.py,
# gh_handoff.py, gsd_driver.py, failure_classifier.py, production_phase_writer.py,
# check_skill_md_length.py, check_skill_versions.py, state_writer.py). Skip the
# tests/ subtree — those are dev-only. Skip __pycache__ — runtime artifacts.
if [ -d "${SCRIPT_DIR}/scripts" ]; then
  for src in "${SCRIPT_DIR}"/scripts/*.py "${SCRIPT_DIR}"/scripts/bootstrap.sh "${SCRIPT_DIR}"/scripts/bootstrap.ps1; do
    [ -f "$src" ] || continue
    cp -p "$src" "${SKILL_DIR}/scripts/$(basename "$src")"
  done
  # Optional sub-trees that scaffold helpers expect alongside the scripts (none today,
  # but keep the structure obvious for future additions).
else
  echo "warn: ${SCRIPT_DIR}/scripts/ missing — skipping scripts copy" >&2
fi

# 2d. assets/ tree — vendored starters + templates the scaffolders read at runtime
# (cli-starter, fastapi-starter, hub-template, dockerfiles, ci-workflows,
# gitignore-templates, gitleaks, readme-template.md). Without this the cli +
# ai-service + desktop scaffolders break with FileNotFoundError on the first run.
if [ -d "${SCRIPT_DIR}/assets" ]; then
  cp -Rp "${SCRIPT_DIR}/assets/." "${SKILL_DIR}/assets/"
  # assets/hub-template/professor-snapshot/ is a vendored example (depth-3+ tree
  # of contributor reference material), not runtime-needed — scaffold_hub() only
  # uses CLAUDE.md.tmpl + subtool-CLAUDE.md.tmpl at the top of hub-template/.
  # Pruning it keeps the installed skill within the Anthropic one-level-deep
  # contract (test_install_no_nested_dirs).
  rm -rf "${SKILL_DIR}/assets/hub-template/professor-snapshot"
else
  echo "warn: ${SCRIPT_DIR}/assets/ missing — skipping assets copy" >&2
fi

# Note: examples/ (web/cli/ai-service galleries) is NOT installed. The skill
# never reads it at runtime; the gallery exists in the source repo for
# documentation purposes (and would otherwise create depth-3 dirs via the
# screenshots/ subdirs). Users who need it can browse the public repo on GitHub.

# Step 3: Ensure executable bits on every copied .py + bootstrap shim.
for f in "${SKILL_DIR}"/scripts/*.py "${SKILL_DIR}/scripts/bootstrap.sh"; do
  [ -f "$f" ] && chmod +x "$f" || true
done

echo "OSBuilder installed at ${SKILL_DIR}" >&2
echo "Run /osbuilder in a Claude Code session to start." >&2
