"""Forecasting models behind one common interface.

Every model implements ``fit(y)`` and ``forecast(horizon) -> ForecastResult`` so the
trainer, predictor, and pipeline treat them uniformly. Point forecasts always come
with approximate 95% prediction intervals.

Models (why each exists):
  - **Naive**          : last-value baseline. Any useful model must beat it.
  - **MovingAverage**  : smooths noise; strong when the series is roughly flat.
  - **LinearRegression**: trend + seasonality + lags/rolling — explainable, coefficients inspectable.
  - **ARIMA**          : captures autocorrelation and non-seasonal structure.
  - **SARIMA**         : ARIMA + explicit seasonality (period 12 monthly) — fits retail seasonality.
  - **Prophet**        : optional; additive trend/seasonality/holidays (heavy dependency, off by default).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from . import features

Z95 = 1.959963984540054  # 97.5th percentile of the standard normal


@dataclass
class ForecastResult:
    index: pd.DatetimeIndex
    yhat: np.ndarray
    yhat_lower: np.ndarray
    yhat_upper: np.ndarray


def _future_index(y: pd.Series, horizon: int) -> pd.DatetimeIndex:
    freq = y.index.freq or pd.infer_freq(y.index) or "MS"
    return pd.date_range(y.index[-1], periods=horizon + 1, freq=freq)[1:]


class BaseForecaster:
    name = "Base"

    def fit(self, y: pd.Series) -> "BaseForecaster":
        raise NotImplementedError

    def forecast(self, horizon: int) -> ForecastResult:
        raise NotImplementedError


class NaiveForecaster(BaseForecaster):
    """Forecast = last observed value; intervals widen like a random walk."""
    name = "Naive"

    def fit(self, y):
        self.y_ = y
        self.last_ = float(y.iloc[-1])
        self.sigma_ = float(np.std(np.diff(y.to_numpy(dtype=float)), ddof=1)) if len(y) > 2 else 0.0
        return self

    def forecast(self, horizon):
        idx = _future_index(self.y_, horizon)
        yhat = np.full(horizon, self.last_)
        band = Z95 * self.sigma_ * np.sqrt(np.arange(1, horizon + 1))
        return ForecastResult(idx, yhat, yhat - band, yhat + band)


class MovingAverageForecaster(BaseForecaster):
    """Forecast = mean of the last ``window`` observations (flat)."""
    name = "MovingAverage"

    def __init__(self, window: int = 3):
        self.window = window

    def fit(self, y):
        self.y_ = y
        self.mean_ = float(y.iloc[-self.window:].mean())
        resid = (y - y.rolling(self.window).mean()).dropna()
        self.sigma_ = float(resid.std(ddof=1)) if len(resid) > 1 else 0.0
        return self

    def forecast(self, horizon):
        idx = _future_index(self.y_, horizon)
        yhat = np.full(horizon, self.mean_)
        band = Z95 * self.sigma_
        return ForecastResult(idx, yhat, yhat - band, yhat + band)


class LinearRegressionForecaster(BaseForecaster):
    """OLS on trend + seasonality + lag/rolling features, forecast recursively."""
    name = "LinearRegression"

    def __init__(self, lags=(1, 12), roll_windows=(3,), period: int = 12):
        self.lags = list(lags)
        self.roll_windows = list(roll_windows)
        self.period = period

    def fit(self, y):
        self.y_ = y
        X, target = features.make_supervised(y, self.lags, self.roll_windows, self.period)
        if len(X) < len(X.columns) + 1:
            raise ValueError("series too short for the requested features")
        self.model_ = LinearRegression().fit(X.to_numpy(), target)
        resid = target - self.model_.predict(X.to_numpy())
        self.sigma_ = float(np.std(resid, ddof=1)) if len(resid) > 1 else 0.0
        self._quarterly = bool(getattr(y.index, "freqstr", "") and y.index.freqstr.startswith("Q"))
        return self

    def forecast(self, horizon):
        idx = _future_index(self.y_, horizon)
        history = list(self.y_.to_numpy(dtype=float))
        n = len(self.y_)
        preds = []
        for k in range(horizon):
            period_number = idx[k].quarter if self._quarterly else idx[k].month
            row = features.feature_row(history, n + k, int(period_number),
                                       self.lags, self.roll_windows, self.period)
            p = float(self.model_.predict([row])[0])
            preds.append(p)
            history.append(p)          # recursive: prediction feeds the next step's lags
        yhat = np.asarray(preds)
        band = Z95 * self.sigma_ * np.sqrt(np.arange(1, horizon + 1))
        return ForecastResult(idx, yhat, yhat - band, yhat + band)


class _StatsmodelsForecaster(BaseForecaster):
    """Shared fit/forecast for statsmodels ARIMA-family models."""

    def _make(self, y):
        raise NotImplementedError

    def fit(self, y):
        self.y_ = y
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.res_ = self._make(y).fit()
        return self

    def forecast(self, horizon):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc = self.res_.get_forecast(steps=horizon)
            mean = fc.predicted_mean
            ci = fc.conf_int(alpha=0.05)
        return ForecastResult(
            pd.DatetimeIndex(mean.index), mean.to_numpy(dtype=float),
            ci.iloc[:, 0].to_numpy(dtype=float), ci.iloc[:, 1].to_numpy(dtype=float),
        )


class ARIMAForecaster(_StatsmodelsForecaster):
    name = "ARIMA"

    def __init__(self, order=(1, 1, 1)):
        self.order = tuple(order)

    def _make(self, y):
        from statsmodels.tsa.arima.model import ARIMA
        return ARIMA(y, order=self.order)


class SARIMAForecaster(_StatsmodelsForecaster):
    name = "SARIMA"

    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)):
        self.order = tuple(order)
        self.seasonal_order = tuple(seasonal_order)

    def _make(self, y):
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        # Keep statsmodels' stability constraints (enforce_stationarity/invertibility=True,
        # the defaults): they bound the forecast and prevent explosive non-stationary output.
        # If a short series can't satisfy them the fit raises and the trainer skips it.
        return SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order)


class ProphetForecaster(BaseForecaster):
    """Optional Prophet adapter (lazy import; raises if prophet isn't installed)."""
    name = "Prophet"

    def fit(self, y):
        from prophet import Prophet  # noqa: F401  (raises ImportError if absent)
        self.y_ = y
        df = pd.DataFrame({"ds": y.index, "y": y.to_numpy(dtype=float)})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model_ = Prophet(interval_width=0.95).fit(df)
        return self

    def forecast(self, horizon):
        freq = self.y_.index.freqstr or "MS"
        future = self.model_.make_future_dataframe(periods=horizon, freq=freq)
        fc = self.model_.predict(future).tail(horizon)
        return ForecastResult(
            pd.DatetimeIndex(fc["ds"].to_numpy()), fc["yhat"].to_numpy(),
            fc["yhat_lower"].to_numpy(), fc["yhat_upper"].to_numpy(),
        )


def build_model_factories(models_cfg: dict, period: int) -> dict[str, callable]:
    """Return ``{name: factory}`` for every enabled model (fresh instance per call)."""
    m = models_cfg
    factories: dict[str, callable] = {}
    if m.get("naive", {}).get("enabled"):
        factories["Naive"] = lambda: NaiveForecaster()
    if m.get("moving_average", {}).get("enabled"):
        w = m["moving_average"].get("window", 3)
        factories["MovingAverage"] = lambda w=w: MovingAverageForecaster(w)
    if m.get("linear_regression", {}).get("enabled"):
        lags = tuple(m["linear_regression"].get("lags", [1, 12]))
        rw = tuple(m["linear_regression"].get("roll_windows", [3]))
        factories["LinearRegression"] = lambda lags=lags, rw=rw: LinearRegressionForecaster(lags, rw, period)
    if m.get("arima", {}).get("enabled"):
        order = tuple(m["arima"].get("order", [1, 1, 1]))
        factories["ARIMA"] = lambda o=order: ARIMAForecaster(o)
    if m.get("sarima", {}).get("enabled"):
        order = tuple(m["sarima"].get("order", [1, 1, 1]))
        so = tuple(m["sarima"].get("seasonal_order", [1, 1, 1, period]))
        factories["SARIMA"] = lambda o=order, s=so: SARIMAForecaster(o, s)
    if m.get("prophet", {}).get("enabled"):
        factories["Prophet"] = lambda: ProphetForecaster()
    return factories
