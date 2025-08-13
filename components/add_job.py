import os
import streamlit as st
from services.job_parser import fetch_job_text
from services.save_job import save_job
from services.job_extraction_agent.run_chain import run_job_extraction_chain
from services.skill_matching_agent.score_job_fit import score_job_fit

def _clear_add_job_session():
    # Only clear add-job related state
    for key in ["job_data", "match", "job_url_input", "job_text_input", "view_job_path"]:
        st.session_state.pop(key, None)
    # Stay on Add Job after clearing
    st.session_state["selected_page"] = "Add Job"

def add_job(profile: dict):
    """
    Streamlit component for adding a job via URL or pasted text.
    """
    st.header("📎 Add a Job Listing")
    input_mode = st.radio(
        "How would you like to add a job?", ["URL", "Full Text"], index=0
    )

    job_url = ""
    job_text = None

    if input_mode == "URL":
        job_url = st.text_input("Paste job URL here", key="job_url_input")
    else:
        job_text = st.text_area("Paste full job description text here", height=50, key="job_text_input")
        job_url = st.text_input("Optional: Paste job URL for reference", key="job_url_ref")

    col_analyze, col_clear = st.columns([1, 1])

    run_clicked = col_analyze.button("Analyze Job", key="scan_job_btn")

    # Only render the Clear button if there’s parsed data
    if ("job_data" in st.session_state) or ("match" in st.session_state):
        col_clear.button(
            "Clear Job Session",
            key="clear_job_session_top",
            on_click=_clear_add_job_session  # with st.rerun() removed inside
        )

    if run_clicked:
        # Validate inputs
        if input_mode == "URL":
            if not job_url.strip():
                st.warning("Please paste a job URL.")
                return
            with st.spinner("Fetching job content from URL..."):
                job_text = fetch_job_text(job_url)
                if not job_text:
                    st.error(
                        "Could not fetch job from this URL. "
                        "If it's blocked (e.g., Indeed), switch to 'Full Text' and paste the page content."
                    )
                    return
        else:
            if not job_text or not job_text.strip():
                st.warning("Please paste the full job description text.")
                return

        # Extract structured details via GPT
        job_data = run_job_extraction_chain(job_text, job_url)

        # Save to session
        st.session_state["job_data"] = job_data

        # Match against profile
        with st.spinner("Matching against your profile..."):
            try:
                match = score_job_fit(job_data, profile)
                job_data["match"] = match
                st.session_state["job_data"] = job_data
            except Exception as e:
                st.error(f"Match failed: {e}")

    # === Display saved data from session ===
    if "job_data" in st.session_state:
        st.subheader("📌 Extracted Job Details")
        st.json(st.session_state["job_data"])

    if "match" in st.session_state:
        st.subheader("✅ Match Insights")
        st.json(st.session_state["match"])

    # === Save button and Clear ===
    if "job_data" in st.session_state:
        job_data = st.session_state["job_data"]

        # Save button
        if st.button("💾 Save this Job", key="save_job_btn"):
            path = save_job(job_data)
            job_data["_source_path"] = path
            st.session_state["view_job_path"] = path
            st.session_state["selected_page"] = "View Job"
            st.rerun()

        if st.button("Clear Job Session", key="clear_job_session_bottom"):
            _clear_add_job_session()