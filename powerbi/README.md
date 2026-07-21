# ForecastIQ — Power BI Build Guide

How to build the dashboard described in [`../docs/dashboard_design.md`](../docs/dashboard_design.md) against
your loaded warehouse. The `.pbix` is intentionally **not committed** (binary + depends on your local data);
this guide rebuilds it in ~15 minutes.

## 1. Connect to the data
**Option A — SQLite (via ODBC)**
1. Install the SQLite ODBC driver.
2. Power BI → *Get Data* → *ODBC* → point to `forecastiq.db`.
3. Load `fact_sales`, `dim_date`, `dim_product`, `dim_region`, `dim_customer`, `forecast_results`, `model_metrics`,
   and the `vw_*` views.

**Option B — CSV (simplest)**
1. Export tables/views to CSV (the pipelines can dump these to `reports/`).
2. Power BI → *Get Data* → *Text/CSV* for each.

## 2. Model relationships
Create these relationships (single direction, one-to-many from dim → fact):

| From | To |
|------|----|
| `dim_date[date_key]` | `fact_sales[order_date_key]` |
| `dim_customer[customer_key]` | `fact_sales[customer_key]` |
| `dim_product[product_key]` | `fact_sales[product_key]` |
| `dim_region[region_key]` | `fact_sales[region_key]` |

Mark `dim_date` as a **Date table** (Modeling → Mark as date table → `full_date`).

## 3. Add measures
Paste the measures from [`dax_measures.md`](dax_measures.md) into a dedicated `_Measures` table.

## 4. Build the four pages
Follow [`../docs/dashboard_design.md`](../docs/dashboard_design.md): Executive Overview, Product & Category,
Regional Performance, Forecast & Segmentation.

## 5. Save screenshots
Export page PNGs into [`../docs/images/`](../docs/images/) and reference them in the README so reviewers see
the dashboard without opening Power BI.
