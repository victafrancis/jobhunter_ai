import json, re
from typing import Dict, Any
from utils.gpt_utils import client
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
        resp = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload)}
            ]
        )

        # Debug token usage
        usage = getattr(resp, "usage", None)
        if usage:
            print(f"[SkillMatch] tokens prompt={usage.prompt_tokens} completion={usage.completion_tokens}")

        msg = resp.choices[0].message
        data = None

        # 1) Try old-school content
        if msg.content and msg.content.strip():
            try:
                data = _to_json(msg.content)
                print("[SkillMatch] Parsed from .content")
            except Exception as e:
                print("[SkillMatch] .content parse failed:", e)

        # 2) Try .parsed (JSON mode sometimes puts it here)
        if data is None and hasattr(msg, "parsed") and msg.parsed:
            try:
                if isinstance(msg.parsed, dict):
                    data = msg.parsed
                else:
                    data = json.loads(msg.parsed)
                print("[SkillMatch] Parsed from .parsed")
            except Exception as e:
                print("[SkillMatch] .parsed parse failed:", e)

        # 3) Try function_call.arguments (another common place)
        if data is None and getattr(msg, "function_call", None):
            args = getattr(msg.function_call, "arguments", None)
            if args:
                try:
                    data = json.loads(args)
                    print("[SkillMatch] Parsed from .function_call.arguments")
                except Exception as e:
                    print("[SkillMatch] function_call parse failed:", e)

        # 4) If still nothing, dump the whole API response for inspection
        if data is None:
            print("[SkillMatch] Empty content in all known fields — dumping raw API response:")
            try:
                raw_dump = resp.model_dump_json()
                print(raw_dump[:4000])  # trim for console
            except Exception as e:
                print("[SkillMatch] Could not dump raw response:", e)
            data = {}

    except Exception as e:
        print("[SkillMatch] Fatal error:", e)
        data = {}

    return ensure_match_shape(data or {})
