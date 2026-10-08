# Custody Operations Analytics: portfolio starter kit

Fictional data and starter scripts for a seven-project data analyst portfolio
(SQL, requirements, Alteryx, Power BI, Power Automate, Dataiku, and a super fund capstone).
**Every name, code and number in this repo is made up.**

## Quick start (Mac)

```bash
# 1. Python packages
python3 -m pip install pandas numpy openpyxl reportlab

# 2. Generate the data (same seed = same data every time)
python3 data_generator/generate_data.py
python3 data_generator/make_notices.py

# 3. Database (Postgres.app running, then from this folder)
createdb custody
psql -d custody -f sql/01_schema.sql
psql -d custody -f sql/02_load.sql
psql -d custody -f sql/03_data_quality_checks.sql
psql -d custody -f sql/04_business_questions.sql
psql -d custody -f sql/05_reconciliation.sql
psql -d custody -f sql/06_exports.sql
psql -d custody -f sql/07_p7_anomalies.sql   # Project 7, Stage D
```

## What's where

| Folder | Contents | Used in |
| --- | --- | --- |
| `data/` | Clients, accounts, securities, trades, settlements, prices, positions | Projects 1, 3, 4, 6 |
| `data/fund_manager_positions.xlsx`, `data/ticker_isin_map.csv` | The "other side" of the reconciliation, deliberately in a different format | Projects 3, 6 |
| `data/_injected_issues.csv` | **Answer key**: every data problem planted on purpose | All |
| `sql/` | Schema, load, data-quality checks, business questions, reconciliation, exports | Project 1 |
| `exports/` | Clean CSVs for Power BI (created by `06_exports.sql`) | Project 4 |
| `project7/` | Super fund transition and data-hub files, notice PDFs, notice answer key | Project 7 |
| `docs/` | Templates: requirements pack, workflow standards, rules catalogue | Projects 2, 3, 7 |

## Expected results (checkpoints)

| Check | Expected |
| --- | --- |
| Rows in `trades` | 10,015 (10,000 trades + 15 duplicates) |
| DQ01–DQ06 failures | 4, 15, 8, 10, 6, 5 |
| Position reconciliation | 847 matched, 26 quantity breaks, 8 missing at client, 8 missing at custodian |
| Highest fail-rate counterparties | Broker C (8.9%), Broker H (6.6%) |
