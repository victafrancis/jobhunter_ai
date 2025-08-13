# utils/config/settings.py
import json, os
from typing import Any, Dict

SETTINGS_PATH = os.path.join("data", "settings.json")

DEFAULTS: Dict[str, Any] = {
    "developer_mode": False,
    "preferred_models": {
        "extract": "gpt-5-mini",
        "summarize": "gpt-5-mini",
        "cover_letter": "gpt-5-mini",
        "resume": "gpt-5-mini",
        "cheap_fallback": "gpt-5-nano",
        "review_extracted_job": "gpt-5-mini",
        "analysis": "gpt-5-mini",
        "analysis_mini": "gpt-5-nano",
        "clean_job_text": "gpt-5-nano",
        "skill_match": "gpt-5-mini"
    },
    "credit_balance": 10
}

def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def load_settings() -> Dict[str, Any]:
    _ensure_data_dir()
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        disk = json.load(f)
    # merge to keep new keys if you upgrade DEFAULTS later
    merged = DEFAULTS.copy()
    merged.update(disk)
    return merged

def save_settings(s: Dict[str, Any]) -> None:
    _ensure_data_dir()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
