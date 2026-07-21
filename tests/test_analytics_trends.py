"""Tests for sales trend analytics."""
from forecastiq.analytics import trends


def test_yearly_yoy_growth(warehouse):
    y = trends.yearly_revenue(warehouse)
    assert list(y["year"]) == [2013, 2014]
    assert y.iloc[1]["revenue"] > y.iloc[0]["revenue"]     # 2014 grows
    assert y.iloc[1]["yoy_growth_pct"] > 0


def test_monthly_and_quarterly_grain(warehouse):
    assert len(trends.monthly_revenue(warehouse)) == 24     # 2 years x 12 months
    assert len(trends.quarterly_revenue(warehouse)) == 8    # 2 years x 4 quarters


def test_rolling_trend_columns(warehouse):
    rev = trends.revenue_trend(warehouse, window=3)
    assert "revenue_3m_avg" in rev.columns
    assert len(rev) == 24
    prof = trends.profit_trend(warehouse, window=3)
    assert "profit_3m_avg" in prof.columns


def test_mom_growth(warehouse):
    df = trends.mom_growth(warehouse)
    assert {"period_start", "mom_growth_pct"}.issubset(df.columns)
    assert df["mom_growth_pct"].iloc[0] is None or df["mom_growth_pct"].isna().iloc[0]
