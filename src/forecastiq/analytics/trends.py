"""Sales trend analytics — revenue over time at multiple grains, plus growth."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from .base import read


def monthly_revenue(engine: Engine) -> pd.DataFrame:
    """Monthly revenue/profit/units/orders (from the vw_monthly_sales view)."""
    return read(
        engine,
        "SELECT period_start, revenue, profit, units, orders "
        "FROM vw_monthly_sales ORDER BY period_start",
    )


def quarterly_revenue(engine: Engine) -> pd.DataFrame:
    """Revenue and profit aggregated to calendar quarters."""
    return read(
        engine,
        """
        SELECT d.year,
               d.quarter,
               printf('%d-Q%d', d.year, d.quarter) AS period,
               ROUND(SUM(f.sales), 2)  AS revenue,
               ROUND(SUM(f.profit), 2) AS profit
        FROM fact_sales f
        JOIN dim_date d ON f.order_date_key = d.date_key
        GROUP BY d.year, d.quarter
        ORDER BY d.year, d.quarter
        """,
    )


def yearly_revenue(engine: Engine) -> pd.DataFrame:
    """Yearly revenue/profit with year-over-year growth %."""
    df = read(
        engine,
        """
        SELECT d.year,
               ROUND(SUM(f.sales), 2)  AS revenue,
               ROUND(SUM(f.profit), 2) AS profit,
               COUNT(DISTINCT f.order_id) AS orders
        FROM fact_sales f
        JOIN dim_date d ON f.order_date_key = d.date_key
        GROUP BY d.year
        ORDER BY d.year
        """,
    )
    df["yoy_growth_pct"] = (df["revenue"].pct_change() * 100).round(2)
    return df


def mom_growth(engine: Engine) -> pd.DataFrame:
    """Month-over-month revenue growth (from the vw_monthly_growth view)."""
    return read(
        engine,
        "SELECT period_start, revenue, prev_revenue, mom_growth_pct "
        "FROM vw_monthly_growth ORDER BY period_start",
    )


def yoy_growth(engine: Engine) -> pd.DataFrame:
    """Month-over-month-a-year-ago growth: revenue vs the same month last year."""
    df = monthly_revenue(engine)[["period_start", "revenue"]].copy()
    df["yoy_growth_pct"] = (df["revenue"].pct_change(periods=12) * 100).round(2)
    return df


def revenue_trend(engine: Engine, window: int = 3) -> pd.DataFrame:
    """Monthly revenue with a rolling-average smoothed trend line."""
    df = monthly_revenue(engine)[["period_start", "revenue"]].copy()
    df[f"revenue_{window}m_avg"] = df["revenue"].rolling(window, min_periods=1).mean().round(2)
    return df


def profit_trend(engine: Engine, window: int = 3) -> pd.DataFrame:
    """Monthly profit with a rolling-average smoothed trend line."""
    df = monthly_revenue(engine)[["period_start", "profit"]].copy()
    df[f"profit_{window}m_avg"] = df["profit"].rolling(window, min_periods=1).mean().round(2)
    return df
