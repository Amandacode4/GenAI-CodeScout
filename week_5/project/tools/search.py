import ast
import os
import subprocess

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_GREP_RESULTS = 50
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

def resolve_path(path: str) -> str | None:
    try:
        resolved = os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
    except Exception:
        return None
    if not resolved.startswith(os.path.realpath(WORKSPACE_ROOT)):
        return None
    return resolved

def grep(
    pattern: str,
    path: str = ".",
    case_sensitive: bool = False,
    max_results: int = MAX_GREP_RESULTS,
) -> dict:
    resolved_path = resolve_path(path)
    if not resolved_path:
        return {"error": f"Path {path} is outside the workspace sandbox."}

    cmd = ["grep", "-rnI"]
    if not case_sensitive:
        cmd.append("-i")
    
    for exclude in EXCLUDE_DIRS:
        cmd.append(f"--exclude-dir={exclude}")
        
    cmd.append(pattern)
    cmd.append(resolved_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return {"error": "grep timed out"}
        
    lines = result.stdout.splitlines()
    matches = []
    
    for line in lines:
        parts = line.split(":", 2)
        if len(parts) >= 3:
            try:
                # grep output format: filename:lineno:text
                file_path = os.path.relpath(parts[0], WORKSPACE_ROOT)
                line_num = int(parts[1])
                text = parts[2]
                matches.append({"file": file_path, "line": line_num, "text": text})
            except ValueError:
                continue

    total_matches = len(matches)
    truncated = False
    
    if total_matches > max_results:
        matches = matches[:max_results]
        truncated = True

    return {
        "matches": matches,
        "truncated": truncated,
        "total_matches": total_matches
    }

class DefinitionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.definitions = []

    def visit_FunctionDef(self, node):
        self.definitions.append({
            "kind": "function",
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.definitions.append({
            "kind": "async function",
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.definitions.append({
            "kind": "class",
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        # Visit class body to find methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.definitions.append({
                    "kind": "method",
                    "name": f"{node.name}.{item.name}",
                    "line": item.lineno,
                    "end_line": getattr(item, "end_lineno", item.lineno)
                })

def list_definitions(path: str) -> dict:
    resolved_path = resolve_path(path)
    if not resolved_path:
        return {"error": f"Path {path} is outside the workspace sandbox."}
        
    if not os.path.exists(resolved_path):
        return {"error": f"File {path} does not exist."}
        
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}
        
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error in {path}: {str(e)}"}
        
    visitor = DefinitionVisitor()
    visitor.visit(tree)
    
    return {"definitions": visitor.definitions}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "Search file contents for a pattern across the workspace. "
                "Use this before read_file when you don't already know which "
                "file you need."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text or regex to search for."},
                    "path": {"type": "string", "description": "Subdirectory to search, default workspace root."},
                    "case_sensitive": {"type": "boolean", "description": "Default false."},
                    "max_results": {
                        "type": "integer",
                        "description": f"Cap on matches returned. Default {MAX_GREP_RESULTS}.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_definitions",
            "description": (
                "List the functions and classes declared in a Python file, "
                "with line numbers, without reading the whole file. Use this "
                "right after grep to decide which match is worth reading in "
                "full with read_file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a Python file."},
                },
                "required": ["path"],
            },
        },
    },
]
