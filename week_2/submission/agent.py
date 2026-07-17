import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

from tools import web_search, web_fetch, LOCAL_TOOLS

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_KEY_2 = os.environ.get("GEMINI_API_KEY_2", "")
GEMINI_API_KEY_3 = os.environ.get("GEMINI_API_KEY_3", "")
GEMINI_API_KEY_4 = os.environ.get("GEMINI_API_KEY_4", "")
GEMINI_API_KEY_5 = os.environ.get("GEMINI_API_KEY_5", "")
GEMINI_API_KEY_6 = os.environ.get("GEMINI_API_KEY_6", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

PROVIDERS = []

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Add multiple Gemini keys if they exist
gemini_keys = [
    GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3, 
    GEMINI_API_KEY_4, GEMINI_API_KEY_5, GEMINI_API_KEY_6
]

for idx, key in enumerate(gemini_keys):
    if key:
        PROVIDERS.append({
            "name": f"Gemini (Key {idx+1})",
            "client": AsyncOpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=key),
            "model": "gemini-2.5-flash"
        })

if GROQ_API_KEY:
    PROVIDERS.append({
        "name": "Groq",
        "client": AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY),
        "model": "llama-3.3-70b-versatile"
    })

if OPENROUTER_API_KEY:
    PROVIDERS.append({
        "name": "OpenRouter",
        "client": AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY),
        "model": "meta-llama/llama-3.3-70b-instruct:free"
    })

MCP_SERVER_URL = "https://api.alphaxiv.org/mcp/v1"

class ResearchAgent:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": "You are a helpful research assistant. Use tools to search the web, read pages, and find academic papers to answer the user's questions. STRICT RULE: You must use the native JSON tool calling feature. NEVER output raw text like <function\\name{...}<\\function> or XML to call tools."}
        ]
        
    async def get_response(self, user_input: str, status_callback=None, stream_callback=None) -> str:
        self.messages.append({"role": "user", "content": user_input})
        
        openai_tools = list(LOCAL_TOOLS)
        
        if status_callback:
            status_callback("Connecting to AlphaXiv MCP server...")
            
        try:
            async with sse_client(MCP_SERVER_URL) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    mcp_tools_res = await session.list_tools()
                    for tool in mcp_tools_res.tools:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        })
                    
                    if status_callback:
                        status_callback("AlphaXiv MCP connected successfully.")
                        
                    return await self._run_loop(openai_tools, status_callback, stream_callback, session)
        except Exception as e:
            if status_callback:
                status_callback(f"MCP server unavailable, falling back to local tools. Error: {e}")
            return await self._run_loop(openai_tools, status_callback, stream_callback, None)
            
    async def _run_loop(self, openai_tools, status_callback, stream_callback, session):
        # Agent loop
        for _ in range(15):
            if status_callback:
                status_callback("Thinking...")
                
            response_successful = False
            current_content = ""
            tool_calls_list = []
            
            while not response_successful:
                for provider in PROVIDERS:
                    try:
                        response = await provider["client"].chat.completions.create(
                            model=provider["model"],
                            messages=self.messages,
                            tools=openai_tools,
                            stream=True
                        )
                        if status_callback:
                            status_callback(f"Connected to {provider['name']} ({provider['model']})")
                            
                        # Try to stream the response
                        current_content = ""
                        tool_calls_dict = {}
                        
                        async for chunk in response:
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta
                            if delta.content:
                                current_content += delta.content
                                if stream_callback:
                                    stream_callback(delta.content)
                            if delta.tool_calls:
                                for tc in delta.tool_calls:
                                    if tc.index not in tool_calls_dict:
                                        tool_calls_dict[tc.index] = {
                                            "id": tc.id,
                                            "type": "function",
                                            "function": {"name": tc.function.name, "arguments": ""}
                                        }
                                    if tc.function.arguments:
                                        tool_calls_dict[tc.index]["function"]["arguments"] += tc.function.arguments
                        
                        tool_calls_list = list(tool_calls_dict.values())
                        response_successful = True
                        break # Successfully streamed!
                        
                    except Exception as e:
                        if status_callback:
                            status_callback(f"{provider['name']} failed: {str(e)[:100]}...")
                        continue
                        
                if not response_successful:
                    if status_callback:
                        status_callback("All servers are heavily loaded. Waiting 10s before retrying...")
                    await asyncio.sleep(10)
            
            # Construct the final message to append to history
            message_to_append = {"role": "assistant"}
            if current_content:
                message_to_append["content"] = current_content
            if tool_calls_list:
                message_to_append["tool_calls"] = tool_calls_list
            
            self.messages.append(message_to_append)
            
            if not tool_calls_list:
                return current_content
            
            async def execute_tool(tool_call):
                name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}
                    
                if status_callback:
                    status_callback(f"Calling tool: {name}")
                    
                # Execute local tools off the main thread to prevent UI freezing
                if name == "web_search":
                    result = await asyncio.to_thread(web_search, args.get("query", ""), SERPER_API_KEY)
                elif name == "web_fetch":
                    result = await asyncio.to_thread(web_fetch, args.get("url", ""))
                elif name == "save_research_note":
                    from tools import save_research_note
                    result = await asyncio.to_thread(save_research_note, args.get("filename", ""), args.get("content", ""))
                # Execute MCP tools (already async)
                else:
                    try:
                        if session:
                            mcp_result = await session.call_tool(name, args)
                            result = mcp_result.content[0].text if mcp_result.content else ""
                        else:
                            result = "Error: MCP server is disconnected."
                    except Exception as e:
                        result = f"Error calling MCP tool: {str(e)}"
                        
                return {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                }
                
            # Run all tool calls concurrently!
            tool_results = await asyncio.gather(*(execute_tool(tc) for tc in tool_calls_list))
            self.messages.extend(tool_results)
                
        return "Agent hit iteration limit without finding a final answer."

async def run_cli():
    agent = ResearchAgent()
    print("Research Agent CLI (type 'exit' to quit)")
    while True:
        query = input("\nYou: ")
        if query.lower() in ["exit", "quit"]:
            break
        
        def status_update(msg):
            print(f"[Status] {msg}")
            
        print("\nAgent: ", end="")
        answer = await agent.get_response(query, status_update)
        print(answer)

if __name__ == "__main__":
    asyncio.run(run_cli())
