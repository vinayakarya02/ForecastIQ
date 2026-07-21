"""IO & database helpers shared across the pipeline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def read_csv_robust(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read a CSV, tolerating the common utf-8 / latin-1 encoding split."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Download the CSV and place it there "
            f"(see docs/installation.md)."
        )
    last_err: Exception | None = None
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:  # pragma: no cover - depends on file
            last_err = e
    raise last_err  # type: ignore[misc]


def get_engine(db_url: str, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for SQLite (default) or PostgreSQL."""
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, echo=echo, connect_args=connect_args, future=True)


def run_sql_script(engine: Engine, sql_path: str | Path) -> None:
    """Execute a multi-statement .sql file (DDL / views)."""
    sql = Path(sql_path).read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        if engine.dialect.name == "sqlite":
            cur.executescript(sql)          # handles comments, PRAGMA, many statements
        else:  # pragma: no cover - postgres path
            cur.execute(sql)                # psycopg2 accepts multi-statement strings
        raw.commit()
    finally:
        raw.close()


def df_to_table(df: pd.DataFrame, table: str, engine: Engine, if_exists: str = "append") -> int:
    """Write a DataFrame to a table; returns rows written.

    Uses pandas' default executemany (not ``method='multi'``) to stay well within
    SQLite's per-statement variable limit regardless of column count.
    """
    df.to_sql(table, engine, if_exists=if_exists, index=False, chunksize=1000)
    return len(df)


def query_df(sql: str, engine: Engine) -> pd.DataFrame:
    """Run a SQL query and return the result as a DataFrame."""
    return pd.read_sql(sql, engine)
