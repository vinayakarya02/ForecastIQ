-- ============================================================================
-- ForecastIQ - Data Warehouse Schema (Star Schema)
-- Dialect: SQLite (default). PostgreSQL notes are inline as -- PG:
-- Grain of fact_sales: one row per order line (product within an order).
-- Foreign keys are declared below for documentation and for engines that enforce
-- them; ForecastIQ guarantees integrity via load order (dims before fact), so we
-- leave SQLite's default (FK enforcement off) to keep schema rebuilds order-free.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- DIMENSION: Date
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,   -- yyyymmdd, e.g. 20140315
    full_date     TEXT    NOT NULL,      -- 'YYYY-MM-DD'  (PG: DATE)
    day           INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    quarter       INTEGER NOT NULL,
    year          INTEGER NOT NULL,
    week_of_year  INTEGER NOT NULL,
    day_of_week   INTEGER NOT NULL,      -- 0=Mon ... 6=Sun
    is_weekend    INTEGER NOT NULL       -- 0/1  (PG: BOOLEAN)
);

-- ---------------------------------------------------------------------------
-- DIMENSION: Customer
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (
    customer_key   INTEGER PRIMARY KEY,  -- PG: GENERATED ALWAYS AS IDENTITY
    customer_id    TEXT NOT NULL UNIQUE,
    customer_name  TEXT,
    segment        TEXT                   -- Consumer / Corporate / Home Office
);

-- ---------------------------------------------------------------------------
-- DIMENSION: Product
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_key    INTEGER PRIMARY KEY,
    product_id     TEXT NOT NULL,
    category       TEXT,
    sub_category   TEXT,
    product_name   TEXT,
    UNIQUE (product_id, product_name)
);

-- ---------------------------------------------------------------------------
-- DIMENSION: Region / Geography
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_region;
CREATE TABLE dim_region (
    region_key     INTEGER PRIMARY KEY,
    country        TEXT,
    market         TEXT,
    region         TEXT,
    state          TEXT,
    city           TEXT,
    region_manager TEXT,                  -- from the People sheet (region -> manager)
    UNIQUE (country, market, region, state, city)
);

-- ---------------------------------------------------------------------------
-- FACT: Sales (order-line grain)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_sales;
CREATE TABLE fact_sales (
    sales_key       INTEGER PRIMARY KEY,
    order_id        TEXT    NOT NULL,
    order_date_key  INTEGER NOT NULL,
    ship_date_key   INTEGER,
    customer_key    INTEGER NOT NULL,
    product_key     INTEGER NOT NULL,
    region_key      INTEGER NOT NULL,
    ship_mode       TEXT,
    order_priority  TEXT,
    -- measures
    sales           REAL    NOT NULL,     -- PG: NUMERIC(12,2)
    quantity        INTEGER NOT NULL,
    discount        REAL,
    profit          REAL,
    shipping_cost   REAL,
    is_returned     INTEGER NOT NULL DEFAULT 0,   -- from the Returns sheet (0/1)
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (ship_date_key)  REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key)   REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key)    REFERENCES dim_product(product_key),
    FOREIGN KEY (region_key)     REFERENCES dim_region(region_key)
);

CREATE INDEX idx_fact_order_date ON fact_sales(order_date_key);
CREATE INDEX idx_fact_customer   ON fact_sales(customer_key);
CREATE INDEX idx_fact_product    ON fact_sales(product_key);
CREATE INDEX idx_fact_region     ON fact_sales(region_key);

-- ---------------------------------------------------------------------------
-- OUTPUT: Forecast results (written back by the forecasting pipeline)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS forecast_results;
CREATE TABLE forecast_results (
    forecast_key  INTEGER PRIMARY KEY,
    run_id        TEXT    NOT NULL,       -- groups one pipeline execution
    series_id     TEXT    NOT NULL,       -- 'total' | 'category:Technology' | 'region:APAC'
    granularity   TEXT    NOT NULL,       -- 'monthly' | 'quarterly'
    model_name    TEXT    NOT NULL,       -- winning model for this series
    period_start  TEXT    NOT NULL,       -- 'YYYY-MM-DD' first day of forecast period
    yhat          REAL    NOT NULL,       -- point forecast
    yhat_lower    REAL,                   -- lower confidence bound
    yhat_upper    REAL,                   -- upper confidence bound
    is_actual     INTEGER NOT NULL DEFAULT 0,  -- 1 if this row is observed history (for forecast-vs-actual)
    created_at    TEXT    NOT NULL
);
CREATE INDEX idx_forecast_series ON forecast_results(series_id, granularity);

-- ---------------------------------------------------------------------------
-- OUTPUT: Model evaluation metrics (one row per model per series per run)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS model_metrics;
CREATE TABLE model_metrics (
    metric_key   INTEGER PRIMARY KEY,
    run_id       TEXT    NOT NULL,
    series_id    TEXT    NOT NULL,
    model_name   TEXT    NOT NULL,
    rmse         REAL,
    mae          REAL,
    mape         REAL,
    r2           REAL,
    is_best      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL
);

-- ---------------------------------------------------------------------------
-- OPS: Data-quality / validation log (written by the ETL validate step)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS data_quality_log;
CREATE TABLE data_quality_log (
    check_key    INTEGER PRIMARY KEY,
    run_id       TEXT    NOT NULL,
    check_name   TEXT    NOT NULL,
    status       TEXT    NOT NULL,        -- PASS | WARN | FAIL
    detail       TEXT,
    rows_flagged INTEGER,
    created_at   TEXT    NOT NULL
);
