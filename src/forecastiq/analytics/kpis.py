"""Executive KPIs — the headline numbers for the whole business."""
from __future__ import annotations

from sqlalchemy.engine import Engine

from .base import pct, read, safe_div


def executive_kpis(engine: Engine) -> dict:
    """Return the headline KPI bundle as a dict of ``metric -> value``.

    Definitions:
        profit_margin_pct = profit / revenue
        avg_order_value   = revenue / distinct orders
        avg_selling_price = revenue / units sold
        return_rate_pct   = returned orders / distinct orders
    """
    row = read(
        engine,
        """
        SELECT
            COALESCE(SUM(sales), 0)   AS total_revenue,
            COALESCE(SUM(profit), 0)  AS total_profit,
            COALESCE(SUM(quantity), 0) AS total_units,
            COUNT(DISTINCT order_id)  AS total_orders,
            COUNT(DISTINCT customer_key) AS total_customers,
            COUNT(DISTINCT CASE WHEN is_returned = 1 THEN order_id END) AS returned_orders
        FROM fact_sales
        """,
    ).iloc[0]

    revenue = float(row["total_revenue"])
    profit = float(row["total_profit"])
    units = int(row["total_units"])
    orders = int(row["total_orders"])
    customers = int(row["total_customers"])
    returned_orders = int(row["returned_orders"])

    return {
        "total_revenue": round(revenue, 2),
        "total_profit": round(profit, 2),
        "profit_margin_pct": pct(profit, revenue),
        "total_orders": orders,
        "total_customers": customers,
        "total_units": units,
        "avg_order_value": round(safe_div(revenue, orders) or 0.0, 2),
        "avg_selling_price": round(safe_div(revenue, units) or 0.0, 2),
        "return_rate_pct": pct(returned_orders, orders),
    }
