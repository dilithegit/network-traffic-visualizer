@echo off
REM CNS Project 1 - Windows Startup Script
REM This script sets up and runs the entire application on Windows

setlocal enabledelayedexpansion

cls
echo ==========================================
echo    CNS Project 1 - Network Analyzer
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Python is not installed or not in PATH
    echo [*] Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Node.js is not installed or not in PATH
    echo [*] Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Navigate to project root
cd /d "%~dp0\.."
echo [*] Project directory: %cd%

REM Backend Setup
echo [*] Setting up backend...
cd backend

REM Install dependencies
python -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo [*] Installing Python dependencies...
    python -m pip install -q -r ../requirements.txt
)

REM Database initialization
echo [*] Initializing database...
python -c "from database.db import init_db; init_db()"

REM Start backend in new window
echo [*] Starting backend API server...
start "CNS Backend" cmd /k python app.py
timeout /t 2 /nobreak

REM Frontend Setup
cd ..\frontend

REM Install npm dependencies
if not exist node_modules (
    echo [*] Installing npm dependencies...
    call npm install --quiet
)

REM Start frontend in new window
echo [*] Starting frontend dev server...
start "CNS Frontend" cmd /k npm run dev

echo.
echo ==========================================
echo    ^✅ Application Started Successfully
echo ==========================================
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://127.0.0.1:5000
echo.
echo Check the opened command windows for output
echo.
pause
