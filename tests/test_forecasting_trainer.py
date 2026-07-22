"""Tests for rolling-origin backtesting and selection."""

from forecastiq.forecasting import models, trainer


def test_backtest_runs_and_selects(synth_series, all_model_factories):
    bt = trainer.rolling_origin_backtest(
        synth_series, all_model_factories, horizon=6, n_folds=3, selection_metric="mape"
    )
    assert bt.n_folds == 3
    assert bt.best is not None
    assert len(bt.metrics) >= 3  # most models should survive
    assert bt.best in bt.predictions
    assert set(bt.predictions[bt.best].columns) == {"period_start", "actual", "predicted"}
    # 3 folds x 6 horizon = 18 pooled out-of-sample points
    assert len(bt.predictions[bt.best]) == 18


def test_backtest_excludes_failing_model(synth_series):
    class _Bad:
        name = "Bad"

        def fit(self, y):
            raise RuntimeError("boom")

    factories = {"Bad": lambda: _Bad(), "Naive": lambda: models.NaiveForecaster()}
    bt = trainer.rolling_origin_backtest(
        synth_series, factories, horizon=6, n_folds=2, selection_metric="rmse"
    )
    assert "Bad" in bt.failures
    assert "Bad" not in bt.metrics
    assert bt.best == "Naive"
