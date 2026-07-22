"""Executive Dashboard — headline KPIs, revenue/profit trends, and a summary."""
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
from utils.format import compact_money, money, number, pct  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Executive Dashboard", "Headline performance across the business", "📊")
scope_banner(scope)

k = da.executive_kpis(scope)
if k["total_revenue"] == 0:
    st.warning("No data for the current filters.")
    st.stop()

mom = da.mom_growth(scope)
latest_mom = None if mom.empty else mom["mom_growth_pct"].dropna().iloc[-1] if mom["mom_growth_pct"].notna().any() else None

kpi_row([
    {"label": "Total Revenue", "value": compact_money(k["total_revenue"]), "delta": latest_mom,
     "sub": "latest MoM" if latest_mom is not None else None},
    {"label": "Total Profit", "value": compact_money(k["total_profit"])},
    {"label": "Profit Margin", "value": pct(k["profit_margin_pct"])},
    {"label": "Return Rate", "value": pct(k["return_rate_pct"])},
])
kpi_row([
    {"label": "Orders", "value": number(k["total_orders"])},
    {"label": "Customers", "value": number(k["total_customers"])},
    {"label": "Avg Order Value", "value": money(k["avg_order_value"], 2)},
    {"label": "Avg Selling Price", "value": money(k["avg_selling_price"], 2)},
])

st.divider()

monthly = da.monthly_revenue(scope)
if not empty_guard(monthly):
    c1, c2 = st.columns(2)
    with c1:
        charts.show(charts.line(monthly, "period_start", "revenue", "Monthly Revenue",
                                labels={"period_start": "", "revenue": "Revenue ($)"}))
    with c2:
        charts.show(charts.line(monthly, "period_start", "profit", "Monthly Profit",
                                labels={"period_start": "", "profit": "Profit ($)"}))

cat = da.category_performance(scope)
yearly = da.yearly_revenue(scope)
c1, c2 = st.columns([1, 1.1])
with c1:
    if not cat.empty:
        charts.show(charts.donut(cat, "category", "revenue", "Revenue by Category"))
with c2:
    st.markdown("#### Executive summary")
    lines = [
        f"- **Revenue** of **{money(k['total_revenue'])}** at a **{pct(k['profit_margin_pct'])}** margin "
        f"across **{number(k['total_orders'])}** orders.",
        f"- **{number(k['total_customers'])}** customers, average order value **{money(k['avg_order_value'], 2)}**.",
    ]
    if not yearly.empty and yearly["yoy_growth_pct"].notna().any():
        last = yearly.iloc[-1]
        lines.append(f"- **{int(last['year'])}** revenue grew **{last['yoy_growth_pct']:.1f}%** year over year.")
    if not cat.empty:
        top = cat.iloc[0]
        lines.append(f"- **{top['category']}** leads with **{money(top['revenue'])}** "
                     f"({pct(top['profit_margin_pct'])} margin).")
    lines.append(f"- **{pct(k['return_rate_pct'])}** of orders are returned.")
    st.markdown("\n".join(lines))

st.divider()
download_csv(monthly, "monthly_revenue.csv", "Export monthly revenue")
