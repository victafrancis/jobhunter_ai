import json
from typing import Dict, Any
import streamlit as st
from utils.prompt_loader import load_prompt
from utils.ai.openai_client import call_gpt

def _build_payload(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job": job or {},
        "candidate": profile or {},
        "constraints": {
            "format": "markdown",
            "sections": ["Header","Summary","Skills","Experience","Projects","Education"],
            "length": "2 pages max",
            "ats_friendly": True
        }
    }

def generate_resume(job: Dict[str, Any], profile: Dict[str, Any], model: str = "gpt-5-mini") -> str:
    system_prompt = load_prompt("resume_agent", "resume_prompt.txt")
    payload = _build_payload(job, profile)
    try:
        print(f"🤖 [Resume] Generating for {job.get('company','Unknown')}")
        text, meta = call_gpt(
            task="resume",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
            ],
        )
        print(f"[Resume] tokens={meta['total_tokens']} cost=${meta['cost_usd']} model={meta['model']}")
        st.empty().success("✅ Resume generated!")
        return (text or "").strip()
    except Exception as e:
        print("[Resume] Fatal error:", e)
        return f"❌ Error: {e}"
