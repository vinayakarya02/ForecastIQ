"""Tests for customer analytics."""

from forecastiq.analytics import segmentation


def test_rfm_scores_present(warehouse):
    df = segmentation.rfm(warehouse)
    assert len(df) == 3
    assert {"r_score", "f_score", "m_score", "rfm_total", "rfm_segment"}.issubset(df.columns)
    assert df["r_score"].between(1, 4).all()


def test_repeat_customers(warehouse):
    r = segmentation.repeat_customers(warehouse)
    assert r["total_customers"] == 3
    assert r["repeat_rate_pct"] == 100.0  # every fixture customer has many orders


def test_clv_ranking(warehouse):
    clv = segmentation.customer_lifetime_value(warehouse)
    assert clv["clv_basic"].is_monotonic_decreasing
    assert clv.iloc[0]["customer_id"] == "C1"  # C1 has the most orders (regular + loss-leader)
    assert len(segmentation.top_customers(warehouse, 2)) == 2


def test_rfm_segment_summary(warehouse):
    summary = segmentation.rfm_segment_summary(warehouse)
    assert {"rfm_segment", "customers", "revenue"}.issubset(summary.columns)
    assert summary["customers"].sum() == 3
