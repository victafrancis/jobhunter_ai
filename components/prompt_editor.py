# /mnt/data/prompt_editor.py
import streamlit as st
import os
from utils.prompt_loader import load_prompt, save_prompt, list_prompts

def _pick_or_default(options, default_name):
    return default_name if default_name in options else (options[0] if options else default_name)

def show_prompt_editor():
    st.header("⚙️ Prompt Settings")
    st.subheader("🧠 System Prompt Templates")
    tabs = st.tabs(["Cover Letter", "Resume"])

    # ---------- Cover Letter tab ----------
    with tabs[0]:
        st.caption("Select a cover-letter prompt file to edit or create a new one.")
        cl_files = list_prompts("cover_letter_agent")
        selected = st.selectbox(
            "Choose cover-letter prompt file",
            options=cl_files,
            index=0 if cl_files else None,
            key="cl_prompt_selected"
        )

        # Editor
        if selected:
            content = load_prompt("cover_letter_agent", selected)
            edited = st.text_area("Cover Letter System Prompt", content, height=300, key="cl_editor")
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button("Save Cover Prompt", key="cl_save"):
                    save_prompt("cover_letter_agent", selected, edited)
                    st.success(f"Saved {selected}")
            with col2:
                if st.button("Reload From Disk", key="cl_reload"):
                    st.rerun()
        else:
            st.info("No cover-letter prompt files found. Create one above.")

        # Create New
        with st.expander("Create New Cover-letter Prompt"):
            new_name = st.text_input(
                "New filename (must end with .txt)",
                value="cover_letter_prompt_new.txt",
                key="cl_new_name"
            )
            new_boiler = st.text_area(
                "Template content",
                value="You are a helpful assistant that writes concise, human cover letters under 300 words.",
                height=150,
                key="cl_new_content"
            )
            if st.button("Create File", key="cl_create"):
                if not new_name.endswith(".txt"):
                    st.error("Filename must end with .txt")
                elif new_name in cl_files:
                    st.error("A file with that name already exists.")
                else:
                    save_prompt("cover_letter_agent", new_name, new_boiler)
                    st.success(f"Created {new_name}. Use the dropdown above to open it.")
                    st.rerun()

    # ---------- Resume tab ----------
    with tabs[1]:
        st.caption("Select a resume prompt file to edit or create a new one.")
        res_files = list_prompts("resume_agent")
        selected = st.selectbox(
            "Choose resume prompt file",
            options=res_files,
            index=0 if res_files else None,
            key="res_prompt_selected"
        )

        if selected:
            content = load_prompt("resume_agent", selected)
            edited = st.text_area("Resume System Prompt", content, height=300, key="res_editor")
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button("Save Resume Prompt", key="res_save"):
                    save_prompt("resume_agent", selected, edited)
                    st.success(f"Saved {selected}")
            with col2:
                if st.button("Reload From Disk", key="res_reload"):
                    st.rerun()
        else:
            st.info("No resume prompt files found. Create one above.")

        # Create New
        with st.expander("Create New Resume Prompt"):
            new_name = st.text_input(
                "New filename (must end with .txt)",
                value="resume_prompt_new.txt",
                key="res_new_name"
            )
            new_boiler = st.text_area(
                "Template content",
                value="You write concise, ATS-aware resume text. Keep bullets sharp and action-led.",
                height=150,
                key="res_new_content"
            )
            if st.button("Create File", key="res_create"):
                if not new_name.endswith(".txt"):
                    st.error("Filename must end with .txt")
                elif new_name in res_files:
                    st.error("A file with that name already exists.")
                else:
                    save_prompt("resume_agent", new_name, new_boiler)
                    st.success(f"Created {new_name}. Use the dropdown above to open it.")
                    st.rerun()
