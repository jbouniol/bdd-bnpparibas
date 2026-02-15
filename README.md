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

- `BNP/Streamlit/`: dashboard application (direct SQLite queries)
- `Docs/`: methodology and analytical guides
- `Notebook/`: deep-dive analyses, EDA, and SQL/Pandas exploration
- `Data/`: source datasets, including `Data/Processed/hobart_database.db`

## Target Architecture

```text
HOBART SQLite (local)
        |
        | BNP/Streamlit/src/data_loader.py
        |  - SQL queries
        |  - temporary SQL views
        |  - Streamlit cache
        v
Streamlit app (BNP/Streamlit/app.py + BNP/Streamlit/pages/*)
```

The dashboard reads directly from `hobart_database.db`.

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
`- requirements.txt
```

## Database Access

By default the app reads:

- `Data/Processed/hobart_database.db`

You can override the path with:

```bash
export HOBART_DB_PATH=/path/to/hobart_database.db
```

## Local Runbook

### 1) Run the dashboard

```bash
cd BNP/Streamlit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 2) Use advanced analysis assets

- Methodology guides: `Docs/`
- Exploratory and deep-dive analyses: `Notebook/`
- SQL conventions and analysis assumptions: `Docs/ANALYSIS_GUIDE.md`

## Change Rules

Any new metric should be aligned across three layers:

1. SQL logic in `BNP/Streamlit/src/data_loader.py` (queries/views)
2. Schema definition in `BNP/Streamlit/src/config.py`
3. Exposure in dashboard/notebooks (`BNP/Streamlit/src/*`, `BNP/Streamlit/pages/*`)

## Go-Live Checklist

- [ ] `HOBART_DB_PATH` points to a valid SQLite file
- [ ] Dashboard runs locally (`streamlit run app.py`)
- [ ] Analysis pages load correctly
- [ ] CSV exports are valid
- [ ] `Docs/` and notebooks are aligned with the current dataset version
