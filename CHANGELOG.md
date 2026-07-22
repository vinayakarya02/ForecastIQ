# Changelog

All notable changes to ForecastIQ are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-21

First stable release — a complete ETL → analytics → forecasting → application platform.

### Added
- **ETL pipeline** (`src/forecastiq/etl`): Excel workbook ingestion (Orders / People / Returns),
  cleaning, data-quality validation with a PASS/WARN/FAIL report, star-schema transform, and SQL load.
  Reconciles the EMEA/AMEA and "United States"/US label mismatches via configurable aliases.
- **Data warehouse**: Kimball star schema (4 dimensions + `fact_sales`) with analytical views and
  forecast/metric output tables. 51,290 order lines loaded from the Global Superstore dataset.
- **Analytics layer** (`src/forecastiq/analytics`): executive KPIs, sales trends, RFM segmentation,
  product / regional / returns analytics, and a rule-based insights engine.
- **Forecasting engine** (`src/forecastiq/forecasting`): Naive, MovingAverage, LinearRegression, ARIMA,
  and SARIMA models behind one interface, with feature engineering, rolling-origin backtesting,
  automatic model selection, prediction intervals, and persistence to the warehouse.
- **Interactive platform** (`app/`): a 10-page Streamlit application with global filters (via a scoped
  in-memory warehouse), Plotly visualisations, an interactive Forecasting page, and CSV exports.
- **Pipelines**: `run_etl.py`, `run_analytics.py`, `run_forecast.py`.
- **Tooling & docs**: Ruff lint/format, 66 tests (incl. Streamlit AppTest page checks), an executed EDA
  notebook, Dockerfile + deployment docs, CI, and full architecture documentation.

[1.0.0]: https://github.com/vinayakarya02/ForecastIQ/releases/tag/v1.0.0
