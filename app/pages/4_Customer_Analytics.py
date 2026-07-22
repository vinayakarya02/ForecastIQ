"""Customer Analytics — RFM segments, CLV, repeat behaviour, top customers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from components import charts  # noqa: E402
from components.kpi import kpi_row  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.format import money, number, pct  # noqa: E402
from utils.theme import apply_theme, style_fig  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Customer Analytics", "Segmentation, lifetime value, and loyalty", "👥")
scope_banner(scope)

repeat = da.repeat_customers(scope)
if repeat["total_customers"] == 0:
    st.warning("No data for the current filters.")
    st.stop()

kpi_row([
    {"label": "Customers", "value": number(repeat["total_customers"])},
    {"label": "Repeat Customers", "value": number(repeat["repeat_customers"])},
    {"label": "Repeat Rate", "value": pct(repeat["repeat_rate_pct"])},
    {"label": "Avg Orders / Customer", "value": f"{repeat['avg_orders_per_customer']:.1f}"},
])

st.divider()
st.markdown("#### RFM segmentation")
rfm = da.rfm_segments(scope)
if not empty_guard(rfm):
    c1, c2 = st.columns(2)
    with c1:
        charts.show(charts.bar(rfm, "rfm_segment", "customers", "Customers per segment",
                               color="rfm_segment", labels={"rfm_segment": "", "customers": "Customers"}))
    with c2:
        charts.show(charts.donut(rfm, "rfm_segment", "revenue", "Revenue per segment"))
    st.dataframe(
        rfm.rename(columns={"rfm_segment": "Segment", "customers": "Customers",
                            "revenue": "Revenue", "avg_monetary": "Avg spend"}),
        hide_index=True, width="stretch")

st.divider()
st.markdown("#### Customer lifetime value")
clv = da.customer_lifetime_value(scope)
if not empty_guard(clv):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = px.histogram(clv, x="clv_basic", nbins=40, title="Distribution of customer value (CLV)")
        fig.update_layout(xaxis_title="Historical revenue per customer ($)", yaxis_title="Customers")
        charts.show(style_fig(fig))
    with c2:
        st.metric("Median CLV", money(clv["clv_basic"].median(), 0))
        st.metric("Mean CLV", money(clv["clv_basic"].mean(), 0))
        st.caption("CLV (basic) = total historical revenue per customer.")

st.divider()
st.markdown("#### Top customers")
n = st.slider("How many", 5, 30, 15, key="cust_topn")
top = da.top_customers(scope, n)
if not empty_guard(top):
    charts.show(charts.bar(top.sort_values("clv_basic"), "clv_basic", "customer_name",
                           "Top customers by lifetime value", orientation="h",
                           labels={"clv_basic": "Revenue ($)", "customer_name": ""}))
    st.dataframe(
        top.rename(columns={"customer_name": "Customer", "segment": "Segment", "orders": "Orders",
                            "clv_basic": "CLV", "avg_order_value": "AOV", "profit": "Profit"}),
        hide_index=True, width="stretch")
    download_csv(top, "top_customers.csv", "Export top customers")
