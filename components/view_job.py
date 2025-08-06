import streamlit as st
import json
import os
from services.gpt_utils import match_profile_to_job, generate_cover_letter, generate_resume
from utils.file_utils import load_cover_letter_prompt_template, load_resume_prompt_template
from services.pdf_utils import export_cover_letter_pdf, export_resume_pdf
from streamlit_quill import st_quill

def show_view_job(profile: dict):
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("← Back", key="back_to_feed_top"):
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Job Feed"
            st.rerun()
    with col2:
        st.header("🔎 View Job Details")


    path = st.session_state.get("view_job_path")
    if not path or not os.path.exists(path):
        st.warning("No job selected. Go back to Job Feed to pick one.")
        if st.button("← Back"):
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Job Feed"  # manually set next page
            st.rerun()
        return

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
    st.markdown("### 🤝 Profile Match Details")

    # match score
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Match Score**")
    col2.metric("", f"{match.get('match_score', 0)}%")

    # missing skills
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Missing Skills**")
    missing = match.get("missing_skills", [])
    if missing:
        col2.markdown("\n".join(f"- {s}" for s in missing))
    else:
        col2.markdown("None 🎉")


    def build_prompt(template_loader):
        tmpl = template_loader()
        return (
            tmpl.replace("{{job_title}}", job["job_title"])
                .replace("{{company}}", job["company"])
                .replace("{{location}}", job.get("location",""))
                .replace("{{summary}}", job.get("summary",""))
                .replace("{{name}}", profile["name"])
                .replace("{{title}}", profile["title"])
                .replace("{{candidate_location}}", profile["location"])
                .replace("{{skills}}", ", ".join(profile["skills"]))
        )

    # --- Generate Buttons ---
    st.markdown("### ✨ Generate Application Documents")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✍️ Generate Cover Letter", key="gen_cl"):
            st.session_state["view_cl"] = generate_cover_letter(
                build_prompt(load_cover_letter_prompt_template),
                company=job["company"]
            )

    with col2:
        if st.button("✍️ Generate Resume", key="gen_res"):
            st.session_state["view_res"] = generate_resume(
                build_prompt(load_resume_prompt_template),
                company=job["company"]
            )

    # --- Cover Letter Editor ---
    if st.session_state.get("view_cl"):
        with st.expander("📝 Edit Cover Letter", expanded=True):
            edited_cl = st_quill(st.session_state["view_cl"], html=True, key="view_quill_cl")
            if st.button("📄 Export Cover Letter PDF", key="export_cl"):
                path = export_cover_letter_pdf(edited_cl, job["job_title"], job["company"])
                st.success(f"📁 Saved to: `{path}`")

    # --- Resume Editor ---
    if st.session_state.get("view_res"):
        with st.expander("📝 Edit Resume", expanded=True):
            edited_res = st_quill(st.session_state["view_res"], html=True, key="view_quill_res")
            if st.button("📄 Export Resume PDF", key="export_res"):
                path = export_resume_pdf(edited_res, job["job_title"], job["company"])
                st.success(f"📁 Saved to: `{path}`")


    if st.button("← Back to Saved Jobs"):
        st.session_state.pop("view_job_path", None)
        st.rerun()
