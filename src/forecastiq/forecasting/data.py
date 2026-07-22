"""Data preparation for forecasting.

Turns the warehouse fact table into clean univariate time series at a chosen
aggregation level (total, category, region, market, product) and grain
(monthly or quarterly). Missing periods are gap-filled so models see a regular
frequency index.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

_ALLOWED_TARGETS = {"sales", "quantity", "profit"}

# level -> (join clause, filter column)
_LEVEL = {
    "category": ("JOIN dim_product p ON f.product_key = p.product_key", "p.category"),
    "product": ("JOIN dim_product p ON f.product_key = p.product_key", "p.product_id"),
    "region": ("JOIN dim_region r ON f.region_key = r.region_key", "r.region"),
    "market": ("JOIN dim_region r ON f.region_key = r.region_key", "r.market"),
}

_FREQ = {"monthly": "MS", "quarterly": "QS"}


def build_series(
    engine: Engine,
    target: str = "sales",
    granularity: str = "monthly",
    level: str = "total",
    key: str | None = None,
) -> pd.Series:
    """Return a gap-filled time series for one slice of the business.

    Parameters
    ----------
    target : one of sales | quantity | profit
    granularity : monthly | quarterly
    level : total | category | region | market | product
    key : the specific category/region/... to filter to (ignored for ``total``)
    """
    if target not in _ALLOWED_TARGETS:
        raise ValueError(f"target must be one of {_ALLOWED_TARGETS}")
    if granularity not in _FREQ:
        raise ValueError(f"granularity must be one of {set(_FREQ)}")

    join, params = "", {}
    where = ""
    if level != "total":
        if level not in _LEVEL:
            raise ValueError(f"level must be 'total' or one of {set(_LEVEL)}")
        join, col = _LEVEL[level]
        where = f"WHERE {col} = :key"
        params = {"key": key}

    sql = text(
        f"""
        SELECT printf('%04d-%02d-01', d.year, d.month) AS period_start,
               SUM(f.{target}) AS value
        FROM fact_sales f
        JOIN dim_date d ON f.order_date_key = d.date_key
        {join}
        {where}
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        """
    )
    df = pd.read_sql(sql, engine, params=params or None)
    if df.empty:
        return pd.Series(dtype=float, name=target)

    s = pd.Series(df["value"].to_numpy(dtype=float), index=pd.to_datetime(df["period_start"]))
    s = s.asfreq("MS").fillna(0.0)  # continuous monthly grid; missing months -> 0
    if granularity == "quarterly":
        s = s.resample("QS").sum()
    s.name = target
    s.index.name = "period_start"
    return s


def list_keys(engine: Engine, level: str) -> list[str]:
    """Distinct keys available at a level (e.g. all categories), for enumerating series."""
    if level not in _LEVEL:
        raise ValueError(f"level must be one of {set(_LEVEL)}")
    _, col = _LEVEL[level]
    join = _LEVEL[level][0]
    df = pd.read_sql(
        text(f"SELECT DISTINCT {col} AS k FROM fact_sales f {join} ORDER BY {col}"), engine
    )
    return [k for k in df["k"].tolist() if k not in (None, "")]


def series_id(level: str, key: str | None) -> str:
    """Canonical series identifier used for persistence, e.g. 'category:Technology'."""
    return "total" if level == "total" or key is None else f"{level}:{key}"
