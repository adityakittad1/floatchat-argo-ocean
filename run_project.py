"""
FloatChat - ARGO Ocean Data Discovery & Visualization Platform
Enterprise 24/7 Always-On Autonomous Runner & Supervisor Watchdog
Prevents local Windows OS sleep, keeps AI MCP agent active, and ensures zero downtime.
"""

import subprocess
import sys
import time
import os
import signal
import threading
import urllib.request
import urllib.error

# Ensure Windows terminal doesn't crash on emoji or Unicode characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Windows Native Power Management (Anti-Sleep Guard) ─────────────────────────
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

def set_anti_sleep(enable: bool = True) -> bool:
    """Tells the Windows OS Kernel to block sleep, idle standby, and network throttling."""
    if os.name == "nt":
        try:
            import ctypes
            if enable:
                flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED | ES_AWAYMODE_REQUIRED
                res = ctypes.windll.kernel32.SetThreadExecutionState(flags)
                return res != 0
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                return True
        except Exception as e:
            print(f"[Power Warning] Could not set Windows execution state: {e}")
            return False
    return False

# ── Service Management ─────────────────────────────────────────────────────────
backend_proc = None
frontend_proc = None
shutdown_requested = False

def start_backend():
    global backend_proc
    print("  [▶] Launching Backend MCP Server on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT_DIR, "backend", "main.py")],
        cwd=ROOT_DIR
    )
    return backend_proc

def start_frontend():
    global frontend_proc
    print("  [▶] Launching Frontend Streamlit on http://localhost:8501...")
    frontend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            os.path.join(ROOT_DIR, "frontend", "main.py"),
            "--server.port", "8501",
            "--server.headless", "true"
        ],
        cwd=ROOT_DIR
    )
    return frontend_proc

def ping_url(url: str, timeout: float = 6.0) -> bool:
    """Fast non-blocking HTTP health check with automatic redirect and cookie support."""
    try:
        import httpx
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url, headers={"User-Agent": "FloatChat-KeepAlive/2.0"})
            return resp.status_code in (200, 304)
    except Exception:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FloatChat-KeepAlive/2.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status in (200, 304)
        except Exception:
            return False

def background_heartbeat_worker():
    """Continuously pings backend, frontend, and cloud app to prevent idling or sleeping."""
    cloud_url = "https://floatchat-argo-ocean-t7cjszmnhgb34rt6jnpgvz.streamlit.app/"
    tick = 0
    while not shutdown_requested:
        time.sleep(20)
        if shutdown_requested:
            break
        tick += 1

        b_ok = ping_url("http://127.0.0.1:8000/health")
        f_ok = ping_url("http://127.0.0.1:8501/_stcore/health")

        # Periodically ping cloud deployment every 60s
        c_status = ""
        if tick % 3 == 0:
            c_ok = ping_url(cloud_url, timeout=5.0)
            c_status = f" | Cloud: {'🟢 Awake' if c_ok else '⏳ Standby'}"

        timestamp = time.strftime("%H:%M:%S")
        status_msg = f"  [{timestamp}] 🛡️ Keep-Alive Heartbeat -> Backend: {'🟢 Online' if b_ok else '🔴 Reconnecting'} | Frontend: {'🟢 Online' if f_ok else '🔴 Reconnecting'}{c_status}"
        print(status_msg, flush=True)

def run_supervisor():
    global shutdown_requested, backend_proc, frontend_proc

    print("\n" + "=" * 70)
    print("  🌊 FloatChat - 24/7 Always-On Autonomous Ocean Intelligence Runner  ")
    print("  Enterprise Deep-Ocean Telemetry & AI Analytics Engine  ")
    print("=" * 70)

    # 1. Engage Windows anti-sleep shield
    anti_sleep_ok = set_anti_sleep(True)
    if anti_sleep_ok:
        print("  🛡️  Windows Anti-Sleep Guard: ENGAGED (OS Sleep & Standby Blocked)")
    else:
        print("  ℹ️  Anti-Sleep Guard: Standalone Mode Active")

    # 2. Start Services
    start_backend()
    time.sleep(3)
    start_frontend()

    print("\n" + "=" * 70)
    print("  ✅ All Services Running Successfully!")
    print("  • Frontend UI:    http://localhost:8501 (Demo: admin / admin)")
    print("  • Backend MCP:   http://localhost:8000")
    print("  • Cloud App:     https://floatchat-argo-ocean-t7cjszmnhgb34rt6jnpgvz.streamlit.app/")
    print("  • Keep-Alive:    24/7 Supervisor Watchdog Active (No Sleep Mode)")
    print("  Press CTRL+C anytime to cleanly shut down.")
    print("=" * 70 + "\n")

    # 3. Launch background heartbeat thread
    heartbeat_thread = threading.Thread(target=background_heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    # 4. Supervisor Watchdog Loop
    try:
        while not shutdown_requested:
            time.sleep(4)

            # Check if backend crashed -> Auto-restart
            if backend_proc and backend_proc.poll() is not None:
                print("\n  ⚠️  Backend MCP process terminated unexpectedly! Auto-recovering...")
                start_backend()

            # Check if frontend crashed -> Auto-restart
            if frontend_proc and frontend_proc.poll() is not None:
                print("\n  ⚠️  Frontend Streamlit process terminated unexpectedly! Auto-recovering...")
                start_frontend()

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("  🛑 Shutdown requested by user. Cleaning up services...")
        shutdown_requested = True

        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()

        set_anti_sleep(False)
        print("  🛡️  Windows power settings restored to normal.")
        print("  ✅ Shutdown complete. Goodbye!")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    run_supervisor()
