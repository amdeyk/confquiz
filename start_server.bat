@echo off
echo ========================================
echo Quiz System - Server Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo [2/3] Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Redis server is not running
    echo Please start Redis server in another terminal:
    echo    redis-server
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

echo [3/3] Starting Quiz System...
echo.
echo Server will start on http://localhost:8000
echo.
echo Access points:
echo  - Landing Page: http://localhost:8000
echo  - Admin Login:  http://localhost:8000/admin/login
echo  - Team Login:   http://localhost:8000/team/login
echo  - Main Display: http://localhost:8000/display
echo.
echo Default Admin Credentials:
echo  Username: admin
echo  Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
