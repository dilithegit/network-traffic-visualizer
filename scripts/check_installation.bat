@echo off
REM Installation Verification Script for Windows

setlocal enabledelayedexpansion

cls
echo ==========================================
echo   CNS Project 1 - Installation Checker
echo ==========================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python NOT FOUND
    echo     Install from: https://www.python.org/downloads/
) else (
    python --version
    echo [✓] Python installed
)

REM Check Python packages
echo.
echo Checking Python packages...
python -c "import flask, flask_cors, scapy" >nul 2>&1
if errorlevel 1 (
    echo [X] Missing packages
    echo     Run: pip install -r requirements.txt
) else (
    echo [✓] All packages installed
)

REM Check Node.js
echo.
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [X] Node.js NOT FOUND
    echo     Install from: https://nodejs.org/
) else (
    node --version
    echo [✓] Node.js installed
)

REM Check npm
echo.
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [X] npm NOT FOUND
) else (
    npm --version
    echo [✓] npm installed
)

REM Check Node modules
echo.
echo Checking Node modules...
if exist "frontend\node_modules" (
    echo [✓] Installed
) else (
    echo [X] Not installed
    echo     Run: cd frontend ^&^& npm install
)

echo.
echo ==========================================
echo   ✓ Installation check complete!
echo ==========================================
echo.
pause
