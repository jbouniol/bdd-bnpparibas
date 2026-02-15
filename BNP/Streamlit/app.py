"""BNP Paribas – SR Analytics Dashboard.

Entry point for the Streamlit multipage app.
Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.config import PAGE_ICON, PAGE_TITLE
from src.filters import render_sidebar_filters
from src.ui import inject_global_styles

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_styles()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/en/thumb/5/5a/BNP_Paribas.svg/220px-BNP_Paribas.svg.png",
    width=160,
)
st.sidebar.markdown("# SR Analytics")
st.sidebar.markdown("---")
render_sidebar_filters()

# ── Landing page ─────────────────────────────────────────────────────────────
st.markdown("# Service Request Analytics")
st.markdown(
    "This dashboard monitors request volume, service performance, and category/desk dynamics "
    "from direct HOBART database queries."
)

st.markdown("### Start Here")
step_col_1, step_col_2, step_col_3 = st.columns(3, gap="large")
with step_col_1:
    st.markdown(
        """
        **1) Set scope in the sidebar**
        
        Choose date range, category scope, and status.
        """
    )
with step_col_2:
    st.markdown(
        """
        **2) Open a page**
        
        Use the page menu to navigate to the analysis module you need.
        """
    )
with step_col_3:
    st.markdown(
        """
        **3) Export results**
        
        Each analysis page provides downloadable tables.
        """
    )

st.markdown("### Analytics Modules")
st.markdown(
    """
    | Page | What You Get |
    |------|---------------|
    | **Executive Overview** | Global KPIs, monthly trajectory, and category-level signals |
    | **Category Deep Dive** | Category ranking table, Pareto distribution, and trend by category |
    | **Desk Benchmark** | Desk ranking, monthly desk comparison, and scorecard export |
    | **Analysis** | Processing-time analysis and evolution of top categories |
    """
)

st.markdown("### Data Pipeline")
st.caption(
    "The app reads directly from the HOBART SQLite database. "
    "SQL views and cached loaders are used to keep page rendering responsive."
)
st.divider()
st.caption("Dashboard v1.1 - Data period and business scope are controlled from sidebar filters.")
