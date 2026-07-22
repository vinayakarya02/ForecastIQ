"""Sales Analytics — trends, growth, moving averages, and dimensional breakdown."""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from components import charts  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Sales Analytics", "Revenue trends, growth, and drill-downs", "📈")
scope_banner(scope)

monthly = da.monthly_revenue(scope)
if empty_guard(monthly):
    st.stop()

tab_trends, tab_growth, tab_break = st.tabs(["📈 Trends", "📊 Growth", "🧩 Breakdown"])

# ---- Trends ----
with tab_trends:
    grain = st.radio("Grain", ["Monthly", "Quarterly", "Yearly"], horizontal=True, key="sa_grain")
    if grain == "Monthly":
        window = st.slider("Moving-average window (months)", 1, 12, 3)
        rt = da.revenue_trend(scope, window).rename(columns={f"revenue_{window}m_avg": "moving_avg"})
        long = rt.melt("period_start", ["revenue", "moving_avg"], var_name="Series", value_name="value")
        long["Series"] = long["Series"].map({"revenue": "Revenue", "moving_avg": f"{window}-mo average"})
        charts.show(charts.line(long, "period_start", "value", "Monthly revenue with moving average",
                                color="Series", labels={"period_start": "", "value": "Revenue ($)"}))
    elif grain == "Quarterly":
        q = da.quarterly_revenue(scope)
        charts.show(charts.bar(q, "period", "revenue", "Quarterly revenue",
                               labels={"period": "", "revenue": "Revenue ($)"}))
    else:
        y = da.yearly_revenue(scope).copy()
        y["year"] = y["year"].astype(str)
        charts.show(charts.bar(y, "year", "revenue", "Yearly revenue",
                               labels={"year": "", "revenue": "Revenue ($)"}))

# ---- Growth ----
with tab_growth:
    mom = da.mom_growth(scope).dropna(subset=["mom_growth_pct"])
    if not mom.empty:
        charts.show(charts.bar(mom, "period_start", "mom_growth_pct", "Month-over-month growth (%)",
                               labels={"period_start": "", "mom_growth_pct": "MoM %"}))
    yearly = da.yearly_revenue(scope).dropna(subset=["yoy_growth_pct"]).copy()
    if not yearly.empty:
        yearly["year"] = yearly["year"].astype(str)
        charts.show(charts.bar(yearly, "year", "yoy_growth_pct", "Year-over-year growth (%)",
                               labels={"year": "", "yoy_growth_pct": "YoY %"}))
    else:
        st.caption("Year-over-year growth needs at least two years in the current selection.")

# ---- Breakdown (reuses the scoped monthly series per dimension value) ----
with tab_break:
    dim = st.radio("Break revenue down by", ["Category", "Market"], horizontal=True, key="sa_break")
    if dim == "Category":
        values = da.category_performance(scope)["category"].tolist()
        refine = lambda v: replace(scope, categories=(v,))  # noqa: E731
    else:
        values = da.market_performance(scope)["market"].tolist()
        refine = lambda v: replace(scope, markets=(v,))  # noqa: E731

    frames = []
    for v in values:
        m = da.monthly_revenue(refine(v))[["period_start", "revenue"]].copy()
        m[dim] = v
        frames.append(m)
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        charts.show(charts.line(combined, "period_start", "revenue",
                                f"Monthly revenue by {dim.lower()}", color=dim,
                                labels={"period_start": "", "revenue": "Revenue ($)"}))

st.divider()
download_csv(monthly, "monthly_sales.csv", "Export monthly sales")
