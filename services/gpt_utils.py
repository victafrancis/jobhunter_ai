import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

PROMPT_DIR = "prompts"

def extract_job_details_with_gpt(raw_text: str, job_url: str = None) -> dict:
    """
    Uses GPT to extract structured job details from pasted text or fetched job description.
    Loads the parsing instructions from prompts/job_parser_prompt.txt, injects the job description
    and optional URL, and returns the JSON output.
    """
    # Load prompt template
    prompt_path = os.path.join(PROMPT_DIR, "job_parser_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"[gpt_utils] Missing template file: {prompt_path}")
        return {"error": "Missing parser prompt template."}

    # Inject raw text and optional URL
    prompt = template.replace("{raw_text}", raw_text)
    prompt = prompt.replace("{job_url}", job_url or "")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            cleaned = content.strip("```json").strip("```")
            return json.loads(cleaned)
    except Exception as e:
        print("[gpt_utils] Error during GPT extraction:", e)
        return {"error": str(e)}


def match_profile_to_job(job_data, profile_data):
    required = job_data.get("Required Skills", [])
    profile_skills = profile_data.get("skills", [])
    prompt = f"""
        You are a helpful job search assistant. Given the job's required skills:
        {required}
        and the user's profile skills:
        {profile_skills},
        calculate the following:

        - match_score (integer from 0–100)
        - missing_skills (list of important skills the user doesn't have)

        Return your response as JSON.
        """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print("[gpt_utils] Error during match scoring:", e)
        return {"match_score": 0, "missing_skills": [], "error": str(e)}


def generate_cover_letter(prompt_text, company=None):
    try:
        if company:
            print(f"🤖 [GPT] Generating cover letter for: {company}")
        else:
            print("🤖 [GPT] Generating cover letter...")

        with open(os.path.join(PROMPT_DIR, "cover_letter_prompt.txt"), "r", encoding="utf-8") as f:
            system_prompt = f.read()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"


def generate_resume(prompt_text, company=None):
    try:
        if company:
            print(f"🤖 [GPT] Generating resume for: {company}")
        else:
            print("🤖 [GPT] Generating resume...")

        with open(os.path.join(PROMPT_DIR, "resume_prompt.txt"), "r", encoding="utf-8") as f:
            system_prompt = f.read()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"