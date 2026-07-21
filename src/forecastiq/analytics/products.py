"""Product analytics — category, sub-category and product performance."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from .base import read

# Reusable product-grain aggregation. {level} is substituted with the GROUP BY columns.
_PERF_SQL = """
SELECT {select}
       ROUND(SUM(f.sales), 2)  AS revenue,
       ROUND(SUM(f.profit), 2) AS profit,
       SUM(f.quantity)         AS units,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales), 0), 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY {group}
ORDER BY revenue DESC
"""


def category_performance(engine: Engine) -> pd.DataFrame:
    """Revenue, profit, units and margin by product category."""
    return read(engine, _PERF_SQL.format(select="p.category,", group="p.category"))


def subcategory_performance(engine: Engine) -> pd.DataFrame:
    """Performance by category → sub-category."""
    return read(
        engine, _PERF_SQL.format(select="p.category, p.sub_category,", group="p.category, p.sub_category")
    )


def product_performance(engine: Engine) -> pd.DataFrame:
    """Performance at the individual product grain."""
    return read(
        engine,
        _PERF_SQL.format(
            select="p.product_id, p.product_name, p.category,",
            group="p.product_id, p.product_name, p.category",
        ),
    )


def top_products(engine: Engine, n: int = 10) -> pd.DataFrame:
    """Top ``n`` products by revenue."""
    return product_performance(engine).head(int(n)).reset_index(drop=True)


def low_performing_products(engine: Engine, n: int | None = 10) -> pd.DataFrame:
    """Loss-making products — biggest negative total profit first.

    Flags products that erode profit despite generating revenue, ranked by the size
    of the loss so the worst offenders surface first. ``n=None`` returns all of them.
    """
    df = product_performance(engine)
    losers = df[df["profit"] < 0].sort_values("profit").reset_index(drop=True)
    if n is not None:
        losers = losers.head(int(n)).reset_index(drop=True)
    return losers
