import streamlit as st
import json
import os
from services.google_docs_utils import create_google_doc_from_html
from services.gpt_utils import match_profile_to_job, generate_cover_letter, generate_resume
from services.sheets_tracker import log_application
from streamlit_quill import st_quill
from config import GOOGLE_DRIVE_FOLDERS
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

    # --- Profile Match Details as two-column rows ---
    match = match_profile_to_job(job, profile)

    # Build one big JSON context string for GPT user prompt
    context_json = json.dumps({
        "job_details":   job,
        "profile":       profile,
        "profile_match": match
    }, indent=2)

    st.markdown("### 🤝 Profile Match Details")
    
    # match score
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Match Score**")
    col2.metric(" ", f"{match.get('match_score', 0)}%")  # one space avoids warning

    # missing skills
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Missing Skills**")
    missing = match.get("missing_skills", [])
    if missing:
        col2.markdown("\n".join(f"- {s}" for s in missing))
    else:
        col2.markdown("None 🎉")

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
                    # feed the full JSON context in
                    prompt_text = f"Please write an engaging cover letter based on this context:\n\n{context_json}"
                    cl = generate_cover_letter(prompt_text, company=job["company"])
                    st.session_state["view_cl"] = cl
                    job.pop("cover_letter_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Cover Letter", key="gen_cl"):
                with st.spinner("Generating cover letter..."):
                    prompt_text = f"Please write an engaging cover letter based on this context:\n\n{context_json}"
                    cl = generate_cover_letter(prompt_text, company=job["company"])
                    st.session_state["view_cl"] = cl

    # Resume column
    with col2:
        res_url = job.get("resume_url") or st.session_state.get("resume_url")
        if res_url:
            #  show “view” link
            st.markdown(f"[📄 View Cover Letter ↗]({cl_url})")
            # Regenerate logic
            if st.button("🔄 Regenerate Resume", key="regen_res"):
                with st.spinner("Regenerating resume..."):
                    prompt_text = f"Please write a concise, ATS-friendly resume based on this context:\n\n{context_json}"
                    res = generate_resume(prompt_text, company=job["company"])
                    st.session_state["view_res"] = res
                    job.pop("resume_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Resume", key="gen_res"):
                with st.spinner("Generating resume..."):
                    prompt_text = f"Please write a concise, ATS-friendly resume based on this context:\n\n{context_json}"
                    res = generate_resume(prompt_text, company=job["company"])
                    st.session_state["view_res"] = res

    # --- Cover Letter Editor ---
    if st.session_state.get("view_cl"):
        with st.expander("📝 Edit Cover Letter", expanded=True):
            edited_cl = st_quill(st.session_state["view_cl"], html=True, key="view_quill_cl")
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
            edited_res = st_quill(st.session_state["view_res"], html=True, key="view_quill_res")
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
    if st.button("➕ Add to Google Sheets", key="add_to_sheets"):
        with st.spinner("Logging application to Google Sheets..."):
            # grab whatever URLs exist (or empty string)
            cl_url = st.session_state.get("cover_letter_url", "")
            res_url = st.session_state.get("resume_url", "")

            # 1) Log to Sheets
            log_application(
                job["job_title"],
                job["company"],
                job["url"],
                resume_path=res_url,
                cover_letter_path=cl_url,
                status="Applied"
            )  # :contentReference[oaicite:0]{index=0}

            # 2) Update the JSON on disk
            job["date_applied"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(job, f, indent=2)

            st.success(f"✅ Logged and marked as applied on {job['date_applied']}")

    if st.button("← Back to Saved Jobs"):
        clear_job_session_state()
        st.session_state.pop("view_job_path", None)
        st.rerun()
