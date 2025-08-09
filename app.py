import streamlit as st
import json
import os

from components.profile_view import show_profile
from components.job_feed import show_job_cards, load_saved_jobs
from components.prompt_editor import show_prompt_editor
from components.add_job import add_job
from components.view_job import show_view_job
from utils.config.settings import load_settings, save_settings

# Load profile
def load_profile():
    with open("profile.json", "r") as f:
        return json.load(f)
    
# initialize settings
if "settings" not in st.session_state:
    st.session_state["settings"] = load_settings()

# function to set developer mode
def set_dev_mode(value: bool):
    s = st.session_state["settings"]
    s["developer_mode"] = bool(value)
    save_settings(s)
    st.session_state["settings"] = s

# initialize developer mode toggle
with st.sidebar:
    st.caption("Settings")
    dev_mode = st.toggle(
        "Developer mode",
        value=st.session_state["settings"]["developer_mode"],
        help="Force cheapest models everywhere"
    )
    if dev_mode != st.session_state["settings"]["developer_mode"]:
        set_dev_mode(dev_mode)
    st.write("🟢 Dev mode ON" if dev_mode else "⚪ Dev mode OFF")

# UI Layout
def main():
    st.set_page_config(page_title="JobHunter.AI", layout="wide")
    st.sidebar.title("🔍 JobHunter.AI")

    profile = load_profile()

    # Handle dynamic view job session route
    if "view_job_path" in st.session_state and st.session_state["view_job_path"]:
        page = "View Job"
    else:
        PAGES = ["Add Job", "Saved Jobs", "Prompt Settings"]
        default_page = st.session_state.get("selected_page", PAGES[0])
        page = st.sidebar.selectbox("🔧 Navigation", PAGES, index=PAGES.index(default_page))
        st.session_state["selected_page"] = page

    if page == "Add Job":
        add_job(profile)
    elif page == "Saved Jobs":
        show_profile(profile)
        jobs = load_saved_jobs()
        show_job_cards(jobs, profile)
    elif page == "Prompt Settings":
        show_prompt_editor()
    elif page == "View Job":
        show_view_job(profile)

if __name__ == "__main__":
    main()
