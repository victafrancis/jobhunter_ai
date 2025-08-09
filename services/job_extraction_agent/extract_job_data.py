# extract_job_data.py
import os
import json
from utils.ai.openai_client import call_gpt
from utils.prompt_loader import load_prompt

def clean_job_text(raw_text: str) -> str:
    prompt = load_prompt("job_extraction_agent", "cleaner_prompt.txt")
    prompt = prompt.replace("{raw_text}", raw_text)

    text, meta = call_gpt(
        task="summarize",
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"[CleanText] tokens={meta['total_tokens']} cost=${meta['cost_usd']}")
    return text.strip()

def extract_job_info(clean_text: str, job_url: str = None) -> dict:
    tmpl = load_prompt("job_extraction_agent", "job_extractor_prompt.txt")
    prompt = tmpl.replace("{clean_text}", clean_text).replace("{job_url}", job_url or "")

    try:
        text, meta = call_gpt(
            task="extract",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        print(f"[ExtractJob] tokens={meta['total_tokens']} cost=${meta['cost_usd']} model={meta['model']}")
        return json.loads(text) if text else {}
    except Exception as e:
        print("[ExtractJob] error:", e)
        return {}

def _dedupe_preserve_order(items):
    if not isinstance(items, list):
        return items
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def review_and_patch_job_data(clean_text: str, job_data: dict) -> dict:
    """
    Re-scan cleaned text and only ADD missing items to job_data.
    Never removes existing items.
    """
    try:
        template = load_prompt("job_extraction_agent", "reviewer_prompt.txt")
        current_json = json.dumps(job_data, ensure_ascii=False)
        prompt = template.replace("{clean_text}", clean_text).replace("{current_json}", current_json)

        text, meta = call_gpt(
            task="review_extracted_job",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        print(f"[Reviewer] tokens={meta['total_tokens']} cost=${meta['cost_usd']}")

        patched = {}
        if text.strip():
            try:
                patched = json.loads(text)
            except json.JSONDecodeError:
                s = text.strip().strip("```json").strip("```").strip()
                from re import search, DOTALL
                m = search(r"\{.*\}", s, DOTALL)
                if m:
                    patched = json.loads(m.group(0))

        # safety dedupe
        for key in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications"]:
            if key in patched and isinstance(patched[key], list):
                seen, out = set(), []
                for x in patched[key]:
                    if x not in seen:
                        seen.add(x); out.append(x)
                patched[key] = out

        return patched
    except Exception as e:
        job_data.setdefault("_review_notes", {})
        job_data["_review_notes"]["error"] = str(e)
        return job_data
