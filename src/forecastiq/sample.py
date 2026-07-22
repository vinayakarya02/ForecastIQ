"""Synthetic sample-data generator.

Produces a small, **fully synthetic** workbook shaped exactly like the Global Superstore
file (Orders / People / Returns sheets, same columns) so the ETL runs unchanged. Used
to bootstrap a runnable demo in environments where the real (copyrighted) dataset is not
present — e.g. Streamlit Community Cloud. The data is generated, not real, and the app
labels it as such. Deterministic (fixed seed) so builds are reproducible.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_MARKETS = {
    "US": {
        "regions": ["East", "West"],
        "country": "United States",
        "cities": {"East": ("New York", "New York"), "West": ("Los Angeles", "California")},
    },
    "EU": {
        "regions": ["Central", "North"],
        "country": "Germany",
        "cities": {"Central": ("Berlin", "Berlin"), "North": ("Hamburg", "Hamburg")},
    },
    "APAC": {
        "regions": ["Oceania", "North Asia"],
        "country": "Australia",
        "cities": {"Oceania": ("Sydney", "New South Wales"), "North Asia": ("Tokyo", "Kanto")},
    },
}
_MANAGERS = {
    "East": "Kelly Williams",
    "West": "Matt Collister",
    "Central": "Anna Andreadi",
    "North": "Jack Lebron",
    "Oceania": "Anthony Jacobs",
    "North Asia": "Shirley Daniels",
}
_CATALOG = {
    "Technology": {"Phones": ("Smartphone", 300), "Accessories": ("USB Hub", 40)},
    "Furniture": {"Chairs": ("Office Chair", 180), "Tables": ("Desk", 350)},
    "Office Supplies": {"Binders": ("Binder Pack", 15), "Paper": ("Copy Paper", 8)},
}
_SEGMENTS = ["Consumer", "Corporate", "Home Office"]
_SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
_PRIORITIES = ["Low", "Medium", "High", "Critical"]


def _build_frames(seed: int = 42):
    rng = np.random.default_rng(seed)
    customers = [(f"C-{i:03d}", f"Customer {i:03d}", _SEGMENTS[i % 3]) for i in range(1, 61)]
    months = pd.date_range("2021-01-01", "2023-12-01", freq="MS")

    orders, oid = [], 0
    for m in months:
        t = (m.year - 2021) * 12 + (m.month - 1)
        season = 1 + 0.35 * np.sin(2 * np.pi * (m.month - 1) / 12 - np.pi / 2)  # late-year peak
        growth = 1 + 0.02 * t
        for market, info in _MARKETS.items():
            for region in info["regions"]:
                city, state = info["cities"][region]
                for _ in range(int(rng.integers(3, 7))):
                    oid += 1
                    order_id = f"{market[:2].upper()}-{m.year}-{oid:06d}"
                    cust_id, cust_name, segment = customers[int(rng.integers(0, len(customers)))]
                    order_date = m + pd.Timedelta(days=int(rng.integers(0, 27)))
                    ship_date = order_date + pd.Timedelta(days=int(rng.integers(1, 6)))
                    for _ in range(int(rng.integers(1, 4))):  # 1-3 lines per order
                        category = list(_CATALOG)[int(rng.integers(0, 3))]
                        sub = list(_CATALOG[category])[int(rng.integers(0, 2))]
                        pname, base = _CATALOG[category][sub]
                        qty = int(rng.integers(1, 6))
                        discount = float(rng.choice([0.0, 0.0, 0.1, 0.2, 0.3]))
                        sales = round(
                            base * qty * season * growth * float(rng.uniform(0.8, 1.2)), 2
                        )
                        profit = round(sales * (float(rng.uniform(-0.1, 0.35)) - discount * 0.5), 2)
                        orders.append(
                            {
                                "Order ID": order_id,
                                "Order Date": order_date,
                                "Ship Date": ship_date,
                                "Ship Mode": _SHIP_MODES[int(rng.integers(0, 4))],
                                "Customer ID": cust_id,
                                "Customer Name": cust_name,
                                "Segment": segment,
                                "City": city,
                                "State": state,
                                "Country": info["country"],
                                "Market": market,
                                "Region": region,
                                "Product ID": f"{category[:3].upper()}-{sub[:3].upper()}-{base}",
                                "Category": category,
                                "Sub-Category": sub,
                                "Product Name": pname,
                                "Sales": sales,
                                "Quantity": qty,
                                "Discount": discount,
                                "Profit": profit,
                                "Shipping Cost": round(sales * float(rng.uniform(0.02, 0.08)), 2),
                                "Order Priority": _PRIORITIES[int(rng.integers(0, 4))],
                            }
                        )

    orders_df = pd.DataFrame(orders)
    people_df = pd.DataFrame({"Person": list(_MANAGERS.values()), "Region": list(_MANAGERS.keys())})

    # ~7% of distinct orders are returned.
    unique = orders_df[["Order ID", "Market"]].drop_duplicates().reset_index(drop=True)
    picked = rng.choice(len(unique), size=int(len(unique) * 0.07), replace=False)
    returns_df = unique.iloc[picked].copy()
    returns_df.insert(0, "Returned", "Yes")

    return orders_df, people_df, returns_df


def write_sample_workbook(path: str | Path, seed: int = 42) -> Path:
    """Write a synthetic Orders/People/Returns workbook to ``path`` (.xlsx)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    orders, people, returns = _build_frames(seed)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        orders.to_excel(writer, sheet_name="Orders", index=False)
        returns.to_excel(writer, sheet_name="Returns", index=False)
        people.to_excel(writer, sheet_name="People", index=False)
    return path
