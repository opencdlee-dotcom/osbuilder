#!/bin/sh
# bootstrap.sh — installs Python 3 if missing, then re-execs into state_writer.py.
#
# POSIX-compatible (/bin/sh). Cross-platform: macOS (Homebrew), Linux (apt/dnf).
# Windows users: see scripts/bootstrap.ps1 (PowerShell counterpart).
#
# Resume Protocol: after Python is present, exec into the installed
# state_writer.py so OSBuilder can read state.md and route to the resumed
# role/phase. If state_writer.py is not yet copied to the install location,
# print a friendly message and exit clean (the installed location may not
# exist yet during a partial first-run).

set -eu

OS=$(uname -s 2>/dev/null || echo unknown)
PYTHON_INSTALLED_NOW=0

# Step 1: Python detection
if command -v python3 >/dev/null 2>&1; then
  : # already present, nothing to install
else
  PYTHON_INSTALLED_NOW=1

  case "$OS" in
    Darwin)
      # macOS: install via Homebrew
      if ! command -v brew >/dev/null 2>&1; then
        echo "Bootstrap needs Homebrew to install Python 3 on macOS." >&2
        echo "Install Homebrew from https://brew.sh and re-run this script." >&2
        exit 1
      fi
      echo "Installing Python 3.13 via Homebrew..." >&2
      brew install python@3.13
      ;;
    Linux)
      # Linux: apt-get (Debian/Ubuntu) or dnf (Fedora/RHEL)
      if command -v apt-get >/dev/null 2>&1; then
        echo "Installing Python 3 via apt-get (sudo required)..." >&2
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
      elif command -v dnf >/dev/null 2>&1; then
        echo "Installing Python 3 via dnf (sudo required)..." >&2
        sudo dnf install -y python3 python3-pip
      else
        echo "Bootstrap could not detect a supported package manager." >&2
        echo "Tried: apt-get, dnf. Install Python 3.13+ manually and re-run." >&2
        exit 1
      fi
      ;;
    *)
      echo "Unsupported OS: $OS" >&2
      echo "Install Python 3.13+ manually and re-run." >&2
      exit 1
      ;;
  esac
fi

# Step 2: Re-exec into state_writer.py at the installed location
SKILL_DIR="${HOME}/.claude/skills/osbuilder"
STATE_WRITER="${SKILL_DIR}/scripts/state_writer.py"

if [ -f "${STATE_WRITER}" ]; then
  exec python3 "${STATE_WRITER}" "$@"
else
  if [ "${PYTHON_INSTALLED_NOW}" -eq 1 ]; then
    echo "Python installed. Run /osbuilder to continue." >&2
  else
    echo "Bootstrap complete. Run /osbuilder to continue." >&2
  fi
fi
