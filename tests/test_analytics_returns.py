"""Tests for returns analytics."""

from forecastiq.analytics import returns


def test_returned_totals(warehouse):
    t = returns.returned_totals(warehouse)
    assert t["returned_orders"] == 13  # seq % 7 == 0 across 96 orders
    assert 0 < t["return_rate_pct"] < 100
    assert t["returned_revenue"] > 0


def test_return_rate_by_category(warehouse):
    df = returns.return_rate_by_category(warehouse)
    assert len(df) == 3
    assert (df["return_rate_pct"] >= 0).all()
    assert (df["return_rate_pct"] <= 100).all()


def test_return_rate_by_region_and_product(warehouse):
    by_region = returns.return_rate_by_region(warehouse)
    assert {"market", "region", "return_rate_pct"}.issubset(by_region.columns)
    by_product = returns.return_rate_by_product(warehouse, min_orders=1)
    assert "return_rate_pct" in by_product.columns
