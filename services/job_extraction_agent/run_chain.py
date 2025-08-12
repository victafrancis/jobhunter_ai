# services/job_extraction_agent/run_chain.py
import streamlit as st
from services.job_extraction_agent.preclean import heuristic_preclean
from services.job_extraction_agent.extract_job_data import (
    clean_job_text,
    extract_job_info,
    review_and_patch_job_data,
)

def _looks_clean_enough(text: str) -> bool:
    if not text:
        return False
    # simple, cheap heuristics
    return (len(text) >= 400) and (text.count("\n") >= 8)

def _needs_review(job_data: dict) -> bool:
    if not isinstance(job_data, dict):
        return True
    required = job_data.get("required_skills") or []
    title_ok = bool(job_data.get("job_title"))
    company_ok = bool(job_data.get("company"))
    location_ok = bool(job_data.get("location"))
    thin_skills = len(required) < 6
    missing_core = not (title_ok and company_ok and location_ok)
    return thin_skills or missing_core

def run_job_extraction_chain(raw_text: str, job_url: str = None) -> dict:
    """
    Pipeline:
        1) heuristic pre-clean (no LLM)
        2) conditional LLM clean (gpt-5-mini) if heuristic looks weak
        3) extraction (gpt-5)
        4) conditional reviewer (gpt-5-mini) if extraction looks thin or forced
    """
    with st.spinner("Analyzing with AI..."):
        stage_status = st.empty()

        # Step 0: deterministic pre-clean
        stage_status.info("Pre-cleaning...")
        pre = heuristic_preclean(raw_text)

        # Step 1: conditional LLM cleaner
        if _looks_clean_enough(pre):
            cleaned = pre
        else:
            stage_status.info("🧼 Cleaning job text...")
            cleaned = clean_job_text(pre)

        # Step 2: extraction
        stage_status.info("📦 Extracting structured data...")
        job_data = extract_job_info(cleaned, job_url)

        # Step 3: conditional reviewer
        if _needs_review(job_data):
            stage_status.info("🔍 Reviewing and patching missing items...")
            job_data = review_and_patch_job_data(cleaned, job_data)

        stage_status.success("✅ Job extracted successfully!")

    return job_data
