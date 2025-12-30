#!/bin/bash

echo "========================================"
echo "Quiz System - Server Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "[1/3] Checking dependencies..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "[2/3] Checking Redis connection..."
if ! redis-cli ping &> /dev/null; then
    echo "WARNING: Redis server is not running"
    echo "Please start Redis server in another terminal:"
    echo "   redis-server"
    echo ""
    echo "Press any key to continue anyway..."
    read -n 1 -s
fi

echo "[3/3] Starting Quiz System..."
echo ""
echo "Server will start on http://localhost:8000"
echo ""
echo "Access points:"
echo "  - Landing Page: http://localhost:8000"
echo "  - Admin Login:  http://localhost:8000/admin/login"
echo "  - Team Login:   http://localhost:8000/team/login"
echo "  - Main Display: http://localhost:8000/display"
echo ""
echo "Default Admin Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
