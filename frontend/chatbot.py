import streamlit as st
import streamlit.components.v1 as components
import httpx
import asyncio
import time
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import uuid
from datetime import datetime
import numpy as np
import base64
import io
import os
import hashlib
import sqlite3

# Import NetCDF helper for realistic conversion & SQLite DB import
try:
    from netcdf_helper import parse_netcdf_and_generate_sql, import_sql_to_db
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from netcdf_helper import parse_netcdf_and_generate_sql, import_sql_to_db

# Plotly 6/7+ compatibility: Scattermap replaced Scattermapbox
ScatterMapTrace = getattr(go, "Scattermap", None) or getattr(go, "Scattermapbox", None)
MAP_LAYOUT_KEY = "map" if hasattr(go, "Scattermap") else "mapbox"


# ── Native Streamlit Modal Dialogs ─────────────────────────────────────────────
@st.dialog("🌊 ARGO Float Specifications")
def show_float_modal_dialog(title: str, content: str):
    st.markdown(f"### {title}")
    st.markdown(content, unsafe_allow_html=True)
    if st.button("Close Dialog", key="float_modal_close_btn", use_container_width=True):
        st.rerun()

@st.dialog("✅ ARGO Action Complete")
def show_info_modal_dialog(title: str, content: str):
    st.markdown(f"### {title}")
    st.markdown(content, unsafe_allow_html=True)
    if st.button("Close Dialog", key="info_modal_close_btn", use_container_width=True):
        st.rerun()

@st.dialog("📊 Database Table Inspector")
def show_table_preview_dialog(table_name: str, df: pd.DataFrame):
    st.subheader(f"Table: {table_name}")
    st.caption(f"Showing sample records • Total columns: {len(df.columns)}")
    st.dataframe(df, use_container_width=True)
    if st.button("Close Dialog", key="table_modal_close_btn", use_container_width=True):
        st.rerun()

@st.dialog("📚 Quick Start: How FloatChat Works")
def show_how_it_works_dialog():
    st.markdown(
        """
        ### 🌊 Welcome to FloatChat!
        **FloatChat** is an enterprise AI oceanographic intelligence platform designed for **Autonomous Deep-Ocean Observation & ARGO Telemetry** 
        to democratize access to global **ARGO oceanographic float data**.

        ---
        #### 🧭 4-Step Quick Tour:
        1. **💬 AI Ocean Chatbot**:
           Ask questions in natural language like *"Show salinity profiles near the equator"* or *"What is the average temperature?"*.
           The AI converts your question into SQL via **Model Context Protocol (MCP)** and queries live ocean databases.
        2. **🗺️ Geospatial Map**:
           Track active autonomous floats in the Indian Ocean, Arabian Sea, and Bay of Bengal. Inspect depth, salinity, and battery levels.
        3. **🔄 NetCDF Ingestion Engine**:
           Upload or sample complex scientific `.nc` (NetCDF) files. Our engine decodes them into clean relational SQL tables with 1 click.
        4. **🗄️ Database Hub & SQL Lab**:
           Inspect live SQLite tables (`profile`, `tech`, `trajectory`) or execute custom SQL queries directly.
        """
    )
    if st.button("Got It! Explore FloatChat", key="how_it_works_close_btn", use_container_width=True, type="primary"):
        st.rerun()


@st.dialog("👥 Project Developer Profiles & Academic Credentials")
def show_developer_profile_dialog(active_profile: str = "aditya"):
    st.markdown(
        """
        <div style="font-size: 0.84rem; color: #94a3b8; margin-bottom: 0.6rem;">
            Departmental Minor Project • B.Tech Final Year (Civil & Ocean Data Engineering)
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if active_profile == "ganesh":
        tab_list = ["🌊 GANESH KAPURE", "🚀 ADITYA KITTAD", "⚡ OM JAISWAL"]
    elif active_profile == "om":
        tab_list = ["⚡ OM JAISWAL", "🚀 ADITYA KITTAD", "🌊 GANESH KAPURE"]
    else:
        tab_list = ["🚀 ADITYA KITTAD", "🌊 GANESH KAPURE", "⚡ OM JAISWAL"]

    tabs = st.tabs(tab_list)

    def render_aditya(t):
        with t:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%), rgba(10, 18, 38, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 1.2rem; margin-bottom: 0.8rem;">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 0.8rem;">
                        <div style="width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8, #6366f1); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 800; color: #ffffff; box-shadow: 0 4px 15px rgba(56,189,248,0.4);">
                            AK
                        </div>
                        <div>
                            <h3 style="margin: 0; color: #ffffff; font-size: 1.25rem;">ADITYA KITTAD</h3>
                            <div style="color: #38bdf8; font-weight: 700; font-size: 0.88rem;">Lead Full-Stack Architect & AI Systems Engineer</div>
                            <div style="color: #94a3b8; font-size: 0.8rem;">B.Tech Final Year • Departmental Minor Project</div>
                        </div>
                    </div>
                    <div style="background: rgba(3, 7, 18, 0.55); border-radius: 10px; padding: 0.9rem; margin-bottom: 0.8rem; border-left: 3px solid #38bdf8;">
                        <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.6;">
                            <b style="color: #38bdf8;">Core Project Responsibilities:</b><br>
                            • Architected the <b>Model Context Protocol (MCP)</b> multi-tool agent backend.<br>
                            • Designed conversational AI Natural Language to SQL generation engine.<br>
                            • Engineered SQLite relational database schema and real-time telemetry indexing.<br>
                            • Built the glassmorphic Obsidian UI design system with responsive state management.
                        </div>
                    </div>
                    <div style="margin-bottom: 0.8rem;">
                        <div style="font-size: 0.74rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Technical Competencies:</div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span style="background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">FastAPI & MCP</span>
                            <span style="background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Streamlit</span>
                            <span style="background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">SQL & SQLite</span>
                            <span style="background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">AI Orchestration</span>
                            <span style="background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Full-Stack Architecture</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08);">
                        <span style="font-size: 0.73rem; color: #64748b;">Instant in-app preview verified</span>
                        <a href="https://www.linkedin.com/in/aditya-kittad-bbb9532ba/" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; background: #0a66c2; color: #ffffff; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.78rem; font-weight: 700;">
                            Open External LinkedIn ↗
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    def render_ganesh(t):
        with t:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%), rgba(10, 18, 38, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 1.2rem; margin-bottom: 0.8rem;">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 0.8rem;">
                        <div style="width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #06b6d4, #3b82f6); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 800; color: #ffffff; box-shadow: 0 4px 15px rgba(6,182,212,0.4);">
                            GK
                        </div>
                        <div>
                            <h3 style="margin: 0; color: #ffffff; font-size: 1.25rem;">GANESH KAPURE</h3>
                            <div style="color: #38bdf8; font-weight: 700; font-size: 0.88rem;">Geospatial Systems & Data Ingestion Engineer</div>
                            <div style="color: #94a3b8; font-size: 0.8rem;">B.Tech Final Year • Departmental Minor Project</div>
                        </div>
                    </div>
                    <div style="background: rgba(3, 7, 18, 0.55); border-radius: 10px; padding: 0.9rem; margin-bottom: 0.8rem; border-left: 3px solid #06b6d4;">
                        <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.6;">
                            <b style="color: #06b6d4;">Core Project Responsibilities:</b><br>
                            • Developed interactive <b>Leaflet / Folium Geospatial Map</b> for ARGO float trajectory tracking.<br>
                            • Implemented binary <b>NetCDF (.nc) file ingestion</b> pipeline using xarray & netCDF4.<br>
                            • Automated conversion of multidimensional scientific arrays into structured SQL dumps.<br>
                            • Formulated geographic bounding-box spatial queries for the Indian Ocean and Arabian Sea.
                        </div>
                    </div>
                    <div style="margin-bottom: 0.8rem;">
                        <div style="font-size: 0.74rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Technical Competencies:</div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span style="background: rgba(6,182,212,0.15); color: #06b6d4; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">NetCDF4 & xarray</span>
                            <span style="background: rgba(6,182,212,0.15); color: #06b6d4; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Leaflet / Folium GIS</span>
                            <span style="background: rgba(6,182,212,0.15); color: #06b6d4; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Geospatial Analytics</span>
                            <span style="background: rgba(6,182,212,0.15); color: #06b6d4; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Data Ingestion Pipelines</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08);">
                        <span style="font-size: 0.73rem; color: #64748b;">Instant in-app preview verified</span>
                        <a href="https://www.linkedin.com/in/ganesh-kapure-5309542ba/" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; background: #0a66c2; color: #ffffff; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.78rem; font-weight: 700;">
                            Open External LinkedIn ↗
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    def render_om(t):
        with t:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%), rgba(10, 18, 38, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 1.2rem; margin-bottom: 0.8rem;">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 0.8rem;">
                        <div style="width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #818cf8, #a855f7); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 800; color: #ffffff; box-shadow: 0 4px 15px rgba(129,140,248,0.4);">
                            OJ
                        </div>
                        <div>
                            <h3 style="margin: 0; color: #ffffff; font-size: 1.25rem;">OM JAISWAL</h3>
                            <div style="color: #38bdf8; font-weight: 700; font-size: 0.88rem;">Oceanographic Data & CTD Telemetry Analyst</div>
                            <div style="color: #94a3b8; font-size: 0.8rem;">B.Tech Final Year • Departmental Minor Project</div>
                        </div>
                    </div>
                    <div style="background: rgba(3, 7, 18, 0.55); border-radius: 10px; padding: 0.9rem; margin-bottom: 0.8rem; border-left: 3px solid #818cf8;">
                        <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.6;">
                            <b style="color: #818cf8;">Core Project Responsibilities:</b><br>
                            • Formulated <b>Practical Salinity Scale 1978 (PSS-78)</b> & seawater equation of state models.<br>
                            • Engineered vertical <b>CTD In-Chat Profile Cast visualization</b> (Surface to 2,000 dbar).<br>
                            • Designed thermohaline circulation (AMOC) & sound velocity acoustic telemetry calculations.<br>
                            • Researched marine structure durability, chloride ingress, and coastal concrete corrosion impacts.
                        </div>
                    </div>
                    <div style="margin-bottom: 0.8rem;">
                        <div style="font-size: 0.74rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Technical Competencies:</div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span style="background: rgba(129,140,248,0.15); color: #818cf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">CTD Telemetry</span>
                            <span style="background: rgba(129,140,248,0.15); color: #818cf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Oceanographic Modeling</span>
                            <span style="background: rgba(129,140,248,0.15); color: #818cf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Acoustic Bathymetry</span>
                            <span style="background: rgba(129,140,248,0.15); color: #818cf8; font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; font-weight: 600;">Civil Marine Materials</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08);">
                        <span style="font-size: 0.73rem; color: #64748b;">Instant in-app preview verified</span>
                        <a href="https://www.linkedin.com/in/om-jaiswal-3b2b39249/" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; background: #0a66c2; color: #ffffff; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.78rem; font-weight: 700;">
                            Open External LinkedIn ↗
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    for i, name in enumerate(tab_list):
        if "ADITYA" in name:
            render_aditya(tabs[i])
        elif "GANESH" in name:
            render_ganesh(tabs[i])
        elif "OM" in name:
            render_om(tabs[i])

    st.caption("✨ Zero Login Required: Full technical dossiers and credentials rendered directly inside FloatChat.")
    if st.button("Close Dossier", key="dev_modal_close_btn", use_container_width=True):
        st.rerun()


class ArgoApp:

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.db_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "argo.db")
        )
        self._ensure_backend_running()

    def _ensure_backend_running(self):
        """Ensures FastAPI MCP backend is active; automatically starts and supervises it in a background thread if needed for 1-click cloud deployments (Streamlit Community Cloud / HuggingFace) or standalone execution."""
        if self.check_backend_health():
            return

        # Start backend in a background daemon thread
        import threading
        def _run_server():
            try:
                import uvicorn
                import sys
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
                from backend.main import app as fastapi_app
                uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
            except Exception:
                pass

        t = threading.Thread(target=_run_server, daemon=True)
        t.start()

    def inject_keep_alive(self):
        """Injects client-side keep-awake engine into the browser:
        1. Screen WakeLock API: Prevents user's OS and display from sleeping while FloatChat is open in browser.
        2. Heartbeat Ping: Periodically pings Streamlit health endpoint every 25s so WebSocket never drops or times out.
        """
        keep_alive_js = """
        <script>
        (function() {
            // 1. Keep OS & Screen awake via modern WakeLock API
            let wakeLock = null;
            async function requestWakeLock() {
                try {
                    if ('wakeLock' in navigator) {
                        wakeLock = await navigator.wakeLock.request('screen');
                    }
                } catch (err) {}
            }
            requestWakeLock();
            document.addEventListener('visibilitychange', () => {
                if (wakeLock !== null && document.visibilityState === 'visible') {
                    requestWakeLock();
                }
            });

            // 2. Active Session Heartbeat ping (every 25 seconds) to prevent WebSocket timeout
            if (!window._floatchatKeepAlive) {
                window._floatchatKeepAlive = setInterval(() => {
                    try {
                        fetch(window.location.origin + '/_stcore/health', { cache: 'no-store' }).catch(() => {});
                    } catch (e) {}
                }, 25000);
            }
        })();
        </script>
        """
        components.html(keep_alive_js, height=0, width=0)

    def _init_session_state(self):
        """Initializes and synchronizes all session state keys on every execution to ensure zero KeyErrors across any browser session, reload, or cloud deployment."""
        # Session Restoration from Query Params (Keeps user logged in on page reload)
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False
        if "username" not in st.session_state:
            st.session_state["username"] = ""

        params = st.query_params
        s_user = params.get("session_user")
        s_token = params.get("session_token")
        if s_user and s_token and not st.session_state.get("authenticated", False):
            expected_token = hashlib.sha256(f"{s_user}:argo_salt_2025".encode()).hexdigest()[:16]
            if s_token == expected_token:
                st.session_state["authenticated"] = True
                st.session_state["username"] = s_user

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "chats"

        if "messages" not in st.session_state:
            st.session_state["messages"] = []

        if "chats" not in st.session_state:
            st.session_state["chats"] = {}
        if "chat_titles" not in st.session_state:
            st.session_state["chat_titles"] = {}
        if "chat_counter" not in st.session_state:
            st.session_state["chat_counter"] = 1

        if "users_data" not in st.session_state:
            st.session_state["users_data"] = pd.DataFrame({
                "email": [
                    "admin@argo.com",
                    "analyst@argo.com",
                    "researcher@argo.com",
                    "oceanographer@argo.com",
                ],
                "password": ["admin123", "analyst123", "research123", "ocean123"],
                "status": ["active", "active", "active", "active"],
                "role": ["Administrator", "Analyst", "Researcher", "Scientist"],
                "last_login": ["Today", "Yesterday", "3 days ago", "1 week ago"]
            })

        # Set up active chat
        if st.session_state.get("authenticated", False):
            chat_id = params.get("chat_id")
            if not chat_id or chat_id not in st.session_state["chats"]:
                chat_id = str(uuid.uuid4())
                st.session_state["chats"][chat_id] = []
                st.session_state["chat_titles"][chat_id] = f"ARGO Inquiry #{st.session_state['chat_counter']}"
                st.session_state["chat_counter"] += 1
                st.query_params["chat_id"] = chat_id
            self.chat_id = chat_id
            self.messages = st.session_state["chats"][self.chat_id]
            st.session_state["messages"] = self.messages
        else:
            self.chat_id = "default"
            self.messages = st.session_state["messages"]

    def setup_custom_css(self):
        """Inject bespoke ultra-modern glassy and glossy UI theme with deep obsidian color grading"""
        st.markdown(
            """
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

            <style>
            /* 1. Global Reset & Luxury Typography */
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #e2e8f0;
            }
            h1, h2, h3, h4, .stTitle {
                font-family: 'Outfit', sans-serif;
                letter-spacing: -0.025em;
            }
            code, pre {
                font-family: 'JetBrains Mono', monospace !important;
            }

            /* 2. Deep Obsidian Luxury Canvas with Bioluminescent Mesh Glow */
            .stApp {
                background-color: #030712 !important;
                background-image: 
                    radial-gradient(ellipse 90% 60% at 15% -5%, rgba(14, 165, 233, 0.16) 0%, transparent 65%),
                    radial-gradient(ellipse 70% 50% at 85% 15%, rgba(99, 102, 241, 0.14) 0%, transparent 60%),
                    radial-gradient(ellipse 80% 60% at 50% 95%, rgba(6, 182, 212, 0.12) 0%, transparent 65%),
                    radial-gradient(ellipse 50% 40% at 92% 80%, rgba(16, 185, 129, 0.08) 0%, transparent 55%) !important;
                background-attachment: fixed !important;
                color: #f1f5f9;
            }

            /* Main Content Container */
            .main .block-container {
                padding-top: 1.8rem;
                padding-left: 2.2rem;
                padding-right: 2.2rem;
                max-width: 1380px;
            }

            /* Holographic Metallic Header Gradients */
            h1, .stTitle {
                background: linear-gradient(135deg, #ffffff 35%, #7dd3fc 80%, #c084fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800 !important;
                letter-spacing: -0.03em !important;
            }

            /* 3. Frosted Glass Sidebar with Specular Accent */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(8, 14, 30, 0.86) 0%, rgba(3, 7, 18, 0.95) 100%) !important;
                backdrop-filter: blur(28px) saturate(190%) !important;
                -webkit-backdrop-filter: blur(28px) saturate(190%) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.09) !important;
                box-shadow: 4px 0 35px rgba(0, 0, 0, 0.6) !important;
            }
            [data-testid="stSidebar"] .block-container {
                padding-top: 1.5rem;
                padding-left: 1.2rem;
                padding-right: 1.2rem;
            }

            /* 4. Ultra-Glossy Metric Cards with Top Specular Reflection */
            .stMetric {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(11, 20, 42, 0.68) !important;
                backdrop-filter: blur(20px) saturate(180%) !important;
                -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.38) !important;
                border-left: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 14px !important;
                padding: 1.1rem 1.3rem !important;
                box-shadow: 0 14px 35px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.25), inset 0 -1px 2px rgba(0, 0, 0, 0.3) !important;
                transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease !important;
            }
            .stMetric:hover {
                transform: translateY(-2px);
                border-color: rgba(56, 189, 248, 0.45) !important;
                border-top-color: rgba(255, 255, 255, 0.65) !important;
                box-shadow: 0 18px 45px rgba(14, 165, 233, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.4) !important;
            }
            [data-testid="stMetricValue"] {
                color: #ffffff !important;
                font-weight: 700 !important;
                font-family: 'Outfit', sans-serif !important;
            }
            [data-testid="stMetricLabel"] {
                color: #94a3b8 !important;
                font-size: 0.85rem !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* 5. Frosted Glass Info Banners */
            .info-banner {
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.14) 0%, rgba(99, 102, 241, 0.09) 100%), rgba(8, 16, 36, 0.72) !important;
                backdrop-filter: blur(20px) saturate(180%) !important;
                border: 1px solid rgba(56, 189, 248, 0.3) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.42) !important;
                border-left: 5px solid #38bdf8 !important;
                border-radius: 14px !important;
                padding: 1.2rem 1.6rem !important;
                margin-bottom: 1.5rem !important;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.22) !important;
            }
            .info-banner h4 {
                color: #38bdf8 !important;
                margin: 0 0 0.4rem 0 !important;
                font-size: 1.1rem !important;
                font-weight: 700 !important;
            }
            .info-banner p {
                color: #cbd5e1 !important;
                margin: 0 !important;
                font-size: 0.93rem !important;
                line-height: 1.6 !important;
            }

            /* 6. Glossy Sensor & Float Cards */
            .sensor-card {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(11, 20, 42, 0.72) !important;
                backdrop-filter: blur(18px) saturate(180%) !important;
                padding: 1.1rem 1.3rem !important;
                color: #ffffff !important;
                border-radius: 12px !important;
                margin: 0.5rem 0 !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.35) !important;
                border-left: 4px solid #06b6d4 !important;
                box-shadow: 0 10px 28px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
                transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            .sensor-card:hover {
                transform: translateY(-3px) scale(1.006) !important;
                border-color: rgba(56, 189, 248, 0.55) !important;
                border-top-color: rgba(255, 255, 255, 0.75) !important;
                box-shadow: 0 16px 36px rgba(6, 182, 212, 0.28), inset 0 1px 2px rgba(255, 255, 255, 0.4) !important;
            }

            /* Status Badges */
            .status-active {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: rgba(16, 185, 129, 0.14);
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-top: 1px solid rgba(255, 255, 255, 0.4);
                color: #34d399;
                font-weight: 700;
                font-size: 0.8rem;
                padding: 2px 10px;
                border-radius: 9999px;
                box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2), inset 0 1px 1px rgba(255,255,255,0.2);
            }
            .status-delayed {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: rgba(245, 158, 11, 0.14);
                border: 1px solid rgba(245, 158, 11, 0.35);
                border-top: 1px solid rgba(255, 255, 255, 0.4);
                color: #fbbf24;
                font-weight: 700;
                font-size: 0.8rem;
                padding: 2px 10px;
                border-radius: 9999px;
                box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2), inset 0 1px 1px rgba(255,255,255,0.2);
            }
            .status-inactive {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: rgba(239, 68, 68, 0.14);
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-top: 1px solid rgba(255, 255, 255, 0.4);
                color: #f87171;
                font-weight: 700;
                font-size: 0.8rem;
                padding: 2px 10px;
                border-radius: 9999px;
                box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2), inset 0 1px 1px rgba(255,255,255,0.2);
            }

            /* 7. Glossy 3D Buttons (Liquid Luster) */
            .stButton > button {
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.03) 50%, rgba(0, 0, 0, 0.18) 100%), rgba(16, 28, 56, 0.82) !important;
                backdrop-filter: blur(14px) !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                font-size: 0.92rem !important;
                color: #f1f5f9 !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.42) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.28) !important;
                transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                background: linear-gradient(180deg, rgba(56, 189, 248, 0.26) 0%, rgba(14, 165, 233, 0.14) 100%), rgba(19, 36, 74, 0.92) !important;
                border-color: rgba(56, 189, 248, 0.6) !important;
                border-top-color: rgba(255, 255, 255, 0.8) !important;
                box-shadow: 0 8px 25px rgba(14, 165, 233, 0.38), inset 0 1px 2px rgba(255, 255, 255, 0.45) !important;
                color: #ffffff !important;
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(180deg, #38bdf8 0%, #0284c7 60%, #0369a1 100%) !important;
                border: 1px solid #7dd3fc !important;
                border-top: 1px solid #ffffff !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4) !important;
                box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.65), inset 0 -2px 4px rgba(0, 0, 0, 0.3) !important;
            }
            .stButton > button[kind="primary"]:hover {
                transform: translateY(-2px) scale(1.01) !important;
                box-shadow: 0 10px 30px rgba(14, 165, 233, 0.7), inset 0 1px 2px #ffffff !important;
            }

            /* 8. Glossy Chat Bubbles */
            [data-testid="stChatMessage"] {
                border-radius: 14px !important;
                padding: 1.1rem !important;
                margin-bottom: 0.9rem !important;
                backdrop-filter: blur(18px) saturate(180%) !important;
                transition: transform 0.2s ease !important;
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.18) 0%, rgba(99, 102, 241, 0.14) 100%), rgba(10, 20, 48, 0.72) !important;
                border: 1px solid rgba(56, 189, 248, 0.32) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.45) !important;
                box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.3) !important;
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(12, 19, 38, 0.78) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.32) !important;
                box-shadow: 0 10px 32px rgba(0, 0, 0, 0.42), inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
            }

            /* 9. Floating Glass Chat Input */
            [data-testid="stChatInput"] {
                background: rgba(8, 15, 32, 0.85) !important;
                border: 1px solid rgba(56, 189, 248, 0.32) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.45) !important;
                border-radius: 14px !important;
                backdrop-filter: blur(20px) !important;
                box-shadow: 0 14px 40px rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.22) !important;
            }

            /* 10. Form Controls (Inputs, Selectboxes, Sliders) */
            div[data-baseweb="input"] > div,
            div[data-baseweb="select"] > div,
            .stTextInput input, .stTextArea textarea {
                background: rgba(8, 15, 32, 0.72) !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
                border-radius: 10px !important;
                color: #f8fafc !important;
                backdrop-filter: blur(14px) !important;
                box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.45), 0 2px 8px rgba(0, 0, 0, 0.2) !important;
            }
            div[data-baseweb="input"]:focus-within > div,
            div[data-baseweb="select"]:focus-within > div,
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #38bdf8 !important;
                border-top-color: #7dd3fc !important;
                box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.35), inset 0 2px 5px rgba(0, 0, 0, 0.45) !important;
            }

            /* 11. Glass Tabs & Expanders */
            [data-baseweb="tab-list"] {
                background: rgba(8, 15, 32, 0.65) !important;
                border-radius: 12px !important;
                padding: 4px !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.22) !important;
            }
            [data-baseweb="tab"] {
                border-radius: 8px !important;
                color: #94a3b8 !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
            }
            [aria-selected="true"][data-baseweb="tab"] {
                background: linear-gradient(180deg, rgba(56, 189, 248, 0.25) 0%, rgba(14, 165, 233, 0.12) 100%) !important;
                color: #ffffff !important;
                border: 1px solid rgba(56, 189, 248, 0.4) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
                box-shadow: 0 4px 15px rgba(14, 165, 233, 0.25) !important;
            }
            .streamlit-expanderHeader {
                background: rgba(12, 22, 45, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
                border-radius: 12px !important;
                backdrop-filter: blur(14px) !important;
            }

            /* 12. Glass Dialog Modals */
            [role="dialog"] {
                background: linear-gradient(135deg, rgba(13, 22, 45, 0.96) 0%, rgba(5, 10, 24, 0.98) 100%) !important;
                backdrop-filter: blur(32px) saturate(190%) !important;
                border: 1px solid rgba(56, 189, 248, 0.3) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
                border-radius: 20px !important;
                box-shadow: 0 25px 70px rgba(0, 0, 0, 0.85), inset 0 1px 2px rgba(255, 255, 255, 0.35) !important;
                color: #f8fafc !important;
            }

            /* 13. Dataframes */
            [data-testid="stDataFrame"] {
                background: rgba(8, 15, 32, 0.5) !important;
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
                overflow: hidden !important;
            }

            /* Custom Bespoke Scrollbars */
            ::-webkit-scrollbar {
                width: 7px;
                height: 7px;
            }
            ::-webkit-scrollbar-track {
                background: rgba(3, 7, 18, 0.5);
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(56, 189, 248, 0.25);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(56, 189, 248, 0.45);
            }
            /* 14. Glossy LinkedIn Team Connect Buttons */
            .team-linkedin-btn {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                padding: 7px 11px !important;
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%), rgba(10, 18, 38, 0.72) !important;
                border: 1px solid rgba(56, 189, 248, 0.28) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.35) !important;
                border-radius: 9px !important;
                color: #f1f5f9 !important;
                text-decoration: none !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.02em !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.15) !important;
                backdrop-filter: blur(12px) !important;
                transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            .team-linkedin-btn:hover {
                transform: translateY(-2px) scale(1.02) !important;
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.28) 0%, rgba(99, 102, 241, 0.2) 100%), rgba(15, 26, 56, 0.85) !important;
                border-color: rgba(56, 189, 248, 0.65) !important;
                border-top-color: #ffffff !important;
                box-shadow: 0 8px 22px rgba(14, 165, 233, 0.38), inset 0 1px 2px rgba(255, 255, 255, 0.4) !important;
                color: #ffffff !important;
                text-decoration: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def show_toast(self, message: str, type: str = "success"):
        """Show toast notification"""
        color = "#10b981" if type == "success" else "#ef4444" if type == "error" else "#f59e0b"
        st.markdown(
            f"""
            <div id="toast" style="
                position: fixed; 
                top: 65px; 
                right: 25px; 
                background: {color}; 
                color: white; 
                padding: 0.8rem 1.6rem; 
                border-radius: 8px; 
                font-weight: 600;
                box-shadow: 0 8px 24px rgba(0,0,0,0.35);
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            ">
                {message}
            </div>
            <style>
            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    def check_backend_health(self) -> bool:
        """Check if FastAPI / MCP server is responding."""
        try:
            r = httpx.get(f"{self.api_url}/health", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def login_page(self):
        """Render centered, inspiring login page with luxury glassy aesthetics"""
        st.markdown(
            """
            <style>
            .stVerticalBlock {
                max-width: 540px;
                margin-left: auto;
                margin-right: auto;
            }
            </style>
            <div style="text-align: center; margin-bottom: 2.2rem; padding-top: 1.8rem;">
                <div style="
                    display: inline-flex; align-items: center; justify-content: center; 
                    width: 78px; height: 78px; 
                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #6366f1 100%); 
                    border-radius: 24px; 
                    box-shadow: 0 12px 32px rgba(14, 165, 233, 0.45), inset 0 1px 1px #fff; 
                    border-top: 1px solid rgba(255,255,255,0.75);
                    margin-bottom: 1.2rem;
                ">
                    <span style="font-size: 38px;">🌊</span>
                </div>
                <h1 style="margin: 0; font-size: 3.1rem; font-weight: 800; letter-spacing: -0.035em;">FloatChat</h1>
                <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 1.12rem; font-weight: 500;">
                    Autonomous Ocean Intelligence & Deep-Sea Telemetry Platform
                </p>
                <div style="
                    display: inline-block; 
                    background: linear-gradient(135deg, rgba(56,189,248,0.2) 0%, rgba(99,102,241,0.15) 100%); 
                    border: 1px solid rgba(56,189,248,0.4); 
                    border-top: 1px solid rgba(255,255,255,0.6); 
                    padding: 5px 18px; 
                    border-radius: 9999px; 
                    color: #7dd3fc; 
                    font-size: 0.85rem; 
                    font-weight: 700; 
                    letter-spacing: 0.03em;
                    margin-top: 8px; 
                    box-shadow: 0 8px 24px rgba(14,165,233,0.25), inset 0 1px 1px rgba(255,255,255,0.3); 
                    backdrop-filter: blur(14px);
                ">
                    ✨ Enterprise Ocean Discovery Engine • v2.4
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            st.markdown("### 🔐 Platform Authentication")
            username = st.text_input("Username or Email", placeholder="e.g. admin or admin@argo.com")
            password = st.text_input("Password", type="password", placeholder="Enter password")

            col1, col2 = st.columns([1, 1])
            with col1:
                login_btn = st.form_submit_button("🚀 Launch FloatChat", use_container_width=True, type="primary")
            with col2:
                st.markdown(
                    '<p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.6rem; text-align: right;">Demo: <b>admin</b> / <b>admin</b></p>',
                    unsafe_allow_html=True,
                )

            if login_btn:
                users_df = st.session_state.get("users_data", pd.DataFrame())
                is_valid = False
                user_role = "User"

                if (username == "admin" and password == "admin") or (username == "admin@argo.com" and password == "admin123"):
                    is_valid = True
                    user_role = "Administrator"
                elif not users_df.empty:
                    match = users_df[(users_df["email"] == username) & (users_df["password"] == password) & (users_df["status"] == "active")]
                    if not match.empty:
                        is_valid = True
                        user_role = match.iloc[0]["role"]

                if is_valid:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["user_role"] = user_role
                    # Store session token in query params so browser reload keeps user logged in
                    token = hashlib.sha256(f"{username}:argo_salt_2025".encode()).hexdigest()[:16]
                    st.query_params["session_user"] = username
                    st.query_params["session_token"] = token
                    self.show_toast(f"🎉 Authenticated as {username} ({user_role})", "success")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Use demo username: admin / password: admin")

        # Explain FloatChat on login screen for anyone confused
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(11, 20, 42, 0.72);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-top: 1px solid rgba(255, 255, 255, 0.42);
                border-radius: 16px;
                padding: 1.4rem 1.5rem;
                margin-top: 1.8rem;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.25);
                backdrop-filter: blur(20px);
            ">
                <h4 style="color:#38bdf8; margin:0 0 0.5rem 0; font-size:1.02rem; font-weight:700;">💡 Platform Overview</h4>
                <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.6; margin:0;">
                    Global oceans are monitored by thousands of autonomous <b>ARGO profiling floats</b> recording salinity, temperature, and depth down to 2,000 meters. 
                    <b>FloatChat</b> allows researchers, students, and oceanographers to ask questions in plain English and automatically explore profiles, maps, and SQL databases.
                </p>
                <div style="margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.09); text-align: center;">
                    <div style="font-size: 0.74rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 10px;">
                        ✨ ARCHITECTED & DEVELOPED BY ✨
                    </div>
                    <div style="display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <a href="https://www.linkedin.com/in/aditya-kittad-bbb9532ba/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 7px 15px; border-radius: 9999px;">
                            <span style="display:flex; align-items:center; gap:6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                ADITYA KITTAD
                            </span>
                            <span style="color:#38bdf8; font-size:0.75rem; margin-left:6px; font-weight:800;">in ↗</span>
                        </a>
                        <a href="https://www.linkedin.com/in/ganesh-kapure-5309542ba/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 7px 15px; border-radius: 9999px;">
                            <span style="display:flex; align-items:center; gap:6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                GANESH KAPURE
                            </span>
                            <span style="color:#38bdf8; font-size:0.75rem; margin-left:6px; font-weight:800;">in ↗</span>
                        </a>
                        <a href="https://www.linkedin.com/in/om-jaiswal-3b2b39249/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 7px 15px; border-radius: 9999px;">
                            <span style="display:flex; align-items:center; gap:6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                OM JAISWAL
                            </span>
                            <span style="color:#38bdf8; font-size:0.75rem; margin-left:6px; font-weight:800;">in ↗</span>
                        </a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("👥 Preview Developer Credentials & Dossiers (No Login Required)", key="login_preview_dossiers_btn", use_container_width=True):
            show_developer_profile_dialog()

    def render_sidebar(self):
        """Render enhanced modern sidebar with intuitive navigation and guide link"""
        with st.sidebar:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.015) 100%), rgba(14, 25, 52, 0.72);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-top: 1px solid rgba(255, 255, 255, 0.45);
                    border-radius: 16px;
                    padding: 1.1rem 1rem;
                    margin-bottom: 1.2rem;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.25);
                    backdrop-filter: blur(16px);
                ">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="
                            width: 44px; height: 44px; 
                            border-radius: 12px; 
                            background: linear-gradient(135deg, #0ea5e9, #6366f1); 
                            display: flex; align-items: center; justify-content: center; 
                            box-shadow: 0 4px 16px rgba(14, 165, 233, 0.45), inset 0 1px 1px #fff;
                            border-top: 1px solid rgba(255,255,255,0.7);
                            font-size: 22px;
                        ">
                            🌊
                        </div>
                        <div>
                            <div style="font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 800; line-height: 1.1; background: linear-gradient(120deg, #ffffff 40%, #38bdf8 80%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                                FloatChat
                            </div>
                            <div style="display: inline-block; background: linear-gradient(135deg, rgba(56,189,248,0.2), rgba(99,102,241,0.15)); border: 1px solid rgba(56,189,248,0.35); border-top: 1px solid rgba(255,255,255,0.4); border-radius: 20px; padding: 2px 8px; color: #7dd3fc; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; margin-top: 4px; box-shadow: inset 0 1px 1px rgba(255,255,255,0.2);">
                                Autonomous Ocean AI
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.8rem; color: #94a3b8; display: flex; align-items: center; justify-content: space-between;">
                        <span>User: <b style="color:#f8fafc;">{st.session_state['username']}</b></span>
                        <span style="display: inline-flex; align-items: center; gap: 4px; color: #10b981; font-weight: 600; font-size: 0.75rem;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span> Online
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Guided Tour Button right in sidebar
            if st.button("❓ How FloatChat Works", key="btn_quick_guide", use_container_width=True):
                show_how_it_works_dialog()

            st.markdown("### 📍 Navigation")

            nav_items = [
                ("chats", "💬 AI Ocean Chatbot", "Natural language querying & charts"),
                ("map", "🗺️ Geospatial Map", "Live float tracking & trajectories"),
                ("analytics", "📈 Ocean Analytics", "Depth profiles & T-S curves"),
                ("converter", "🔄 NetCDF Ingestion Engine", "Transform .nc files into SQL/DB"),
                ("database", "🗄️ Database Hub & SQL Lab", "Inspect tables & run custom SQL"),
                ("guide", "📚 Platform Guide & Architecture", "Learn ARGO, NetCDF, and MCP"),
                ("users", "👥 User Roles & Access", "Manage access permissions"),
            ]

            active_page = st.session_state.get("current_page", "chats")
            for page_key, label, desc in nav_items:
                is_selected = (active_page == page_key)
                btn_type = "primary" if is_selected else "secondary"
                if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=btn_type, help=desc):
                    st.session_state["current_page"] = page_key
                    st.rerun()

            st.markdown("---")

            # Real-time System Status Card
            is_healthy = self.check_backend_health()
            badge_color = "#10b981" if is_healthy else "#f59e0b"
            status_text = "MCP Server Online (:8000)" if is_healthy else "Standalone Mode (Active)"

            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%), rgba(8, 15, 32, 0.72);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-top: 1px solid rgba(255,255,255,0.32);
                    border-radius: 12px;
                    padding: 10px 12px;
                    font-size: 0.8rem;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.15);
                    backdrop-filter: blur(12px);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">System Engine</span>
                        <span style="color: {badge_color}; font-weight: 700; font-size: 0.78rem; text-shadow: 0 0 10px {badge_color};">● {status_text}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.73rem; display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>Live Database:</span>
                        <span style="color: #38bdf8; font-weight: 600;">argo.db (777+ rows)</span>
                    </div>
                    <div style="padding-top: 5px; border-top: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; align-items: center; font-size: 0.73rem;">
                        <span style="color: #94a3b8;">24/7 Keep-Alive:</span>
                        <span style="color: #10b981; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                            🛡️ Guard Active (No Sleep)
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%), rgba(10, 18, 38, 0.72);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-top: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 14px;
                    padding: 0.9rem 0.8rem;
                    margin-top: 1.2rem;
                    text-align: center;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.2);
                    backdrop-filter: blur(14px);
                ">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 6px;">
                        <span>✨</span> ARCHITECTED BY <span>✨</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #38bdf8; font-weight: 700; margin-bottom: 8px;">
                        B.Tech Final Year • Minor Project
                    </div>
                    <div style="font-size: 0.68rem; color: #94a3b8; margin-bottom: 8px;">
                        Click below for instant credentials (No Login Required):
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_dev_a, col_dev_b, col_dev_c = st.columns(3)
            with col_dev_a:
                if st.button("🚀 AK", key="btn_side_ak", use_container_width=True, help="Inspect Aditya Kittad Credentials"):
                    show_developer_profile_dialog("aditya")
            with col_dev_b:
                if st.button("🌊 GK", key="btn_side_gk", use_container_width=True, help="Inspect Ganesh Kapure Credentials"):
                    show_developer_profile_dialog("ganesh")
            with col_dev_c:
                if st.button("⚡ OJ", key="btn_side_oj", use_container_width=True, help="Inspect Om Jaiswal Credentials"):
                    show_developer_profile_dialog("om")

            if st.button("👥 Open Developer Dossiers", key="btn_side_open_all_dossiers", use_container_width=True, help="View all developer profiles with zero login required"):
                show_developer_profile_dialog()

            st.markdown(
                """
                <div style="margin: 6px 0 10px 0; text-align: center; font-size: 0.68rem; color: #64748b;">
                    External LinkedIn: 
                    <a href="https://www.linkedin.com/in/aditya-kittad-bbb9532ba/" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none; font-weight: 600;">Aditya ↗</a> • 
                    <a href="https://www.linkedin.com/in/ganesh-kapure-5309542ba/" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none; font-weight: 600;">Ganesh ↗</a> • 
                    <a href="https://www.linkedin.com/in/om-jaiswal-3b2b39249/" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none; font-weight: 600;">Om ↗</a>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

    def render_chat_page(self):
        """Render the Conversational AI Interface with in-chat charts, SQL inspector, and sample prompts"""
        # Header with guidance
        st.title("💬 AI Ocean Chatbot")
        st.markdown(
            """
            <div class="info-banner">
                <h4>💡 How to Use the Chat Assistant:</h4>
                <p>
                    Ask questions in plain conversational English. The chatbot uses <b>Model Context Protocol (MCP)</b> 
                    to understand your intent, translate it into optimized SQL, retrieve records from the ARGO database, and generate 
                    both structured oceanographic insights and interactive depth-profile plots!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick Question Suggestion Cards
        st.markdown("##### ⚡ Popular Ocean Queries (Click to Run):")
        chip_col1, chip_col2, chip_col3 = st.columns(3)

        preset_query = None
        with chip_col1:
            if st.button("🌡️ Average Ocean Temperature", key="q_temp", use_container_width=True, help="Computes mean, min, and max temperatures across all ARGO profiles"):
                preset_query = "What is the average temperature in profile table?"
            if st.button("🧂 Salinity Profiles Near Equator", key="q_sal", use_container_width=True, help="Retrieves practical salinity and pressure between -5° and +5° latitude"):
                preset_query = "Show me salinity profiles near the equator in March 2023"

        with chip_col2:
            if st.button("📍 Active ARGO Floats & Coordinates", key="q_float", use_container_width=True, help="Discovers nearest floats and their recorded coordinates"):
                preset_query = "What are the nearest ARGO floats to this location?"
            if st.button("🏔️ Temperature & Salinity vs Depth", key="q_depth", use_container_width=True, help="Plots vertical profile CTD casts down to 2,000 dbar"):
                preset_query = "Plot temperature and salinity profiles vs depth"

        with chip_col3:
            if st.button("🤖 What is an ARGO Float?", key="q_what", use_container_width=True, help="Explains the autonomous profiling mechanism"):
                preset_query = "What is an ARGO float and how does it work?"
            if st.button("📊 Total Database Statistics", key="q_stat", use_container_width=True, help="Summarizes profile cycles and float numbers"):
                preset_query = "How many profiles are recorded in the ARGO database?"

        st.markdown("---")

        # Display Chat History
        chat_messages = st.session_state.get("messages", [])
        for message in chat_messages:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            elif message["role"] == "assistant":
                content = message["content"]
                st.chat_message("assistant").write(content)

                # Multimodal Enhancement: Auto-render interactive depth profile if query relates to depth/profiles
                if any(k in content.lower() for k in ["salinity", "temperature", "pres", "depth", "profile", "equator"]) and "SQL_QUERY" in content:
                    self._render_in_chat_profile_plot(content)

        # Chat Input Box
        query = st.chat_input("Ask a question about ARGO oceanography (e.g. 'Show temperature near equator' or 'Explain salinity')...")
        if preset_query:
            query = preset_query

        if query:
            # Set chat title
            if len(self.messages) == 0:
                st.session_state["chat_titles"][self.chat_id] = query[:30]

            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)
            st.chat_message("user").write(query)

            typing_placeholder = st.empty()
            with typing_placeholder.container():
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; padding: 1rem; background: rgba(15, 23, 42, 0.7); border-radius: 10px; border-left: 4px solid #38bdf8; margin: 1rem 0;">
                        <span style="font-size: 20px; margin-right: 12px;">🌊</span>
                        <div style="color: #38bdf8; font-weight: 600;">ARGO MCP Agent is interpreting query, analyzing schema, and executing SQL...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Query backend or direct fallback
            try:
                with httpx.Client(timeout=45.0) as client:
                    response = client.post(f"{self.api_url}/query", json={"query": query})
                    typing_placeholder.empty()

                    if response.status_code == 200:
                        messages = response.json()["messages"]
                        st.session_state["messages"] = messages
                        st.session_state["chats"][self.chat_id] = messages
                        latest_resp = messages[-1]["content"]
                        st.chat_message("assistant").write(latest_resp)

                        # Render interactive chart if relevant
                        if any(k in query.lower() for k in ["temperature", "salinity", "temp", "psal", "depth", "pres", "equator", "profile"]):
                            self._render_in_chat_profile_plot(latest_resp)
                    else:
                        st.error(f"Backend returned error {response.status_code}: {response.text}")
            except Exception as e:
                typing_placeholder.empty()
                local_resp = self._run_local_query_fallback(query)
                assistant_msg = {"role": "assistant", "content": local_resp}
                self.messages.append(assistant_msg)
                st.chat_message("assistant").write(local_resp)
                if any(k in query.lower() for k in ["temperature", "salinity", "temp", "psal", "depth", "pres", "equator", "profile"]):
                    self._render_in_chat_profile_plot(local_resp)

    def _render_in_chat_profile_plot(self, context_text: str):
        """Dynamically render an interactive depth profile chart right inside the chat response"""
        with st.expander("📈 Interactive In-Chat CTD Profile Visualization", expanded=True):
            st.caption("Auto-generated depth cast based on retrieved observations:")
            try:
                # Query real sample from SQLite profile table
                conn = sqlite3.connect(self.db_path)
                df_profile = pd.read_sql_query(
                    'SELECT pres as Depth_dbar, "temp" as Temperature_C, psal as Salinity_PSU FROM profile WHERE pres IS NOT NULL AND "temp" IS NOT NULL ORDER BY pres ASC LIMIT 35;',
                    conn
                )
                conn.close()

                if not df_profile.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_profile['Temperature_C'],
                        y=df_profile['Depth_dbar'],
                        mode='lines+markers',
                        name='Temperature (°C)',
                        line=dict(color='#ff6b6b', width=2.5),
                        marker=dict(size=5)
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_profile['Salinity_PSU'],
                        y=df_profile['Depth_dbar'],
                        mode='lines+markers',
                        name='Salinity (PSU)',
                        line=dict(color='#38bdf8', width=2.5),
                        marker=dict(size=5)
                    ))
                    fig.update_layout(
                        title="ARGO Ocean Vertical Profile Cast (Surface to 2,000 dbar)",
                        yaxis=dict(title="Pressure / Depth (dbar)", autorange="reversed", gridcolor="rgba(255,255,255,0.08)"),
                        xaxis=dict(title="Oceanographic Value (°C / PSU)", gridcolor="rgba(255,255,255,0.08)"),
                        template="plotly_dark",
                        height=350,
                        margin=dict(l=20, r=20, t=35, b=20),
                        legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98, bgcolor="rgba(0,0,0,0.5)")
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

    def _format_dataframe_to_markdown(self, df: pd.DataFrame, max_rows: int = 12) -> str:
        """Format DataFrame into a clean GitHub-style Markdown table with appropriate rounding."""
        if df.empty:
            return "*No matching records found in argo.db.*"

        display_df = df.head(max_rows).copy()
        headers = [str(c) for c in display_df.columns]
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for _, row in display_df.iterrows():
            row_vals = []
            for col, val in row.items():
                if pd.isna(val) or val is None:
                    row_vals.append("—")
                elif isinstance(val, (int, np.integer)):
                    row_vals.append(str(val))
                elif isinstance(val, float):
                    if val.is_integer() and any(k in str(col).lower() for k in ["platform", "cycle", "count", "sample", "row", "total"]):
                        row_vals.append(str(int(val)))
                    else:
                        row_vals.append(f"{val:.3f}")
                else:
                    row_vals.append(str(val))
            lines.append("| " + " | ".join(row_vals) + " |")

        table_md = "\n".join(lines)
        if len(df) > max_rows:
            table_md += f"\n\n*Displaying top {max_rows} of {len(df)} matching observations.*"
        return table_md

    def _run_local_query_fallback(self, query: str) -> str:
        """Local direct query against SQLite argo.db when FastAPI is offline."""
        try:
            conn = sqlite3.connect(self.db_path)
            q = query.lower()

            # 1. SALINITY ACADEMIC EXPLANATION
            if any(k in q for k in ["explain salinity", "what is salinity", "what is psal", "how is salinity measured", "tell me about salinity", "salinity concept"]):
                sal_stats = pd.read_sql_query(
                    'SELECT COUNT(psal) as count, ROUND(AVG(psal), 3) as avg_sal, ROUND(MIN(psal), 3) as min_sal, ROUND(MAX(psal), 3) as max_sal, ROUND(MIN(pres), 1) as min_pres, ROUND(MAX(pres), 1) as max_pres FROM profile WHERE psal IS NOT NULL;',
                    conn
                ).iloc[0]
                sample_df = pd.read_sql_query(
                    'SELECT platform_number, cycle_number, pres as depth_dbar, psal as salinity_psu, "temp" as temp_c, ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude FROM profile WHERE psal IS NOT NULL ORDER BY pres ASC LIMIT 8;',
                    conn
                )
                conn.close()
                sample_table = self._format_dataframe_to_markdown(sample_df, max_rows=8)

                return (
                    "### 🧂 Scientific Guide: Practical Salinity (PSAL) in Oceanography & ARGO Telemetry\n\n"
                    "#### 1. Fundamental Definition & Measurement Physics\n"
                    "• **What is Seawater Salinity?**: Salinity is the total mass of dissolved inorganic salts in seawater (predominantly $\\text{Cl}^-$, $\\text{Na}^+$, $\\text{SO}_4^{2-}$, and $\\text{Mg}^{2+}$).\n"
                    "• **The Practical Salinity Scale (PSS-78)**: In modern oceanography and the ARGO program, salinity is calculated as **Practical Salinity (PSAL)**—a dimensionless ratio of the electrical conductivity of seawater to a standard Potassium Chloride ($\\text{KCl}$) solution at $15^\\circ\\text{C}$ and $1\\text{ atm}$. Hence, salinity is recorded in **Practical Salinity Units (PSU)** (roughly $\\text{g/kg}$).\n"
                    "• **CTD Sensor Mechanism**: ARGO floats measure conductivity, temperature, and pressure simultaneously using an onboard **Conductivity-Temperature-Depth (CTD)** inductive sensor (Sea-Bird SBE 41/41CP). From conductivity $C$, temperature $T$, and pressure $P$, the UNESCO algorithms compute in-situ salinity with $\\pm 0.003\\text{ PSU}$ accuracy.\n\n"
                    "---\n\n"
                    "#### 2. Vertical Ocean Stratification & Halocline Dynamics\n"
                    "1. **Surface Epipelagic Layer (0 – 100 dbar)**: Driven by solar heating, precipitation (dilution), evaporation (salinity spike), and river freshwater run-off.\n"
                    "2. **The Halocline (100 – 800 dbar)**: The critical oceanic transition zone characterized by a steep vertical salinity gradient. The halocline acts as a strong density barrier inhibiting vertical mixing.\n"
                    "3. **Deep Abyssal Water (800 – 2,000 dbar)**: Highly uniform global salinity (**~34.60 to 34.85 PSU**), dominated by cold, dense Antarctic Bottom Water (AABW) and North Atlantic Deep Water (NADW).\n\n"
                    "---\n\n"
                    "#### 3. Civil & Environmental Engineering Significance\n"
                    "• **Density & Thermohaline Circulation**: Seawater density $\\rho(S, T, P)$ is strongly modulated by salinity. Gradients in density drive the global Thermohaline Circulation (AMOC) and planetary climate regulation.\n"
                    "• **Marine Structure Durability**: Higher ocean salinity accelerates chloride penetration, inducing reinforcement bar corrosion in coastal structures, offshore wind turbines, and breakwaters.\n"
                    "• **Underwater Sonar & Telemetry**: Sound velocity in seawater increases by $\\approx 1.34\\text{ m/s}$ for every $1\\text{ PSU}$ increase in salinity, directly impacting acoustic navigation, bathymetric surveys, and underwater communication.\n\n"
                    "---\n\n"
                    f"#### 📊 Empirical ARGO Telemetry Statistics (From Live `argo.db`):\n"
                    f"• **Total Salinity Observations**: `{int(sal_stats['count']):,}` records\n"
                    f"• **Mean Salinity across Dataset**: `{sal_stats['avg_sal']:.3f} PSU`\n"
                    f"• **Observed Salinity Range**: `{sal_stats['min_sal']:.3f} PSU` to `{sal_stats['max_sal']:.3f} PSU`\n"
                    f"• **Vertical Depth Profile Range**: `{sal_stats['min_pres']:.1f} dbar` (Surface) to `{sal_stats['max_pres']:.1f} dbar` (Deep Cast)\n\n"
                    "#### 🔍 Sample Vertical Profile Cast (Surface to Depth):\n"
                    f"{sample_table}\n\n"
                    "---\n"
                    "💡 *Scroll below to inspect the auto-generated interactive CTD Depth Profile Chart!*"
                )

            # 2. TEMPERATURE ACADEMIC EXPLANATION
            if any(k in q for k in ["explain temp", "what is temp", "what is thermocline", "thermocline", "temperature concept"]):
                temp_stats = pd.read_sql_query(
                    'SELECT COUNT("temp") as count, ROUND(AVG("temp"), 3) as avg_temp, ROUND(MIN("temp"), 3) as min_temp, ROUND(MAX("temp"), 3) as max_temp, ROUND(MIN(pres), 1) as min_pres, ROUND(MAX(pres), 1) as max_pres FROM profile WHERE "temp" IS NOT NULL;',
                    conn
                ).iloc[0]
                sample_df = pd.read_sql_query(
                    'SELECT platform_number, cycle_number, pres as depth_dbar, "temp" as temp_c, psal as salinity_psu, ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude FROM profile WHERE "temp" IS NOT NULL ORDER BY pres ASC LIMIT 8;',
                    conn
                )
                conn.close()
                sample_table = self._format_dataframe_to_markdown(sample_df, max_rows=8)

                return (
                    "### 🌡️ Scientific Guide: In-Situ Seawater Temperature & Thermocline Dynamics\n\n"
                    "#### 1. Definition & Measurement Physics\n"
                    "• **In-Situ Temperature vs Potential Temperature ($\\theta$)**: In-situ temperature is the actual seawater temperature measured at depth. Potential temperature ($\\theta$) removes adiabatic compression to reference sea surface pressure.\n"
                    "• **CTD Thermal Sensors**: Measured using aging-resistant platinum resistance thermometers (PRT) calibrated to ITS-90 with accuracy of $\\pm 0.002^\\circ\\text{C}$.\n\n"
                    "---\n\n"
                    "#### 2. Vertical Thermal Stratification\n"
                    "1. **Surface Mixed Layer**: Wind-stirred warm layer with uniform temperatures.\n"
                    "2. **The Thermocline (100 – 600 dbar)**: A steep vertical temperature gradient separating warm surface waters from the cold ocean interior.\n"
                    "3. **Deep Abyssal Ocean (>1,000 dbar)**: Cold, dense polar-origin waters remaining between $1.5^\\circ\\text{C}$ and $3.0^\\circ\\text{C}$.\n\n"
                    "---\n\n"
                    f"#### 📊 Empirical ARGO Telemetry Statistics (From Live `argo.db`):\n"
                    f"• **Total Temperature Observations**: `{int(temp_stats['count']):,}` records\n"
                    f"• **Mean Temperature across Dataset**: `{temp_stats['avg_temp']:.2f} °C`\n"
                    f"• **Observed Temperature Range**: `{temp_stats['min_temp']:.2f} °C` to `{temp_stats['max_temp']:.2f} °C`\n"
                    f"• **Vertical Cast Span**: `{temp_stats['min_pres']:.1f} dbar` to `{temp_stats['max_pres']:.1f} dbar`\n\n"
                    "#### 🔍 Sample Vertical Profile Cast:\n"
                    f"{sample_table}\n\n"
                    "---\n"
                    "💡 *Scroll below to inspect the auto-generated interactive CTD Depth Profile Chart!*"
                )

            if any(k in q for k in ["what is argo", "how does argo work"]):
                conn.close()
                return (
                    "### 🌊 What is an ARGO Float and How Does it Work?\n\n"
                    "• **Autonomous Oceanic Robotic Probes**: The ARGO program is a global observation network of over 4,000 autonomous robotic floats drifting across the world's oceans.\n"
                    "• **The 10-Day Profiling Cycle**:\n"
                    "  1. **Descent**: The float changes buoyancy using an internal oil bladder and descends to a 'parking depth' of 1,000 meters.\n"
                    "  2. **Drift**: It drifts passively with deep ocean currents for approximately 9 days.\n"
                    "  3. **Deep Cast**: It descends further to 2,000 meters (2,000 dbar pressure).\n"
                    "  4. **Ascent & CTD Cast**: It ascends to the surface over 6 hours while continuously measuring **Conductivity (Salinity)**, **Temperature**, and **Pressure (Depth)**.\n"
                    "  5. **Data Transmission**: At the sea surface, it acquires GPS coordinates and transmits data packets via Argos or Iridium satellites to oceanographic data centres (AOML, INCOIS, Coriolis).\n"
                    "• **Data Model**: In this FloatChat platform, observations are decoded from NetCDF files and indexed into `profile`, `tech`, and `trajectory` relational tables."
                )

            if "temp" in q:
                sql = 'SELECT ROUND(AVG("temp"), 3) as avg_temperature, ROUND(MIN("temp"), 3) as min_temp, ROUND(MAX("temp"), 3) as max_temp, COUNT(*) as sample_count FROM profile WHERE "temp" IS NOT NULL;'
            elif "salin" in q:
                sql = 'SELECT ROUND(AVG(psal), 3) as avg_salinity, ROUND(MIN(psal), 3) as min_salinity, ROUND(MAX(psal), 3) as max_salinity, COUNT(*) as sample_count FROM profile WHERE psal IS NOT NULL;'
            elif "nearest" in q or "float" in q:
                sql = 'SELECT platform_number, project_name, pi_name, ROUND(AVG(latitude), 4) as avg_lat, ROUND(AVG(longitude), 4) as avg_lon, COUNT(*) as profiles FROM profile GROUP BY platform_number LIMIT 10;'
            else:
                sql = 'SELECT COUNT(*) as total_profile_rows, COUNT(DISTINCT platform_number) as distinct_floats, COUNT(DISTINCT cycle_number) as distinct_cycles FROM profile;'

            df = pd.read_sql_query(sql, conn)
            conn.close()

            table_md = self._format_dataframe_to_markdown(df, max_rows=12)
            return f"### 🌊 ARGO Ocean Insights (Local Engine)\n\n#### 🔍 Executed SQL Query:\n```sql\n{sql}\n```\n\n#### 📊 Empirical Observations from `argo.db`:\n{table_md}\n\n---\n💡 *Tip: Check the **Geospatial Map** tab to view float positions or the **NetCDF Converter** to ingest more profile files!*"
        except Exception as e:
            return f"❌ Query execution failed: {e}"

    def render_map_page(self):
        """Render Interactive Geospatial Map with Float Markers and Guidance"""
        st.title("🗺️ Geospatial ARGO Float Tracking")
        st.markdown(
            """
            <div class="info-banner">
                <h4>🗺️ How to Read This Map:</h4>
                <p>
                    Autonomous ARGO floats drift across major ocean basins (Indian Ocean, Arabian Sea, and Bay of Bengal).
                    • <b>🟢 Green markers</b> = Active floats transmitting profiles within normal 10-day cycles.<br>
                    • <b>🟡 Amber markers</b> = Delayed transmissions.<br>
                    • <b>⭐ Blue star</b> = Your current ground station location (Coimbatore, India).<br>
                    Click on any float marker or click <b>"View Specs"</b> below to inspect cycle count, battery level, and CTD depth ratings!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        current_lat, current_lon = 11.0168, 76.9558  # User Location

        # Filters
        st.markdown("##### 🎛️ Filter Floats by Region & Condition:")
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            region_f = st.selectbox("Ocean Basin", ["All Regions", "Indian Ocean", "Bay of Bengal", "Arabian Sea", "Pacific Ocean"])
        with f2:
            status_f = st.selectbox("Operational Status", ["All Status", "Active", "Delayed", "Inactive"])
        with f3:
            temp_f = st.selectbox("Surface Temp", ["All Temps", "Cold (<25°C)", "Moderate (25-30°C)", "Warm (>30°C)"])
        with f4:
            battery_f = st.selectbox("Battery", ["All Levels", "High (>80%)", "Medium (60-80%)", "Low (<60%)"])

        # Base 24 Floats Fleet
        argo_floats = pd.DataFrame({
            'float_id': [f'{5900000 + i}' for i in range(1, 25)],
            'lat': [
                -15.2, -8.5, 12.3, 15.7, 6.2, 9.8, 14.1, 18.4,
                16.2, 19.5, 13.8, 11.4, 17.9, 20.1,
                10.5, 8.9, 12.7, 15.3, 18.6, 21.2,
                25.1, 28.4, 23.7, 26.9
            ],
            'lon': [
                65.2, 78.2, 82.5, 85.1, 79.8, 83.4, 88.2, 86.7,
                84.3, 87.9, 81.6, 79.2, 85.8, 88.4,
                75.3, 73.1, 77.8, 74.6, 76.9, 78.5,
                120.3, 125.7, 118.9, 123.4
            ],
            'temperature': [
                24.8, 26.8, 28.2, 27.5, 29.1, 26.3, 25.9, 24.7,
                27.9, 28.5, 29.3, 30.1, 26.8, 25.4,
                31.2, 32.1, 30.8, 29.7, 28.9, 27.6,
                22.1, 21.5, 23.4, 20.9
            ],
            'salinity': [
                34.8, 34.2, 34.5, 34.1, 34.8, 34.3, 33.9, 34.6,
                34.1, 34.7, 34.9, 35.2, 34.0, 33.8,
                35.8, 36.1, 35.4, 35.0, 34.7, 34.3,
                33.5, 33.2, 33.8, 33.1
            ],
            'max_depth': [2000] * 24,
            'cycle_number': np.random.randint(50, 350, 24),
            'days_since_profile': np.random.randint(0, 15, 24),
            'battery_level': np.random.uniform(65, 100, 24),
            'status': np.random.choice(['Active', 'Delayed', 'Inactive'], 24, p=[0.8, 0.15, 0.05]),
            'ocean_region': (['Indian Ocean'] * 8 + ['Bay of Bengal'] * 6 + ['Arabian Sea'] * 6 + ['Pacific Ocean'] * 4)
        })

        # Apply filters
        df_f = argo_floats.copy()
        if region_f != "All Regions":
            df_f = df_f[df_f['ocean_region'] == region_f]
        if status_f != "All Status":
            df_f = df_f[df_f['status'] == status_f]
        if temp_f == "Cold (<25°C)":
            df_f = df_f[df_f['temperature'] < 25]
        elif temp_f == "Moderate (25-30°C)":
            df_f = df_f[(df_f['temperature'] >= 25) & (df_f['temperature'] <= 30)]
        elif temp_f == "Warm (>30°C)":
            df_f = df_f[df_f['temperature'] > 30]

        if battery_f == "High (>80%)":
            df_f = df_f[df_f['battery_level'] > 80]
        elif battery_f == "Medium (60-80%)":
            df_f = df_f[(df_f['battery_level'] >= 60) & (df_f['battery_level'] <= 80)]
        elif battery_f == "Low (<60%)":
            df_f = df_f[df_f['battery_level'] < 60]

        # Interactive Mapbox / Map plot
        fig = go.Figure()
        status_colors = {'Active': '#10b981', 'Delayed': '#f59e0b', 'Inactive': '#ef4444'}

        for st_name in df_f['status'].unique():
            sub = df_f[df_f['status'] == st_name]
            fig.add_trace(ScatterMapTrace(
                lat=sub['lat'],
                lon=sub['lon'],
                mode='markers',
                marker=dict(size=14, color=status_colors.get(st_name, '#38bdf8')),
                text=sub['float_id'],
                hovertemplate="<b>🌊 Float WMO: %{text}</b><br>Region: " + sub['ocean_region'] + "<br>Surface Temp: %{customdata[0]:.1f}°C<br>Salinity: %{customdata[1]:.2f} PSU<br>Battery: %{customdata[2]:.1f}%<extra></extra>",
                customdata=np.stack((sub['temperature'], sub['salinity'], sub['battery_level']), axis=-1),
                name=f"{st_name} Floats ({len(sub)})"
            ))

        # Add User Location Pin
        fig.add_trace(ScatterMapTrace(
            lat=[current_lat],
            lon=[current_lon],
            mode='markers',
            marker=dict(size=16, color='#38bdf8', symbol='star'),
            name="📍 Current Ground Station (Coimbatore)",
            hovertemplate="<b>📍 Your Ground Station</b><br>Coimbatore, Tamil Nadu<extra></extra>"
        ))

        layout_kwargs = {
            MAP_LAYOUT_KEY: dict(
                style="open-street-map",
                center=dict(lat=14.0, lon=82.0),
                zoom=4
            ),
            "height": 550,
            "margin": dict(l=0, r=0, t=10, b=0),
            "legend": dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(15,23,42,0.8)", font=dict(color="white"))
        }
        fig.update_layout(**layout_kwargs)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**Displaying {len(df_f)} of {len(argo_floats)} ARGO profiling floats**")

        # Float cards with working details modal
        cols_per_row = 3
        float_rows = [df_f.iloc[i:i+cols_per_row] for i in range(0, min(12, len(df_f)), cols_per_row)]

        for f_row in float_rows:
            cols = st.columns(len(f_row))
            for i, (_, float_data) in enumerate(f_row.iterrows()):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div class="sensor-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="color:#f8fafc; font-size:1.05rem;">Float {float_data['float_id']}</strong>
                                <span class="status-{float_data['status'].lower()}">● {float_data['status']}</span>
                            </div>
                            <div style="color:#94a3b8; font-size:0.85rem; margin-top:4px;">📍 {float_data['ocean_region']}</div>
                            <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.82rem; color:#cbd5e1;">
                                <span>🌡️ {float_data['temperature']:.1f}°C</span>
                                <span>🧂 {float_data['salinity']:.1f} PSU</span>
                                <span>🔋 {float_data['battery_level']:.0f}%</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(f"🔍 View Specs #{float_data['float_id']}", key=f"btn_card_{float_data['float_id']}", use_container_width=True):
                        modal_content = f"""
                        <strong>🆔 Float WMO ID:</strong> {float_data['float_id']}<br>
                        <strong>🌊 Ocean Basin:</strong> {float_data['ocean_region']}<br>
                        <strong>📍 Coordinates:</strong> {float_data['lat']:.4f}° N, {float_data['lon']:.4f}° E<br>
                        <strong>🔄 Current Cycle:</strong> #{float_data['cycle_number']}<br>
                        <strong>🌡️ Sea Surface Temp:</strong> {float_data['temperature']:.2f}°C<br>
                        <strong>🧂 Practical Salinity:</strong> {float_data['salinity']:.2f} PSU<br>
                        <strong>🏔️ Max Profiling Depth:</strong> {float_data['max_depth']} meters (2,000 dbar)<br>
                        <strong>🔋 Battery Health:</strong> {float_data['battery_level']:.1f}%<br>
                        <strong>📊 Telemetry Status:</strong> {float_data['status']} (Iridium & Argos Satellites)
                        """
                        show_float_modal_dialog(f"ARGO Float {float_data['float_id']} Specifications", modal_content)

    def render_converter_page(self):
        """Render NetCDF to SQL Converter with Visual Pipeline, Real Parsing, and Database Ingestion"""
        st.title("🔄 NetCDF to SQL Ingestion Engine")
        st.markdown(
            """
            <div class="info-banner">
                <h4>🔄 NetCDF to Relational SQL Pipeline (Autonomous Scientific Pipeline):</h4>
                <p>
                    <b>Problem</b>: ARGO float CTD data is stored in complex, multidimensional binary files (<code>.nc</code> - NetCDF). 
                    Domain scientists and non-technical users cannot easily query this format.<br>
                    <b>Solution</b>: This engine reads NetCDF binary dimensions, decodes the multi-dimensional arrays (Pressure, Temperature, Salinity, Coordinates), 
                    generates standardized relational SQL tables, and imports them directly into our live database (<code>argo.db</code>)!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 📂 Step 1: Select Source NetCDF File")
        tab1, tab2 = st.tabs(["🌊 Quick Load Bundled Sample (1900683_prof.nc)", "📤 Upload Custom NetCDF File (.nc)"])

        selected_bytes = None
        selected_name = None

        with tab1:
            st.markdown("Use our pre-bundled Indian/Atlantic Ocean real float file (`argo_sample/1900683_prof.nc`):")
            sample_path = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "argo_sample", "1900683_prof.nc")
            )
            if st.button("🌊 Load Sample NetCDF Profile (1900683_prof.nc)", key="btn_load_sample", use_container_width=True):
                if os.path.exists(sample_path):
                    with open(sample_path, "rb") as f:
                        st.session_state["active_nc_bytes"] = f.read()
                        st.session_state["active_nc_name"] = "1900683_prof.nc"
                        self.show_toast("✅ Successfully loaded 1900683_prof.nc into converter memory!")
                else:
                    st.error("Sample NetCDF not found on disk.")

        with tab2:
            uploaded_file = st.file_uploader("Choose an ARGO NetCDF file (.nc)", type=["nc", "netcdf"], key="netcdf_uploader")
            if uploaded_file is not None:
                st.session_state["active_nc_bytes"] = uploaded_file.getvalue()
                st.session_state["active_nc_name"] = uploaded_file.name

        if "active_nc_bytes" in st.session_state:
            selected_bytes = st.session_state["active_nc_bytes"]
            selected_name = st.session_state["active_nc_name"]

            st.success(f"Loaded file: **{selected_name}** ({len(selected_bytes) / 1024:.1f} KB)")

            st.markdown("---")
            st.markdown("### ⚙️ Step 2: Configure SQL Extraction")
            c1, c2 = st.columns(2)
            with c1:
                target_table = st.text_input("Destination Database Table Name", value="argo_netcdf_profiles")
            with c2:
                profile_limit = st.slider("Number of Profile Casts to Extract", min_value=1, max_value=25, value=5, help="Number of 10-day CTD cycles to decode")

            if st.button("🚀 Execute NetCDF Decoding & Compile SQL", key="btn_run_conversion", use_container_width=True, type="primary"):
                with st.spinner("Decoding multidimensional arrays (PRES, TEMP, PSAL, LATITUDE, LONGITUDE)..."):
                    sql_text, row_count, preview_df = parse_netcdf_and_generate_sql(
                        selected_bytes, selected_name, target_table, profile_limit
                    )
                    st.session_state["converted_sql"] = sql_text
                    st.session_state["converted_rows"] = row_count
                    st.session_state["converted_df"] = preview_df
                    st.session_state["converted_table"] = target_table

            # Display Conversion Results
            if "converted_sql" in st.session_state:
                st.markdown("---")
                st.markdown("### 📋 Step 3: Inspect Decoded Relational Data")

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("📊 Total Records Decoded", f"{st.session_state['converted_rows']:,}")
                with m2:
                    st.metric("📋 SQL Table Generated", st.session_state['converted_table'])
                with m3:
                    st.metric("💾 SQL Script Payload", f"{len(st.session_state['converted_sql']) / 1024:.1f} KB")

                # Preview Dataframe
                st.markdown("#### 🔍 Extracted Data Preview (Pressure, Temperature, Salinity):")
                st.dataframe(st.session_state["converted_df"].head(10), use_container_width=True)

                # Action Buttons
                st.markdown("### 📤 Step 4: Export or Import to Database:")
                act_col1, act_col2 = st.columns(2)

                with act_col1:
                    st.download_button(
                        label="📥 Download SQL Script (.sql)",
                        data=st.session_state["converted_sql"],
                        file_name=f"{st.session_state['converted_table']}.sql",
                        mime="text/sql",
                        use_container_width=True
                    )

                with act_col2:
                    if st.button("📊 Import Directly into Live SQLite Database", key="btn_import_sql", use_container_width=True, type="primary"):
                        with st.spinner("Injecting SQL statements into argo.db..."):
                            inserted_rows = import_sql_to_db(st.session_state["converted_sql"], self.db_path)
                            modal_text = f"""
                            <strong>Destination Table:</strong> <code>{st.session_state['converted_table']}</code><br>
                            <strong>Rows Inserted:</strong> {inserted_rows} rows<br>
                            <strong>Database Engine:</strong> SQLite (Live: <code>argo.db</code>)<br>
                            <strong>Decoded Variables:</strong> Pressure (PRES), Temperature (TEMP), Salinity (PSAL), Coordinates (LAT/LON)<br>
                            <br>
                            <em>You can now query this table immediately through the Chat Assistant or inspect it in the Database Hub!</em>
                            """
                            show_info_modal_dialog("✅ Data Imported into Database Successfully", modal_text)

    def render_analytics_page(self):
        """Render Oceanographic Analytics Dashboard with Thermocline & T-S curves"""
        st.title("📈 Oceanographic Analytics")
        st.markdown(
            """
            <div class="info-banner">
                <h4>📈 What is Oceanographic Analysis?</h4>
                <p>
                    Oceanographers analyze the <b>Thermocline</b> (the zone where water temperature drops rapidly with depth) 
                    and <b>T-S (Temperature-Salinity) curves</b> to identify distinct water masses, track climate warming, and understand marine currents.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        total_real_profiles = 777
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM profile;")
                total_real_profiles = c.fetchone()[0]
                conn.close()
        except Exception:
            pass

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Active ARGO Fleet", "24 Floats", delta="100% Operational")
        with col2:
            st.metric("📊 Ingested Profile Casts", f"{total_real_profiles:,}", delta="Live in argo.db")
        with col3:
            st.metric("🔋 Mean Fleet Battery", "84.2%", delta="Optimal range")
        with col4:
            st.metric("🌊 Ocean Basins", "3 Basins", delta="Indian Ocean, Bay of Bengal, Arabian Sea")

        st.markdown("---")

        # Thermocline Visualization
        st.markdown("### 🏔️ Ocean Thermocline: Temperature vs Depth (0 to 2,000 dbar)")
        st.caption("Notice how warm surface waters (~28°C) drop steeply through the thermocline (100m - 500m) to cold deep water (~2.5°C).")

        depths = np.linspace(5, 2000, 50)
        temp_curve = 28.5 * np.exp(-depths / 320.0) + 2.5
        sal_curve = 34.2 + 1.1 * (1 - np.exp(-depths / 450.0))

        c_plot1, c_plot2 = st.columns(2)
        with c_plot1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=temp_curve, y=depths, mode='lines', name='Temperature (°C)', line=dict(color='#ff6b6b', width=3)))
            fig_temp.update_layout(
                title="Vertical Temperature Gradient",
                yaxis=dict(title="Pressure / Depth (dbar)", autorange="reversed", gridcolor="rgba(255,255,255,0.08)"),
                xaxis=dict(title="Seawater Temperature (°C)", gridcolor="rgba(255,255,255,0.08)"),
                template="plotly_dark",
                height=380,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        with c_plot2:
            fig_sal = go.Figure()
            fig_sal.add_trace(go.Scatter(x=sal_curve, y=depths, mode='lines', name='Salinity (PSU)', line=dict(color='#38bdf8', width=3)))
            fig_sal.update_layout(
                title="Vertical Salinity Gradient (Halocline)",
                yaxis=dict(title="Pressure / Depth (dbar)", autorange="reversed", gridcolor="rgba(255,255,255,0.08)"),
                xaxis=dict(title="Practical Salinity (PSU)", gridcolor="rgba(255,255,255,0.08)"),
                template="plotly_dark",
                height=380,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_sal, use_container_width=True)

        # T-S Diagram
        st.markdown("### 🔬 Temperature-Salinity (T-S) Water Mass Diagram")
        st.caption("A fundamental oceanographic plot showing water mass characteristics across different depths:")

        fig_ts = px.scatter(
            x=sal_curve,
            y=temp_curve,
            color=depths,
            labels={'x': 'Salinity (PSU)', 'y': 'Temperature (°C)', 'color': 'Depth (dbar)'},
            title="T-S Diagram colored by Depth",
            template="plotly_dark",
            color_continuous_scale="Viridis"
        )
        fig_ts.update_layout(height=400, margin=dict(l=20, r=20, t=35, b=20))
        st.plotly_chart(fig_ts, use_container_width=True)

    def render_database_page(self):
        """Render Database Hub with Live Table Inspector and Interactive SQL Lab"""
        st.title("🗄️ Database Hub & SQL Lab")
        st.markdown(
            """
            <div class="info-banner">
                <h4>🗄️ Relational Database Management (SQLite `argo.db`):</h4>
                <p>
                    All ingested ARGO observations are structured in relational tables. 
                    Inspect live schemas, preview raw records, or test your own custom SQL queries in our interactive SQL Lab below!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 📊 Active Database Tables in `argo.db`")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

            table_rows = []
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t};")
                cnt = cursor.fetchone()[0]
                desc = "Profile CTD Casts" if t == "profile" else "Engineering Sensors" if t == "tech" else "GPS Drift Tracks" if t == "trajectory" else "NetCDF Ingested"
                table_rows.append({"Table Name": t, "Row Count": cnt, "Category": desc})
            conn.close()

            df_tables = pd.DataFrame(table_rows)
            st.dataframe(df_tables, use_container_width=True)

            # Table Inspector
            st.markdown("#### 🔍 Table Schema & Row Inspector:")
            sel_table = st.selectbox("Choose Table to Inspect", tables)
            if st.button(f"Preview First 20 Rows of '{sel_table}'", key="btn_preview_tbl"):
                conn = sqlite3.connect(self.db_path)
                preview_df = pd.read_sql_query(f"SELECT * FROM {sel_table} LIMIT 20;", conn)
                conn.close()
                show_table_preview_dialog(sel_table, preview_df)

        except Exception as e:
            st.error(f"Error accessing database: {e}")

        st.markdown("---")

        # Interactive SQL Query Lab
        st.markdown("### ⚡ Interactive SQL Query Lab")
        st.caption("Execute arbitrary SQL queries against `argo.db` in real-time:")

        default_sql = "SELECT platform_number, cycle_number, pres, temp, psal FROM profile WHERE pres < 100 LIMIT 10;"
        user_sql = st.text_area("SQL Statement", value=default_sql, height=90)

        if st.button("▶️ Run SQL Query", key="btn_run_custom_sql", type="primary"):
            try:
                conn = sqlite3.connect(self.db_path)
                res_df = pd.read_sql_query(user_sql, conn)
                conn.close()

                st.success(f"Query returned {len(res_df)} rows:")
                st.dataframe(res_df, use_container_width=True)

                # Download CSV
                csv_bytes = res_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Query Result as CSV", data=csv_bytes, file_name="argo_query_result.csv", mime="text/csv")
            except Exception as e:
                st.error(f"SQL Error: {e}")

    def render_guide_page(self):
        """Render comprehensive illustrated Guide & Architecture tour"""
        st.title("📚 Platform Guide & System Architecture")
        st.markdown(
            """
            <div class="info-banner">
                <h4>📚 Complete Reference Guide for Evaluators & Users:</h4>
                <p>
                    Everything you need to know about the <b>ARGO Program</b>, <b>NetCDF format</b>, 
                    <b>Model Context Protocol (MCP)</b>, and how <b>FloatChat</b> revolutionizes autonomous oceanographic telemetry and data discovery.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown(
                """
                ### 🌊 1. What is the ARGO Program?
                - **Autonomous Ocean Probes**: Over ~4,000 autonomous battery-powered robotic floats drift across all the world's oceans.
                - **10-Day Cycle**:
                  1. Descends to a parking depth of **1,000 meters** (1,000 dbar).
                  2. Drifts with deep ocean currents for **9-10 days**.
                  3. Descends to **2,000 meters** deep cast.
                  4. Surfaces while continuously recording **Conductivity/Salinity (PSAL)**, **Temperature (TEMP)**, and **Pressure (PRES)**.
                  5. Transmits data via satellites (Argos/Iridium) to global data assembly centres.
                
                ---
                ### 📦 2. What is NetCDF (`.nc`)?
                - **Network Common Data Form**: A binary, self-describing scientific format used by NOAA, NASA, and INCOIS.
                - **Challenge**: NetCDF files cannot be viewed in standard spreadsheets or SQL databases without specialized scientific libraries (`xarray`, `netCDF4`).
                - **FloatChat Solution**: Ingests `.nc` arrays and transforms them into relational tables in milliseconds.
                """
            )

        with col_g2:
            st.markdown(
                """
                ### ⚡ 3. What is Model Context Protocol (MCP)?
                - **Open Protocol by Anthropic**: MCP standardizes how AI agents discover and execute tools and databases.
                - **How FloatChat Uses MCP**:
                  - The backend exposes MCP tools: `get_schema` and `get_query_response`.
                  - The client interprets user questions in natural language, queries the live schema, constructs SQL, executes it, and formats the response.
                  - Fully decoupled and extensible to Postgres, Vector databases, and Cloud APIs.
                """
            )

            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%), rgba(10, 18, 38, 0.72);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-top: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 14px;
                    padding: 1.1rem;
                    margin-top: 1.2rem;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.35), inset 0 1px 1px rgba(255,255,255,0.2);
                ">
                    <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 6px;">
                        👥 Project Engineering Team & Contributors
                    </div>
                    <div style="font-size: 0.84rem; color: #cbd5e1; margin-bottom: 12px;">
                        Departmental Minor Project • B.Tech Final Year (Civil / Ocean Data Engineering)
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <a href="https://www.linkedin.com/in/aditya-kittad-bbb9532ba/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 9px 13px;">
                            <span style="display: flex; align-items: center; gap: 9px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="15" height="15" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                <span style="font-size: 0.88rem;">ADITYA KITTAD</span>
                            </span>
                            <span style="font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.16); padding: 3px 8px; border-radius: 6px; font-weight: 800;">Connect on LinkedIn ↗</span>
                        </a>
                        <a href="https://www.linkedin.com/in/ganesh-kapure-5309542ba/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 9px 13px;">
                            <span style="display: flex; align-items: center; gap: 9px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="15" height="15" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                <span style="font-size: 0.88rem;">GANESH KAPURE</span>
                            </span>
                            <span style="font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.16); padding: 3px 8px; border-radius: 6px; font-weight: 800;">Connect on LinkedIn ↗</span>
                        </a>
                        <a href="https://www.linkedin.com/in/om-jaiswal-3b2b39249/" target="_blank" rel="noopener noreferrer" class="team-linkedin-btn" style="padding: 9px 13px;">
                            <span style="display: flex; align-items: center; gap: 9px;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="15" height="15" fill="#38bdf8"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z"/></svg>
                                <span style="font-size: 0.88rem;">OM JAISWAL</span>
                            </span>
                            <span style="font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.16); padding: 3px 8px; border-radius: 6px; font-weight: 800;">Connect on LinkedIn ↗</span>
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("👥 Open Full Developer Dossiers (Zero Login Required)", key="guide_open_dossiers_btn", use_container_width=True):
                show_developer_profile_dialog()

        st.markdown("---")
        st.markdown("### 📖 Oceanographic Variable Dictionary:")

        var_df = pd.DataFrame([
            {"Variable": "PRES", "Unit": "dbar (decibars)", "Meaning": "Pressure / Depth (1 dbar is approximately 1 meter of seawater depth)"},
            {"Variable": "TEMP", "Unit": "°C (Celsius)", "Meaning": "In-situ seawater temperature (typically 25-30°C surface down to 2°C at 2000m)"},
            {"Variable": "PSAL", "Unit": "PSU", "Meaning": "Practical Salinity Unit (ocean salinity typically ranges between 34.0 and 36.0 PSU)"},
            {"Variable": "JULD", "Unit": "Days / UTC", "Meaning": "Julian Days relative to 1950-01-01 (measurement timestamp)"},
            {"Variable": "PLATFORM_NUMBER", "Unit": "WMO ID", "Meaning": "Unique international World Meteorological Organization float identifier"},
            {"Variable": "CYCLE_NUMBER", "Unit": "Integer", "Meaning": "The sequential number of the 10-day profiling dive performed by the float"},
        ])
        st.dataframe(var_df, use_container_width=True)

    def render_users_page(self):
        """Render User Management and Access Control"""
        st.title("👥 User Roles & Access Control")
        st.markdown(
            """
            <div class="info-banner">
                <h4>👥 Role-Based Access Control:</h4>
                <p>
                    Manage researcher, oceanographer, and administrator credentials for the FloatChat platform.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        users = st.session_state["users_data"]

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Users", len(users))
        with m2:
            st.metric("Active", len(users[users["status"] == "active"]))
        with m3:
            st.metric("Inactive", len(users[users["status"] == "inactive"]))
        with m4:
            st.metric("Administrators", len(users[users["role"] == "Administrator"]))

        st.markdown("---")

        # Add User Form
        with st.expander("➕ Add New Researcher / Analyst Account"):
            with st.form("new_user_form"):
                u_email = st.text_input("User Email / Username")
                u_pass = st.text_input("Password", type="password")
                u_role = st.selectbox("Access Role", ["Researcher", "Analyst", "Scientist", "Administrator"])
                if st.form_submit_button("Create Account"):
                    if u_email and u_pass:
                        new_row = pd.DataFrame([{
                            "email": u_email,
                            "password": u_pass,
                            "status": "active",
                            "role": u_role,
                            "last_login": "Never"
                        }])
                        st.session_state["users_data"] = pd.concat([st.session_state["users_data"], new_row], ignore_index=True)
                        self.show_toast(f"Created account for {u_email}!")
                        st.rerun()

        # User Table
        for idx, u in users.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            with c1:
                st.markdown(f"**{u['email']}**")
            with c2:
                st.caption(f"Role: {u['role']}")
            with c3:
                status_color = "#10b981" if u["status"] == "active" else "#ef4444"
                st.markdown(f"<span style='color:{status_color}; font-weight:600;'>● {u['status'].upper()}</span>", unsafe_allow_html=True)
            with c4:
                toggle_label = "Deactivate" if u["status"] == "active" else "Activate"
                if st.button(toggle_label, key=f"tog_{idx}"):
                    new_st = "inactive" if u["status"] == "active" else "active"
                    st.session_state["users_data"].loc[idx, "status"] = new_st
                    st.rerun()

    def run(self):
        """Main application runner"""
        st.set_page_config(
            page_title="FloatChat - ARGO Ocean Intelligence",
            page_icon="🌊",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        self._init_session_state()

        self.setup_custom_css()
        self.inject_keep_alive()

        if not st.session_state.get("authenticated", False):
            self.login_page()
            return

        self.render_sidebar()

        # Route to active page
        page = st.session_state.get("current_page", "chats")
        if page == "chats":
            self.render_chat_page()
        elif page == "map":
            self.render_map_page()
        elif page == "analytics":
            self.render_analytics_page()
        elif page == "converter":
            self.render_converter_page()
        elif page == "database":
            self.render_database_page()
        elif page == "guide":
            self.render_guide_page()
        elif page == "users":
            self.render_users_page()


if __name__ == "__main__":
    app = ArgoApp()
    app.run()
