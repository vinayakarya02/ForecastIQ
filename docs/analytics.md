# ForecastIQ — Analytics Layer

The analytics layer turns the warehouse into business answers. Every function takes a SQLAlchemy
`engine` and returns a pandas DataFrame (tables) or dict (scalar bundles). Metric definitions live in
SQL views where possible so the API, notebook, and Power BI all agree.

Run it: `python pipelines/run_analytics.py` → console summary + CSV/insight exports in `reports/analytics/`.

## Modules

| Module | Provides |
|--------|----------|
| `analytics/base.py` | shared read + math helpers (`read`, `pct`, `safe_div`, `growth_pct`) |
| `analytics/kpis.py` | executive KPI bundle |
| `analytics/trends.py` | monthly/quarterly/yearly revenue, MoM & YoY growth, rolling trends |
| `analytics/segmentation.py` | RFM segmentation, basic CLV, repeat analysis, top customers |
| `analytics/products.py` | category / sub-category / product performance, top & low performers |
| `analytics/regional.py` | market / region / country / state / city / manager performance |
| `analytics/returns.py` | return rate by region/category/product, returned revenue/profit |
| `analytics/insights.py` | rule-based business insights engine |

## KPI definitions
| KPI | Formula |
|-----|---------|
| Profit Margin % | `total_profit / total_revenue` |
| Avg Order Value | `total_revenue / distinct orders` |
| Avg Selling Price | `total_revenue / units sold` |
| Return Rate % | `returned distinct orders / distinct orders` |
| Repeat Rate % | `customers with >1 order / customers` |

## Customer segmentation (RFM)
- **Recency** (days since last order), **Frequency** (distinct orders), **Monetary** (total revenue) come from `vw_customer_rfm`.
- Each is scored into quartiles (1–4) with `NTILE(4)`; recency is inverted (more recent = higher).
- Rule-based labels: **Champions, Loyal, New/Promising, At Risk, Hibernating**.
- **Basic CLV** = total historical revenue per customer (`clv_basic`). A fuller model would add predicted lifespan/retention; this stays on observed history so it is interview-defendable.

## Returns semantics
Returns are recorded at **order** grain (via the Returns sheet). Return rate = returned distinct orders ÷
distinct orders. Because an order can touch multiple categories, per-category returned-order counts can sum
above the overall total — the overall rate always uses distinct orders. The Returns sheet labels the US
market `United States`; a `market_alias` maps it to `US` so those returns match (see [etl_pipeline.md](etl_pipeline.md)).

## Insights engine (`insights.py`)
Each rule reads the warehouse and emits `Insight(category, title, detail, metric)` objects. Thresholds are
**data-derived** (medians, growth signs, volume floors), never hardcoded.

| Rule | Logic |
|------|-------|
| Fastest-growing / declining categories | per-category revenue YoY (last two order-years) |
| Best / weakest region | top region by revenue; lowest margin among above-median-revenue regions |
| Highest-returning product | max return rate among products with ≥ `min_orders` (default 20) |
| Seasonal peak | calendar month with highest average revenue across years |
| High-profit opportunity | highest-margin sub-category at above-median revenue |
| Loss-makers | count + total loss of products with negative profit |

## Testing
`tests/test_analytics_*.py` load a deterministic 2-year fixture warehouse (`warehouse` fixture in
`conftest.py`) and assert both structure and known values (row counts, YoY sign, seasonal peak month,
loss-leader detection, RFM ranking). Run: `pytest -q`.
