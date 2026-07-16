import json
import os

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
PLAN_FILE = os.path.join(WORKSPACE_ROOT, ".agent", "plan.json")

def _load_todos():
    if os.path.exists(PLAN_FILE):
        try:
            with open(PLAN_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_todos(todos):
    os.makedirs(os.path.dirname(PLAN_FILE), exist_ok=True)
    with open(PLAN_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def add_todos(todos: list) -> dict:
    """Add one or more todos to the plan."""
    current = _load_todos()
    
    for item in todos:
        if not isinstance(item, dict) or "title" not in item or "description" not in item or "verification_method" not in item:
            return {"error": "Each todo must have 'title', 'description', and 'verification_method'"}
        
        # Ensure it has a unique ID
        new_id = len(current) + 1
        current.append({
            "id": new_id,
            "title": item["title"],
            "description": item["description"],
            "verification_method": item["verification_method"],
            "status": "pending",
            "evidence": None
        })
        
    _save_todos(current)
    return {"status": "success", "added": len(todos), "current_plan": current}

def get_todos() -> dict:
    """Get the current todo list."""
    current = _load_todos()
    return {"plan": current}

def mark_todo(todo_id: int, status: str, evidence: str = None) -> dict:
    """Update a todo's status. Marking 'completed' requires evidence."""
    current = _load_todos()
    
    for item in current:
        if item["id"] == todo_id:
            if status == "completed" and not evidence:
                return {"error": "Cannot mark completed without concrete evidence (e.g. exit code 0 from pytest)."}
            
            item["status"] = status
            if evidence:
                item["evidence"] = evidence
                
            _save_todos(current)
            return {"status": "success", "updated_todo": item}
            
    return {"error": f"Todo ID {todo_id} not found."}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": (
                "Add items to your working plan. Use this to break down the task "
                "into verifiable steps (e.g. 1. Find bug, 2. Fix bug, 3. Verify fix)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "verification_method": {
                                    "type": "string", 
                                    "description": "How will you know this is definitively done? e.g. 'pytest tests/test_auth.py returns exit code 0'"
                                }
                            },
                            "required": ["title", "description", "verification_method"]
                        }
                    }
                },
                "required": ["todos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "Get your current plan and check the status of all todos.",
            
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_todo",
            "description": (
                "Update the status of a todo. To mark it 'completed', you MUST "
                "provide concrete evidence (like a test exit code or a log output). "
                "The agent loop will not stop until all todos are 'completed'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "blocked"]
                    },
                    "evidence": {
                        "type": "string",
                        "description": "Required if status is 'completed'. What is the exact proof this is done?"
                    }
                },
                "required": ["todo_id", "status"],
            },
        },
    }
]
