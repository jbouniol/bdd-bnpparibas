"""Cached data loading and schema validation for Parquet extracts."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import (
    DATA_DIR,
    EXTRACT_CATEGORY_KPIS,
    EXTRACT_GLOBAL_STATS,
    EXTRACT_MONTHLY_CATEGORY_TRENDS,
    EXTRACT_MONTHLY_DESK_METRICS,
    EXTRACT_SR_SAMPLE,
    EXTRACT_TREATMENT_TIME,
    SCHEMA_CATEGORY_KPIS,
    SCHEMA_GLOBAL_STATS,
    SCHEMA_MONTHLY_CATEGORY_TRENDS,
    SCHEMA_MONTHLY_DESK_METRICS,
    SCHEMA_SR_SAMPLE,
    SCHEMA_TREATMENT_TIME,
)

logger = logging.getLogger(__name__)


# ── Schema validation ────────────────────────────────────────────────────────

def validate_schema(df: pd.DataFrame, schema: dict[str, str], name: str) -> pd.DataFrame:
    """Warn on missing columns and coerce types best-effort."""
    missing = [c for c in schema if c not in df.columns]
    if missing:
        st.warning(f"[{name}] Missing columns: {missing}. Some features may be unavailable.")
        logger.warning("Extract %s missing columns: %s", name, missing)
    for col, expected in schema.items():
        if col not in df.columns:
            continue
        if expected == "datetime":
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif expected == "float":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        elif expected == "int":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif expected == "object":
            df[col] = df[col].astype(str)
    return df


def _safe_read_parquet(path: Path, schema: dict[str, str], name: str) -> pd.DataFrame:
    """Read parquet file or return empty DataFrame with expected columns."""
    if not path.exists():
        st.error(f"Extract file not found: `{path.name}`. Run `scripts/build_extracts.py` first.")
        logger.error("File not found: %s", path)
        return pd.DataFrame(columns=list(schema.keys()))
    df = pd.read_parquet(path)
    return validate_schema(df, schema, name)


# ── Cached loaders ───────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Loading global stats…")
def load_global_stats() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_GLOBAL_STATS, SCHEMA_GLOBAL_STATS, "global_stats"
    )


@st.cache_data(ttl=3600, show_spinner="Loading category KPIs…")
def load_category_kpis() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_CATEGORY_KPIS, SCHEMA_CATEGORY_KPIS, "category_kpis"
    )


@st.cache_data(ttl=3600, show_spinner="Loading category trends…")
def load_monthly_category_trends() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_MONTHLY_CATEGORY_TRENDS,
        SCHEMA_MONTHLY_CATEGORY_TRENDS,
        "monthly_category_trends",
    )


@st.cache_data(ttl=3600, show_spinner="Loading desk metrics…")
def load_monthly_desk_metrics() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_MONTHLY_DESK_METRICS,
        SCHEMA_MONTHLY_DESK_METRICS,
        "monthly_desk_metrics",
    )


@st.cache_data(ttl=3600, show_spinner="Loading treatment times…")
def load_treatment_time() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_TREATMENT_TIME, SCHEMA_TREATMENT_TIME, "treatment_time"
    )


@st.cache_data(ttl=3600, show_spinner="Loading SR sample…")
def load_sr_sample() -> pd.DataFrame:
    return _safe_read_parquet(
        DATA_DIR / EXTRACT_SR_SAMPLE, SCHEMA_SR_SAMPLE, "sr_sample"
    )


# ── Convenience: distinct values for filters ─────────────────────────────────

@st.cache_data(ttl=3600)
def get_distinct_desks() -> list[str]:
    df = load_monthly_desk_metrics()
    if "desk" in df.columns:
        return sorted(df["desk"].dropna().unique().tolist())
    return []


@st.cache_data(ttl=3600)
def get_distinct_categories() -> list[str]:
    df = load_category_kpis()
    if "category" in df.columns:
        return sorted(df["category"].dropna().unique().tolist())
    return []


@st.cache_data(ttl=3600)
def get_date_range() -> tuple[pd.Timestamp, pd.Timestamp]:
    df = load_global_stats()
    if "month" in df.columns and not df.empty:
        return df["month"].min(), df["month"].max()
    return pd.Timestamp("2024-01-01"), pd.Timestamp("2025-09-01")
