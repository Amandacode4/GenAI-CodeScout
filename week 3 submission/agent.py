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

load_dotenv()

BASE_PROMPT = """You are Research Desk, an intelligent research assistant.
You have access to a variety of tools to search the web, read academic papers, and save your findings to local files.
If a user asks a question, formulate a plan, use your tools to gather information, and synthesize a comprehensive answer.
Always cite your sources using inline markdown links.
"""

ALL_TOOLS = WEB_TOOLS + PAPER_TOOLS + FILE_TOOLS

class Agent:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or generate(size=10)
        self.sessions_dir = os.path.join(".agent", "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.session_file = os.path.join(self.sessions_dir, f"{self.session_id}.json")
        
        self.messages = []
        self._load_session()
        
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

    def _load_system_prompt(self) -> str:
        parts = [BASE_PROMPT]
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
                    
                    stream = await client.chat.completions.create(
                        model=provider["model"],
                        messages=self.messages,
                        tools=ALL_TOOLS,
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
                    
                    if not tool_calls_buffer:
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

                await self.chat(user_input)
                print()
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
            agent.run()
        else:
            query = " ".join(sys.argv[1:])
            agent = REPLAgent()
            asyncio.run(agent.run_once(query))
    else:
        agent = REPLAgent()
        asyncio.run(agent.run())

if __name__ == "__main__":
    main()