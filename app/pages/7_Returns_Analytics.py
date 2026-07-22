"""Returns Analytics — return rate, returned value, trends, and hotspots."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from components import charts  # noqa: E402
from components.kpi import kpi_row  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.format import compact_money, number, pct  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Returns Analytics", "Return rates, returned value, and hotspots", "↩️")
scope_banner(scope)

totals = da.returned_totals(scope)
if totals["total_orders"] == 0:
    st.warning("No data for the current filters.")
    st.stop()

kpi_row(
    [
        {"label": "Return Rate", "value": pct(totals["return_rate_pct"])},
        {"label": "Returned Orders", "value": number(totals["returned_orders"])},
        {
            "label": "Returned Revenue",
            "value": compact_money(totals["returned_revenue"]),
            "sub": f"{pct(totals['returned_revenue_share_pct'])} of revenue",
        },
        {"label": "Returned Profit", "value": compact_money(totals["returned_profit"])},
    ]
)

st.divider()
st.markdown("#### Return-rate trend")
trend = da.returns_trend(scope)
if not empty_guard(trend):
    charts.show(
        charts.line(
            trend,
            "period_start",
            "return_rate_pct",
            "Monthly return rate (%)",
            labels={"period_start": "", "return_rate_pct": "Return rate %"},
        )
    )

c1, c2 = st.columns(2)
with c1:
    by_region = da.return_rate_by_region(scope)
    if not by_region.empty:
        top = by_region.head(10).copy()
        top["label"] = top["market"] + " / " + top["region"]
        charts.show(
            charts.bar(
                top.sort_values("return_rate_pct"),
                "return_rate_pct",
                "label",
                "Return rate by region (top 10)",
                orientation="h",
                labels={"return_rate_pct": "Return rate %", "label": ""},
            )
        )
with c2:
    by_cat = da.return_rate_by_category(scope)
    if not by_cat.empty:
        charts.show(
            charts.bar(
                by_cat,
                "category",
                "return_rate_pct",
                "Return rate by category",
                labels={"category": "", "return_rate_pct": "Return rate %"},
            )
        )

st.divider()
st.markdown("#### Highest-returning products")
by_prod = da.return_rate_by_product(scope, min_orders=20, n=15)
if by_prod.empty:
    st.caption("No products meet the minimum-volume threshold for a reliable return rate.")
else:
    st.dataframe(
        by_prod.rename(
            columns={
                "product_name": "Product",
                "category": "Category",
                "orders": "Orders",
                "returned_orders": "Returned",
                "return_rate_pct": "Return rate %",
                "returned_revenue": "Returned revenue",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    download_csv(by_prod, "return_rate_by_product.csv", "Export product returns")
