import os
import json
import streamlit as st
from datetime import datetime

JOBS_FOLDER = "data/jobs"

def _parse_when(s: str):
    """Try parsing multiple date formats safely for sorting."""
    if not s:
        return datetime.min
    try:
        return datetime.fromisoformat(s.replace("Z", "").split(".")[0])
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

def load_saved_jobs(folder=JOBS_FOLDER):
    jobs = []
    if not os.path.exists(folder):
        os.makedirs(folder)

    # New: recursive load
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".json"):
                path = os.path.join(root, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        job = json.load(f)
                        job["_source_path"] = path
                        jobs.append(job)
                except Exception as e:
                    st.warning(f"Skipped {path}: {e}")
    return jobs

def show_job_cards(jobs):
    st.header("🗃️ Saved Jobs")

    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "Newest"
    if "job_filter" not in st.session_state:
        st.session_state["job_filter"] = "All Jobs"

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

    # Sort using _parse_when
    jobs = sorted(jobs, key=lambda j: _parse_when(j.get("date_added", "")), reverse=(sort_order == "Newest"))

    for idx, job in enumerate(jobs):
        with st.container(border=True):
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
                    st.rerun()

            target = st.session_state.get("confirm_delete")
            if target == job["_source_path"]:
                st.warning("Delete this job? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, delete it", key=f"confirm_yes_{idx}"):
                        try:
                            if os.path.exists(target):
                                os.remove(target)
                            st.session_state["confirm_delete"] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
                with c2:
                    if st.button("❌ Cancel", key=f"confirm_no_{idx}"):
                        st.session_state["confirm_delete"] = None
                        st.rerun()
