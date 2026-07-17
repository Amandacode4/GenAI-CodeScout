import os
import ast
from collections import defaultdict
from tools.files import resolve_path, WORKSPACE_ROOT

def build_repo_map() -> str:
    """Builds a map of all functions and classes in the repo and ranks them."""
    python_files = []
    
    # Exclude typical build/vendor directories
    excludes = {".git", "venv", ".venv", "node_modules", "__pycache__", "build", "dist"}
    
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d not in excludes]
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))
                
    definitions = defaultdict(list)
    
    # 1. Extract definitions
    for path in python_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            rel_path = os.path.relpath(path, WORKSPACE_ROOT)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    definitions[rel_path].append(node.name)
        except Exception:
            continue
            
    # For a real Repo Map (like Aider's), we'd use tree-sitter and PageRank. 
    # Here, we will just construct a tree of the top files with the most definitions.
    
    sorted_files = sorted(definitions.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Cap to top 20 files to save context window
    capped_files = sorted_files[:20]
    
    lines = ["Repo Map (Top 20 files with most definitions):"]
    for path, defs in capped_files:
        if defs:
            lines.append(f"\\n{path}:")
            for d in defs[:10]: # cap to top 10 defs per file
                lines.append(f"  - {d}")
            if len(defs) > 10:
                lines.append(f"  - ... ({len(defs) - 10} more)")
                
    if not capped_files:
        return "No python definitions found."
        
    return "\\n".join(lines)

def get_repo_map_tool():
    return {
        "type": "function",
        "function": {
            "name": "get_repo_map",
            "description": "Get an AST-based structural outline of the entire repository.",
            
        }
    }
