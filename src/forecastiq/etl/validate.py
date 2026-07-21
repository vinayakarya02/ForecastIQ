"""Stage 3 — Validate: run data-quality gates and produce a PASS/WARN/FAIL report.

Returns ``(report_df, ok)`` where ``ok`` is False if any check FAILs. The caller
(run_etl) prints the report and aborts before loading when ``ok`` is False.
"""
from __future__ import annotations

import pandas as pd

from ..config import Config


def validate(df: pd.DataFrame, cfg: Config, logger=None) -> tuple[pd.DataFrame, bool]:
    rules = cfg["etl"]["validation"]
    checks: list[dict] = []

    def add(name: str, status: str, detail: str = "", rows: int = 0):
        checks.append({"check_name": name, "status": status, "detail": detail, "rows_flagged": rows})

    # 1. Required columns present.
    missing = [c for c in rules.get("required_columns", []) if c not in df.columns]
    if missing:
        add("required_columns_present", "FAIL", f"missing: {missing}", len(missing))
    else:
        add("required_columns_present", "PASS", "all present")

    # 2. Required columns non-null.
    present_required = [c for c in rules.get("required_columns", []) if c in df.columns]
    null_required = {c: int(df[c].isna().sum()) for c in present_required if df[c].isna().any()}
    if null_required:
        add("required_non_null", "FAIL", str(null_required), sum(null_required.values()))
    elif present_required:
        add("required_non_null", "PASS", "no nulls in required columns")

    # 3. Non-negative measures.
    for col in rules.get("non_negative_columns", []):
        if col in df.columns:
            bad = int((df[col] < 0).sum())
            if bad:
                add(f"non_negative[{col}]", "FAIL", f"{bad} negative values", bad)
            else:
                add(f"non_negative[{col}]", "PASS", "no negatives")

    # 4. Discount within range (WARN).
    dr = rules.get("discount_range")
    if dr and "discount" in df.columns:
        lo, hi = dr
        bad = int(((df["discount"] < lo) | (df["discount"] > hi)).sum())
        add("discount_in_range", "WARN" if bad else "PASS",
            f"{bad} outside [{lo}, {hi}]" if bad else f"within [{lo}, {hi}]", bad)

    # 5. Per-column null fraction (WARN).
    max_null = rules.get("max_null_fraction", 1.0)
    offenders = {c: round(float(df[c].isna().mean()), 3) for c in df.columns
                 if df[c].isna().mean() > max_null}
    add("null_fraction", "WARN" if offenders else "PASS",
        str(offenders) if offenders else f"all columns <= {max_null}", len(offenders))

    # 6. ship_date >= order_date (WARN).
    if {"order_date", "ship_date"}.issubset(df.columns):
        mask = df["ship_date"].notna() & df["order_date"].notna() & (df["ship_date"] < df["order_date"])
        bad = int(mask.sum())
        add("ship_after_order", "WARN" if bad else "PASS",
            f"{bad} ship_date < order_date" if bad else "ok", bad)

    # 7. Duplicate order line (WARN).
    if {"order_id", "product_id"}.issubset(df.columns):
        bad = int(df.duplicated(["order_id", "product_id"]).sum())
        add("unique_order_line", "WARN" if bad else "PASS",
            f"{bad} duplicate order_id+product_id" if bad else "unique", bad)

    report = pd.DataFrame(checks, columns=["check_name", "status", "detail", "rows_flagged"])
    ok = not (report["status"] == "FAIL").any()

    if logger:
        n_fail = int((report["status"] == "FAIL").sum())
        n_warn = int((report["status"] == "WARN").sum())
        logger.info("Validation: %d checks, %d WARN, %d FAIL", len(report), n_warn, n_fail)
    return report, ok
