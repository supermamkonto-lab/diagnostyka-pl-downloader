@echo off
chcp 65001 >nul 2>&1
cls
title Medical Data Collector

cd /d "%~dp0"

echo.
echo ========================================
echo   Medical Data Collector - Menu
echo ========================================
echo.

python.exe --version >nul 2>&1
if errorlevel 1 (
    echo BLAD: Python nie znaleziony!
    echo.
    pause
    exit /b 1
)

python.exe menu.py
pause
