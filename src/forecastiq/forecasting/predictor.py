"""Select, refit, forecast, and persist.

Ties the pieces together: backtest a series, refit the winning model on the full
history, produce the forward forecast with intervals, and write forecasts + metrics +
the selected model back into the warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..utils.io import df_to_table
from . import trainer
from .models import ForecastResult


@dataclass
class SeriesForecast:
    series_id: str
    granularity: str
    best_model: str
    metrics: dict            # model name -> metric dict
    failures: dict           # model name -> error
    history: pd.Series
    forecast: ForecastResult
    backtest: pd.DataFrame | None = None   # best model's out-of-sample (period, actual, predicted)


def forecast_series(y: pd.Series, model_factories: dict[str, callable], *, horizon: int,
                    n_folds: int, selection_metric: str, series_id: str,
                    granularity: str) -> SeriesForecast:
    """Backtest, pick the best model, refit on full history, and forecast ``horizon`` ahead."""
    bt = trainer.rolling_origin_backtest(y, model_factories, horizon, n_folds, selection_metric)
    if bt.best is None:
        raise RuntimeError(f"No model could be fit for series '{series_id}': {bt.failures}")
    best = model_factories[bt.best]().fit(y)          # refit winner on ALL history
    fc = best.forecast(horizon)
    return SeriesForecast(series_id, granularity, bt.best, bt.metrics, bt.failures, y, fc,
                          backtest=bt.predictions.get(bt.best))


def clear_forecasts(engine: Engine) -> None:
    """Wipe previous forecast output so only the latest run is stored."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM forecast_results"))
        conn.execute(text("DELETE FROM model_metrics"))


def persist(engine: Engine, sf: SeriesForecast, run_id: str) -> None:
    """Write forecast_results (history + forecast) and model_metrics for one series."""
    now = datetime.now().isoformat(timespec="seconds")

    rows = []
    for period, value in sf.history.items():
        rows.append({
            "run_id": run_id, "series_id": sf.series_id, "granularity": sf.granularity,
            "model_name": sf.best_model, "period_start": pd.Timestamp(period).strftime("%Y-%m-%d"),
            "yhat": float(value), "yhat_lower": None, "yhat_upper": None,
            "is_actual": 1, "created_at": now,
        })
    fc = sf.forecast
    for i, period in enumerate(fc.index):
        rows.append({
            "run_id": run_id, "series_id": sf.series_id, "granularity": sf.granularity,
            "model_name": sf.best_model, "period_start": pd.Timestamp(period).strftime("%Y-%m-%d"),
            "yhat": float(fc.yhat[i]), "yhat_lower": float(fc.yhat_lower[i]),
            "yhat_upper": float(fc.yhat_upper[i]), "is_actual": 0, "created_at": now,
        })
    df_to_table(pd.DataFrame(rows), "forecast_results", engine)

    metric_rows = []
    for name, m in sf.metrics.items():
        metric_rows.append({
            "run_id": run_id, "series_id": sf.series_id, "model_name": name,
            "rmse": m.get("rmse"), "mae": m.get("mae"), "mape": m.get("mape"), "r2": m.get("r2"),
            "is_best": int(name == sf.best_model), "created_at": now,
        })
    if metric_rows:
        df_to_table(pd.DataFrame(metric_rows), "model_metrics", engine)
