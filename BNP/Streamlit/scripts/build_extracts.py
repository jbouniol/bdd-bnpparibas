#!/usr/bin/env python3
"""Offline script: reads hobart_database.db and produces Parquet extracts.

Usage:
    HOBART_DB_PATH=/path/to/hobart_database.db python scripts/build_extracts.py

Optional env vars:
    START_DATE  – first month (format: YYYY-MM, optional)
    END_DATE    – last month  (format: YYYY-MM, optional)
"""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# ── Config ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger("build_extracts")

DB_PATH = os.environ.get("HOBART_DB_PATH", "hobart_database.db")
START_DATE = os.environ.get("START_DATE")
END_DATE = os.environ.get("END_DATE")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Load raw data with proper JOINs ─────────────────────────────────────────

def _load_raw(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load SR data with category names, computing SLA from EXPIRATION_DATE."""
    where_clause = ""
    params: list[str] = []
    if START_DATE and END_DATE:
        where_clause = "WHERE strftime('%Y-%m', sr.CREATIONDATE) BETWEEN ? AND ?"
        params = [START_DATE, END_DATE]
        log.info("Executing query with date range: %s -> %s", START_DATE, END_DATE)
    elif START_DATE:
        where_clause = "WHERE strftime('%Y-%m', sr.CREATIONDATE) >= ?"
        params = [START_DATE]
        log.info("Executing query with lower bound: %s", START_DATE)
    elif END_DATE:
        where_clause = "WHERE strftime('%Y-%m', sr.CREATIONDATE) <= ?"
        params = [END_DATE]
        log.info("Executing query with upper bound: %s", END_DATE)
    else:
        log.info("Executing query with no date filter (full available history).")

    sql = f"""
        SELECT
            sr.ID                AS sr_id,
            sr.SRNUMBER          AS sr_number,
            COALESCE(c.NAME, 'Unknown (' || sr.CATEGORY_ID || ')') AS category,
            sr.JUR_DESK_ID       AS desk,
            sr.STATUS_ID         AS status_id,
            sr.CREATIONDATE      AS created_at,
            sr.CLOSINGDATE       AS closed_at,
            sr.EXPIRATION_DATE   AS expiration_date,
            sr.ACKNOWLEDGE_DATE  AS first_response_at
        FROM sr
        LEFT JOIN category c ON sr.CATEGORY_ID = c.ID
        {where_clause}
    """
    df = pd.read_sql(sql, conn, params=params)
    log.info("Loaded %s rows", f"{len(df):,}")
    return df


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates and compute derived columns."""
    for col in ["created_at", "closed_at", "expiration_date", "first_response_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["month"] = df["created_at"].dt.to_period("M").dt.to_timestamp()

    # Hours to close
    df["hours_to_close"] = (
        (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600
    )

    # First response hours (from ACKNOWLEDGE_DATE)
    df["first_response_hours"] = (
        (df["first_response_at"] - df["created_at"]).dt.total_seconds() / 3600
    )

    # Is closed: based on closed_at being present
    df["is_closed"] = df["closed_at"].notna()

    # SLA met: closed before expiration date
    both_present = df["closed_at"].notna() & df["expiration_date"].notna()
    df["sla_met"] = pd.array([None] * len(df), dtype=pd.BooleanDtype())
    df.loc[both_present, "sla_met"] = (
        df.loc[both_present, "closed_at"] <= df.loc[both_present, "expiration_date"]
    )

    # Desk as string (no lookup table available – prefix with "Desk ")
    df["desk"] = df["desk"].astype(str)

    # Status label from closed_at
    df["status"] = df["is_closed"].map({True: "Closed", False: "Open"})

    return df


# ── Extract builders ─────────────────────────────────────────────────────────

def build_global_stats(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("month").agg(
        total_sr=("sr_id", "count"),
        closed_sr=("is_closed", "sum"),
        avg_hours_to_close=("hours_to_close", "mean"),
        avg_first_response_hours=("first_response_hours", "mean"),
    ).reset_index()
    g["open_sr"] = g["total_sr"] - g["closed_sr"]
    g["closure_rate"] = (g["closed_sr"] / g["total_sr"] * 100).round(2)

    # SLA compliance per month
    sla_df = df.dropna(subset=["sla_met"])
    if not sla_df.empty:
        sla = sla_df.groupby("month")["sla_met"].mean().reset_index()
        sla.columns = ["month", "sla_compliance"]
        sla["sla_compliance"] = (sla["sla_compliance"] * 100).round(2)
        g = g.merge(sla, on="month", how="left")
    else:
        g["sla_compliance"] = None

    return g


def build_category_kpis(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("category").agg(
        total_sr=("sr_id", "count"),
        avg_hours_to_close=("hours_to_close", "mean"),
        avg_first_response_hours=("first_response_hours", "mean"),
        closed=("is_closed", "sum"),
    ).reset_index()
    g["closure_rate"] = (g["closed"] / g["total_sr"] * 100).round(2)

    sla_df = df.dropna(subset=["sla_met"])
    if not sla_df.empty:
        sla = sla_df.groupby("category")["sla_met"].mean().reset_index()
        sla.columns = ["category", "sla_compliance"]
        sla["sla_compliance"] = (sla["sla_compliance"] * 100).round(2)
        g = g.merge(sla, on="category", how="left")
    else:
        g["sla_compliance"] = None

    return g.drop(columns=["closed"])


def build_monthly_category_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly trends for ALL categories (pages will filter top N)."""
    g = df.groupby(["month", "category"]).agg(
        total_sr=("sr_id", "count"),
        avg_hours_to_close=("hours_to_close", "mean"),
        closed=("is_closed", "sum"),
    ).reset_index()
    g["closure_rate"] = (g["closed"] / g["total_sr"] * 100).round(2)
    return g.drop(columns=["closed"])


def build_monthly_desk_metrics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["month", "desk"]).agg(
        total_sr=("sr_id", "count"),
        avg_hours_to_close=("hours_to_close", "mean"),
        avg_first_response_hours=("first_response_hours", "mean"),
        closed=("is_closed", "sum"),
    ).reset_index()
    g["closure_rate"] = (g["closed"] / g["total_sr"] * 100).round(2)

    sla_df = df.dropna(subset=["sla_met"])
    if not sla_df.empty:
        sla = (
            sla_df.groupby(["month", "desk"])["sla_met"]
            .mean()
            .reset_index()
        )
        sla.columns = ["month", "desk", "sla_compliance"]
        sla["sla_compliance"] = (sla["sla_compliance"] * 100).round(2)
        g = g.merge(sla, on=["month", "desk"], how="left")
    else:
        g["sla_compliance"] = None

    return g.drop(columns=["closed"])


def build_treatment_time_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Top categories by average treatment time (categories with > 100 SRs)."""
    closed_df = df[df["is_closed"] & df["hours_to_close"].notna()].copy()
    g = closed_df.groupby("category").agg(
        total_sr=("sr_id", "count"),
        avg_hours=("hours_to_close", "mean"),
        min_hours=("hours_to_close", "min"),
        max_hours=("hours_to_close", "max"),
    ).reset_index()
    g = g[g["total_sr"] > 100]
    g["avg_days"] = (g["avg_hours"] / 24).round(1)
    g = g.sort_values("avg_hours", ascending=False).reset_index(drop=True)
    return g


def build_sr_sample(df: pd.DataFrame, max_rows: int = 50_000) -> pd.DataFrame:
    cols = [
        "sr_id", "sr_number", "category", "desk", "status", "created_at",
        "closed_at", "hours_to_close", "first_response_hours", "sla_met",
    ]
    available = [c for c in cols if c in df.columns]
    sample = df[available]
    if len(sample) > max_rows:
        sample = sample.sample(n=max_rows, random_state=42)
        log.info("SR sample capped to %s rows", f"{max_rows:,}")
    return sample.reset_index(drop=True)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not Path(DB_PATH).exists():
        log.error("Database not found at: %s", DB_PATH)
        log.error("Set HOBART_DB_PATH env var to the correct path.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    try:
        raw = _load_raw(conn)
        df = _enrich(raw)

        extracts = {
            "extract_global_stats.parquet": build_global_stats(df),
            "extract_category_kpis.parquet": build_category_kpis(df),
            "extract_monthly_category_trends.parquet": build_monthly_category_trends(df),
            "extract_monthly_desk_metrics.parquet": build_monthly_desk_metrics(df),
            "extract_treatment_time.parquet": build_treatment_time_by_category(df),
            "extract_sr_sample.parquet": build_sr_sample(df),
        }

        for filename, data in extracts.items():
            path = OUTPUT_DIR / filename
            data.to_parquet(path, index=False)
            log.info(
                "Wrote %s  (%s rows, %.1f KB)",
                filename, f"{len(data):,}", path.stat().st_size / 1024,
            )

        log.info("All extracts written to %s", OUTPUT_DIR)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
