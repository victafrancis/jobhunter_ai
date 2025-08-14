# save_job.py
import os, json, re, unicodedata
from datetime import datetime

JOB_DIR = os.path.join("data", "jobs")
_FORBIDDEN = r'<>:"/\\|?*'

def _safe_slug(text: str, max_len: int = 80) -> str:
    """Convert text into a safe filename-friendly slug."""
    if not text:
        return "untitled"
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = re.sub(f"[{re.escape(_FORBIDDEN)}]", " ", norm)
    norm = re.sub(r"[^A-Za-z0-9\s\-\_,.]", " ", norm)
    norm = re.sub(r"[\s\-_]+", "_", norm).strip("_.")
    if not norm:
        norm = "untitled"
    return norm[:max_len]

def save_job(job_data: dict):
    os.makedirs(JOB_DIR, exist_ok=True)

    now = datetime.now()
    job_data["date_added"] = now.strftime("%Y-%m-%d %H:%M:%S")
    job_data.setdefault("date_applied", "")

    title   = _safe_slug(job_data.get("job_title", "untitled"))
    company = _safe_slug(job_data.get("company", "unknown"))
    ts      = now.strftime("%Y%m%d_%H%M%S")
    fname   = f"{ts}_{title}_{company}.json"

    # New: group by day subfolder
    day_dir = os.path.join(JOB_DIR, now.strftime("%Y%m%d"))
    os.makedirs(day_dir, exist_ok=True)

    path = os.path.join(day_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2, ensure_ascii=False)

    return path
