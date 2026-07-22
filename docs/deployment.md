# ForecastIQ — Deployment

The app **self-provisions**: on first start it builds the warehouse if it's missing, so it runs anywhere
with **zero manual steps** — including a fresh clone on Streamlit Community Cloud where the dataset is absent.

## Data provisioning — the decision

The source dataset (Global Superstore) is **git-ignored and never committed**: its licensing (a Kaggle
re-upload of a Tableau sample) does not explicitly permit redistribution, so committing it — raw or as a
derived database — is avoided. A fresh clone therefore has no data.

To keep the deployed demo runnable and licensing-clean, ForecastIQ resolves its data source at startup
(`forecastiq.bootstrap.ensure_warehouse`):

| Condition | Behaviour | Data mode |
|-----------|-----------|-----------|
| Warehouse (`forecastiq.db`) already exists | use it as-is | `existing` |
| Real dataset present at `data/raw/Global Superstore.xls` | build ETL + forecasts from it | `real` |
| No dataset present | **generate a synthetic sample workbook**, then build from it | `sample` |

The synthetic sample is fully generated (deterministic, ~1,960 rows, 36 months, 3 categories, 3 markets,
6 regions, returns, managers) — enough to exercise every page and the forecasting engine. The app shows a
clear **"Demo on generated sample data"** banner in that mode. Drop the real `.xls` in `data/raw/` (or mount
it) to see actual Global Superstore figures. This keeps the repo free of copyrighted data while guaranteeing
a working demo.

Bootstrap runs **once** per process (cached with `st.cache_resource`); first load takes ~10–15 s while the
warehouse builds, then every page is instant.

## Run locally
```bash
pip install -e ".[app]"          # or: pip install -r requirements.txt
streamlit run app/app.py         # http://localhost:8501  (builds the warehouse on first run)
```
Add `data/raw/Global Superstore.xls` first for real figures; otherwise it starts on generated sample data.

## Streamlit Community Cloud  ✅ zero-touch
1. Push the repo to GitHub (already public).
2. On <https://share.streamlit.io> → **New app** → repo `vinayakarya02/ForecastIQ`, branch `main`,
   **main file `app/app.py`**.
3. Deploy. Streamlit installs `requirements.txt`, runs `app/app.py`, and the app **builds a sample warehouse
   on first load automatically** — no dataset upload, no build step, no secrets required.

Optional: to serve real figures, add the dataset to the repo/storage or point `FORECASTIQ_DB_URL`
(via `.streamlit/secrets.toml`, see `secrets.toml.example`) at a hosted database.

## Docker
```bash
docker build -t forecastiq .
docker run -p 8501:8501 forecastiq                       # starts on generated sample data
docker run -p 8501:8501 -v "$(pwd)/data:/app/data" forecastiq   # uses your dataset if mounted
```
The entrypoint runs `pipelines/bootstrap.py` (builds the warehouse if missing) then launches Streamlit.

## Configuration
| Setting | Where | Default |
|---------|-------|---------|
| Theme, server flags | `.streamlit/config.toml` | brand theme, headless, XSRF on |
| Database URL | `FORECASTIQ_DB_URL` env / secret | `sqlite:///forecastiq.db` (project root) |
| Data source path | `FORECASTIQ_SOURCE_PATH` env / `config.yaml` | `data/raw/Global Superstore.xls` |

All paths resolve relative to the project root (computed from the package location), so the app is
CWD-independent. Secrets (`.streamlit/secrets.toml`) are git-ignored.

## Health & smoke test
- Health endpoint: `GET /_stcore/health` → `200`.
- Manual bootstrap: `python pipelines/bootstrap.py` → prints `Warehouse ready (…​ data).`
- Page smoke tests: `pytest tests/test_app_pages.py` (renders all 10 pages via Streamlit's AppTest).
