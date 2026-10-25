import os
import sys
import traceback
from typing import Optional
from dotenv import load_dotenv

# Ensure backend root is in sys.path
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from utils.logger import logger
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = None
        self.tools = []
        self.messages = []
        self.logger = logger

        # Initialize optional Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and len(api_key) > 20 and not api_key.startswith("your_"):
            try:
                from anthropic import Anthropic
                self.llm = Anthropic(api_key=api_key)
            except Exception as e:
                self.logger.warning(f"Anthropic initialization skipped: {e}")

    async def connect_to_server(self, server_script_path: str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server script must be a Python or JavaScript file")

            command = sys.executable if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=dict(os.environ)
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()
            self.logger.info("Connected to MCP server")

            mcp_tools = await self.get_mcp_tools()

            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in mcp_tools
            ]

            self.logger.info(f"Available MCP tools: {[tool['name'] for tool in self.tools]}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            traceback.print_exc()
            raise e

    async def get_mcp_tools(self):
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            self.logger.error(f"Failed to get MCP tools: {e}")
            raise e

    async def get_table_schema(self):
        try:
            response = await self.session.call_tool("get_schema", {})
            return response
        except Exception as e:
            self.logger.error(f"Failed to get table schema: {e}")
            raise e

    async def _format_mcp_response_to_markdown(self, query: str, tool_result_text: str) -> str:
        """Format raw MCP tool output into an informative conversational markdown message."""
        if "EXPLANATION:" in tool_result_text:
            content = tool_result_text.replace("EXPLANATION:", "").strip()
            return content

        sql_part = ""
        result_part = tool_result_text

        if "SQL_QUERY:" in tool_result_text and "RESULT:" in tool_result_text:
            parts = tool_result_text.split("RESULT:", 1)
            sql_part = parts[0].replace("SQL_QUERY:", "").strip()
            result_part = parts[1].strip()

        # Build response
        md = []
        md.append(f"### 🌊 ARGO Ocean Insights")
        md.append(f"**Research Inquiry**: *\"{query}\"*\n")

        # Explain what the data represents
        q_lower = query.lower()
        if "salin" in q_lower:
            md.append("🔬 **Oceanographic Parameter**: Practical Salinity (PSAL) • Measured via electrical conductivity (PSS-78 scale in PSU).")
        elif "temp" in q_lower:
            md.append("🌡️ **Oceanographic Parameter**: In-situ Temperature (TEMP) • Capturing vertical thermal stratification and thermocline structure.")
        elif "depth" in q_lower or "pres" in q_lower:
            md.append("🏔️ **Oceanographic Parameter**: Hydrostatic Pressure / Depth (PRES) • Measured in decibars (1 dbar ≈ 1 meter).")
        else:
            md.append("🛰️ **Oceanographic Telemetry**: Autonomous robotic profiling floats transmitting observations via satellite.")

        if sql_part:
            md.append("\n#### 🔍 Generated SQL Query (via MCP Protocol):")
            md.append(f"```sql\n{sql_part}\n```")

        md.append("\n#### 📊 Empirical Observations from `argo.db`:")
        if result_part and result_part != "[]" and result_part != "NO_RECORDS":
            if "|" in result_part:
                # Direct rich Markdown table rendering
                md.append(result_part)
            else:
                md.append(f"```text\n{result_part}\n```")
        else:
            md.append("*No matching observations found in current database subset.*")

        md.append("\n---\n💡 *Tip: Check out the **Geospatial Map** to view float coordinates or the **NetCDF Converter** to ingest more profiles.*")

        return "\n".join(md)

    async def process_query(self, query: str):
        try:
            self.logger.info(f"Processing query: {query}")
            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)

            # Try LLM tool-calling if LLM is available
            used_llm = False
            if self.llm is not None:
                try:
                    response = await self.call_llm()
                    if response.content[0].type == "text" and len(response.content) == 1:
                        assistant_message = {"role": "assistant", "content": response.content[0].text}
                        self.messages.append(assistant_message)
                        return self.messages

                    assistant_message = {
                        "role": "assistant",
                        "content": response.to_dict()["content"]
                    }
                    self.messages.append(assistant_message)

                    for content in response.content:
                        if content.type == "tool_use":
                            tool_name = content.name
                            tool_args = content.input
                            tool_use_id = content.id
                            self.logger.info(f"Calling MCP tool: {tool_name} with args: {tool_args}")
                            result = await self.session.call_tool(tool_name, tool_args)
                            self.messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": result.content,
                                    }
                                ]
                            })
                    # Call LLM once more to summarize
                    final_response = await self.call_llm()
                    if final_response.content:
                        self.messages.append({"role": "assistant", "content": final_response.content[0].text})
                    used_llm = True
                except Exception as e:
                    self.logger.warning(f"LLM tool calling encountered an issue ({e}). Using direct MCP tool execution.")

            if not used_llm:
                # Direct MCP Tool Execution via the MCP session
                tool_res = await self.session.call_tool("get_query_response", {"query": query})
                raw_text = ""
                if hasattr(tool_res, "content"):
                    for item in tool_res.content:
                        if hasattr(item, "text"):
                            raw_text += item.text
                        else:
                            raw_text += str(item)
                else:
                    raw_text = str(tool_res)

                formatted_answer = await self._format_mcp_response_to_markdown(query, raw_text)
                assistant_message = {"role": "assistant", "content": formatted_answer}
                self.messages.append(assistant_message)

            return self.messages
        except Exception as e:
            self.logger.error(f"Failed to process query: {e}")
            traceback.print_exc()
            raise e

    async def call_llm(self):
        try:
            self.logger.info("Calling Anthropic LLM")
            # Anthropic 1.x omits temperature parameter
            response = self.llm.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=2500,
                messages=self.messages,
                tools=self.tools,
            )
            return response
        except Exception as e:
            self.logger.error(f"Failed to call LLM: {e}")
            raise e

    async def get_sql_query(self, query: str):
        try:
            response = await self.session.call_tool("get_query_response", {"query": query})
            return response
        except Exception as e:
            self.logger.error(f"Failed to get SQL query: {e}")
            raise e

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            traceback.print_exc()
