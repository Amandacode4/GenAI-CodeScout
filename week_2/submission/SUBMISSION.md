# Week 2 Submission: Research Agent (Definitive Edition)

## What I Built
I built a Perplexity-style research agent capable of searching the web, reading web pages, querying academic papers via the AlphaXiv MCP server, and saving those findings directly to local files. The entire system is enclosed in a responsive, split-panel Terminal User Interface (TUI) built with Textual, featuring a chat panel for user interaction, a real-time token streaming display, and a side panel for logging tool activity. 

The agent loop works by querying the OpenAI SDK with `stream=True`. It handles both local tools (web search, web fetch, save notes) and remote MCP tools (fetched via an SSE connection to AlphaXiv). During the streamed response, the system intelligently buffers tool calls (since OpenAI streams function arguments piece by piece) and executes them once complete, handling any failures gracefully by returning string errors back to the model.

## Design Decision
One major design decision was implementing **real-time token streaming inside a Textual TUI**. Textual's standard `RichLog` does not natively support character-by-character appending very well. Instead of fighting `RichLog`, I designed a custom dynamic `Static` widget (`#stream_display`) that becomes visible during generation. The LLM streams its text chunks directly into this widget's update loop via an async callback. Once the model finishes answering, the `Static` widget is hidden and the final completed block is written cleanly into the `RichLog`. This creates a beautiful "typing" effect without UI stuttering.

## What Surprised Me
I was surprised by how seamlessly the Model Context Protocol (MCP) bridges the gap between third-party infrastructure and local agent loops. Being able to fetch the AlphaXiv tool schemas directly via `session.list_tools()`, convert them to the OpenAI JSON schema format, and dynamically pass them into `tools=` without writing any manual parsing logic felt incredibly powerful.

## Bonus Challenges Completed
I was able to push the week 2 limits and implement **all** of the bonus challenges:
1. **Split-panel TUI:** Implemented a right-hand sidebar strictly for real-time tool logs.
2. **Streaming:** Used `AsyncOpenAI` with `stream=True` to provide a real-time Perplexity-like typing effect.
3. **Save Research Note Tool:** Added `save_research_note` to dynamically create a `notes/` directory and save markdown findings across sessions.
4. **Error Recovery:** Agent loop elegantly catches timeouts and MCP errors and relays them safely back to the LLM.
5. **Multi-API Fallback:** Built an automatic failover system that loops through 6 Gemini keys and an OpenRouter endpoint to instantly recover from 429 Rate Limit errors mid-thought.
6. **Parallel Execution:** Implemented `asyncio.gather` and `asyncio.to_thread` to execute multiple tool calls (e.g. 3 web fetches) concurrently without blocking the Textual UI main thread.
