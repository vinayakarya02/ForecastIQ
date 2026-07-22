"""Forecasting — pick a series, run the engine, view forecast + intervals + metrics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from components import charts  # noqa: E402
from components.kpi import kpi_row  # noqa: E402
from components.layout import page_header  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.format import pct  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
page_header("Forecasting", "Backtest every model, auto-select the best, and forecast ahead", "🔮")
st.caption("Forecasts use the full history from the warehouse (independent of the global filters).")

levels = da.forecast_levels()
LEVEL_LABELS = {
    "Total revenue": ("total", None),
    "Category": ("category", None),
    "Market": ("market", None),
    "Region": ("region", None),
    "Product": ("product", None),
}

c1, c2, c3 = st.columns([1.2, 1.6, 1])
with c1:
    choice = st.selectbox("Series", list(LEVEL_LABELS), key="fc_level")
level = LEVEL_LABELS[choice][0]
key = None
with c2:
    if level != "total":
        options = levels[level]
        if level == "product":
            st.caption("Only products with enough history will forecast.")
        key = st.selectbox(choice, options, key="fc_key") if options else None
with c3:
    horizon = st.slider("Horizon (months)", 3, 12, 6, key="fc_h")

if level != "total" and key is None:
    st.info("Select a value to forecast.")
    st.stop()

try:
    result = da.run_forecast(level, key, horizon)
except Exception as ex:  # noqa: BLE001 - surface data-sufficiency issues cleanly
    st.error(f"Could not forecast this series: {ex}")
    st.stop()

best = result["best_model"]
metrics = result["metrics"]
best_row = metrics[metrics["model"] == best].iloc[0]

kpi_row(
    [
        {"label": "Selected Model", "value": best},
        {"label": "MAPE", "value": pct(best_row["mape"])},
        {"label": "RMSE", "value": f"{best_row['rmse']:,.0f}"},
        {"label": "R²", "value": f"{best_row['r2']:.2f}" if pd.notna(best_row["r2"]) else "-"},
    ]
)

st.markdown("#### Forecast")
charts.show(
    charts.forecast_chart(
        result["history"],
        result["forecast"],
        f"{result['series_id']} — history & {horizon}-month forecast",
    )
)

c1, c2 = st.columns([1.3, 1])
with c1:
    st.markdown("#### Backtest comparison")
    show = metrics.copy().sort_values("mape")
    show.insert(0, "", show["model"].map(lambda m: "⭐" if m == best else ""))
    st.dataframe(
        show.rename(
            columns={"model": "Model", "rmse": "RMSE", "mae": "MAE", "mape": "MAPE %", "r2": "R²"}
        ),
        hide_index=True,
        width="stretch",
    )
    if result["failures"]:
        st.caption("Skipped (insufficient data / unstable): " + ", ".join(result["failures"]))
with c2:
    st.markdown("#### Forecast table")
    fc = result["forecast"].copy()
    fc["period_start"] = pd.to_datetime(fc["period_start"]).dt.strftime("%Y-%m")
    fc = fc.rename(
        columns={
            "period_start": "Month",
            "yhat": "Forecast",
            "yhat_lower": "Lower",
            "yhat_upper": "Upper",
        }
    )
    st.dataframe(
        fc.style.format({"Forecast": "{:,.0f}", "Lower": "{:,.0f}", "Upper": "{:,.0f}"}),
        hide_index=True,
        width="stretch",
    )

download_csv(
    result["forecast"], f"forecast_{result['series_id'].replace(':', '_')}.csv", "Export forecast"
)
