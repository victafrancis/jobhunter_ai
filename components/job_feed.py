from datetime import datetime
import os
import streamlit as st
from gpt_utils import generate_cover_letter, generate_resume
from utils import load_cover_letter_prompt_template, load_resume_prompt_template
from pdf_utils import export_cover_letter_pdf, export_resume_pdf
from streamlit_quill import st_quill
from sheets_tracker import log_application

def show_job_cards(jobs, profile):
    st.subheader("🔥 New Opportunities")

    for job in jobs:
        job_key = job["url"]

        with st.container():
            # --- Job info ---
            st.markdown(f"### {job['title']} at {job['company']}")
            st.markdown(f"📍 {job['location']}")
            st.markdown(job["summary"])
            st.markdown(f"[🔗 View Job Posting]({job['url']})", unsafe_allow_html=True)

            # --- Generate Cover Letter ---
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Generate Cover Letter", key=f"cl_{job_key}"):
                    with st.spinner(f"🔧 Generating cover letter for {job['company']}..."):
                        prompt_text = build_cover_letter_prompt(job, profile)
                        st.session_state[f"cl_text_{job_key}"] = generate_cover_letter(
                            prompt_text,
                            company=job["company"]
                        )

            with col2:
                if st.button("Generate Resume", key=f"res_{job_key}"):
                    with st.spinner(f"🔧 Generating resume for {job['company']}..."):
                        prompt_text = build_resume_prompt(job, profile)
                        st.session_state[f"res_text_{job_key}"] = generate_resume(
                            prompt_text, company=job["company"]
                        )

            with col3:
                st.button("Save for Later", key=f"save_{job_key}")

        # --- Cover Letter Editor & Preview & Export Section ---
        if f"cl_text_{job_key}" in st.session_state:
            # simple expander—click its header to open or collapse
            with st.expander("✍️ Edit Cover Letter", expanded=True):
                edited_html = st_quill(
                    st.session_state[f"cl_text_{job_key}"],
                    html=True, key=f"quill_cl_{job_key}"
                )

            # Export PDF
            if st.button("📄 Export Cover Letter as PDF", key=f"pdf_{job_key}"):
                file_path = export_cover_letter_pdf(
                    html_content=edited_html,
                    job_title=job["title"],
                    company=job["company"]
                )
                filename = os.path.basename(file_path)
                st.session_state[f"file_path_{job_key}"] = file_path
                st.session_state[f"filename_{job_key}"] = filename
                st.success(f"✔️ Cover letter saved as {filename}")

            # Download button (once PDF exists)
            if f"file_path_{job_key}" in st.session_state:
                with open(st.session_state[f"file_path_{job_key}"], "rb") as f:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=f,
                        file_name=st.session_state[f"filename_{job_key}"],  # use session filename
                        mime="application/pdf",
                        key=f"download_{job_key}"
                    )

            # Persistent Save to Tracker button
            if f"file_path_{job_key}" in st.session_state:
                if not st.session_state.get(f"tracker_saved_{job_key}", False):
                    if st.button("✅ Save to Tracker", key=f"tracker_{job_key}"):
                        log_application(
                            job_title=job["title"],
                            company=job["company"],
                            url=job["url"],
                            resume_path="N/A",
                            cover_letter_path=st.session_state[f"file_path_{job_key}"],
                            status="Pending"
                        )
                        st.session_state[f"tracker_saved_{job_key}"] = True
                        st.success("📋 Application saved to tracker!")

        # --- Resume & Preview & Export Section ---
        if f"res_text_{job_key}" in st.session_state:
            # simple expander—click its header to open or collapse
            with st.expander("✍️ Edit Resume", expanded=True):
                edited_md = st_quill(
                    st.session_state[f"res_text_{job_key}"],
                    html=True, key=f"quill_res_{job_key}"
                )

            # export resume PDF
            if st.button("📄 Export Resume as PDF", key=f"pdf_res_{job_key}"):
                file_path = export_resume_pdf(
                    html_content=edited_md,
                    job_title=job["title"],
                    company=job["company"]
                )
                filename = os.path.basename(file_path)
                st.session_state[f"res_path_{job_key}"] = file_path
                st.session_state[f"res_fname_{job_key}"] = filename
                st.success(f"✔️ Resume saved as {filename}")

            # download resume
            if f"res_path_{job_key}" in st.session_state:
                with open(st.session_state[f"res_path_{job_key}"], "rb") as f:
                    st.download_button(
                        label="⬇️ Download Resume",
                        data=f,
                        file_name=st.session_state[f"res_fname_{job_key}"],
                        mime="application/pdf",
                        key=f"download_res_{job_key}"
                    )

            # save resume to tracker
            if f"res_path_{job_key}" in st.session_state:
                if not st.session_state.get(f"tracker_res_{job_key}", False):
                    if st.button("✅ Save Resume to Tracker", key=f"tracker_res_{job_key}"):
                        log_application(
                            job_title=job["title"],
                            company=job["company"],
                            url=job["url"],
                            resume_path=st.session_state[f"res_path_{job_key}"],
                            cover_letter_path="N/A",
                            status="Pending"
                        )
                        st.session_state[f"tracker_res_{job_key}"] = True
                        st.success("📋 Resume saved to tracker!")

        st.divider()


def build_cover_letter_prompt(job, profile):
    template = load_cover_letter_prompt_template()
    return (
        template
        .replace("{{job_title}}", job["title"])
        .replace("{{company}}", job["company"])
        .replace("{{location}}", job["location"])
        .replace("{{summary}}", job["summary"])
        .replace("{{name}}", profile["name"])
        .replace("{{title}}", profile["title"])
        .replace("{{candidate_location}}", profile["location"])
        .replace("{{skills}}", ", ".join(profile["skills"]))
    )

def build_resume_prompt(job, profile):
    template = load_resume_prompt_template()
    return (template
        .replace("{{job_title}}", job["title"])
        .replace("{{company}}", job["company"])
        .replace("{{location}}", job["location"])
        .replace("{{summary}}", job["summary"])
        .replace("{{name}}", profile["name"])
        .replace("{{title}}", profile["title"])
        .replace("{{candidate_location}}", profile["location"])
        .replace("{{skills}}", ", ".join(profile["skills"]))
    )
