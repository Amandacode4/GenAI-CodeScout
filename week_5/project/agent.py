import os
import sys
import json
import asyncio
import datetime
from typing import List, Dict, Any, Callable
from nanoid import generate

from openai import AsyncOpenAI
from dotenv import load_dotenv

from tools.web import web_search, web_fetch, WEB_TOOLS
from tools.papers import paper_search, read_paper, PAPER_TOOLS
from tools.files import read_file, write_file, edit_file, list_files, FILE_TOOLS
from tools.exec import run_command, TOOLS as EXEC_TOOLS
from tools.search import grep, list_definitions, TOOLS as SEARCH_TOOLS
from tools.plan import add_todos, get_todos, mark_todo, _load_todos, TOOLS as PLAN_TOOLS
from tools.subagent import create_explore_subagent_tool, get_subagent_tool_schema
from tools.repomap import build_repo_map, get_repo_map_tool
from tools.skills import get_skills_metadata, load_skill, SKILL_TOOLS
from tools.mcp_manager import MCPManager, load_mcp_config

load_dotenv()

BASE_PROMPT = """You are Code Scout, an autonomous coding agent.
You have access to a variety of tools to explore the codebase, plan out your changes, run tests, and edit files.
If a user asks a question or assigns a task, formulate a plan using add_todos, execute it, and synthesize a comprehensive answer.
You must use your todo tools to track your progress. The system will not let you stop until all todos are verified.
"""

class Agent:
    def __init__(self, session_id: str = None, tools: list = None):
        self.session_id = session_id or generate(size=10)
        self.sessions_dir = os.path.join(".agent", "sessions")
        
        # Initialize tools
        if tools is None:
            self.tools = WEB_TOOLS + PAPER_TOOLS + FILE_TOOLS + EXEC_TOOLS + SEARCH_TOOLS + PLAN_TOOLS + [get_subagent_tool_schema(), get_repo_map_tool()]
        else:
            self.tools = tools
            
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.session_file = os.path.join(self.sessions_dir, f"{self.session_id}.json")
        
        self.messages = []
        self._load_session()
        
        self.mcp_manager = MCPManager()
        self.mcp_config = load_mcp_config()
        
        # Load providers from env
        self.providers = []
        gemini_keys = [
            os.environ.get("GEMINI_API_KEY"),
            os.environ.get("GEMINI_API_KEY_2"),
            os.environ.get("GEMINI_API_KEY_3"),
            os.environ.get("GEMINI_API_KEY_4"),
            os.environ.get("GEMINI_API_KEY_5"),
            os.environ.get("GEMINI_API_KEY_6")
        ]
        
        for idx, key in enumerate(gemini_keys):
            if key:
                self.providers.append({
                    "name": f"Gemini (Key {idx+1})",
                    "client": AsyncOpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=key),
                    "model": "gemini-2.5-flash"
                })
                
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            self.providers.append({
                "name": "Groq",
                "client": AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key),
                "model": "llama-3.3-70b-versatile"
            })
            
        or_key = os.environ.get("OPENROUTER_API_KEY")
        if or_key:
            self.providers.append({
                "name": "OpenRouter",
                "client": AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key),
                "model": "meta-llama/llama-3.3-70b-instruct:free"
            })

    async def initialize(self):
        """Async initialization for MCP connections."""
        if self.mcp_config:
            self._emit("status", "Connecting to default MCP servers...")
            await self.mcp_manager.connect_all(self.mcp_config)

    def _load_system_prompt(self) -> str:
        parts = [BASE_PROMPT]
        
        skills_meta = get_skills_metadata()
        if skills_meta:
            parts.append(skills_meta)
            
        for path in ("AGENTS.md", ".agent/AGENTS.md"):
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        parts.append(f"## Project Rules\\n{f.read()}")
                    break
                except Exception as e:
                    self._emit("status", f"Error reading {path}: {e}")
        return "\\n\\n".join(parts)

    def _load_session(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.messages = data.get("messages", [])
                self._emit("status", f"Loaded session {self.session_id}")
            except Exception as e:
                self._emit("status", f"Failed to load session: {e}")
                
        if not self.messages:
            self.messages = [{"role": "system", "content": self._load_system_prompt()}]
            self._save_session()

    def _save_session(self):
        data = {
            "id": self.session_id,
            "updated_at": datetime.datetime.now().isoformat(),
            "messages": self.messages
        }
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._emit("status", f"Failed to save session: {e}")

    def _emit(self, event_type: str, data: str):
        """Hook for subclasses to intercept UI updates."""
        pass
        
    async def dispatch(self, name: str, args: dict) -> str:
        self._emit("tool_start", name)
        try:
            if name == "web_search": return web_search(args.get("query"), os.environ.get("SERPER_API_KEY"))
            if name == "web_fetch": return web_fetch(args.get("url"))
            if name == "paper_search": return paper_search(args.get("query"))
            if name == "read_paper": return read_paper(args.get("paper_id"))
            if name == "read_file": return read_file(args.get("path"), args.get("start_line", 1), args.get("read_lines", 200))
            if name == "write_file": return write_file(args.get("path"), args.get("content"))
            if name == "edit_file": return edit_file(args.get("path"), args.get("operation"), args.get("start_line"), args.get("end_line"), args.get("content", ""))
            if name == "list_files": return list_files(args.get("path", "."))
            if name == "run_command": return run_command(args.get("command"), timeout=args.get("timeout", 10))
            if name == "grep": return grep(args.get("pattern"), args.get("path", "."), args.get("case_sensitive", False), args.get("max_results", 50))
            if name == "list_definitions": return list_definitions(args.get("path"))
            if name == "add_todos": return add_todos(args.get("todos", []))
            if name == "get_todos": return get_todos()
            if name == "mark_todo": return mark_todo(args.get("todo_id"), args.get("status"), args.get("evidence"))
            if name == "explore_subagent": return await create_explore_subagent_tool(Agent)(args.get("task"))
            if name == "get_repo_map": return build_repo_map()
            if name == "load_skill": return load_skill(args.get("name"))
            
            if name in self.mcp_manager.tool_to_session:
                return await self.mcp_manager.call_tool(name, args)
                
            return f"Unknown tool: {name}"
        except Exception as e:
            return f"Tool exception: {e}"

    async def chat(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        self._save_session()
        return await self._run_loop()

    async def _run_loop(self) -> str:
        if not self.providers:
            return "Error: No API providers configured in .env"
            
        while True:
            response_successful = False
            
            for provider in self.providers:
                try:
                    self._emit("status", f"Connecting to {provider['name']}...")
                    client = provider["client"]
                    
                    active_tools = self.tools + SKILL_TOOLS + self.mcp_manager.openai_tools
                    
                    stream = await client.chat.completions.create(
                        model=provider["model"],
                        messages=self.messages,
                        tools=active_tools,
                        stream=True,
                        temperature=0.3
                    )
                    
                    response_successful = True
                    current_text = ""
                    tool_calls_buffer = {}
                    
                    async for chunk in stream:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            current_text += delta.content
                            self._emit("stream", delta.content)
                            
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                idx = tc.index
                                if idx not in tool_calls_buffer:
                                    tool_calls_buffer[idx] = {
                                        "id": tc.id,
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                if tc.function.name:
                                    tool_calls_buffer[idx]["function"]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments

                    # Reconstruct assistant message
                    assistant_msg = {"role": "assistant"}
                    if current_text:
                        assistant_msg["content"] = current_text
                    
                    if tool_calls_buffer:
                        tool_calls = [tc for idx, tc in sorted(tool_calls_buffer.items())]
                        assistant_msg["tool_calls"] = tool_calls
                        if not current_text:
                            assistant_msg["content"] = None
                            
                    self.messages.append(assistant_msg)
                    self._save_session()
                    
                    if not current_text and not tool_calls_buffer:
                        print("\\n[Warning] Model returned an empty response (possibly a malformed function call). Retrying...", flush=True)
                        self.messages.append({"role": "system", "content": "Your last response was empty or contained a malformed function call. Please formulate a valid plan using the `add_todos` tool."})
                        continue
                    
                    if not tool_calls_buffer:
                        todos = _load_todos()
                        unfinished = [t for t in todos if t["status"] in ["pending", "in_progress", "blocked"]]
                        if todos and unfinished:
                            self._emit("status", "System: Forcing continuation, there are unfinished todos.")
                            self.messages.append({
                                "role": "user", 
                                "content": "You have unfinished items in your todo list. You must complete and verify them. If you are stuck, update the plan. Use get_todos to review your plan, and continue."
                            })
                            self._save_session()
                            continue # Jump to next outer loop iteration
                        else:
                            return current_text
                        
                    # Execute tools
                    for tc in tool_calls:
                        name = tc["function"]["name"]
                        args_str = tc["function"]["arguments"]
                        try:
                            args = json.loads(args_str)
                        except:
                            args = {}
                            
                        result = await self.dispatch(name, args)
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": str(result)
                        })
                    self._save_session()
                    break # Break out of provider loop, continue outer while True loop
                    
                except Exception as e:
                    self._emit("status", f"{provider['name']} failed: {str(e)[:100]}...")
                    continue
                    
            if not response_successful:
                self._emit("status", "All servers are heavily loaded. Waiting 5s before retrying...")
                await asyncio.sleep(5)


class REPLAgent(Agent):
    def _emit(self, event_type: str, data: str):
        if event_type == "status":
            print(f"\\033[90m[{data}]\\033[0m")
        elif event_type == "tool_start":
            print(f"\\033[36mCalling tool: {data}\\033[0m")
        elif event_type == "stream":
            sys.stdout.write(data)
            sys.stdout.flush()

    def list_sessions(self):
        print("\\n\\033[1mAvailable Sessions:\\033[0m")
        try:
            files = os.listdir(self.sessions_dir)
            for f in files:
                if f.endswith(".json"):
                    with open(os.path.join(self.sessions_dir, f), "r") as json_file:
                        data = json.load(json_file)
                        msgs = data.get("messages", [])
                        # Try to find the first user message for a title preview
                        title = "Empty Session"
                        for m in msgs:
                            if m.get("role") == "user":
                                title = m.get("content", "")[:50] + "..."
                                break
                        updated = data.get("updated_at", "Unknown")
                        print(f" - {f.replace('.json','')} | {updated[:10]} | {title}")
        except Exception as e:
            print(f"Error listing sessions: {e}")
        print()

    async def run(self):
        print(f"\\033[1;32mResearch Desk REPL Started. Session ID: {self.session_id}\\033[0m")
        print("Type '/sessions' to list sessions, '/resume <id>' to switch, or 'quit' to exit.")
        while True:
            try:
                user_input = input("\\n\\033[1;34m[You]\\033[0m\\n> ").strip()
                if not user_input: continue
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                if user_input.lower() == '/sessions':
                    self.list_sessions()
                    continue
                if user_input.lower().startswith('/resume'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        self.session_id = parts[1]
                        self.session_file = os.path.join(self.sessions_dir, f"{self.session_id}.json")
                        self.messages = []
                        self._load_session()
                        print(f"\\033[32mSwitched to session {self.session_id}\\033[0m")
                    else:
                        print("Usage: /resume <session_id>")
                    continue
                    
                if user_input.lower() == '/skills list':
                    print("\\n\\033[1mAvailable Skills:\\033[0m")
                    print(get_skills_metadata())
                    print()
                    continue

                if user_input.lower().startswith('/mcp'):
                    parts = user_input.split()
                    if len(parts) == 2 and parts[1] == 'list':
                        print("\\n\\033[1mMCP Servers:\\033[0m")
                        for srv in self.mcp_config.keys():
                            status = "Connected" if srv in self.mcp_manager.servers_connected else "Disconnected"
                            print(f" - {srv} [{status}]")
                        print()
                    elif len(parts) == 3 and parts[1] == 'enable':
                        srv = parts[2]
                        if srv in self.mcp_config:
                            print(f"\\033[90mConnecting to {srv}...\\033[0m")
                            await self.mcp_manager.connect(srv, self.mcp_config[srv])
                            print(f"\\033[32mMCP {srv} enabled.\\033[0m")
                        else:
                            print(f"Server '{srv}' not found in config.json")
                    elif len(parts) == 3 and parts[1] == 'disable':
                        srv = parts[2]
                        if await self.mcp_manager.disable(srv):
                            print(f"\\033[33mMCP {srv} disabled.\\033[0m")
                        else:
                            print(f"MCP {srv} is not currently connected.")
                    else:
                        print("Usage: /mcp list | /mcp enable <name> | /mcp disable <name>")
                    continue

                await self.chat(user_input)
                print() # newline after response
            except (KeyboardInterrupt, EOFError):
                break

    async def run_once(self, query: str):
        print(f"\\033[1;32mResearch Desk - Single Query (Session {self.session_id})\\033[0m")
        await self.chat(query)
        print("\\n")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--tui":
            from tui import TUIAgent
            agent = TUIAgent()
            # Note: TUIAgent needs to await agent.initialize() if it uses MCP!
            agent.run()
        else:
            query = " ".join(sys.argv[1:])
            agent = REPLAgent()
            async def run_single():
                await agent.initialize()
                await agent.run_once(query)
                await agent.mcp_manager.aclose()
            asyncio.run(run_single())
    else:
        agent = REPLAgent()
        async def run_repl():
            await agent.initialize()
            await agent.run()
            await agent.mcp_manager.aclose()
        asyncio.run(run_repl())

if __name__ == "__main__":
    main()