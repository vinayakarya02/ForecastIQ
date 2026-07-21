"""Regional analytics — performance at every geography grain plus region manager."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from .base import read

_PERF_SQL = """
SELECT {select}
       ROUND(SUM(f.sales), 2)  AS revenue,
       ROUND(SUM(f.profit), 2) AS profit,
       COUNT(DISTINCT f.order_id)     AS orders,
       COUNT(DISTINCT f.customer_key) AS customers,
       ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales), 0), 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY {group}
ORDER BY revenue DESC
"""


def market_performance(engine: Engine) -> pd.DataFrame:
    """Performance by macro market (APAC, EU, US, LATAM, …)."""
    return read(engine, _PERF_SQL.format(select="r.market,", group="r.market"))


def region_performance(engine: Engine) -> pd.DataFrame:
    """Performance by market → region."""
    return read(engine, _PERF_SQL.format(select="r.market, r.region,", group="r.market, r.region"))


def country_performance(engine: Engine) -> pd.DataFrame:
    """Performance by country."""
    return read(engine, _PERF_SQL.format(select="r.country,", group="r.country"))


def state_performance(engine: Engine) -> pd.DataFrame:
    """Performance by country → state."""
    return read(engine, _PERF_SQL.format(select="r.country, r.state,", group="r.country, r.state"))


def city_performance(engine: Engine) -> pd.DataFrame:
    """Performance by country → city."""
    return read(engine, _PERF_SQL.format(select="r.country, r.city,", group="r.country, r.city"))


def region_manager_performance(engine: Engine) -> pd.DataFrame:
    """Performance by regional manager (from the People sheet)."""
    return read(
        engine, _PERF_SQL.format(select="r.region_manager,", group="r.region_manager")
    )
