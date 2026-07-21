# ForecastIQ — Installation & Setup

## Prerequisites
- Python 3.10+ (developed on 3.11)
- Git
- Power BI Desktop (Windows) for the dashboard — optional
- ~200 MB free disk space

## 1. Clone & environment
```bash
git clone https://github.com/vinayakarya02/ForecastIQ.git
cd ForecastIQ

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Get the dataset (real data — not generated)
1. Download **Global Superstore** from Kaggle:
   <https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset>
2. Save the workbook to:
   ```
   data/raw/Global Superstore.xls        # sheets: Orders, People, Returns
   ```
   The `.xls` reader (`xlrd`) is installed by `requirements.txt`. Config already points here
   (`source.type: excel`). To use a CSV instead, set `source.type: csv` and `paths.raw_csv`.
3. If your column names differ, edit `etl.column_map` in `config/config.yaml`. No code changes needed.

## 3. Configure (optional)
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
Defaults use SQLite (`forecastiq.db` in the project root). To use PostgreSQL, set `FORECASTIQ_DB_URL`
and `pip install psycopg2-binary`.

## 4. Run the pipelines
```bash
# ETL: raw CSV -> validated star-schema warehouse
python pipelines/run_etl.py

# Forecasting: backtest models, select best, persist forecasts
python pipelines/run_forecast.py --granularity monthly --horizon 6
```
Outputs: `forecastiq.db`, plus CSVs/figures under `reports/`.

## 5. (Optional) API
```bash
uvicorn forecastiq.api.main:app --reload
# open http://localhost:8000/docs
```

## 6. (Optional) Power BI
Open Power BI Desktop → **Get Data** → SQLite/ODBC (or import the exported CSVs) → build the report using
[`../powerbi/README.md`](../powerbi/README.md).

## Troubleshooting
| Symptom | Fix |
|--------|-----|
| `FileNotFoundError: data/raw/...` | Dataset not placed — see step 2 |
| Date parsing looks wrong | Toggle `etl.dayfirst` in `config.yaml` |
| Validation `FAIL` aborts run | Read the printed report; fix source data or adjust thresholds |
| `prophet`/`xgboost` import error | They're optional; keep them disabled in config or `pip install` them |
