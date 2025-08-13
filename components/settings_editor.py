# components/settings_editor.py
import json
import os
import tempfile
from typing import Any, Dict, List
import streamlit as st
from utils.config.settings import load_settings, save_settings  # reuse your existing helpers

# ---------- Small UI helpers ----------
def _inject_css():
    st.markdown(
        """
        <style>
          .kv { display:grid; grid-template-columns: 180px 1fr; gap:.4rem .8rem; }
          .kv div:nth-child(odd){ font-weight:600; opacity:.9; }
          .kv div:nth-child(even){ opacity:.95; }
          .pill { display:inline-block; padding:.25rem .6rem; border-radius:999px; font-weight:600; font-size:.85rem; }
          .pill-ok { background:rgba(16,185,129,.15); color:#10b981; }
          .pill-warn { background:rgba(234,179,8,.15); color:#eab308; }
          .pill-muted { background:rgba(148,163,184,.18); color:#94a3b8; }
          .big { font-size:1.25rem; font-weight:700; }
          .subtle { opacity:.8; }
          .section-title { font-weight:700; margin-bottom:.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _pretty_json(d: Dict[str, Any]) -> str:
    return json.dumps(d, indent=2, ensure_ascii=False)

def _basic_settings_checks(d: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if "developer_mode" in d and not isinstance(d["developer_mode"], bool):
        errs.append("`developer_mode` should be a boolean.")
    if "credit_balance" in d and not isinstance(d["credit_balance"], (int, float)):
        errs.append("`credit_balance` should be a number.")

    pm = d.get("preferred_models")
    if pm is not None:
        if not isinstance(pm, dict):
            errs.append("`preferred_models` should be an object mapping task -> model name.")
        else:
            for k in ["extract","summarize","cover_letter","resume","cheap_fallback","review_extracted_job","analysis","analysis_mini","clean_job_text", "skill_match"]:
                if k in pm and not isinstance(pm[k], str):
                    errs.append(f"`preferred_models.{k}` should be a string (model name).")
    return errs

# ---------- Main ----------
def show_settings_editor():
    st.header("🛠️ App Settings")
    _inject_css()

    # Always reload live settings so View reflects current state
    s = load_settings()
    st.caption("Control models, developer mode, credit balance, and other app flags.")

    tab_view, tab_edit = st.tabs(["View", "Edit JSON"])

    # ===== View (prettier) =====
    with tab_view:
        top = st.columns([2, 2, 2, 3])

        # Developer mode badge
        with top[0]:
            dev = bool(s.get("developer_mode", False))
            st.markdown("**Developer Mode**")
            st.markdown(
                f"<span class='pill {'pill-ok' if dev else 'pill-muted'}'>{'ON' if dev else 'OFF'}</span>",
                unsafe_allow_html=True,
            )
            st.caption("Forces cheaper models and extra debug output.")

        # Credit balance big number
        with top[1]:
            bal = float(s.get("credit_balance", 0.0)) if isinstance(s.get("credit_balance", 0.0), (int,float)) else 0.0
            st.markdown("**Credit Balance**")
            st.markdown(f"<div class='big'>${bal:,.2f}</div>", unsafe_allow_html=True)
            st.caption("Updated after each API call.")

        # Model count
        with top[2]:
            pm = s.get("preferred_models", {}) or {}
            st.markdown("**Preferred Models**")
            st.markdown(f"<div class='big'>{len(pm)} tasks</div>", unsafe_allow_html=True)
            st.caption("Tasks mapped to model names.")

        # File info
        with top[3]:
            st.markdown("**File**")
            st.markdown(
                "<div class='kv'>"
                "<div>Path</div><div>settings.json</div>"
                "<div>Backup</div><div>settings.backup.json (auto)</div>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown("<div class='section-title'>Preferred Models</div>", unsafe_allow_html=True)
        pm = s.get("preferred_models", {}) or {}

        if not pm:
            st.info("No preferred models configured.")
        else:
            # Build a simple table
            rows = [{"Task": k, "Model": v} for k, v in pm.items()]
            # Keep tasks sorted for readability
            rows = sorted(rows, key=lambda r: r["Task"])
            st.table(rows)

        st.divider()
        with st.expander("Raw JSON"):
            st.json(s, expanded=False)

    # ===== Edit JSON (your original logic) =====
    with tab_edit:
        st.caption("Edit the raw settings JSON. Validates before saving.")

        if "settings_json_buffer" not in st.session_state:
            st.session_state["settings_json_buffer"] = _pretty_json(s)

        edited = st.text_area(
            "Settings JSON",
            key="settings_json_buffer",
            height=360,
            help="Paste or edit JSON. Use Validate to catch format errors."
        )

        # Save
        if st.button("Save"):
            try:
                parsed = json.loads(edited)  # syntax validation
            except json.JSONDecodeError as e:
                st.error(f"Cannot save. Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}")
            else:
                errs = _basic_settings_checks(parsed)  # semantic validation
                if errs:
                    st.error("Fix these before saving:\n\n- " + "\n- ".join(errs))
                else:
                    try:
                        # Use the same mechanism the rest of the app uses
                        save_settings(parsed)
                        # keep session in sync and refresh
                        st.session_state["settings"] = parsed
                        st.success("Settings saved.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to save: {ex}")

        st.divider()
        if st.button("Reload from disk"):
            fresh = load_settings()
            st.session_state["settings_json_buffer"] = _pretty_json(fresh)
            st.success("Reloaded latest settings.")
