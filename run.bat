@echo off
setlocal enabledelayedexpansion

echo.
echo ====================================
echo   AI Stock Bestie
echo ====================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version

if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --quiet --upgrade pip

echo [INFO] Installing dependencies...
python -m pip install --quiet --upgrade -r requirements.txt

echo.
echo [SUCCESS] Setup complete!
echo [INFO] Starting application...
echo.

streamlit run src\app.py
