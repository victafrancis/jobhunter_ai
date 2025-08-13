import os
import json
import streamlit as st
from datetime import datetime

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

def show_job_cards(jobs):
    st.header("🗃️ Saved Jobs")
    
    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "Newest"
    if "job_filter" not in st.session_state:
        st.session_state["job_filter"] = "All Jobs"

    # sort and filter options
    col1, col2 = st.columns([1, 2])
    with col1:
        sort_order = st.radio("Sort by", ["Newest", "Oldest"], horizontal=True, key="sort_order")
    with col2:
        filter_option = st.radio("Filter", ["All Jobs", "Applied Only"], horizontal=True, key="job_filter")

    if not jobs:
        st.info("No saved jobs yet. Add one on the 'Add Job' page.")
        return
    
    # Filter
    if filter_option == "Applied Only":
        jobs = [job for job in jobs if job.get("date_applied")]

    # Sort
    def job_sort_key(job):
        return job.get("date_added", "1970-01-01")
    jobs = sorted(jobs, key=job_sort_key, reverse=(sort_order == "Newest"))

    for idx, job in enumerate(jobs):
        with st.container(border=True):
            # show applied badge if set
            if job.get("date_applied"):
                st.markdown(f"✅ **Applied on {job['date_applied']}**")

            st.subheader(f"{job.get('job_title')} at {job.get('company')}")
            st.markdown(f"📍 {job.get('location', 'N/A')}  |  {job.get('work_location', 'N/A')}")
            summary = (job.get("summary") or "").strip()
            if summary:
                st.write(summary[:400] + ("..." if len(summary) > 400 else ""))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 View", key=f"view_{idx}"):
                    st.session_state["view_job_path"] = job["_source_path"]
                    st.session_state["selected_page"] = "View Job"
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    st.session_state["confirm_delete"] = job["_source_path"]

            # If a delete is requested, show confirmation
            if "confirm_delete" in st.session_state and st.session_state["confirm_delete"]:
                st.warning("Are you sure you want to delete this job?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, delete it"):
                        os.remove(st.session_state["confirm_delete"])
                        st.session_state["confirm_delete"] = None
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel"):
                        st.session_state["confirm_delete"] = None
