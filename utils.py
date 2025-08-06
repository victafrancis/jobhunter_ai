def load_cover_letter_prompt_template():
    with open("prompts/cover_letter_prompt.txt", "r") as f:
        return f.read()

def load_resume_prompt_template():
    with open("prompts/resume_prompt.txt", "r") as f:
        return f.read()