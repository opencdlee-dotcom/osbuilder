# bootstrap.ps1 — installs Python 3 if missing, then re-execs into state_writer.py.
#
# PowerShell 5.1-compatible (built into Windows 10/11). Two-mode behavior to
# work around the documented winget PATH-refresh gotcha (Pitfall 5):
#
#   - If Python WAS already on PATH before this script ran (existing-Python
#     mode), re-exec into state_writer.py in the same shell.
#   - If Python was JUST installed by winget (just-installed mode), the
#     current shell cannot see it without reopening. Exit 0 with a
#     "reopen shell" message and let the user re-run from a fresh shell.

$ErrorActionPreference = "Stop"

# Step 1: Capture pre-install state (BEFORE any installer runs)
$pythonAlreadyPresent = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
$JustInstalled = $false

# Step 2: If Python missing, install via winget (winget primary on Win10+/11)
if (-not $pythonAlreadyPresent) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        Write-Error "Bootstrap needs winget (Windows 10+ / 11). Update Windows or install Python 3.13+ manually from https://www.python.org/downloads/."
        exit 1
    }

    Write-Host "Installing Python 3.13 via winget..." -ForegroundColor Cyan
    & winget install -e --id Python.Python.3.13 --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Error "winget install failed (exit $LASTEXITCODE). Install Python 3.13+ manually and re-run."
        exit 1
    }
    $JustInstalled = $true
}

# Step 3: Two-mode dispatch
$SkillDir = Join-Path $HOME ".claude/skills/osbuilder"
$StateWriter = Join-Path $SkillDir "scripts/state_writer.py"

if ($JustInstalled) {
    # winget PATH refresh required — same shell cannot see python yet
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Python 3.13 installed successfully." -ForegroundColor Green
    Write-Host "Reopen your shell (or open a new PowerShell window), then re-run /osbuilder." -ForegroundColor Yellow
    exit 0
}

# Existing-Python path: re-exec into state_writer.py
if (Test-Path $StateWriter) {
    & python $StateWriter @args
    exit $LASTEXITCODE
} else {
    Write-Host "Bootstrap complete. Run /osbuilder to continue." -ForegroundColor Green
    exit 0
}
