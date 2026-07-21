-- Revenue, profit and MoM growth over time (feeds the "Revenue Trends" visual).
SELECT
    period_start,
    revenue,
    prev_revenue,
    mom_growth_pct
FROM vw_monthly_growth
ORDER BY period_start;

-- Rolling 3-month average revenue (smoothed trend line).
SELECT
    period_start,
    revenue,
    ROUND(AVG(revenue) OVER (ORDER BY period_start
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS revenue_3m_avg
FROM vw_monthly_sales
ORDER BY period_start;
