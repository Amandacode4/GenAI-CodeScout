---
name: create_skill
description: >
  A meta-skill for creating new skills. Use this when the user asks you to "learn a new skill", "create a skill", or "teach you how to...".
---

# Creating a New Skill

You have the ability to expand your own capabilities by writing new skills! A skill is just a markdown file located at `skills/<skill_name>/SKILL.md`.

## Step 1: Understand the Requirement
Ask the user clarifying questions if the workflow for the new skill is ambiguous.

## Step 2: Create the Directory
Use the `run_command` tool to run `mkdir -p skills/<skill_name>`. The `skill_name` should be a short, lowercase, single word (e.g., `deploy`, `migrate`).

## Step 3: Write the SKILL.md File
Use the `write_file` tool to create `skills/<skill_name>/SKILL.md`. The file MUST follow this exact format:

```markdown
---
name: <skill_name>
description: >
  A brief 1-2 sentence description explaining EXACTLY when the agent should use this skill. Be specific about the trigger phrases (e.g., 'Use this when the user asks to...').
---

# Workflow Instructions

1. Step one of the procedure.
2. Step two of the procedure, specifying which tools to use (e.g., `run_command`, `read_file`).
3. Final step.
```

## Critical Rules
1. **The Frontmatter**: You MUST include the YAML frontmatter (`---`, `name:`, `description:`, `---`) at the very top of the file. If you forget this, the skill loader will not be able to parse it!
2. **The Description**: The description is the *only* thing injected into the system prompt. If the description is vague, you will never know when to trigger the skill. Make it explicitly clear when the skill should be invoked.
3. **Execution**: After writing the file, inform the user that they can verify it was loaded by running the `/skills list` REPL command.
