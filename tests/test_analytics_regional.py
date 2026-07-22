"""Tests for regional analytics."""

from forecastiq.analytics import regional


def test_market_and_region_grain(warehouse):
    assert set(regional.market_performance(warehouse)["market"]) == {"US", "EU"}
    assert len(regional.region_performance(warehouse)) == 3


def test_region_manager_performance(warehouse):
    mgr = regional.region_manager_performance(warehouse)
    assert set(mgr["region_manager"]) == {"Kelly Williams", "Matt Collister", "Anna Andreadi"}
    assert (mgr["revenue"] > 0).all()


def test_geography_levels(warehouse):
    assert len(regional.country_performance(warehouse)) == 2  # United States, Germany
    assert not regional.state_performance(warehouse).empty
    assert not regional.city_performance(warehouse).empty
