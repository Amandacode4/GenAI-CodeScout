import asyncio
import json
import os
import re
from contextlib import AsyncExitStack

from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

def load_mcp_config(path="config.json"):
    """Read config.json and substitute ${ENV_VAR} references from the environment."""
    if not os.path.exists(path):
        return {}
        
    raw = open(path).read()

    def substitute(match):
        var = match.group(1)
        value = os.environ.get(var)
        if value is None:
            raise RuntimeError(f"config.json references ${{{var}}}, but it isn't set in your .env")
        return value

    resolved = re.sub(r"\$\{([A-Z0-9_]+)\}", substitute, raw)
    try:
        return json.loads(resolved).get("mcpServers", {})
    except json.JSONDecodeError:
        return {}

class MCPManager:
    """Connects to every server in the config and exposes their tools as one flat list."""

    def __init__(self):
        self.stack = AsyncExitStack()
        self.openai_tools = []          # merged tool schemas, for the model
        self.tool_to_session = {}       # tool name -> the session that owns it
        self.servers_connected = set()

    async def connect(self, name: str, cfg: dict):
        if name in self.servers_connected:
            return
            
        try:
            read, write, _ = await self.stack.enter_async_context(
                streamablehttp_client(cfg["url"], headers=cfg.get("headers"))
            )
            session = await self.stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            tools = await session.list_tools()
            for tool in tools.tools:
                tool_name = f"{name}.{tool.name}"
                self.tool_to_session[tool_name] = session
                
                self.openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                })
            self.servers_connected.add(name)
            return len(tools.tools)
        except Exception as e:
            raise Exception(f"Failed to connect to MCP '{name}': {e}")

    async def connect_all(self, servers: dict):
        for name, cfg in servers.items():
            try:
                count = await self.connect(name, cfg)
                print(f"connected '{name}': {count} tools")
            except Exception as e:
                print(e)

    async def disable(self, name: str):
        if name not in self.servers_connected:
            return False
            
        to_remove = [t for t in self.tool_to_session.keys() if t.startswith(f"{name}.")]
        for t in to_remove:
            del self.tool_to_session[t]
            
        self.openai_tools = [t for t in self.openai_tools if not t["function"]["name"].startswith(f"{name}.")]
        self.servers_connected.remove(name)
        return True

    async def call_tool(self, name: str, args: dict) -> str:
        session = self.tool_to_session.get(name)
        if not session:
            return f"Error: MCP tool {name} not found or disconnected."
            
        actual_name = name.split(".", 1)[1] if "." in name else name
        result = await session.call_tool(actual_name, args)
        return result.content[0].text if result.content else ""

    async def aclose(self):
        await self.stack.aclose()
