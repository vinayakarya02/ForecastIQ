# ForecastIQ — Resume Description

Ready-to-use blurbs. Pick the length that fits your template. All are interview-defendable against the
actual code in this repo — no fabricated metrics or users.

## One-liner (headline)
**ForecastIQ — AI-Powered Sales Forecasting & Business Analytics Platform** · *Python, SQL, Pandas, statsmodels, scikit-learn, Power BI*

## Three-bullet version (recommended for a resume project entry)
- Built an end-to-end analytics platform that ingests sales data through a validated ETL pipeline into a SQL star-schema warehouse.
- Engineered a forecasting module comparing ARIMA, SARIMA, and ML models, auto-selecting the best by MAPE/RMSE on a backtest window.
- Designed an interactive Power BI dashboard for revenue trends, product/regional analysis, RFM segmentation, and forecast-vs-actual.

## Two-bullet version (compact)
- Developed ForecastIQ, an ETL-to-forecast analytics platform on real retail data, with SQL star schema, data-quality gates, and Power BI dashboards.
- Implemented time-series forecasting (ARIMA/SARIMA/Random Forest) with backtesting and automatic model selection reported via RMSE, MAE, MAPE, and R².

## Skills this project evidences
`Python` · `SQL` · `Pandas` · `NumPy` · `statsmodels` · `scikit-learn` · `ETL` · `Data Validation` ·
`Time Series Forecasting` · `Statistics` · `Power BI` · `Data Visualization` · `Business Intelligence` · `FastAPI`

## Interview talking points (be ready for these)
1. **Why a star schema?** Slicing by date/product/region/customer; small fact rows; clear measure vs attribute split.
2. **How do you avoid overfitting in model selection?** Hold-out backtest; models never see the test window; select on out-of-sample MAPE.
3. **What are the data-quality gates?** Required-column, non-negativity, discount range, null-fraction, date-order, duplicate checks — fail-fast before load.
4. **Why MAPE as the default metric?** Scale-free and stakeholder-friendly; complemented by RMSE for large-error sensitivity.
5. **How is it generic across businesses?** A YAML column map decouples the pipeline from any one dataset's schema.
6. **Limitations you'd call out?** Needs ~24+ months of history for stable seasonality; structural breaks raise MAPE (surfaced, not hidden).

## GitHub
`github.com/vinayakarya02/ForecastIQ`
