import pandas as pd
import streamlit as st


def render_regulatory_feed(publications: list[dict]) -> None:
    st.title("Regulatory Feed")
    st.caption("Search and review discovered regulatory publications. The current feed contains synthetic demo records.")
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        query = st.text_input("Search publications", placeholder="Search title, authority or reference")
    with c2:
        countries = ["All"] + sorted({p["country"] for p in publications})
        country = st.selectbox("Region", countries)
    with c3:
        statuses = ["All"] + sorted({p["status"] for p in publications})
        status = st.selectbox("Review status", statuses)
    filtered = publications
    if query:
        filtered = [p for p in filtered if query.lower() in " ".join(str(v) for v in p.values()).lower()]
    if country != "All":
        filtered = [p for p in filtered if p["country"] == country]
    if status != "All":
        filtered = [p for p in filtered if p["status"] == status]
    st.caption(f"{len(filtered)} publication(s)")
    if filtered:
        st.dataframe(pd.DataFrame(filtered), use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect publication", [p["id"] for p in filtered])
        item = next(p for p in filtered if p["id"] == selected)
        with st.expander("Publication details", expanded=True):
            st.write(f"**{item['title']}**")
            st.write(f"Authority: {item['authority']} · Region: {item['country']}")
            st.write(f"Published: {item['published']} · Effective: {item['effective']}")
            st.write(f"Business area: {item['area']} · Classification: {item['kind']}")
    else:
        st.warning("No publications match these filters.")
