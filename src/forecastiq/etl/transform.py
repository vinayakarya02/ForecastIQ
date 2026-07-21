"""Stage 4 — Transform: build conformed dimensions and the sales fact table.

Produces a dict of DataFrames whose columns match ``sql/schema.sql`` exactly, so
``load`` can append them straight into the star schema.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config


def _series_or_blank(df: pd.DataFrame, name: str) -> pd.Series:
    """Return column ``name`` or an all-empty-string series if it's absent."""
    if name in df.columns:
        return df[name]
    return pd.Series([""] * len(df), index=df.index, dtype="object")


def _fill_keys(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Fill NaN in string key columns with '' so joins are deterministic."""
    out = frame.copy()
    for c in cols:
        if out[c].dtype == object or str(out[c].dtype) == "string":
            out[c] = out[c].fillna("")
    return out


def _date_key(dt: pd.Series) -> pd.Series:
    """yyyymmdd integer key from a datetime series (NaT -> <NA>)."""
    key = dt.dt.year * 10000 + dt.dt.month * 100 + dt.dt.day
    return key.astype("Int64")


def _build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    date_cols = [c for c in ("order_date", "ship_date") if c in df.columns]
    all_dates = pd.concat([df[c] for c in date_cols], ignore_index=True).dropna()
    unique = pd.to_datetime(pd.Series(all_dates.unique())).sort_values()

    dim = pd.DataFrame({"full_date_ts": unique})
    dim["date_key"] = _date_key(dim["full_date_ts"]).astype("int64")
    dim["full_date"] = dim["full_date_ts"].dt.strftime("%Y-%m-%d")
    dim["day"] = dim["full_date_ts"].dt.day
    dim["month"] = dim["full_date_ts"].dt.month
    dim["month_name"] = dim["full_date_ts"].dt.strftime("%B")
    dim["quarter"] = dim["full_date_ts"].dt.quarter
    dim["year"] = dim["full_date_ts"].dt.year
    dim["week_of_year"] = dim["full_date_ts"].dt.isocalendar().week.astype(int)
    dim["day_of_week"] = dim["full_date_ts"].dt.dayofweek
    dim["is_weekend"] = (dim["day_of_week"] >= 5).astype(int)
    return dim.drop(columns=["full_date_ts"]).reset_index(drop=True)


def _build_dim(df: pd.DataFrame, key_cols: list[str], attr_cols: list[str],
               key_name: str) -> pd.DataFrame:
    cols = key_cols + attr_cols
    frame = pd.DataFrame({c: _series_or_blank(df, c) for c in cols})
    frame = _fill_keys(frame, cols)
    dim = frame.drop_duplicates(subset=key_cols).reset_index(drop=True)
    dim.insert(0, key_name, np.arange(1, len(dim) + 1))
    return dim


def _attach_key(df: pd.DataFrame, dim: pd.DataFrame, key_cols: list[str], key_name: str) -> pd.Series:
    left = pd.DataFrame({c: _series_or_blank(df, c) for c in key_cols})
    left = _fill_keys(left, key_cols)
    merged = left.merge(dim[key_cols + [key_name]], on=key_cols, how="left")
    return merged[key_name].to_numpy()


def transform(df: pd.DataFrame, cfg: Config, logger=None) -> dict[str, pd.DataFrame]:
    """Build ``dim_*`` tables and ``fact_sales`` from the cleaned frame."""
    # --- Dimensions ---
    dim_date = _build_dim_date(df)
    dim_customer = _build_dim(df, ["customer_id"], ["customer_name", "segment"], "customer_key")
    dim_product = _build_dim(df, ["product_id", "product_name"], ["category", "sub_category"],
                             "product_key")
    dim_region = _build_dim(df, ["country", "market", "region", "state", "city"],
                            ["region_manager"], "region_key")

    # Reorder dimension columns to match schema.sql.
    dim_customer = dim_customer[["customer_key", "customer_id", "customer_name", "segment"]]
    dim_product = dim_product[["product_key", "product_id", "category", "sub_category", "product_name"]]
    dim_region = dim_region[["region_key", "country", "market", "region", "state", "city",
                             "region_manager"]]

    # --- Fact ---
    fact = pd.DataFrame()
    fact["sales_key"] = np.arange(1, len(df) + 1)
    fact["order_id"] = _series_or_blank(df, "order_id")
    fact["order_date_key"] = _date_key(df["order_date"])
    fact["ship_date_key"] = _date_key(df["ship_date"]) if "ship_date" in df.columns else pd.NA
    fact["customer_key"] = _attach_key(df, dim_customer, ["customer_id"], "customer_key")
    fact["product_key"] = _attach_key(df, dim_product, ["product_id", "product_name"], "product_key")
    fact["region_key"] = _attach_key(
        df, dim_region, ["country", "market", "region", "state", "city"], "region_key")
    fact["ship_mode"] = _series_or_blank(df, "ship_mode")
    fact["order_priority"] = _series_or_blank(df, "order_priority")
    fact["sales"] = pd.to_numeric(df.get("sales"), errors="coerce")
    fact["quantity"] = pd.to_numeric(df.get("quantity"), errors="coerce").astype("Int64")
    fact["discount"] = pd.to_numeric(df.get("discount"), errors="coerce") if "discount" in df else pd.NA
    fact["profit"] = pd.to_numeric(df.get("profit"), errors="coerce") if "profit" in df else pd.NA
    fact["shipping_cost"] = (pd.to_numeric(df.get("shipping_cost"), errors="coerce")
                             if "shipping_cost" in df else pd.NA)
    fact["is_returned"] = (pd.to_numeric(df.get("is_returned"), errors="coerce").fillna(0).astype(int)
                           if "is_returned" in df.columns else 0)

    tables = {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_region": dim_region,
        "fact_sales": fact,
    }
    if logger:
        logger.info(
            "Transformed -> dim_date=%d, dim_customer=%d, dim_product=%d, dim_region=%d, fact_sales=%d",
            *(len(tables[t]) for t in ["dim_date", "dim_customer", "dim_product", "dim_region", "fact_sales"]),
        )
    return tables
