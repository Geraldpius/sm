@echo off
title Uganda School Management System
color 1F
echo.
echo  ============================================
echo   UGANDA SCHOOL MANAGEMENT SYSTEM
echo  ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "venv\Scripts\activate.bat" (
    echo  [SETUP] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo  [SETUP] Installing dependencies...
    pip install -r requirements.txt -q
) else (
    call venv\Scripts\activate.bat
)

REM Run migrations
echo  [DB] Running migrations...
python manage.py migrate --run-syncdb -q

REM Check if setup has been run
python -c "import django; django.setup(); from apps.core.models import SchoolSettings; s=SchoolSettings.objects.first(); exit(0 if s else 1)" 2>nul
if errorlevel 1 (
    echo  [SETUP] Running first-time setup...
    python setup.py
)

REM Start server
echo.
echo  [OK] Starting server at http://127.0.0.1:8000/
echo  [OK] Press Ctrl+C to stop.
echo.
start "" http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000

pause
