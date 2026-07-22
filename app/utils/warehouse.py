"""Warehouse access + global filtering.

Filtering is applied by materialising a **scoped in-memory SQLite warehouse**: the fact
table is copied filtered by the active ``FactScope`` (via dimension joins), the
dimensions are copied whole, and the analytical views are recreated. The existing
``forecastiq.analytics`` / ``forecastiq.forecasting`` modules then run against this
engine **unchanged** — no analytics logic is duplicated. Unfiltered pages use the base
(on-disk) engine directly for speed. All builders are cached per scope.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from forecastiq.config import Config
from forecastiq.utils.io import get_engine, run_sql_script

from .scope import FactScope

_DIMS = ("dim_date", "dim_customer", "dim_product", "dim_region")
_FACT_JOINS = (
    "JOIN dim_date d     ON f.order_date_key = d.date_key "
    "JOIN dim_product p  ON f.product_key   = p.product_key "
    "JOIN dim_region r   ON f.region_key    = r.region_key "
    "JOIN dim_customer c ON f.customer_key  = c.customer_key"
)


@st.cache_resource(show_spinner=False)
def _config() -> Config:
    return Config.load()


@st.cache_resource(show_spinner=False)
def base_engine() -> Engine:
    """The on-disk warehouse engine."""
    return get_engine(_config().db_url)


@st.cache_resource(show_spinner=False)
def _scoped_engine(scope: FactScope) -> Engine:
    """Build a filtered in-memory warehouse for ``scope`` (cached per scope)."""
    base = base_engine()
    mem = create_engine(
        "sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    fact = pd.read_sql(text(f"SELECT f.* FROM fact_sales f {_FACT_JOINS} {scope.where()}"), base)
    fact.to_sql("fact_sales", mem, index=False)
    for dim in _DIMS:
        pd.read_sql(text(f"SELECT * FROM {dim}"), base).to_sql(dim, mem, index=False)
    run_sql_script(mem, _config().root / "sql" / "views.sql")
    return mem


def engine_for(scope: FactScope) -> Engine:
    """Return the base engine when no filters are active, else a scoped in-memory one."""
    return base_engine() if scope.is_empty() else _scoped_engine(scope)


def warehouse_exists() -> bool:
    """True if the on-disk SQLite warehouse is present (ETL has been run)."""
    url = _config().db_url
    prefix = "sqlite:///"
    if url.startswith(prefix):
        return Path(url[len(prefix) :]).exists()
    return True  # non-SQLite backends: assume reachable


@st.cache_data(show_spinner=False)
def filter_options() -> dict[str, list]:
    """Distinct values for every sidebar filter, read once from the base warehouse."""
    e = base_engine()

    def distinct(col: str, table: str, join: str = "") -> list:
        df = pd.read_sql(
            text(
                f"SELECT DISTINCT {col} AS v FROM {table} {join} "
                f"WHERE {col} IS NOT NULL ORDER BY {col}"
            ),
            e,
        )
        return df["v"].tolist()

    return {
        "years": distinct(
            "year", "dim_date d", "JOIN fact_sales f ON f.order_date_key = d.date_key"
        ),
        "markets": distinct("market", "dim_region"),
        "regions": distinct("region", "dim_region"),
        "countries": distinct("country", "dim_region"),
        "categories": distinct("category", "dim_product"),
        "sub_categories": distinct("sub_category", "dim_product"),
        "segments": distinct("segment", "dim_customer"),
    }


@st.cache_data(show_spinner=False)
def warehouse_stats() -> dict:
    """Headline warehouse statistics for the Home page."""
    e = base_engine()

    def scalar(sql: str):
        return pd.read_sql(text(sql), e).iloc[0, 0]

    span = pd.read_sql(text("SELECT MIN(full_date) lo, MAX(full_date) hi FROM dim_date"), e).iloc[0]
    return {
        "fact_rows": int(scalar("SELECT COUNT(*) FROM fact_sales")),
        "customers": int(scalar("SELECT COUNT(*) FROM dim_customer")),
        "products": int(scalar("SELECT COUNT(*) FROM dim_product")),
        "regions": int(scalar("SELECT COUNT(*) FROM dim_region")),
        "months": int(scalar("SELECT COUNT(*) FROM vw_monthly_sales")),
        "date_min": str(span["lo"]),
        "date_max": str(span["hi"]),
        "has_forecasts": int(scalar("SELECT COUNT(*) FROM forecast_results")) > 0,
    }
