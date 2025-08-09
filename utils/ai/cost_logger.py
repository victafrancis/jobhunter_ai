# utils/ai/cost_logger.py
import csv, os, time
from typing import Optional, Dict, Any

CSV_PATH = "data/gpt_calls.csv"
CSV_HEADERS = [
    "timestamp", "task", "model", "prompt_tokens", "completion_tokens",
    "total_tokens", "cost_usd", "latency_s", "notes"
]

def _ensure_csv():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

def log_call(task: str, meta: Dict[str, Any], notes: Optional[str] = ""):
    _ensure_csv()
    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "task": task,
        "model": meta.get("model"),
        "prompt_tokens": meta.get("prompt_tokens", 0),
        "completion_tokens": meta.get("completion_tokens", 0),
        "total_tokens": meta.get("total_tokens", 0),
        "cost_usd": meta.get("cost_usd", 0.0),
        "latency_s": meta.get("latency_s", 0.0),
        "notes": notes or "",
    }
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_HEADERS).writerow(row)
