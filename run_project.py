"""
FloatChat - ARGO Ocean Data Discovery & Visualization Platform
Unified Startup Launcher for Backend (FastAPI + MCP) and Frontend (Streamlit)
"""

import subprocess
import sys
import time
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def start_services():
    print("=" * 65)
    print("  🌊 FloatChat - Autonomous Ocean Intelligence Platform Launch  ")
    print("  Enterprise Deep-Ocean Telemetry & AI Analytics Engine  ")
    print("=" * 65)

    # 1. Start FastAPI + MCP Server
    print("\n[1/2] Starting Backend MCP Server on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT_DIR, "backend", "main.py")],
        cwd=ROOT_DIR
    )

    # Wait for backend to initialize
    time.sleep(3)

    # 2. Start Streamlit Frontend
    print("[2/2] Starting Frontend UI on http://localhost:8501...")
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", os.path.join(ROOT_DIR, "frontend", "main.py"), "--server.port", "8501"],
        cwd=ROOT_DIR
    )

    print("\n" + "=" * 65)
    print("  ✅ All Services Running Successfully!")
    print("  • Frontend UI:    http://localhost:8501 (Demo: admin / admin)")
    print("  • Backend MCP:   http://localhost:8000")
    print("  • SQLite DB:     backend/argo.db")
    print("  Press CTRL+C to terminate both services.")
    print("=" * 65 + "\n")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    start_services()
