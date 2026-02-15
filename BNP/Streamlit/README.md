# BNP Paribas - SR Analytics Platform

Plateforme d'analyse construite pour le cas de conseil BNP Paribas, avec deux volets complementaires:

1. Dashboard Streamlit pour le pilotage executif des Service Requests.
2. Analyse approfondie de la base HOBART (SQL + notebooks + guides analytiques).

## Contributors

- Sacha Nardoux
- Anna Spira
- Keira Chang

## Scope du repository

Le repository combine:

- `BNP/Streamlit/`: application dashboard (lecture de fichiers Parquet)
- `Docs/`: cadre methodologique et guides analytiques
- `Notebook/`: analyses poussees, EDA et explorations SQL/Pandas
- `Data/`: jeux de donnees de travail (hors base brute 16 GB en versioning)

## Architecture cible

```text
HOBART SQLite (local)
        |
        | scripts/build_extracts.py
        v
Parquet extracts (BNP/Streamlit/data)
        |
        | src/data_loader.py (cache + validation schema)
        v
Streamlit app (app.py + pages/*)
```

Le dashboard ne se connecte pas directement a SQLite en production: il consomme uniquement les extracts Parquet versionnes.

## Architecture de l'application Streamlit

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

## Process d'extraction (SQLite -> Parquet)

Le script `scripts/build_extracts.py` suit un pipeline unique:

1. Chargement SQL depuis HOBART (`sr` + `category`) avec fenetre temporelle configurable.
2. Enrichissement metier (`month`, `hours_to_close`, `first_response_hours`, `is_closed`, `sla_met`, `status`).
3. Construction des datasets agreges par usage analytique.
4. Ecriture des extracts Parquet dans `BNP/Streamlit/data/`.

### Catalogue des extracts

| Extract | Niveau | Usage principal |
|---|---|---|
| `extract_global_stats.parquet` | Mensuel global | KPI executifs, volume, closure, SLA |
| `extract_category_kpis.parquet` | Categorie | Pareto, comparaison categories |
| `extract_monthly_category_trends.parquet` | Mois x Categorie | Evolution des categories |
| `extract_monthly_desk_metrics.parquet` | Mois x Desk | Benchmark desks |
| `extract_treatment_time.parquet` | Categorie (closed SR) | Analyse des temps de traitement |
| `extract_sr_sample.parquet` | SR niveau detail (sample) | Analyse ad hoc/notebooks |

## Runbook local

### 1) Regenerer les extracts

```bash
cd BNP/Streamlit

export HOBART_DB_PATH=/path/to/hobart_database.db
# Optionnel
export START_DATE=2024-01
export END_DATE=2025-09

python scripts/build_extracts.py
```

### 2) Lancer le dashboard

```bash
cd BNP/Streamlit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 3) Exploiter l'analyse poussee

- Guides methodologiques: `Docs/`
- Analyses exploratoires et deep dives: `Notebook/`
- Les hypotheses analytiques et conventions SQL sont documentees dans `Docs/ANALYSIS_GUIDE.md`.

## Regles d'evolution

Toute nouvelle metrique doit etre alignee sur les 3 couches:

1. Calcul dans `scripts/build_extracts.py`
2. Schema dans `src/config.py`
3. Exposition dans dashboard/notebook (`src/*` + `pages/*`)

## Go-live checklist

- [ ] Extraction offline terminee sans erreur
- [ ] Extracts Parquet actualises dans `BNP/Streamlit/data/`
- [ ] Dashboard fonctionnel (`streamlit run app.py`)
- [ ] Pages analytiques chargees et lisibles
- [ ] Exports CSV valides
- [ ] Guides `Docs/` et notebooks alignes avec la version des donnees
