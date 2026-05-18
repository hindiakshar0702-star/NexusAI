# ============================================================
#  NexusAI backend launcher for Windows PowerShell.
#
#  Behavior:
#    1. Move into this script's directory (the backend root).
#    2. Create .venv if missing, install requirements.
#    3. Load environment variables from .env if it exists.
#    4. Start uvicorn with --reload, honoring BACKEND_HOST /
#       BACKEND_PORT overrides.
#
#  Usage:
#    cd backend
#    .\run.ps1
#
#  If you see "running scripts is disabled on this system",
#  run this once in PowerShell:
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# ============================================================

$ErrorActionPreference = 'Stop'

# Move to this script's directory so paths resolve consistently.
Set-Location -Path $PSScriptRoot

# --- Step 1: ensure python is available ------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[error] python is not on PATH. Install Python 3.10+ from python.org." -ForegroundColor Red
    exit 1
}

# --- Step 2: create venv on first run --------------------------
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[setup] creating virtualenv in .venv ..." -ForegroundColor Cyan
    python -m venv .venv
}

# --- Step 3: install/upgrade requirements ----------------------
Write-Host "[setup] installing dependencies (idempotent) ..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt

# --- Step 4: load .env if present ------------------------------
# PowerShell has no built-in `source`, so we parse the file ourselves.
# Format: KEY=VALUE per line. Lines starting with # are comments.
if (Test-Path ".env") {
    Write-Host "[setup] loading variables from .env ..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            $parts = $line -split '=', 2
            if ($parts.Length -eq 2) {
                $name = $parts[0].Trim()
                # Strip surrounding quotes if any.
                $value = $parts[1].Trim().Trim('"').Trim("'")
                Set-Item -Path "Env:$name" -Value $value
            }
        }
    }
}

# --- Step 5: apply defaults ------------------------------------
if (-not $env:BACKEND_HOST) { $env:BACKEND_HOST = '0.0.0.0' }
if (-not $env:BACKEND_PORT) { $env:BACKEND_PORT = '8000' }

# --- Step 6: launch uvicorn ------------------------------------
Write-Host ""
Write-Host "[launch] starting NexusAI on http://$($env:BACKEND_HOST):$($env:BACKEND_PORT)" -ForegroundColor Green
Write-Host "         docs available at http://localhost:$($env:BACKEND_PORT)/docs" -ForegroundColor Green
Write-Host "         press CTRL+C to stop." -ForegroundColor Green
Write-Host ""

& $venvPython -m uvicorn nexusai.api.app:app `
    --host $env:BACKEND_HOST `
    --port $env:BACKEND_PORT `
    --reload