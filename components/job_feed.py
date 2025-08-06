import os
import json
import streamlit as st

JOBS_FOLDER = "data/jobs"

def load_saved_jobs(folder=JOBS_FOLDER):
    jobs = []
    if not os.path.exists(folder):
        os.makedirs(folder)
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                job = json.load(f)
                job["_source_path"] = os.path.join(folder, filename)
                jobs.append(job)
    return jobs

def show_job_cards(jobs, profile):
    st.header("🗃️ Saved Jobs")

    if not jobs:
        st.info("No saved jobs yet. Add one on the 'Add Job' page.")
        return

    for idx, job in enumerate(jobs):
        with st.container(border=True):
            st.subheader(f"{job.get('job_title')} at {job.get('company')}")
            st.markdown(f"📍 {job.get('location', 'N/A')}  |  💼 {job.get('job_type', 'N/A')}")
            st.write(job.get("summary", "")[:400] + "...")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 View", key=f"view_{idx}"):
                    st.session_state["view_job_path"] = job["_source_path"]
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    os.remove(job["_source_path"])
                    st.rerun()
