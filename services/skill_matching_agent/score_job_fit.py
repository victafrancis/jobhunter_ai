# run_chain.py
import json, re
from typing import Dict, Any
from utils.ai.openai_client import call_gpt
from utils.prompt_loader import load_prompt
from .utils import prepare_fit_payload, ensure_match_shape

def _strip_fences(s: str) -> str:
    s = (s or "").strip()
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE|re.DOTALL).strip()

def _first_json_block(s: str) -> str:
    m = re.search(r"\{.*\}", s, re.DOTALL)
    return m.group(0) if m else s

def _to_json(s: str) -> dict:
    s = _strip_fences(s)
    s = _first_json_block(s)
    return json.loads(s)

def score_job_fit(job_data: Dict[str, Any], profile: Dict[str, Any], weights: Dict[str, Any] | None = None) -> Dict[str, Any]:
    system_prompt = load_prompt("skill_matching_agent", "skill_match_prompt.txt") + \
        "\n\nRULES: Return ONLY a single valid JSON object. Do not wrap in code fences. No extra text."

    payload = prepare_fit_payload(job_data, profile, weights)

    try:
        print("🤖 [SkillMatch] Scoring job fit...")
        text, meta = call_gpt(
            task="analysis",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload)}
            ],
            response_format={"type": "json_object"}
        )
        print(f"[SkillMatch] tokens={meta['total_tokens']} cost=${meta['cost_usd']} model={meta['model']}")

        # load json
        data = {}
        if text.strip():
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # last‑ditch: strip fences or grab the first JSON object if model misbehaves
                from re import search, DOTALL
                s = text.strip().strip("```json").strip("```").strip()
                m = search(r"\{.*\}", s, DOTALL)
                if m:
                    data = json.loads(m.group(0))

    except Exception as e:
        print("[SkillMatch] Fatal error:", e)
        data = {}

    return ensure_match_shape(data or {})
