# components/profile_view.py
import json
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st

# ---------- Small helpers ----------
def ym_to_pretty(s: str | None) -> str:
    if not s or "-" not in s:
        return "—"
    try:
        dt = datetime.strptime(s, "%Y-%m")
        return dt.strftime("%b %Y")
    except Exception:
        return s

def chip_css():
    st.markdown(
        """
        <style>
        .chips { display:flex; flex-wrap:wrap; gap:.4rem; }
        .chip {
            padding:.25rem .55rem;
            border-radius:999px;
            border:1px solid rgba(255,255,255,.15);
            font-size:.85rem;
            line-height:1.2;
            background:rgba(127,127,127,.12);
            backdrop-filter: blur(2px);
        }
        .badge {
            display:inline-block;
            padding:.2rem .5rem;
            border-radius:999px;
            font-size:.8rem;
            font-weight:600;
        }
        .green { background:rgba(16,185,129,.15); color:#10b981; }
        .yellow { background:rgba(234,179,8,.15); color:#eab308; }
        .red { background:rgba(239,68,68,.15); color:#ef4444; }
        .card-title { font-weight:700; font-size:1.05rem; margin-bottom:.25rem; }
        .muted { opacity:.8; font-size:.9rem; }
        .kv { display:grid; grid-template-columns: 160px 1fr; gap:.35rem .75rem; }
        .kv div:nth-child(odd){ font-weight:600; opacity:.85; }
        .kv div:nth-child(even){ opacity:.9; }
        .section-pad { padding-top:.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def chips(items: List[str]) -> None:
    if not items:
        st.write("_None_")
        return
    st.markdown(
        '<div class="chips">' + "".join([f'<span class="chip">{st.session_state.get("chip_prefix","")}{i}</span>' for i in items]) + "</div>",
        unsafe_allow_html=True,
    )

def kv_row(label: str, value: str | Any) -> None:
    st.markdown(
        f"""
        <div class="kv">
          <div>{label}</div>
          <div>{value if value not in (None, "") else "—"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- IO helpers ----------
PROFILE_PATH = "data/profile.json"

def save_profile(data: Dict[str, Any], path: str = PROFILE_PATH) -> None:
    """Simple writer to keep consistent with the rest of the app."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def pretty_json(d: Dict[str, Any]) -> str:
    return json.dumps(d, indent=2, ensure_ascii=False)

def basic_shape_checks(d: Dict[str, Any]) -> list[str]:
    """Lightweight guardrails. Add more as you formalize profile.json."""
    errs = []
    if "skills" in d and not isinstance(d["skills"], list):
        errs.append("`skills` should be a list of strings.")
    if "traits" in d and not isinstance(d["traits"], list):
        errs.append("`traits` should be a list of strings.")
    if "qualifications" in d and not isinstance(d["qualifications"], list):
        errs.append("`qualifications` should be a list of strings.")
    if "work_experience" in d and not isinstance(d["work_experience"], list):
        errs.append("`work_experience` should be a list of objects.")
    if "education" in d and not isinstance(d["education"], list):
        errs.append("`education` should be a list of objects.")
    if "projects" in d and not isinstance(d["projects"], list):
        errs.append("`projects` should be a list of objects.")
    return errs

# ---------- Display-only renderer ----------
def render_profile_view(profile: Dict[str, Any]):
    chip_css()
    # Top
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"### {profile.get('name','Your Name')}")
            st.write(profile.get("title", "—"))
            st.write(profile.get("location", "—"))
            contact = profile.get("contact", {})
            links = []
            if contact.get("email"):
                links.append(f"[Email](mailto:{contact['email']})")
            if contact.get("phone"):
                links.append(f"Tel: {contact['phone']}")
            if contact.get("linkedin"):
                links.append(f"[LinkedIn]({contact['linkedin']})")
            if contact.get("github"):
                links.append(f"[GitHub]({contact['github']})")
            if contact.get("website"):
                links.append(f"[Website]({contact['website']})")
            if links:
                st.markdown(" • ".join(links))
        with right:
            prefs = profile.get("preferences", {})
            remote = prefs.get("remote", False)
            hybrid = prefs.get("hybrid", False)
            onsite = prefs.get("onsite", False)
            st.markdown("**Work Preferences**")
            st.markdown(
                f"""
                <div class="section-pad">
                  <span class="badge {'green' if remote else 'red'}">Remote</span>
                  <span class="badge {'green' if hybrid else 'red'}">Hybrid</span>
                  <span class="badge {'green' if onsite else 'red'}">Onsite</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if prefs.get("job_titles"):
                st.markdown("**Target Titles**")
                chips(prefs["job_titles"])
            if prefs.get("work_locations"):
                st.markdown("**Preferred Locations**")
                chips(prefs["work_locations"])
            if prefs.get("work_preferences"):
                st.markdown("**Work Preferences**")
                chips(prefs["work_preferences"])

    # Summary
    with st.container(border=True):
        st.subheader("Summary")
        st.write(profile.get("summary", "—"))

    # Traits
    with st.container(border=True):
        st.subheader("Traits")
        traits = profile.get("traits", [])
        if traits:
            st.markdown("\n".join([f"- {t}" for t in traits]))
        else:
            st.write("_None_")

    # Skills
    with st.container(border=True):
        st.subheader("Skills")
        chips(profile.get("skills", []))

    # Qualifications
    with st.container(border=True):
        st.subheader("Qualifications")
        quals = profile.get("qualifications", [])
        if not quals:
            st.write("_None_")
        else:
            st.markdown("\n".join([f"- {q}" for q in quals]))

    # Work Experience
    with st.container(border=True):
        st.subheader("Work Experience")
        exp = profile.get("work_experience", [])
        if not exp:
            st.write("_No work experience added yet_")
        else:
            for job in exp:
                pos = job.get("position", "—")
                company = job.get("company", "—")
                loc = job.get("location", "—")
                start = ym_to_pretty(job.get("start_date"))
                end = ym_to_pretty(job.get("end_date")) if job.get("end_date") else "Present"
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{pos}</div>', unsafe_allow_html=True)
                    st.markdown(f"{company} • {loc} · {start} — {end}")
                    r_cols = st.columns(2)
                    with r_cols[0]:
                        st.markdown("**Responsibilities**")
                        resp = job.get("responsibilities", [])
                        st.markdown("\n".join([f"- {r}" for r in resp]) or "_None_")
                    with r_cols[1]:
                        st.markdown("**Achievements**")
                        ach = job.get("achievements", [])
                        st.markdown("\n".join([f"- {a}" for a in ach]) or "_None_")

    # Education
    with st.container(border=True):
        st.subheader("Education")
        edu = profile.get("education", [])
        if not edu:
            st.write("_No education added yet_")
        else:
            for e in edu:
                deg = e.get("degree", "—")
                inst = e.get("institution", "—")
                loc = e.get("location", "—")
                start = ym_to_pretty(e.get("start_date"))
                end = ym_to_pretty(e.get("end_date"))
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{deg}</div>', unsafe_allow_html=True)
                    st.markdown(f"{inst} • {loc} · {start} — {end}")
                    if e.get("details"):
                        st.markdown(f"<span class='muted'>{e['details']}</span>", unsafe_allow_html=True)

    # Projects
    with st.container(border=True):
        st.subheader("Projects")
        projs = profile.get("projects", [])
        if not projs:
            st.write("_No projects added yet_")
        else:
            for p in projs:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{p.get("title","Untitled Project")}</div>', unsafe_allow_html=True)
                    st.write(p.get("description", ""))

# ---------- Main ----------
def show_profile_page(profile: Dict[str, Any]):
    st.header("👤 Profile")

    tab_view, tab_edit = st.tabs(["View", "Edit JSON"])

    with tab_view:
        render_profile_view(profile)

    with tab_edit:
        st.caption("Edit the raw profile.json. It will validate and pretty‑print on save.")

        # One‑time refresh: if we asked for a buffer refresh last run, reload from disk first
        if st.session_state.get("_profile_refresh"):
            try:
                with open("data/profile.json", "r", encoding="utf-8") as f:
                    fresh = json.load(f)
                st.session_state["profile_json_buffer"] = json.dumps(fresh, indent=2, ensure_ascii=False)
            except Exception:
                # if anything goes wrong, just keep whatever is in the buffer
                pass
            finally:
                st.session_state.pop("_profile_refresh", None)

        # Initialize editor buffer once
        if "profile_json_buffer" not in st.session_state:
            st.session_state["profile_json_buffer"] = json.dumps(profile, indent=2, ensure_ascii=False)

        edited = st.text_area(
            "Profile JSON",
            key="profile_json_buffer",
            height=420,
            help="Paste or edit JSON. Click Save to apply.",
        )

        # Single strict button: validate then save
        if st.button("Save"):
            try:
                parsed = json.loads(edited)          # syntax validation
            except json.JSONDecodeError as e:
                st.error(f"Cannot save. Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}")
            else:
                # lightweight structural checks
                errs = basic_shape_checks(parsed)
                if errs:
                    st.error("Fix these before saving:\n\n- " + "\n- ".join(errs))
                else:
                    try:
                        # write using the same simple pattern used elsewhere
                        with open("data/profile.json", "w", encoding="utf-8") as f:
                            json.dump(parsed, f, indent=2, ensure_ascii=False)

                        # request a fresh buffer next run and rerun immediately
                        st.session_state["_profile_refresh"] = True
                        st.success("Profile saved.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to save: {ex}")

        st.divider()
        st.caption("Optional: replace your profile by uploading a JSON file.")
        uploaded = st.file_uploader("Upload profile.json", type=["json"])
        if uploaded is not None:
            try:
                new_data = json.load(uploaded)
                st.session_state["profile_json_buffer"] = pretty_json(new_data)
                st.success("Loaded into editor. Validate and Save when ready.")
            except Exception as e:
                st.error(f"Failed to read uploaded file: {e}")
