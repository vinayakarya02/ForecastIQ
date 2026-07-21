"""Forecast evaluation metrics and best-model selection.

All metrics take aligned 1-D arrays of actuals and predictions and are None-safe on
empty input. MAPE is computed over non-zero actuals to avoid division by zero.
"""
from __future__ import annotations

import numpy as np

# Lower-is-better for these; R2 is higher-is-better.
_LOWER_IS_BETTER = {"rmse", "mae", "mape"}


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    """Mean absolute percentage error (%), computed over non-zero actuals."""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = y_true != 0
    if not mask.any():
        return None
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot == 0:
        return None
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    return float(1.0 - ss_res / ss_tot)


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Return all four metrics as a dict."""
    return {
        "rmse": round(rmse(y_true, y_pred), 4),
        "mae": round(mae(y_true, y_pred), 4),
        "mape": None if mape(y_true, y_pred) is None else round(mape(y_true, y_pred), 4),
        "r2": None if r2(y_true, y_pred) is None else round(r2(y_true, y_pred), 4),
    }


def select_best(metrics_by_model: dict[str, dict], metric: str = "mape") -> str | None:
    """Pick the model name with the best score on ``metric``.

    Falls back to RMSE when the chosen metric is missing (e.g. MAPE undefined for an
    all-zero series). Higher is better only for R2.
    """
    candidates = {m: s.get(metric) for m, s in metrics_by_model.items() if s.get(metric) is not None}
    if not candidates:
        metric = "rmse"
        candidates = {m: s.get(metric) for m, s in metrics_by_model.items() if s.get(metric) is not None}
    if not candidates:
        return None
    reverse = metric == "r2"
    return max(candidates, key=candidates.get) if reverse else min(candidates, key=candidates.get)
