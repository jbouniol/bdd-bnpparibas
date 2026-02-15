"""Page 1 – Executive Overview: KPIs, monthly trends, top categories."""

from __future__ import annotations

import streamlit as st

from src.charts import bar_top_categories, line_monthly_sr, scatter_volume_vs_hours
from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import load_category_kpis, load_global_stats
from src.filters import apply_date_filter, render_sidebar_filters
from src.metrics import compute_header_kpis
from src.ui import inject_global_styles, page_header, render_kpi_row, show_empty_state

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{PAGE_TITLE} – Overview", page_icon=PAGE_ICON, layout="wide")
render_sidebar_filters()
inject_global_styles()

# ── Header ───────────────────────────────────────────────────────────────────
page_header("Executive Overview", "High-level diagnostics across all service requests")

# ── Data ─────────────────────────────────────────────────────────────────────
global_stats = apply_date_filter(load_global_stats())
category_kpis = load_category_kpis()

if global_stats.empty:
    show_empty_state()
    st.stop()

# ── KPI row ──────────────────────────────────────────────────────────────────
kpis = compute_header_kpis(global_stats)
render_kpi_row(kpis)

st.markdown("")  # spacer

# ── Charts ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2.5, 1.5], gap="large")

with col_left:
    st.plotly_chart(line_monthly_sr(global_stats), use_container_width=True)

with col_right:
    if not category_kpis.empty:
        st.plotly_chart(bar_top_categories(category_kpis), use_container_width=True)
    else:
        show_empty_state("No category data available.")

st.divider()

# ── Scatter ──────────────────────────────────────────────────────────────────
st.markdown("### Volume vs. Resolution Time by Category")
if not category_kpis.empty:
    st.plotly_chart(scatter_volume_vs_hours(category_kpis), use_container_width=True)
else:
    show_empty_state("No category data available.")
