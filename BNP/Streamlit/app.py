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
    """
    Executive dashboard for monitoring SR volume, closure performance, treatment delays,
    and desk/category dynamics from pre-aggregated extracts.

    Use the sidebar to navigate across the analytics modules:

    | Page | Purpose |
    |------|---------|
    | **Executive Overview** | High-level KPIs, monthly trends, top categories |
    | **Category Deep Dive** | Sortable table, Pareto analysis, category trends |
    | **Desk Benchmark** | Clear desk benchmark: ranking, monthly trend, scorecard |
    | **Analysis** | Processing time pain points, top category evolution |

    *Data source: Parquet extracts generated offline from the Hobart SQLite database.*
    """
)
st.divider()
st.caption("Dashboard v1.1 - Data period and business scope are controlled from sidebar filters.")
