import json
from typing import Dict, Any
import streamlit as st

from utils.prompt_loader import load_prompt
from utils.ai.openai_client import call_gpt

def _build_full_payload(job_data: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    # MVP: include everything; we can add a stripper later to trim tokens
    return {
        "job": job_data or {},
        "candidate": profile or {},
        "constraints": {
            "format": "markdown",
            "company_name": (job_data or {}).get("company"),
            "job_title": (job_data or {}).get("job_title")
        }
    }

def generate_cover_letter(job_data: Dict[str, Any], profile: Dict[str, Any], model: str = "gpt-5-mini") -> str:
    """
    Same structure as score_job_fit:
        - load_prompt + RULES
        - build payload
        - call_gpt(...)
    """
    system_prompt = load_prompt("cover_letter_agent", "cover_letter_prompt.txt")

    payload = _build_full_payload(job_data, profile)

    try:
        print(f"🤖 [CoverLetter] Generating for {job_data.get('company', 'Unknown Company')}")
        text, meta = call_gpt(
            task="cover_letter",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
            ],
        )
        # print(f"[CoverLetter] tokens={meta['total_tokens']} cost=${meta['cost_usd']} model={meta['model']}")
        st.empty().success("✅ Cover letter generated!")

        # Clean and return
        letter = (text or "").strip()
        return letter

    except Exception as e:
        print("[CoverLetter] Fatal error:", e)
        return f"❌ Error: {e}"
