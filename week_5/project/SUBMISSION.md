# Week 5 Submission: The Code Scout Platform

## What Code Scout Does Now
In Week 4, Code Scout evolved from a passive research assistant to an active codebase explorer with an interactive sandbox. However, its tools and procedures were hardcoded into its core logic. Every new tool meant editing `agent.py`, and every new procedure meant bloating the system prompt.

This week, Code Scout has transformed into an extensible platform through two key upgrades:
1. **Agent Skills (Progressive Disclosure)**: Code Scout can now learn complex, multi-step procedures simply by dropping a markdown file into the `skills/` directory. It uses a progressive disclosure architecture: only the skill's name and description are loaded into the system prompt. The actual instructions (and any bundled scripts) are only fetched into the LLM context when the agent actively decides to invoke the `load_skill` tool based on the user's prompt. 
2. **Model Context Protocol (MCP)**: Code Scout can now connect to external servers to access tools it was never shipped with. By using an implementation of `Streamable HTTP`, it can authenticate with secure servers (like GitHub) and dynamically merge their tool schemas into its own active toolset.

## New Features and Implementations

### 1. Configuration as Code
I moved the agent away from hardcoded configurations. The agent now reads from `config.json` to discover available MCP servers. It dynamically substitutes environment variable placeholders (like `${GITHUB_PAT}`) using the local `.env` file, ensuring secrets are never hardcoded or committed to version control.

### 2. The Skills Subsystem
- **Storage**: Skills are stored in the `skills/` directory. Each skill has a `SKILL.md` file containing YAML frontmatter (`name`, `description`) and the markdown body containing the instructions.
- **Loading**: On startup, `agent.py` uses `tools/skills.py` to parse the YAML frontmatter of all available skills and injects them into the agent's base prompt.
- **Execution**: I implemented the `load_skill` tool. When the agent uses it, it reads the requested `SKILL.md` body and any bundled files, injecting them into the context. From there, the agent follows the instructions using its existing toolset (`run_command`, `read_file`, etc).
- **Interactive REPL**: I added the `/skills list` command to the REPL, allowing users to see what skills are currently loaded and available.

### 3. The MCP Manager
I built an `MCPManager` class to handle dynamic server connections using `mcp.client.streamable_http`. 
- **Dynamic Tool Merging**: When a server connects, the manager parses its `list_tools()` response and dynamically converts the input schemas into standard OpenAI tool schemas, merging them into the agent's active tools list.
- **Smart Dispatch**: I implemented a `tool_to_session` router in the manager so `agent.py` can seamlessly forward arbitrary tool calls to the correct remote MCP server.
- **Interactive Session Toggling**: To prevent tool-list bloat (where the model is overwhelmed with 100+ tools), the agent only loads servers on-demand. I added `/mcp list`, `/mcp enable <server_name>`, and `/mcp disable <server_name>` commands to the REPL, allowing users to toggle external servers per-session.

## Feature Spotlight: The Automated Committer & Meta-Skills
To showcase the extensibility of the platform, I created three skills:

### 1. The Commit Workflow Skill
**What it does:** When the user asks the agent to "save my work" or "commit these changes", the agent triggers the `commit` skill. It automatically runs tests, stages files, and writes a conventional commit message.
**How to replicate it:**
1. Run `python agent.py`.
2. Type: `Please save my work and commit these changes.`
3. The agent will load `skills/commit/SKILL.md` and execute the workflow.

### 2. The Code Review Skill
**What it does:** When the user asks to "review my code" or "check for bugs", the agent triggers the `review` skill. It reads the uncommitted `git diff` (or a specific file) and evaluates it against a strict checklist (Security, Secrets, Hardcoded Configuration, Error Handling, Performance).

### 3. The Meta-Skill (A Skill that Writes Skills)
**What it does:** I implemented a `create_skill` meta-skill. This teaches Code Scout how to expand its own capabilities! If you tell it to "learn a new skill for deploying to Vercel", it will use `run_command` and `write_file` to create `skills/deploy/SKILL.md` formatted with the required YAML frontmatter and markdown body. Once created, it immediately becomes available in `/skills list`.

## Testing and Surprises
- **Testing**: I tested the skills loader by creating dummy skills with invalid YAML to ensure it degrades gracefully and skips them instead of crashing. I also tested the REPL commands to ensure I could toggle the GitHub MCP server on and off, observing the live tool list adapt dynamically.
- **Surprises**: Connecting to MCP servers dynamically highlighted the importance of `AsyncExitStack`. When managing multiple streamable HTTP connections that can be toggled on and off per-session, keeping track of asynchronous contexts proved critical to preventing connection leaks. I also learned that if a streamable HTTP connection fails authentication (e.g., HTTP 400), the underlying `anyio` library can throw noisy cancellation errors if the stack isn't managed carefully.
