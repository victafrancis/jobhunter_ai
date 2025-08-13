import json
from typing import Dict, Any
from utils.prompt_loader import load_prompt
from utils.ai.openai_client import call_gpt
from services.skill_matching_agent.skill_match_utils import ensure_analysis_shape

def build_payload(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    bullets = []
    for w in profile.get("work_experience", []) or []:
        bullets += (w.get("responsibilities") or [])
        bullets += (w.get("achievements") or [])
    return {
        "JOB_DATA": {
            "job_title": job.get("job_title"),
            "company": job.get("company"),
            "responsibilities": job.get("responsibilities") or [],
            "job_text": job.get("job_text", ""),
        },
        "PROFILE": {
            "skills": profile.get("skills", []),
            "experience_bullets": bullets,
            "preferences": profile.get("preferences", {}),
        },
    }

def run_in_depth_analysis(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = load_prompt("analysis_agent", "run_analysis_prompt.txt")
    payload = build_payload(job, profile)
    text, meta = call_gpt(
        task="analysis",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload)}
        ],
        response_format={"type": "json_object"}
    )
    print(f"[Analysis Agent] tokens={meta['total_tokens']} cost=${meta['cost_usd']} model={meta['model']}")
    data = json.loads(text) if text else {}
    return ensure_analysis_shape(data or {})
