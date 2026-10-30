"""
FloatChat - 24/7 Standalone Keep-Alive & Anti-Sleep Utility
Continuously pings the local and cloud deployments to ensure 100% uptime and prevent sleeping.
"""

import time
import sys
import os
import urllib.request
import urllib.error

# Ensure Windows terminal doesn't crash on emoji or Unicode characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Windows Anti-Sleep Guard
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

def lock_system_awake():
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED | ES_AWAYMODE_REQUIRED
            )
            print("🛡️ Windows Anti-Sleep Shield: Active (System & Display Sleep Blocked)")
        except Exception as e:
            print(f"Note on power lock: {e}")

def ping(url: str, timeout: float = 8.0) -> bool:
    try:
        import httpx
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 FloatChat-KeepAlive/2.0"})
            return resp.status_code in (200, 304)
    except Exception:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 FloatChat-KeepAlive/2.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status in (200, 304)
        except Exception:
            return False

def main():
    cloud_url = "https://floatchat-argo-ocean-t7cjszmnhgb34rt6jnpgvz.streamlit.app/"
    local_backend = "http://127.0.0.1:8000/health"
    local_frontend = "http://127.0.0.1:8501/_stcore/health"

    print("=" * 65)
    print("  🌊 FloatChat 24/7 Keep-Alive & Anti-Sleep Watchdog")
    print("  Keeping Local & Streamlit Cloud Deployments Permanently Awake")
    print("=" * 65)
    lock_system_awake()
    print(f"Monitoring:\n  1. Cloud:   {cloud_url}\n  2. Backend: {local_backend}\n  3. Web UI:  {local_frontend}\n")
    print("Press CTRL+C to stop.\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            now = time.strftime("%Y-%m-%d %H:%M:%S")

            cloud_ok = ping(cloud_url)
            backend_ok = ping(local_backend)
            frontend_ok = ping(local_frontend)

            c_badge = "🟢 AWAKE" if cloud_ok else "⏳ SLEEPING / TIMED OUT"
            b_badge = "🟢 ONLINE" if backend_ok else "⚪ OFFLINE (Local)"
            f_badge = "🟢 ONLINE" if frontend_ok else "⚪ OFFLINE (Local)"

            print(f"[{now}] Ping #{iteration:04d} -> Cloud: {c_badge} | Backend: {b_badge} | Frontend: {f_badge}", flush=True)
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nKeep-Alive Watchdog stopped cleanly.")

if __name__ == "__main__":
    main()
