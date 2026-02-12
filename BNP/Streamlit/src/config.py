"""Central configuration for the BNP SR Analytics dashboard."""

from pathlib import Path
from typing import Final

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = ROOT_DIR / "data"

# ── Extract file names ───────────────────────────────────────────────────────
EXTRACT_GLOBAL_STATS: Final[str] = "extract_global_stats.parquet"
EXTRACT_CATEGORY_KPIS: Final[str] = "extract_category_kpis.parquet"
EXTRACT_MONTHLY_CATEGORY_TRENDS: Final[str] = "extract_monthly_category_trends.parquet"
EXTRACT_MONTHLY_DESK_METRICS: Final[str] = "extract_monthly_desk_metrics.parquet"
EXTRACT_TREATMENT_TIME: Final[str] = "extract_treatment_time.parquet"
EXTRACT_SR_SAMPLE: Final[str] = "extract_sr_sample.parquet"

# ── Default date range for build_extracts ────────────────────────────────────
DEFAULT_START_DATE: Final[str] = "2024-01"
DEFAULT_END_DATE: Final[str] = "2025-09"

# ── Expected schemas (column → dtype string prefix) ─────────────────────────
SCHEMA_GLOBAL_STATS: Final[dict[str, str]] = {
    "month": "datetime",
    "total_sr": "int",
    "closed_sr": "int",
    "open_sr": "int",
    "avg_hours_to_close": "float",
    "avg_first_response_hours": "float",
    "closure_rate": "float",
    "sla_compliance": "float",
}

SCHEMA_CATEGORY_KPIS: Final[dict[str, str]] = {
    "category": "object",
    "total_sr": "int",
    "avg_hours_to_close": "float",
    "avg_first_response_hours": "float",
    "closure_rate": "float",
    "sla_compliance": "float",
}

SCHEMA_MONTHLY_CATEGORY_TRENDS: Final[dict[str, str]] = {
    "month": "datetime",
    "category": "object",
    "total_sr": "int",
    "avg_hours_to_close": "float",
    "closure_rate": "float",
}

SCHEMA_MONTHLY_DESK_METRICS: Final[dict[str, str]] = {
    "month": "datetime",
    "desk": "object",
    "total_sr": "int",
    "avg_hours_to_close": "float",
    "avg_first_response_hours": "float",
    "closure_rate": "float",
    "sla_compliance": "float",
}

SCHEMA_TREATMENT_TIME: Final[dict[str, str]] = {
    "category": "object",
    "total_sr": "int",
    "avg_hours": "float",
    "min_hours": "float",
    "max_hours": "float",
    "avg_days": "float",
}

SCHEMA_SR_SAMPLE: Final[dict[str, str]] = {
    "sr_id": "object",
    "category": "object",
    "desk": "object",
    "status": "object",
    "created_at": "datetime",
    "closed_at": "datetime",
    "hours_to_close": "float",
    "first_response_hours": "float",
    "sla_met": "object",
}

# ── Colour palette ───────────────────────────────────────────────────────────
COLOR_PRIMARY: Final[str] = "#00915A"   # BNP green
COLOR_SECONDARY: Final[str] = "#007A4D"
COLOR_ACCENT: Final[str] = "#E4002B"    # alert red
COLOR_NEUTRAL: Final[str] = "#4A4F55"
COLOR_LIGHT: Final[str] = "#F5F6F7"

PALETTE_SEQUENTIAL: Final[list[str]] = [
    "#E8F5E9", "#A5D6A7", "#66BB6A", "#2E7D32", "#1B5E20",
]
PALETTE_CATEGORICAL: Final[list[str]] = [
    "#00915A", "#007A4D", "#4A4F55", "#E4002B", "#0072CE",
    "#FFC107", "#8E24AA", "#00ACC1", "#FF7043", "#9E9E9E",
]

# ── Page config ──────────────────────────────────────────────────────────────
PAGE_ICON: Final[str] = "📊"
PAGE_TITLE: Final[str] = "BNP Paribas – SR Analytics"
