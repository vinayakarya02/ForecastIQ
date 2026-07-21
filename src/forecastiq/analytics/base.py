"""Shared helpers for the analytics layer.

Every analytics function takes a SQLAlchemy ``engine`` and returns a pandas
DataFrame (for tabular results) or a plain dict (for scalar KPI bundles). Metric
logic lives in SQL views where possible so definitions stay in one place.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from ..utils.io import query_df


def read(engine: Engine, sql: str) -> pd.DataFrame:
    """Run a read-only query and return a DataFrame (single impl via utils.io)."""
    return query_df(sql, engine)


def safe_div(numerator: float, denominator: float) -> float | None:
    """Divide, returning None when the denominator is zero/None."""
    if not denominator:
        return None
    return numerator / denominator


def pct(numerator: float, denominator: float, digits: int = 2) -> float | None:
    """Percentage ``numerator/denominator * 100`` (None-safe)."""
    value = safe_div(numerator, denominator)
    return round(value * 100.0, digits) if value is not None else None


def growth_pct(current: float, previous: float, digits: int = 2) -> float | None:
    """Period-over-period growth as a percentage (None-safe)."""
    value = safe_div(current - previous, previous)
    return round(value * 100.0, digits) if value is not None else None
