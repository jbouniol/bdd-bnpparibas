"""Reusable UI components for the dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.metrics import format_hours, format_number, format_pct


# ── KPI row ──────────────────────────────────────────────────────────────────

def render_kpi_row(kpis: dict[str, float | None]) -> None:
    """Render the executive KPI header as a row of st.metric cards."""
    cols = st.columns(5)

    with cols[0]:
        st.metric("Total SR", format_number(kpis.get("total_sr")))
    with cols[1]:
        st.metric("Closure Rate", format_pct(kpis.get("closure_rate")))
    with cols[2]:
        st.metric("Avg Time to Close", format_hours(kpis.get("avg_hours_to_close")))
    with cols[3]:
        st.metric("Avg 1st Response", format_hours(kpis.get("avg_first_response_hours")))
    with cols[4]:
        sla = kpis.get("sla_compliance")
        st.metric("SLA Compliance", format_pct(sla) if sla is not None else "N/A")


# ── Downloadable table ───────────────────────────────────────────────────────

def render_dataframe_with_download(
    df: pd.DataFrame,
    label: str = "Download CSV",
    key: str | None = None,
    height: int = 400,
) -> None:
    """Display a sortable dataframe with a CSV download button."""
    st.dataframe(df, use_container_width=True, height=height)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=f"{key or 'export'}.csv",
        mime="text/csv",
        key=key,
    )


# ── Empty state ──────────────────────────────────────────────────────────────

def show_empty_state(message: str = "No data available for the current filters.") -> None:
    st.info(message)


# ── Page header ──────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


# ── Paginated table ──────────────────────────────────────────────────────────

def render_paginated_table(
    df: pd.DataFrame,
    page_size: int = 25,
    key_prefix: str = "pag",
) -> pd.DataFrame:
    """Show a paginated dataframe. Returns the currently visible slice."""
    if df.empty:
        show_empty_state()
        return df

    total_rows = len(df)
    total_pages = max(1, (total_rows - 1) // page_size + 1)
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
        key=f"{key_prefix}_page",
    )
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    st.caption(f"Showing {start + 1}–{min(end, total_rows)} of {total_rows:,}")
    st.dataframe(page_df, use_container_width=True)
    return page_df
