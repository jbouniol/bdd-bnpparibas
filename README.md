# BNP Paribas - SR Analytics Platform

Analytics platform built for the BNP Paribas consulting case, with two complementary tracks:

1. Streamlit dashboard for executive monitoring of Service Requests.
2. In-depth HOBART database analysis (SQL, notebooks, and analysis guides).

## Contributors

- Sacha Nardoux
- Anna Spira
- Keira Chang

## Repository Scope

This repository combines:

- `BNP/Streamlit/`: dashboard application (Parquet-based reads)
- `Docs/`: methodology and analytical guides
- `Notebook/`: deep-dive analyses, EDA, and SQL/Pandas exploration
- `Data/`: working datasets (excluding the 16 GB raw database from versioning)

## Target Architecture

```text
HOBART SQLite (local)
        |
        | BNP/Streamlit/scripts/build_extracts.py
        v
Parquet extracts (BNP/Streamlit/data)
        |
        | BNP/Streamlit/src/data_loader.py (cache + schema validation)
        v
Streamlit app (BNP/Streamlit/app.py + BNP/Streamlit/pages/*)
```

The dashboard does not connect directly to SQLite in production. It reads versioned Parquet extracts only.

## Streamlit Application Structure

```text
BNP/Streamlit/
|- app.py
|- pages/
|  |- 1_Executive_Overview.py
|  |- 2_Category_Deep_Dive.py
|  |- 3_Desk_Benchmark.py
|  `- 4_Analysis.py
|- src/
|  |- config.py
|  |- data_loader.py
|  |- filters.py
|  |- metrics.py
|  |- charts.py
|  `- ui.py
|- scripts/
|  `- build_extracts.py
|- data/
|  |- extract_global_stats.parquet
|  |- extract_category_kpis.parquet
|  |- extract_monthly_category_trends.parquet
|  |- extract_monthly_desk_metrics.parquet
|  |- extract_treatment_time.parquet
|  `- extract_sr_sample.parquet
`- requirements.txt
```

## Extraction Process (SQLite -> Parquet)

`BNP/Streamlit/scripts/build_extracts.py` runs a single pipeline:

1. SQL load from HOBART (`sr` + `category`) with optional date bounds.
2. Business enrichment (`month`, `hours_to_close`, `first_response_hours`, `is_closed`, `sla_met`, `status`).
3. Build aggregated datasets by analytical use case.
4. Write Parquet extracts to `BNP/Streamlit/data/`.

### Extract Catalog

| Extract | Grain | Primary Use |
|---|---|---|
| `extract_global_stats.parquet` | Monthly global | Executive KPIs, volume, closure, SLA |
| `extract_category_kpis.parquet` | Category | Pareto and category comparison |
| `extract_monthly_category_trends.parquet` | Month x Category | Category evolution |
| `extract_monthly_desk_metrics.parquet` | Month x Desk | Desk benchmark |
| `extract_treatment_time.parquet` | Category (closed SR) | Processing-time analysis |
| `extract_sr_sample.parquet` | SR-level sample | Ad hoc analysis / notebooks |

## Local Runbook

### 1) Regenerate extracts

```bash
cd BNP/Streamlit

export HOBART_DB_PATH=/path/to/hobart_database.db
# Optional
# export START_DATE=2025-01
# export END_DATE=2025-12

python scripts/build_extracts.py
```

### 2) Run the dashboard

```bash
cd BNP/Streamlit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 3) Use advanced analysis assets

- Methodology guides: `Docs/`
- Exploratory and deep-dive analyses: `Notebook/`
- SQL conventions and analysis assumptions: `Docs/ANALYSIS_GUIDE.md`

## Change Rules

Any new metric must be aligned across three layers:

1. Computation in `BNP/Streamlit/scripts/build_extracts.py`
2. Schema definition in `BNP/Streamlit/src/config.py`
3. Exposure in dashboard/notebooks (`BNP/Streamlit/src/*`, `BNP/Streamlit/pages/*`)

## Go-Live Checklist

- [ ] Offline extraction completes without errors
- [ ] Parquet extracts are updated in `BNP/Streamlit/data/`
- [ ] Dashboard runs locally (`streamlit run app.py`)
- [ ] Analysis pages load correctly
- [ ] CSV exports are valid
- [ ] `Docs/` and notebooks are aligned with the current dataset version
