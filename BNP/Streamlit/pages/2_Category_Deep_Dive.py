"""Page 2 – Category Deep Dive: sortable table, Pareto, trend per category."""

from __future__ import annotations

import streamlit as st

from src.charts import line_category_trend, pareto_categories
from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import load_category_kpis, load_monthly_category_trends
from src.filters import (
    apply_category_filter,
    apply_date_filter,
    render_sidebar_filters,
)
from src.ui import (
    inject_global_styles,
    page_header,
    render_dataframe_with_download,
    show_empty_state,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{PAGE_TITLE} – Categories", page_icon=PAGE_ICON, layout="wide")
render_sidebar_filters()
inject_global_styles()

# ── Header ───────────────────────────────────────────────────────────────────
page_header("Category Deep Dive", "Analyze category volume, resolution time, and SLA compliance")

# ── Data ─────────────────────────────────────────────────────────────────────
cat_kpis = apply_category_filter(load_category_kpis())
trends = apply_date_filter(apply_category_filter(load_monthly_category_trends()))

if cat_kpis.empty:
    show_empty_state()
    st.stop()

# ── Sortable table ───────────────────────────────────────────────────────────
st.markdown("### Category KPIs")

display_df = cat_kpis.copy()
display_df = display_df.sort_values("total_sr", ascending=False).reset_index(drop=True)

render_dataframe_with_download(display_df, label="Download Category KPIs", key="cat_kpis_csv")

st.divider()

# ── Pareto ───────────────────────────────────────────────────────────────────
st.markdown("### Pareto Analysis")
st.caption(
    "Bars show request volume by category. The red line shows cumulative contribution "
    "to total volume, with a configurable threshold."
)
control_col_1, control_col_2 = st.columns([1, 1], gap="large")
with control_col_1:
    pareto_top_n = st.slider("Top categories shown", 8, 40, 20, key="pareto_top_n")
with control_col_2:
    pareto_threshold = st.slider("Cumulative threshold (%)", 60, 95, 80, key="pareto_threshold")

st.plotly_chart(
    pareto_categories(cat_kpis, top_n=pareto_top_n, target_pct=float(pareto_threshold)),
    use_container_width=True,
)

st.divider()

# ── Category trend selector ──────────────────────────────────────────────────
st.markdown("### Category Trend")
if not trends.empty and "category" in trends.columns:
    categories = sorted(trends["category"].unique().tolist())
    selector_col, _ = st.columns([1.8, 2.2], gap="large")
    with selector_col:
        selected = st.selectbox("Select a category", categories, key="cat_trend_select")
    if selected:
        st.plotly_chart(line_category_trend(trends, selected), use_container_width=True)
else:
    show_empty_state("No trend data available.")
