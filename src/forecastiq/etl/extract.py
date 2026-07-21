"""Stage 1 — Extract: read the source (Excel workbook or CSV) into one canonical frame.

For the Global Superstore workbook this reads three sheets:
    Orders  -> primary fact dataset (renamed to canonical columns)
    People  -> region -> manager map, added as ``region_manager``
    Returns -> (order_id, market) that were returned, added as ``is_returned`` flag
"""
from __future__ import annotations

import pandas as pd

from ..config import Config
from ..utils.io import read_csv_robust


def _canonicalize_orders(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Rename to canonical columns, parse dates, keep only mapped columns."""
    etl = cfg["etl"]
    rename = {src: dst for src, dst in etl["column_map"].items() if src in df.columns}
    df = df.rename(columns=rename)
    for col in etl.get("date_columns", []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=etl.get("dayfirst", False), errors="coerce")
    canonical = [v for v in etl["column_map"].values() if v in df.columns]
    return df[canonical].copy()


def _add_region_manager(orders: pd.DataFrame, people: pd.DataFrame,
                        aliases: dict | None = None, logger=None) -> pd.DataFrame:
    """Attach ``region_manager`` by mapping each order's region -> People.Person.

    ``aliases`` reconciles differing region labels between the Orders and People
    sheets (e.g. Orders 'EMEA' -> People 'AMEA') before the lookup.
    """
    aliases = aliases or {}
    cols = {c.lower(): c for c in people.columns}
    region_col, person_col = cols.get("region"), cols.get("person")
    if not region_col or not person_col or "region" not in orders.columns:
        orders["region_manager"] = "Unknown"
        return orders
    mapping = dict(
        zip(people[region_col].astype(str).str.strip(), people[person_col].astype(str).str.strip())
    )
    resolved = orders["region"].astype(str).str.strip().replace(aliases)
    orders["region_manager"] = resolved.map(mapping).fillna("Unknown")
    if logger:
        unmapped = int((orders["region_manager"] == "Unknown").sum())
        logger.info("People: %d regions mapped to managers (%d order lines unmapped)",
                    len(mapping), unmapped)
    return orders


def _add_return_flag(orders: pd.DataFrame, returns: pd.DataFrame,
                     market_aliases: dict | None = None, logger=None) -> pd.DataFrame:
    """Attach ``is_returned`` (0/1) by matching (order_id, market) against Returns.

    ``market_aliases`` reconciles market labels between the Returns and Orders sheets
    (e.g. Returns 'United States' -> Orders 'US'). The market key matters: 37 order IDs
    span two markets, so an order_id-only join would mis-flag them.
    """
    market_aliases = market_aliases or {}
    ren = {}
    for c in returns.columns:
        lc = c.lower()
        if lc == "order id":
            ren[c] = "order_id"
        elif lc == "market":
            ren[c] = "market"
    returns = returns.rename(columns=ren)
    if "order_id" not in returns.columns:
        orders["is_returned"] = 0
        return orders

    keys = ["order_id", "market"] if "market" in returns.columns and "market" in orders.columns else ["order_id"]
    ret = returns[keys].copy()
    for k in keys:
        ret[k] = ret[k].astype(str).str.strip()
    if "market" in keys and market_aliases:
        ret["market"] = ret["market"].replace(market_aliases)
    ret = ret.drop_duplicates()
    ret["is_returned"] = 1

    left = orders.copy()
    for k in keys:
        left[k] = left[k].astype(str).str.strip()
    merged = left.merge(ret, on=keys, how="left")
    orders["is_returned"] = merged["is_returned"].fillna(0).astype(int).to_numpy()
    if logger:
        logger.info("Returns: %d return records; flagged %d order lines as returned",
                    len(ret), int(orders["is_returned"].sum()))
    return orders


def extract(cfg: Config, logger=None) -> pd.DataFrame:
    """Load the raw source into a canonical-schema DataFrame."""
    src = cfg.get("source", {}) or {}
    stype = src.get("type", "csv")

    if stype == "excel":
        path = cfg.path("source", "path")
        if logger:
            logger.info("Reading Excel workbook: %s", path.name)
        book = pd.read_excel(path, sheet_name=None)  # dict of all sheets
        orders_raw = book[src.get("orders_sheet", "Orders")]
        df = _canonicalize_orders(orders_raw, cfg)
        if logger:
            logger.info("Extracted %d order rows x %d canonical cols", len(df), df.shape[1])

        people = book.get(src.get("people_sheet", "People"))
        aliases = src.get("region_aliases", {}) or {}
        df = (_add_region_manager(df, people, aliases, logger)
              if people is not None else df.assign(region_manager="Unknown"))

        returns = book.get(src.get("returns_sheet", "Returns"))
        market_aliases = src.get("market_aliases", {}) or {}
        df = (_add_return_flag(df, returns, market_aliases, logger)
              if returns is not None else df.assign(is_returned=0))
        return df

    # ---- CSV fallback ----
    df = read_csv_robust(cfg.raw_csv)
    if logger:
        logger.info("Extracted %d rows x %d cols from %s", len(df), df.shape[1], cfg.raw_csv.name)
    df = _canonicalize_orders(df, cfg)
    df["region_manager"] = "Unknown"
    df["is_returned"] = 0
    return df
