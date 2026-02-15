"""Sidebar filters backed by st.session_state for cross-page persistence."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.data_loader import get_date_range, load_category_kpis


# ── Session-state keys ───────────────────────────────────────────────────────
_KEY_DATE_START = "filter_date_start"
_KEY_DATE_END = "filter_date_end"
_KEY_DESKS = "filter_desks"
_KEY_CATEGORIES = "filter_categories"
_KEY_STATUS = "filter_status"
_DEFAULT_START_DATE = date(2025, 1, 1)


def render_sidebar_filters() -> None:
    """Draw the global sidebar filter panel and persist values in session_state."""
    st.sidebar.header("Filters")

    # Date range
    min_dt, max_dt = get_date_range()
    first_start_date = max(min_dt.date(), _DEFAULT_START_DATE)
    start_default = st.session_state.get(_KEY_DATE_START, first_start_date)
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

    # Desk filter is disabled.
    st.session_state[_KEY_DESKS] = []

    # Category filter modes.
    st.sidebar.subheader("Category Scope")
    mode = st.sidebar.radio(
        "Selection mode",
        options=["All categories", "Top by volume", "Search and select"],
        key="__sb_category_mode",
    )

    category_kpis = load_category_kpis()
    if {"category", "total_sr"}.issubset(category_kpis.columns):
        categories = (
            category_kpis.sort_values("total_sr", ascending=False)["category"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
    elif "category" in category_kpis.columns:
        categories = sorted(category_kpis["category"].dropna().astype(str).unique().tolist())
    else:
        categories = []

    if mode == "All categories":
        st.session_state[_KEY_CATEGORIES] = []
        st.sidebar.caption("All categories are included.")
    elif mode == "Top by volume":
        if not categories:
            st.session_state[_KEY_CATEGORIES] = []
            st.sidebar.caption("No category list available.")
        else:
            max_top = min(100, len(categories))
            min_top = 1 if max_top < 5 else 5
            default_top = min(20, max_top)
            step = 1 if max_top < 10 else 5
            top_n = st.sidebar.slider(
                "Top categories (N)",
                min_value=min_top,
                max_value=max_top,
                value=default_top,
                step=step,
                key="__sb_cat_top_n",
            )
            st.session_state[_KEY_CATEGORIES] = categories[:top_n]
            st.sidebar.caption(f"{top_n} categories selected.")
    else:
        search_term = st.sidebar.text_input(
            "Search keyword",
            value=st.session_state.get("__sb_cat_search", ""),
            placeholder="Type part of a category name",
            key="__sb_cat_search",
        ).strip().lower()
        if search_term:
            filtered_options = [cat for cat in categories if search_term in cat.lower()]
        else:
            filtered_options = categories[:200]

        previous = st.session_state.get(_KEY_CATEGORIES, [])
        default_custom = [cat for cat in previous if cat in filtered_options]
        selected_cats = st.sidebar.multiselect(
            "Categories",
            options=filtered_options,
            default=default_custom,
            key="__sb_cats_custom",
        )
        st.session_state[_KEY_CATEGORIES] = selected_cats
        st.sidebar.caption(f"{len(filtered_options):,} matching options.")

    # Status
    default_status = st.session_state.get(_KEY_STATUS, "All")
    selected_status = st.sidebar.radio(
        "Status", options=["All", "Closed", "Open"], index=["All", "Closed", "Open"].index(default_status), key="__sb_status"
    )
    st.session_state[_KEY_STATUS] = selected_status


# ── Accessor helpers ─────────────────────────────────────────────────────────

def get_date_filter() -> tuple[date, date]:
    return (
        st.session_state.get(_KEY_DATE_START, _DEFAULT_START_DATE),
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
