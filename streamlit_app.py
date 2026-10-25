# FloatChat: Autonomous ARGO Ocean Intelligence & Telemetry Platform
# Streamlit Community Cloud Root Entrypoint

import sys
import os

# Add frontend and backend to sys.path
root_dir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(root_dir, "frontend")
backend_dir = os.path.join(root_dir, "backend")

if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from frontend.chatbot import ArgoApp

if __name__ == "__main__":
    app = ArgoApp()
    app.run()
