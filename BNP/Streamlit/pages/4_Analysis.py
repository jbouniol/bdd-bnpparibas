"""Page 4 – Analysis: treatment time by category + top category monthly evolution."""

from __future__ import annotations

import streamlit as st

from src.charts import bar_treatment_time, line_top_categories_monthly
from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import (
    load_category_kpis,
    load_monthly_category_trends,
    load_treatment_time,
)
from src.filters import apply_date_filter, render_sidebar_filters
from src.ui import (
    inject_global_styles,
    page_header,
    render_dataframe_with_download,
    show_empty_state,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{PAGE_TITLE} – Analysis", page_icon=PAGE_ICON, layout="wide",
)
render_sidebar_filters()
inject_global_styles()

# ── Header ───────────────────────────────────────────────────────────────────
page_header(
    "Analysis",
    "Processing time profile and top category evolution",
)

# ── Data ─────────────────────────────────────────────────────────────────────
treatment_df = load_treatment_time()
category_kpis = load_category_kpis()
trends_df = apply_date_filter(load_monthly_category_trends())

# =====================================================================
# 1) Average processing time by category
# =====================================================================
st.markdown("### Average Processing Time by Category")
st.caption(
    "Categories with > 100 closed SRs, ranked by longest average resolution time. "
    "This view highlights categories with the highest processing-time load."
)

if treatment_df.empty:
    show_empty_state("No treatment time data available.")
else:
    st.plotly_chart(bar_treatment_time(treatment_df, top_n=20), use_container_width=True)

    # Display table below
    display_cols = ["category", "total_sr", "avg_days", "avg_hours", "min_hours", "max_hours"]
    available = [c for c in display_cols if c in treatment_df.columns]
    st.markdown("#### Detail Table (sorted by longest avg)")
    render_dataframe_with_download(
        treatment_df[available].head(30),
        label="Download Treatment Time Data",
        key="treatment_csv",
    )

st.divider()

# =====================================================================
# 2) Monthly evolution of top 5 categories
# =====================================================================
st.markdown("### Monthly Evolution – Top 5 Categories")
st.caption(
    "How the 5 highest-volume categories evolve month over month. "
    "Spot seasonal patterns or growing demand."
)

if trends_df.empty or category_kpis.empty:
    show_empty_state("Trend or category data not available.")
else:
    slider_col, _ = st.columns([1.7, 2.3], gap="large")
    with slider_col:
        top_n = st.slider("Number of top categories", 3, 10, 5, key="top_n_slider")
    st.plotly_chart(
        line_top_categories_monthly(trends_df, category_kpis, top_n=top_n),
        use_container_width=True,
    )
