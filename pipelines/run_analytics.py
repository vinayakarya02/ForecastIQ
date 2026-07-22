"""ForecastIQ analytics entrypoint: compute business analytics + insights from the warehouse.

Prints an executive summary to the console and exports every result table (plus the
generated insights) to ``reports/analytics/``.

Usage:
    python pipelines/run_analytics.py
    python pipelines/run_analytics.py --top 15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Make `import forecastiq` work when running this script directly, and make stdout
# tolerant of non-ASCII product names on Windows consoles.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    pass

from forecastiq.analytics import (  # noqa: E402
    insights,
    kpis,
    products,
    regional,
    returns,
    segmentation,
    trends,
)
from forecastiq.config import Config  # noqa: E402
from forecastiq.utils.io import get_engine  # noqa: E402
from forecastiq.utils.logger import get_logger  # noqa: E402


def _table(df: pd.DataFrame, n: int | None = None) -> str:
    view = df.head(n) if n else df
    try:
        from tabulate import tabulate

        return tabulate(view, headers="keys", tablefmt="github", showindex=False, floatfmt=",.2f")
    except ImportError:  # pragma: no cover
        return view.to_string(index=False)


def _section(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ForecastIQ analytics layer.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--top", type=int, default=10, help="Rows to show for top-N tables")
    args = parser.parse_args()

    cfg = Config.load(args.config)
    logger = get_logger()
    engine = get_engine(cfg.db_url)
    out_dir = cfg.path("paths", "reports_dir") / "analytics"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== ForecastIQ Analytics ===")

    # ---- Compute every analytics view ----
    kpi = kpis.executive_kpis(engine)
    tables: dict[str, pd.DataFrame] = {
        "monthly_revenue": trends.monthly_revenue(engine),
        "quarterly_revenue": trends.quarterly_revenue(engine),
        "yearly_revenue": trends.yearly_revenue(engine),
        "mom_growth": trends.mom_growth(engine),
        "category_performance": products.category_performance(engine),
        "subcategory_performance": products.subcategory_performance(engine),
        "top_products": products.top_products(engine, args.top),
        "low_performing_products": products.low_performing_products(engine, args.top),
        "market_performance": regional.market_performance(engine),
        "region_performance": regional.region_performance(engine),
        "country_performance": regional.country_performance(engine),
        "region_manager_performance": regional.region_manager_performance(engine),
        "rfm_segments": segmentation.rfm_segment_summary(engine),
        "top_customers": segmentation.top_customers(engine, args.top),
        "return_rate_by_region": returns.return_rate_by_region(engine),
        "return_rate_by_category": returns.return_rate_by_category(engine),
        "return_rate_by_product": returns.return_rate_by_product(engine),
    }
    repeat = segmentation.repeat_customers(engine)
    ret_tot = returns.returned_totals(engine)
    generated = insights.generate_insights(engine)
    tables["executive_kpis"] = pd.DataFrame([kpi])
    tables["insights"] = insights.insights_to_frame(generated)

    # ---- Console executive summary ----
    _section("EXECUTIVE KPIs")
    for key, value in kpi.items():
        label = key.replace("_", " ").title()
        if isinstance(value, float):
            print(f"   {label:22} {value:,.2f}")
        else:
            print(f"   {label:22} {value:,}")
    print(
        f"   {'Repeat Rate Pct':22} {repeat['repeat_rate_pct']:.2f}   "
        f"({repeat['repeat_customers']:,}/{repeat['total_customers']:,} customers)"
    )
    print(
        f"   {'Returned Revenue':22} {ret_tot['returned_revenue']:,.2f}   "
        f"({ret_tot['returned_revenue_share_pct']:.2f}% of revenue)"
    )

    _section("YEARLY REVENUE & YoY GROWTH")
    print(_table(tables["yearly_revenue"]))
    _section("CATEGORY PERFORMANCE")
    print(_table(tables["category_performance"]))
    _section("MARKET PERFORMANCE")
    print(_table(tables["market_performance"]))
    _section("RFM SEGMENTS")
    print(_table(tables["rfm_segments"]))
    _section("RETURN RATE BY REGION")
    print(_table(tables["return_rate_by_region"]))
    _section(f"BUSINESS INSIGHTS ({len(generated)})")
    for ins in generated:
        print(f"   [{ins.category.upper():11}] {ins.title}\n                 {ins.detail}")

    # ---- Export everything ----
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8")
    _write_insights_md(out_dir / "insights.md", generated, kpi)
    logger.info("Exported %d tables + insights.md to %s", len(tables), out_dir)
    return 0


def _write_insights_md(path: Path, generated, kpi: dict) -> None:
    lines = [
        "# ForecastIQ - Automated Business Insights\n",
        f"_Total revenue ${kpi['total_revenue']:,.0f} | "
        f"profit ${kpi['total_profit']:,.0f} | margin {kpi['profit_margin_pct']}%_\n",
    ]
    for ins in generated:
        lines.append(f"### [{ins.category.upper()}] {ins.title}\n{ins.detail}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
