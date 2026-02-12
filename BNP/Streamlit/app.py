"""BNP Paribas – SR Analytics Dashboard.

Entry point for the Streamlit multipage app.
Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.config import PAGE_ICON, PAGE_TITLE
from src.filters import render_sidebar_filters

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for executive look ────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    /* KPI cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #212529;
    }
    /* Divider */
    hr {
        border-color: #E0E0E0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    Welcome to the **BNP Paribas SR Analytics Dashboard**.

    Use the sidebar to navigate across pages:

    | Page | Purpose |
    |------|---------|
    | **Executive Overview** | High-level KPIs, monthly trends, top categories |
    | **Category Deep Dive** | Sortable table, Pareto analysis, category trends |
    | **Desk Benchmark** | Desk ranking, heatmap, outlier detection |
    | **SR Explorer** | Search, paginated table, individual SR details |
    | **Jo Analysis** | Processing time pain points, top 5 category evolution |

    *Data source: pre-aggregated Parquet extracts generated from the Hobart database.*
    """
)
st.divider()
st.caption("Dashboard v1.0 — Data period configured in sidebar filters.")
