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
#   3. Copies the artifact set: SKILL.md, references/, scripts/state_writer.py,
#      scripts/bootstrap.sh, scripts/bootstrap.ps1.
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

# 2c. state_writer.py (required for FOUND-05)
if [ -f "${SCRIPT_DIR}/scripts/state_writer.py" ]; then
  cp -p "${SCRIPT_DIR}/scripts/state_writer.py" "${SKILL_DIR}/scripts/state_writer.py"
else
  echo "warn: ${SCRIPT_DIR}/scripts/state_writer.py missing — skipping" >&2
fi

# 2d. bootstrap.sh (POSIX shim)
if [ -f "${SCRIPT_DIR}/scripts/bootstrap.sh" ]; then
  cp -p "${SCRIPT_DIR}/scripts/bootstrap.sh" "${SKILL_DIR}/scripts/bootstrap.sh"
else
  echo "warn: ${SCRIPT_DIR}/scripts/bootstrap.sh missing — skipping" >&2
fi

# 2e. bootstrap.ps1 (Windows PowerShell shim)
if [ -f "${SCRIPT_DIR}/scripts/bootstrap.ps1" ]; then
  cp -p "${SCRIPT_DIR}/scripts/bootstrap.ps1" "${SKILL_DIR}/scripts/bootstrap.ps1"
else
  echo "warn: ${SCRIPT_DIR}/scripts/bootstrap.ps1 missing — skipping" >&2
fi

# Step 3: Ensure executable bits on copied scripts (only if files exist after copy)
[ -f "${SKILL_DIR}/scripts/state_writer.py" ] && chmod +x "${SKILL_DIR}/scripts/state_writer.py" || true
[ -f "${SKILL_DIR}/scripts/bootstrap.sh" ]    && chmod +x "${SKILL_DIR}/scripts/bootstrap.sh"    || true

echo "OSBuilder installed at ${SKILL_DIR}" >&2
echo "Run /osbuilder in a Claude Code session to start." >&2
