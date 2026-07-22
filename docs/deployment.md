# ForecastIQ — Deployment

The app needs a built warehouse (`forecastiq.db`). Build it once, then serve the Streamlit app.

## Prerequisites
1. `pip install -r requirements.txt`
2. Place the dataset at `data/raw/Global Superstore.xls` (see [installation.md](installation.md)).
3. Build the warehouse + forecasts:
   ```bash
   python pipelines/run_etl.py
   python pipelines/run_forecast.py
   ```

## Run locally
```bash
streamlit run app/app.py
# opens http://localhost:8501
```

## Docker
The image auto-builds the warehouse on first start if the dataset is mounted.
```bash
docker build -t forecastiq .
docker run -p 8501:8501 \
  -v "$(pwd)/data:/app/data" \
  forecastiq
# http://localhost:8501
```
To bake a prebuilt warehouse into the image instead, copy `forecastiq.db` in before `docker build`
(remove it from `.dockerignore`/`.gitignore` scope for that build).

## Streamlit Community Cloud
1. Push the repo to GitHub.
2. On <https://share.streamlit.io>, create an app pointing at `app/app.py`.
3. The warehouse must be present at runtime. Either:
   - commit a prebuilt `forecastiq.db` (it's a build artifact, ~a few MB), **or**
   - add the dataset + a build step so the app can construct it.
   Configuration lives in `.streamlit/config.toml`; optional secrets in `.streamlit/secrets.toml`
   (see `secrets.toml.example`) can point `FORECASTIQ_DB_URL` at a hosted database.

## Configuration
| Setting | Where | Default |
|---------|-------|---------|
| Theme, server flags | `.streamlit/config.toml` | brand theme, headless, XSRF on |
| Database URL | `FORECASTIQ_DB_URL` env / secret | `sqlite:///forecastiq.db` (project root) |
| Dataset path | `FORECASTIQ_RAW_CSV` / `config.yaml` | `data/raw/Global Superstore.xls` |

## Health & smoke test
- Health endpoint: `GET /_stcore/health` → `200`.
- Page smoke tests: `pytest tests/test_app_pages.py` (renders all 10 pages via Streamlit's AppTest).
