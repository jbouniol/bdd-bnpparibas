"""Plotly chart factory functions — one function per chart type.
"""

from __future__ import annotations

import textwrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import (
    COLOR_ACCENT,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    PALETTE_CATEGORICAL,
)

# ── Shared layout defaults ───────────────────────────────────────────────────
_LAYOUT_DEFAULTS: dict = dict(
    font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=COLOR_NEUTRAL),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
)


def _apply_defaults(fig: go.Figure, **overrides: object) -> go.Figure:
    layout = {**_LAYOUT_DEFAULTS, **overrides}
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E0E0E0")
    return fig


# ── 1) Line chart: monthly SR volume ────────────────────────────────────────

def line_monthly_sr(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df.sort_values("month"),
        x="month",
        y="total_sr",
        markers=True,
        labels={"month": "Month", "total_sr": "Total SR"},
    )
    fig.update_traces(line_color=COLOR_PRIMARY, line_width=2.5, marker_size=8)
    return _apply_defaults(fig, title="Monthly SR Volume")


# ── 2) Bar chart: categories by volume ──────────────────────────────────────

def _select_category_slice(df: pd.DataFrame, top_n: int, mode: str) -> pd.DataFrame:
    if mode == "bottom":
        return df.nsmallest(top_n, "total_sr").sort_values("total_sr", ascending=True)
    return df.nlargest(top_n, "total_sr").sort_values("total_sr", ascending=True)


def bar_category_volume(df: pd.DataFrame, top_n: int = 15, mode: str = "top") -> go.Figure:
    """Horizontal bar of top or bottom N categories by volume."""
    subset = _select_category_slice(df, top_n, mode)
    has_closure = "closure_rate" in subset.columns
    title_prefix = "Top" if mode == "top" else "Flop"
    fig = go.Figure(
        go.Bar(
            y=subset["category"],
            x=subset["total_sr"],
            orientation="h",
            text=subset["total_sr"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            marker=dict(
                color=subset["closure_rate"] if has_closure else COLOR_PRIMARY,
                colorscale="RdYlGn" if has_closure else None,
                showscale=has_closure,
                colorbar=dict(title="Closure %") if has_closure else None,
            ),
            hovertemplate="<b>%{y}</b><br>Volume: %{x:,}<extra></extra>",
        )
    )
    return _apply_defaults(
        fig,
        title=f"{title_prefix} {top_n} Categories by Volume",
        xaxis_title="Number of Requests",
        height=max(400, top_n * 32),
    )


def bar_top_categories(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Backward-compatible wrapper for top category volume bar chart."""
    return bar_category_volume(df, top_n=top_n, mode="top")


# ── 3) Scatter: volume vs avg hours (color = SLA) ───────────────────────────

def scatter_volume_vs_hours(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Scatter of top N categories: volume vs resolution time."""
    subset = df.nlargest(top_n, "total_sr").copy()
    has_sla = "sla_compliance" in subset.columns and subset["sla_compliance"].notna().any()

    fig = px.scatter(
        subset,
        x="total_sr",
        y="avg_hours_to_close",
        color="sla_compliance" if has_sla else None,
        size="total_sr",
        hover_name="category",
        labels={
            "total_sr": "Volume",
            "avg_hours_to_close": "Avg Hours to Close",
            "sla_compliance": "SLA %",
        },
        color_continuous_scale="RdYlGn",
        size_max=50,
    )
    fig.update_traces(marker=dict(line=dict(width=1, color="white")))
    if has_sla:
        fig.add_hline(
            y=subset["avg_hours_to_close"].median(), line_dash="dash",
            line_color="#999", annotation_text="Median", annotation_position="right",
        )
    return _apply_defaults(fig, title="Volume vs. Resolution Time (Top Categories)", height=500)


# ── 4) Pareto chart (top 20 only) ───────────────────────────────────────────

def pareto_categories(
    df: pd.DataFrame,
    top_n: int = 20,
    target_pct: float = 80.0,
) -> go.Figure:
    """Pareto chart on top N categories."""
    sorted_df = df.nlargest(top_n, "total_sr").sort_values("total_sr", ascending=False).reset_index(drop=True)
    if sorted_df.empty:
        return go.Figure()

    sorted_df["category_label"] = sorted_df["category"].astype(str).map(
        lambda value: "<br>".join(textwrap.wrap(value, width=22))
    )
    shown_total = sorted_df["total_sr"].sum()
    sorted_df["cumulative_pct"] = sorted_df["total_sr"].cumsum() / shown_total * 100.0

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=sorted_df["category_label"],
            y=sorted_df["total_sr"],
            name="Volume",
            marker_color=COLOR_PRIMARY,
            text=sorted_df["total_sr"].apply(lambda v: f"{v:,}"),
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Volume: %{y:,}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sorted_df["category_label"],
            y=sorted_df["cumulative_pct"],
            name="Cumulative %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color=COLOR_ACCENT, width=2.5),
            marker=dict(size=6),
            hovertemplate="%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis=dict(title="Volume"),
        yaxis2=dict(
            title="Cumulative share of shown categories (%)",
            overlaying="y",
            side="right",
            range=[0, 105],
        ),
        xaxis_tickangle=-20,
        legend=dict(orientation="h", x=0.0, y=1.04),
        margin=dict(l=40, r=30, t=80, b=70),
    )
    fig.add_hline(
        y=target_pct,
        yref="y2",
        line_dash="dash",
        line_color=COLOR_ACCENT,
        annotation_text=f"{target_pct:.0f}% threshold",
        annotation_position="top right",
    )
    fig.update_traces(cliponaxis=False)
    return _apply_defaults(fig, title=f"Pareto – Top {top_n} Categories", height=560)


# ── 5) Trend line for a single category ─────────────────────────────────────

def line_category_trend(df: pd.DataFrame, category: str) -> go.Figure:
    subset = (
        df[df["category"] == category].sort_values("month")
        if "category" in df.columns else df
    )
    fig = px.line(
        subset,
        x="month",
        y="total_sr",
        markers=True,
        labels={"month": "Month", "total_sr": "SR Volume"},
    )
    fig.update_traces(line_color=COLOR_SECONDARY, line_width=2, marker_size=7)
    return _apply_defaults(fig, title=f"Trend – {category}")


# ── 6) Top 5 categories monthly evolution (multi-line) ──────────────────────

def line_top_categories_monthly(
    trends_df: pd.DataFrame,
    category_kpis_df: pd.DataFrame,
    top_n: int = 5,
    mode: str = "top",
) -> go.Figure:
    """Multi-line chart: monthly evolution of top or bottom N categories by total volume."""
    if mode == "bottom":
        selected_cats = category_kpis_df.nsmallest(top_n, "total_sr")["category"].tolist()
        title_prefix = "Flop"
    else:
        selected_cats = category_kpis_df.nlargest(top_n, "total_sr")["category"].tolist()
        title_prefix = "Top"
    subset = trends_df[trends_df["category"].isin(selected_cats)].sort_values("month")

    fig = px.line(
        subset,
        x="month",
        y="total_sr",
        color="category",
        markers=True,
        labels={"month": "Month", "total_sr": "Number of Requests", "category": "Category"},
        color_discrete_sequence=PALETTE_CATEGORICAL[:top_n],
    )
    fig.update_traces(line_width=2.5, marker_size=6)
    return _apply_defaults(fig, title=f"Monthly Evolution – {title_prefix} {top_n} Categories", height=500)


# ── 7) Treatment time bar (horizontal, colour = days) ───────────────────────

def bar_treatment_time(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar: top N slowest categories by avg days to close."""
    top = df.head(top_n).sort_values("avg_days", ascending=True)

    fig = go.Figure(
        go.Bar(
            y=top["category"],
            x=top["avg_days"],
            orientation="h",
            text=top["avg_days"].apply(lambda x: f"{x:.1f} d"),
            textposition="outside",
            marker=dict(color=top["avg_days"], colorscale="Reds"),
            hovertemplate="<b>%{y}</b><br>Avg: %{x:.1f} days<extra></extra>",
        )
    )
    return _apply_defaults(
        fig,
        title="Average Processing Time by Category (days)",
        xaxis_title="Days",
        height=max(400, top_n * 32),
        showlegend=False,
    )


# ── 8) Desk ranking bar (top N only) ────────────────────────────────────────

def bar_desk_ranking(
    df: pd.DataFrame, metric: str = "total_sr", top_n: int = 20,
) -> go.Figure:
    """Top N desks by selected metric (aggregated mean across months)."""
    agg = df.groupby("desk", as_index=False)[metric].mean()
    top = agg.nlargest(top_n, metric).sort_values(metric, ascending=True)

    label_map = {
        "total_sr": "Avg Monthly SR",
        "avg_hours_to_close": "Avg Hours to Close",
        "closure_rate": "Closure Rate %",
        "sla_compliance": "SLA Compliance %",
        "avg_first_response_hours": "Avg 1st Response (h)",
    }
    fig = go.Figure(
        go.Bar(
            y=top["desk"],
            x=top[metric],
            orientation="h",
            text=top[metric].apply(lambda v: f"{v:,.1f}"),
            textposition="outside",
            marker_color=COLOR_PRIMARY,
            hovertemplate="<b>Desk %{y}</b><br>%{x:,.1f}<extra></extra>",
        )
    )
    return _apply_defaults(
        fig,
        title=f"Top {top_n} Desks – {label_map.get(metric, metric)}",
        xaxis_title=label_map.get(metric, metric),
        height=max(400, top_n * 28),
    )


# ── 9) Heatmap month × desk (top N desks only) ─────────────────────────────

def heatmap_desk_month(
    df: pd.DataFrame, metric: str = "total_sr", top_n: int = 20,
) -> go.Figure:
    if df.empty:
        return go.Figure()

    # Keep only top N desks by total volume
    desk_totals = df.groupby("desk")["total_sr"].sum()
    top_desks = desk_totals.nlargest(top_n).index.tolist()
    filtered = df[df["desk"].isin(top_desks)]

    pivot = filtered.pivot_table(
        index="desk", columns="month", values=metric, aggfunc="mean",
    )
    pivot = pivot.fillna(0)
    col_labels = [
        c.strftime("%Y-%m") if hasattr(c, "strftime") else str(c)
        for c in pivot.columns
    ]

    label_map = {
        "total_sr": "SR Volume",
        "avg_hours_to_close": "Avg Hours to Close",
        "closure_rate": "Closure Rate %",
        "sla_compliance": "SLA Compliance %",
    }
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=col_labels,
            y=pivot.index.tolist(),
            colorscale="Greens",
            hovertemplate="Desk: %{y}<br>Month: %{x}<br>Value: %{z:.1f}<extra></extra>",
        )
    )
    return _apply_defaults(
        fig,
        title=f"Heatmap – {label_map.get(metric, metric)} (Top {top_n} Desks)",
        height=max(400, top_n * 28),
    )


# ── 10) Outlier highlight bar ───────────────────────────────────────────────

def bar_outliers(
    df: pd.DataFrame, value_col: str, group_col: str = "desk",
) -> go.Figure:
    colors = [
        COLOR_ACCENT if row.get("is_outlier") else COLOR_PRIMARY
        for _, row in df.iterrows()
    ]
    fig = go.Figure(
        go.Bar(
            x=df[group_col],
            y=df[value_col],
            marker_color=colors,
            text=df[value_col].apply(lambda v: f"{v:,.1f}"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:,.1f}<extra></extra>",
        )
    )
    return _apply_defaults(fig, title=f"Outlier Detection – {value_col}", height=450)
