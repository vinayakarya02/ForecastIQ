"""Display formatting helpers (currency, percentages, compact numbers)."""

from __future__ import annotations


def money(value: float | None, decimals: int = 0) -> str:
    if value is None:
        return "-"
    return f"${value:,.{decimals}f}"


def compact_money(value: float | None) -> str:
    """$1.2M / $45.0K style for KPI cards."""
    if value is None:
        return "-"
    v = float(value)
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= threshold:
            return f"${v / threshold:,.2f}{suffix}"
    return f"${v:,.0f}"


def compact_number(value: float | None) -> str:
    if value is None:
        return "-"
    v = float(value)
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= threshold:
            return f"{v / threshold:,.1f}{suffix}"
    return f"{v:,.0f}"


def pct(value: float | None, decimals: int = 1) -> str:
    return "-" if value is None else f"{value:.{decimals}f}%"


def number(value: float | None) -> str:
    return "-" if value is None else f"{value:,.0f}"
