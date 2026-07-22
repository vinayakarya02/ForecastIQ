"""Shared pytest fixtures for ForecastIQ tests."""

import numpy as np
import pandas as pd
import pytest

from forecastiq.config import Config
from forecastiq.etl.load import load
from forecastiq.etl.transform import transform
from forecastiq.utils.io import get_engine, run_sql_script


@pytest.fixture
def cfg():
    return Config.load()


def _row(seq, year, month, cust, prod, reg, sales, qty, profit):
    """One canonical order-line dict for the rich fixture."""
    return {
        "order_id": f"O-{year}-{seq:04d}",
        "order_date": pd.Timestamp(year, month, 15),
        "ship_date": pd.Timestamp(year, month, 18),
        "ship_mode": "Standard Class",
        "customer_id": cust[0],
        "customer_name": cust[1],
        "segment": cust[2],
        "country": reg[0],
        "market": reg[1],
        "region": reg[2],
        "state": reg[3],
        "city": reg[4],
        "product_id": prod[0],
        "product_name": prod[1],
        "category": prod[2],
        "sub_category": prod[3],
        "sales": sales,
        "quantity": qty,
        "discount": 0.1,
        "profit": profit,
        "shipping_cost": round(sales * 0.05, 2),
        "order_priority": "Medium",
        "region_manager": reg[5],
        "is_returned": 1 if seq % 7 == 0 else 0,
    }


@pytest.fixture
def rich_frame():
    """A deterministic 2-year canonical sales frame for analytics tests.

    Properties baked in for assertions:
      - 96 order lines: 2013 + 2014, 12 months each, 4 lines/month
      - 4 products across 3 categories; P4 is a net loss-maker (negative profit)
      - 3 customers, 3 regions (2 markets: US, EU), 3 region managers
      - 2014 revenue > 2013 (year factor 1.4) -> positive YoY
      - Nov/Dec uplift (season 1.5) -> a detectable seasonal peak
      - ~1 in 7 orders flagged returned
    """
    customers = [
        ("C1", "Alice", "Consumer"),
        ("C2", "Bob", "Corporate"),
        ("C3", "Cara", "Home Office"),
    ]
    prods = [
        ("P1", "Server Rack", "Technology", "Servers"),
        ("P2", "Office Chair", "Furniture", "Chairs"),
        ("P3", "Ballpoint Pen", "Office Supplies", "Pens"),
    ]
    regions = [
        ("United States", "US", "East", "New York", "New York", "Kelly Williams"),
        ("United States", "US", "West", "California", "Los Angeles", "Matt Collister"),
        ("Germany", "EU", "Central", "Berlin", "Berlin", "Anna Andreadi"),
    ]
    rows, seq = [], 0
    for year in (2013, 2014):
        for month in range(1, 13):
            season = 1.5 if month in (11, 12) else 1.0
            yfac = 1.0 if year == 2013 else 1.4
            for i in range(3):
                seq += 1
                sales = round(100 * season * yfac + i * 10, 2)
                rows.append(
                    _row(
                        seq,
                        year,
                        month,
                        customers[i],
                        prods[i],
                        regions[i],
                        sales=sales,
                        qty=2 + i,
                        profit=round(sales * 0.15, 2),
                    )
                )
            # loss-leader: a net negative-profit product (Technology)
            seq += 1
            rows.append(
                _row(
                    seq,
                    year,
                    month,
                    customers[0],
                    ("P4", "Faulty Gadget", "Technology", "Gadgets"),
                    regions[0],
                    sales=50.0,
                    qty=1,
                    profit=-20.0,
                )
            )
    return pd.DataFrame(rows)


@pytest.fixture
def warehouse(rich_frame, cfg, tmp_path):
    """Load the rich fixture into a temp SQLite warehouse and return the engine."""
    tables = transform(rich_frame, cfg)
    engine = get_engine(f"sqlite:///{(tmp_path / 'warehouse.db').as_posix()}")
    load(tables, cfg, engine=engine)
    return engine


@pytest.fixture
def synth_series():
    """A deterministic 48-month series with linear trend + annual seasonality."""
    idx = pd.date_range("2011-01-01", periods=48, freq="MS")
    t = np.arange(48)
    seasonal = 1 + 0.3 * np.sin(2 * np.pi * (idx.month - 1) / 12)
    return pd.Series((1000 + 20 * t) * seasonal, index=idx, name="sales")


@pytest.fixture
def schema_engine(cfg, tmp_path):
    """Temp SQLite DB with the full (empty) schema — for persistence tests."""
    engine = get_engine(f"sqlite:///{(tmp_path / 'fc.db').as_posix()}")
    run_sql_script(engine, cfg.root / "sql" / "schema.sql")
    return engine


@pytest.fixture
def all_model_factories():
    """All five forecasters wired up (period 12)."""
    from forecastiq.forecasting import models

    return models.build_model_factories(
        {
            "naive": {"enabled": True},
            "moving_average": {"enabled": True, "window": 3},
            "linear_regression": {"enabled": True, "lags": [1, 12], "roll_windows": [3]},
            "arima": {"enabled": True, "order": [1, 1, 1]},
            "sarima": {"enabled": True, "order": [1, 1, 1], "seasonal_order": [1, 1, 1, 12]},
        },
        period=12,
    )


@pytest.fixture
def sales_frame():
    """A tiny, well-formed canonical sales frame (4 order lines, 2 months)."""
    return pd.DataFrame(
        {
            "order_id": ["O1", "O1", "O2", "O3"],
            "order_date": pd.to_datetime(["2014-01-05", "2014-01-05", "2014-02-10", "2014-02-15"]),
            "ship_date": pd.to_datetime(["2014-01-08", "2014-01-08", "2014-02-12", "2014-02-18"]),
            "ship_mode": ["Standard", "Standard", "First", "Second"],
            "customer_id": ["C1", "C1", "C2", "C1"],
            "customer_name": ["Alice", "Alice", "Bob", "Alice"],
            "segment": ["Consumer", "Consumer", "Corporate", "Consumer"],
            "city": ["NY", "NY", "LA", "NY"],
            "state": ["NY", "NY", "CA", "NY"],
            "country": ["US", "US", "US", "US"],
            "market": ["US", "US", "US", "US"],
            "region": ["East", "East", "West", "East"],
            "product_id": ["P1", "P2", "P1", "P3"],
            "product_name": ["Widget", "Gadget", "Widget", "Gizmo"],
            "category": ["Technology", "Furniture", "Technology", "Technology"],
            "sub_category": ["Phones", "Chairs", "Phones", "Phones"],
            "sales": [100.0, 50.0, 100.0, 75.0],
            "quantity": pd.array([2, 1, 2, 3], dtype="Int64"),
            "discount": [0.1, 0.0, 0.1, 0.2],
            "profit": [10.0, 5.0, 10.0, -2.0],
            "shipping_cost": [1.0, 2.0, 1.0, 3.0],
            "order_priority": ["High", "High", "Medium", "Low"],
        }
    )
