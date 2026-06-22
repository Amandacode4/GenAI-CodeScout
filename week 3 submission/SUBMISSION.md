# Week 3 Submission

So this week I basically rewrote the whole agent from scratch because the amnesia issue from week 2 was getting annoying. It's fully object-oriented now.

## What changed

### 1. The Agent Class 
I split the brain logic out into a base `Agent` class in `agent.py`. It handles the main loop, tools, and the API fallback stuff without touching the UI. 
Then I made two subclasses:
- `REPLAgent`: for the terminal stuff, added `/sessions` and `/resume` commands.
- `TUIAgent`: ported the Textual app over from last week to subclass the Agent so it can stream directly into the UI.

### 2. Memory 
- **AGENTS.md**: the agent reads this on startup to know how to behave. Kinda like system instructions.
- **Sessions**: it saves every conversation to `.agent/sessions/{id}.json` now. so if you close the terminal, you can just do `/resume <id>` and it picks right back up where u left off.

### 3. File Tools
Added some sandboxing in `tools/files.py` so the model cant go rogue on my hard drive. 
- `read_file` supports line numbers and pagination now.
- `write_file` and `edit_file` let it actually edit notes. The edit one returns a diff preview which helps it not mess up the file.

### 4. Papers API
Ripped out the MCP server from week 2 and wrote custom tools (`paper_search` and `read_paper`) to hit the Hugging Face Papers API directly. It's way cleaner and handles rate limits better.

overall it feels way more like a real app now instead of just a script!
