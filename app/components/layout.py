"""Page layout helpers: headers, section titles, and the active-filter banner."""

from __future__ import annotations

import streamlit as st
from utils.scope import FactScope


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    st.markdown(f"## {icon} {title}".strip())
    if subtitle:
        st.caption(subtitle)


def section(title: str) -> None:
    st.markdown(f"#### {title}")


def scope_banner(scope: FactScope) -> None:
    """Show the active global filters (or an 'all data' note)."""
    if scope.is_empty():
        st.caption("🔎 Showing **all data** — use the sidebar filters to drill down.")
    else:
        st.info(f"🔎 Filtered — {scope.summary()}", icon="🔎")


def empty_guard(df, message: str = "No data for the current filters.") -> bool:
    """Return True (and show a message) when a result is empty, so pages can bail early."""
    if (
        df is None
        or (hasattr(df, "empty") and df.empty)
        or (hasattr(df, "__len__") and len(df) == 0)
    ):
        st.warning(message)
        return True
    return False
