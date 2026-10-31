import streamlit as st


def render_settings() -> None:
    st.title("Settings")
    st.caption("Manage regulatory source configuration and workspace preferences.")
    st.subheader("Regulatory source coverage")
    sources = [
        ("India", "Reserve Bank of India", "Planned"),
        ("UAE", "Central Bank of the UAE", "Planned"),
        ("Saudi Arabia", "Saudi Central Bank (SAMA)", "Planned"),
        ("Africa", "Selected central bank / financial regulator", "To configure"),
    ]
    for region, authority, status in sources:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            c1.write(f"**{region}**")
            c2.write(authority)
            c3.caption(status)
    st.subheader("Monitoring preferences")
    st.selectbox("Monitoring frequency", ["Manual only", "Every 6 hours", "Daily", "Weekly"], index=0)
    st.button("Save preferences", disabled=True, help="Configuration persistence will be added with the backend.")
    st.subheader("Workspace configuration")
    st.write("Authentication, database connectivity, document storage and Gemini settings will be introduced in subsequent iterations.")
