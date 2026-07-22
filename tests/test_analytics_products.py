"""Tests for product analytics."""

from forecastiq.analytics import products


def test_category_performance(warehouse):
    df = products.category_performance(warehouse)
    assert set(df["category"]) == {"Technology", "Furniture", "Office Supplies"}
    assert df["revenue"].is_monotonic_decreasing  # ordered by revenue
    assert {"profit_margin_pct", "units", "orders"}.issubset(df.columns)


def test_product_and_subcategory_grain(warehouse):
    assert len(products.product_performance(warehouse)) == 4  # P1..P4
    assert len(products.top_products(warehouse, 2)) == 2
    assert not products.subcategory_performance(warehouse).empty


def test_low_performers_are_losses(warehouse):
    low = products.low_performing_products(warehouse)
    assert not low.empty
    assert (low["profit"] < 0).all()
    assert "P4" in set(low["product_id"])  # the injected loss-leader
