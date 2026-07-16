---
name: review
description: >
  Review code changes in a file or git diff. Use when the user asks to "review my code", "check for bugs", or "CR this".
---

# Code Review Checklist

When performing a code review, analyze the target code against the following checklist:

1. **Security & Secrets**: Are there any hardcoded API keys, passwords, or secrets? If so, flag them immediately as a CRITICAL violation. Secrets should be loaded from the environment (e.g., `.env`).
2. **Hardcoded Configuration**: Are there any hardcoded URLs, server endpoints, or timeouts that should be externalized to a config file?
3. **Error Handling**: Are network calls and risky operations wrapped in `try/except` blocks? Are exceptions swallowed silently or handled appropriately?
4. **Performance**: Are there any obvious performance bottlenecks? (e.g., N+1 queries, reading entire large files into memory instead of streaming).
5. **Readability & Formatting**: Are variable names descriptive? Does the code follow standard PEP8 (for Python) or language-specific conventions?

## How to execute the review
- If the user specifies a file, read the file using `read_file`.
- If the user does not specify a file but wants you to review their current changes, run `git diff` using `run_command` to get the uncommitted changes.
- Provide a summary report to the user, highlighting issues by checklist category. Suggest specific code snippets to fix the issues.
