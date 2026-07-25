-- ============================================
-- STOCK MARKET ANALYTICS QUERIES
-- Database: stock_analytics_db
-- ============================================


-- --------------------------------------------
-- 1. Preview daily enriched data
-- --------------------------------------------
SELECT *
FROM gold_daily_enriched
LIMIT 10;


-- --------------------------------------------
-- 2. Latest closing price per ticker
-- --------------------------------------------
SELECT
    ticker,
    MAX(date) AS latest_date,
    MAX_BY(close, date) AS latest_close
FROM gold_daily_enriched
GROUP BY ticker
ORDER BY ticker;


-- --------------------------------------------
-- 3. Top 5 most volatile stocks (last 30 days)
-- --------------------------------------------
SELECT
    ticker,
    ROUND(AVG(volatility_30), 6) AS avg_volatility_30d
FROM gold_daily_enriched
WHERE date >= DATE_ADD('day', -30, CURRENT_DATE)
GROUP BY ticker
ORDER BY avg_volatility_30d DESC
LIMIT 5;


-- --------------------------------------------
-- 4. Month-over-month return per ticker (2025)
-- --------------------------------------------
SELECT
    ticker,
    year,
    month,
    ROUND(monthly_return * 100, 2) AS monthly_return_pct,
    trading_days
FROM gold_monthly_aggregates
WHERE year = 2025
ORDER BY ticker, month;


-- --------------------------------------------
-- 5. Best performing stock per quarter (2025)
-- --------------------------------------------
SELECT
    ticker,
    CASE
        WHEN month BETWEEN 1 AND 3  THEN 'Q1'
        WHEN month BETWEEN 4 AND 6  THEN 'Q2'
        WHEN month BETWEEN 7 AND 9  THEN 'Q3'
        WHEN month BETWEEN 10 AND 12 THEN 'Q4'
    END AS quarter,
    ROUND(SUM(monthly_return) * 100, 2) AS quarterly_return_pct
FROM gold_monthly_aggregates
WHERE year = 2025
GROUP BY ticker, 2
ORDER BY quarterly_return_pct DESC;


-- --------------------------------------------
-- 6. Moving average crossover signal
--    (7-day MA crosses above 30-day MA = bullish)
-- --------------------------------------------
SELECT
    ticker,
    date,
    ROUND(close, 2)  AS close,
    ROUND(ma_7, 2)   AS ma_7,
    ROUND(ma_30, 2)  AS ma_30,
    CASE
        WHEN ma_7 > ma_30 THEN 'BULLISH'
        WHEN ma_7 < ma_30 THEN 'BEARISH'
        ELSE 'NEUTRAL'
    END AS signal
FROM gold_daily_enriched
WHERE date >= DATE_ADD('day', -60, CURRENT_DATE)
ORDER BY ticker, date DESC;


-- --------------------------------------------
-- 7. Average daily return comparison
-- --------------------------------------------
SELECT
    ticker,
    ROUND(AVG(daily_return) * 100, 4) AS avg_daily_return_pct,
    ROUND(MAX(daily_return) * 100, 2) AS best_day_pct,
    ROUND(MIN(daily_return) * 100, 2) AS worst_day_pct
FROM gold_daily_enriched
WHERE year = 2025
GROUP BY ticker
ORDER BY avg_daily_return_pct DESC;


-- --------------------------------------------
-- 8. Total volume traded per ticker per month
-- --------------------------------------------
SELECT
    ticker,
    year,
    month,
    monthly_volume,
    ROUND(monthly_volume / SUM(monthly_volume) OVER (PARTITION BY year, month) * 100, 2) AS volume_share_pct
FROM gold_monthly_aggregates
WHERE year = 2025
ORDER BY year, month, volume_share_pct DESC;