@echo off
REM Medical Data Collector GUI Launcher — Windows
REM This script launches the desktop application

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Medical Data Collector - GUI Application (Windows)
echo ============================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set APP_ROOT=%SCRIPT_DIR%..

REM Change to app root directory
cd /d "%APP_ROOT%"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Run the GUI application
echo Starting GUI application...
echo.
python gui_app.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start GUI application
    echo Please check that all dependencies are installed:
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

endlocal
