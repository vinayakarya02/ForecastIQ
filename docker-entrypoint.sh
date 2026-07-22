#!/bin/sh
# Build the warehouse on first run if the dataset is mounted and the DB doesn't exist,
# then launch the Streamlit app.
set -e

if [ ! -f forecastiq.db ] && [ -f "data/raw/Global Superstore.xls" ]; then
  echo "[entrypoint] Building warehouse from dataset..."
  python pipelines/run_etl.py
  python pipelines/run_forecast.py
fi

exec streamlit run app/app.py --server.port="${PORT:-8501}" --server.address=0.0.0.0
