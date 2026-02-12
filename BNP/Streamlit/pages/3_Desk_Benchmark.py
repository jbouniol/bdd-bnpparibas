"""Page 3 – Desk Benchmark: ranking, heatmap, outlier detection."""

from __future__ import annotations

import streamlit as st

from src.charts import bar_desk_ranking, bar_outliers, heatmap_desk_month
from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import load_monthly_desk_metrics
from src.filters import apply_all_filters, render_sidebar_filters
from src.metrics import detect_outliers_iqr
from src.ui import page_header, render_dataframe_with_download, show_empty_state

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{PAGE_TITLE} – Desk Benchmark", page_icon=PAGE_ICON, layout="wide")
render_sidebar_filters()

# ── Header ───────────────────────────────────────────────────────────────────
page_header("Desk Benchmark", "Compare desk performance and identify outliers")

# ── Data ─────────────────────────────────────────────────────────────────────
desk_df = apply_all_filters(
    load_monthly_desk_metrics(),
    date_col="month",
    desk_col="desk",
    category_col="",
)

if desk_df.empty:
    show_empty_state()
    st.stop()

# ── Metric selector ─────────────────────────────────────────────────────────
METRIC_OPTIONS = {
    "SR Volume": "total_sr",
    "Avg Hours to Close": "avg_hours_to_close",
    "Avg First Response (h)": "avg_first_response_hours",
    "Closure Rate %": "closure_rate",
    "SLA Compliance %": "sla_compliance",
}

# Filter to only available columns
available_options = {k: v for k, v in METRIC_OPTIONS.items() if v in desk_df.columns}
selected_label = st.selectbox("Metric", list(available_options.keys()), key="desk_metric")
selected_metric = available_options[selected_label]

# ── Layout ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Desk Ranking")
    st.plotly_chart(bar_desk_ranking(desk_df, selected_metric), use_container_width=True)

with col_right:
    st.markdown("### Heatmap – Month x Desk")
    st.plotly_chart(heatmap_desk_month(desk_df, selected_metric), use_container_width=True)

st.divider()

# ── Outlier detection ────────────────────────────────────────────────────────
st.markdown("### Outlier Detection (IQR)")
outlier_df = detect_outliers_iqr(desk_df, selected_metric, "desk")

if not outlier_df.empty:
    n_outliers = outlier_df["is_outlier"].sum()
    if n_outliers > 0:
        st.warning(f"{n_outliers} desk(s) flagged as outlier(s) on **{selected_label}**.")
    else:
        st.success("No outliers detected on this metric.")
    st.plotly_chart(bar_outliers(outlier_df, selected_metric, "desk"), use_container_width=True)
    render_dataframe_with_download(outlier_df, label="Download Outlier Data", key="outlier_csv")
else:
    show_empty_state("Not enough data for outlier analysis.")
