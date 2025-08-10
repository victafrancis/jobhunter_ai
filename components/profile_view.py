import streamlit as st
from datetime import datetime
from typing import List, Dict, Any

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

# ---------- Main renderer ----------
def show_profile_page(profile: Dict[str, Any]):
    st.header("👤 Profile")

    chip_css()

    # Top identity block
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"### {profile.get('name','Your Name')}")
            st.write(profile.get("title", "—"))
            st.write(profile.get("location", "—"))
            # Contact links
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
            # Availability badges
            st.markdown("**Work Preferences**")
            st.markdown(
                f"""
                <div class="section-pad">
                  <span class="badge {'green' if remote else 'red'}">Remote</span>
                  <span class="badge {'yellow' if hybrid else 'red'}">Hybrid</span>
                  <span class="badge {'green' if onsite else 'red'}">Onsite</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Preferred titles and locations
            if prefs.get("job_titles"):
                st.markdown("**Target Titles**")
                chips(prefs["job_titles"])
            if prefs.get("work_locations"):
                st.markdown("**Preferred Locations**")
                chips(prefs["work_locations"])

    # Summary and traits
    cols = st.columns([2, 1])
    with cols[0]:
        with st.container(border=True):
            st.subheader("Summary")
            st.write(profile.get("summary", "—"))
    with cols[1]:
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

    # Experience timeline
    with st.container(border=True):
        st.subheader("Work Experience")
        exp = profile.get("work_experience", [])
        if not exp:
            st.write("_No work experience added yet_")
        else:
            for i, job in enumerate(exp):
                pos = job.get("position", "—")
                company = job.get("company", "—")
                loc = job.get("location", "—")
                start = ym_to_pretty(job.get("start_date"))
                end = ym_to_pretty(job.get("end_date")) if job.get("end_date") else "Present"

                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{pos}</div>', unsafe_allow_html=True)
                    st.markdown(f"{company} • {loc} · {start} — {end}")
                    # Responsibilities and achievements side by side
                    r_cols = st.columns(2)
                    with r_cols[0]:
                        st.markdown("**Responsibilities**")
                        resp = job.get("responsibilities", [])
                        if resp:
                            st.markdown("\n".join([f"- {r}" for r in resp]))
                        else:
                            st.write("_None_")
                    with r_cols[1]:
                        st.markdown("**Achievements**")
                        ach = job.get("achievements", [])
                        if ach:
                            st.markdown("\n".join([f"- {a}" for a in ach]))
                        else:
                            st.write("_None_")

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

    st.caption("Next: add inline editing and a Save button to write back into profile.json")
