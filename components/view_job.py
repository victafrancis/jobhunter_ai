import streamlit as st
import json
import os
import markdown2
from services.google_docs_utils import create_google_doc_from_html
from services.cover_letter_agent.generate_cover_letter import generate_cover_letter as cl_generate
from services.resume_agent.generate_resume import generate_resume as res_generate
from services.sheets_tracker import log_application
from streamlit_quill import st_quill
from utils.config.config import GOOGLE_DRIVE_FOLDERS, SHEETS_URL
from datetime import datetime

def save_job_json(job: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

def clear_job_session_state():
    for key in [
        "view_cl",
        "view_res",
        "cover_letter_url",
        "resume_url",
        "last_viewed_job"
    ]:
        st.session_state.pop(key, None)

def show_view_job(profile: dict):
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("← Back", key="back_to_feed_top"):
            clear_job_session_state()
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Saved Jobs"
            st.rerun()
    with col2:
        st.header("🔎 View Job Details")


    path = st.session_state.get("view_job_path")
    if not path or not os.path.exists(path):
        st.warning("No job selected. Go back to Saved Jobs to pick one.")
        if st.button("← Back"):
            clear_job_session_state()
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Saved Jobs"  # manually set next page
            st.rerun()
        return

    # Clear session state if viewing a different job than before
    if st.session_state.get("last_viewed_job") != path:
        clear_job_session_state()
        st.session_state["last_viewed_job"] = path

    with open(path, "r", encoding="utf-8") as f:
        job = json.load(f)

    st.subheader(f"{job.get('job_title', 'Unknown Title')} at {job.get('company', 'Unknown Company')}")
    st.markdown(f"📍 {job.get('location', '—')}")

    # --- Full Job Details as two-column rows ---
    st.markdown("### 📋 Full Job Details")

    basic_fields = {
        "Job Title": job.get("job_title", "—"),
        "Company": job.get("company", "—"),
        "Location": job.get("location", "—"),
        "Work Location": job.get("work_location", "—"),
        "Salary": job.get("salary", "—"),
        "Job Type": job.get("job_type", "—"),
        "Summary": job.get("summary", "—"),
        "URL": job.get("url", "—"),
        "Notes": job.get("notes", "—"),
        "Date Added": job.get("date_added", "—"),
        "Date Applied": job.get("date_applied", "—"),
    }

    # render each basic field
    for label, val in basic_fields.items():
        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**{label}**")
        col2.markdown(val)

    # now the list-style sections
    list_sections = {
        "Required Skills": job.get("required_skills", []),
        "Nice-to-Have Skills": job.get("nice_to_have_skills", []),
        "Responsibilities": job.get("responsibilities", []),
        "Qualifications": job.get("qualifications", []),
    }

    for section, items in list_sections.items():
        if items:
            col1, col2 = st.columns([1, 3])
            col1.markdown(f"**{section}**")
            # join into markdown bullets
            bullets = "\n".join(f"- {i}" for i in items)
            col2.markdown(bullets)

    st.markdown("---")

    # --- Profile Match Details ---
    match = job.get("match", {})

    st.markdown("### 🤝 Profile Match Details")

    if not match:
        st.info("No match data available. Try re-running the skill matching agent.")
    else:
        scores = match.get("scores", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Skill Score", f"{scores.get('skill_score', 0)}%")
        col2.metric("Preference Score", f"{scores.get('preference_score', 0)}%")
        col3.metric("Overall Score", f"{scores.get('overall_score', 0)}%")

        # --- Skills ---
        st.subheader("Skills Match")
        skills_data = match.get("fit", {}).get("skills", {})
        for skill_type, data in skills_data.items():
            st.markdown(f"**{skill_type.replace('_', ' ').title()}**")
            col1, col2 = st.columns(2)
            col1.markdown("✅ Matched")
            col1.markdown("\n".join(f"- {s}" for s in data.get("matched", [])) or "_None_")
            col2.markdown("❌ Missing")
            col2.markdown("\n".join(f"- {s}" for s in data.get("missing", [])) or "_None_")
            st.markdown(f"Score: **{data.get('score', 0)}%**")

        # --- Qualifications ---
        st.subheader("Qualifications")
        quals = match.get("fit", {}).get("qualifications", {})
        col1, col2 = st.columns(2)
        col1.markdown("✅ Matched")
        col1.markdown("\n".join(f"- {q}" for q in quals.get("matched", [])) or "_None_")
        col2.markdown("❌ Missing")
        col2.markdown("\n".join(f"- {q}" for q in quals.get("missing", [])) or "_None_")
        st.markdown(f"Score: **{quals.get('score', 0)}%**")

        # --- Responsibilities evidence ---
        st.subheader("Responsibilities Evidence")
        resp_data = match.get("fit", {}).get("responsibilities", {})
        confidence = resp_data.get("confidence", 0)
        st.markdown(f"**Coverage Confidence:** {confidence}%")
        for r in resp_data.get("evidence", []):
            st.markdown(f"- **{r.get('resp', '')}** → _{r.get('evidence', '')}_")

        # --- Analysis ---
        st.subheader("Analysis")
        analysis = match.get("analysis", {})
        st.markdown("**Strengths**")
        st.markdown("\n".join(f"- {s}" for s in analysis.get("strengths", [])) or "_None_")
        st.markdown("**Gaps**")
        st.markdown("\n".join(f"- {g}" for g in analysis.get("gaps", [])) or "_None_")
        st.markdown("**Fast Upskill Suggestions**")
        st.markdown("\n".join(f"- {u}" for u in analysis.get("fast_upskill_suggestions", [])) or "_None_")

        # --- Doc recommendations ---
        st.subheader("Document Recommendations")
        doc_recs = match.get("doc_recommendations", {})
        cl_recs = doc_recs.get("cover_letter", {})
        res_recs = doc_recs.get("resume", {})

        with st.expander("📄 Cover Letter Recommendations", expanded=False):
            st.markdown("**Highlights**")
            st.markdown("\n".join(f"- {h}" for h in cl_recs.get("highlights", [])) or "_None_")
            st.markdown("**Address Gaps**")
            st.markdown("\n".join(f"- {a}" for a in cl_recs.get("address_gaps", [])) or "_None_")
            st.markdown(f"**Tone:** {cl_recs.get('tone', 'N/A')}")

        with st.expander("📄 Resume Recommendations", expanded=False):
            st.markdown("**Reorder Suggestions**")
            st.markdown("\n".join(f"- {r}" for r in res_recs.get("reorder_suggestions", [])) or "_None_")
            st.markdown("**Keywords to Include**")
            st.markdown("\n".join(f"- {k}" for k in res_recs.get("keywords_to_include", [])) or "_None_")
            st.markdown("**Bullets to Add**")
            st.markdown("\n".join(f"- {b}" for b in res_recs.get("bullets_to_add", [])) or "_None_")

    # --- Generate or View Application Documents ---
    st.markdown("### ✨ Application Documents")
    col1, col2 = st.columns([1,1])

    with col1:
        cl_url = job.get("cover_letter_url") or st.session_state.get("cover_letter_url")
        if cl_url:
            #  show “view” link
            st.markdown(f"[📄 View Cover Letter ↗]({cl_url})")
            #  Regenerate logic
            if st.button("🔄 Regenerate Cover Letter", key="regen_cl"):
                with st.spinner("Regenerating cover letter..."):
                    cl = cl_generate(job, profile)
                    st.session_state["view_cl"] = cl
                    job.pop("cover_letter_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Cover Letter", key="gen_cl"):
                with st.spinner("Generating cover letter..."):
                    cl = cl_generate(job, profile)
                    st.session_state["view_cl"] = cl

    # Resume column
    with col2:
        res_url = job.get("resume_url") or st.session_state.get("resume_url")
        if res_url:
            st.markdown(f"[📄 View Resume ↗]({res_url})")
            if st.button("🔄 Regenerate Resume", key="regen_res"):
                with st.spinner("Regenerating resume..."):
                    res = res_generate(job, profile)
                    st.session_state["view_res"] = res
                    job.pop("resume_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Resume", key="gen_res"):
                with st.spinner("Generating resume..."):
                    res = res_generate(job, profile)
                    st.session_state["view_res"] = res

    # --- Cover Letter Editor ---
    if st.session_state.get("view_cl"):
        with st.expander("📝 Edit Cover Letter", expanded=True):
            # Convert Markdown → HTML before rendering
            html_cl = markdown2.markdown(st.session_state["view_cl"])
            edited_cl = st_quill(html_cl, html=True, key="view_quill_cl")
            if st.button("📄 Export to Google Docs", key="export_cl"):
                with st.spinner("Exporting to Google Docs..."):
                    company = job.get("company", "UnknownCompany")
                    job_title = job.get("job_title", "UnknownJob")
                    doc_title = f"{company}_{job_title}_Cover_Letter"
                try:
                    cover_letter_folder_id = GOOGLE_DRIVE_FOLDERS["cover_letters"]
                    cl_url = create_google_doc_from_html(edited_cl, doc_title, folder_id=cover_letter_folder_id)
                    # save url to job JSON
                    job["cover_letter_url"] = cl_url
                    save_job_json(job, path)
                    st.session_state["cover_letter_url"] = cl_url
                    st.success(f"✅ [Click here to open in Google Docs ↗]({cl_url})")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    # --- Resume Editor ---
    if st.session_state.get("view_res"):
        with st.expander("📝 Edit Resume", expanded=True):
            # Convert Markdown → HTML before rendering
            html_res = markdown2.markdown(st.session_state["view_res"])
            edited_res = st_quill(html_res, html=True, key="view_quill_res")
            if st.button("📄 Export to Google Docs", key="export_res"):
                with st.spinner("Exporting resume to Google Docs..."):
                    company = job.get("company", "UnknownCompany")
                    job_title = job.get("job_title", "UnknownJob")
                    doc_title = f"{company}_{job_title}_Resume"
                try:
                    resume_folder_id = GOOGLE_DRIVE_FOLDERS["resumes"]
                    res_url = create_google_doc_from_html(edited_res, doc_title, folder_id=resume_folder_id)
                    # Save URL to job JSON
                    job["resume_url"] = res_url
                    save_job_json(job, path)
                    st.session_state["resume_url"] = res_url
                    st.success(f"✅ [Click here to open in Google Docs ↗]({res_url})")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    # --- Log to Google Sheets & mark as applied ---
    if job.get("sheets_logged"):
        st.success("✅ Already logged to Google Sheets for this job.")
        # Show a link button and a plain link for redundancy
        st.link_button("↗ Open in Google Sheets", SHEETS_URL, help="Open your application tracker")
    else:
        if st.button("➕ Add to Google Sheets", key="add_to_sheets"):
            with st.spinner("Logging application to Google Sheets..."):
                cl_url = st.session_state.get("cover_letter_url", "")
                res_url = st.session_state.get("resume_url", "")

                # Log to Sheets
                log_application(
                    job.get("job_title", ""),
                    job.get("company", ""),
                    job.get("url", ""),
                    resume_path=res_url,
                    cover_letter_path=cl_url,
                    status="Applied"
                )

                # Save a simple flag and the global sheet link
                job["sheets_logged"] = True
                job["date_applied"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_job_json(job, path)

                st.success(f"✅ Logged and marked as applied on {job['date_applied']}")
                st.link_button("↗ Open in Google Sheets", SHEETS_URL)

    if st.button("← Back to Saved Jobs"):
        clear_job_session_state()
        st.session_state.pop("view_job_path", None)
        st.rerun()
