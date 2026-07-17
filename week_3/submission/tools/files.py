import os
import glob
from pathlib import Path

# Load workspace root from env, default to current directory
WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))

def resolve_path(path_str: str) -> str:
    """Resolve a path against WORKSPACE_ROOT and ensure it doesn't escape the sandbox."""
    try:
        # Convert path to absolute path
        full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path_str))
        # Ensure the resolved path starts with the workspace root
        if not full_path.startswith(WORKSPACE_ROOT):
            raise ValueError(f"Path '{path_str}' escapes workspace root")
        return full_path
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> str:
    """Read a window of lines from a file, adding line numbers."""
    try:
        full_path = resolve_path(path)
        if not os.path.isfile(full_path):
            return f'{{"error": "File not found: {path}"}}'
            
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        
        # 1-indexed start line
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + read_lines)
        
        chunk = lines[start_idx:end_idx]
        has_more = end_idx < total_lines
        
        output_lines = []
        for i, line in enumerate(chunk):
            line_num = start_idx + i + 1
            output_lines.append(f"{line_num:4d}| {line.rstrip()}")
            
        content = "\\n".join(output_lines)
        
        # Cap output at ~12k chars as a safety net
        if len(content) > 12000:
            content = content[:12000] + "\\n... (truncated due to length)"
            has_more = True
            
        result = {
            "content": content,
            "total_lines": total_lines,
            "has_more": has_more
        }
        return str(result)
    except Exception as e:
        return f'{{"error": "Failed to read file: {e}"}}'

def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist. Overwrites existing."""
    try:
        full_path = resolve_path(path)
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f'{{"content": "Successfully wrote to {path}"}}'
    except Exception as e:
        return f'{{"error": "Failed to write file: {e}"}}'

def edit_file(path: str, operation: str, start_line: int, end_line: int = None, content: str = "") -> str:
    """Edit a file using replace, delete, or append operations by line number."""
    try:
        full_path = resolve_path(path)
        if not os.path.isfile(full_path):
            return f'{{"error": "File not found: {path}"}}'
            
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Ensure trailing newline on the content lines if needed, but splitlines is safer
        new_lines_list = [line + "\\n" for line in content.splitlines()] if content else []
        
        start_idx = max(0, start_line - 1)
        end_idx = max(0, end_line - 1) if end_line is not None else start_idx
        
        if operation == "replace":
            if end_line is None:
                return '{"error": "end_line required for replace"}'
            del lines[start_idx:end_idx + 1]
            lines[start_idx:start_idx] = new_lines_list
            
        elif operation == "delete":
            if end_line is None:
                return '{"error": "end_line required for delete"}'
            del lines[start_idx:end_idx + 1]
            
        elif operation == "append":
            # Insert AFTER start_line (start_idx is start_line - 1, so insert at start_idx + 1)
            insert_idx = start_idx + 1
            if start_line == 0:
                insert_idx = 0
            lines[insert_idx:insert_idx] = new_lines_list
            
        else:
            return f'{{"error": "Unknown operation: {operation}"}}'
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        # Generate a small diff preview
        preview_start = max(0, start_idx - 2)
        preview_end = min(len(lines), start_idx + len(new_lines_list) + 2)
        preview_lines = []
        for i in range(preview_start, preview_end):
            preview_lines.append(f"{i+1:4d}| {lines[i].rstrip()}")
            
        preview = "\\n".join(preview_lines)
        return f'{{"content": "Edit successful. Preview:\\n{preview}"}}'
        
    except Exception as e:
        return f'{{"error": "Failed to edit file: {e}"}}'

def list_files(path: str = ".") -> str:
    """List files in a directory matching an optional glob pattern."""
    try:
        full_path = resolve_path(path)
        if os.path.isfile(full_path):
            return f'{{"content": "Path is a file: {path}"}}'
            
        if os.path.isdir(full_path):
            # List all files recursively up to a certain depth or just the dir?
            # The prompt suggested glob. We can support glob patterns.
            # Let's just list the directory contents for simplicity if no * is present.
            files = os.listdir(full_path)
            return f'{{"content": {files}}}'
        else:
            # Assume it's a glob pattern
            parent_dir = os.path.dirname(full_path)
            if not parent_dir.startswith(WORKSPACE_ROOT):
                return '{"error": "Escaped workspace root"}'
                
            matches = glob.glob(full_path, recursive=True)
            # Remove absolute prefixes to return clean relative paths
            rel_matches = [os.path.relpath(m, WORKSPACE_ROOT) for m in matches]
            return f'{{"content": {rel_matches[:100]}}}' # limit to 100
    except Exception as e:
        return f'{{"error": "Failed to list files: {e}"}}'

FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a specific window of lines from a file. Includes line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file."},
                    "start_line": {"type": "integer", "description": "1-indexed start line."},
                    "read_lines": {"type": "integer", "description": "Number of lines to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a completely new file. Overwrites if it exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to save."},
                    "content": {"type": "string", "description": "File content."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit an existing file by line numbers (replace, delete, append).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path."},
                    "operation": {"type": "string", "enum": ["replace", "delete", "append"]},
                    "start_line": {"type": "integer", "description": "Start line number."},
                    "end_line": {"type": "integer", "description": "End line number (required for replace/delete)."},
                    "content": {"type": "string", "description": "Content to insert or replace with."}
                },
                "required": ["path", "operation", "start_line"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory or by glob pattern (e.g. notes/*).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory or glob pattern."}
                },
                "required": ["path"]
            }
        }
    }
]
