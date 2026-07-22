"""Regional Analytics — market → city performance, managers, and a world map."""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from components import charts  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.theme import apply_theme, style_fig  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Regional Analytics", "Performance from market down to city, plus managers", "🌍")
scope_banner(scope)

market = da.market_performance(scope)
if empty_guard(market):
    st.stop()

# ---- World map ----
country = da.country_performance(scope)
st.markdown("#### Revenue by country")
if not country.empty:
    # "country names" locationmode emits a future-deprecation notice; silence it (our
    # country labels are standard and render correctly on the current Plotly version).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        fig = px.choropleth(country, locations="country", locationmode="country names",
                            color="revenue", color_continuous_scale="Blues",
                            hover_name="country", hover_data={"revenue": ":,.0f", "profit": ":,.0f"})
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), geo=dict(showframe=False, showcoastlines=False))
    charts.show(style_fig(fig))

# ---- Market & region ----
c1, c2 = st.columns(2)
with c1:
    charts.show(charts.bar(market, "market", "revenue", "Revenue by market",
                           labels={"market": "", "revenue": "Revenue ($)"}))
with c2:
    charts.show(charts.bar(market, "market", "profit_margin_pct", "Margin by market (%)",
                           labels={"market": "", "profit_margin_pct": "Margin %"}))

region = da.region_performance(scope)
st.markdown("#### Region performance")
charts.show(charts.bar(region.sort_values("revenue"), "revenue", "region",
                       "Revenue by region", orientation="h", color="market",
                       labels={"revenue": "Revenue ($)", "region": ""}))

# ---- Managers ----
st.markdown("#### Region manager performance")
mgr = da.region_manager_performance(scope)
if not mgr.empty:
    charts.show(charts.bar(mgr.sort_values("revenue"), "revenue", "region_manager",
                           "Revenue by region manager", orientation="h",
                           labels={"revenue": "Revenue ($)", "region_manager": ""}))

# ---- Geography tables ----
st.divider()
tab_country, tab_state, tab_city = st.tabs(["Countries", "States", "Cities"])
n = 15
with tab_country:
    st.dataframe(country.head(n).rename(columns={"country": "Country", "revenue": "Revenue",
                 "profit": "Profit", "orders": "Orders", "customers": "Customers",
                 "profit_margin_pct": "Margin %"}), hide_index=True, width="stretch")
    download_csv(country, "country_performance.csv", "Export countries")
with tab_state:
    state = da.state_performance(scope)
    st.dataframe(state.head(n).rename(columns={"country": "Country", "state": "State",
                 "revenue": "Revenue", "profit": "Profit", "profit_margin_pct": "Margin %"}),
                 hide_index=True, width="stretch")
with tab_city:
    city = da.city_performance(scope)
    st.dataframe(city.head(n).rename(columns={"country": "Country", "city": "City",
                 "revenue": "Revenue", "profit": "Profit", "profit_margin_pct": "Margin %"}),
                 hide_index=True, width="stretch")
