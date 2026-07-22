"""Self-provisioning bootstrap.

Builds the warehouse (ETL + forecasts) in-process so the app and container start with
zero manual steps. Data-source resolution:

1. If the real dataset is present at ``source.path`` -> build from it ("real").
2. Otherwise generate a synthetic sample workbook and build from that ("sample").

Provenance is recorded in a ``warehouse_meta`` table so later runs know whether the
existing warehouse holds real or sample data. If a warehouse was built from the sample
but the real dataset later becomes available, it is refreshed from the real data.
"""

from __future__ import annotations

import os
import sqlite3
import warnings
from datetime import datetime
from pathlib import Path

from .config import Config
from .sample import write_sample_workbook
from .utils.logger import get_logger

_META_TABLE = "warehouse_meta"


def _db_path(cfg: Config) -> Path | None:
    url = cfg.db_url
    prefix = "sqlite:///"
    return Path(url[len(prefix) :]) if url.startswith(prefix) else None


def _read_meta(db_path: Path) -> str | None:
    """Recorded data mode of an existing SQLite warehouse ('real'|'sample'), else None."""
    if not db_path.exists():
        return None
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(f"SELECT data_mode FROM {_META_TABLE} LIMIT 1").fetchone()
        return row[0] if row else None
    except sqlite3.Error:  # empty file or no meta table yet
        return None
    finally:
        con.close()


def _write_meta(db_path: Path, mode: str, source_name: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {_META_TABLE} "
            "(data_mode TEXT, source_name TEXT, built_at TEXT)"
        )
        con.execute(f"DELETE FROM {_META_TABLE}")
        con.execute(
            f"INSERT INTO {_META_TABLE} (data_mode, source_name, built_at) VALUES (?, ?, ?)",
            (mode, source_name, datetime.now().isoformat(timespec="seconds")),
        )
        con.commit()
    finally:
        con.close()


def record_data_mode(cfg: Config, mode: str, source_name: str) -> None:
    """Record warehouse provenance (no-op for non-SQLite backends)."""
    db_path = _db_path(cfg)
    if db_path is not None and db_path.exists():
        _write_meta(db_path, mode, source_name)


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
    """Build the warehouse if missing. Returns 'existing', 'real', or 'sample'.

    An existing warehouse is reused as-is, except a sample-built one is rebuilt from the
    real dataset once that dataset becomes available.
    """
    cfg = cfg or Config.load()
    logger = logger or get_logger()

    db_path = _db_path(cfg)
    if db_path is None:  # external (e.g. Postgres) DB: assume it is provisioned
        return "existing"

    real_available = cfg.source_path.exists()

    if db_path.exists():
        recorded = _read_meta(db_path)
        if recorded == "sample" and real_available:
            logger.info(
                "Real dataset now present — refreshing warehouse from %s.", cfg.source_path.name
            )
            # fall through and rebuild from the real dataset
        elif recorded == "sample":
            return "sample"  # still no real data: keep the demo running
        else:
            return recorded or "existing"  # real-built or legacy warehouse: reuse as-is

    if real_available:
        mode, source_name = "real", cfg.source_path.name
        logger.info("Bootstrap: building warehouse from dataset %s", source_name)
    else:
        mode, source_name = "sample", "generated sample"
        sample = (
            Path(sample_path)
            if sample_path
            else cfg.root / "data" / "raw" / "sample_superstore.xlsx"
        )
        write_sample_workbook(sample)
        os.environ["FORECASTIQ_SOURCE_PATH"] = str(sample)
        logger.info("Bootstrap: no dataset found — generated synthetic sample data.")

    _run_etl(cfg, logger)
    _write_meta(db_path, mode, source_name)
    if with_forecast:
        _run_forecast(cfg, logger)
    logger.info("Bootstrap complete (%s data).", mode)
    return mode


if __name__ == "__main__":
    print("Warehouse source:", ensure_warehouse())
