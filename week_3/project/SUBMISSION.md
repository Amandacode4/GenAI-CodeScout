# Week 3 Submission

This week, I rebuilt the Research Agent from the ground up to solve the amnesia problem from Week 2. The script is no longer a simple procedural loop; it's a robust Object-Oriented system.

## Key Upgrades

### 1. Object-Oriented Architecture
I abstracted the core intelligence into an `Agent` base class (`agent.py`). This class owns the chat loop, the tool registry, and the fallback API pipeline. It knows nothing about the terminal or the UI.
I then built two subclasses:
- `REPLAgent`: A lightweight wrapper that provides the interactive terminal prompt (`/sessions`, `/resume`) and the one-shot CLI mode.
- `TUIAgent`: A Textual App (`tui.py`) that inherits the base brain but overrides the `_emit()` hook to pipe status updates, tool logs, and text streams safely into the UI widgets.

### 2. Persistent Memory (CoALA Episodic & Procedural)
- **Procedural Memory**: On boot, the agent reads `AGENTS.md` and prepends the project rules to its system prompt. This acts as the agent's core instructions on how to behave, how to cite, and when to use which tools.
- **Episodic Memory**: Every conversation is saved to `.agent/sessions/{id}.json`. When you restart the script with `/resume <id>`, the agent reloads the exact JSON message history, allowing it to seamlessly pick up where it left off, complete with all its prior tool knowledge.

### 3. OpenCode-Style File Tools
I implemented a secure `WORKSPACE_ROOT` sandbox in `tools/files.py`. The agent can now:
- `read_file`: With pagination (`start_line`, `read_lines`) and line numbers.
- `write_file`: To dump new findings into the `notes/` directory.
- `edit_file`: To surgically `replace`, `delete`, or `append` lines by number, returning a diff preview to the agent so it can verify its edits.
- `list_files`: To explore the workspace.

### 4. Hugging Face Papers API
I replaced the AlphaXiv MCP server with direct calls to the Hugging Face Papers API (`tools/papers.py`). The agent intelligently routes queries using `paper_search` for academic questions and then calls `read_paper` to ingest the Markdown content or abstract.

## Conclusion
The agent now possesses a past. It can build a long-term research archive in the `notes/` directory, resume investigations across days, and dynamically failover across 8 different free-tier API endpoints if it hits rate limits.
