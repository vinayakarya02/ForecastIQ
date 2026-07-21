-- ============================================================================
-- ForecastIQ - Analytical Views
-- Reusable business logic on top of the star schema. Power BI / the API / SQL
-- clients read these so metric definitions live in one place.
-- ============================================================================

-- ---- Monthly revenue, profit and units (overall time series) ---------------
DROP VIEW IF EXISTS vw_monthly_sales;
CREATE VIEW vw_monthly_sales AS
SELECT
    d.year,
    d.month,
    printf('%04d-%02d-01', d.year, d.month) AS period_start,  -- PG: make_date(d.year,d.month,1)
    ROUND(SUM(f.sales), 2)    AS revenue,
    ROUND(SUM(f.profit), 2)   AS profit,
    SUM(f.quantity)           AS units,
    COUNT(DISTINCT f.order_id) AS orders
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
GROUP BY d.year, d.month;

-- ---- Sales by category / sub-category --------------------------------------
DROP VIEW IF EXISTS vw_sales_by_category;
CREATE VIEW vw_sales_by_category AS
SELECT
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2)  AS revenue,
    ROUND(SUM(f.profit), 2) AS profit,
    SUM(f.quantity)         AS units,
    ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales), 0), 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category, p.sub_category;

-- ---- Regional performance (enriched with region manager from People) -------
DROP VIEW IF EXISTS vw_regional_performance;
CREATE VIEW vw_regional_performance AS
SELECT
    r.market,
    r.region,
    r.country,
    MAX(r.region_manager) AS region_manager,
    ROUND(SUM(f.sales), 2)  AS revenue,
    ROUND(SUM(f.profit), 2) AS profit,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(DISTINCT f.customer_key) AS customers
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.market, r.region, r.country;

-- ---- Return-rate analytics (from the Returns sheet) ------------------------
-- Return rate = share of distinct orders flagged returned, by market & region.
DROP VIEW IF EXISTS vw_return_rate;
CREATE VIEW vw_return_rate AS
SELECT
    r.market,
    r.region,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(DISTINCT CASE WHEN f.is_returned = 1 THEN f.order_id END) AS returned_orders,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.is_returned = 1 THEN f.order_id END)
        / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS return_rate_pct,
    ROUND(SUM(CASE WHEN f.is_returned = 1 THEN f.sales ELSE 0 END), 2) AS returned_revenue
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.market, r.region;

-- ---- Top products by revenue -----------------------------------------------
DROP VIEW IF EXISTS vw_top_products;
CREATE VIEW vw_top_products AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(SUM(f.sales), 2)  AS revenue,
    ROUND(SUM(f.profit), 2) AS profit,
    SUM(f.quantity)         AS units
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_id, p.product_name, p.category;

-- ---- Customer RFM base (Recency / Frequency / Monetary) --------------------
-- Recency measured in days relative to the latest order date in the warehouse.
DROP VIEW IF EXISTS vw_customer_rfm;
CREATE VIEW vw_customer_rfm AS
WITH last_day AS (
    SELECT MAX(d.full_date) AS max_date
    FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key
)
SELECT
    c.customer_key,
    c.customer_id,
    c.customer_name,
    c.segment,
    CAST(julianday((SELECT max_date FROM last_day))
       - julianday(MAX(d.full_date)) AS INTEGER)      AS recency_days,   -- PG: (max_date - MAX(full_date))
    COUNT(DISTINCT f.order_id)                         AS frequency,
    ROUND(SUM(f.sales), 2)                             AS monetary
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_date d     ON f.order_date_key = d.date_key
GROUP BY c.customer_key, c.customer_id, c.customer_name, c.segment;

-- ---- Month-over-month growth ----------------------------------------------
DROP VIEW IF EXISTS vw_monthly_growth;
CREATE VIEW vw_monthly_growth AS
SELECT
    period_start,
    revenue,
    LAG(revenue) OVER (ORDER BY period_start) AS prev_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY period_start))
        / NULLIF(LAG(revenue) OVER (ORDER BY period_start), 0), 2) AS mom_growth_pct
FROM vw_monthly_sales;
