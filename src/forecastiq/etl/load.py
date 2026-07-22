"""Stage 5 — Load: (re)create the schema and write dimensions, fact, and views."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy.engine import Engine

from ..config import Config
from ..utils.io import df_to_table, get_engine, run_sql_script

# Load dimensions before the fact so foreign keys resolve.
_LOAD_ORDER = ["dim_date", "dim_customer", "dim_product", "dim_region", "fact_sales"]


def load(
    tables: dict[str, pd.DataFrame], cfg: Config, logger=None, engine: Engine | None = None
) -> dict[str, int]:
    """Create schema + views and bulk-load the star schema. Returns per-table row counts."""
    engine = engine or get_engine(cfg.db_url, echo=cfg["database"].get("echo", False))

    run_sql_script(engine, cfg.root / "sql" / "schema.sql")
    if logger:
        logger.info("Schema created at %s", cfg.db_url)

    summary: dict[str, int] = {}
    for table in _LOAD_ORDER:
        summary[table] = df_to_table(tables[table], table, engine, if_exists="append")
        if logger:
            logger.info("Loaded %-14s %7d rows", table, summary[table])

    run_sql_script(engine, cfg.root / "sql" / "views.sql")
    if logger:
        logger.info("Analytical views created")
    return summary


def write_quality_log(
    report: pd.DataFrame, cfg: Config, run_id: str, engine: Engine | None = None
) -> None:
    """Persist the validation report into ``data_quality_log`` for auditability."""
    engine = engine or get_engine(cfg.db_url)
    now = datetime.now().isoformat(timespec="seconds")
    rows = report.rename(columns={"check_name": "check_name"}).copy()
    rows["run_id"] = run_id
    rows["created_at"] = now
    rows = rows[["run_id", "check_name", "status", "detail", "rows_flagged", "created_at"]]
    df_to_table(rows, "data_quality_log", engine, if_exists="append")
