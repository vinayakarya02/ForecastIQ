"""ForecastIQ forecasting entrypoint.

Builds each configured series, backtests all models with rolling-origin CV, selects
the best per series, forecasts ahead, persists forecasts + metrics to the warehouse,
and saves diagnostic figures.

Usage:
    python pipelines/run_forecast.py
    python pipelines/run_forecast.py --granularity monthly --horizon 6 --series total,by_category
"""

from __future__ import annotations

import argparse
import sys
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    pass
warnings.filterwarnings("ignore")  # statsmodels convergence chatter

from forecastiq.config import Config  # noqa: E402
from forecastiq.forecasting import data, models, predictor, visualizations  # noqa: E402
from forecastiq.utils.io import get_engine  # noqa: E402
from forecastiq.utils.logger import get_logger  # noqa: E402


def _resolve_series(engine, entries: list[str]) -> list[tuple[str, str | None]]:
    """Expand config entries (total / by_category / by_region / by_market) to (level, key)."""
    plan: list[tuple[str, str | None]] = []
    for entry in entries:
        if entry == "total":
            plan.append(("total", None))
        elif entry.startswith("by_"):
            level = entry[3:]
            plan += [(level, key) for key in data.list_keys(engine, level)]
        else:
            raise ValueError(f"Unknown series entry: {entry}")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ForecastIQ forecasting pipeline.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--granularity", default=None, help="monthly | quarterly")
    parser.add_argument("--horizon", type=int, default=None)
    parser.add_argument("--series", default=None, help="comma list e.g. total,by_category")
    args = parser.parse_args()

    cfg = Config.load(args.config)
    fcfg = cfg["forecasting"]
    logger = get_logger()
    engine = get_engine(cfg.db_url)

    target = fcfg["target"]
    granularity = args.granularity or fcfg["granularity"]
    horizon = args.horizon or fcfg["horizon"]
    folds = fcfg["backtest_folds"]
    metric = fcfg["selection_metric"]
    period = 4 if granularity == "quarterly" else fcfg.get("seasonal_period", 12)
    entries = args.series.split(",") if args.series else fcfg["series"]

    run_id = datetime.now().strftime("fc_%Y%m%d_%H%M%S")
    logger.info(
        "=== ForecastIQ Forecasting (run_id=%s, %s, horizon=%d) ===", run_id, granularity, horizon
    )

    factories = models.build_model_factories(fcfg["models"], period)
    logger.info(
        "Models: %s | backtest folds: %d | selection: %s", ", ".join(factories), folds, metric
    )

    plan = _resolve_series(engine, entries)
    predictor.clear_forecasts(engine)

    results, summary_rows, forecast_rows = [], [], []
    for level, key in plan:
        sid = data.series_id(level, key)
        y = data.build_series(engine, target, granularity, level, key)
        if len(y) < folds * horizon + 3:
            logger.warning(
                "Skipping %s: only %d periods (need >= %d)", sid, len(y), folds * horizon + 3
            )
            continue
        sf = predictor.forecast_series(
            y,
            factories,
            horizon=horizon,
            n_folds=folds,
            selection_metric=metric,
            series_id=sid,
            granularity=granularity,
        )
        predictor.persist(engine, sf, run_id)
        results.append(sf)

        best_m = sf.metrics.get(sf.best_model, {})
        summary_rows.append(
            {
                "series_id": sid,
                "best_model": sf.best_model,
                "mape": best_m.get("mape"),
                "rmse": best_m.get("rmse"),
                "r2": best_m.get("r2"),
                "models_compared": len(sf.metrics),
            }
        )
        for i, ts in enumerate(sf.forecast.index):
            forecast_rows.append(
                {
                    "series_id": sid,
                    "model": sf.best_model,
                    "period_start": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                    "yhat": round(float(sf.forecast.yhat[i]), 2),
                    "yhat_lower": round(float(sf.forecast.yhat_lower[i]), 2),
                    "yhat_upper": round(float(sf.forecast.yhat_upper[i]), 2),
                }
            )

    if not results:
        logger.error("No series forecast — check the warehouse and config.")
        return 1

    # ---- Console summary ----
    summary = pd.DataFrame(summary_rows)
    print("\n" + "=" * 78 + "\nMODEL SELECTION SUMMARY\n" + "=" * 78)
    try:
        from tabulate import tabulate

        print(
            tabulate(summary, headers="keys", tablefmt="github", showindex=False, floatfmt=",.2f")
        )
    except ImportError:
        print(summary.to_string(index=False))
    won = summary["best_model"].value_counts().to_dict()
    print(f"\nWinning models across {len(results)} series: {won}")

    # ---- Visualizations for the total series ----
    total_sf = next((s for s in results if s.series_id == "total"), results[0])
    fig_dir = cfg.path("paths", "figures_dir")
    y_total = total_sf.history
    paths = [
        visualizations.plot_actual_vs_forecast(
            total_sf, fig_dir / "forecast_actual_vs_forecast.png"
        ),
        visualizations.plot_residual_analysis(total_sf, fig_dir / "forecast_residuals.png"),
        visualizations.plot_model_comparison(
            total_sf, fig_dir / "forecast_model_comparison.png", metric
        ),
        visualizations.plot_forecast_comparison(
            y_total, factories, horizon, fig_dir / "forecast_comparison.png"
        ),
    ]
    logger.info("Saved %d figures to %s", len(paths), fig_dir)

    # ---- Export forecast tables ----
    out_dir = cfg.path("paths", "forecasts_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "model_selection_summary.csv", index=False)
    pd.DataFrame(forecast_rows).to_csv(out_dir / "forecasts.csv", index=False)
    logger.info("Exported forecast tables to %s", out_dir)
    logger.info("=== Forecasting complete: %d series, persisted to warehouse ===", len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
