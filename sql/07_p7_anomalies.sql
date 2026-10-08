-- Project 7, Stages C-D: load the super fund prices and NAVs, then flag anomalies and stale prices.
-- Run from the repo root:  psql -d custody -f sql/07_p7_anomalies.sql

DROP TABLE IF EXISTS p7_prices, p7_nav;
CREATE TABLE p7_prices (isin CHAR(12), price_date DATE, close_price NUMERIC(18,4));
CREATE TABLE p7_nav (nav_date DATE, investment_option TEXT, unit_price NUMERIC(18,5));
\copy p7_prices FROM 'project7/p7_prices.csv' WITH (FORMAT csv, HEADER true)
\copy p7_nav    FROM 'project7/p7_nav.csv'    WITH (FORMAT csv, HEADER true)

-- Daily return per security, plus the spread (standard deviation) of the previous 20 returns
CREATE OR REPLACE VIEW v_p7_price_returns AS
WITH r AS (
    SELECT isin, price_date, close_price,
           close_price / LAG(close_price) OVER w - 1 AS daily_return
    FROM p7_prices
    WINDOW w AS (PARTITION BY isin ORDER BY price_date)
)
SELECT r.*,
       STDDEV_SAMP(daily_return) OVER (PARTITION BY isin ORDER BY price_date
                                       ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS prior_20d_sd,
       COUNT(daily_return)       OVER (PARTITION BY isin ORDER BY price_date
                                       ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS prior_obs
FROM r;

-- Rule A: absolute daily move above 15%
SELECT 'R08a move > 15%' AS rule, isin, price_date, ROUND(100 * daily_return, 1) AS move_pct
FROM v_p7_price_returns
WHERE ABS(daily_return) > 0.15
ORDER BY isin, price_date;

-- Rule B: move more than 4 standard deviations from recent behaviour (needs 10+ prior days)
SELECT 'R08b z-score > 4' AS rule, isin, price_date,
       ROUND(100 * daily_return, 1) AS move_pct,
       ROUND(daily_return / prior_20d_sd, 1) AS z_score
FROM v_p7_price_returns
WHERE prior_obs >= 10 AND prior_20d_sd > 0
  AND ABS(daily_return / prior_20d_sd) > 4
ORDER BY ABS(daily_return / prior_20d_sd) DESC;

-- Compare thresholds: how many flags each one produces
SELECT threshold, COUNT(*) AS flags, COUNT(DISTINCT isin) AS securities
FROM (
    SELECT 'abs move > 15%' AS threshold, isin FROM v_p7_price_returns WHERE ABS(daily_return) > 0.15
    UNION ALL
    SELECT 'z > 4', isin FROM v_p7_price_returns
     WHERE prior_obs >= 10 AND prior_20d_sd > 0 AND ABS(daily_return / prior_20d_sd) > 4
    UNION ALL
    SELECT 'z > 3', isin FROM v_p7_price_returns
     WHERE prior_obs >= 10 AND prior_20d_sd > 0 AND ABS(daily_return / prior_20d_sd) > 3
) t
GROUP BY threshold
ORDER BY flags;

-- R01 Stale price: the latest price has not changed for 5 or more business days
WITH flagged AS (
    SELECT isin, price_date, close_price,
           CASE WHEN close_price = LAG(close_price) OVER (PARTITION BY isin ORDER BY price_date)
                THEN 0 ELSE 1 END AS changed
    FROM p7_prices
), runs AS (
    SELECT isin, price_date, close_price,
           SUM(changed) OVER (PARTITION BY isin ORDER BY price_date) AS run_id
    FROM flagged
), last_run AS (
    SELECT isin, run_id, COUNT(*) - 1 AS unchanged_days, MAX(price_date) AS last_date
    FROM runs
    GROUP BY isin, run_id
)
SELECT 'R01 stale price' AS rule, isin, unchanged_days, last_date
FROM last_run
WHERE last_date = DATE '2026-06-30' AND unchanged_days >= 5
ORDER BY isin;

-- R09 NAV unit price moves of more than 3% in a day
SELECT * FROM (
    SELECT 'R09 NAV move > 3%' AS rule, investment_option, nav_date,
           ROUND(100 * (unit_price / LAG(unit_price) OVER w - 1), 2) AS move_pct
    FROM p7_nav
    WINDOW w AS (PARTITION BY investment_option ORDER BY nav_date)
) x
WHERE ABS(move_pct) > 3
ORDER BY investment_option, nav_date;
