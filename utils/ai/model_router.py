# utils/ai/model_router.py
from typing import Literal, Dict
from utils.config.settings import load_settings

Task = Literal["extract", "summarize", "cover_letter", "resume", "generic", "review_extracted_job", "analysis", "clean_job_text"]

def choose_model(task: Task) -> str:
    s = load_settings()
    if s.get("developer_mode"):
        return s["preferred_models"].get("cheap_fallback", "gpt-5-nano")
    m: Dict[str, str] = s.get("preferred_models", {})
    return m.get(task, m.get("summarize", "gpt-5-mini"))
