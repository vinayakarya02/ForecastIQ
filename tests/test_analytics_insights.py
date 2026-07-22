"""Tests for the rule-based insights engine."""

from forecastiq.analytics import insights


def test_generate_insights_categories(warehouse):
    generated = insights.generate_insights(warehouse)
    assert len(generated) >= 4
    cats = {i.category for i in generated}
    assert "growth" in cats  # fastest-growing category
    assert "seasonality" in cats  # Nov/Dec uplift
    assert "risk" in cats  # loss-making products
    assert "regional" in cats  # best/weakest region


def test_seasonal_peak_detected(warehouse):
    generated = insights.generate_insights(warehouse)
    seasonal = next(i for i in generated if i.category == "seasonality")
    assert ("November" in seasonal.detail) or ("December" in seasonal.detail)


def test_insights_frame_shape(warehouse):
    generated = insights.generate_insights(warehouse)
    df = insights.insights_to_frame(generated)
    assert list(df.columns) == ["category", "title", "detail", "metric"]
    assert len(df) == len(generated)
