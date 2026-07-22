"""Returns analytics — return rates by region/category/product and returned value.

Returns are recorded at the order grain (an order is returned or not), so return
rate = returned distinct orders / total distinct orders. Returned revenue/profit sum
the line-level measures on returned orders.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from .base import pct, read

_RATE_SQL = """
SELECT {select}
       COUNT(DISTINCT f.order_id) AS orders,
       COUNT(DISTINCT CASE WHEN f.is_returned = 1 THEN f.order_id END) AS returned_orders,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.is_returned = 1 THEN f.order_id END)
             / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS return_rate_pct,
       ROUND(SUM(CASE WHEN f.is_returned = 1 THEN f.sales ELSE 0 END), 2) AS returned_revenue
FROM fact_sales f
{join}
GROUP BY {group}
ORDER BY return_rate_pct DESC
"""


def return_rate_by_region(engine: Engine) -> pd.DataFrame:
    """Return rate by market → region (from the vw_return_rate view)."""
    return read(
        engine,
        "SELECT market, region, orders, returned_orders, return_rate_pct, returned_revenue "
        "FROM vw_return_rate ORDER BY return_rate_pct DESC",
    )


def return_rate_by_category(engine: Engine) -> pd.DataFrame:
    """Return rate by product category."""
    return read(
        engine,
        _RATE_SQL.format(
            select="p.category,",
            join="JOIN dim_product p ON f.product_key = p.product_key",
            group="p.category",
        ),
    )


def return_rate_by_product(engine: Engine, min_orders: int = 20, n: int = 20) -> pd.DataFrame:
    """Highest return rates at product grain, filtered to meaningful volume.

    ``min_orders`` guards against tiny-sample noise (a 1/1 return is not "100%").
    """
    df = read(
        engine,
        _RATE_SQL.format(
            select="p.product_id, p.product_name, p.category,",
            join="JOIN dim_product p ON f.product_key = p.product_key",
            group="p.product_id, p.product_name, p.category",
        ),
    )
    df = df[df["orders"] >= int(min_orders)]
    return df.sort_values("return_rate_pct", ascending=False).head(int(n)).reset_index(drop=True)


def returned_totals(engine: Engine) -> dict:
    """Total returned revenue/profit and their share of the overall business."""
    row = read(
        engine,
        """
        SELECT
            ROUND(SUM(CASE WHEN is_returned = 1 THEN sales  ELSE 0 END), 2) AS returned_revenue,
            ROUND(SUM(CASE WHEN is_returned = 1 THEN profit ELSE 0 END), 2) AS returned_profit,
            ROUND(SUM(sales), 2)  AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit,
            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(DISTINCT CASE WHEN is_returned = 1 THEN order_id END) AS returned_orders
        FROM fact_sales
        """,
    ).iloc[0]
    return {
        "returned_revenue": float(row["returned_revenue"]),
        "returned_profit": float(row["returned_profit"]),
        "returned_orders": int(row["returned_orders"]),
        "total_orders": int(row["total_orders"]),
        "return_rate_pct": pct(int(row["returned_orders"]), int(row["total_orders"])),
        "returned_revenue_share_pct": pct(
            float(row["returned_revenue"]), float(row["total_revenue"])
        ),
    }
