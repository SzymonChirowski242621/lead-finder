@echo off
title Lead Finder - Initializing...
echo ========================================================
echo   ROBOTIC INTERN - LEAD FINDER
echo   (First run will take 1-2 minutes to install)
echo ========================================================
echo.

REM 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found!
    echo Please install Python from python.org (checked "Add to PATH")
    pause
    exit /b
)

REM 2. Create private environment if missing
if not exist ".venv_runtime" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv_runtime
)

REM 3. Activate and Install
call .venv_runtime\Scripts\activate

REM Only install if we haven't before (checks for a marker file)
if not exist ".venv_runtime\installed.marker" (
    echo [SETUP] Installing libraries from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Installation failed.
        pause
        exit /b
    )
    echo done > .venv_runtime\installed.marker
)

REM 4. Run the App
cls
echo [RUNNING] Starting GUI...
python src/gui.py

REM Keep open only on crash
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Application closed with an error.
    pause
)
