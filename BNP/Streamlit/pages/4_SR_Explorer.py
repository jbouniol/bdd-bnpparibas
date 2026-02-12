"""Page 4 – SR Explorer: search, paginated table, detail panel, timeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import PAGE_ICON, PAGE_TITLE
from src.data_loader import load_sr_sample
from src.filters import apply_all_filters, render_sidebar_filters
from src.metrics import format_hours
from src.ui import (
    page_header,
    render_dataframe_with_download,
    render_paginated_table,
    show_empty_state,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{PAGE_TITLE} – SR Explorer", page_icon=PAGE_ICON, layout="wide")
render_sidebar_filters()

# ── Header ───────────────────────────────────────────────────────────────────
page_header("SR Explorer", "Search and inspect individual service requests")

# ── Data ─────────────────────────────────────────────────────────────────────
sr_df = apply_all_filters(
    load_sr_sample(),
    date_col="created_at",
    desk_col="desk",
    category_col="category",
    status_col="status",
)

if sr_df.empty:
    show_empty_state("No SR data found. Adjust filters or generate extracts.")
    st.stop()

# ── Search ───────────────────────────────────────────────────────────────────
search_query = st.text_input("Search SR ID", placeholder="e.g. SR-12345", key="sr_search")

if search_query:
    mask = sr_df["sr_id"].astype(str).str.contains(search_query, case=False, na=False)
    if "sr_number" in sr_df.columns:
        mask = mask | sr_df["sr_number"].astype(str).str.contains(search_query, case=False, na=False)
    sr_df = sr_df[mask]
    if sr_df.empty:
        show_empty_state(f"No SR matching '{search_query}'.")
        st.stop()

st.markdown(f"**{len(sr_df):,}** service requests found.")

# ── Paginated table ──────────────────────────────────────────────────────────
visible = render_paginated_table(sr_df, page_size=25, key_prefix="sr_table")

# ── Download ─────────────────────────────────────────────────────────────────
render_dataframe_with_download(sr_df, label="Download Filtered SRs", key="sr_download")

st.divider()

# ── Detail panel ─────────────────────────────────────────────────────────────
st.markdown("### SR Detail")

if "sr_id" in sr_df.columns:
    sr_ids = sr_df["sr_id"].tolist()
    selected_id = st.selectbox("Select SR", sr_ids, key="sr_detail_select")

    if selected_id:
        row = sr_df[sr_df["sr_id"] == selected_id].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**SR ID:** `{row.get('sr_id', '—')}`")
            st.markdown(f"**Category:** {row.get('category', '—')}")
            st.markdown(f"**Desk:** {row.get('desk', '—')}")
        with col2:
            st.markdown(f"**Status:** {row.get('status', '—')}")
            sla_raw = row.get("sla_met")
            if pd.notna(sla_raw):
                sla_label = "Yes" if sla_raw else "No"
            else:
                sla_label = "—"
            st.markdown(f"**SLA Met:** {sla_label}")
        with col3:
            created = row.get("created_at")
            closed = row.get("closed_at")
            st.markdown(f"**Created:** {created.strftime('%Y-%m-%d %H:%M') if pd.notna(created) else '—'}")
            st.markdown(f"**Closed:** {closed.strftime('%Y-%m-%d %H:%M') if pd.notna(closed) else '—'}")
            st.markdown(f"**Time to Close:** {format_hours(row.get('hours_to_close'))}")
            st.markdown(f"**1st Response:** {format_hours(row.get('first_response_hours'))}")

        # ── Mini timeline ────────────────────────────────────────────────────
        st.markdown("#### Timeline")
        events: list[tuple[str, pd.Timestamp | None]] = [
            ("Created", created),
            ("Closed", closed),
        ]
        first_resp_hours = row.get("first_response_hours")
        if pd.notna(created) and pd.notna(first_resp_hours):
            events.append(("First Response", created + pd.Timedelta(hours=first_resp_hours)))

        events = [(label, ts) for label, ts in events if pd.notna(ts)]
        events.sort(key=lambda x: x[1])

        if events:
            timeline_df = pd.DataFrame(events, columns=["Event", "Timestamp"])
            timeline_df["Timestamp"] = timeline_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            st.table(timeline_df)
        else:
            st.caption("No timeline data available.")
else:
    show_empty_state("SR ID column not available.")
