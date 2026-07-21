-- Top 10 products by revenue.
SELECT product_name, category, revenue, profit, units
FROM vw_top_products
ORDER BY revenue DESC
LIMIT 10;

-- Category contribution to total revenue (share %).
SELECT
    category,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM vw_sales_by_category), 2) AS revenue_share_pct
FROM vw_sales_by_category
GROUP BY category
ORDER BY revenue DESC;

-- Least profitable sub-categories (loss-makers worth flagging).
SELECT category, sub_category, revenue, profit, profit_margin_pct
FROM vw_sales_by_category
ORDER BY profit ASC
LIMIT 10;
