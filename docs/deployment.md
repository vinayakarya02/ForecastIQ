# ForecastIQ — Deployment

The app **self-provisions**: on first start it builds the warehouse if it's missing, so it runs anywhere
with **zero manual steps** — including a fresh clone on Streamlit Community Cloud.

## Data provisioning

The real **Global Superstore** dataset is committed to the repo at `data/raw/Global Superstore.xls`
(Tableau's fictional demo dataset — no real company or personal data), so a fresh clone builds the **real**
warehouse automatically with no upload or configuration. A synthetic sample is kept only as a fallback for
the case where the dataset is genuinely missing.

The data source is resolved at startup (`forecastiq.bootstrap.ensure_warehouse`):

| Condition | Behaviour | Data mode |
|-----------|-----------|-----------|
| Warehouse (`forecastiq.db`) already exists | use it as-is (rebuilt from the dataset if it was a sample) | `existing` / `real` |
| Real dataset present at `data/raw/Global Superstore.xls` | build ETL + forecasts from it | `real` |
| No dataset present | generate a synthetic sample workbook, then build from it | `sample` |

Provenance is recorded in a `warehouse_meta` table. If a warehouse was ever built from the sample and the
real dataset later becomes available, it is **refreshed from the real data** on the next start. The
**"Demo on generated sample data"** banner appears only in `sample` mode — i.e. only when the dataset is
absent, which is not the case for the committed repo.

Bootstrap runs **once** per process (cached with `st.cache_resource`); first load takes ~10–15 s while the
warehouse builds, then every page is instant.

## Run locally
```bash
pip install -e ".[app]"          # or: pip install -r requirements.txt
streamlit run app/app.py         # http://localhost:8501  (builds the real warehouse on first run)
```

## Streamlit Community Cloud  ✅ zero-touch
1. Push the repo to GitHub (already public, dataset included).
2. On <https://share.streamlit.io> → **New app** → repo `vinayakarya02/ForecastIQ`, branch `main`,
   **main file `app/app.py`**.
3. Deploy. Streamlit installs `requirements.txt`, runs `app/app.py`, and the app **builds the real
   warehouse from the committed dataset on first load** — no upload, no build step, no secrets required.

To point at a hosted database instead of the on-disk SQLite file, set `FORECASTIQ_DB_URL`
(via `.streamlit/secrets.toml`, see `secrets.toml.example`).

## Docker
```bash
docker build -t forecastiq .
docker run -p 8501:8501 forecastiq                              # builds from the bundled dataset
docker run -p 8501:8501 -v "$(pwd)/data:/app/data" forecastiq   # or mount your own data/
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
- Manual bootstrap: `python pipelines/bootstrap.py` → prints `Warehouse source: …`.
- Page smoke tests: `pytest tests/test_app_pages.py` (renders all 10 pages via Streamlit's AppTest).
