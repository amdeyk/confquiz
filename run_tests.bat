@echo off
REM Quick test runner for Windows
REM Usage: run_tests.bat

echo.
echo ========================================
echo Quiz Application Test Runner
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if test dependencies are installed
echo Checking test dependencies...
python -c "import requests, websocket, colorama" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing test dependencies...
    pip install -r test_requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting tests...
echo.

REM Run tests
python test_all_endpoints.py %*

REM Pause to see results
echo.
pause
