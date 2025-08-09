import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

PROMPT_DIR = "prompts"

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