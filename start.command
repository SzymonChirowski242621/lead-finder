#!/bin/bash

# Move to the script's directory (Crucial for macOS double-clicking)
cd "$(dirname "$0")"

echo "========================================================"
echo "  ROBOTIC INTERN - LEAD FINDER (MacOS)"
echo "  (First run will take 1-2 minutes to install)"
echo "========================================================"
echo ""

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo "Please install Python from python.org or using 'brew install python'"
    read -n 1 -s -r -p "Press any key to exit..."
    exit 1
fi

# 2. Create private environment if missing
if [ ! -d ".venv_runtime" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv .venv_runtime
fi

# 3. Activate Environment
source .venv_runtime/bin/activate

# 4. Install Libraries (only if missing)
if [ ! -f ".venv_runtime/installed.marker" ]; then
    echo "[SETUP] Installing libraries from requirements.txt..."

    # Upgrade pip just in case
    pip install --upgrade pip > /dev/null 2>&1

    pip install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo "[ERROR] Installation failed."
        echo "Try running 'xcode-select --install' in terminal if this persists."
        read -n 1 -s -r -p "Press any key to exit..."
        exit 1
    fi
    touch .venv_runtime/installed.marker
fi

# 5. Run the App
clear
echo "[RUNNING] Starting GUI..."
# Tkinter on Mac sometimes has issues with dark mode, but standard python works fine.
python src/gui.py

# Keep window open on crash
if [ $? -ne 0 ]; then
    echo ""
    echo "[CRASH] Application closed with an error."
    read -n 1 -s -r -p "Press any key to exit..."
fi
