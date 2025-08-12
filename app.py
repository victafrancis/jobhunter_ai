import os
import json
import streamlit as st

# --- Components (same as your original) ---
from components.profile_view import show_profile_page
from components.job_feed import show_job_cards, load_saved_jobs
from components.prompt_editor import show_prompt_editor
from components.add_job import add_job
from components.view_job import show_view_job
from components.settings_editor import show_settings_editor
from utils.config.settings import load_settings, save_settings

# =========================
# 1) Page config FIRST
# =========================
st.set_page_config(
    page_title="JobHunter.AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# 2) Session defaults
# =========================
if "settings" not in st.session_state:
    try:
        st.session_state["settings"] = load_settings()
    except Exception:
        st.session_state["settings"] = {"developer_mode": True}

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Add Job"

if "view_job_path" not in st.session_state:
    st.session_state["view_job_path"] = None

# =========================
# 3) Helpers
# =========================
def load_profile():
    path = "data/profile.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def goto(page_name: str):
    st.session_state["selected_page"] = page_name
    if page_name != "View Job":
        # leaving the detail page, so clear its state
        st.session_state.pop("view_job_path", None)
    st.rerun()

def set_dev_mode(value: bool):
    s = dict(st.session_state["settings"])
    s["developer_mode"] = bool(value)
    save_settings(s)
    st.session_state["settings"] = s

# =========================
# 4) Global CSS (nice nav)
# =========================
st.markdown("""
<style>
/* Keep header so mobile hamburger works */
header[data-testid="stHeader"] {
  background: transparent;
  height: 2.5rem;
  box-shadow: none;
}

/* Sidebar nav look */
.nav-list { margin: 0; padding: 0; }
.nav-item { list-style: none; margin: 0 0 .45rem 0; }

/* Base button look */
.nav-btn, .nav-active {
  display: block;
  width: 100%;
  text-align: left;
  padding: .60rem .80rem;
  border-radius: 10px;
  font-size: 0.96rem;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  line-height: 1.2;
}

/* Inactive: clickable */
.nav-btn:hover { background: rgba(255,255,255,0.08); }

/* Active: highlighted, not clickable */
.nav-active {
  background: rgba(124,58,237,0.18);
  /* draw the left accent without changing layout */
  box-shadow: inset 4px 0 0 0 #7c3aed;
  padding: .60rem .80rem;        /* same as .nav-btn */
  border-radius: 10px;
  font-weight: 600;
  cursor: default;
  pointer-events: none;
  text-align: center;
}

/* Slight mobile polish */
@media (max-width: 900px) {
  [data-testid="stSidebar"] {
    box-shadow: 0 0 20px rgba(0,0,0,0.35);
  }
}
</style>
""", unsafe_allow_html=True)

# =========================
# 5) Sidebar: brand + nav + settings
# =========================
with st.sidebar:
    st.title("JobHunter.AI")

    current = st.session_state["selected_page"]

    def nav_button(label: str):
        is_active = (current == label)
        if is_active:
            st.markdown(
                f'<div class="nav-item"><div class="nav-active">{label}</div></div>',
                unsafe_allow_html=True
            )
        else:
            if st.button(label, key=f"nav_{label}", use_container_width=True):
                goto(label)

    # Navigation buttons
    nav_button("Add Job")
    nav_button("Saved Jobs")
    nav_button("Profile")    
    nav_button("Prompt Settings")
    nav_button("App Settings") 

    st.divider()
    st.caption("Settings")
    dev_on = st.toggle(
        "Developer mode",
        value=st.session_state["settings"].get("developer_mode", True),
        help="Force cheapest models everywhere"
    )
    if dev_on != st.session_state["settings"].get("developer_mode", True):
        set_dev_mode(dev_on)
    st.write("🟢 Dev mode ON" if dev_on else "⚪ Dev mode OFF")

    # --- Live credit balance controls ---
    # Always fetch the latest from disk to reflect deductions done by call_gpt
    _live_settings = load_settings()
    live_balance = float(_live_settings.get("credit_balance", 0.0))

    # Compact badge at the top of Settings
    st.markdown(f"**💳 Credit balance:** ${live_balance:,.2f}")

# =========================
# 6) Main routing (original logic)
# =========================
profile = load_profile()

# Always respect the selected page
page = st.session_state["selected_page"]

# If user is on View Job but there is no job selected, bounce to Saved Jobs
if page == "View Job" and not st.session_state.get("view_job_path"):
    page = "Saved Jobs"

if page == "Add Job":
    add_job(profile)

elif page == "Saved Jobs":
    jobs = load_saved_jobs()
    show_job_cards(jobs)

elif page == "Profile":
    show_profile_page(profile)

elif page == "Prompt Settings":
    show_prompt_editor()

elif page == "App Settings":
    show_settings_editor()

elif page == "View Job":
    show_view_job(profile)
