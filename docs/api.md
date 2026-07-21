# ForecastIQ — API Design (optional)

A thin **FastAPI** service that exposes the warehouse's KPIs and forecasts as JSON, for anyone who wants the
numbers without opening Power BI. It is optional — the platform is fully functional without it.

Run: `uvicorn forecastiq.api.main:app --reload` → docs at `http://localhost:8000/docs`.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| GET | `/kpis` | Headline KPIs (revenue, profit, margin, orders, AOV) |
| GET | `/revenue/monthly` | Monthly revenue/profit/units series |
| GET | `/products/top?limit=10` | Top products by revenue |
| GET | `/regions` | Regional performance table |
| GET | `/segments/rfm` | RFM segment summary |
| GET | `/forecast?series=total&granularity=monthly` | Latest forecast + confidence bounds |
| GET | `/forecast/metrics?series=total` | Model accuracy for a series |

## Example response — `GET /forecast?series=total&granularity=monthly`
```json
{
  "series_id": "total",
  "granularity": "monthly",
  "model_name": "SARIMA",
  "generated_at": "2026-07-21T10:00:00",
  "points": [
    {"period_start": "2015-01-01", "yhat": 51230.4, "yhat_lower": 47010.1, "yhat_upper": 55450.7},
    {"period_start": "2015-02-01", "yhat": 49810.2, "yhat_lower": 45120.0, "yhat_upper": 54500.4}
  ]
}
```

## Design notes
- Read-only over the warehouse; no writes, so it is safe to expose locally.
- Response schemas are declared with **Pydantic** models in `api/schemas.py` for automatic validation + OpenAPI docs.
- The API reads the **same SQL views** as Power BI, so numbers are guaranteed consistent across surfaces.
- Pagination/limits on list endpoints; sensible defaults; 404 when a requested series has no forecast yet.
