import streamlit as st
import os
from utils.prompt_loader import load_prompt, save_prompt

def show_prompt_editor():
    st.header("⚙️ Prompt Settings")
    st.subheader("🧠 System Prompt Templates")
    tabs = st.tabs(["Cover Letter", "Resume"])

    # cover letter tab
    with tabs[0]:
        try:
            cover = load_prompt("cover_letter_agent", "cover_letter_prompt.txt")
        except FileNotFoundError:
            st.warning("Cover-letter prompt not found")
            cover = ""
        updated = st.text_area("Cover Letter System Prompt", cover, height=300)
        if st.button("Save Cover Prompt"):
            save_prompt("cover_letter_agent", "cover_letter_prompt.txt", updated)
            st.success("Cover prompt saved")

    # resume tab
    with tabs[1]:
        try:
            resume = load_prompt("resume_agent", "resume_prompt.txt")
        except FileNotFoundError:
            st.warning("Resume prompt not found")
            resume = ""
        updated = st.text_area("Resume System Prompt", resume, height=300)
        if st.button("Save Resume Prompt"):
            save_prompt("resume_agent", "resume_prompt.txt", updated)
            st.success("Resume prompt saved")
