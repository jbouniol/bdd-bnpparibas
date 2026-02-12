"""Sidebar filters backed by st.session_state for cross-page persistence."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.data_loader import get_date_range, get_distinct_categories, get_distinct_desks


# ── Session-state keys ───────────────────────────────────────────────────────
_KEY_DATE_START = "filter_date_start"
_KEY_DATE_END = "filter_date_end"
_KEY_DESKS = "filter_desks"
_KEY_CATEGORIES = "filter_categories"
_KEY_STATUS = "filter_status"


def render_sidebar_filters() -> None:
    """Draw the global sidebar filter panel and persist values in session_state."""
    st.sidebar.header("Filters")

    # Date range
    min_dt, max_dt = get_date_range()
    start_default = st.session_state.get(_KEY_DATE_START, min_dt.date())
    end_default = st.session_state.get(_KEY_DATE_END, max_dt.date())

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=start_default,
            min_value=min_dt.date(),
            max_value=max_dt.date(),
            key="__sb_start",
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=end_default,
            min_value=min_dt.date(),
            max_value=max_dt.date(),
            key="__sb_end",
        )
    st.session_state[_KEY_DATE_START] = start_date
    st.session_state[_KEY_DATE_END] = end_date

    # Desk multiselect
    desks = get_distinct_desks()
    default_desks = st.session_state.get(_KEY_DESKS, desks)
    selected_desks = st.sidebar.multiselect(
        "Desk", options=desks, default=default_desks, key="__sb_desks"
    )
    st.session_state[_KEY_DESKS] = selected_desks

    # Category multiselect
    categories = get_distinct_categories()
    default_cats = st.session_state.get(_KEY_CATEGORIES, categories)
    selected_cats = st.sidebar.multiselect(
        "Category", options=categories, default=default_cats, key="__sb_cats"
    )
    st.session_state[_KEY_CATEGORIES] = selected_cats

    # Status
    default_status = st.session_state.get(_KEY_STATUS, "All")
    selected_status = st.sidebar.radio(
        "Status", options=["All", "Closed", "Open"], index=["All", "Closed", "Open"].index(default_status), key="__sb_status"
    )
    st.session_state[_KEY_STATUS] = selected_status


# ── Accessor helpers ─────────────────────────────────────────────────────────

def get_date_filter() -> tuple[date, date]:
    return (
        st.session_state.get(_KEY_DATE_START, date(2024, 1, 1)),
        st.session_state.get(_KEY_DATE_END, date(2025, 9, 30)),
    )


def get_selected_desks() -> list[str]:
    return st.session_state.get(_KEY_DESKS, [])


def get_selected_categories() -> list[str]:
    return st.session_state.get(_KEY_CATEGORIES, [])


def get_selected_status() -> str:
    return st.session_state.get(_KEY_STATUS, "All")


# ── DataFrame filtering ─────────────────────────────────────────────────────

def apply_date_filter(df: pd.DataFrame, date_col: str = "month") -> pd.DataFrame:
    """Filter DataFrame by the sidebar date range."""
    if date_col not in df.columns or df.empty:
        return df
    start, end = get_date_filter()
    mask = (df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)
    return df.loc[mask].copy()


def apply_desk_filter(df: pd.DataFrame, col: str = "desk") -> pd.DataFrame:
    if col not in df.columns or df.empty:
        return df
    selected = get_selected_desks()
    if not selected:
        return df
    return df.loc[df[col].isin(selected)].copy()


def apply_category_filter(df: pd.DataFrame, col: str = "category") -> pd.DataFrame:
    if col not in df.columns or df.empty:
        return df
    selected = get_selected_categories()
    if not selected:
        return df
    return df.loc[df[col].isin(selected)].copy()


def apply_status_filter(df: pd.DataFrame, col: str = "status") -> pd.DataFrame:
    if col not in df.columns or df.empty:
        return df
    status = get_selected_status()
    if status == "All":
        return df
    return df.loc[df[col].str.lower() == status.lower()].copy()


def apply_all_filters(
    df: pd.DataFrame,
    date_col: str = "month",
    desk_col: str = "desk",
    category_col: str = "category",
    status_col: str | None = None,
) -> pd.DataFrame:
    """Apply all sidebar filters in one call."""
    df = apply_date_filter(df, date_col)
    if desk_col:
        df = apply_desk_filter(df, desk_col)
    if category_col:
        df = apply_category_filter(df, category_col)
    if status_col:
        df = apply_status_filter(df, status_col)
    return df
