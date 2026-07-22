"""Home — landing page: overview, architecture, dataset, warehouse & forecast stats."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from components.kpi import kpi_row  # noqa: E402
from sqlalchemy import text  # noqa: E402
from utils.format import compact_number, number  # noqa: E402
from utils.theme import apply_theme  # noqa: E402
from utils.warehouse import base_engine, warehouse_stats  # noqa: E402

apply_theme()

st.markdown(
    '<div class="hero"><h1>📈 ForecastIQ</h1>'
    "<p>AI-Powered Sales Forecasting &amp; Business Analytics Platform</p></div>",
    unsafe_allow_html=True,
)

stats = warehouse_stats()

# ---- Overview + architecture ----
left, right = st.columns([1.3, 1])
with left:
    st.markdown("#### Overview")
    st.write(
        "ForecastIQ turns raw transactional sales data into clean insights, demand forecasts, and "
        "interactive dashboards. It is built on the public **Global Superstore** dataset and is "
        "domain-agnostic — it works for any business with historical sales."
    )
    st.markdown("#### Architecture")
    st.markdown(
        "- **ETL** — Excel (Orders / People / Returns) → validated **star-schema** warehouse\n"
        "- **Analytics** — KPIs, trends, RFM, product, regional & returns analytics + a rule-based insight engine\n"
        "- **Forecasting** — Naive · MovingAverage · LinearRegression · ARIMA · SARIMA with rolling-origin "
        "backtesting and automatic model selection\n"
        "- **This app** — a Streamlit BI layer that reuses those engines unchanged"
    )
with right:
    st.markdown("#### Dataset")
    st.markdown(
        f"**Global Superstore**\n\n"
        f"- Grain: one row per order line\n"
        f"- Span: `{stats['date_min']}` → `{stats['date_max']}`\n"
        f"- {number(stats['fact_rows'])} order lines across {stats['months']} months\n"
        f"- 3 categories · 7 markets · 3 customer segments"
    )

st.divider()

# ---- Warehouse statistics ----
st.markdown("#### Warehouse statistics")
kpi_row(
    [
        {"label": "Order Lines", "value": compact_number(stats["fact_rows"])},
        {"label": "Customers", "value": number(stats["customers"])},
        {"label": "Products", "value": number(stats["products"])},
        {"label": "Geographies", "value": number(stats["regions"])},
        {"label": "Months", "value": number(stats["months"])},
    ]
)

# ---- Forecast summary ----
st.markdown("#### Forecasting summary")
if stats["has_forecasts"]:
    best = pd.read_sql(
        text(
            "SELECT series_id, model_name, ROUND(mape,2) AS mape, ROUND(r2,2) AS r2 "
            "FROM model_metrics WHERE is_best = 1 "
            "AND run_id = (SELECT run_id FROM model_metrics ORDER BY created_at DESC LIMIT 1) "
            "ORDER BY series_id"
        ),
        base_engine(),
    )
    c1, c2 = st.columns([1, 1.4])
    with c1:
        kpi_row(
            [
                {"label": "Series Forecast", "value": number(len(best))},
                {"label": "Avg Best MAPE", "value": f"{best['mape'].mean():.1f}%"},
            ]
        )
    with c2:
        st.dataframe(
            best.rename(
                columns={
                    "series_id": "Series",
                    "model_name": "Best model",
                    "mape": "MAPE %",
                    "r2": "R²",
                }
            ),
            hide_index=True,
            width="stretch",
        )
else:
    st.info(
        "No forecasts yet — run `python pipelines/run_forecast.py` to populate the Forecasting page."
    )

st.divider()

# ---- Navigation ----
st.markdown("#### Explore")
nav = [
    ("pages/2_Executive_Dashboard.py", "📊 Executive Dashboard", "Headline KPIs & revenue trends"),
    ("pages/3_Sales_Analytics.py", "📈 Sales Analytics", "Monthly/quarterly/yearly + growth"),
    ("pages/4_Customer_Analytics.py", "👥 Customer Analytics", "RFM, CLV, repeat & top customers"),
    ("pages/5_Product_Analytics.py", "📦 Product Analytics", "Category, product & loss-makers"),
    ("pages/6_Regional_Analytics.py", "🌍 Regional Analytics", "Market → city & managers"),
    ("pages/7_Returns_Analytics.py", "↩️ Returns Analytics", "Return rate & returned value"),
    ("pages/8_Forecasting.py", "🔮 Forecasting", "Interactive demand forecasts"),
    ("pages/9_Business_Insights.py", "💡 Business Insights", "Rule-based observations"),
    ("pages/10_Model_Performance.py", "🏁 Model Performance", "Compare every forecast model"),
]
for row_start in range(0, len(nav), 3):
    cols = st.columns(3)
    for col, (path, title, desc) in zip(cols, nav[row_start : row_start + 3], strict=False):
        with col:
            try:
                st.page_link(path, label=title)
            except Exception:  # noqa: BLE001 - no nav context (e.g. page run standalone/under test)
                st.markdown(f"**{title}**")
            st.caption(desc)
