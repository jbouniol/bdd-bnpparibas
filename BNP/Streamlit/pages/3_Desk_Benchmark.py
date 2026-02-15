"""Page 3 – Desk Benchmark: clear ranking, monthly trend, and desk scorecard."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import load_monthly_desk_metrics
from src.filters import apply_all_filters, render_sidebar_filters
from src.ui import (
    inject_global_styles,
    page_header,
    render_dataframe_with_download,
    show_empty_state,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{PAGE_TITLE} – Desk Benchmark", page_icon=PAGE_ICON, layout="wide")
render_sidebar_filters()
inject_global_styles()

# ── Header ───────────────────────────────────────────────────────────────────
page_header("Desk Benchmark", "Benchmark lisible des desks: ranking, tendance mensuelle et scorecard")

# ── Data ─────────────────────────────────────────────────────────────────────
desk_df = apply_all_filters(
    load_monthly_desk_metrics(),
    date_col="month",
    desk_col="",
    category_col="",
)

if desk_df.empty or "desk" not in desk_df.columns:
    show_empty_state("Desk data is unavailable for the current filters.")
    st.stop()

# ── Metric selector and benchmark setup ─────────────────────────────────────
METRIC_OPTIONS: dict[str, dict[str, object]] = {
    "Average monthly SR volume": {
        "col": "avg_monthly_sr",
        "higher_is_better": True,
        "axis_label": "Average Monthly SR",
    },
    "Average hours to close": {
        "col": "avg_hours_to_close",
        "higher_is_better": False,
        "axis_label": "Average Hours to Close",
    },
    "Average first response (hours)": {
        "col": "avg_first_response_hours",
        "higher_is_better": False,
        "axis_label": "Average First Response (h)",
    },
    "Closure rate (%)": {
        "col": "closure_rate",
        "higher_is_better": True,
        "axis_label": "Closure Rate (%)",
    },
    "SLA compliance (%)": {
        "col": "sla_compliance",
        "higher_is_better": True,
        "axis_label": "SLA Compliance (%)",
    },
}

summary = (
    desk_df.groupby("desk", as_index=False)
    .agg(
        months_covered=("month", "nunique"),
        total_sr=("total_sr", "sum"),
        avg_monthly_sr=("total_sr", "mean"),
        avg_hours_to_close=("avg_hours_to_close", "mean"),
        avg_first_response_hours=("avg_first_response_hours", "mean"),
        closure_rate=("closure_rate", "mean"),
        sla_compliance=("sla_compliance", "mean"),
    )
)

available_options = {
    label: meta for label, meta in METRIC_OPTIONS.items() if meta["col"] in summary.columns
}
if not available_options:
    show_empty_state("No benchmark metric is available.")
    st.stop()

control_col_1, control_col_2 = st.columns([1.6, 1], gap="large")
with control_col_1:
    selected_label = st.selectbox("Benchmark metric", list(available_options.keys()), key="desk_metric")
with control_col_2:
    max_n = min(25, len(summary))
    min_n = 1 if max_n < 5 else 5
    default_n = min(10, max_n)
    top_n = st.slider("Top desks displayed", min_value=min_n, max_value=max_n, value=default_n, step=1)

metric_meta = available_options[selected_label]
metric_col = str(metric_meta["col"])
higher_is_better = bool(metric_meta["higher_is_better"])
axis_label = str(metric_meta["axis_label"])

ranking = summary.dropna(subset=[metric_col]).sort_values(metric_col, ascending=not higher_is_better)
if ranking.empty:
    show_empty_state("No desk ranking can be computed for this metric.")
    st.stop()

best_row = ranking.iloc[0]
worst_row = ranking.iloc[-1]
spread = (
    best_row[metric_col] - worst_row[metric_col]
    if higher_is_better
    else worst_row[metric_col] - best_row[metric_col]
)

def _fmt_metric(value: float, col: str) -> str:
    if col in {"closure_rate", "sla_compliance"}:
        return f"{value:.1f}%"
    if col in {"avg_hours_to_close", "avg_first_response_hours"}:
        return f"{value:.1f} h"
    return f"{value:,.1f}"

kpi_col_1, kpi_col_2, kpi_col_3 = st.columns(3, gap="small")
with kpi_col_1:
    st.metric("Best desk", str(best_row["desk"]))
    st.caption(f"{axis_label}: {_fmt_metric(float(best_row[metric_col]), metric_col)}")
with kpi_col_2:
    st.metric("Lowest desk", str(worst_row["desk"]))
    st.caption(f"{axis_label}: {_fmt_metric(float(worst_row[metric_col]), metric_col)}")
with kpi_col_3:
    st.metric("Performance spread", _fmt_metric(float(spread), metric_col))

st.info(
    "Lecture: le ranking montre les desks les plus performants selon la metrique choisie. "
    "La tendance mensuelle permet de verifier si la performance est stable dans le temps."
)

# ── Layout ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1.15, 1.85], gap="large")

with col_left:
    st.markdown("### Ranking")
    top_slice = ranking.head(top_n).sort_values(metric_col, ascending=True)
    fig_rank = px.bar(
        top_slice,
        x=metric_col,
        y="desk",
        orientation="h",
        color=metric_col,
        color_continuous_scale="Greens" if higher_is_better else "Reds",
        text=top_slice[metric_col].map(lambda x: _fmt_metric(float(x), metric_col)),
        labels={metric_col: axis_label, "desk": "Desk"},
    )
    fig_rank.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>%{x:.2f}<extra></extra>")
    fig_rank.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=35, b=10), height=520)
    st.plotly_chart(fig_rank, use_container_width=True)

with col_right:
    st.markdown("### Monthly trend (selected desks)")
    default_desks = ranking.head(min(5, len(ranking)))["desk"].astype(str).tolist()
    selected_desks = st.multiselect(
        "Desks to compare",
        options=ranking["desk"].astype(str).tolist(),
        default=default_desks,
        key="desk_compare_desks",
    )

    trend_df = desk_df[desk_df["desk"].astype(str).isin(selected_desks)].copy()
    if trend_df.empty:
        show_empty_state("Select at least one desk to display the trend.")
    else:
        fig_trend = px.line(
            trend_df.sort_values("month"),
            x="month",
            y=metric_col,
            color="desk",
            markers=True,
            labels={"month": "Month", metric_col: axis_label, "desk": "Desk"},
        )
        fig_trend.update_layout(margin=dict(l=10, r=10, t=35, b=10), height=520)
        st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Scorecard table ──────────────────────────────────────────────────────────
st.markdown("### Desk scorecard")
table_columns = [
    "desk",
    "months_covered",
    "total_sr",
    "avg_monthly_sr",
    "avg_hours_to_close",
    "avg_first_response_hours",
    "closure_rate",
    "sla_compliance",
]
scorecard = ranking[[col for col in table_columns if col in ranking.columns]].copy()

for col in ["avg_monthly_sr", "avg_hours_to_close", "avg_first_response_hours", "closure_rate", "sla_compliance"]:
    if col in scorecard.columns:
        scorecard[col] = scorecard[col].astype(float).round(2)

render_dataframe_with_download(
    scorecard,
    label="Download Desk Scorecard",
    key="desk_scorecard_csv",
    height=460,
)
