# ForecastIQ — Power BI Dashboard Design

The dashboard connects to the SQL warehouse (or the analytical views) and presents four report pages.
Build guide and DAX measures: [`../powerbi/README.md`](../powerbi/README.md) and
[`../powerbi/dax_measures.md`](../powerbi/dax_measures.md).

## Data model in Power BI
Import the star schema tables and let Power BI mirror the SQL relationships:

```
dim_date[date_key]     1 --- * fact_sales[order_date_key]
dim_customer[...key]   1 --- * fact_sales[customer_key]
dim_product[...key]    1 --- * fact_sales[product_key]
dim_region[...key]     1 --- * fact_sales[region_key]
```
Mark `dim_date` as the official **date table**. `forecast_results` is a separate table linked on `period_start`.

## Page 1 — Executive Overview
- **KPI cards**: Total Revenue, Total Profit, Profit Margin %, Orders, Avg Order Value, MoM Growth %.
- **Revenue trend** line chart (monthly) with 3-month rolling average.
- **Sales by Category** donut; **Sales by Segment** bar.
- Slicers: Year, Market, Category, Segment.

## Page 2 — Product & Category
- Top 10 products (bar), category → sub-category **decomposition tree**.
- Profit-margin scatter (revenue vs margin, sized by units) to spot loss-makers.
- Matrix: Category × Sub-Category with revenue, profit, margin.

## Page 3 — Regional Performance
- Filled **map** of revenue by country/region.
- Market/region ranking bar; orders & customers by region.
- Drill-through from region → product mix.

## Page 4 — Forecast & Segmentation
- **Forecast vs Actual** line: actuals solid, forecast dashed, shaded confidence band (`yhat_lower/upper`).
- Model accuracy card: winning model + MAPE/RMSE per series (from `model_metrics`).
- **RFM segmentation**: customer count and revenue by `rfm_segment`; scatter of Frequency vs Monetary.

## Interactivity
- Cross-filtering across all visuals on a page.
- Sync slicers for Year/Market across pages.
- Tooltips show profit margin and MoM growth on hover.

## Suggested theme
Neutral background, single accent color for actuals, a muted secondary for forecast, and a diverging scale
for profit margin (red = loss, green = healthy). Keep to one accent family for a clean, executive look.

> A `.pbix` file is not committed (binary + dataset-dependent). This doc + the DAX file let anyone rebuild
> the report in minutes against their own loaded warehouse, and screenshots go in `docs/images/`.
