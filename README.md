# Code Scout: Autonomous AI Coding Agent 🚀

Welcome to my 5-week engineering journey building **Code Scout**, a fully autonomous AI coding assistant built entirely from scratch during the CAIC Summer of Technology 2026. 

This repository documents the step-by-step evolution of Code Scout from a simple API script into a powerful, extensible platform capable of reading codebases, executing terminal commands, fixing bugs autonomously, and learning new skills dynamically.

---

## 🌟 What is Code Scout?
Code Scout is a terminal-based, autonomous coding agent. Instead of just generating text, Code Scout *takes action*. It features:
- **Interactive REPL & TUI**: Chat with the agent in a standard terminal or a full-screen Textual interface.
- **Autonomous Execution Loop**: Capable of multi-step reasoning, tool dispatching, and verifying its own work.
- **Sandboxed Execution**: Executes safe commands immediately but pauses destructive/modifying commands for user approval.
- **Progressive Disclosure Skills**: Learns complex procedures by loading Markdown-based `SKILL.md` files dynamically.
- **Model Context Protocol (MCP)**: Connects to external MCP servers (like GitHub) to dynamically expand its toolset.

---

## 🏗️ The 5-Week Evolution (Directory Structure)

This repository is organized by week, demonstrating the architectural evolution of the agent. You can explore each folder to see how the complexity scaled.

### [Week 1: The Foundation](week_1/)
We started with the absolute basics. I implemented secure API-key hygiene using `.env`, mastered LLM API mechanics, and built a manual conversation state manager to hold coherent multi-turn conversations without any external frameworks.

### [Week 2: Tools & Terminal UI](week_2/)
I built a custom tool-calling schema from scratch before transitioning to native function calling. The agent gained the ability to fetch web pages, search the web, and connect to its first basic MCP server to read academic papers. Everything was wrapped in a beautiful full-screen Terminal UI (TUI).

### [Week 3: Memory & Filesystem](week_3/)
An agent needs persistence. I added the ability to save/resume sessions to disk and implemented persistent instructions via `AGENTS.md`. More importantly, the agent gained hands: it can now read files, write code, and edit existing files using a precise line-replacement tool.

### [Week 4: Code Scout - The Coding Agent](week_4/)
This is where it became a real coding assistant. I implemented `run_command` with a safety sandbox, allowing the agent to run tests and analyze crashes. I built a persistent `TODO` system to force the agent to verify its changes before stopping. It also gained codebase exploration tools (grep, definitions) and the ability to spin up read-only subagents for research without polluting its main context window.

### [Week 5: The Extensible Platform](week_5/)
The final capstone. Code Scout transformed from a hardcoded script into an extensible platform:
- **Skills System**: By dropping a `SKILL.md` into the `skills/` directory, the agent can learn any new procedure.
- **Configuration as Code**: Hardcoded API endpoints were replaced with a dynamic `config.json`.
- **Dynamic MCP Integration**: Using Streamable HTTP, the agent can connect to external servers (like GitHub) on the fly, seamlessly merging their tools into its own capabilities.

---

## 🚀 Running the Final Version (Week 5)

Want to try out the final, fully-featured version of Code Scout?

### 1. Setup
```bash
# Navigate to the final project directory
cd week_5/project

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy the `.env.example` file to `.env` and add your API keys:
```bash
cp .env.example .env
```
*(You will need at least one Gemini, Groq, or OpenRouter API key).*

### 3. Run the Agent
Start the interactive REPL:
```bash
python agent.py
```
Or start the full-screen TUI:
```bash
python agent.py --tui
```

### 4. Try the Features!
- Type `/skills list` to see what the agent can do automatically (try asking it to "commit my changes").
- Type `/mcp list` to view available external servers.
- Ask it to fix a bug in your code, and watch it explore, edit, and verify!

---
*Built with ❤️ during CAIC SOT 2026. No LangChain or high-level frameworks were used in the making of this agent.*