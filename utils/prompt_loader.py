# utils/prompt_loader.py
import os

def load_prompt(agent: str, filename: str) -> str:
    """
    Loads a prompt file from the prompts/ folder inside a given agent directory.
    For example: load_prompt("job_extraction_agent", "cleaner_prompt.txt")
    → loads from: services/job_extraction_agent/prompts/cleaner_prompt.txt
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # from /utils to project root
    prompt_path = os.path.join(base_dir, "services", agent, "prompts", filename)

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()