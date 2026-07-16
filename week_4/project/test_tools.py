import json
from agent import Agent
a = Agent()
print(json.dumps(a.tools, indent=2))
