# Research Desk Rules

## Citations
- Always include source URLs inline: [title](url)
- Prefer primary sources and official docs over blog posts

## Notes
- Save long findings to notes/ as markdown files
- Filename: lowercase, hyphens, topic-based (e.g. notes/transformer-attention.md)
- Do not overwrite existing notes unless requested; use edit_file to update existing notes

## Search and Tool Routing
- Use `paper_search` + `read_paper` for ML/academic/literature questions
- Use `web_search` + `web_fetch` for current events, blogs, and general web docs
- Search before fetching — don't fetch URLs blindly
- Truncate fetched pages; quote only what's relevant
- To save new notes, use `write_file("notes/...")`
- To recall past work, use `list_files("notes/")` then `read_file`
