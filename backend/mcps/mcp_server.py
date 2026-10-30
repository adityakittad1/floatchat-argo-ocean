from mcp.server.mcpserver import MCPServer as FastMCP
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import pandas as pd
import numpy as np
import sqlite3
import sqlalchemy
import sys
import os
import re

# IMPORTANT: MCP uses stdio for JSON-RPC. All debug output MUST go to stderr,
# never stdout, or it will corrupt the protocol.
def _log(*args):
    print(*args, file=sys.stderr, flush=True)

load_dotenv()

mcp = FastMCP("sql-agent")

# ── SQLite setup (loads CSVs so no PostgreSQL needed) ──────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # backend/mcps/
_BACKEND_DIR = os.path.dirname(_BASE_DIR)                        # backend/
_DB_PATH = os.path.join(_BACKEND_DIR, "argo.db")
_db_uri = f"sqlite:///{_DB_PATH.replace(os.sep, '/')}"

def _init_sqlite_db():
    """Load CSV files into a local SQLite database if tables do not exist yet."""
    engine = sqlalchemy.create_engine(_db_uri)
    csv_map = {
        "profile":    os.path.join(_BACKEND_DIR, "profile_df.csv"),
        "tech":       os.path.join(_BACKEND_DIR, "tech.csv"),
        "trajectory": os.path.join(_BACKEND_DIR, "trajectory.csv"),
    }
    try:
        inspector = sqlalchemy.inspect(engine)
        existing_tables = inspector.get_table_names()
    except Exception:
        existing_tables = []

    with engine.begin() as conn:
        for table_name, csv_path in csv_map.items():
            if table_name not in existing_tables and os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # Normalize column names to lowercase
                df.columns = [c.lower() for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                _log(f"[argo-db] Initialized {len(df)} rows -> table '{table_name}'")

_init_sqlite_db()

db = SQLDatabase.from_uri(_db_uri)

# Initialize LLM optionally (Anthropic)
llm = None
anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
if anthropic_key and len(anthropic_key) > 20 and not anthropic_key.startswith("your_"):
    try:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-3-5-haiku-20241022")
    except Exception as e:
        _log(f"[argo-mcp] ChatAnthropic initialization note: {e}")

# ── Prompt template ────────────────────────────────────────────────────────────
template = """
Based on the table schema below, write a SQLite-compatible SQL query that would answer the user's question.
{schema}

Question: {question}
SQL Query:

Give only the SQL query as the response. Do not include any explanations or additional text.
"""
prompt = ChatPromptTemplate.from_template(template)

def get_table_schema(_=None):
    return db.get_table_info()

def _clean_sql_query(raw_query: str) -> str:
    """Strip markdown code fencing or preamble from generated SQL."""
    cleaned = raw_query.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    # Remove leading SQL: prefix if any
    cleaned = re.sub(r'^(SQL\s*Query|SQL)\s*:\s*', '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned

def _fallback_nl_to_sql(query: str) -> str:
    """
    Intelligent domain-aware fallback parser for ARGO float queries when external LLM is offline.
    Maps natural language questions to exact, optimized SQLite queries on profile, tech, and trajectory.
    """
    q = query.lower()

    # Direct SQL passthrough
    if q.strip().startswith("select") or q.strip().startswith("with") or q.strip().startswith("pragma"):
        return query.strip()

    # Conceptual inquiries
    if any(k in q for k in ["explain salinity", "what is salinity", "what is psal", "how is salinity measured", "tell me about salinity", "salinity concept", "halocline"]):
        return "-- EXPLANATION: SALINITY_CONCEPT"
    if any(k in q for k in ["explain temperature", "what is temperature", "tell me about temperature", "what is thermocline", "thermocline", "temperature concept"]):
        return "-- EXPLANATION: TEMPERATURE_CONCEPT"
    if any(k in q for k in ["explain pressure", "what is pressure", "what is dbar", "tell me about pressure", "what is depth", "depth vs pressure"]):
        return "-- EXPLANATION: PRESSURE_CONCEPT"
    if any(k in q for k in ["dataset summary", "database overview", "summary of data", "tell me about dataset", "summary statistics"]):
        return "-- EXPLANATION: DATASET_OVERVIEW"
    if any(k in q for k in ["what is argo", "what is an argo", "how does argo work", "who is argo", "tell me about argo"]):
        return "-- EXPLANATION: ARGO_CONCEPT"
    if any(k in q for k in ["what is netcdf", "how does netcdf work", "explain netcdf", "netcdf format"]):
        return "-- EXPLANATION: NETCDF_CONCEPT"
    if any(k in q for k in ["what is mcp", "model context protocol", "explain mcp", "how mcp works"]):
        return "-- EXPLANATION: MCP_CONCEPT"
    if any(k in q for k in ["how does this work", "how floatchat works", "help me", "how to use", "what can you do"]):
        return "-- EXPLANATION: FLOATCHAT_CONCEPT"

    # Float list / nearest floats / locations
    if any(k in q for k in ["nearest", "which float", "what float", "list float", "platform", "floats in", "active float", "all float"]):
        return (
            'SELECT platform_number, project_name, pi_name, data_centre, '
            'ROUND(AVG(latitude), 4) as avg_lat, ROUND(AVG(longitude), 4) as avg_lon, '
            'COUNT(DISTINCT cycle_number) as cycles_count, COUNT(*) as measurements '
            'FROM profile GROUP BY platform_number LIMIT 20;'
        )

    # Technical parameters / BGC / Sensors
    if any(k in q for k in ["bgc", "technical", "tech", "sensor", "parameter", "handbook", "battery"]):
        if "surface" in q or "offset" in q:
            return "SELECT platform_number, cycle_number, technical_parameter_name, technical_parameter_value FROM tech WHERE technical_parameter_name LIKE '%surface%' LIMIT 25;"
        return (
            'SELECT technical_parameter_name, COUNT(*) as count, '
            'ROUND(AVG(technical_parameter_value), 3) as avg_val, '
            'ROUND(MIN(technical_parameter_value), 3) as min_val, '
            'ROUND(MAX(technical_parameter_value), 3) as max_val '
            'FROM tech GROUP BY technical_parameter_name ORDER BY count DESC LIMIT 20;'
        )

    # Trajectory / Movement / GPS track
    if any(k in q for k in ["trajectory", "track", "path", "movement", "drift", "positioning"]):
        return (
            'SELECT platform_number, cycle_number, juld, '
            'ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude, '
            'pres, "temp", psal '
            'FROM trajectory WHERE latitude IS NOT NULL ORDER BY cycle_number ASC LIMIT 50;'
        )

    # Counts / summary
    if any(k in q for k in ["how many", "count", "total rows", "total profile", "number of"]):
        return (
            'SELECT COUNT(*) as total_profile_rows, '
            'COUNT(DISTINCT platform_number) as distinct_floats, '
            'COUNT(DISTINCT cycle_number) as distinct_cycles, '
            'MIN(juld) as earliest_date, MAX(juld) as latest_date '
            'FROM profile;'
        )

    # Average / statistics
    if any(k in q for k in ["average", "avg", "mean", "min", "max", "highest", "lowest", "extreme"]):
        if "salin" in q:
            return (
                'SELECT ROUND(AVG(psal), 3) as avg_salinity, '
                'ROUND(MIN(psal), 3) as min_salinity, '
                'ROUND(MAX(psal), 3) as max_salinity, '
                'COUNT(psal) as measured_samples '
                'FROM profile WHERE psal IS NOT NULL;'
            )
        if "temp" in q:
            return (
                'SELECT ROUND(AVG("temp"), 3) as avg_temperature, '
                'ROUND(MIN("temp"), 3) as min_temperature, '
                'ROUND(MAX("temp"), 3) as max_temperature, '
                'COUNT("temp") as measured_samples '
                'FROM profile WHERE "temp" IS NOT NULL;'
            )
        if "depth" in q or "pres" in q:
            return (
                'SELECT ROUND(AVG(pres), 2) as avg_pressure_dbar, '
                'ROUND(MIN(pres), 2) as min_pressure_dbar, '
                'ROUND(MAX(pres), 2) as max_pressure_dbar, '
                'COUNT(pres) as total_samples '
                'FROM profile WHERE pres IS NOT NULL;'
            )
        return (
            'SELECT ROUND(AVG("temp"), 2) as avg_temp, '
            'ROUND(AVG(psal), 2) as avg_salinity, '
            'ROUND(AVG(pres), 1) as avg_depth_dbar '
            'FROM profile WHERE "temp" IS NOT NULL AND psal IS NOT NULL;'
        )

    # Equator or regional filter
    if "equator" in q:
        return (
            'SELECT platform_number, cycle_number, juld, '
            'ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude, '
            'pres, "temp", psal '
            'FROM profile WHERE latitude BETWEEN -5.0 AND 5.0 '
            'ORDER BY pres ASC LIMIT 50;'
        )

    # Salinity profiles
    if "salin" in q or "psal" in q:
        return (
            'SELECT platform_number, cycle_number, juld, '
            'ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude, '
            'pres as depth_dbar, psal as salinity '
            'FROM profile WHERE psal IS NOT NULL '
            'ORDER BY pres ASC LIMIT 40;'
        )

    # Temperature profiles
    if "temp" in q:
        return (
            'SELECT platform_number, cycle_number, juld, '
            'ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude, '
            'pres as depth_dbar, "temp" as temperature '
            'FROM profile WHERE "temp" IS NOT NULL '
            'ORDER BY pres ASC LIMIT 40;'
        )

    # Depth / Deep ocean
    if "depth" in q or "deep" in q or "pres" in q:
        return (
            'SELECT platform_number, cycle_number, '
            'MAX(pres) as max_depth_dbar, '
            'ROUND("temp", 2) as temp_at_depth, '
            'ROUND(psal, 2) as salinity_at_depth '
            'FROM profile WHERE pres IS NOT NULL '
            'GROUP BY platform_number, cycle_number ORDER BY max_depth_dbar DESC LIMIT 25;'
        )

    # Default profile overview
    return (
        'SELECT platform_number, cycle_number, juld, '
        'ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude, '
        'pres, "temp", psal '
        'FROM profile ORDER BY juld DESC LIMIT 25;'
    )

# ── MCP Tools ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_schema():
    """
    Get the table schema of the ARGO SQLite database (tables: profile, tech, trajectory).
    """
    try:
        schema = db.get_table_info()
        return schema
    except Exception as e:
        return str(e)

def _format_dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 12) -> str:
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

async def get_sql_response(sql_query: str) -> str:
    """
    Given a SQL query, execute it against the SQLite database and return formatted results.
    """
    try:
        clean_sql = _clean_sql_query(sql_query)
        conn = sqlite3.connect(_DB_PATH)
        df = pd.read_sql_query(clean_sql, conn)
        conn.close()

        if df.empty:
            return "*No matching records found in the database.*"

        table_md = _format_dataframe_to_markdown(df, max_rows=12)

        insights = []
        for col in df.columns:
            col_l = col.lower()
            if col_l in ["salinity", "psal", "avg_salinity", "min_salinity", "max_salinity"]:
                insights.append(f"• **Salinity (PSAL)**: Mean = `{df[col].mean():.3f} PSU` (Range: `{df[col].min():.3f}` to `{df[col].max():.3f} PSU`)")
            elif col_l in ["temperature", "temp", "avg_temperature", "min_temperature", "max_temperature"]:
                insights.append(f"• **Temperature (TEMP)**: Mean = `{df[col].mean():.2f} °C` (Range: `{df[col].min():.2f}` to `{df[col].max():.2f} °C`)")
            elif col_l in ["depth_dbar", "pres", "max_depth_dbar", "avg_pressure_dbar"]:
                insights.append(f"• **Pressure / Depth**: Cast Depth Range = `{df[col].min():.1f}` to `{df[col].max():.1f} dbar` (~{df[col].max():.1f} meters)")

        if insights:
            summary = "\n\n**🔬 Quantitative Synthesis & Statistical Summary:**\n" + "\n".join(insights)
            return f"{table_md}{summary}"
        return table_md
    except Exception as e:
        return f"Error executing SQL: {e}"

async def get_sql_query(query: str):
    """
    Given a natural language question, generate a SQL query to answer the question.
    """
    global llm
    if llm is not None:
        try:
            sql_chain = (
                RunnablePassthrough.assign(schema=get_table_schema)
                | prompt
                | llm
                | StrOutputParser()
            )
            raw_sql = sql_chain.invoke({"question": query})
            return _clean_sql_query(raw_sql)
        except Exception as e:
            _log(f"[mcp-server] LLM failed: {e}. Falling back to domain parser.")
    return _fallback_nl_to_sql(query)

@mcp.tool()
async def get_query_response(query: str):
    """
    Given a natural language question, generate a SQL query to answer the question,
    execute it against the ARGO SQLite database, and return the results with the generated SQL.
    """
    try:
        sql_query = await get_sql_query(query)

        # 1. SALINITY ACADEMIC EXPLANATION
        if sql_query == "-- EXPLANATION: SALINITY_CONCEPT":
            conn = sqlite3.connect(_DB_PATH)
            sal_stats = pd.read_sql_query(
                'SELECT COUNT(psal) as count, ROUND(AVG(psal), 3) as avg_sal, ROUND(MIN(psal), 3) as min_sal, ROUND(MAX(psal), 3) as max_sal, ROUND(MIN(pres), 1) as min_pres, ROUND(MAX(pres), 1) as max_pres FROM profile WHERE psal IS NOT NULL;',
                conn
            ).iloc[0]
            sample_df = pd.read_sql_query(
                'SELECT platform_number, cycle_number, pres as depth_dbar, psal as salinity_psu, "temp" as temp_c, ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude FROM profile WHERE psal IS NOT NULL ORDER BY pres ASC LIMIT 8;',
                conn
            )
            conn.close()
            sample_table = _format_dataframe_to_markdown(sample_df, max_rows=8)

            explanation = (
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
            return f"EXPLANATION:\n{explanation}"

        # 2. TEMPERATURE ACADEMIC EXPLANATION
        if sql_query == "-- EXPLANATION: TEMPERATURE_CONCEPT":
            conn = sqlite3.connect(_DB_PATH)
            temp_stats = pd.read_sql_query(
                'SELECT COUNT("temp") as count, ROUND(AVG("temp"), 3) as avg_temp, ROUND(MIN("temp"), 3) as min_temp, ROUND(MAX("temp"), 3) as max_temp, ROUND(MIN(pres), 1) as min_pres, ROUND(MAX(pres), 1) as max_pres FROM profile WHERE "temp" IS NOT NULL;',
                conn
            ).iloc[0]
            sample_df = pd.read_sql_query(
                'SELECT platform_number, cycle_number, pres as depth_dbar, "temp" as temp_c, psal as salinity_psu, ROUND(latitude, 4) as latitude, ROUND(longitude, 4) as longitude FROM profile WHERE "temp" IS NOT NULL ORDER BY pres ASC LIMIT 8;',
                conn
            )
            conn.close()
            sample_table = _format_dataframe_to_markdown(sample_df, max_rows=8)

            explanation = (
                "### 🌡️ Scientific Guide: In-Situ Seawater Temperature & Thermocline Dynamics\n\n"
                "#### 1. Definition & Measurement Physics\n"
                "• **In-Situ Temperature vs Potential Temperature ($\\theta$)**: In-situ temperature is the actual seawater temperature measured at depth. As water descends, adiabatic compression raises its temperature slightly. Potential temperature ($\\theta$) removes this compression effect to reference pressure at the sea surface.\n"
                "• **CTD Thermal Sensors**: Measured using aging-resistant platinum resistance thermometers (PRT) calibrated to the International Temperature Scale 1990 (ITS-90) with an initial accuracy of $\\pm 0.002^\\circ\\text{C}$.\n\n"
                "---\n\n"
                "#### 2. Vertical Thermal Stratification\n"
                "1. **Surface Mixed Layer**: Wind-stirred warm layer exhibiting near-isothermal conditions.\n"
                "2. **The Thermocline (100 – 600 dbar)**: A steep vertical temperature drop separating warm surface waters from the cold ocean interior.\n"
                "3. **Deep Abyssal Ocean (>1,000 dbar)**: Cold, dense polar-origin waters remaining between $1.5^\\circ\\text{C}$ and $3.0^\\circ\\text{C}$.\n\n"
                "---\n\n"
                "#### 3. Civil & Climate Engineering Significance\n"
                "• **Thermosteric Sea-Level Rise**: Thermal expansion of warming seawater accounts for $\\approx 40\\%$ of global sea level rise.\n"
                "• **Tropical Cyclone Heat Potential (TCHP)**: The depth of the $26^\\circ\\text{C}$ isotherm determines ocean heat energy available to fuel severe tropical storms and monsoons.\n\n"
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
            return f"EXPLANATION:\n{explanation}"

        # 3. PRESSURE & DEPTH ACADEMIC EXPLANATION
        if sql_query == "-- EXPLANATION: PRESSURE_CONCEPT":
            conn = sqlite3.connect(_DB_PATH)
            pres_stats = pd.read_sql_query(
                'SELECT COUNT(pres) as count, ROUND(AVG(pres), 1) as avg_p, ROUND(MIN(pres), 1) as min_p, ROUND(MAX(pres), 1) as max_p FROM profile WHERE pres IS NOT NULL;',
                conn
            ).iloc[0]
            conn.close()

            explanation = (
                "### 🏔️ Scientific Guide: Hydrostatic Pressure & Ocean Depth Casts\n\n"
                "#### 1. Hydrostatic Relationship\n"
                "• **The Decibar (dbar) Unit**: In oceanography, depth is measured in hydrostatic pressure units of **decibars (dbar)** (1 dbar = 10,000 Pa).\n"
                "• **Depth Conversion**: Because mean seawater density $\\approx 1,025\\text{ kg/m}^3$ and gravity $g \\approx 9.81\\text{ m/s}^2$:\n"
                "  $$P = \\int_{0}^{z} \\rho(S, T, P) g \\, dz \\implies 1\\text{ dbar} \\approx 0.992\\text{ meters}$$\n"
                "  To high accuracy, **1 dbar corresponds to approximately 1 meter of ocean depth**.\n\n"
                "---\n\n"
                "#### 2. ARGO Sensor Mechanism\n"
                "• Pressure is captured using a micromachined silicon piezoresistive strain gauge sensor rated up to $2,000\\text{ dbar}$ with an accuracy of $\\pm 2.4\\text{ dbar}$.\n\n"
                "---\n\n"
                f"#### 📊 Empirical ARGO Telemetry Statistics (From Live `argo.db`):\n"
                f"• **Total Pressure Samples**: `{int(pres_stats['count']):,}` records\n"
                f"• **Mean Cast Pressure**: `{pres_stats['avg_p']:.1f} dbar`\n"
                f"• **Active Cast Depths**: `{pres_stats['min_p']:.1f} dbar` (Surface) down to `{pres_stats['max_p']:.1f} dbar` (~1,800 meters deep abyssal cast)"
            )
            return f"EXPLANATION:\n{explanation}"

        # 4. DATASET OVERVIEW EXPLANATION
        if sql_query == "-- EXPLANATION: DATASET_OVERVIEW":
            conn = sqlite3.connect(_DB_PATH)
            overview_df = pd.read_sql_query(
                'SELECT COUNT(*) as total_profile_rows, COUNT(DISTINCT platform_number) as distinct_floats, COUNT(DISTINCT cycle_number) as distinct_cycles, ROUND(MIN(pres), 1) as min_depth, ROUND(MAX(pres), 1) as max_depth, ROUND(MIN("temp"), 2) as min_temp, ROUND(MAX("temp"), 2) as max_temp, ROUND(MIN(psal), 2) as min_sal, ROUND(MAX(psal), 2) as max_sal FROM profile;',
                conn
            )
            conn.close()
            overview_table = _format_dataframe_to_markdown(overview_df)
            explanation = (
                "### 📊 Comprehensive ARGO Database Overview (`argo.db`)\n\n"
                "Below is the complete dataset summary across all ingested profile, tech, and trajectory tables:\n\n"
                f"{overview_table}\n\n"
                "• **Relational Tables**: `profile` (CTD measurements), `tech` (engineering sensors & battery), `trajectory` (satellite GPS drift coordinates).\n"
                "• **Ingestion Engine**: Supports on-the-fly scientific NetCDF (`.nc`) decoding and automated SQLite schema generation."
            )
            return f"EXPLANATION:\n{explanation}"

        if sql_query == "-- EXPLANATION: ARGO_CONCEPT":
            explanation = (
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
            return f"EXPLANATION:\n{explanation}"

        if sql_query == "-- EXPLANATION: NETCDF_CONCEPT":
            explanation = (
                "### 📦 What is NetCDF (Network Common Data Form)?\n\n"
                "• **The Oceanographic Standard**: NetCDF (`.nc`) is a binary, self-describing, machine-independent data format widely used by NASA, NOAA, INCOIS, and Copernicus for multi-dimensional scientific arrays.\n"
                "• **Key Dimensions**: ARGO NetCDF files organize data across dimensions like `N_PROF` (profiles/cycles) and `N_LEVELS` (depth levels down to 2,000m).\n"
                "• **FloatChat Ingestion**: Our built-in NetCDF Converter decodes multi-dimensional variables (`TEMP`, `PSAL`, `PRES`, `LATITUDE`, `LONGITUDE`, `CYCLE_NUMBER`), constructs standard relational SQL statements, and stores them in SQLite (`argo.db`) or PostgreSQL for instant SQL querying."
            )
            return f"EXPLANATION:\n{explanation}"

        if sql_query == "-- EXPLANATION: MCP_CONCEPT":
            explanation = (
                "### ⚡ What is the Model Context Protocol (MCP)?\n\n"
                "• **Open Standard for AI Agents**: MCP is an open-standard architecture introduced by Anthropic that connects AI reasoning agents directly to tools, external databases, and local file systems.\n"
                "• **How FloatChat Leverages MCP**:\n"
                "  - Our FastAPI client initializes an MCP client session communicating via JSON-RPC with `mcp_server.py`.\n"
                "  - MCP tools (`get_schema`, `get_query_response`) allow the AI to discover the live database schema dynamically, translate user queries into SQL, execute queries against `argo.db`, and return structured oceanographic answers.\n"
                "  - MCP ensures an extensible, modular architecture ready for global enterprise ocean observation systems."
            )
            return f"EXPLANATION:\n{explanation}"

        if sql_query == "-- EXPLANATION: FLOATCHAT_CONCEPT":
            explanation = (
                "### 💡 How to Use FloatChat:\n\n"
                "1. **💬 Chat Assistant**: Ask any question in plain English (e.g. *'What is the average temperature?'*, *'Show salinity near equator'*, or *'Plot temperature vs depth'*). The AI generates SQL, executes it, and displays both data and interactive charts!\n"
                "2. **🗺️ Geospatial Map**: View real-time positions of ARGO floats across the Indian Ocean, Arabian Sea, and Bay of Bengal. Click any float to see its battery, depth, and cycle specs.\n"
                "3. **🔄 NetCDF Converter**: Ingest NetCDF files (`.nc`), generate clean SQL, download `.sql` files, and import records into SQLite with 1 click.\n"
                "4. **📈 Analytics**: Inspect T-S diagrams, thermocline depths, and regional ocean basin comparisons.\n"
                "5. **🗄️ Database Hub**: Inspect tables (`profile`, `tech`, `trajectory`), preview rows, and test custom SQL queries!"
            )
            return f"EXPLANATION:\n{explanation}"

        result = await get_sql_response(sql_query)
        return f"SQL_QUERY:\n{sql_query}\n\nRESULT:\n{result}"
    except Exception as e:
        return f"Query processing error: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
