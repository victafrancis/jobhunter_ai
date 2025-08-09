import os
import json
from utils.gpt_utils import client
from utils.prompt_loader import load_prompt

def clean_job_text(raw_text: str) -> str:
    prompt = load_prompt("job_extraction_agent", "cleaner_prompt.txt")
    prompt = prompt.replace("{raw_text}", raw_text)

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def extract_job_info(clean_text: str, job_url: str = None) -> dict:
    prompt = load_prompt("job_extraction_agent", "job_extractor_prompt.txt")
    prompt = prompt.replace("{clean_text}", clean_text).replace("{job_url}", job_url or "")

    try:
        resp = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=3000
        )

        # Optional debug
        usage = getattr(resp, "usage", None)
        if usage:
            print(f"[ExtractJob] tokens prompt={usage.prompt_tokens} completion={usage.completion_tokens}")

        content = (resp.choices[0].message.content or "").strip()
        return json.loads(content) if content else {}
    except Exception as e:
        print("[ExtractJob] error:", e)
        return {}

def _dedupe_preserve_order(items):
    if not isinstance(items, list):
        return items
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def review_and_patch_job_data(clean_text: str, job_data: dict) -> dict:
    """
    Uses gpt-3.5-turbo to re-scan cleaned text and only ADD missing items to job_data.
    Never removes existing items. Returns updated dict.
    """
    try:
        template = load_prompt("job_extraction_agent", "reviewer_prompt.txt")
        current_json = json.dumps(job_data, ensure_ascii=False)
        prompt = (
            template
            .replace("{clean_text}", clean_text)
            .replace("{current_json}", current_json)
        )

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=3000
        )
        content = response.choices[0].message.content.strip()

        try:
            patched = json.loads(content)
        except json.JSONDecodeError:
            cleaned = content.strip("```json").strip("```").strip()
            patched = json.loads(cleaned)

        # Safety: dedupe lists we care about
        for key in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications"]:
            if key in patched:
                patched[key] = _dedupe_preserve_order(patched[key])

        return patched

    except Exception as e:
        # If reviewer fails for any reason, return original with a note
        job_data.setdefault("_review_notes", {})
        job_data["_review_notes"]["error"] = str(e)
        return job_data