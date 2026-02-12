# BNP Paribas – SR Analytics Dashboard

Streamlit multipage dashboard for diagnosing client service request pain points: volume, resolution delays, desk performance, and category analysis.

---

## Architecture

```
Streamlit/
├── app.py                          # Entry point (landing page + sidebar)
├── pages/
│   ├── 1_Executive_Overview.py     # KPIs, monthly trends, scatter
│   ├── 2_Category_Deep_Dive.py     # Table, Pareto, category trend
│   ├── 3_Desk_Benchmark.py         # Ranking, heatmap, outliers
│   └── 4_SR_Explorer.py            # Search, paginated table, detail
├── src/
│   ├── config.py                   # Paths, schemas, colours
│   ├── data_loader.py              # Cached Parquet loaders + validation
│   ├── filters.py                  # Sidebar filters (session_state)
│   ├── metrics.py                  # KPI computation, formatting, outliers
│   ├── charts.py                   # Plotly chart factories
│   └── ui.py                       # Reusable UI components
├── scripts/
│   └── build_extracts.py           # Offline: DB → Parquet extracts
├── data/                           # Parquet extracts (git-tracked)
├── .streamlit/config.toml          # Theme & server config
└── requirements.txt
```

---

## 1. Generate the Parquet extracts

The 16 GB Hobart SQLite database is **never** uploaded to the repo or used online. Instead, a one-time offline script produces lightweight pre-aggregated Parquet files.

```bash
# Set the path to the database
export HOBART_DB_PATH=/path/to/hobart_database.db

# Optional: override the date range (defaults: 2024-01 → 2025-09)
export START_DATE=2024-01
export END_DATE=2025-09

# Run from the Streamlit/ directory
cd BNP/Streamlit
python scripts/build_extracts.py
```

This writes 5 files into `data/`:

| File | Description |
|------|-------------|
| `extract_global_stats.parquet` | Monthly aggregated KPIs |
| `extract_category_kpis.parquet` | Per-category summary |
| `extract_monthly_category_trends.parquet` | Monthly breakdown per category |
| `extract_monthly_desk_metrics.parquet` | Monthly breakdown per desk |
| `extract_sr_sample.parquet` | Raw SR sample (max 50 k rows) |

---

## 2. Run locally

```bash
cd BNP/Streamlit

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt

streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 3. Push to GitHub

```bash
cd BNP/Streamlit
git init
git add .
git commit -m "Initial dashboard commit"

# Create the repo on GitHub, then:
git remote add origin https://github.com/<your-org>/bnp-sr-analytics.git
git branch -M main
git push -u origin main
```

> The `.gitignore` already excludes `.db`, `__pycache__`, and virtual env folders.
> The `data/*.parquet` files **are** tracked — they are small enough for GitHub.

---

## 4. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select:
   - **Repository:** `<your-org>/bnp-sr-analytics`
   - **Branch:** `main`
   - **Main file path:** `BNP/Streamlit/app.py`
4. Click **Deploy**.

Streamlit Cloud will install `requirements.txt` and serve the app. No database or secrets needed — the app reads only the Parquet files committed to the repo.

---

## 5. Why the 16 GB database is not used online

| Concern | Solution |
|---------|----------|
| GitHub file size limit (100 MB) | Parquet extracts are < 10 MB total |
| Streamlit Cloud has no persistent storage | Static Parquet files in repo |
| Cold start speed | Cached reads of small Parquet files |
| Security | No credentials or connection strings needed |

The `build_extracts.py` script runs **once** on your local machine where the DB lives, producing portable extracts that contain only the aggregated data the dashboard needs.

---

## 6. Adding a new metric

Follow these steps to add a metric cleanly:

### a) Update the extract script
In `scripts/build_extracts.py`, add the computation in the relevant `build_*` function (e.g., `build_global_stats`).

### b) Update the schema
In `src/config.py`, add the new column to the matching `SCHEMA_*` dict with its expected dtype.

### c) Expose the metric in the loader
No changes needed if the column is in the Parquet — `data_loader.py` reads all columns and validates against the schema.

### d) Use in a page
- If it's a KPI: update `src/metrics.py` → `compute_header_kpis()` and `src/ui.py` → `render_kpi_row()`.
- If it's a chart axis: add or modify a chart factory in `src/charts.py`.
- If it's a filter dimension: add a new filter in `src/filters.py`.

### e) Regenerate extracts
```bash
HOBART_DB_PATH=/path/to/db python scripts/build_extracts.py
```
Commit the updated Parquet files and push.

---

## Go-Live Checklist

- [ ] `build_extracts.py` ran successfully — 5 Parquet files in `data/`
- [ ] `streamlit run app.py` works locally — all 4 pages load
- [ ] Sidebar filters work across all pages
- [ ] CSV download buttons produce valid files
- [ ] No `st.error` messages with the generated extracts
- [ ] `.gitignore` excludes `.db`, `.venv`, `__pycache__`
- [ ] Repo pushed to GitHub
- [ ] Streamlit Community Cloud deployment successful
- [ ] Landing page loads under 3 seconds on Cloud
- [ ] Shared URL tested with a colleague
