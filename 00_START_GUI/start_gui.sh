#!/bin/bash
# Medical Data Collector GUI Launcher — Linux/macOS
# This script launches the desktop application

echo ""
echo "============================================================"
echo "Medical Data Collector - GUI Application (Linux/macOS)"
echo "============================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to app root directory
cd "$APP_ROOT" || exit 1

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.9+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  macOS: brew install python3"
    exit 1
fi

# Run the GUI application
echo "Starting GUI application..."
echo ""
python3 gui_app.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start GUI application (exit code: $EXIT_CODE)"
    echo "Please check that all dependencies are installed:"
    echo "  pip install -r requirements.txt"
    exit 1
fi
