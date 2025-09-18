# utils/prompt_loader.py
import os

BASE = os.path.join("services")

def _prompt_dir(agent: str) -> str:
    d = os.path.join(BASE, agent, "prompts")
    os.makedirs(d, exist_ok=True)
    return d

def list_prompts(agent: str) -> list[str]:
    """Return *.txt prompt files for an agent, sorted."""
    d = _prompt_dir(agent)
    files = [f for f in os.listdir(d) if f.endswith(".txt")]
    return sorted(files)

def load_prompt(agent: str, filename: str) -> str:
    """Load the exact prompt filename from the agent's prompts folder."""
    path = os.path.join(_prompt_dir(agent), filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_prompt(agent: str, filename: str, content: str) -> None:
    """Save content to the exact prompt filename."""
    path = os.path.join(_prompt_dir(agent), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
