"""Forecast visualizations (saved as PNGs).

Headless matplotlib (Agg backend) so figures render in scripts/CI without a display.
Four diagnostics: actual-vs-forecast with intervals, residual analysis, model
comparison, and a forecast comparison across models.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .predictor import SeriesForecast  # noqa: E402

ACTUAL, FORECAST, BAND = "#2563eb", "#f59e0b", "#f59e0b"
plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "font.size": 10})


def _save(fig, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_actual_vs_forecast(sf: SeriesForecast, path: str | Path) -> Path:
    """History line + forward forecast with a shaded 95% prediction interval."""
    fc = sf.forecast
    hist = sf.history
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(hist.index, hist.to_numpy(), color=ACTUAL, label="Actual")
    ax.plot(
        fc.index,
        fc.yhat,
        color=FORECAST,
        ls="--",
        marker="o",
        ms=3,
        label=f"Forecast ({sf.best_model})",
    )
    ax.fill_between(
        fc.index, fc.yhat_lower, fc.yhat_upper, color=BAND, alpha=0.2, label="95% interval"
    )
    mape = sf.metrics.get(sf.best_model, {}).get("mape")
    ax.set_title(
        f"Actual vs Forecast - {sf.series_id}" + (f"  (backtest MAPE {mape:.1f}%)" if mape else "")
    )
    ax.set_ylabel(sf.history.name or "value")
    ax.legend(loc="upper left")
    return _save(fig, path)


def plot_residual_analysis(sf: SeriesForecast, path: str | Path) -> Path:
    """Out-of-sample residuals (from backtest) over time and as a histogram."""
    bt = sf.backtest
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    if bt is None or bt.empty:
        ax[0].text(0.5, 0.5, "No backtest residuals", ha="center")
        return _save(fig, path)
    resid = bt["actual"].to_numpy() - bt["predicted"].to_numpy()
    ax[0].axhline(0, color="gray", lw=1)
    ax[0].plot(pd.to_datetime(bt["period_start"]), resid, color=ACTUAL, marker="o", ms=3)
    ax[0].set_title(f"Backtest residuals over time - {sf.best_model}")
    ax[0].set_ylabel("actual - predicted")
    ax[1].hist(resid, bins=min(12, max(4, len(resid))), color=ACTUAL, alpha=0.8)
    ax[1].axvline(0, color="gray", lw=1)
    ax[1].set_title(f"Residual distribution (mean {resid.mean():,.0f})")
    return _save(fig, path)


def plot_model_comparison(sf: SeriesForecast, path: str | Path, metric: str = "mape") -> Path:
    """Bar chart of each model's backtest metric; the winner is highlighted."""
    names, vals = [], []
    for name, m in sf.metrics.items():
        if m.get(metric) is not None:
            names.append(name)
            vals.append(m[metric])
    order = np.argsort(vals)[:: -1 if metric == "r2" else 1]
    names = [names[i] for i in order]
    vals = [vals[i] for i in order]
    colors = [FORECAST if n == sf.best_model else "#94a3b8" for n in names]

    fig, ax = plt.subplots(figsize=(9, 4.2))
    bars = ax.bar(names, vals, color=colors)
    ax.set_title(
        f"Model comparison by {metric.upper()} - {sf.series_id} (lower is better)"
        if metric != "r2"
        else f"Model comparison by R2 - {sf.series_id} (higher is better)"
    )
    ax.set_ylabel(metric.upper())
    for b, v in zip(bars, vals, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.1f}", ha="center", va="bottom", fontsize=9)
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(15)
    return _save(fig, path)


def plot_forecast_comparison(
    history: pd.Series, model_factories: dict, horizon: int, path: str | Path, tail: int = 24
) -> Path:
    """Overlay every model's forward forecast on the recent history."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    recent = history.iloc[-tail:]
    ax.plot(recent.index, recent.to_numpy(), color="black", lw=2, label="Actual")
    for name, factory in model_factories.items():
        try:
            fc = factory().fit(history).forecast(horizon)
            ax.plot(fc.index, fc.yhat, ls="--", marker=".", label=name)
        except Exception:  # noqa: BLE001 - a model that can't fit is simply omitted
            continue
    ax.set_title(f"Forecast comparison across models (+{horizon} periods)")
    ax.set_ylabel(history.name or "value")
    ax.legend(loc="upper left", fontsize=8)
    return _save(fig, path)
