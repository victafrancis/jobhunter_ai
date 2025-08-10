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
    
def save_prompt(agent: str, filename: str, content: str) -> None:
    """
    Saves content to a prompt file inside the prompts/ folder of the given agent directory.
    Creates the folder if it doesn't exist.
    For example: save_prompt("resume_agent", "resume_prompt.txt", "my new prompt")
    → saves to: services/resume_agent/prompts/resume_prompt.txt
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # from /utils to project root
    prompts_dir = os.path.join(base_dir, "services", agent, "prompts")
    os.makedirs(prompts_dir, exist_ok=True)

    prompt_path = os.path.join(prompts_dir, filename)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(content)
