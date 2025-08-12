import streamlit as st
import json
import os
import markdown2
import hashlib
from services.google_docs_utils import create_google_doc_from_html
from services.cover_letter_agent.generate_cover_letter import generate_cover_letter as cl_generate
from services.resume_agent.generate_resume import generate_resume as res_generate
from services.sheets_tracker import log_application
from streamlit_quill import st_quill
from services.skill_matching_agent.score_job_fit import score_job_fit
from utils.config.config import GOOGLE_DRIVE_FOLDERS, SHEETS_URL
from datetime import datetime

def _band_label(v: float) -> str:
    try:
        v = float(v)
    except Exception:
        return ""
    if v >= 85: return "Strong match"
    if v >= 70: return "Good match"
    if v >= 55: return "Moderate match"
    return "Stretch"

def _pct(v):
    return f"{float(v):.1f}%"

def save_job_json(job: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

def clear_job_session_state():
    for key in [
        "view_cl",
        "view_res",
        "cover_letter_url",
        "resume_url",
        "last_viewed_job"
    ]:
        st.session_state.pop(key, None)

def _stable_key(prefix: str, text: str) -> str:
    return f"{prefix}_{hashlib.md5(text.encode('utf-8')).hexdigest()[:10]}"

def show_view_job(profile: dict):
    col1, col2 = st.columns([0.6, 7.4])
    with col1:
        if st.button("← Back", key="back_to_feed_top"):
            clear_job_session_state()
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Saved Jobs"
            st.rerun()
    with col2:
        st.header("🔎 View Job Details")


    path = st.session_state.get("view_job_path")
    if not path or not os.path.exists(path):
        st.warning("No job selected. Go back to Saved Jobs to pick one.")
        if st.button("← Back"):
            clear_job_session_state()
            st.session_state.pop("view_job_path", None)
            st.session_state["selected_page"] = "Saved Jobs"  # manually set next page
            st.rerun()
        return

    # Clear session state if viewing a different job than before
    if st.session_state.get("last_viewed_job") != path:
        clear_job_session_state()
        st.session_state["last_viewed_job"] = path

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
        "Notes": job.get("notes", "—"),
        "Date Added": job.get("date_added", "—"),
        "Date Applied": job.get("date_applied", "—"),
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

    # --- Profile Match Details ---
    match = job.get("match", {})

    st.markdown("### 🤝 Profile Match Details")

    if not match:
        st.info("No match data available. Try re-running the skill matching agent.")
    else:
        scores = match.get("scores", {})
        skill_v   = scores.get("skill_score", 0)
        pref_v    = scores.get("preference_score", 0)
        overall_v = scores.get("overall_score", 0)

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Skill Score",
            _pct(skill_v),
            help="How well your skills and qualifications match the posting. Weighted average: Required 60%, Nice‑to‑Have 20%, Qualifications 20%. Sections missing in the job post are ignored rather than penalized."
        )
        col2.metric(
            "Preference Score",
            _pct(pref_v),
            help="Starts at 100 and subtracts only for explicit conflicts: location, work mode, salary. Unknown data is neutral and does not reduce the score."
        )
        col3.metric(
            f"Overall Score · {_band_label(overall_v)}",
            _pct(overall_v),
            help="Final blend: 70% Skill + 20% Preferences + 10% Responsibilities bonus (based on coverage confidence). Capped at 100."
        )

        with st.expander("ℹ️ How this score works", expanded=False):
            skills_data = match.get("fit", {}).get("skills", {})
            req = skills_data.get("required", {}) or {}
            nice = skills_data.get("nice_to_have", {}) or {}
            quals = match.get("fit", {}).get("qualifications", {}) or {}
            resp  = match.get("fit", {}).get("responsibilities", {}) or {}
            prefs = match.get("preferences", {}) or {}

            req_m, req_x = len(req.get("matched", []) or []), len(req.get("missing", []) or [])
            nice_m, nice_x = len(nice.get("matched", []) or []), len(nice.get("missing", []) or [])
            qual_m, qual_x = len(quals.get("matched", []) or []), len(quals.get("missing", []) or [])
            total_req  = req_m + req_x
            total_nice = nice_m + nice_x
            total_qual = qual_m + qual_x

            st.markdown(
                "- **Skill score** is a weighted average of match ratios:\n"
                "  - Required 60%  •  Nice‑to‑Have 20%  •  Qualifications 20%\n"
                "  - Empty sections in the posting are ignored instead of counted as zero.\n"
                "- **Preference score** starts at 100 and subtracts only for clear conflicts:\n"
                "  - Location, work mode, salary. Unknown stays neutral.\n"
                "- **Responsibilities bonus** comes from coverage confidence (0–100) and contributes a small bonus inside the overall blend.\n"
                "- **Overall** = 70% Skill + 20% Preferences + 10% (Skill + responsibilities bonus), then capped at 100."
            )

            st.markdown("**Your counts**")
            st.markdown(
                f"- Required: {req_m} matched / {req_x} missing"
                + ("" if total_req else " _(section not present in posting)_")
            )
            st.markdown(
                f"- Nice‑to‑Have: {nice_m} matched / {nice_x} missing"
                + ("" if total_nice else " _(section not present in posting)_")
            )
            st.markdown(
                f"- Qualifications: {qual_m} matched / {qual_x} missing"
                + ("" if total_qual else " _(section not present in posting)_")
            )

            conf = resp.get("confidence", 0) or 0
            st.markdown(f"- Responsibilities coverage confidence: **{conf}%**")

            # Preference details
            loc_ok  = prefs.get("location_ok",  None)
            mode_ok = prefs.get("work_mode_ok", None)
            sal_ok  = prefs.get("salary_ok",    "unknown")
            st.markdown("**Preference checks**")
            st.markdown(f"- Location OK: **{loc_ok}**")
            st.markdown(f"- Work mode OK: **{mode_ok}**")
            st.markdown(f"- Salary OK: **{sal_ok}**")

        # --- Required Skills ---
        st.subheader("Required Skills")
        req_skills = match.get("fit", {}).get("skills", {}).get("required", {})
        col1, col2 = st.columns(2)
        col1.markdown("✅ Matched")
        col1.markdown("\n".join(f"- {s}" for s in req_skills.get("matched", [])) or "_None_")
        col2.markdown("❌ Missing")
        col2.markdown("\n".join(f"- {s}" for s in req_skills.get("missing", [])) or "_None_")

        # --- Nice-to-Have Skills ---
        st.subheader("Nice-to-Have Skills")
        nice_skills = match.get("fit", {}).get("skills", {}).get("nice_to_have", {})
        col1, col2 = st.columns(2)
        col1.markdown("✅ Matched")
        col1.markdown("\n".join(f"- {s}" for s in nice_skills.get("matched", [])) or "_None_")
        col2.markdown("❌ Missing")
        col2.markdown("\n".join(f"- {s}" for s in nice_skills.get("missing", [])) or "_None_")

        # --- Qualifications ---
        st.subheader("Qualifications")
        quals = match.get("fit", {}).get("qualifications", {})
        col1, col2 = st.columns(2)
        col1.markdown("✅ Matched")
        col1.markdown("\n".join(f"- {q}" for q in quals.get("matched", [])) or "_None_")
        col2.markdown("❌ Missing")
        col2.markdown("\n".join(f"- {q}" for q in quals.get("missing", [])) or "_None_")

        # Calculate ratio for display
        total_qual = len(quals.get("matched", []) or []) + len(quals.get("missing", []) or [])
        qual_ratio = (len(quals.get("matched", [])) / total_qual * 100) if total_qual else None

        if qual_ratio is not None:
            st.metric(
                "Qualifications Match Ratio",
                f"{qual_ratio:.1f}%",
                help="The percentage of qualifications from the posting that match your profile. "
                    "Empty sections are ignored rather than counted as zero. "
                    "This ratio is also factored into the overall Skill Score."
            )
        else:
            st.caption("_No qualifications listed in the job posting — this section does not affect the score._")

        # --- Add missing to Profile (AI-normalized) ---
        PROFILE_PATH = "data/profile.json"

        def _load_profile():
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        def _save_profile(p):
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(p, f, indent=2, ensure_ascii=False)

        def _sig(obj: dict) -> str:
            j = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
            return hashlib.md5(j).hexdigest()

        with st.expander("➕ Add missing to Profile", expanded=False):
            # Collect both required and nice-to-have missing skills
            skills_data = match.get("fit", {}).get("skills", {})
            req_missing  = skills_data.get("required", {}).get("missing", []) or []
            nice_missing = skills_data.get("nice_to_have", {}).get("missing", []) or []
            all_missing_skills = sorted({*req_missing, *nice_missing})

            # Missing qualifications
            quals_data = match.get("fit", {}).get("qualifications", {})
            quals_missing = sorted(set(quals_data.get("missing", []) or []))

            st.caption("Select items you actually have. We will clean names with gpt‑5‑nano and only add new entries.")
            st.markdown("**Missing Skills**")
            pick_skills = {s: st.checkbox(s, key=_stable_key("pick_skill", s)) for s in all_missing_skills}

            st.markdown("**Missing Qualifications**")
            pick_quals  = {q: st.checkbox(q, key=_stable_key("pick_qual", q)) for q in quals_missing}

            chosen_skills = [s for s, on in pick_skills.items() if on]
            chosen_quals  = [q for q, on in pick_quals.items() if on]

            if st.button("Preview additions", key="preview_add"):
                from utils.ai.normalizer import normalize_skills_with_nano, normalize_quals_with_nano

                # Show quick debug counts so you can see selections pre‑normalization
                st.caption(f"Selected skills: {len(chosen_skills)} · Selected quals: {len(chosen_quals)}")

                # Run normalizers
                try:
                    skill_pairs = normalize_skills_with_nano(chosen_skills) if chosen_skills else []
                except Exception as e:
                    st.info(f"Skill normalizer error: {e} — using raw values.")
                    skill_pairs = []

                try:
                    qual_pairs  = normalize_quals_with_nano(chosen_quals) if chosen_quals else []
                except Exception as e:
                    st.info(f"Qualification normalizer error: {e} — using raw values.")
                    qual_pairs = []

                # Fallback: if user selected items but normalizer returned nothing, pass through raw
                if chosen_skills and not skill_pairs:
                    skill_pairs = [{"raw": s, "normalized": s.strip()} for s in chosen_skills]
                    st.caption("Normalizer returned no skills. Using raw values.")

                if chosen_quals and not qual_pairs:
                    qual_pairs = [{"raw": q, "normalized": q.strip()} for q in chosen_quals]
                    st.caption("Normalizer returned no qualifications. Using raw values.")

                st.session_state["pending_skill_pairs"] = skill_pairs
                st.session_state["pending_qual_pairs"]  = qual_pairs

                if skill_pairs:
                    st.markdown("#### Skills to add")
                    for p in skill_pairs:
                        st.markdown(f"- {p['raw']} → **{p['normalized']}**")
                else:
                    st.info("No skills selected or nothing valid after normalization.")

                if qual_pairs:
                    st.markdown("#### Qualifications to add")
                    for p in qual_pairs:
                        st.markdown(f"- {p['raw']} → **{p['normalized']}**")
                else:
                    st.info("No qualifications selected or nothing valid after normalization.")

            st.markdown("---")
            # Toggle to hint scorer to use cheaper model
            use_cheap = st.checkbox(
                "Use cheaper model on re‑score and analysis (gpt-5 → gpt‑5‑mini)",
                value=False,
                help="When on, we hint the scorer to use your 'analysis_mini' task which maps to gpt‑5‑mini in settings."
            )

            if st.button("Confirm & Save, then Re‑score", key="confirm_add"):
                pending_skill_pairs = st.session_state.get("pending_skill_pairs", [])
                pending_qual_pairs  = st.session_state.get("pending_qual_pairs", [])

                if not pending_skill_pairs and not pending_qual_pairs:
                    st.warning("Nothing to add. Click Preview first.")
                else:
                    # Load latest profile and capture signature
                    latest = _load_profile()
                    old_sig = _sig({"skills": latest.get("skills", []), "qual": latest.get("qualifications", [])})

                    # Add-only updates
                    skill_set = set(latest.get("skills", []) or [])
                    for p in pending_skill_pairs:
                        skill_set.add(p["normalized"])
                    latest["skills"] = sorted(skill_set)

                    qual_list = set((latest.get("qualifications") or []))
                    for p in pending_qual_pairs:
                        qual_list.add(p["normalized"])
                    latest["qualifications"] = sorted(qual_list)

                    _save_profile(latest)

                    # keep in-memory profile fresh
                    profile.clear()
                    profile.update(latest)

                    new_sig = _sig({"skills": latest.get("skills", []), "qual": latest.get("qualifications", [])})

                    st.success("Profile updated.")

                    # Auto re-score only if signature changed
                    if old_sig != new_sig:
                        print(f"🤖 [SkillMatch] Re-scoring due to profile update for job '{job.get('job_title')}' at {job.get('company')}")
                        with st.spinner("Re-scoring match with updated profile..."):
                            try:
                                # Hint cheaper model without changing function signature
                                if use_cheap:
                                    os.environ["JOBHUNTER_MODEL_HINT"] = "analysis_mini"
                                try:
                                    updated_match = score_job_fit(job, latest)
                                finally:
                                    # Always clean up the hint
                                    if use_cheap:
                                        os.environ.pop("JOBHUNTER_MODEL_HINT", None)

                                if updated_match:
                                    job["match"] = updated_match
                                    save_job_json(job, path)
                                    st.success("Re-scored with updated profile.")
                                    st.rerun()
                                else:
                                    st.info("Saved profile. Re-score skipped: scorer returned no data.")
                            except Exception as e:
                                st.info(f"Saved profile. Re-score skipped: {e}")
                    else:
                        st.info("Profile unchanged. Re-score not needed.")


        # --- Responsibilities evidence ---
        st.subheader("Responsibilities Evidence")
        resp_data = match.get("fit", {}).get("responsibilities", {})
        confidence = resp_data.get("confidence", 0)
        st.markdown(f"**Coverage Confidence:** {confidence}%")
        for r in resp_data.get("evidence", []):
            st.markdown(f"- **{r.get('resp', '')}** → _{r.get('evidence', '')}_")

        # --- Analysis ---
        st.subheader("Analysis")
        analysis = match.get("analysis", {})
        st.markdown("**Strengths**")
        st.markdown("\n".join(f"- {s}" for s in analysis.get("strengths", [])) or "_None_")
        st.markdown("**Gaps**")
        st.markdown("\n".join(f"- {g}" for g in analysis.get("gaps", [])) or "_None_")
        st.markdown("**Fast Upskill Suggestions**")
        st.markdown("\n".join(f"- {u}" for u in analysis.get("fast_upskill_suggestions", [])) or "_None_")

        # --- Doc recommendations ---
        st.subheader("Document Recommendations")
        doc_recs = match.get("doc_recommendations", {})
        cl_recs = doc_recs.get("cover_letter", {})
        res_recs = doc_recs.get("resume", {})

        with st.expander("📄 Cover Letter Recommendations", expanded=False):
            st.markdown("**Highlights**")
            st.markdown("\n".join(f"- {h}" for h in cl_recs.get("highlights", [])) or "_None_")
            st.markdown("**Address Gaps**")
            st.markdown("\n".join(f"- {a}" for a in cl_recs.get("address_gaps", [])) or "_None_")
            st.markdown(f"**Tone:** {cl_recs.get('tone', 'N/A')}")

        with st.expander("📄 Resume Recommendations", expanded=False):
            st.markdown("**Reorder Suggestions**")
            st.markdown("\n".join(f"- {r}" for r in res_recs.get("reorder_suggestions", [])) or "_None_")
            st.markdown("**Keywords to Include**")
            st.markdown("\n".join(f"- {k}" for k in res_recs.get("keywords_to_include", [])) or "_None_")
            st.markdown("**Bullets to Add**")
            st.markdown("\n".join(f"- {b}" for b in res_recs.get("bullets_to_add", [])) or "_None_")

    # --- Generate or View Application Documents ---
    st.markdown("### ✨ Application Documents")
    col1, col2 = st.columns([1,1])

    with col1:
        cl_url = job.get("cover_letter_url") or st.session_state.get("cover_letter_url")
        if cl_url:
            #  show “view” link
            st.markdown(f"[📄 View Cover Letter ↗]({cl_url})")
            #  Regenerate logic
            if st.button("🔄 Regenerate Cover Letter", key="regen_cl"):
                with st.spinner("Regenerating cover letter..."):
                    cl = cl_generate(job, profile)
                    st.session_state["view_cl"] = cl
                    job.pop("cover_letter_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Cover Letter", key="gen_cl"):
                with st.spinner("Generating cover letter..."):
                    cl = cl_generate(job, profile)
                    st.session_state["view_cl"] = cl

    # Resume column
    with col2:
        res_url = job.get("resume_url") or st.session_state.get("resume_url")
        if res_url:
            st.markdown(f"[📄 View Resume ↗]({res_url})")
            if st.button("🔄 Regenerate Resume", key="regen_res"):
                with st.spinner("Regenerating resume..."):
                    res = res_generate(job, profile)
                    st.session_state["view_res"] = res
                    job.pop("resume_url", None)
                    save_job_json(job, path)
        else:
            if st.button("✍️ Generate Resume", key="gen_res"):
                with st.spinner("Generating resume..."):
                    res = res_generate(job, profile)
                    st.session_state["view_res"] = res

    # --- Cover Letter Editor ---
    if st.session_state.get("view_cl"):
        with st.expander("📝 Edit Cover Letter", expanded=True):
            # Convert Markdown → HTML before rendering
            html_cl = markdown2.markdown(st.session_state["view_cl"])
            edited_cl = st_quill(html_cl, html=True, key="view_quill_cl")
            if st.button("📄 Export to Google Docs", key="export_cl"):
                with st.spinner("Exporting to Google Docs..."):
                    company = job.get("company", "UnknownCompany")
                    job_title = job.get("job_title", "UnknownJob")
                    doc_title = f"{company}_{job_title}_Cover_Letter"
                try:
                    cover_letter_folder_id = GOOGLE_DRIVE_FOLDERS["cover_letters"]
                    cl_url = create_google_doc_from_html(edited_cl, doc_title, folder_id=cover_letter_folder_id)
                    # save url to job JSON
                    job["cover_letter_url"] = cl_url
                    save_job_json(job, path)
                    st.session_state["cover_letter_url"] = cl_url
                    st.success(f"✅ [Click here to open in Google Docs ↗]({cl_url})")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    # --- Resume Editor ---
    if st.session_state.get("view_res"):
        with st.expander("📝 Edit Resume", expanded=True):
            # Convert Markdown → HTML before rendering
            html_res = markdown2.markdown(st.session_state["view_res"])
            edited_res = st_quill(html_res, html=True, key="view_quill_res")
            if st.button("📄 Export to Google Docs", key="export_res"):
                with st.spinner("Exporting resume to Google Docs..."):
                    company = job.get("company", "UnknownCompany")
                    job_title = job.get("job_title", "UnknownJob")
                    doc_title = f"{company}_{job_title}_Resume"
                try:
                    resume_folder_id = GOOGLE_DRIVE_FOLDERS["resumes"]
                    res_url = create_google_doc_from_html(edited_res, doc_title, folder_id=resume_folder_id)
                    # Save URL to job JSON
                    job["resume_url"] = res_url
                    save_job_json(job, path)
                    st.session_state["resume_url"] = res_url
                    st.success(f"✅ [Click here to open in Google Docs ↗]({res_url})")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    # --- Log to Google Sheets & mark as applied ---
    if job.get("sheets_logged"):
        st.success("✅ Already logged to Google Sheets for this job.")
        # Show a link button and a plain link for redundancy
        st.link_button("↗ Open in Google Sheets", SHEETS_URL, help="Open your application tracker")
    else:
        if st.button("➕ Add to Google Sheets", key="add_to_sheets"):
            with st.spinner("Logging application to Google Sheets..."):
                cl_url = st.session_state.get("cover_letter_url", "")
                res_url = st.session_state.get("resume_url", "")

                # Log to Sheets
                log_application(
                    job.get("job_title", ""),
                    job.get("company", ""),
                    job.get("url", ""),
                    resume_path=res_url,
                    cover_letter_path=cl_url,
                    status="Applied"
                )

                # Save a simple flag and the global sheet link
                job["sheets_logged"] = True
                job["date_applied"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_job_json(job, path)

                st.success(f"✅ Logged and marked as applied on {job['date_applied']}")
                st.link_button("↗ Open in Google Sheets", SHEETS_URL)

    if st.button("← Back to Saved Jobs"):
        clear_job_session_state()
        st.session_state.pop("view_job_path", None)
        st.session_state["selected_page"] = "Saved Jobs"
        st.rerun()
