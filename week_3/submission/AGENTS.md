# Research Desk Rules

## Citations
- Always include source URLs inline when quoting information: [title](url)
- Prefer primary sources and official documentation over blog posts where possible.

## Notes
- Save significant findings to the `notes/` folder as markdown files.
- Keep filenames simple, using lowercase letters and hyphens (e.g. `notes/transformer-attention.md`).
- Do not overwrite existing notes unless specifically requested. Use the `edit_file` tool to update them instead.

## Search and Tool Routing
- Use `paper_search` and `read_paper` for ML, academic research, and literature questions.
- Use `web_search` and `web_fetch` for current events, blogs, and general web searches.
- Search for URLs before attempting to fetch them; do not guess links.
- Truncate fetched pages and quote only the relevant sections.
- To save a new note: `write_file("notes/...")`
- To review previous research: `list_files("notes/")` followed by `read_file`.
