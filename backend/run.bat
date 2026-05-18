@echo off
REM ============================================================
REM  NexusAI backend launcher for Windows (cmd.exe).
REM
REM  Behavior:
REM    1. Move into this script's directory (the backend root).
REM    2. Create .venv if missing, install requirements.
REM    3. Load environment variables from .env if it exists.
REM    4. Start uvicorn with --reload, honoring BACKEND_HOST /
REM       BACKEND_PORT overrides.
REM
REM  Usage:
REM    cd backend
REM    run.bat
REM ============================================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM --- Step 1: ensure python is available ----------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [error] python is not on PATH. Install Python 3.10+ from python.org.
    exit /b 1
)

REM --- Step 2: create venv on first run ------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [setup] creating virtualenv in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [error] failed to create virtualenv.
        exit /b 1
    )
)

REM --- Step 3: install/upgrade requirements -------------------
echo [setup] installing dependencies (idempotent) ...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [error] pip install failed.
    exit /b 1
)

REM --- Step 4: load .env if present ---------------------------
REM   cmd.exe has no built-in `source`, so we parse line-by-line.
REM   Lines beginning with `#` and blank lines are skipped.
if exist ".env" (
    echo [setup] loading variables from .env ...
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "_KEY=%%A"
        set "_VAL=%%B"
        REM Skip comment lines.
        if not "!_KEY:~0,1!"=="#" (
            if not "!_KEY!"=="" (
                set "!_KEY!=!_VAL!"
            )
        )
    )
)

REM --- Step 5: apply defaults ---------------------------------
if "%BACKEND_HOST%"=="" set "BACKEND_HOST=0.0.0.0"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"

REM --- Step 6: launch uvicorn ---------------------------------
echo.
echo [launch] starting NexusAI on http://%BACKEND_HOST%:%BACKEND_PORT%
echo          docs available at http://localhost:%BACKEND_PORT%/docs
echo          press CTRL+C to stop.
echo.

".venv\Scripts\python.exe" -m uvicorn nexusai.api.app:app ^
    --host "%BACKEND_HOST%" ^
    --port %BACKEND_PORT% ^
    --reload

endlocal