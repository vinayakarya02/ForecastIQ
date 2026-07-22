"""Model Performance — compare every forecasting model from the last persisted run."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from components import charts  # noqa: E402
from components.kpi import kpi_row  # noqa: E402
from components.layout import page_header  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.format import number, pct  # noqa: E402
from utils.theme import ACCENT, MUTED, apply_theme, style_fig  # noqa: E402

apply_theme()
page_header("Model Performance", "How every forecasting model scored in rolling-origin backtesting", "🏁")

mm = da.persisted_model_metrics()
if mm.empty:
    st.info("No model metrics yet. Run `python pipelines/run_forecast.py` to populate this page.")
    st.stop()

winners = mm[mm["is_best"] == 1]
kpi_row([
    {"label": "Series Forecast", "value": number(winners["series_id"].nunique())},
    {"label": "Models Compared", "value": number(mm["model_name"].nunique())},
    {"label": "Avg Best MAPE", "value": pct(winners["mape"].mean())},
    {"label": "Best R²", "value": f"{winners['r2'].max():.2f}"},
])

st.divider()
c1, c2 = st.columns([1, 1.3])
with c1:
    st.markdown("#### Winning models")
    wc = winners["model_name"].value_counts().reset_index()
    wc.columns = ["model", "wins"]
    charts.show(charts.bar(wc, "model", "wins", "Series won per model",
                           labels={"model": "", "wins": "Series won"}))
with c2:
    st.markdown("#### Best model per series")
    st.dataframe(
        winners[["series_id", "model_name", "mape", "rmse", "r2"]].rename(
            columns={"series_id": "Series", "model_name": "Best model", "mape": "MAPE %",
                     "rmse": "RMSE", "r2": "R²"}),
        hide_index=True, width="stretch")

st.divider()
st.markdown("#### Compare models for a series")
series = st.selectbox("Series", sorted(mm["series_id"].unique()), key="mp_series")
metric = st.radio("Metric", ["mape", "rmse", "mae", "r2"], horizontal=True, key="mp_metric",
                  format_func=str.upper)

sub = mm[mm["series_id"] == series].dropna(subset=[metric]).copy()
ascending = metric != "r2"
sub = sub.sort_values(metric, ascending=ascending)
sub["is_best"] = sub["is_best"].astype(bool)
fig = px.bar(sub, x="model_name", y=metric, color="is_best",
             color_discrete_map={True: ACCENT, False: MUTED},
             title=f"{series} — {metric.upper()} by model "
                   f"({'higher is better' if metric == 'r2' else 'lower is better'})",
             labels={"model_name": "", metric: metric.upper(), "is_best": "Selected"})
charts.show(style_fig(fig))

st.dataframe(
    sub[["model_name", "rmse", "mae", "mape", "r2"]].rename(
        columns={"model_name": "Model", "rmse": "RMSE", "mae": "MAE", "mape": "MAPE %", "r2": "R²"}),
    hide_index=True, width="stretch")

download_csv(mm, "model_metrics.csv", "Export all model metrics")
