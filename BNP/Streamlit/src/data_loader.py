"""Cached data loading and schema validation for SQLite-backed datasets."""

from __future__ import annotations

import logging
import sqlite3

import pandas as pd
import streamlit as st

from src.config import (
    HOBART_DB_PATH,
    SCHEMA_CATEGORY_KPIS,
    SCHEMA_GLOBAL_STATS,
    SCHEMA_MONTHLY_CATEGORY_TRENDS,
    SCHEMA_MONTHLY_DESK_METRICS,
    SCHEMA_SR_SAMPLE,
    SCHEMA_TREATMENT_TIME,
)

logger = logging.getLogger(__name__)


def validate_schema(df: pd.DataFrame, schema: dict[str, str], name: str) -> pd.DataFrame:
    """Warn on missing columns and coerce expected types."""
    missing = [c for c in schema if c not in df.columns]
    if missing:
        st.warning(f"[{name}] Missing columns: {missing}. Some features may be unavailable.")
        logger.warning("Dataset %s missing columns: %s", name, missing)
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


def _prepare_temp_views(conn: sqlite3.Connection) -> None:
    """Create temporary views used by dashboard queries."""
    conn.executescript(
        """
        CREATE TEMP VIEW IF NOT EXISTS dashboard_sr_enriched_v AS
        SELECT
            sr.ID AS sr_id,
            sr.SRNUMBER AS sr_number,
            COALESCE(c.NAME, 'Unknown (' || sr.CATEGORY_ID || ')') AS category,
            CAST(sr.JUR_DESK_ID AS TEXT) AS desk,
            sr.CREATIONDATE AS created_at,
            sr.CLOSINGDATE AS closed_at,
            sr.EXPIRATION_DATE AS expiration_date,
            sr.ACKNOWLEDGE_DATE AS first_response_at,
            DATE(sr.CREATIONDATE, 'start of month') AS month,
            (JULIANDAY(sr.CLOSINGDATE) - JULIANDAY(sr.CREATIONDATE)) * 24.0 AS hours_to_close,
            (JULIANDAY(sr.ACKNOWLEDGE_DATE) - JULIANDAY(sr.CREATIONDATE)) * 24.0 AS first_response_hours,
            CASE WHEN sr.CLOSINGDATE IS NOT NULL THEN 1 ELSE 0 END AS is_closed,
            CASE
                WHEN sr.CLOSINGDATE IS NOT NULL
                    AND sr.EXPIRATION_DATE IS NOT NULL
                    AND sr.CLOSINGDATE <= sr.EXPIRATION_DATE THEN 1
                WHEN sr.CLOSINGDATE IS NOT NULL
                    AND sr.EXPIRATION_DATE IS NOT NULL
                    AND sr.CLOSINGDATE > sr.EXPIRATION_DATE THEN 0
                ELSE NULL
            END AS sla_met,
            CASE WHEN sr.CLOSINGDATE IS NOT NULL THEN 'Closed' ELSE 'Open' END AS status
        FROM sr
        LEFT JOIN category c ON sr.CATEGORY_ID = c.ID
        WHERE sr.CREATIONDATE IS NOT NULL;
        """
    )


def _query_sql(sql: str, schema: dict[str, str], name: str, params: tuple | None = None) -> pd.DataFrame:
    """Run a SQL query and apply schema validation."""
    if not HOBART_DB_PATH.exists():
        st.error(f"Database file not found: `{HOBART_DB_PATH}`")
        logger.error("Database not found: %s", HOBART_DB_PATH)
        return pd.DataFrame(columns=list(schema.keys()))

    try:
        with sqlite3.connect(str(HOBART_DB_PATH)) as conn:
            _prepare_temp_views(conn)
            df = pd.read_sql_query(sql, conn, params=params)
        return validate_schema(df, schema, name)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to query `{name}` from database.")
        logger.exception("SQL query failed for %s: %s", name, exc)
        return pd.DataFrame(columns=list(schema.keys()))


@st.cache_data(ttl=3600, show_spinner="Loading global stats from database...")
def load_global_stats() -> pd.DataFrame:
    sql = """
        SELECT
            month,
            COUNT(*) AS total_sr,
            SUM(is_closed) AS closed_sr,
            COUNT(*) - SUM(is_closed) AS open_sr,
            AVG(hours_to_close) AS avg_hours_to_close,
            AVG(first_response_hours) AS avg_first_response_hours,
            ROUND(SUM(is_closed) * 100.0 / COUNT(*), 2) AS closure_rate,
            ROUND(AVG(sla_met) * 100.0, 2) AS sla_compliance
        FROM dashboard_sr_enriched_v
        GROUP BY month
        ORDER BY month
    """
    return _query_sql(sql, SCHEMA_GLOBAL_STATS, "global_stats")


@st.cache_data(ttl=3600, show_spinner="Loading category KPIs from database...")
def load_category_kpis() -> pd.DataFrame:
    sql = """
        SELECT
            category,
            COUNT(*) AS total_sr,
            AVG(hours_to_close) AS avg_hours_to_close,
            AVG(first_response_hours) AS avg_first_response_hours,
            ROUND(SUM(is_closed) * 100.0 / COUNT(*), 2) AS closure_rate,
            ROUND(AVG(sla_met) * 100.0, 2) AS sla_compliance
        FROM dashboard_sr_enriched_v
        GROUP BY category
        ORDER BY total_sr DESC
    """
    return _query_sql(sql, SCHEMA_CATEGORY_KPIS, "category_kpis")


@st.cache_data(ttl=3600, show_spinner="Loading category trends from database...")
def load_monthly_category_trends() -> pd.DataFrame:
    sql = """
        SELECT
            month,
            category,
            COUNT(*) AS total_sr,
            AVG(hours_to_close) AS avg_hours_to_close,
            ROUND(SUM(is_closed) * 100.0 / COUNT(*), 2) AS closure_rate
        FROM dashboard_sr_enriched_v
        GROUP BY month, category
        ORDER BY month, total_sr DESC
    """
    return _query_sql(sql, SCHEMA_MONTHLY_CATEGORY_TRENDS, "monthly_category_trends")


@st.cache_data(ttl=3600, show_spinner="Loading desk metrics from database...")
def load_monthly_desk_metrics() -> pd.DataFrame:
    sql = """
        SELECT
            month,
            desk,
            COUNT(*) AS total_sr,
            AVG(hours_to_close) AS avg_hours_to_close,
            AVG(first_response_hours) AS avg_first_response_hours,
            ROUND(SUM(is_closed) * 100.0 / COUNT(*), 2) AS closure_rate,
            ROUND(AVG(sla_met) * 100.0, 2) AS sla_compliance
        FROM dashboard_sr_enriched_v
        GROUP BY month, desk
        ORDER BY month, desk
    """
    return _query_sql(sql, SCHEMA_MONTHLY_DESK_METRICS, "monthly_desk_metrics")


@st.cache_data(ttl=3600, show_spinner="Loading treatment times from database...")
def load_treatment_time() -> pd.DataFrame:
    sql = """
        SELECT
            category,
            COUNT(*) AS total_sr,
            AVG(hours_to_close) AS avg_hours,
            MIN(hours_to_close) AS min_hours,
            MAX(hours_to_close) AS max_hours,
            ROUND(AVG(hours_to_close) / 24.0, 1) AS avg_days
        FROM dashboard_sr_enriched_v
        WHERE is_closed = 1 AND hours_to_close IS NOT NULL
        GROUP BY category
        HAVING COUNT(*) > 100
        ORDER BY avg_hours DESC
    """
    return _query_sql(sql, SCHEMA_TREATMENT_TIME, "treatment_time")


@st.cache_data(ttl=3600, show_spinner="Loading SR sample from database...")
def load_sr_sample(max_rows: int = 50_000) -> pd.DataFrame:
    sql = """
        SELECT
            sr_id,
            sr_number,
            category,
            desk,
            status,
            created_at,
            closed_at,
            hours_to_close,
            first_response_hours,
            sla_met
        FROM dashboard_sr_enriched_v
        ORDER BY created_at DESC
        LIMIT ?
    """
    return _query_sql(sql, SCHEMA_SR_SAMPLE, "sr_sample", params=(max_rows,))


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
    return pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-01")
