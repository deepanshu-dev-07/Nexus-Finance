@echo off
title Nexus Finance - Money Tracker
cd /d "%~dp0"

if exist "dist\Nexus Finance\Nexus Finance.exe" (
    start "" "dist\Nexus Finance\Nexus Finance.exe"
    exit /b 0
)

if exist "Nexus Finance.exe" (
    start "" "Nexus Finance.exe"
    exit /b 0
)

echo Nexus Finance.exe not found.
echo.
echo Build it first: double-click build_exe.bat
echo Or run from source: Run Finance Tracker.bat
echo.
pause
