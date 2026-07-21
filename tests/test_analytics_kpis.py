"""Tests for executive KPIs."""
from forecastiq.analytics import kpis


def test_executive_kpis_totals(warehouse):
    k = kpis.executive_kpis(warehouse)
    assert k["total_orders"] == 96
    assert k["total_customers"] == 3
    assert k["total_units"] == 240
    assert abs(k["total_revenue"] - 11280.0) < 0.01
    assert abs(k["avg_order_value"] - round(11280.0 / 96, 2)) < 0.01
    assert abs(k["avg_selling_price"] - 47.0) < 0.01


def test_margin_reflects_loss_leader(warehouse):
    k = kpis.executive_kpis(warehouse)
    # Overall margin is dragged below the 15% line by the loss-making product.
    assert 0 < k["profit_margin_pct"] < 15
    assert 0 <= k["return_rate_pct"] <= 100
