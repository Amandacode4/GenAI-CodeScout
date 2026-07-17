# Week 3 Submission

For Week 3, I restructured the agent to use an object-oriented approach to solve the memory issues from the previous week.

## Changes Made

### 1. Agent Class
The core logic now lives in a base `Agent` class in `agent.py`. It manages the API fallback, tools, and the main chat loop independently from the UI. 
I created two subclasses for the interfaces:
- `REPLAgent`: Handles the interactive terminal and one-shot CLI commands. I also added `/sessions` and `/resume` commands here.
- `TUIAgent`: Wraps the Textual app from Week 2 around the base Agent class so it can handle streaming directly in the UI.

### 2. Memory
- **AGENTS.md**: The agent reads this file on startup to load project rules into its system prompt.
- **Sessions**: The agent saves conversation history to `.agent/sessions/{id}.json`. You can use `/resume <id>` to reload a previous session state.

### 3. File Tools
I added a `WORKSPACE_ROOT` sandbox in `tools/files.py` to keep file operations constrained to the project folder.
- `read_file` now supports line numbers and pagination.
- `write_file` and `edit_file` allow the agent to save and modify research notes. `edit_file` returns a diff preview to help the agent catch formatting mistakes.

### 4. Papers API
I removed the AlphaXiv MCP server and wrote custom `paper_search` and `read_paper` tools to interact directly with the Hugging Face Papers API.

Overall, the agent can now maintain long-term context across multiple sessions and safely manage a research archive in the notes directory.
