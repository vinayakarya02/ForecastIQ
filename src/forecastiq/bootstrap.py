"""Self-provisioning bootstrap.

Builds the warehouse (ETL + forecasts) in-process **only if it doesn't already exist**,
so the app and container can start with zero manual steps. Data-source resolution:

1. If the real dataset is present at ``source.path`` -> use it ("real").
2. Otherwise generate a synthetic sample workbook and build from that ("sample").

This lets a fresh clone (e.g. Streamlit Community Cloud, where the copyrighted dataset is
git-ignored and absent) come up as a working demo without committing any dataset.
"""

from __future__ import annotations

import os
import warnings
from datetime import datetime
from pathlib import Path

from .config import Config
from .sample import write_sample_workbook
from .utils.logger import get_logger


def _db_path(cfg: Config) -> Path | None:
    url = cfg.db_url
    prefix = "sqlite:///"
    return Path(url[len(prefix) :]) if url.startswith(prefix) else None


def _run_etl(cfg: Config, logger) -> None:
    from .etl.clean import clean
    from .etl.extract import extract
    from .etl.load import load, write_quality_log
    from .etl.transform import transform
    from .etl.validate import validate

    run_id = datetime.now().strftime("etl_%Y%m%d_%H%M%S")
    cleaned = clean(extract(cfg, logger), cfg, logger)
    report, ok = validate(cleaned, cfg, logger)
    if not ok:
        raise RuntimeError("Source data failed validation during bootstrap.")
    load(transform(cleaned, cfg, logger), cfg, logger)
    write_quality_log(report, cfg, run_id)


def _run_forecast(cfg: Config, logger) -> None:
    from .forecasting import data as fdata
    from .forecasting import models as fmodels
    from .forecasting import predictor
    from .utils.io import get_engine

    fcfg = cfg["forecasting"]
    period = 4 if fcfg["granularity"] == "quarterly" else fcfg.get("seasonal_period", 12)
    factories = fmodels.build_model_factories(fcfg["models"], period)
    engine = get_engine(cfg.db_url)
    predictor.clear_forecasts(engine)
    run_id = datetime.now().strftime("fc_%Y%m%d_%H%M%S")

    plan = [("total", None)] + [("category", k) for k in fdata.list_keys(engine, "category")]
    min_len = fcfg["backtest_folds"] * fcfg["horizon"] + 3
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for level, key in plan:
            y = fdata.build_series(engine, fcfg["target"], fcfg["granularity"], level, key)
            if len(y) < min_len:
                continue
            sf = predictor.forecast_series(
                y,
                factories,
                horizon=fcfg["horizon"],
                n_folds=fcfg["backtest_folds"],
                selection_metric=fcfg["selection_metric"],
                series_id=fdata.series_id(level, key),
                granularity=fcfg["granularity"],
            )
            predictor.persist(engine, sf, run_id)


def ensure_warehouse(
    cfg: Config | None = None,
    logger=None,
    with_forecast: bool = True,
    sample_path: str | Path | None = None,
) -> str:
    """Build the warehouse if missing. Returns 'existing', 'real', or 'sample'."""
    cfg = cfg or Config.load()
    logger = logger or get_logger()

    db_path = _db_path(cfg)
    if db_path is None:  # external (e.g. Postgres) DB: assume it is provisioned
        return "existing"
    if db_path.exists():
        return "existing"

    if cfg.source_path.exists():
        mode = "real"
        logger.info("Bootstrap: building warehouse from dataset at %s", cfg.source_path.name)
    else:
        mode = "sample"
        sample = (
            Path(sample_path)
            if sample_path
            else cfg.root / "data" / "raw" / "sample_superstore.xlsx"
        )
        write_sample_workbook(sample)
        os.environ["FORECASTIQ_SOURCE_PATH"] = str(sample)
        logger.info("Bootstrap: no dataset found — generated synthetic sample data.")

    _run_etl(cfg, logger)
    if with_forecast:
        _run_forecast(cfg, logger)
    logger.info("Bootstrap complete (%s data).", mode)
    return mode


if __name__ == "__main__":
    print("Warehouse source:", ensure_warehouse())
