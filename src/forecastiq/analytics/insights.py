"""Rule-based business insights engine.

Each rule reads the warehouse (reusing the analytics modules) and emits zero or more
``Insight`` objects. Thresholds are derived from the data itself (medians, growth signs,
volume floors) rather than hardcoded, so insights stay valid as the data changes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
from sqlalchemy.engine import Engine

from . import products, regional, returns
from .base import growth_pct, read


@dataclass
class Insight:
    category: str          # growth | risk | opportunity | seasonality | returns | regional
    title: str
    detail: str
    metric: float | None = None


# --------------------------------------------------------------------------- helpers
def _category_revenue_by_year(engine: Engine) -> pd.DataFrame:
    return read(
        engine,
        """
        SELECT p.category, d.year, SUM(f.sales) AS revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_date d    ON f.order_date_key = d.date_key
        GROUP BY p.category, d.year
        """,
    )


# --------------------------------------------------------------------------- rules
def _category_growth_insights(engine: Engine) -> list[Insight]:
    df = _category_revenue_by_year(engine)
    years = sorted(df["year"].unique())
    if len(years) < 2:
        return []
    last, prev = years[-1], years[-2]
    pivot = df.pivot(index="category", columns="year", values="revenue").fillna(0.0)
    growth = {cat: growth_pct(pivot.loc[cat, last], pivot.loc[cat, prev]) for cat in pivot.index}
    growth = {c: g for c, g in growth.items() if g is not None}
    if not growth:
        return []

    out: list[Insight] = []
    fastest = max(growth, key=growth.get)
    out.append(Insight(
        "growth",
        f"Fastest-growing category: {fastest}",
        f"{fastest} revenue grew {growth[fastest]:.1f}% in {last} vs {prev}.",
        growth[fastest],
    ))
    declining = sorted([(c, g) for c, g in growth.items() if g < 0], key=lambda x: x[1])
    if declining:
        names = ", ".join(f"{c} ({g:.1f}%)" for c, g in declining)
        out.append(Insight(
            "risk",
            "Declining categories",
            f"Categories with negative YoY revenue growth in {last}: {names}.",
            declining[0][1],
        ))
    return out


def _regional_insights(engine: Engine) -> list[Insight]:
    df = regional.region_performance(engine)
    if df.empty:
        return []
    out: list[Insight] = []
    best = df.iloc[0]  # already sorted by revenue desc
    out.append(Insight(
        "regional",
        f"Best-performing region: {best['region']} ({best['market']})",
        f"{best['region']} leads on revenue at ${best['revenue']:,.0f} "
        f"({best['profit_margin_pct']:.1f}% margin).",
        float(best["revenue"]),
    ))
    # Weakest = lowest margin among regions with above-median revenue (ignore tiny regions).
    meaningful = df[df["revenue"] >= df["revenue"].median()]
    if not meaningful.empty:
        weak = meaningful.sort_values("profit_margin_pct").iloc[0]
        out.append(Insight(
            "regional",
            f"Weakest margin region: {weak['region']} ({weak['market']})",
            f"{weak['region']} has the thinnest margin among major regions at "
            f"{weak['profit_margin_pct']:.1f}% on ${weak['revenue']:,.0f} revenue.",
            float(weak["profit_margin_pct"]),
        ))
    return out


def _returns_insights(engine: Engine, min_orders: int = 20) -> list[Insight]:
    df = returns.return_rate_by_product(engine, min_orders=min_orders, n=5)
    if df.empty:
        return []
    top = df.iloc[0]
    return [Insight(
        "returns",
        f"Highest-returning product: {top['product_name']}",
        f"{top['product_name']} has a {top['return_rate_pct']:.1f}% return rate over "
        f"{int(top['orders'])} orders (min {min_orders} orders considered).",
        float(top["return_rate_pct"]),
    )]


def _seasonality_insight(engine: Engine) -> list[Insight]:
    df = read(
        engine,
        """
        SELECT d.month, d.month_name,
               SUM(f.sales) AS revenue,
               COUNT(DISTINCT d.year) AS years
        FROM fact_sales f
        JOIN dim_date d ON f.order_date_key = d.date_key
        GROUP BY d.month, d.month_name
        """,
    )
    if df.empty:
        return []
    df["avg_revenue"] = df["revenue"] / df["years"]
    overall = df["avg_revenue"].mean()
    peak = df.loc[df["avg_revenue"].idxmax()]
    lift = growth_pct(peak["avg_revenue"], overall)
    return [Insight(
        "seasonality",
        f"Seasonal peak in {peak['month_name']}",
        f"{peak['month_name']} is the strongest month on average "
        f"(~{lift:.0f}% above the typical month).",
        float(lift) if lift is not None else None,
    )]


def _opportunity_insight(engine: Engine) -> list[Insight]:
    df = products.subcategory_performance(engine)
    if df.empty:
        return []
    # High-margin sub-categories at meaningful volume are the scale-up opportunities.
    meaningful = df[df["revenue"] >= df["revenue"].median()]
    if meaningful.empty:
        return []
    best = meaningful.sort_values("profit_margin_pct", ascending=False).iloc[0]
    return [Insight(
        "opportunity",
        f"High-profit opportunity: {best['sub_category']}",
        f"{best['sub_category']} ({best['category']}) earns a {best['profit_margin_pct']:.1f}% "
        f"margin on ${best['revenue']:,.0f} revenue - a candidate to scale.",
        float(best["profit_margin_pct"]),
    )]


def _loss_maker_insight(engine: Engine) -> list[Insight]:
    df = products.low_performing_products(engine, n=None)   # all loss-makers for a true count
    if df.empty:
        return []
    total_loss = float(df["profit"].sum())
    worst = df.iloc[0]
    return [Insight(
        "risk",
        f"{len(df)} loss-making products",
        f"{len(df)} products post negative profit, eroding ${abs(total_loss):,.0f} in total; "
        f"worst is {worst['product_name']} (${worst['profit']:,.0f}).",
        total_loss,
    )]


_RULES = (
    _category_growth_insights,
    _regional_insights,
    _returns_insights,
    _seasonality_insight,
    _opportunity_insight,
    _loss_maker_insight,
)


def generate_insights(engine: Engine) -> list[Insight]:
    """Run every rule and return the collected insights."""
    insights: list[Insight] = []
    for rule in _RULES:
        insights.extend(rule(engine))
    return insights


def insights_to_frame(insights: list[Insight]) -> pd.DataFrame:
    """Tabular view of insights for printing/export."""
    return pd.DataFrame([asdict(i) for i in insights], columns=["category", "title", "detail", "metric"])
