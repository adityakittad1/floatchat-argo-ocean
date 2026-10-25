import os
import sys

_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _FRONTEND_DIR not in sys.path:
    sys.path.insert(0, _FRONTEND_DIR)

from chatbot import ArgoApp

if __name__ == "__main__":
    app = ArgoApp()
    app.run()