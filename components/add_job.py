import streamlit as st
from services.job_parser import fetch_job_text
from services.gpt_utils import extract_job_details_with_gpt, match_profile_to_job
from services.save_job import save_job

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

    if st.button("Analyze Job", key="scan_job_btn"):
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

        # Display raw job text
        st.subheader("📄 Raw Job Description")
        st.text_area("Job Text", job_text, height=50)

        # Extract structured details via GPT
        with st.spinner("Analyzing with AI..."):
            print(f"🤖 [GPT] Analyzing listing..")
            job_data = extract_job_details_with_gpt(job_text, job_url)

        # Save to session
        st.session_state["job_data"] = job_data

        # Match against profile
        with st.spinner("Matching against your profile..."):
            match = match_profile_to_job(job_data, profile)
            st.session_state["match"] = match
            job_data.update(match)

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
            st.success("✅ Job saved to your feed!")
            st.write(f"📁 Saved to: `{path}`")
            st.session_state["view_job_path"] = path  # Store path for immediate view

        if st.session_state.get("view_job_path"):
            if st.button("🔍 View Saved Job"):
                st.rerun()

        if st.button("Clear Job Session", key="clear_job_session"):
            for key in ["job_data", "match", "job_url_input", "job_text_input"]:
                if key in st.session_state:
                    del st.session_state[key]