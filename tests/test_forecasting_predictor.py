"""Tests for the predictor: select, refit, forecast, persist."""
import pandas as pd

from forecastiq.forecasting import predictor


def test_forecast_series_and_persist(synth_series, all_model_factories, schema_engine):
    sf = predictor.forecast_series(
        synth_series, all_model_factories, horizon=6, n_folds=3,
        selection_metric="mape", series_id="total", granularity="monthly")

    assert sf.best_model in all_model_factories
    assert len(sf.forecast.yhat) == 6
    assert sf.backtest is not None and not sf.backtest.empty

    predictor.persist(schema_engine, sf, run_id="run1")

    fr = pd.read_sql("SELECT * FROM forecast_results", schema_engine)
    mm = pd.read_sql("SELECT * FROM model_metrics", schema_engine)

    assert int((fr["is_actual"] == 1).sum()) == len(synth_series)   # history persisted
    assert int((fr["is_actual"] == 0).sum()) == 6                   # forecast persisted
    assert int((mm["is_best"] == 1).sum()) == 1                     # exactly one winner
    assert mm.loc[mm["is_best"] == 1, "model_name"].iloc[0] == sf.best_model


def test_clear_forecasts(synth_series, all_model_factories, schema_engine):
    sf = predictor.forecast_series(
        synth_series, all_model_factories, horizon=3, n_folds=2,
        selection_metric="mape", series_id="total", granularity="monthly")
    predictor.persist(schema_engine, sf, run_id="run1")
    predictor.clear_forecasts(schema_engine)
    assert pd.read_sql("SELECT COUNT(*) AS n FROM forecast_results", schema_engine)["n"].iloc[0] == 0
    assert pd.read_sql("SELECT COUNT(*) AS n FROM model_metrics", schema_engine)["n"].iloc[0] == 0
