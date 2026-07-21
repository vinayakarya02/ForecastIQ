-- Forecast vs actual for the total revenue series (feeds the forecast visual).
-- Combines observed history (is_actual = 1) with forward forecast rows.
SELECT
    period_start,
    model_name,
    CASE WHEN is_actual = 1 THEN yhat END AS actual,
    CASE WHEN is_actual = 0 THEN yhat END AS forecast,
    yhat_lower,
    yhat_upper
FROM forecast_results
WHERE series_id = 'total'
  AND granularity = 'monthly'
  AND run_id = (SELECT run_id FROM forecast_results ORDER BY created_at DESC LIMIT 1)
ORDER BY period_start;

-- Winning model + accuracy per series for the latest run.
SELECT series_id, model_name, rmse, mae, mape, r2
FROM model_metrics
WHERE is_best = 1
  AND run_id = (SELECT run_id FROM model_metrics ORDER BY created_at DESC LIMIT 1)
ORDER BY series_id;
