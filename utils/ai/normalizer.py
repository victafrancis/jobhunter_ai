import json
from typing import List, Dict
from utils.ai.openai_client import call_gpt

_SKILL_SYSTEM = """You normalize skill names for a developer profile.

Rules:
- Return ONLY JSON: {"skills":[{"raw":"","normalized":""}, ...]}
- Only ADD, never remove or change existing profile entries.
- Normalize case, trim symbols, remove trailing slashes or pipes.
- Prefer canonical developer names (e.g., "Next.js", "React", "Java").
- Merge obvious synonyms (e.g., "object oriented programming","OOP" -> "Object-Oriented Programming").
- If input is junk, omit it from the list.
"""

_QUAL_SYSTEM = """You normalize qualifications for a developer profile.

Rules:
- Return ONLY JSON: {"qualifications":[{"raw":"","normalized":""}, ...]}
- Only ADD, never remove existing profile entries.
- Keep concise sentence fragments (e.g., "Diploma in CS or equivalent experience").
- Trim punctuation, fix casing, remove duplicates.
- If input is junk, omit it.
"""

def normalize_skills_with_nano(candidates: List[str]) -> List[Dict[str, str]]:
    if not candidates:
        return []
    payload = {"candidates": candidates}
    text, _ = call_gpt(
        task="cheap_fallback",  # maps to gpt-5-nano via your settings
        messages=[
            {"role": "system", "content": _SKILL_SYSTEM},
            {"role": "user", "content": json.dumps(payload)}
        ],
        response_format={"type": "json_object"}
    )
    try:
        data = json.loads(text or "{}")
        return [x for x in data.get("skills", []) if x.get("normalized")]
    except Exception:
        return []

def normalize_quals_with_nano(candidates: List[str]) -> List[Dict[str, str]]:
    if not candidates:
        return []
    payload = {"candidates": candidates}
    text, _ = call_gpt(
        task="cheap_fallback",
        messages=[
            {"role": "system", "content": _QUAL_SYSTEM},
            {"role": "user", "content": json.dumps(payload)}
        ],
        response_format={"type": "json_object"}
    )
    try:
        data = json.loads(text or "{}")
        return [x for x in data.get("qualifications", []) if x.get("normalized")]
    except Exception:
        return []
