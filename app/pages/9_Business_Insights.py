"""Business Insights — the rule-based insight engine, presented as cards."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from components.layout import empty_guard, page_header, scope_banner  # noqa: E402
from utils import data_access as da  # noqa: E402
from utils.export import download_csv  # noqa: E402
from utils.filters import current_scope  # noqa: E402
from utils.theme import apply_theme  # noqa: E402

apply_theme()
scope = current_scope()
page_header(
    "Business Insights",
    "Rule-based observations computed from the warehouse — no hardcoded numbers",
    "💡",
)
scope_banner(scope)

_ACCENT = {
    "growth": "#16a34a",
    "risk": "#dc2626",
    "regional": "#2563eb",
    "seasonality": "#f59e0b",
    "opportunity": "#7c3aed",
    "returns": "#db2777",
}

df = da.business_insights(scope)
if empty_guard(df, "No insights for the current filters."):
    st.stop()

st.caption(f"{len(df)} insights generated from the current selection.")

for _, row in df.iterrows():
    accent = _ACCENT.get(row["category"], "#2563eb")
    metric = ""
    if row["metric"] is not None:
        try:
            metric = (
                f'<span style="color:#94a3b8;font-size:.8rem"> · {float(row["metric"]):,.1f}</span>'
            )
        except (TypeError, ValueError):
            metric = ""
    st.markdown(
        f'<div class="insight-card" style="--acc:{accent}">'
        f'<span class="insight-tag" style="background:{accent}">{row["category"]}</span>'
        f'<div class="insight-title">{row["title"]}{metric}</div>'
        f'<div class="insight-detail">{row["detail"]}</div></div>',
        unsafe_allow_html=True,
    )

st.divider()
download_csv(df, "business_insights.csv", "Export insights")
