"""Unit tests for the validate stage."""

import pandas as pd

from forecastiq.etl.validate import validate


def _status(report, name):
    return report.loc[report["check_name"] == name, "status"].iloc[0]


def test_valid_frame_passes(cfg, sales_frame):
    report, ok = validate(sales_frame, cfg)
    assert ok is True
    assert not (report["status"] == "FAIL").any()
    assert _status(report, "required_columns_present") == "PASS"


def test_negative_sales_fails(cfg, sales_frame):
    bad = sales_frame.copy()
    bad.loc[0, "sales"] = -10.0
    report, ok = validate(bad, cfg)
    assert ok is False
    assert _status(report, "non_negative[sales]") == "FAIL"


def test_out_of_range_discount_warns(cfg, sales_frame):
    bad = sales_frame.copy()
    bad.loc[0, "discount"] = 1.5  # outside [0, 1]
    report, ok = validate(bad, cfg)
    assert ok is True  # WARN does not block the load
    assert _status(report, "discount_in_range") == "WARN"


def test_ship_before_order_warns(cfg, sales_frame):
    bad = sales_frame.copy()
    bad.loc[0, "ship_date"] = pd.Timestamp("2013-12-01")  # before order_date
    report, ok = validate(bad, cfg)
    assert _status(report, "ship_after_order") == "WARN"
