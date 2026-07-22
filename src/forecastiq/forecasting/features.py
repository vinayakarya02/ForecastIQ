"""Feature engineering for the machine-learning forecasters.

Builds a supervised design matrix from a univariate series using:
  - a linear **trend** (absolute time index)
  - **seasonality** (cyclical sin/cos encoding of the calendar month/quarter)
  - **lag** features (value at t-1, t-12, ...)
  - **rolling / moving averages** (mean of the last w observations)

The same row-builder is used for training and for recursive multi-step forecasting,
so features are identical in both paths.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def feature_names(lags, roll_windows) -> list[str]:
    return (
        ["trend", "season_sin", "season_cos"]
        + [f"lag_{L}" for L in lags]
        + [f"roll_{w}" for w in roll_windows]
    )


def _seasonal(period_number: int, period: int) -> tuple[float, float]:
    """Cyclical encoding: period_number is 1..period (month 1-12 or quarter 1-4)."""
    angle = 2.0 * np.pi * ((period_number - 1) / period)
    return float(np.sin(angle)), float(np.cos(angle))


def feature_row(
    history, t: int, period_number: int, lags, roll_windows, period: int
) -> list[float]:
    """Feature vector for one position, given the values *before* it (``history``)."""
    sin, cos = _seasonal(period_number, period)
    row = [float(t), sin, cos]
    row += [float(history[-L]) for L in lags]
    row += [float(np.mean(history[-w:])) for w in roll_windows]
    return row


def make_supervised(
    y: pd.Series, lags, roll_windows, period: int
) -> tuple[pd.DataFrame, np.ndarray]:
    """Build (X, target) for supervised learning from series ``y``.

    Rows before enough history exists (``max(lags, roll_windows)``) are dropped.
    Seasonality uses the calendar month (monthly) or quarter (quarterly) of the target.
    """
    values = y.to_numpy(dtype=float)
    idx = y.index
    is_quarterly = getattr(idx, "freqstr", "") and idx.freqstr.startswith("Q")
    period_numbers = idx.quarter if is_quarterly else idx.month
    warmup = max(list(lags) + list(roll_windows))

    rows, target = [], []
    for t in range(warmup, len(values)):
        rows.append(feature_row(values[:t], t, int(period_numbers[t]), lags, roll_windows, period))
        target.append(values[t])
    X = pd.DataFrame(rows, columns=feature_names(lags, roll_windows))
    return X, np.asarray(target, dtype=float)
