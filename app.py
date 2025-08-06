import streamlit as st
import json
import os

from components.profile_view import show_profile
from components.job_feed import show_job_cards
from components.prompt_editor import show_prompt_editor


# Load profile
def load_profile():
    with open("profile.json", "r") as f:
        return json.load(f)

# Load mock jobs
def load_mock_jobs():
    with open("mock_data/sample_jobs.json", "r") as f:
        return json.load(f)


# UI Layout
def main():
    st.set_page_config(page_title="JobHunter.AI", layout="wide")
    st.title("🔎 JobHunter.AI")

    profile = load_profile()
    jobs = load_mock_jobs()

    PAGES = ["Job Feed", "Prompt Settings"]
    page = st.sidebar.selectbox("🔧 Navigation", PAGES)

    if page == "Job Feed":
        show_profile(profile)
        show_job_cards(jobs, profile)
    elif page == "Prompt Settings":
        show_prompt_editor()

if __name__ == "__main__":
    main()
