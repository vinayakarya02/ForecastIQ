"""Unit tests for the Excel enrichment helpers (People + Returns)."""
import pandas as pd

from forecastiq.etl.extract import _add_region_manager, _add_return_flag


def test_region_manager_resolves_alias():
    orders = pd.DataFrame({"region": ["EMEA", "East", "Atlantis"]})
    people = pd.DataFrame(
        {"Person": ["Larry Hughes", "Kelly Williams"], "Region": ["AMEA", "East"]}
    )
    out = _add_region_manager(orders.copy(), people, aliases={"EMEA": "AMEA"})
    assert out.loc[0, "region_manager"] == "Larry Hughes"    # EMEA -> AMEA -> manager
    assert out.loc[1, "region_manager"] == "Kelly Williams"
    assert out.loc[2, "region_manager"] == "Unknown"         # region not in People


def test_return_flag_by_order_and_market():
    orders = pd.DataFrame({"order_id": ["O1", "O2", "O3"], "market": ["EU", "EU", "US"]})
    returns = pd.DataFrame(
        {"Returned": ["Yes", "Yes"], "Order ID": ["O1", "O3"], "Market": ["EU", "US"]}
    )
    out = _add_return_flag(orders.copy(), returns)
    assert out["is_returned"].tolist() == [1, 0, 1]


def test_return_flag_is_market_specific():
    # Same order_id in a different market must not be cross-flagged.
    orders = pd.DataFrame({"order_id": ["O1", "O1"], "market": ["EU", "US"]})
    returns = pd.DataFrame({"Returned": ["Yes"], "Order ID": ["O1"], "Market": ["EU"]})
    out = _add_return_flag(orders.copy(), returns)
    assert out["is_returned"].tolist() == [1, 0]
