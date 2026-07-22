"""Customer analytics — RFM segmentation, basic CLV, repeat behaviour, top customers."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from .base import pct, read

# RFM quartile scoring on top of the vw_customer_rfm view.
# Recency is inverted (more recent = higher score). Segments are rule-based on scores.
_RFM_SQL = """
WITH scored AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        recency_days,
        frequency,
        monetary,
        5 - NTILE(4) OVER (ORDER BY recency_days) AS r_score,
        NTILE(4) OVER (ORDER BY frequency)        AS f_score,
        NTILE(4) OVER (ORDER BY monetary)         AS m_score
    FROM vw_customer_rfm
)
SELECT
    customer_id, customer_name, segment,
    recency_days, frequency, monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 2                  THEN 'Loyal'
        WHEN r_score >= 3 AND f_score = 1                   THEN 'New / Promising'
        WHEN r_score = 2                                    THEN 'At Risk'
        ELSE 'Hibernating'
    END AS rfm_segment
FROM scored
ORDER BY rfm_total DESC
"""


def rfm(engine: Engine) -> pd.DataFrame:
    """Per-customer RFM scores (1-4 each) and a rule-based segment label."""
    return read(engine, _RFM_SQL)


def rfm_segment_summary(engine: Engine) -> pd.DataFrame:
    """Customer count, revenue and average monetary value per RFM segment."""
    df = rfm(engine)
    summary = (
        df.groupby("rfm_segment")
        .agg(
            customers=("customer_id", "nunique"),
            revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    summary["revenue"] = summary["revenue"].round(2)
    summary["avg_monetary"] = summary["avg_monetary"].round(2)
    return summary


def customer_lifetime_value(engine: Engine) -> pd.DataFrame:
    """Basic (historical) CLV per customer.

    ``clv_basic`` is the customer's total historical revenue (monetary value). A fuller
    model would multiply average order value by predicted lifespan/retention; this
    keeps to observed history so it is fully interview-defendable.
    """
    return read(
        engine,
        """
        SELECT
            c.customer_id,
            c.customer_name,
            c.segment,
            COUNT(DISTINCT f.order_id)                       AS orders,
            SUM(f.quantity)                                  AS units,
            ROUND(SUM(f.sales), 2)                           AS clv_basic,
            ROUND(SUM(f.profit), 2)                          AS profit,
            ROUND(SUM(f.sales) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.customer_id, c.customer_name, c.segment
        ORDER BY clv_basic DESC
        """,
    )


def repeat_customers(engine: Engine) -> dict:
    """Repeat-purchase summary across the customer base."""
    df = read(
        engine,
        "SELECT customer_key, COUNT(DISTINCT order_id) AS orders FROM fact_sales GROUP BY customer_key",
    )
    total = len(df)
    repeat = int((df["orders"] > 1).sum())
    return {
        "total_customers": total,
        "repeat_customers": repeat,
        "one_time_customers": total - repeat,
        "repeat_rate_pct": pct(repeat, total),
        "avg_orders_per_customer": round(float(df["orders"].mean()), 2) if total else 0.0,
    }


def top_customers(engine: Engine, n: int = 10) -> pd.DataFrame:
    """Top ``n`` customers by historical revenue (CLV)."""
    return customer_lifetime_value(engine).head(int(n)).reset_index(drop=True)
