import streamlit as st

def show_profile(profile):
    with st.sidebar:
        st.header("👤 Your Profile")
        st.markdown(f"**Name:** {profile['name']}")
        st.markdown(f"**Title:** {profile['title']}")
        st.markdown(f"**Location:** {profile['location']}")
        st.markdown("**Skills:**")
        for skill in profile["skills"]:
            st.markdown(f"- {skill}")
        st.markdown("**Preferences:**")
        for key, value in profile["preferences"].items():
            st.markdown(f"- {key.capitalize()}: {value}")
