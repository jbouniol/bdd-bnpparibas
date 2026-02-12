"""Metric computation helpers — no Streamlit dependency except types."""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Duration formatting ──────────────────────────────────────────────────────

def format_hours(hours: float | None) -> str:
    """Human-readable duration from hours (e.g. '2d 5h' or '3h 12m')."""
    if hours is None or np.isnan(hours):
        return "—"
    if hours < 0:
        return "—"
    total_minutes = int(round(hours * 60))
    days, remainder = divmod(total_minutes, 1440)
    h, m = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {h}h"
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def format_pct(value: float | None, decimals: int = 1) -> str:
    if value is None or np.isnan(value):
        return "—"
    return f"{value:.{decimals}f}%"


def format_number(value: float | int | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and np.isnan(value):
        return "—"
    return f"{int(value):,}"


# ── Aggregate KPIs ───────────────────────────────────────────────────────────

def compute_header_kpis(df: pd.DataFrame) -> dict[str, float | None]:
    """Compute executive header KPIs from global_stats extract."""
    if df.empty:
        return {
            "total_sr": None,
            "closure_rate": None,
            "avg_hours_to_close": None,
            "avg_first_response_hours": None,
            "sla_compliance": None,
        }
    total_sr = df["total_sr"].sum() if "total_sr" in df.columns else None

    closed = df["closed_sr"].sum() if "closed_sr" in df.columns else 0
    closure_rate = (closed / total_sr * 100) if total_sr else None

    avg_close = (
        df["avg_hours_to_close"].mean() if "avg_hours_to_close" in df.columns else None
    )
    avg_first = (
        df["avg_first_response_hours"].mean()
        if "avg_first_response_hours" in df.columns
        else None
    )
    sla = df["sla_compliance"].mean() if "sla_compliance" in df.columns else None

    return {
        "total_sr": total_sr,
        "closure_rate": closure_rate,
        "avg_hours_to_close": avg_close,
        "avg_first_response_hours": avg_first,
        "sla_compliance": sla,
    }


# ── Outlier detection ────────────────────────────────────────────────────────

def detect_outliers_iqr(
    df: pd.DataFrame, value_col: str, group_col: str = "desk"
) -> pd.DataFrame:
    """Flag groups whose metric is an IQR outlier. Returns df with 'is_outlier' column."""
    if df.empty or value_col not in df.columns:
        return df.assign(is_outlier=False)

    agg = df.groupby(group_col, as_index=False)[value_col].mean()
    q1 = agg[value_col].quantile(0.25)
    q3 = agg[value_col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    agg["is_outlier"] = (agg[value_col] < lower) | (agg[value_col] > upper)
    return agg
