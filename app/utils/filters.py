"""Global sidebar filters -> a FactScope stored in session_state.

Rendered once per run from the app entrypoint so the filters appear on every page.
Pages read the active scope with ``current_scope()`` (defaults to an empty, unfiltered
scope when the app is run page-standalone, e.g. under test).
"""

from __future__ import annotations

import streamlit as st

from .scope import FactScope
from .warehouse import filter_options

_KEYS = [
    "f_years",
    "f_markets",
    "f_regions",
    "f_countries",
    "f_categories",
    "f_subcats",
    "f_segments",
]


def _reset() -> None:
    for k in _KEYS:
        st.session_state.pop(k, None)


def render_sidebar_filters() -> FactScope:
    """Draw the filter controls and return (and store) the resulting FactScope."""
    opts = filter_options()
    sb = st.sidebar
    sb.markdown("### 🔎 Global Filters")

    years = sb.multiselect("Year", opts["years"], key="f_years")
    markets = sb.multiselect("Market", opts["markets"], key="f_markets")
    regions = sb.multiselect("Region", opts["regions"], key="f_regions")
    countries = sb.multiselect("Country", opts["countries"], key="f_countries")
    categories = sb.multiselect("Category", opts["categories"], key="f_categories")
    sub_categories = sb.multiselect("Sub-category", opts["sub_categories"], key="f_subcats")
    segments = sb.multiselect("Segment", opts["segments"], key="f_segments")

    sb.button("Reset filters", on_click=_reset, width="stretch")

    scope = FactScope(
        years=tuple(years),
        markets=tuple(markets),
        regions=tuple(regions),
        countries=tuple(countries),
        categories=tuple(categories),
        sub_categories=tuple(sub_categories),
        segments=tuple(segments),
    )
    st.session_state["scope"] = scope
    sb.caption("Filters apply across every analytics page.")
    return scope


def current_scope() -> FactScope:
    """The active scope (empty if filters haven't been rendered — e.g. under test)."""
    return st.session_state.get("scope", FactScope())
