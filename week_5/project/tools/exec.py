import os
import shlex
import subprocess
from rich.console import Console

console = Console()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
TIMEOUT_DEFAULT = 10
MAX_OUTPUT_CHARS = 8_000

READ_ONLY_PREFIXES = (
    "grep", "find", "ls", "cat", "head", "tail", "wc",
    "git log", "git diff", "git status", "git blame", "git show",
    "pytest", "python -m pytest", "ruff", "flake8", "mypy", "python"
)

DESTRUCTIVE_PATTERNS = (
    "rm ", "mv ", ">", ">>", "git commit", "git push", "git checkout --",
    "pip install", "npm install", "curl ", "sudo ", "chmod ",
)

def paths_within_sandbox(command: str, workspace_root: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    for token in tokens:
        if token.startswith("-") or "=" in token:
            continue
        if os.path.isabs(token) or "/" in token:
            try:
                resolved = os.path.realpath(os.path.join(workspace_root, token))
            except Exception:
                continue
            if not resolved.startswith(os.path.realpath(workspace_root)):
                return False
    return True

def classify_command(command: str) -> str:
    for pat in DESTRUCTIVE_PATTERNS:
        if pat in command:
            return "ask"
    
    for prefix in READ_ONLY_PREFIXES:
        if command.startswith(prefix + " ") or command == prefix:
            return "read_only"
            
    return "ask"

def run_command(command: str, cwd: str = WORKSPACE_ROOT, timeout: int = TIMEOUT_DEFAULT) -> dict:
    if not paths_within_sandbox(command, WORKSPACE_ROOT):
        return {"error": f"Command attempts to access paths outside {WORKSPACE_ROOT}"}

    classification = classify_command(command)
    
    if classification == "ask":
        console.print(f"\\n[bold red]WARNING:[/bold red] The agent wishes to run a destructive or unclassified command:")
        console.print(f"[bold cyan]{command}[/bold cyan]")
        choice = input("Do you approve? [y/N]: ").strip().lower()
        if choice != 'y':
            return {"error": "Human operator declined to run this command."}

    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, timeout=timeout,
            capture_output=True, text=True
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + f"\\n... (truncated {len(stdout) - MAX_OUTPUT_CHARS} characters)"
        if len(stderr) > MAX_OUTPUT_CHARS:
            stderr = stderr[:MAX_OUTPUT_CHARS] + f"\\n... (truncated {len(stderr) - MAX_OUTPUT_CHARS} characters)"

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds."}
    except Exception as e:
        return {"error": f"Failed to execute command: {str(e)}"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command in the workspace and return its output. "
                "Use this to search (grep/find), inspect history (git log/diff), "
                "run tests, or make a change. Read-only commands run immediately. "
                "Anything that writes, deletes, or installs will pause and ask the "
                "human operator for approval — expect that pause, it's not a failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": f"Seconds before the command is killed. Default {TIMEOUT_DEFAULT}.",
                    },
                },
                "required": ["command"],
            },
        },
    }
]
