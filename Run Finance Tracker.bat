@echo off
title Nexus Finance - Money Tracker

echo ========================================
echo    Starting Nexus Finance Tracker...
echo ========================================

:: Activate virtual environment and run the app
call venv\Scripts\activate.bat

echo Virtual Environment Activated.
echo Launching Application...

python main.py

pause