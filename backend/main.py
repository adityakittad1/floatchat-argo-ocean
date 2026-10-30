import os
import sys

# Ensure backend root is in sys.path
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from mcps.mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import uvicorn

load_dotenv()

class Settings(BaseSettings):
    server_script_path: str = os.path.join(_BASE_DIR, "mcps", "mcp_server.py")

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    client = MCPClient()
    try:
        await client.connect_to_server(settings.server_script_path)
    except Exception as e:
        print(f"[Lifespan Warning] Initial MCP connection attempt: {e}")

    app.state.client = client

    # Continuous background watchdog to keep MCP agent permanently awake
    stop_event = asyncio.Event()

    async def _keep_alive_watchdog():
        while not stop_event.is_set():
            try:
                await asyncio.sleep(30)
                if hasattr(app.state, "client") and app.state.client is not None:
                    await app.state.client.ensure_connected()
            except asyncio.CancelledError:
                break
            except Exception as e:
                pass

    watchdog_task = asyncio.create_task(_keep_alive_watchdog())

    yield

    stop_event.set()
    watchdog_task.cancel()
    try:
        await watchdog_task
    except (asyncio.CancelledError, Exception):
        pass
    await client.cleanup()

app = FastAPI(
    title="FloatChat - ARGO MCP Backend API",
    description="Model Context Protocol (MCP) Backend for Autonomous ARGO Float Ocean Data Discovery & Visualization",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class Message(BaseModel):
    role: str
    content: Any

class ToolCallRequest(BaseModel):
    name: str
    args: Dict[str, Any]

@app.get("/")
async def root():
    """Root health check endpoint."""
    return {
        "status": "online",
        "service": "FloatChat ARGO MCP Server",
        "version": "2.0.0",
        "keep_alive": True,
        "endpoints": ["/tools", "/get_schema", "/query", "/get_sql_query", "/health", "/keepalive", "/ping"]
    }

@app.get("/health")
async def health():
    is_mcp_ok = hasattr(app.state, "client") and app.state.client.session is not None
    return {
        "status": "healthy",
        "mcp_connected": is_mcp_ok,
        "keep_alive": True,
        "service": "FloatChat ARGO MCP Backend"
    }

@app.get("/keepalive")
@app.get("/ping")
async def keepalive():
    """Explicit keep-alive ping for watchdog and external monitoring to prevent sleeping."""
    if hasattr(app.state, "client") and app.state.client is not None:
        await app.state.client.ensure_connected()
    return {
        "status": "awake",
        "agent": "FloatChat MCP Agent",
        "active": True
    }

@app.post("/get_schema")
async def get_schema():
    """Get the table schema from the MCP server."""
    try:
        schema = await app.state.client.get_table_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a user query and return the response."""
    try:
        messages = await app.state.client.process_query(request.query)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_sql_query")
async def get_sql_query(request: QueryRequest):
    """Get the SQL query generated from a natural language question."""
    try:
        sql_query = await app.state.client.get_sql_query(request.query)
        return {"sql_query": sql_query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_tools():
    """Get the list of available tools."""
    try:
        tools = await app.state.client.get_mcp_tools()
        return {"tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
