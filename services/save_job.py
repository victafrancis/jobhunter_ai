import os, json
from datetime import datetime

JOB_DIR = os.path.join("data", "jobs")

def save_job(job_data: dict):
    os.makedirs(JOB_DIR, exist_ok=True)

    # add timestamp fields
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_data["date_added"] = now
    job_data.setdefault("date_applied", "")  # blank until applied

    title   = job_data.get("job_title", "untitled").replace(" ", "_")
    company = job_data.get("company", "unknown").replace(" ", "_")
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname   = f"{ts}_{title}_{company}.json"

    path = os.path.join(JOB_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)

    return path