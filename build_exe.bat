@echo off
title Build Nexus Finance.exe
cd /d "%~dp0"

echo ========================================
echo   Building Nexus Finance (PyInstaller)
echo ========================================

if not exist "venv\Scripts\python.exe" (
    echo ERROR: venv not found. Create it first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Installing / updating build tools...
pip install -q pyinstaller

echo.
echo Running PyInstaller...
pyinstaller nexus_finance.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo BUILD FAILED.
    pause
    exit /b 1
)

if exist "data" (
    echo Copying existing database to dist folder...
    if not exist "dist\Nexus Finance\data" mkdir "dist\Nexus Finance\data"
    xcopy /E /I /Y "data\*" "dist\Nexus Finance\data\" >nul
)

echo.
echo ========================================
echo   Build complete!
echo ========================================
echo.
echo   App folder:  dist\Nexus Finance\
echo   Run:         dist\Nexus Finance\Nexus Finance.exe
echo.
echo   Your database is stored next to the .exe:
echo   dist\Nexus Finance\data\finance.db
echo.
echo   Tip: Copy the whole "Nexus Finance" folder to Desktop or USB.
echo.
pause
