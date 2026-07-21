-- RFM scoring: split Recency, Frequency, Monetary into quartile scores (1-4)
-- and label customers into actionable segments.
WITH scored AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        recency_days,
        frequency,
        monetary,
        -- lower recency = better, so invert the recency score
        5 - NTILE(4) OVER (ORDER BY recency_days)          AS r_score,
        NTILE(4) OVER (ORDER BY frequency)                 AS f_score,
        NTILE(4) OVER (ORDER BY monetary)                  AS m_score
    FROM vw_customer_rfm
)
SELECT
    customer_id,
    customer_name,
    segment,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 2                  THEN 'Loyal'
        WHEN r_score >= 3 AND f_score = 1                   THEN 'New / Promising'
        WHEN r_score = 2                                    THEN 'At Risk'
        ELSE 'Hibernating'
    END AS rfm_segment
FROM scored
ORDER BY rfm_total DESC;
