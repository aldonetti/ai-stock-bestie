#!/usr/bin/env bash
set -euo pipefail

echo "===================="
echo "  AI Stock Bestie"
echo "===================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[INFO] Python version: $(python3 --version)"

if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Upgrading pip..."
pip install --quiet --upgrade pip

echo "[INFO] Installing dependencies..."
pip install --quiet --upgrade -r requirements.txt

echo ""
echo "[SUCCESS] Setup complete!"
echo "[INFO] Starting application..."
echo ""

streamlit run src/app.py
