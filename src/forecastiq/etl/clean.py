"""Stage 2 — Clean: normalize strings, coerce numerics, dedupe, drop broken rows."""
from __future__ import annotations

import pandas as pd
from pandas.api import types as pdt

from ..config import Config

_NUMERIC_COLS = ["sales", "quantity", "discount", "profit", "shipping_cost"]


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def clean(df: pd.DataFrame, cfg: Config, logger=None) -> pd.DataFrame:
    """Return a cleaned copy of ``df`` ready for validation."""
    rules = cfg["etl"]["validation"]
    df = df.copy()
    start_rows = len(df)

    # 1. Trim whitespace on string columns (preserves NaN).
    #    is_string_dtype covers object, pandas StringDtype, and pandas-3 "str" dtype.
    str_cols = [c for c in df.columns if pdt.is_string_dtype(df[c])]
    for col in str_cols:
        df[col] = df[col].map(_strip)

    # 2. Coerce numeric measures; unparseable -> NaN.
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Drop exact duplicate rows.
    if rules.get("drop_exact_duplicates", True):
        before = len(df)
        df = df.drop_duplicates()
        dropped = before - len(df)
        if dropped and logger:
            logger.info("Dropped %d exact duplicate rows", dropped)

    # 4. Drop rows missing any required field (can't key the fact without them).
    required = [c for c in rules.get("required_columns", []) if c in df.columns]
    if required:
        before = len(df)
        df = df.dropna(subset=required)
        dropped = before - len(df)
        if dropped and logger:
            logger.info("Dropped %d rows missing required fields %s", dropped, required)

    # 5. Cast quantity to a nullable integer for a clean fact grain.
    if "quantity" in df.columns:
        df["quantity"] = df["quantity"].round().astype("Int64")

    df = df.reset_index(drop=True)
    if logger:
        logger.info("Cleaned: %d -> %d rows retained", start_rows, len(df))
    return df
