import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def generate_cover_letter(prompt_text, company=None):
    try:
        if company: # DEV LOG
            print(f"🤖 [GPT] Generating cover letter for: {company}")
        else:
            print("🤖 [GPT] Generating cover letter...")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # update to gpt4 later
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes professional, concise, and enthusiastic cover letters under 300 words."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=600
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

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes ATS-friendly, markdown‐style resumes."},
                {"role": "user",   "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"