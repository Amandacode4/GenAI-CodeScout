import os
import yaml
import glob
from collections import defaultdict

def get_skills_metadata(skills_dir="skills") -> str:
    """Returns a string containing the name and description of all available skills."""
    if not os.path.isdir(skills_dir):
        return "No external skills are loaded."
        
    skill_descriptions = []
    
    for skill_name in os.listdir(skills_dir):
        skill_dir = os.path.join(skills_dir, skill_name)
        if not os.path.isdir(skill_dir):
            continue
            
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_file):
            continue
            
        with open(skill_file, "r") as f:
            content = f.read()
            
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    if "name" in frontmatter and "description" in frontmatter:
                        skill_descriptions.append(f"- **{frontmatter['name']}**: {frontmatter['description'].strip()}")
                except yaml.YAMLError:
                    pass
                    
    if not skill_descriptions:
        return "No external skills are loaded."
        
    return "Available External Skills:\n" + "\n".join(skill_descriptions)

def load_skill(name: str, skills_dir="skills") -> str:
    """Loads the full body of a skill and lists any bundled files."""
    skill_dir = os.path.join(skills_dir, name)
    skill_file = os.path.join(skill_dir, "SKILL.md")
    
    if not os.path.isfile(skill_file):
        return f"Error: Skill '{name}' not found."
        
    with open(skill_file, "r") as f:
        content = f.read()
        
    # Strip frontmatter
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
            
    # Find bundled files
    bundled_files = []
    for root, _, sorted_files in os.walk(skill_dir):
        for file in sorted_files:
            if file == "SKILL.md": continue
            rel_path = os.path.relpath(os.path.join(root, file), start=skills_dir)
            bundled_files.append(rel_path)
            
    result = f"--- Loaded Skill: {name} ---\n\n{body}"
    if bundled_files:
        result += "\n\nBundled files available for reading/execution:\n" + "\n".join([f"- skills/{f}" for f in bundled_files])
        
    return result

SKILL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "Load the full instructions and bundled files for a specific skill. Use this when you recognize a relevant skill in your system prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the skill to load (e.g. 'commit')"
                    }
                },
                "required": ["name"]
            }
        }
    }
]
