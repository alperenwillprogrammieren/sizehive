@echo off
REM Wrapper for Windows Task Scheduler: activates the venv and runs the daily
REM pipeline. Task Scheduler starts processes with an arbitrary working
REM directory, so everything here is resolved relative to this file.
REM
REM Register (per-user, no admin needed):
REM   schtasks /Create /TN "sizehive daily update" /TR "<repo>\backend\scripts\daily_update.bat" /SC DAILY /ST 05:00
REM Remove:
REM   schtasks /Delete /TN "sizehive daily update" /F

setlocal
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%.."
set "REPO_DIR=%BACKEND_DIR%\.."

cd /d "%BACKEND_DIR%" || exit /b 1

if exist "%REPO_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON=%REPO_DIR%\.venv\Scripts\python.exe"
) else if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
) else (
    echo Could not find a virtualenv python. Looked in %REPO_DIR%\.venv and %BACKEND_DIR%\.venv
    exit /b 1
)

"%PYTHON%" "%SCRIPT_DIR%daily_update.py"
exit /b %ERRORLEVEL%
