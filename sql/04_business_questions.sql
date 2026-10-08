-- Project 1: business questions, answered from the clean view v_trades_clean.
-- Run 03_data_quality_checks.sql first (it creates the view).

-- Q1 Fail rate by counterparty (trades due to settle by 30 Jun 2026)
SELECT c.counterparty_name,
       COUNT(*)                                             AS trades_due,
       COUNT(s.fail_reason)                                 AS trades_failed,
       ROUND(100.0 * COUNT(s.fail_reason) / COUNT(*), 1)    AS fail_rate_pct
FROM v_trades_clean t
JOIN settlements s    ON s.trade_id = t.trade_id
JOIN counterparties c ON c.counterparty_id = t.counterparty_id
WHERE s.status <> 'PENDING'
GROUP BY c.counterparty_name
ORDER BY fail_rate_pct DESC;

-- Q2 The 10 oldest fails still open at 30 Jun 2026
SELECT t.trade_id, c.counterparty_name, sec.security_name, t.trade_value, t.currency,
       s.expected_settle_date, s.fail_reason,
       DATE '2026-06-30' - s.expected_settle_date AS days_outstanding
FROM v_trades_clean t
JOIN settlements s    ON s.trade_id = t.trade_id
JOIN counterparties c ON c.counterparty_id = t.counterparty_id
JOIN securities sec   ON sec.security_id = t.security_id
WHERE s.status = 'FAILED'
ORDER BY days_outstanding DESC
LIMIT 10;

-- Q3 Settled value by client and currency
SELECT cl.client_name, t.currency, ROUND(SUM(t.trade_value) / 1e6, 2) AS settled_value_m
FROM v_trades_clean t
JOIN settlements s ON s.trade_id = t.trade_id
JOIN accounts a    ON a.account_id = t.account_id
JOIN clients cl    ON cl.client_id = a.client_id
WHERE s.status = 'SETTLED'
GROUP BY cl.client_name, t.currency
ORDER BY cl.client_name, settled_value_m DESC;

-- Q4 Average days late for failed trades, by market and fail reason
SELECT sec.market, s.fail_reason, COUNT(*) AS fails, ROUND(AVG(s.days_late), 1) AS avg_days_late
FROM v_trades_clean t
JOIN settlements s  ON s.trade_id = t.trade_id
JOIN securities sec ON sec.security_id = t.security_id
WHERE s.fail_reason IS NOT NULL AND s.status = 'SETTLED'
GROUP BY sec.market, s.fail_reason
ORDER BY sec.market, fails DESC;

-- Q5 Fails per month, and the change from the previous month (LAG window function)
WITH monthly AS (
    SELECT DATE_TRUNC('month', s.expected_settle_date)::date AS month,
           COUNT(s.fail_reason) AS fails
    FROM v_trades_clean t
    JOIN settlements s ON s.trade_id = t.trade_id
    WHERE s.status <> 'PENDING'
    GROUP BY 1
)
SELECT month, fails,
       fails - LAG(fails) OVER (ORDER BY month) AS change_vs_prev_month
FROM monthly
ORDER BY month;

-- Q6 Running total of settled value through the half-year (cumulative SUM window)
WITH daily AS (
    SELECT s.actual_settle_date AS day, SUM(t.trade_value) AS settled_value
    FROM v_trades_clean t
    JOIN settlements s ON s.trade_id = t.trade_id
    WHERE s.status = 'SETTLED' AND t.currency = 'AUD'
    GROUP BY 1
)
SELECT day, ROUND(settled_value / 1e6, 2) AS settled_m,
       ROUND(SUM(settled_value) OVER (ORDER BY day) / 1e6, 1) AS running_total_m
FROM daily
ORDER BY day;

-- Q7 Counterparties whose fail rate is above the overall average (CTE + comparison)
WITH by_cp AS (
    SELECT t.counterparty_id,
           AVG(CASE WHEN s.fail_reason IS NOT NULL THEN 1.0 ELSE 0 END) AS fail_rate
    FROM v_trades_clean t
    JOIN settlements s ON s.trade_id = t.trade_id
    WHERE s.status <> 'PENDING'
    GROUP BY t.counterparty_id
), overall AS (
    SELECT AVG(fail_rate) AS avg_rate FROM by_cp
)
SELECT c.counterparty_name, ROUND(100 * b.fail_rate, 1) AS fail_rate_pct,
       ROUND(100 * o.avg_rate, 1) AS average_pct
FROM by_cp b
CROSS JOIN overall o
JOIN counterparties c ON c.counterparty_id = b.counterparty_id
WHERE b.fail_rate > o.avg_rate
ORDER BY b.fail_rate DESC;
