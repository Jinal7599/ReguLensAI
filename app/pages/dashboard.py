import pandas as pd
import streamlit as st


def render_dashboard(publications: list[dict]) -> None:
    st.markdown('<div class="hero"><h1>Regulatory intelligence, made actionable.</h1><p>Monitor regulatory developments, understand obligations and review potential business impact across regions.</p></div>', unsafe_allow_html=True)
    st.subheader("Your regulatory overview")
    st.caption("Illustrative dashboard metrics based on bundled synthetic demo records.")
    cols = st.columns(4)
    metrics = [
        ("Publications", len(publications)),
        ("New / changed", sum(p["status"] in {"New", "Awaiting review", "Relationship unresolved"} for p in publications)),
        ("Awaiting review", sum(p["status"] == "Awaiting review" for p in publications)),
        ("Regions represented", len({p["country"] for p in publications})),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Recent regulatory developments")
        df = pd.DataFrame(publications)[["title", "authority", "country", "published", "status"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Coverage by region")
        counts = pd.DataFrame(publications).groupby("country").size().rename("Publications")
        st.bar_chart(counts, horizontal=True, color="#356a9a")
        st.info("Connect official source feeds in a later iteration. Current records are synthetic and do not represent real regulatory publications.")
