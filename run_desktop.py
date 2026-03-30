"""
run_desktop.py — Launch the School Management System as a Desktop Application

Requirements:
    pip install pywebview

Usage:
    python run_desktop.py
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser

# ── Configuration ────────────────────────────────────────────
PORT = 8765
URL  = f"http://127.0.0.1:{PORT}/"
BASE = os.path.dirname(os.path.abspath(__file__))


def start_django_server():
    """Start the Django development server in background."""
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'school_mgmt.settings'
    subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{PORT}', '--noreload'],
        cwd=BASE,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_server(timeout=15):
    """Block until Django is ready."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def launch_pywebview():
    """Open as a native desktop window using pywebview."""
    try:
        import webview
        window = webview.create_window(
            'School Management System',
            URL,
            width=1400,
            height=900,
            min_size=(900, 600),
            resizable=True,
        )
        webview.start(debug=False)
    except ImportError:
        print("[!] pywebview not installed. Falling back to browser.")
        print("    Install with:  pip install pywebview")
        webbrowser.open(URL)
        input("Press ENTER to stop the server...")


if __name__ == '__main__':
    print("Starting School Management System...")
    print(f"Server URL: {URL}")

    # Start Django in background thread
    server_thread = threading.Thread(target=start_django_server, daemon=True)
    server_thread.start()

    print("Waiting for server to be ready...")
    ready = wait_for_server(timeout=20)

    if not ready:
        print("[!] Server did not start in time. Opening browser anyway...")

    launch_pywebview()
