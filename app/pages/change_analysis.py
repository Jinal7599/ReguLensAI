import streamlit as st

from app.data.sample_data import CHANGES


def render_change_analysis() -> None:
    st.title("Change Analysis")
    st.caption("Review clause-level changes, indicative impact and suggested follow-up actions.")
    selected = st.selectbox("Select a detected change", [c["id"] for c in CHANGES])
    change = next(c for c in CHANGES if c["id"] == selected)
    c1, c2, c3 = st.columns(3)
    c1.metric("Classification", change["classification"])
    c2.metric("Priority", change["priority"])
    c3.metric("Region", change["country"])
    st.subheader(change["publication"])
    old, new = st.columns(2)
    with old:
        st.markdown("**Previous position**")
        st.info(change["previous"])
    with new:
        st.markdown("**Updated position**")
        st.success(change["updated"])
    st.subheader("Potential business impact")
    st.write(change["impact"])
    st.subheader("Suggested review actions")
    for action in change["actions"]:
        st.checkbox(action, key=f"{change['id']}-{action}")
    st.caption(f"Evidence reference: {change['source']}")
    st.warning("AI impact assessments are advisory. A qualified compliance reviewer must validate interpretations and actions.")
