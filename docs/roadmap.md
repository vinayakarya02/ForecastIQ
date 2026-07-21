# ForecastIQ — Development Roadmap

Delivered in phases so each is independently demoable and interview-defendable.

## Phase 0 — Foundation ✅ (this commit)
- [x] Architecture, data flow, and design decisions
- [x] Repository structure + packaging layout
- [x] Star-schema DDL, analytical views, analysis queries
- [x] Config-driven design (`config.yaml`, `.env`)
- [x] Full documentation set

## Phase 1 — ETL pipeline ✅
- [x] `utils/` (config loader, logger, DB engine)
- [x] `extract` → `clean` → `validate` → `transform` → `load`
- [x] Excel source: Orders (fact), People (region manager), Returns (return flag)
- [x] `data_quality_log` populated; fail-fast on FAIL checks
- [x] `pipelines/run_etl.py` CLI + console load summary
- [x] Unit tests for clean, validate, transform/load, enrichment

## Phase 2 — Analytics layer ✅
- [x] `kpis.py` (revenue, profit, margin, AOV, ASP, return rate)
- [x] `trends.py` (monthly/quarterly/yearly, MoM/YoY, rolling trends)
- [x] `segmentation.py` (RFM, basic CLV, repeat analysis, top customers)
- [x] `products.py` + `regional.py` (category/product + market→city + manager)
- [x] `returns.py` (return rate by region/category/product, returned value)
- [x] `insights.py` (rule-based, data-derived business insights)
- [x] `pipelines/run_analytics.py` + CSV/insight exports
- [x] EDA notebook with charts (`notebooks/01_eda.ipynb`)
- [x] Comprehensive analytics unit tests

## Phase 3 — Forecasting ✅
- [x] `data.py` (monthly/quarterly series for total/category/region/market/product)
- [x] `features.py` (trend, seasonality, lags, rolling/moving averages)
- [x] `models.py` (Naive, MovingAverage, LinearRegression, ARIMA, SARIMA, optional Prophet)
- [x] `evaluator.py` (RMSE/MAE/MAPE/R² + best-model selection)
- [x] `trainer.py` (rolling-origin backtesting)
- [x] `predictor.py` (refit winner, forecast with intervals, persist to warehouse)
- [x] `visualizations.py` (actual-vs-forecast, residuals, model & forecast comparison)
- [x] `pipelines/run_forecast.py` CLI + CSV/figure exports
- [x] Comprehensive forecasting unit tests

## Phase 4 — Presentation
- [ ] FastAPI service (`/kpis`, `/forecast`, …)
- [ ] Power BI report (4 pages) + DAX measures
- [ ] Screenshots into `docs/images/`

## Phase 5 — Polish
- [ ] GitHub Actions CI (lint + pytest)
- [ ] `Makefile` / task runner shortcuts
- [ ] Short demo GIF in README

## Stretch ideas (explicitly optional)
- Prophet & XGBoost model plugins (interfaces already allow them)
- Automated weekly refresh via scheduler
- Anomaly flags on MoM growth
- Streamlit companion viewer

> Scope is deliberately bounded: a genuine student portfolio project, not a fake enterprise system.
