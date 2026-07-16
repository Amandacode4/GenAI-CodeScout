import json

# Remove parameters if empty in tools/plan.py
with open('tools/plan.py', 'r') as f:
    content = f.read()

content = content.replace('"parameters": {\n                "type": "object",\n                "properties": {},\n            },', '')
with open('tools/plan.py', 'w') as f:
    f.write(content)

# Remove parameters if empty in tools/repomap.py
with open('tools/repomap.py', 'r') as f:
    content = f.read()

content = content.replace('"parameters": {\n                "type": "object",\n                "properties": {},\n            }', '')
with open('tools/repomap.py', 'w') as f:
    f.write(content)
