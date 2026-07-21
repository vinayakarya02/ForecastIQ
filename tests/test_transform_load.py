"""Integration tests: transform -> load -> views against a temp SQLite DB."""
from forecastiq.etl.transform import transform
from forecastiq.etl.load import load
from forecastiq.utils.io import get_engine, query_df


def test_transform_grain_and_keys(cfg, sales_frame):
    tables = transform(sales_frame, cfg)

    assert len(tables["fact_sales"]) == 4                 # one row per order line
    assert len(tables["dim_customer"]) == 2               # C1, C2
    assert len(tables["dim_product"]) == 3                # (P1,Widget),(P2,Gadget),(P3,Gizmo)
    assert set(tables["fact_sales"]["order_date_key"]) == {20140105, 20140210, 20140215}
    # every fact row resolved its dimension keys
    for key in ["customer_key", "product_key", "region_key"]:
        assert tables["fact_sales"][key].notna().all()


def test_load_roundtrip_and_views(cfg, sales_frame, tmp_path):
    tables = transform(sales_frame, cfg)
    db = tmp_path / "test.db"
    engine = get_engine(f"sqlite:///{db.as_posix()}")

    summary = load(tables, cfg, engine=engine)
    assert summary["fact_sales"] == 4

    # Monthly revenue view: Jan=150, Feb=175, total=325
    total = query_df("SELECT SUM(revenue) AS r FROM vw_monthly_sales", engine)["r"].iloc[0]
    assert abs(total - 325.0) < 1e-6

    months = query_df("SELECT COUNT(*) AS n FROM vw_monthly_sales", engine)["n"].iloc[0]
    assert months == 2

    # Category view aggregates correctly (Technology = 100+100+75 = 275)
    tech = query_df(
        "SELECT SUM(revenue) AS r FROM vw_sales_by_category WHERE category='Technology'", engine
    )["r"].iloc[0]
    assert abs(tech - 275.0) < 1e-6
