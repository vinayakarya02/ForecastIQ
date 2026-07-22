#!/bin/sh
# Ensure the warehouse exists (real dataset if mounted, else generated sample),
# then launch the Streamlit app.
set -e

python pipelines/bootstrap.py

exec streamlit run app/app.py --server.port="${PORT:-8501}" --server.address=0.0.0.0
