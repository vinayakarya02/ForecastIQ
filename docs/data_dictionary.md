# ForecastIQ — Data Dictionary

## Source dataset: Global Superstore (Kaggle)

The reference file is a multi-sheet Excel workbook (`data/raw/Global Superstore.xls`) read with
`pandas.read_excel`. Three sheets are used:

| Sheet | Rows | Role | Effect |
|-------|------|------|--------|
| **Orders** | 51,290 | primary fact dataset | becomes `fact_sales` + dimensions |
| **People** | 13 | region → manager map | adds `region_manager` to `dim_region` |
| **Returns** | 1,173 | returned (order_id, market) | adds `is_returned` flag to `fact_sales` |

> Label reconciliation: Orders uses region `EMEA` while People uses `AMEA` for the same manager —
> handled by `source.region_aliases` in `config.yaml` (no manual editing of the data).

Raw **Orders** columns as they appear in the sheet, and the canonical name ForecastIQ maps them to
(via `etl.column_map` in `config/config.yaml`).

| Raw column | Canonical name | Type | Description |
|------------|----------------|------|-------------|
| Order ID | `order_id` | string | Business key for an order (repeats across lines) |
| Order Date | `order_date` | date | When the order was placed |
| Ship Date | `ship_date` | date | When the order shipped |
| Ship Mode | `ship_mode` | string | Standard Class / Second Class / First Class / Same Day |
| Customer ID | `customer_id` | string | Natural key for a customer |
| Customer Name | `customer_name` | string | Customer display name |
| Segment | `segment` | string | Consumer / Corporate / Home Office |
| City | `city` | string | Ship-to city |
| State | `state` | string | Ship-to state/province |
| Country | `country` | string | Ship-to country |
| Market | `market` | string | Macro market (APAC, EU, US, LATAM, …) |
| Region | `region` | string | Sub-region within a market |
| Product ID | `product_id` | string | Natural key for a product |
| Category | `category` | string | Furniture / Office Supplies / Technology |
| Sub-Category | `sub_category` | string | e.g. Chairs, Phones, Binders |
| Product Name | `product_name` | string | Product display name |
| Sales | `sales` | float | Line revenue (currency) |
| Quantity | `quantity` | int | Units sold on the line |
| Discount | `discount` | float | Fractional discount 0.0–1.0 |
| Profit | `profit` | float | Line profit (can be negative) |
| Shipping Cost | `shipping_cost` | float | Shipping cost for the line |
| Order Priority | `order_priority` | string | Critical / High / Medium / Low |

> Column names vary slightly between the "Sample Superstore" and "Global Superstore" files
> (e.g. `Postal Code`, `Row ID`). Only the mapping in `config.yaml` needs updating — the pipeline is unchanged.

## Engineered features (added in `transform.py`)

| Feature | Grain | Description |
|---------|-------|-------------|
| `order_date_key` / `ship_date_key` | fact | `yyyymmdd` surrogate keys into `dim_date` |
| `year`, `month`, `quarter`, `week_of_year` | date dim | Calendar parts for slicing & seasonality |
| `is_weekend` | date dim | 1 if order placed on Sat/Sun |
| `region_manager` | dim_region | Regional manager from the **People** sheet (via region + alias map) |
| `is_returned` | fact_sales | 1 if the (order_id, market) appears in the **Returns** sheet, else 0 |
| `revenue_lag_1`, `revenue_lag_12` | monthly series | Prior-period & prior-year revenue (ML features) |
| `revenue_roll_3` | monthly series | 3-month rolling mean (trend feature) |
| `month_sin`, `month_cos` | monthly series | Cyclical encoding of month for regression models |

## Output tables (semantics)

| Column | Table | Meaning |
|--------|-------|---------|
| `series_id` | forecast/metrics | `total`, `category:<name>`, or `region:<name>` |
| `yhat`, `yhat_lower`, `yhat_upper` | forecast_results | point forecast and confidence interval |
| `is_actual` | forecast_results | 1 = observed history, 0 = forward forecast |
| `mape` | model_metrics | mean absolute percentage error on hold-out (selection metric) |
| `is_best` | model_metrics | 1 = model chosen for that series |
