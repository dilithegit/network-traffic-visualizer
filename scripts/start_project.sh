#!/bin/bash

# CNS Project 1 - Complete Startup Script
# This script sets up and runs the entire application

set -e

echo "=========================================="
echo "   CNS Project 1 - Network Analyzer"
echo "=========================================="

# Check if running as admin (for packet capture)
if [[ $EUID -ne 0 ]]; then
   echo "[!] WARNING: This script should ideally be run with sudo for network packet capture"
   echo "[*] Continuing anyway... (limited capture possible)"
fi

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Backend Setup
echo "[*] Setting up backend..."
cd backend

# Install dependencies if not already installed
if ! python3 -m pip show flask &> /dev/null; then
    echo "[*] Installing Python dependencies..."
    python3 -m pip install -q -r ../requirements.txt
fi

# Database initialization
echo "[*] Initializing database..."
python3 -c "from database.db import init_db; init_db()"

# Start backend in background
echo "[*] Starting backend API server..."
python3 app.py &
BACKEND_PID=$!
sleep 2

# Frontend Setup
echo "[*] Setting up frontend..."
cd ../frontend

# Install npm dependencies if not already installed
if [ ! -d "node_modules" ]; then
    echo "[*] Installing npm dependencies..."
    npm install --quiet
fi

# Start frontend dev server
echo "[*] Starting frontend dev server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "   ✅ Application Started Successfully"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend API: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
