"""KPI card components (styled HTML for a commercial look)."""

from __future__ import annotations

import streamlit as st


def kpi_card(
    container, label: str, value: str, sub: str | None = None, delta: float | None = None
) -> None:
    """Render a single KPI card into ``container`` (a column)."""
    delta_html = ""
    if delta is not None:
        cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="{cls}">{arrow} {abs(delta):.1f}%</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    container.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>{delta_html}{sub_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict]) -> None:
    """Render a responsive row of KPI cards. Each item: {label, value, sub?, delta?}."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items, strict=True):
        kpi_card(col, **item)
