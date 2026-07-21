"""Unit tests for the clean stage."""
import pandas as pd

from forecastiq.etl.clean import clean


def test_clean_strips_dedupes_and_coerces(cfg):
    df = pd.DataFrame(
        {
            "order_id": ["O1", "O1", "O2"],
            "order_date": pd.to_datetime(["2014-01-01", "2014-01-01", "2014-01-02"]),
            "customer_id": ["C1 ", "C1 ", "C2"],   # trailing spaces
            "product_id": ["P1", "P1", "P2"],
            "product_name": ["Widget", "Widget", "Gadget"],
            "sales": [100.5, 100.5, 50.0],
            "quantity": [2, 2, 3],
            "profit": ["10.0", "10.0", "xyz"],      # 'xyz' -> NaN (profit not required)
        }
    )
    out = clean(df, cfg)

    assert len(out) == 2                              # exact duplicate removed
    assert set(out["customer_id"]) == {"C1", "C2"}   # whitespace stripped
    assert out.loc[out["order_id"] == "O2", "profit"].isna().all()  # bad numeric -> NaN


def test_clean_drops_rows_missing_required(cfg):
    df = pd.DataFrame(
        {
            "order_id": ["O1", None],                # required -> row dropped
            "order_date": pd.to_datetime(["2014-01-01", "2014-01-02"]),
            "customer_id": ["C1", "C2"],
            "product_id": ["P1", "P2"],
            "sales": [10.0, 20.0],
            "quantity": [1, 2],
        }
    )
    out = clean(df, cfg)
    assert len(out) == 1
    assert out.iloc[0]["order_id"] == "O1"
