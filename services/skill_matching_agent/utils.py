import re
from typing import Dict, Any, Iterable

ALIASES = {
    "next.js": {"nextjs", "next js", "next"},
    "react": {"reactjs", "react.js"},
    "gcp": {"google cloud platform", "google cloud"},
    "sse": {"server sent events", "server-sent events"},
    "restful apis": {"rest api", "rest", "apis"},
    "openai": {"openai api", "openai sdk"},
    "mongodb": {"mongo db"},
    "tailwind css": {"tailwind"},
}

def _norm(s: str) -> str:
    s = s or ""
    s = s.lower().replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\b(v?\d+(\.\d+)?\+?)\b", "", s).strip()
    return s

def _canonicalize(n: str) -> str:
    for canon, alts in ALIASES.items():
        if n == canon or n in alts:
            return canon
    return n

def normalize_set(items: Iterable[str] | None) -> set[str]:
    out: set[str] = set()
    for it in items or []:
        n = _canonicalize(_norm(it))
        if n:
            out.add(n)
    return out

def flatten_experience_bullets(profile: Dict[str, Any]) -> list[str]:
    bullets: list[str] = []
    for w in profile.get("work_experience", []) or []:
        bullets += (w.get("responsibilities") or [])
        bullets += (w.get("achievements") or [])
    return bullets

def default_weights() -> Dict[str, Any]:
    return {
        "w_required": 0.60, "w_nice": 0.20, "w_qual": 0.20,
        "penalties": {"location": 25, "work_mode": 30, "salary": 20, "seniority": 10}
    }

def prepare_fit_payload(job_data: Dict[str, Any], profile: Dict[str, Any], weights: Dict[str, Any] | None) -> Dict[str, Any]:
    jd_req  = normalize_set(job_data.get("required_skills"))
    jd_nice = normalize_set(job_data.get("nice_to_have_skills"))
    jd_qual = normalize_set(job_data.get("qualifications"))
    jd_resp = list(job_data.get("responsibilities") or [])

    prof_sk = normalize_set(profile.get("skills"))
    bullets = flatten_experience_bullets(profile)
    prefs = profile.get("preferences", {})

    return {
        "weights": weights or default_weights(),
        "JOB_DATA": {
            "job_title": job_data.get("job_title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "work_location": job_data.get("work_location"),
            "salary": job_data.get("salary"),
            "job_type": job_data.get("job_type"),
            "required_skills": sorted(list(jd_req)),
            "nice_to_have_skills": sorted(list(jd_nice)),
            "qualifications": sorted(list(jd_qual)),
            "responsibilities": jd_resp,
            "job_text": job_data.get("job_text", "")
        },
        "PROFILE": {
            "name": profile.get("name"),
            "title": profile.get("title"),
            "location": profile.get("location"),
            "skills": sorted(list(prof_sk)),
            "experience_bullets": bullets,
            "preferences": {
                "remote": prefs.get("remote", True),
                "hybrid": prefs.get("hybrid", True),
                "onsite": prefs.get("onsite", False),
                "job_titles": prefs.get("job_titles", []),
            }
        }
    }

def ensure_match_shape(data: Dict[str, Any]) -> Dict[str, Any]:
    def _d(k, v):
        if k not in data or not isinstance(data[k], type(v)):
            data[k] = v
    _d("fit", {})
    data["fit"].setdefault("skills", {})
    data["fit"]["skills"].setdefault("required", {"matched": [], "missing": [], "score": 0})
    data["fit"]["skills"].setdefault("nice_to_have", {"matched": [], "missing": [], "score": 0})
    data["fit"].setdefault("qualifications", {"matched": [], "missing": [], "score": 0})
    data["fit"].setdefault("responsibilities", {"evidence": [], "confidence": 0})

    _d("preferences", {"location_ok": True, "work_mode_ok": True, "salary_ok": "unknown", "notes": ""})
    _d("scores", {"skill_score": 0, "preference_score": 0, "overall_score": 0})
    _d("analysis", {"strengths": [], "gaps": [], "fast_upskill_suggestions": []})
    data.setdefault("doc_recommendations", {})
    data["doc_recommendations"].setdefault("cover_letter", {"highlights": [], "address_gaps": [], "tone": "impact-focused"})
    data["doc_recommendations"].setdefault("resume", {"reorder_suggestions": [], "keywords_to_include": [], "bullets_to_add": []})
    return data

def compute_scores_from_matches(result: dict, weights: dict | None = None) -> dict:
    w = {"w_required": 0.6, "w_nice": 0.2, "w_qual": 0.2,
        "penalties": {"location": 15, "work_mode": 10, "salary": 8, "seniority": 12}}
    if weights: w.update({k: v for k, v in weights.items() if k in ("w_required","w_nice","w_qual","penalties")})

    fit = result.get("fit", {})
    req = fit.get("skills", {}).get("required", {})
    nice = fit.get("skills", {}).get("nice_to_have", {})
    qual = fit.get("qualifications", {})

    def ratio(matched, missing):
        total = len(matched) + len(missing)
        return None if total == 0 else len(matched) / total

    r_req  = ratio(req.get("matched", []),  req.get("missing", []))
    r_nice = ratio(nice.get("matched", []), nice.get("missing", []))
    r_qual = ratio(qual.get("matched", []), qual.get("missing", []))

    parts = [(r_req, w["w_required"]), (r_nice, w["w_nice"]), (r_qual, w["w_qual"])]
    used = [(v, wt) for v, wt in parts if v is not None and wt > 0]
    skill_score = 100 * (sum(v * wt for v, wt in used) / (sum(wt for _, wt in used) or 1)) if used else 0
    skill_score = round(skill_score, 1)

    prefs = result.get("preferences", {})
    pref_score = 100
    if prefs.get("location_ok") is False:  pref_score -= w["penalties"]["location"]
    if prefs.get("work_mode_ok") is False: pref_score -= w["penalties"]["work_mode"]
    sal = prefs.get("salary_ok", "unknown")
    if sal == "below":                     pref_score -= w["penalties"]["salary"]
    pref_score = max(0, min(100, pref_score))

    resp_conf = fit.get("responsibilities", {}).get("confidence", 0) or 0
    bonus = 8 * max(0, min(100, resp_conf)) / 100.0  # small bonus

    overall = 0.7 * skill_score + 0.2 * pref_score + 0.1 * (skill_score + bonus)
    overall = round(min(100, overall), 1)

    result["scores"] = {
        "skill_score": skill_score,
        "preference_score": round(pref_score, 1),
        "overall_score": overall
    }
    return result
