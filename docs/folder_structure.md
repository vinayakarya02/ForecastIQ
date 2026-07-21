# ForecastIQ — Folder Structure

```
ForecastIQ/
│
├── README.md                     # project overview + quick start
├── LICENSE                       # MIT
├── requirements.txt              # pinned dependencies
├── .gitignore                    # excludes data, db, venv, reports
├── .env.example                  # env var template (DB URL, paths)
│
├── config/
│   └── config.yaml               # paths, column map, ETL rules, model params
│
├── data/                         # (git-ignored contents)
│   ├── raw/                      # original CSV drops from Kaggle
│   ├── interim/                  # partially cleaned intermediate files
│   ├── processed/                # analysis-ready extracts
│   └── external/                 # reference/lookup data
│
├── sql/
│   ├── schema.sql                # star-schema DDL
│   ├── views.sql                 # analytical views (metric definitions)
│   └── queries/                  # ready-to-run analysis queries
│       ├── revenue_trends.sql
│       ├── top_products.sql
│       ├── regional_performance.sql
│       ├── customer_segmentation.sql
│       └── forecast_vs_actual.sql
│
├── src/forecastiq/               # installable package (import forecastiq)
│   ├── config.py                 # loads config.yaml + env overrides
│   ├── etl/
│   │   ├── extract.py            # read + rename + parse
│   │   ├── clean.py              # types, dedupe, nulls
│   │   ├── validate.py           # quality gates + report
│   │   ├── transform.py          # dims + fact + features
│   │   └── load.py               # write to SQL
│   ├── forecasting/
│   │   ├── preprocess.py         # build time series + features
│   │   ├── models.py             # ARIMA/SARIMA/LinReg/RF (+optional)
│   │   ├── evaluate.py           # RMSE/MAE/MAPE/R2
│   │   └── pipeline.py           # backtest + select best + persist
│   ├── analytics/
│   │   ├── kpis.py               # headline KPIs
│   │   └── segmentation.py       # RFM
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   └── schemas.py            # Pydantic response models
│   └── utils/
│       ├── logger.py             # configured logging
│       └── io.py                 # read/write helpers, DB engine
│
├── pipelines/
│   ├── run_etl.py                # CLI entrypoint: full ETL
│   └── run_forecast.py           # CLI entrypoint: forecasting
│
├── notebooks/
│   ├── 01_eda.ipynb              # exploratory data analysis
│   ├── 02_etl_demo.ipynb         # walk through the ETL stages
│   └── 03_forecasting.ipynb      # model comparison + plots
│
├── powerbi/
│   ├── README.md                 # how to build the dashboard
│   └── dax_measures.md           # copy-paste DAX measures
│
├── docs/                         # this documentation set
│   └── images/                   # dashboard/architecture screenshots
│
├── tests/                        # pytest unit tests
│   ├── test_validate.py
│   ├── test_clean.py
│   └── test_evaluate.py
│
└── reports/                      # (git-ignored contents)
    ├── figures/                  # generated PNG charts
    └── forecasts/                # exported forecast CSV/Excel
```

## Conventions
- **Package code** lives under `src/forecastiq/` and is imported as `forecastiq.*`.
- **Runnable scripts** live in `pipelines/` and only orchestrate package functions (thin entrypoints).
- **No secrets or data** are committed — everything reproducible lives in code/config; everything heavy is git-ignored.
- **Docs mirror modules**: each layer (ETL, forecasting, dashboard, API) has a matching design doc.
