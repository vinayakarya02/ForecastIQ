"""Tests for forecast evaluation metrics and model selection."""

import numpy as np

from forecastiq.forecasting import evaluator


def test_perfect_prediction():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    m = evaluator.evaluate(y, y)
    assert m["rmse"] == 0.0 and m["mae"] == 0.0 and m["mape"] == 0.0 and m["r2"] == 1.0


def test_known_values():
    y = np.array([100.0, 200.0])
    p = np.array([110.0, 180.0])
    assert evaluator.mae(y, p) == 15.0
    assert abs(evaluator.mape(y, p) - 10.0) < 1e-9  # (10% + 10%) / 2
    assert abs(evaluator.rmse(y, p) - np.sqrt((100 + 400) / 2)) < 1e-9


def test_mape_skips_zero_actuals():
    assert evaluator.mape(np.array([0.0, 0.0]), np.array([1.0, 2.0])) is None
    # only the non-zero actual counts: |100-110|/100 = 10%
    assert abs(evaluator.mape(np.array([0.0, 100.0]), np.array([5.0, 110.0])) - 10.0) < 1e-9


def test_select_best_direction():
    metrics = {"A": {"mape": 10, "rmse": 5, "r2": 0.8}, "B": {"mape": 20, "rmse": 3, "r2": 0.9}}
    assert evaluator.select_best(metrics, "mape") == "A"  # lower better
    assert evaluator.select_best(metrics, "rmse") == "B"  # lower better
    assert evaluator.select_best(metrics, "r2") == "B"  # higher better


def test_select_best_falls_back_to_rmse():
    metrics = {"A": {"mape": None, "rmse": 5.0}, "B": {"mape": None, "rmse": 9.0}}
    assert evaluator.select_best(metrics, "mape") == "A"
