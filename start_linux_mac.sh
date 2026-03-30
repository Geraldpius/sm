#!/bin/bash
# ============================================================
#  UGANDA SCHOOL MANAGEMENT SYSTEM — Startup Script
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " ============================================"
echo "  UGANDA SCHOOL MANAGEMENT SYSTEM"
echo " ============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python 3 is not installed."
    echo " Install it with: sudo apt install python3 python3-pip  (Ubuntu/Debian)"
    exit 1
fi

# Virtual environment
if [ ! -d "venv" ]; then
    echo " [SETUP] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo " [SETUP] Checking dependencies..."
pip install -r requirements.txt -q

# Migrations
echo " [DB] Running migrations..."
python manage.py migrate --run-syncdb -q 2>/dev/null

# First-time setup
SETUP_CHECK=$(python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','school_mgmt.settings')
django.setup()
from apps.core.models import SchoolSettings
print('done' if SchoolSettings.objects.exists() else 'needed')
" 2>/dev/null)

if [ "$SETUP_CHECK" = "needed" ]; then
    echo " [SETUP] Running first-time setup..."
    python setup.py
fi

PORT=${1:-8000}
echo ""
echo " [OK] Starting server at http://127.0.0.1:${PORT}/"
echo " [OK] Press Ctrl+C to stop."
echo ""

# Open browser (optional)
if command -v xdg-open &>/dev/null; then
    sleep 1.5 && xdg-open "http://127.0.0.1:${PORT}/" &
elif command -v open &>/dev/null; then
    sleep 1.5 && open "http://127.0.0.1:${PORT}/" &
fi

python manage.py runserver "127.0.0.1:${PORT}"
