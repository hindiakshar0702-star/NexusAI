@echo off
REM ============================================================
REM  NexusAI backend launcher for Windows (Command Prompt + PS).
REM
REM  What this does:
REM    1. Creates a Python virtualenv in .venv if missing.
REM    2. Installs/updates dependencies.
REM    3. Starts uvicorn with auto-reload on port 8000.
REM
REM  Usage:
REM    cd backend
REM    run.bat
REM ============================================================

setlocal EnableDelayedExpansion

REM Move to the script's own directory so paths work no matter
REM where the user invoked us from.
cd /d "%~dp0"

REM --- Step 1: pick a Python interpreter -------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [error] python is not on PATH. Install Python 3.10+ from python.org and re-run.
    exit /b 1
)

REM --- Step 2: create venv on first run --------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [setup] creating virtualenv in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [error] failed to create virtualenv.
        exit /b 1
    )
)

REM --- Step 3: install/upgrade requirements ---------------------
echo [setup] installing dependencies (idempotent, safe to re-run) ...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [error] pip install failed. See messages above.
    exit /b 1
)

REM --- Step 4: launch uvicorn -----------------------------------
echo.
echo [launch] starting NexusAI on http://localhost:8000
echo          docs available at http://localhost:8000/docs
echo          press CTRL+C to stop.
echo.

".venv\Scripts\python.exe" -m uvicorn nexusai.api.app:app --host 0.0.0.0 --port 8000 --reload

endlocal
