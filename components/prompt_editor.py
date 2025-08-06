import streamlit as st
import os

def show_prompt_editor():
    st.subheader("🧠 System Prompt Templates")
    tabs = st.tabs(["Cover Letter", "Resume"])

    # cover letter tab
    with tabs[0]:
        path = "prompts/cover_letter_prompt.txt"
        if not os.path.exists(path):
            st.warning("Cover-letter prompt not found")
        else:
            with open(path) as f:
                cover = f.read()
            updated = st.text_area("Cover Letter System Prompt", cover, height=300)
            if st.button("Save Cover Prompt"):
                with open(path, "w") as f:
                    f.write(updated)
                st.success("Cover prompt saved")

    # resume tab
    with tabs[1]:
        path = "prompts/resume_prompt.txt"
        if not os.path.exists(path):
            st.warning("Resume prompt not found")
        else:
            with open(path) as f:
                resume = f.read()
            updated = st.text_area("Resume System Prompt", resume, height=300)
            if st.button("Save Resume Prompt"):
                with open(path, "w") as f:
                    f.write(updated)
                st.success("Resume prompt saved")
