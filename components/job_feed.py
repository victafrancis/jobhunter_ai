import os
import json
import math
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

    # Recursive load
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

def _ensure_session_defaults():
    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "Newest"
    if "job_filter" not in st.session_state:
        st.session_state["job_filter"] = "All Jobs"
    if "page_size" not in st.session_state:
        st.session_state["page_size"] = 10
    if "page" not in st.session_state:
        st.session_state["page"] = 0
    if "search_query" not in st.session_state:
        st.session_state["search_query"] = ""
    if "_last_controls_snapshot" not in st.session_state:
        st.session_state["_last_controls_snapshot"] = None

def _controls_snapshot():
    # Reset page when these controls change
    return (
        st.session_state.get("sort_order"),
        st.session_state.get("job_filter"),
        st.session_state.get("page_size"),
        st.session_state.get("search_query"),
    )

def _reset_page_if_controls_changed():
    snap = _controls_snapshot()
    if st.session_state["_last_controls_snapshot"] != snap:
        st.session_state["page"] = 0
        st.session_state["_last_controls_snapshot"] = snap

def show_job_cards(jobs):
    _ensure_session_defaults()

    st.header("🗃️ Saved Jobs")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        sort_order = st.radio("Sort by", ["Newest", "Oldest"], horizontal=True, key="sort_order")
    with col2:
        filter_option = st.radio("Filter", ["All Jobs", "Applied Only"], horizontal=True, key="job_filter")
    with col3:
        st.text_input("Search", key="search_query", placeholder="Title, company or location..")

    _reset_page_if_controls_changed()

    if not jobs:
        st.info("No saved jobs yet. Add one on the 'Add Job' page.")
        return

    # Filter
    if filter_option == "Applied Only":
        jobs = [job for job in jobs if job.get("date_applied")]

    # Search
    q = (st.session_state.get("search_query") or "").strip().lower()
    if q:
        def _matches(job):
            title = (job.get("job_title") or "").lower()
            company = (job.get("company") or "").lower()
            location = (job.get("location") or "").lower()
            return q in title or q in company or q in location
        jobs = [j for j in jobs if _matches(j)]

    # Sort using _parse_when
    jobs = sorted(
        jobs,
        key=lambda j: _parse_when(j.get("date_added", "")),
        reverse=(sort_order == "Newest"),
    )

    # Pagination math
    total = len(jobs)
    page_size = st.session_state["page_size"]
    total_pages = max(1, math.ceil(total / page_size))
    page = min(st.session_state["page"], total_pages - 1)
    page = max(0, page)

    # Slice
    start = page * page_size
    end = start + page_size
    visible_jobs = jobs[start:end]

    # Render cards (same as before) ...
    for idx, job in enumerate(visible_jobs):
        with st.container(border=True):
            if job.get("date_applied"):
                st.markdown(f"✅ **Applied on {job['date_applied']}**")
            st.subheader(f"{job.get('job_title')} at {job.get('company')}")
            st.markdown(f"📍 {job.get('location', 'N/A')}  |  {job.get('work_location', 'N/A')}")
            summary = (job.get("summary") or "").strip()
            if summary:
                st.write(summary[:400] + ("..." if len(summary) > 400 else ""))

            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔍 View", key=f"view_{job.get('_source_path', '')}"):
                    st.session_state["view_job_path"] = job["_source_path"]
                    st.session_state["selected_page"] = "View Job"
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete", key=f"delete_{job.get('_source_path', '')}"):
                    st.session_state["confirm_delete"] = job["_source_path"]
                    st.rerun()

            target = st.session_state.get("confirm_delete")
            if target == job.get("_source_path"):
                st.warning("Delete this job? This cannot be undone.")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("✅ Yes, delete it", key=f"confirm_yes_{job.get('_source_path', '')}"):
                        try:
                            if os.path.exists(target):
                                os.remove(target)
                            st.session_state["confirm_delete"] = None
                            # Keep page valid after deletion
                            st.session_state["page"] = min(st.session_state["page"], max(0, total_pages - 1))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
                with d2:
                    if st.button("❌ Cancel", key=f"confirm_no_{job.get('_source_path', '')}"):
                        st.session_state["confirm_delete"] = None
                        st.rerun()

    # Bottom controls
    st.divider()
    left, mid, right = st.columns([1, 2, 1])

    with left:
        st.caption(f"Showing {0 if total == 0 else start + 1}-{min(end, total)} of {total}")

    with mid:
        b1, b2, b3, b4, sel = st.columns([1, 1, 1, 1, 2])

        # First
        if b1.button("⏮ First", disabled=(page == 0)):
            st.session_state["page"] = 0
            st.rerun()

        # Prev
        if b2.button("◀ Prev", disabled=(page == 0)):
            st.session_state["page"] = max(0, page - 1)
            st.rerun()

        # Next
        if b3.button("Next ▶", disabled=(page >= total_pages - 1)):
            st.session_state["page"] = min(total_pages - 1, page + 1)
            st.rerun()

        # Last
        if b4.button("Last ⏭", disabled=(page >= total_pages - 1)):
            st.session_state["page"] = total_pages - 1
            st.rerun()

        # Listings per page dropdown
        with sel:
            st.selectbox(
                "Listings per page",
                [5, 10, 20, 50],
                index=[5, 10, 20, 50].index(st.session_state["page_size"]),
                key="page_size",
            )

    with right:
        st.caption(f"Page {page + 1} of {total_pages}")

