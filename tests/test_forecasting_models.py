"""Tests for the forecasting models."""

import numpy as np
import pandas as pd

from forecastiq.forecasting import models


def _check_result(fc, horizon):
    assert len(fc.yhat) == horizon
    assert len(fc.index) == horizon
    assert np.all(np.isfinite(fc.yhat))
    assert np.all(fc.yhat_lower <= fc.yhat) and np.all(fc.yhat <= fc.yhat_upper)


def test_naive(synth_series):
    fc = models.NaiveForecaster().fit(synth_series).forecast(3)
    _check_result(fc, 3)
    assert fc.yhat[0] == synth_series.iloc[-1]
    assert fc.index[0] == pd.Timestamp("2015-01-01")  # month after 2014-12


def test_moving_average(synth_series):
    fc = models.MovingAverageForecaster(3).fit(synth_series).forecast(2)
    _check_result(fc, 2)
    assert abs(fc.yhat[0] - synth_series.iloc[-3:].mean()) < 1e-6


def test_linear_regression(synth_series):
    fc = models.LinearRegressionForecaster((1, 12), (3,), 12).fit(synth_series).forecast(6)
    _check_result(fc, 6)


def test_arima_and_sarima(synth_series):
    for model in (
        models.ARIMAForecaster((1, 1, 1)),
        models.SARIMAForecaster((1, 1, 1), (1, 1, 1, 12)),
    ):
        fc = model.fit(synth_series).forecast(4)
        _check_result(fc, 4)


def test_build_model_factories_respects_enabled():
    factories = models.build_model_factories(
        {"naive": {"enabled": True}, "sarima": {"enabled": False}}, period=12
    )
    assert "Naive" in factories and "SARIMA" not in factories
    assert isinstance(factories["Naive"](), models.NaiveForecaster)
