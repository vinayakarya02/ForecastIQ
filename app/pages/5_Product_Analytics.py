"""Product Analytics — category, sub-category, product performance, and loss-makers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from components import charts  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
scope = current_scope()
page_header("Product Analytics", "Category, product performance, and loss-makers", "📦")
scope_banner(scope)

cat = da.category_performance(scope)
if empty_guard(cat):
    st.stop()

st.markdown("#### Category performance")
c1, c2 = st.columns(2)
with c1:
    charts.show(
        charts.bar(
            cat,
            "category",
            "revenue",
            "Revenue by category",
            labels={"category": "", "revenue": "Revenue ($)"},
        )
    )
with c2:
    charts.show(
        charts.bar(
            cat,
            "category",
            "profit_margin_pct",
            "Profit margin by category (%)",
            labels={"category": "", "profit_margin_pct": "Margin %"},
        )
    )
st.dataframe(
    cat.rename(
        columns={
            "category": "Category",
            "revenue": "Revenue",
            "profit": "Profit",
            "units": "Units",
            "orders": "Orders",
            "profit_margin_pct": "Margin %",
        }
    ),
    hide_index=True,
    width="stretch",
)

st.divider()
st.markdown("#### Sub-category performance")
sub = da.subcategory_performance(scope)
if not sub.empty:
    focus = st.selectbox("Filter by category", ["All"] + cat["category"].tolist(), key="prod_cat")
    view = sub if focus == "All" else sub[sub["category"] == focus]
    charts.show(
        charts.bar(
            view.sort_values("revenue"),
            "revenue",
            "sub_category",
            "Revenue by sub-category",
            orientation="h",
            color="category",
            labels={"revenue": "Revenue ($)", "sub_category": ""},
        )
    )

st.divider()
tab_top, tab_low = st.tabs(["🏆 Top products", "⚠️ Loss-making products"])
with tab_top:
    n = st.slider("How many", 5, 30, 15, key="prod_topn")
    top = da.top_products(scope, n)
    if not empty_guard(top):
        st.dataframe(
            top.rename(
                columns={
                    "product_name": "Product",
                    "category": "Category",
                    "revenue": "Revenue",
                    "profit": "Profit",
                    "units": "Units",
                    "profit_margin_pct": "Margin %",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        download_csv(top, "top_products.csv", "Export top products")
with tab_low:
    low = da.low_performing_products(scope, 15)
    if low.empty:
        st.success("No loss-making products in the current selection. 🎉")
    else:
        st.caption(f"{len(low)} products with negative total profit shown (worst first).")
        st.dataframe(
            low.rename(
                columns={
                    "product_name": "Product",
                    "category": "Category",
                    "revenue": "Revenue",
                    "profit": "Profit",
                    "units": "Units",
                    "profit_margin_pct": "Margin %",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        download_csv(low, "loss_making_products.csv", "Export loss-makers")
