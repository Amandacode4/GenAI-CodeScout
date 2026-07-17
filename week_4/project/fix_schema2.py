import json

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # We want to replace the no-parameters with standard parameters
    # Let's just do it manually with python ast/json... Actually string replace is fine.
    # Wait, we removed parameters from plan.py and repomap.py.
    # Let's just manually rewrite get_todos and get_repo_map to have valid empty parameters.
    pass

with open('tools/plan.py', 'r') as f:
    content = f.read()

content = content.replace(
'''    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "Get your current plan and check the status of all todos."
        }
    },''',
'''    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "Get your current plan and check the status of all todos.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },''')

with open('tools/plan.py', 'w') as f:
    f.write(content)

with open('tools/repomap.py', 'r') as f:
    content = f.read()
    
content = content.replace(
'''def get_repo_map_tool():
    return {
        "type": "function",
        "function": {
            "name": "get_repo_map",
            "description": "Get an AST-based structural outline of the entire repository.",
        }
    }''',
'''def get_repo_map_tool():
    return {
        "type": "function",
        "function": {
            "name": "get_repo_map",
            "description": "Get an AST-based structural outline of the entire repository.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }''')
with open('tools/repomap.py', 'w') as f:
    f.write(content)

