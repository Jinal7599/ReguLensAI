from __future__ import annotations

# Streamlit may put the app/ directory, rather than the repository root,
# on sys.path when launched as "streamlit run app/main.py". Add the root so
# package imports such as "from app.data..." work in local and hosted runs.
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.data.sample_data import PUBLICATIONS
from app.pages.change_analysis import render_change_analysis
from app.pages.dashboard import render_dashboard
from app.pages.regulatory_feed import render_regulatory_feed
from app.pages.settings import render_settings

st.set_page_config(
    page_title="ReguLens AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f6f8fb; }
[data-testid="stSidebar"] { background: #101d32; }
[data-testid="stSidebar"] * { color: #edf3fc !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 8px 10px; border-radius: 8px; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
.hero { background: linear-gradient(115deg,#142b4d 0%,#244d75 100%); padding: 26px 30px; border-radius: 16px; color: white; margin-bottom: 22px; }
.hero h1 { color: white; font-size: 2rem; margin: 0 0 6px 0; }
.hero p { color: #d7e5f6; margin: 0; }
.metric-card { background: white; border: 1px solid #e7edf4; border-radius: 13px; padding: 18px 20px; min-height: 112px; }
.metric-label { color: #64748b; font-size: .85rem; font-weight: 600; }
.metric-value { color: #142b4d; font-size: 2rem; font-weight: 700; margin-top: 4px; }
.section-note { color: #64748b; font-size: .9rem; }
div[data-testid="stDataFrame"] { background: white; border-radius: 12px; }
.stButton button { border-radius: 9px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ◈ ReguLens AI")
    st.caption("REGULATORY INTELLIGENCE")
    st.divider()
    page = st.radio(
        "Workspace",
        ["Overview", "Regulatory Feed", "Change Analysis", "Settings"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("DEMO ENVIRONMENT")
    st.caption("Synthetic sample data")
    st.caption("Build: Iteration 1")

if page == "Overview":
    render_dashboard(PUBLICATIONS)
elif page == "Regulatory Feed":
    render_regulatory_feed(PUBLICATIONS)
elif page == "Change Analysis":
    render_change_analysis()
else:
    render_settings()
