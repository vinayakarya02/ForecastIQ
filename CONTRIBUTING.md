# Contributing to ForecastIQ

Thanks for your interest! ForecastIQ is a portfolio-grade analytics & forecasting platform, and
contributions that improve correctness, clarity, or documentation are welcome.

## Development setup
```bash
git clone https://github.com/vinayakarya02/ForecastIQ.git
cd ForecastIQ
python -m venv .venv && . .venv/Scripts/activate   # Windows; use source .venv/bin/activate on Unix
pip install -e ".[app,dev]"
```
Add the dataset at `data/raw/Global Superstore.xls` (see [docs/installation.md](docs/installation.md)),
then build the warehouse:
```bash
python pipelines/run_etl.py
python pipelines/run_forecast.py
```

## Quality gates (must pass before a PR)
```bash
ruff check .            # lint
ruff format --check .   # formatting
pytest -q               # tests
```
Or install the git hooks so these run automatically:
```bash
pre-commit install
```

## Conventions
- **Style**: [Ruff](https://docs.astral.sh/ruff/) (lint + format), line length 100, Python 3.10+ type hints.
- **Layout**: engine logic lives in `src/forecastiq/`; entrypoints in `pipelines/`; UI in `app/`.
  The Streamlit app must **reuse** the analytics/forecasting modules — do not duplicate metric logic in the UI.
- **Tests**: add/extend tests under `tests/` for any behavioural change; keep them deterministic
  (use the fixtures in `conftest.py`).
- **Commits**: clear, imperative subject lines; group related changes.

## Pull requests
1. Branch from `main`.
2. Keep the PR focused; describe the change and how you verified it (fill in the PR template).
3. Ensure all quality gates pass and docs are updated where relevant.

## Reporting bugs / ideas
Open an issue using the templates. Include steps to reproduce, expected vs actual behaviour, and your
environment (OS, Python version).
