"""Tests for forecasting data preparation (series building from the warehouse)."""

from forecastiq.forecasting import data


def test_build_monthly_total(warehouse):
    s = data.build_series(warehouse, "sales", "monthly", "total")
    assert len(s) == 24  # 2013 + 2014
    assert s.index.freqstr == "MS"
    assert (s > 0).all()
    assert s.name == "sales"


def test_build_category_series(warehouse):
    s = data.build_series(warehouse, "sales", "monthly", "category", "Technology")
    assert len(s) == 24
    assert (s > 0).all()


def test_build_quarterly(warehouse):
    s = data.build_series(warehouse, "sales", "quarterly", "total")
    assert len(s) == 8  # 2 years x 4 quarters
    assert s.index.freqstr in ("QS", "QS-JAN", "QS-OCT")


def test_list_keys(warehouse):
    assert set(data.list_keys(warehouse, "category")) == {
        "Technology",
        "Furniture",
        "Office Supplies",
    }
    assert set(data.list_keys(warehouse, "market")) == {"US", "EU"}


def test_series_id():
    assert data.series_id("total", None) == "total"
    assert data.series_id("category", "Technology") == "category:Technology"


def test_invalid_target_raises(warehouse):
    import pytest

    with pytest.raises(ValueError):
        data.build_series(warehouse, "not_a_column", "monthly", "total")
