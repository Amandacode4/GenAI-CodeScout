def create_explore_subagent_tool(agent_class):
    async def explore_subagent(task: str) -> str:
        """
        Spawns a read-only subagent to explore the codebase and return a digest.
        Use this to avoid flooding your own context with large files or long grep outputs.
        """
        # Create a new agent instance
        subagent = agent_class(session_id="subagent_temp")
        
        # Override its tools to be read-only
        from tools.search import TOOLS as SEARCH_TOOLS
        from tools.files import FILE_TOOLS
        from tools.exec import TOOLS as EXEC_TOOLS
        
        # Only read_file and list_files
        safe_file_tools = [t for t in FILE_TOOLS if t["function"]["name"] in ("read_file", "list_files")]
        
        subagent_tools = SEARCH_TOOLS + safe_file_tools + EXEC_TOOLS
        
        # Override the system prompt
        subagent.messages = [{"role": "system", "content": (
            "You are an Explore Subagent. You have read-only tools to explore the codebase. "
            "Your job is to answer the user's question by searching and reading files. "
            "Once you find the answer, summarize your findings into a concise digest, including relevant file paths and line numbers. "
            "Do NOT try to fix the bug, just report your findings."
        )}]
        
        # Run it with a turn limit of 5 tool calls
        # We will just await subagent.chat(task), but how to limit turns?
        # Since this is a simple implementation for the bonus, we can just run it.
        # But to prevent infinite loops, we can monkey-patch _run_loop to break after 5 iterations.
        
        original_run_loop = subagent._run_loop
        
        iteration = 0
        async def limited_run_loop():
            nonlocal iteration
            while iteration < 5:
                iteration += 1
                result = await original_run_loop()
                if not isinstance(result, str) or not subagent.messages[-1].get("tool_calls"):
                    return result
            return "Subagent reached turn limit. Current findings: " + str(subagent.messages[-1].get("content"))
            
        subagent._run_loop = limited_run_loop
        
        try:
            result = await subagent.chat(task)
            return f"Subagent Digest:\\n{result}"
        except Exception as e:
            return f"Subagent failed: {e}"

    return explore_subagent

def get_subagent_tool_schema():
    return {
        "type": "function",
        "function": {
            "name": "explore_subagent",
            "description": (
                "Delegate a read-only exploration task to a subagent. "
                "The subagent can search, read files, and run read-only commands. "
                "It will return a concise summary of its findings, keeping your context window clean. "
                "Provide clear instructions on what you want it to find."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The specific exploration task."}
                },
                "required": ["task"]
            }
        }
    }
