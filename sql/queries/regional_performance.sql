-- Revenue & profit by market/region with margin.
SELECT
    market,
    region,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(profit), 2)  AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS profit_margin_pct,
    SUM(orders)    AS orders,
    SUM(customers) AS customers
FROM vw_regional_performance
GROUP BY market, region
ORDER BY revenue DESC;

-- Top 10 countries by revenue.
SELECT country, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit
FROM vw_regional_performance
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;
