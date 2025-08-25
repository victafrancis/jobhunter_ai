# add_job.py
import os
import streamlit as st
from services.job_parser import fetch_job_text
from services.save_job import save_job
from services.job_extraction_agent.run_chain import run_job_extraction_chain
from services.skill_matching_agent.score_job_fit import score_job_fit

def _clear_add_job_session():
    for key in ["job_data", "match", "job_url_input", "job_text_input", "job_url_ref", "view_job_path"]:
        st.session_state.pop(key, None)
    # Reset page and flags
    st.session_state["selected_page"] = "Add Job"
    st.session_state["analyzing_job"] = False
    st.session_state["analysis_requested"] = False

def _kickoff_analysis():
    # Phase 1: acquire lock and rerun so UI disables immediately
    st.session_state["analyzing_job"] = True
    st.session_state["analysis_requested"] = True

def add_job(profile: dict):
    # init flags
    if "analyzing_job" not in st.session_state:
        st.session_state["analyzing_job"] = False
    if "analysis_requested" not in st.session_state:
        st.session_state["analysis_requested"] = False

    st.header("📎 Add a Job Listing")
    input_mode = st.radio("How would you like to add a job?", ["URL", "Full Text"], index=0)

    disabled = st.session_state["analyzing_job"]

    if input_mode == "URL":
        st.text_input("Paste job URL here", key="job_url_input", disabled=disabled)
    else:
        st.text_area("Paste full job description text here", height=50, key="job_text_input", disabled=disabled)
        st.text_input("Optional: Paste job URL for reference", key="job_url_ref", disabled=disabled)

    col_analyze, col_clear = st.columns([1, 1])

    analyze_label = "Analyzing…" if disabled else "Analyze Job"
    col_analyze.button(
        analyze_label,
        key="scan_job_btn",
        disabled=disabled,
        on_click=_kickoff_analysis
    )

    if ("job_data" in st.session_state) or ("match" in st.session_state):
        col_clear.button("Clear Job Session", key="clear_job_session_top", on_click=_clear_add_job_session, disabled=disabled)

    # Phase 2: do the work while the button stays disabled and show stages
    if st.session_state["analyzing_job"] and st.session_state["analysis_requested"]:
        try:
            with st.status("Analyzing job…", expanded=True) as status_box:
                # Validate/get inputs
                if input_mode == "URL":
                    url_val = (st.session_state.get("job_url_input") or "").strip()
                    if not url_val:
                        st.warning("Please paste a job URL.")
                        st.session_state["analysis_requested"] = False
                        return
                    status_box.update(label="Fetching job content…")
                    job_text_local = fetch_job_text(url_val)
                    if not job_text_local:
                        st.error("Could not fetch this URL. If it is blocked, switch to 'Full Text' and paste the content.")
                        st.session_state["analysis_requested"] = False
                        return
                    job_url_local = url_val
                else:
                    text_val = (st.session_state.get("job_text_input") or "").strip()
                    if not text_val:
                        st.warning("Please paste the full job description text.")
                        st.session_state["analysis_requested"] = False
                        return
                    job_text_local = text_val
                    job_url_local = (st.session_state.get("job_url_ref") or "").strip()

                status_box.update(label="Extracting structured details…")
                job_data = run_job_extraction_chain(job_text_local, job_url_local)

                status_box.update(label="Scoring match against your profile…")
                match = score_job_fit(job_data, profile)
                job_data["match"] = match

                # Save to session for display
                st.session_state["job_data"] = job_data
                st.session_state["match"] = match

                status_box.update(label="Done", state="complete")

        except Exception as e:
            st.error(f"Analysis failed: {e}")
        finally:
            # Release lock and clear the one-shot trigger
            st.session_state["analyzing_job"] = False
            st.session_state["analysis_requested"] = False
            st.rerun()  # refresh UI to show results and re-enable controls

    # === Display saved data from session ===
    if "job_data" in st.session_state:
        st.subheader("📌 Extracted Job Details")
        st.json(st.session_state["job_data"])

    # === Save and Clear ===
    if "job_data" in st.session_state:
        job_data = st.session_state["job_data"]

        if st.button("💾 Save this Job", key="save_job_btn", disabled=st.session_state["analyzing_job"]):
            path = save_job(job_data)
            job_data["_source_path"] = path
            st.session_state["view_job_path"] = path
            st.session_state["selected_page"] = "View Job"
            st.rerun()

        st.button(
            "Clear Job Session",
            key="clear_job_session_bottom",
            disabled=st.session_state["analyzing_job"],
            on_click=_clear_add_job_session,
        )
