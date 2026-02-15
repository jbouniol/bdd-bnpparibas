"""Reusable UI components for the dashboard."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src.metrics import format_hours, format_number, format_pct


def inject_global_styles() -> None:
    """Inject lightweight global styling for a cleaner executive layout."""
    st.markdown(
        """
        <style>
        :root {
            --bnp-green: #00915A;
            --bnp-green-dark: #007A4D;
            --bnp-neutral: #5A646E;
            --bnp-border: #DEE5E1;
            --bnp-surface: #F7FAF8;
        }

        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F8FAF9 0%, #F2F6F4 100%);
            border-right: 1px solid var(--bnp-border);
        }

        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid var(--bnp-border);
            border-left: 4px solid var(--bnp-green);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            min-height: 108px;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.76rem;
            color: var(--bnp-neutral);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        [data-testid="stMetricValue"] {
            color: #1F2933;
            font-weight: 700;
        }

        .page-header {
            margin-bottom: 0.35rem;
        }

        .page-header h2 {
            margin-bottom: 0.15rem;
        }

        .page-header p {
            margin: 0;
            color: var(--bnp-neutral);
            font-size: 0.95rem;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            border-radius: 10px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            border: 1px solid #C8D5CF;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid #E3E9E6;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── KPI row ──────────────────────────────────────────────────────────────────

def render_kpi_row(kpis: dict[str, float | None]) -> None:
    """Render the executive KPI header as a row of st.metric cards."""
    cols = st.columns(5, gap="small")

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
    _, action_col = st.columns([4, 1], gap="small")
    with action_col:
        st.download_button(
            label=label,
            data=csv,
            file_name=f"{key or 'export'}.csv",
            mime="text/csv",
            key=key,
            use_container_width=True,
        )


# ── Empty state ──────────────────────────────────────────────────────────────

def show_empty_state(message: str = "No data available for the current filters.") -> None:
    st.info(message)


# ── Page header ──────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    title_html = escape(title)
    if subtitle:
        subtitle_html = escape(subtitle)
        st.markdown(
            f'<div class="page-header"><h2>{title_html}</h2><p>{subtitle_html}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="page-header"><h2>{title_html}</h2></div>', unsafe_allow_html=True)
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
    info_col, page_col = st.columns([4, 1], gap="small")
    with page_col:
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

    with info_col:
        st.caption(f"Showing {start + 1}-{min(end, total_rows)} of {total_rows:,}")
    st.dataframe(page_df, use_container_width=True)
    return page_df
