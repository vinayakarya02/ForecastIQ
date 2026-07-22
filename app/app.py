"""ForecastIQ — interactive analytics platform (Streamlit entrypoint).

Run:  streamlit run app/app.py

Defines the multipage navigation and renders the global sidebar filters once per run so
every analytics page reacts to the same FactScope. All data comes from the existing
warehouse / analytics / forecasting engines via the cached data-access layer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # put app/ on the path

import streamlit as st  # noqa: E402
from utils.filters import render_sidebar_filters  # noqa: E402
from utils.theme import apply_theme  # noqa: E402
from utils.warehouse import warehouse_exists  # noqa: E402

st.set_page_config(
    page_title="ForecastIQ", page_icon="📈", layout="wide", initial_sidebar_state="expanded"
)
apply_theme()

if not warehouse_exists():
    st.title("📈 ForecastIQ")
    st.error(
        "**Warehouse not found.** Build it first:\n\n"
        "```bash\npython pipelines/run_etl.py\npython pipelines/run_forecast.py\n```",
        icon="🗄️",
    )
    st.stop()

PAGES = [
    st.Page("pages/1_Home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/2_Executive_Dashboard.py", title="Executive Dashboard", icon="📊"),
    st.Page("pages/3_Sales_Analytics.py", title="Sales Analytics", icon="📈"),
    st.Page("pages/4_Customer_Analytics.py", title="Customer Analytics", icon="👥"),
    st.Page("pages/5_Product_Analytics.py", title="Product Analytics", icon="📦"),
    st.Page("pages/6_Regional_Analytics.py", title="Regional Analytics", icon="🌍"),
    st.Page("pages/7_Returns_Analytics.py", title="Returns Analytics", icon="↩️"),
    st.Page("pages/8_Forecasting.py", title="Forecasting", icon="🔮"),
    st.Page("pages/9_Business_Insights.py", title="Business Insights", icon="💡"),
    st.Page("pages/10_Model_Performance.py", title="Model Performance", icon="🏁"),
]

nav = st.navigation(PAGES)
render_sidebar_filters()
st.sidebar.divider()
st.sidebar.caption("ForecastIQ · AI-Powered Sales Forecasting & BI")
nav.run()
