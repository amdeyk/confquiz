#!/bin/bash
# Quick test runner for Linux/Mac
# Usage: ./run_tests.sh [options]
# Example: ./run_tests.sh --url http://192.168.1.100:8000

echo ""
echo "========================================"
echo "Quiz Application Test Runner"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if test dependencies are installed
echo "Checking test dependencies..."
python3 -c "import requests, websocket, colorama" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing test dependencies..."
    pip3 install -r test_requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "Starting tests..."
echo ""

# Run tests with any provided arguments
python3 test_all_endpoints.py "$@"

# Exit with test result code
exit $?
