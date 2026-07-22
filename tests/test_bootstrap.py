"""Tests for the sample-data generator and the self-provisioning bootstrap."""

import sqlite3

import pandas as pd

from forecastiq import bootstrap
from forecastiq.config import Config
from forecastiq.sample import write_sample_workbook


def test_sample_workbook_structure(tmp_path):
    path = write_sample_workbook(tmp_path / "sample.xlsx")
    book = pd.read_excel(path, sheet_name=None)
    assert set(book) == {"Orders", "People", "Returns"}

    orders = book["Orders"]
    assert len(orders) > 500
    for col in ["Order ID", "Order Date", "Market", "Region", "Category", "Sales", "Quantity"]:
        assert col in orders.columns
    assert set(book["People"].columns) == {"Person", "Region"}
    assert "Returned" in book["Returns"].columns


def test_ensure_warehouse_builds_from_sample(tmp_path, monkeypatch):
    db = tmp_path / "w.db"
    monkeypatch.setenv("FORECASTIQ_DB_URL", f"sqlite:///{db.as_posix()}")
    monkeypatch.setenv("FORECASTIQ_SOURCE_PATH", str(tmp_path / "absent.xls"))

    mode = bootstrap.ensure_warehouse(
        Config.load(), with_forecast=False, sample_path=tmp_path / "sample.xlsx"
    )
    assert mode == "sample"

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0] > 500
        assert conn.execute("SELECT COUNT(*) FROM vw_monthly_sales").fetchone()[0] >= 24
    finally:
        conn.close()


def test_ensure_warehouse_existing_short_circuits(tmp_path, monkeypatch):
    db = tmp_path / "w.db"
    db.write_bytes(b"")  # pretend a warehouse already exists
    monkeypatch.setenv("FORECASTIQ_DB_URL", f"sqlite:///{db.as_posix()}")
    assert bootstrap.ensure_warehouse(Config.load()) == "existing"


def test_ensure_warehouse_refreshes_sample_to_real(tmp_path, monkeypatch):
    db = tmp_path / "w.db"
    monkeypatch.setenv("FORECASTIQ_DB_URL", f"sqlite:///{db.as_posix()}")

    # 1) No dataset present -> builds from the generated sample and records it.
    monkeypatch.setenv("FORECASTIQ_SOURCE_PATH", str(tmp_path / "absent.xls"))
    assert (
        bootstrap.ensure_warehouse(
            Config.load(), with_forecast=False, sample_path=tmp_path / "sample.xlsx"
        )
        == "sample"
    )

    # 2) The dataset appears -> warehouse is refreshed from it and re-recorded as real.
    real = write_sample_workbook(tmp_path / "real.xlsx")  # stand-in for the real workbook
    monkeypatch.setenv("FORECASTIQ_SOURCE_PATH", str(real))
    assert bootstrap.ensure_warehouse(Config.load(), with_forecast=False) == "real"

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT data_mode FROM warehouse_meta").fetchone()[0] == "real"
    finally:
        conn.close()
