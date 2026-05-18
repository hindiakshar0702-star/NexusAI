# ============================================================
#  NexusAI backend launcher for Windows PowerShell.
#
#  What this does:
#    1. Creates a Python virtualenv in .venv if missing.
#    2. Installs/updates dependencies.
#    3. Starts uvicorn with auto-reload on port 8000.
#
#  Usage:
#    cd backend
#    .\run.ps1
#
#  If you see "running scripts is disabled on this system",
#  open PowerShell as Administrator once and run:
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# ============================================================

$ErrorActionPreference = 'Stop'

# Move to this script's directory so paths resolve consistently.
Set-Location -Path $PSScriptRoot

# --- Step 1: pick a Python interpreter -----------------------
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[error] python is not on PATH. Install Python 3.10+ from python.org and re-run." -ForegroundColor Red
    exit 1
}

# --- Step 2: create venv on first run ------------------------
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[setup] creating virtualenv in .venv ..." -ForegroundColor Cyan
    python -m venv .venv
}

# --- Step 3: install/upgrade requirements -------------------
Write-Host "[setup] installing dependencies (idempotent, safe to re-run) ..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt

# --- Step 4: launch uvicorn ---------------------------------
Write-Host ""
Write-Host "[launch] starting NexusAI on http://localhost:8000" -ForegroundColor Green
Write-Host "         docs available at http://localhost:8000/docs" -ForegroundColor Green
Write-Host "         press CTRL+C to stop." -ForegroundColor Green
Write-Host ""

& $venvPython -m uvicorn nexusai.api.app:app --host 0.0.0.0 --port 8000 --reload
