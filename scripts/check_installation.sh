#!/bin/bash
# Installation Verification Script
# Checks if all dependencies are installed

echo "=========================================="
echo "  CNS Project 1 - Installation Checker"
echo "=========================================="
echo ""

# Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo "✗ NOT FOUND"
    echo "  Install from: https://www.python.org/downloads/"
fi

# Check Python packages
echo -n "Checking Python packages... "
python3 -c "import flask, flask_cors, scapy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All packages installed"
else
    echo "✗ Missing packages"
    echo "  Run: pip install -r requirements.txt"
fi

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Found: $NODE_VERSION"
else
    echo "✗ NOT FOUND"
    echo "  Install from: https://nodejs.org/"
fi

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ Found: $NPM_VERSION"
else
    echo "✗ NOT FOUND"
fi

# Check Node modules
echo -n "Checking Node modules... "
if [ -d "frontend/node_modules" ]; then
    echo "✓ Installed"
else
    echo "✗ Not installed"
    echo "  Run: cd frontend && npm install"
fi

# Check ports
echo -n "Checking port 5000... "
if ! nc -z localhost 5000 2>/dev/null; then
    echo "✓ Available"
else
    echo "✗ In use"
fi

echo -n "Checking port 5173... "
if ! nc -z localhost 5173 2>/dev/null; then
    echo "✓ Available"
else
    echo "✗ In use"
fi

echo ""
echo "=========================================="
echo "  ✅ Installation check complete!"
echo "=========================================="
