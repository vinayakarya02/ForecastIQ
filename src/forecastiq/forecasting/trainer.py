"""Rolling-origin backtesting and automatic model selection.

Instead of a single train/test split, each model is evaluated over several
**rolling origins**: fit on history up to a cut-off, forecast the next ``horizon``
periods, step the cut-off forward, repeat. Metrics are pooled across all folds so the
comparison reflects genuine out-of-sample performance. A model that errors on *any*
fold is excluded from selection (fair, same-folds comparison).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import evaluator


@dataclass
class BacktestResult:
    metrics: dict[str, dict]              # model name -> {rmse, mae, mape, r2}
    best: str | None                      # selected model name
    failures: dict[str, str]              # model name -> error message
    n_folds: int                          # folds actually evaluated
    predictions: dict[str, "pd.DataFrame"]  # model name -> (period_start, actual, predicted)


def rolling_origin_backtest(y: pd.Series, model_factories: dict[str, callable],
                            horizon: int, n_folds: int = 3,
                            selection_metric: str = "mape") -> BacktestResult:
    n = len(y)
    fold = horizon
    collected = {name: {"idx": [], "true": [], "pred": []} for name in model_factories}
    failures: dict[str, str] = {}
    folds_used = 0

    for f in range(n_folds, 0, -1):
        test_end = n - (f - 1) * fold
        test_start = test_end - fold
        if test_start < 3:                       # need a minimal train window
            continue
        train, test = y.iloc[:test_start], y.iloc[test_start:test_end]
        folds_used += 1
        for name, factory in model_factories.items():
            if name in failures:                 # already disqualified
                continue
            try:
                fc = factory().fit(train).forecast(len(test))
                pred = np.asarray(fc.yhat[:len(test)], dtype=float)
                if not np.all(np.isfinite(pred)):
                    raise ValueError("non-finite forecast")
                collected[name]["idx"].extend(test.index)
                collected[name]["true"].extend(test.to_numpy(dtype=float))
                collected[name]["pred"].extend(pred)
            except Exception as ex:               # noqa: BLE001 - record and drop the model
                failures[name] = f"{type(ex).__name__}: {ex}"

    metrics, predictions = {}, {}
    for name, d in collected.items():
        if name in failures or not d["true"]:
            continue
        metrics[name] = evaluator.evaluate(np.asarray(d["true"]), np.asarray(d["pred"]))
        predictions[name] = pd.DataFrame(
            {"period_start": d["idx"], "actual": d["true"], "predicted": d["pred"]}
        )
    best = evaluator.select_best(metrics, selection_metric)
    return BacktestResult(metrics=metrics, best=best, failures=failures,
                          n_folds=folds_used, predictions=predictions)
