# Release Guide

## Release checklist
- [ ] `ruff check .` and `ruff format --check .` are clean
- [ ] `pytest -q` passes (engine tests on fixtures; page tests when a warehouse exists)
- [ ] Full pipeline verified end-to-end: `run_etl.py` → `run_analytics.py` → `run_forecast.py`
- [ ] App boots: `streamlit run app/app.py`
- [ ] `CHANGELOG.md` updated with the new version and date
- [ ] Version bumped in `pyproject.toml`
- [ ] Docs reflect any behavioural changes
- [ ] Tag the release and publish notes

## Cutting a release
```bash
# 1. Ensure main is green and the changelog/version are updated.
# 2. Tag:
git tag -a v1.0.0 -m "ForecastIQ v1.0.0"
git push origin v1.0.0            # (push only when you have a remote configured)

# 3. Create a GitHub release from the tag using the notes below.
```

## Release notes — v1.0.0

**ForecastIQ v1.0.0 — AI-Powered Sales Forecasting & Business Analytics Platform**

First stable release: a complete, tested ETL → analytics → forecasting → application stack built on the
public Global Superstore dataset.

**Highlights**
- 🗄️ **Validated ETL** into a Kimball star schema (51,290 order lines) with data-quality gates.
- 📊 **Analytics engine**: KPIs, trends, RFM, product/regional/returns analytics, and a rule-based
  insights engine.
- 🔮 **Forecasting engine**: 5 models, rolling-origin backtesting, automatic model selection, and
  prediction intervals persisted to the warehouse.
- 🖥️ **Streamlit platform**: 10 interactive pages with global filters that reuse the engines unchanged.
- ✅ **Quality**: 66 tests, Ruff lint/format, CI, Docker, and full architecture documentation.

**Metrics (Global Superstore, monthly revenue)**: best-model MAPE 12–21% per series; total revenue
$12.64M across 2011–2014.

See [`CHANGELOG.md`](../CHANGELOG.md) for the full list.
